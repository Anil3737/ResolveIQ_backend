from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, current_user
from app.services.ticket_service import TicketService
from app.models.ticket import Ticket
from app.models.feedback import Feedback
from app.utils.decorators import roles_required
from app.utils.dept_isolation import apply_dept_filter
from app.extensions import db
from datetime import datetime, timedelta

ticket_bp = Blueprint('tickets', __name__)

APPROVAL_WINDOW_MINUTES = 15

@ticket_bp.route('', methods=['POST'])
@roles_required('EMPLOYEE')
def create_ticket():
    data = request.get_json()
    user_id = current_user.id
    ticket = TicketService.create_ticket(data, user_id)
    return jsonify({"success": True, "data": ticket.to_dict(role="EMPLOYEE")}), 201

@ticket_bp.route('', methods=['GET'])
@jwt_required()
def get_tickets():
    user_id = current_user.id
    user_role = current_user.role.name if current_user.role else "EMPLOYEE"
    limit = request.args.get('limit', type=int)

    if user_role == 'EMPLOYEE':
        # Employees see only their own tickets
        query = Ticket.query.filter_by(created_by=user_id).order_by(Ticket.created_at.desc())
        if limit:
            query = query.limit(limit)
        tickets = query.all()

    elif user_role == 'TEAM_LEAD':
        # Team Lead sees ALL tickets in their department (all statuses)
        # for tracking purposes. Strict "OPEN+unassigned" view is at /team-lead/my-tickets
        dept_id = current_user.team_lead_profile.department_id if current_user.team_lead_profile else None
        query = Ticket.query.filter(Ticket.department_id == dept_id).order_by(Ticket.created_at.desc())
        if limit:
            query = query.limit(limit)
        tickets = query.all()

    elif user_role == 'AGENT':
        # STRICT: Agents see only:
        #   1. Tickets assigned directly to them (any status)
        #   2. Unassigned APPROVED tickets in their department
        dept_id = current_user.agent_profile.department_id if current_user.agent_profile else None
        query = Ticket.query.filter(
            Ticket.department_id == dept_id,
            db.or_(
                # Rule 1: Assigned to self
                Ticket.assigned_to == user_id,
                # Rule 2: Unassigned APPROVED pool only
                db.and_(
                    Ticket.assigned_to == None,
                    Ticket.status == 'APPROVED'
                )
            )
        ).order_by(Ticket.created_at.desc())
        if limit:
            query = query.limit(limit)
        tickets = query.all()

    elif user_role == 'ADMIN':
        # Admin unrestricted — sees all tickets globally
        dept_id_filter = request.args.get('department_id', type=int)
        escalated_filter = request.args.get('escalated', 'false').lower() == 'true'
        
        query = Ticket.query
        if dept_id_filter:
            query = query.filter(Ticket.department_id == dept_id_filter)
        
        if escalated_filter:
            query = query.filter(
                db.or_(
                    Ticket.escalation_required == True,
                    Ticket.status == 'ESCALATED'
                )
            )
            
        query = query.order_by(Ticket.created_at.desc())
        if limit:
            query = query.limit(limit)
        tickets = query.all()
    else:
        tickets = Ticket.query.filter_by(created_by=user_id).all()

    return jsonify({"success": True, "data": [t.to_dict(role=user_role) for t in tickets]}), 200

