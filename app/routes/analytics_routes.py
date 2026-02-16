from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.models.ticket import Ticket
from app.extensions import db
from sqlalchemy import func

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_summary():
    total_tickets = Ticket.query.count()
    status_counts = db.session.query(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status).all()
    priority_counts = db.session.query(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority).all()
    
    return jsonify({
        "success": True,
        "data": {
            "total_tickets": total_tickets,
            "status_summary": dict(status_counts),
            "priority_summary": dict(priority_counts)
        }
    }), 200
