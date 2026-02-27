from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, current_user
from app.models.ticket import Ticket
from app.extensions import db
from sqlalchemy import func

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_summary():
    """
    Returns ticket summary counts, scoped by the caller's role and department.

    DEPT ISOLATION:
      ADMIN      → global counts across all tickets
      TEAM_LEAD  → counts limited to their department
      AGENT      → counts limited to their department
      EMPLOYEE   → counts limited to their own created tickets
    """
    role = current_user.role.name if current_user.role else "EMPLOYEE"

    # Build the department/ownership filter predicate
    if role == "ADMIN":
        dept_filter = True  # No restriction — SQLAlchemy ignores literal True
        base_query = Ticket.query
    elif role == "TEAM_LEAD":
        dept_id = current_user.team_lead_profile.department_id if current_user.team_lead_profile else None
        base_query = Ticket.query.filter(Ticket.department_id == dept_id)
    elif role == "AGENT":
        dept_id = current_user.agent_profile.department_id if current_user.agent_profile else None
        base_query = Ticket.query.filter(Ticket.department_id == dept_id)
    else:
        # EMPLOYEE — only own tickets
        base_query = Ticket.query.filter(Ticket.created_by == current_user.id)

    total_tickets = base_query.count()

    # Scope status/priority aggregates to the same filtered set
    ticket_ids = [t.id for t in base_query.with_entities(Ticket.id).all()]

    status_counts = (
        db.session.query(Ticket.status, func.count(Ticket.id))
        .filter(Ticket.id.in_(ticket_ids))
        .group_by(Ticket.status)
        .all()
    )
    priority_counts = (
        db.session.query(Ticket.priority, func.count(Ticket.id))
        .filter(Ticket.id.in_(ticket_ids))
        .group_by(Ticket.priority)
        .all()
    )

    return jsonify({
        "success": True,
        "data": {
            "total_tickets": total_tickets,
            "status_summary": dict(status_counts),
            "priority_summary": dict(priority_counts)
        }
    }), 200
