import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import current_user
from app.models.ticket import Ticket
from app.models.user import User, AgentProfile
from app.models.role import Role
from app.models.team import Team
from app.models.team_member import TeamMember
from app.utils.decorators import roles_required
from app.utils.dept_isolation import apply_dept_filter, assert_dept_access
from app.extensions import db
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

team_lead_bp = Blueprint('team_lead', __name__)


@team_lead_bp.route('/my-tickets', methods=['GET'])
@roles_required('TEAM_LEAD')
def get_my_team_tickets():
    """
    STRICT: Returns ONLY tickets visible to this Team Lead for action.

    Rule:
        ticket.department_id == TL.department_id
        AND ticket.status == 'OPEN'
        AND ticket.assigned_to IS NULL
        AND ticket.parent_ticket_id IS NULL  ← Child tickets are hidden; they appear
                                               under the parent's "Related Reports" panel.

    Team Lead must NOT see:
        - Other department tickets
        - Already assigned tickets
        - Closed / Approved / In-Progress tickets (those are 'done' from TL perspective)
        - Child tickets (informational only; bundled under the parent)
    """
    dept_id = (
        current_user.team_lead_profile.department_id
        if current_user.team_lead_profile else None
    )
    if not dept_id:
        return jsonify({"success": False, "message": "Team Lead has no department assigned"}), 403

    tickets = Ticket.query.filter(
        Ticket.department_id == dept_id,
        Ticket.status == 'OPEN',
        Ticket.assigned_to == None,
        Ticket.parent_ticket_id == None,    # ← Only show parent tickets, not children
    ).order_by(Ticket.created_at.asc()).all()

    return jsonify({"success": True, "data": [t.to_dict() for t in tickets]}), 200


@team_lead_bp.route('/tickets/<int:ticket_id>/related-reports', methods=['GET'])
@roles_required('TEAM_LEAD')
def get_related_reports(ticket_id):
    """
    Returns all child tickets linked to a parent ticket.
    Used by the Team Lead dashboard "Related Reports" panel.

    Only shows children belonging to the Team Lead's department.
    """
    dept_id = (
        current_user.team_lead_profile.department_id
        if current_user.team_lead_profile else None
    )
    if not dept_id:
        return jsonify({"success": False, "message": "Team Lead has no department assigned"}), 403

    # Verify the parent ticket belongs to this TL's department
    parent = Ticket.query.get_or_404(ticket_id)
    if parent.department_id != dept_id:
        return jsonify({"success": False, "message": "Access denied: ticket belongs to a different department"}), 403

    children = Ticket.query.filter_by(parent_ticket_id=ticket_id).order_by(Ticket.created_at.asc()).all()

    child_data = []
    for child in children:
        child_data.append({
            "id": child.id,
            "ticket_number": child.ticket_number,
            "title": child.title,
            "created_by": child.created_by,
            "created_by_name": child.creator.full_name if child.creator else None,
            "status": child.status,
            "created_at": child.created_at.isoformat() + "+00:00" if child.created_at else None,
            "location": child.location,
        })

    return jsonify({
        "success": True,
        "parent_ticket_number": parent.ticket_number,
        "affected_users": len(child_data),
        "data": child_data
    }), 200


@team_lead_bp.route('/approve-ticket', methods=['POST'])
@roles_required('TEAM_LEAD')
def approve_ticket():
    """
    Team Lead approves an OPEN ticket from their department.
    Status becomes IN_PROGRESS so agents can see and accept it.
    assigned_to stays NULL — agents self-assign via accept action.
    """
    data = request.get_json()
    ticket_id = data.get('ticket_id')

    if not ticket_id:
        return jsonify({"success": False, "message": "ticket_id is required"}), 400

    ticket = Ticket.query.get_or_404(ticket_id)

    # Must be in team lead's department
    dept_id = current_user.team_lead_profile.department_id if current_user.team_lead_profile else None
    if ticket.department_id != dept_id:
        return jsonify({"success": False, "message": "Ticket does not belong to your department"}), 403

    # Only OPEN tickets can be approved
    if ticket.status != 'OPEN':
        return jsonify({"success": False, "message": f"Ticket is already {ticket.status}, cannot approve"}), 400

    ticket.status = 'APPROVED'
    ticket.approved_by = current_user.id
    ticket.approved_at = datetime.now(timezone.utc)
    ticket.updated_at = datetime.now(timezone.utc)

    try:
        from app.services.audit_service import AuditService
        from app.utils.logging_utils import log_activity
        AuditService.log_action(
            f"TL_APPROVED: Ticket approved and made visible to agents",
            current_user.id, ticket.id
        )
        log_activity(
            user_id=current_user.id,
            action_type="TICKET_APPROVED",
            entity_type="TICKET",
            entity_id=ticket.id,
            description=f"Ticket approved by Team Lead {current_user.full_name}"
        )
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Ticket approved — now visible to agents in the pool",
            "data": ticket.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@team_lead_bp.route('/assign-ticket', methods=['POST'])