def _build_progress(ticket):
    """
    Derives a 6-stage progress object using existing columns and timestamps.
    Stages: Created -> Approved -> Assigned -> Accepted -> Resolved -> Closed
    """
    # 1. Created
    progress = {
        "created": {"status": True, "timestamp": ticket.created_at.isoformat() + "+00:00"}
    }

    # 2. Approved
    is_approved = ticket.status not in ['OPEN'] or ticket.approved_at is not None
    progress["approved"] = {
        "status": is_approved,
        "timestamp": ticket.approved_at.isoformat() + "+00:00" if ticket.approved_at else None
    }

    # 3. Assigned
    is_assigned = (ticket.assigned_to is not None) or (ticket.assigned_at is not None)
    progress["assigned"] = {
        "status": is_assigned,
        "timestamp": ticket.assigned_at.isoformat() + "+00:00" if ticket.assigned_at else None
    }

    # 4. Accepted
    is_accepted = ticket.status in ['IN_PROGRESS', 'RESOLVED', 'CLOSED'] and ticket.accepted_at is not None
    progress["accepted"] = {
        "status": is_accepted,
        "timestamp": ticket.accepted_at.isoformat() + "+00:00" if ticket.accepted_at else None
    }

    # 5. Resolved
    is_resolved = ticket.status in ['RESOLVED', 'CLOSED'] or ticket.resolved_at is not None
    progress["resolved"] = {
        "status": is_resolved,
        "timestamp": ticket.resolved_at.isoformat() + "+00:00" if ticket.resolved_at else None
    }

    # 6. Closed
    is_closed = ticket.status == 'CLOSED' or ticket.closed_at is not None
    progress["closed"] = {
        "status": is_closed,
        "timestamp": ticket.closed_at.isoformat() + "+00:00" if ticket.closed_at else None
    }

    return progress

@ticket_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_ticket(id):
    ticket = Ticket.query.get_or_404(id)

    user_id   = current_user.id
    user_role = current_user.role.name if current_user.role else "EMPLOYEE"

    # EMPLOYEE — can only view tickets they created
    if user_role == "EMPLOYEE":
        if ticket.created_by != user_id:
            return jsonify({"success": False, "message": "Access denied"}), 403

    # AGENT — strict: only assigned-to-self OR unassigned APPROVED in same dept
    elif user_role == "AGENT":
        agent_dept = current_user.agent_profile.department_id if current_user.agent_profile else None
        if ticket.department_id != agent_dept:
            return jsonify({"success": False, "message": "Access denied: ticket belongs to a different department"}), 403
        is_visible = (
            ticket.assigned_to == user_id or
            (ticket.assigned_to is None and ticket.status == 'APPROVED')
        )
        if not is_visible:
            return jsonify({"success": False, "message": "Access denied"}), 403

    # TEAM_LEAD — can only view tickets in their department
    elif user_role == "TEAM_LEAD":
        tl_dept = (
            current_user.team_lead_profile.department_id
            if current_user.team_lead_profile else None
        )
        if ticket.department_id != tl_dept:
            return jsonify({"success": False, "message": "Access denied: ticket belongs to a different department"}), 403

    # ADMIN — unrestricted access

    ticket_dict = ticket.to_dict(role=user_role)
    if user_role == "AGENT":
        # can_accept if:
        # 1. Unassigned APPROVED pool ticket (original logic)
        # OR 
        # 2. Directly assigned to user but NOT YET accepted (accepted_at is None)
        ticket_dict['can_accept']  = (
            (ticket.assigned_to is None and ticket.status == 'APPROVED') or
            (ticket.assigned_to == user_id and ticket.accepted_at is None)
        )
        ticket_dict['can_decline'] = (ticket.assigned_to == user_id)
        ticket_dict['can_resolve'] = (ticket.assigned_to == user_id and ticket.status == 'IN_PROGRESS')

    return jsonify({
        "success": True,
        "data": ticket_dict,
        "progress": _build_progress(ticket)
    }), 200

@ticket_bp.route('/<int:id>/assign', methods=['PATCH'])
@roles_required('TEAM_LEAD')
def assign_ticket(id):
    """
    Team Lead direct assignment via PATCH. Validates dept isolation before assigning.
    """
    data = request.get_json()
    agent_id = data.get('agent_id')
    user_id = int(get_jwt_identity())

    ticket = Ticket.query.get_or_404(id)

    # DEPT ISOLATION: TL can only assign tickets from their own department
    tl_dept = (
        current_user.team_lead_profile.department_id
        if current_user.team_lead_profile else None
    )
    if ticket.department_id != tl_dept:
        return jsonify({"success": False, "message": "Access denied: ticket belongs to a different department"}), 403

    # Validate agent is in same department
    from app.models.user import User
    agent = User.query.get_or_404(agent_id)
    agent_dept = agent.agent_profile.department_id if agent.agent_profile else None
    if agent_dept != ticket.department_id:
        return jsonify({"success": False, "message": "Agent belongs to a different department — cross-department assignment rejected"}), 403

    ticket = TicketService.assign_ticket(id, agent_id, user_id)
    return jsonify({"success": True, "data": ticket.to_dict(role="TEAM_LEAD")}), 200

