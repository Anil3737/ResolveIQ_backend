from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, current_user
from app.models.feedback import Feedback
from app.models.ticket import Ticket
from app.extensions import db
from app.utils.decorators import roles_required
from datetime import datetime

feedback_bp = Blueprint('feedback', __name__)

@feedback_bp.route('/<int:ticket_id>/feedback', methods=['POST'])
@roles_required('EMPLOYEE')
def create_feedback(ticket_id):
    data = request.get_json()
    rating = data.get('rating')
    comments = data.get('comments')
    suggestions = data.get('suggestions') # Expected to be a list of strings

    if not rating:
        return jsonify({"success": False, "message": "Rating is required"}), 400

    ticket = Ticket.query.get_or_404(ticket_id)
    
    # Requirement: status must be RESOLVED
    if ticket.status.upper() != 'RESOLVED':
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

@feedback_bp.route('/<int:ticket_id>/feedback', methods=['GET'])
@jwt_required()
def get_feedback(ticket_id):
    feedback = Feedback.query.filter_by(ticket_id=ticket_id).first()
    if not feedback:
        return jsonify({"success": True, "data": None}), 200
    
    return jsonify({"success": True, "data": feedback.to_dict()}), 200