@roles_required('TEAM_LEAD')
def assign_ticket():
    """
    Team Lead assigns a ticket to a specific agent within their department.
    All child tickets of the assigned parent are automatically assigned too.
    """
    data = request.get_json()
    ticket_id = data.get('ticket_id')
    agent_id = data.get('agent_id')

    if not all([ticket_id, agent_id]):
        return jsonify({"success": False, "message": "Missing ticket_id or agent_id"}), 400

    ticket = Ticket.query.get_or_404(ticket_id)
    agent = User.query.get_or_404(agent_id)

    # 0. DEPT ISOLATION: Ticket must belong to THIS Team Lead's department
    tl_dept = current_user.team_lead_profile.department_id if current_user.team_lead_profile else None
    if ticket.department_id != tl_dept:
        return jsonify({"success": False, "message": "Access denied: ticket belongs to a different department"}), 403

    # 1. Validation: Is the target user actually an agent?
    if not agent.role or agent.role.name != 'AGENT':
        return jsonify({"success": False, "message": "Can only assign tickets to Support Agents"}), 400

    # 2. Validation: Does the agent belong to the same department as the ticket?
    agent_dept = agent.agent_profile.department_id if agent.agent_profile else None
    if agent_dept != ticket.department_id:
        return jsonify({"success": False, "message": "Agent belongs to a different department — cross-department assignment rejected"}), 403

    # 4. Perform Assignment on parent ticket
    ticket.assigned_to = agent_id
    ticket.status = 'IN_PROGRESS'
    ticket.assigned_at = datetime.now(timezone.utc)
    ticket.accepted_at = datetime.now(timezone.utc) # Automatically "accept" on behalf of agent for immediate visibility
    ticket.updated_at = datetime.now(timezone.utc)

    # ── Propagate assignment to all child tickets ────────────────────────────
    Ticket.query.filter_by(parent_ticket_id=ticket_id).update({
        "assigned_to": agent_id,
        "status": "IN_PROGRESS",
        "assigned_at": datetime.now(timezone.utc),
        "accepted_at": datetime.now(timezone.utc), # Sync accepted_at
        "updated_at": datetime.now(timezone.utc)
    }, synchronize_session=False)

    try:
        from app.services.audit_service import AuditService
        from app.utils.logging_utils import log_activity
        AuditService.log_action(f"TL_ASSIGNED: Ticket assigned to agent {agent.full_name}", current_user.id, ticket.id)
        
        log_activity(
            user_id=current_user.id,
            action_type="TICKET_ASSIGNED",
            entity_type="TICKET",
            entity_id=ticket.id,
            description=f"Ticket assigned to agent {agent.full_name} by TL {current_user.full_name}"
        )
        
        db.session.commit()
        return jsonify({
            "success": True, 
            "message": f"Ticket assigned to {agent.full_name}",
            "data": ticket.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@team_lead_bp.route('/team-members', methods=['GET'])
@roles_required('TEAM_LEAD')
def get_team_members():
    """
    Fetch support agents belonging to the logged-in Team Lead.
    Includes agents assigned directly on their profile and those assigned via Teams.
    """
    lead_id = current_user.id

    # 1. Get IDs from direct AgentProfile assignment
    direct_ids = [p.user_id for p in AgentProfile.query.filter_by(team_lead_id=lead_id).all()]

    # 2. Get IDs from Team membership associations
    # We join TeamMember and Team where the team's lead is the current user
    team_ids = [
        row[0] for row in db.session.query(TeamMember.user_id)
        .join(Team, TeamMember.team_id == Team.id)
        .filter(Team.team_lead_id == lead_id)
        .all()
    ]

    # Combine all unique IDs
    all_agent_ids = list(set(direct_ids + team_ids))

    if not all_agent_ids:
        return jsonify({"success": True, "data": []}), 200

    # Fetch User objects for these IDs, ensuring they are actually AGENTS
    agents = User.query.join(Role).filter(
        User.id.in_(all_agent_ids),
        Role.name == "AGENT"
    ).all()

    result = []
    
    for agent in agents:
        # Only count parent tickets for workload (children are tracked through parent)
        active_count = Ticket.query.filter(
            Ticket.assigned_to == agent.id,
            Ticket.status.in_(["OPEN", "IN_PROGRESS"]),
            Ticket.parent_ticket_id == None,    # Count parent workload only
        ).count()

        resolved_today = Ticket.query.filter(
            Ticket.assigned_to == agent.id,
            Ticket.status.in_(["RESOLVED", "CLOSED"]),
            Ticket.parent_ticket_id == None,    # Count parent resolutions only
        ).count()

        profile = agent.agent_profile
        result.append({
            "id": agent.id,
            "full_name": agent.full_name,
            "email": agent.email,
            "department": profile.department.name if profile and profile.department else "",
            "location": profile.location if profile else "",
            "active_tickets": active_count,
            "resolved_today": resolved_today,
            "workload_status": f"Solved {resolved_today} tickets",
            "daily_capacity": 15
        })

    return jsonify({
        "success": True,
        "data": result
    }), 200
