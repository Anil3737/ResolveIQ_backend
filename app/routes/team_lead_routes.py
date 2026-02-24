from flask import Blueprint, request, jsonify
from flask_jwt_extended import current_user
from app.models.ticket import Ticket
from app.models.user import User, AgentProfile
from app.utils.decorators import roles_required
from app.extensions import db
from datetime import datetime

team_lead_bp = Blueprint('team_lead', __name__)

@team_lead_bp.route('/assign-ticket', methods=['POST'])
@roles_required('TEAM_LEAD')
def assign_ticket():
    """
    Team Lead assigns a ticket to an agent within their department.
    """
    data = request.get_json()
    ticket_id = data.get('ticket_id')
    agent_id = data.get('agent_id')

    if not all([ticket_id, agent_id]):
        return jsonify({"success": False, "message": "Missing ticket_id or agent_id"}), 400

    ticket = Ticket.query.get_or_404(ticket_id)
    agent = User.query.get_or_404(agent_id)

    # 1. Validation: Is the target user actually an agent?
    if agent.role.name != 'AGENT':
        return jsonify({"success": False, "message": "Can only assign tickets to Support Agents"}), 400

    # 2. Validation: Does the agent belong to the same department as the ticket?
    if agent.agent_profile.department_id != ticket.department_id:
        return jsonify({"success": False, "message": "Agent belongs to a different department"}), 400

    # 3. Validation: Does the agent belong to THIS Team Lead?
    if agent.agent_profile.team_lead_id != current_user.id:
        return jsonify({"success": False, "message": "This agent is not in your team"}), 400

    # 4. Perform Assignment
    ticket.assigned_to = agent_id
    ticket.status = 'IN_PROGRESS'
    ticket.updated_at = datetime.utcnow()

    try:
        from app.services.audit_service import AuditService
        AuditService.log_action(f"TL_ASSIGNED: Ticket assigned to agent {agent.full_name}", current_user.id, ticket.id)
        db.session.commit()
        return jsonify({
            "success": True, 
            "message": f"Ticket assigned to {agent.full_name}",
            "data": ticket.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
