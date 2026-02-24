from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, current_user
from app.services.ticket_service import TicketService
from app.models.ticket import Ticket
from app.utils.decorators import roles_required
from app.extensions import db

ticket_bp = Blueprint('tickets', __name__)

@ticket_bp.route('', methods=['POST'])
@roles_required('EMPLOYEE')
def create_ticket():
    data = request.get_json()
    user_id = current_user.id
    ticket = TicketService.create_ticket(data, user_id)
    return jsonify({"success": True, "data": ticket.to_dict()}), 201

@ticket_bp.route('', methods=['GET'])
@jwt_required()
def get_tickets():
    user_id = current_user.id
    user_role = current_user.role.name if current_user.role else "EMPLOYEE"

    if user_role == 'EMPLOYEE':
        # Employees see only their created tickets
        tickets = Ticket.query.filter_by(created_by=user_id).order_by(Ticket.created_at.desc()).all()
    elif user_role == 'TEAM_LEAD':
        # Team Leads see tickets assigned to them OR tickets in their department
        dept_id = current_user.team_lead_profile.department_id if current_user.team_lead_profile else None
        tickets = Ticket.query.filter(
            (Ticket.assigned_to == user_id) | (Ticket.department_id == dept_id)
        ).order_by(Ticket.created_at.desc()).all()
    elif user_role == 'AGENT':
        # Agents see only tickets assigned to them
        tickets = Ticket.query.filter_by(assigned_to=user_id).order_by(Ticket.created_at.desc()).all()
    elif user_role == 'ADMIN':
        # Admins see all tickets
        tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    else:
        # Fallback
        tickets = Ticket.query.filter_by(created_by=user_id).all()

    return jsonify({"success": True, "data": [t.to_dict() for t in tickets]}), 200

@ticket_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    return jsonify({"success": True, "data": ticket.to_dict()}), 200

@ticket_bp.route('/<int:id>/assign', methods=['PATCH'])
@roles_required('TEAM_LEAD')
def assign_ticket(id):
    data = request.get_json()
    agent_id = data.get('agent_id')
    user_id = int(get_jwt_identity())
    ticket = TicketService.assign_ticket(id, agent_id, user_id)
    return jsonify({"success": True, "data": ticket.to_dict()}), 200

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
            "data": ticket.to_dict()
        }), 200
    except (ValueError, PermissionError) as e:
        return jsonify({"success": False, "message": str(e)}), 403
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@ticket_bp.route('/<int:id>', methods=['DELETE'])
@roles_required('ADMIN')
def delete_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    db.session.delete(ticket)
    db.session.commit()
    return jsonify({"success": True, "message": "Ticket deleted"}), 200