@ticket_bp.route('/update-status', methods=['POST'])
@jwt_required()
def update_ticket_status():
    data = request.get_json()
    ticket_id = data.get('ticket_id')
    new_status = data.get('new_status')
    
    if not all([ticket_id, new_status]):
        return jsonify({"success": False, "message": "Missing ticket_id or new_status"}), 400
        
    try:
        ticket = TicketService.update_ticket_status(ticket_id, new_status, current_user)
        return jsonify({
            "success": True, 
            "data": ticket.to_dict(role=current_user.role.name if current_user.role else "EMPLOYEE")
        }), 200
    except (ValueError, PermissionError) as e:
        return jsonify({"success": False, "message": str(e)}), 403
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@ticket_bp.route('/<int:id>/resolve-escalation', methods=['POST'])
@roles_required('ADMIN')
def resolve_escalation(id):
    """
    Clears the escalation flag for a ticket.
    """
    ticket = TicketService.resolve_escalation(id, current_user.id)
    return jsonify({"success": True, "data": ticket.to_dict(role="ADMIN")}), 200

@ticket_bp.route('/<int:id>', methods=['DELETE'])
@roles_required('ADMIN')
def delete_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    ticket_num = ticket.ticket_number
    db.session.delete(ticket)
    
    from app.utils.logging_utils import log_activity
    log_activity(
        user_id=current_user.id,
        action_type="TICKET_DELETED",
        entity_type="TICKET",
        entity_id=id,
        description=f"Admin deleted ticket {ticket_num}"
    )
    
    db.session.commit()
    return jsonify({"success": True, "message": "Ticket deleted"}), 200

@ticket_bp.route('/<int:ticket_id>/feedback', methods=['POST'])
@roles_required('EMPLOYEE')
def create_feedback(ticket_id):
    data = request.get_json()
    rating = data.get('rating')
    comments = data.get('comments')
    suggestions = data.get('suggestions') # Expected to be a list of strings

    if not rating:
        return jsonify({"success": False, "message": "Rating is required"}), 400

    ticket = Ticket.query.get_or_404(ticket_id)
    
    # Requirement: status must be RESOLVED or CLOSED
    valid_statuses = ['RESOLVED', 'CLOSED']
    if ticket.status.upper() not in valid_statuses:
         return jsonify({"success": False, "message": "Feedback can only be provided for resolved tickets"}), 400

    # Requirement: only the creator can provide feedback
    if ticket.created_by != current_user.id:
        return jsonify({"success": False, "message": "You can only provide feedback for tickets you created"}), 403

    # Check if feedback already exists
    existing_feedback = Feedback.query.filter_by(ticket_id=ticket_id, user_id=current_user.id).first()
    if existing_feedback:
        return jsonify({"success": False, "message": "Feedback for this ticket has already been submitted"}), 400

    new_feedback = Feedback(
        ticket_id=ticket_id,
        user_id=current_user.id,
        rating=rating,
        comments=comments,
        suggestions=suggestions
    )

    db.session.add(new_feedback)
    db.session.commit()

    return jsonify({"success": True, "data": new_feedback.to_dict()}), 201

@ticket_bp.route('/<int:ticket_id>/feedback', methods=['GET'])
@jwt_required()
def get_feedback(ticket_id):
    feedback = Feedback.query.filter_by(ticket_id=ticket_id).first()
    if not feedback:
        return jsonify({"success": True, "data": None}), 200
    
    return jsonify({"success": True, "data": feedback.to_dict()}), 200
