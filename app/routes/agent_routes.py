from flask import Blueprint, request, jsonify
from flask_jwt_extended import current_user
from app.models.ticket import Ticket
from app.utils.decorators import roles_required
from app.utils.dept_isolation import assert_dept_access
from app.extensions import db
from datetime import datetime

agent_bp = Blueprint('agent', __name__)


@agent_bp.route('/tickets', methods=['GET'])
@roles_required('AGENT')
def get_agent_tickets():
    """
    Returns tickets visible to the authenticated agent.

    STRICT Visibility Rules:
      1. Tickets directly assigned to this agent (any status)
      2. Unassigned tickets in agent's department where:
           status == 'APPROVED'  (Team Lead explicitly approved OR auto-approved)
           AND assigned_to IS NULL

    Agents must NOT see:
      - Other department tickets
      - OPEN tickets (not yet approved by Team Lead)
      - Tickets assigned to other agents
      - CLOSED tickets from other departments
    """
    agent_id = current_user.id
    dept_id = current_user.agent_profile.department_id if current_user.agent_profile else None

    tickets = Ticket.query.filter(
        Ticket.department_id == dept_id,
        db.or_(
            # Rule 1: Tickets directly assigned to this agent (any status)
            Ticket.assigned_to == agent_id,
            # Rule 2: Unassigned APPROVED pool — agent can accept
            db.and_(
                Ticket.assigned_to == None,
                Ticket.status == 'APPROVED'
            )
        )
    ).order_by(Ticket.created_at.desc()).all()

    result = []
    for t in tickets:
        d = t.to_dict()
        d['can_accept']  = (t.assigned_to is None and t.status == 'APPROVED')
        d['can_decline'] = (t.assigned_to == agent_id)
        d['can_resolve'] = (t.assigned_to == agent_id and t.status == 'IN_PROGRESS')
        result.append(d)

    return jsonify({"success": True, "data": result}), 200


@agent_bp.route('/update-ticket', methods=['POST'])
@roles_required('AGENT')
def update_ticket():
    """
    Agent actions on a ticket.

    Payload:
        { "ticket_id": <int>, "action": "ACCEPT" | "DECLINE" | "RESOLVE" }

    ACCEPT  — Claim an unassigned APPROVED ticket (atomic lock prevents race condition)
    DECLINE — Release a ticket back to the APPROVED unassigned pool
    RESOLVE — Mark ticket as RESOLVED when work is done

    DEPT ISOLATION:
        ACCEPT is blocked with 403 if ticket.department_id != agent.department_id
    """
    data = request.get_json()
    ticket_id = data.get('ticket_id')
    action    = (data.get('action') or '').upper()
    agent_id  = current_user.id

    if not ticket_id or not action:
        return jsonify({"success": False, "message": "ticket_id and action are required"}), 400

    if action not in ('ACCEPT', 'DECLINE', 'RESOLVE'):
        return jsonify({"success": False, "message": "action must be ACCEPT, DECLINE, or RESOLVE"}), 400

    try:
        # ── ACCEPT ────────────────────────────────────────────────────────────
        if action == 'ACCEPT':
            # Row-level lock to prevent double claiming (race condition guard)
            ticket = Ticket.query.with_for_update().get(ticket_id)
            if ticket is None:
                return jsonify({"success": False, "message": "Ticket not found"}), 404

            # DEPT ISOLATION: Block cross-department acceptance
            agent_dept = current_user.agent_profile.department_id if current_user.agent_profile else None
            if ticket.department_id != agent_dept:
                return jsonify({
                    "success": False,
                    "message": "Access denied: cannot accept tickets from a different department"
                }), 403

            if ticket.assigned_to is not None and ticket.assigned_to != agent_id:
                return jsonify({"success": False, "message": "Ticket already accepted by another agent"}), 409

            if ticket.status not in ('APPROVED', 'IN_PROGRESS'):
                return jsonify({"success": False, "message": f"Cannot accept a ticket with status {ticket.status}. Only APPROVED or IN_PROGRESS tickets can be accepted."}), 400

            ticket.assigned_to = agent_id
            ticket.status      = 'IN_PROGRESS'
            ticket.accepted_at = datetime.utcnow()
            ticket.updated_at  = datetime.utcnow()

            _log(agent_id, ticket, "TICKET_ACCEPTED", f"Ticket accepted by agent {current_user.full_name}")

        # ── DECLINE ───────────────────────────────────────────────────────────
        elif action == 'DECLINE':
            ticket = Ticket.query.get(ticket_id)
            if ticket is None:
                return jsonify({"success": False, "message": "Ticket not found"}), 404

            if ticket.assigned_to != agent_id:
                return jsonify({"success": False, "message": "You can only decline tickets assigned to you"}), 403

            ticket.assigned_to = None
            ticket.status      = 'APPROVED'   # Returns to APPROVED pool
            ticket.updated_at  = datetime.utcnow()

            _log(agent_id, ticket, "TICKET_DECLINED", f"Ticket released back to pool by agent {current_user.full_name}")

        # ── RESOLVE ───────────────────────────────────────────────────────────
        elif action == 'RESOLVE':
            ticket = Ticket.query.get(ticket_id)
            if ticket is None:
                return jsonify({"success": False, "message": "Ticket not found"}), 404

            if ticket.assigned_to != agent_id:
                return jsonify({"success": False, "message": "You can only resolve tickets assigned to you"}), 403

            ticket.status      = 'RESOLVED'
            ticket.resolved_at = datetime.utcnow()
            ticket.updated_at  = datetime.utcnow()

            _log(agent_id, ticket, "TICKET_RESOLVED", f"Ticket resolved by agent {current_user.full_name}")

        db.session.commit()
        return jsonify({
            "success": True,
            "message": f"Action {action} performed successfully",
            "data": ticket.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


# ─── helpers ────────────────────────────────────────────────────────────────

def _log(user_id, ticket, action_type, description):
    """Fire-and-forget audit + activity log. Does NOT commit."""
    try:
        from app.services.audit_service import AuditService
        from app.utils.logging_utils import log_activity
        AuditService.log_action(description, user_id, ticket.id)
        log_activity(
            user_id=user_id,
            action_type=action_type,
            entity_type="TICKET",
            entity_id=ticket.id,
            description=description
        )
    except Exception as ex:
        print(f"⚠️ LOG ERROR: {ex}")
