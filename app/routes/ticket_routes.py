from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.ticket_service import TicketService
from app.models.ticket import Ticket
from app.utils.decorators import roles_required
from app.extensions import db

ticket_bp = Blueprint('tickets', __name__)

@ticket_bp.route('', methods=['POST'])
@roles_required('EMPLOYEE')
def create_ticket():
    data = request.get_json()
    user_id = get_jwt_identity().get('id')
    ticket = TicketService.create_ticket(data, user_id)
    return jsonify({"success": True, "data": ticket.to_dict()}), 201

@ticket_bp.route('', methods=['GET'])
@jwt_required()
def get_tickets():
    identity = get_jwt_identity()
    role = identity.get('role')
    user_id = identity.get('id')

    if role == 'EMPLOYEE':
        tickets = Ticket.query.filter_by(created_by=user_id).all()
    elif role == 'AGENT':
        tickets = Ticket.query.filter_by(assigned_to=user_id).all()
    else:
        tickets = Ticket.query.all()

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
    user_id = get_jwt_identity().get('id')
    ticket = TicketService.assign_ticket(id, agent_id, user_id)
    return jsonify({"success": True, "data": ticket.to_dict()}), 200

@ticket_bp.route('/<int:id>/status', methods=['PATCH'])
@roles_required('AGENT', 'TEAM_LEAD')
def update_status(id):
    data = request.get_json()
    status = data.get('status')
    user_id = get_jwt_identity().get('id')
    ticket = TicketService.update_status(id, status, user_id)
    return jsonify({"success": True, "data": ticket.to_dict()}), 200

@ticket_bp.route('/<int:id>', methods=['DELETE'])
@roles_required('ADMIN')
def delete_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    db.session.delete(ticket)
    db.session.commit()
    return jsonify({"success": True, "message": "Ticket deleted"}), 200
