from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user
from app.models.ticket import Ticket
from app.models.user import User
from app.extensions import db
from sqlalchemy import func, case
from datetime import datetime, timedelta, timezone

import logging
logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__)


# ─────────────────────────────────────────────
# Helper: build base query scoped by role
# ─────────────────────────────────────────────
def _base_query():
    role = current_user.role.name if current_user.role else "EMPLOYEE"
    if role == "ADMIN":
        return Ticket.query, role
    elif role == "TEAM_LEAD":
        dept_id = current_user.team_lead_profile.department_id if current_user.team_lead_profile else None
        return Ticket.query.filter(Ticket.department_id == dept_id), role
    elif role == "AGENT":
        dept_id = current_user.agent_profile.department_id if current_user.agent_profile else None
        return Ticket.query.filter(Ticket.department_id == dept_id), role
    else:
        return Ticket.query.filter(Ticket.created_by == current_user.id), role


# ─────────────────────────────────────────────
# 1. Summary  (status + priority breakdown)
# ─────────────────────────────────────────────
@analytics_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_summary():
    base_query, _ = _base_query()
    total_tickets = base_query.count()
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


# ─────────────────────────────────────────────
# 2. Tickets by Department
# ─────────────────────────────────────────────
@analytics_bp.route('/by-department', methods=['GET'])
@jwt_required()
def tickets_by_department():
    """Count total, open, resolved tickets per department."""
    try:
        from app.models.department import Department
        departments = Department.query.all()
        result = []
        for dept in departments:
            total = Ticket.query.filter_by(department_id=dept.id).count()
            if total == 0:
                continue
            open_count = Ticket.query.filter(
                Ticket.department_id == dept.id,
                Ticket.status.in_(['OPEN', 'APPROVED', 'IN_PROGRESS', 'ESCALATED'])
            ).count()
            resolved = Ticket.query.filter(
                Ticket.department_id == dept.id,
                Ticket.status.in_(['RESOLVED', 'CLOSED'])
            ).count()
            result.append({
                "department": dept.name,
                "total": total,
                "open": open_count,
                "resolved": resolved
            })
        result.sort(key=lambda x: x["total"], reverse=True)
        return jsonify({"success": True, "data": result}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ─────────────────────────────────────────────
# 3. Ticket Creation Trend  (last N days, daily)
# ─────────────────────────────────────────────
@analytics_bp.route('/trend', methods=['GET'])
@jwt_required()
def tickets_trend():
    """Daily ticket creation count for the last `days` days (default 30)."""
    try:
        days = int(request.args.get('days', 30))
        days = min(max(days, 7), 90)  # clamp 7–90
        base_query, _ = _base_query()

        start = datetime.now(timezone.utc) - timedelta(days=days)
        rows = (
            db.session.query(
                func.date(Ticket.created_at).label('day'),
                func.count(Ticket.id).label('count')
            )
            .filter(Ticket.created_at.isnot(None))
            .filter(Ticket.id.in_([t.id for t in base_query.with_entities(Ticket.id).all()]))
            .group_by(func.date(Ticket.created_at))
            .order_by(func.date(Ticket.created_at))
            .all()
        )

        # Fill gaps with 0
        day_map = {str(r.day): r.count for r in rows}
        result = []
        for i in range(days):
            d = (start + timedelta(days=i + 1)).date()
            result.append({"date": str(d), "tickets": day_map.get(str(d), 0)})

        return jsonify({"success": True, "data": result}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ─────────────────────────────────────────────
# 4. Agent Performance
# ─────────────────────────────────────────────
@analytics_bp.route('/agent-performance', methods=['GET'])
@jwt_required()
def agent_performance():
    """Per-agent: assigned, resolved, avg resolution time (hours)."""
    try:
        from app.models.role import Role
        agent_role = Role.query.filter_by(name='AGENT').first()
        if not agent_role:
            return jsonify({"success": True, "data": []}), 200

        agents = User.query.filter_by(role_id=agent_role.id, is_active=True).all()
        result = []
        for agent in agents:
            assigned = Ticket.query.filter_by(assigned_to=agent.id).count()
            if assigned == 0:
                continue
            resolved_tickets = Ticket.query.filter(
                Ticket.assigned_to == agent.id,
                Ticket.status.in_(['RESOLVED', 'CLOSED']),
                Ticket.resolved_at.isnot(None)
            ).all()
            resolved_count = len(resolved_tickets)

            # Average resolution time in hours
            avg_hours = None
            if resolved_count > 0:
                total_seconds = 0
                for t in resolved_tickets:
                    if t.resolved_at and t.created_at:
                        r_at = t.resolved_at.replace(tzinfo=timezone.utc) if t.resolved_at.tzinfo is None else t.resolved_at
                        c_at = t.created_at.replace(tzinfo=timezone.utc) if t.created_at.tzinfo is None else t.created_at
                        total_seconds += (r_at - c_at).total_seconds()
                avg_hours = round(total_seconds / 3600 / resolved_count, 1)

            resolution_rate = round((resolved_count / assigned) * 100, 1) if assigned else 0
            result.append({
                "agent": agent.full_name,
                "emp_id": agent.emp_id or "",
                "assigned": assigned,
                "resolved": resolved_count,
                "resolution_rate": resolution_rate,
                "avg_resolution_hours": avg_hours
            })

        result.sort(key=lambda x: x["resolution_rate"], reverse=True)
        return jsonify({"success": True, "data": result}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ─────────────────────────────────────────────
# 5. SLA Compliance Report
# ─────────────────────────────────────────────
@analytics_bp.route('/sla-compliance', methods=['GET'])
@jwt_required()
def sla_compliance():
    """Global SLA compliance % + per-department breakdown."""
    try:
        now = datetime.now(timezone.utc)
        base_query, _ = _base_query()
        ticket_ids = [t.id for t in base_query.with_entities(Ticket.id).all()]

        # Only tickets that have an SLA deadline set
        sla_tickets = Ticket.query.filter(
            Ticket.id.in_(ticket_ids),
            Ticket.sla_deadline.isnot(None)
        ).all()

        total_sla = len(sla_tickets)
        breached = 0
        for t in sla_tickets:
            sla_d = t.sla_deadline.replace(tzinfo=timezone.utc) if t.sla_deadline.tzinfo is None else t.sla_deadline
            if sla_d < now and t.status not in ['RESOLVED', 'CLOSED']:
                breached += 1
        
        met = total_sla - breached
        compliance_pct = round((met / total_sla) * 100, 1) if total_sla else 100.0

        # Per-department SLA compliance
        from app.models.department import Department
        departments = Department.query.all()
        dept_breakdown = []
        for dept in departments:
            dept_tickets = [t for t in sla_tickets if t.department_id == dept.id]
            if not dept_tickets:
                continue
            dept_breached = 0
            for t in dept_tickets:
                sla_d = t.sla_deadline.replace(tzinfo=timezone.utc) if t.sla_deadline.tzinfo is None else t.sla_deadline
                if sla_d < now and t.status not in ['RESOLVED', 'CLOSED']:
                    dept_breached += 1
            dept_met = len(dept_tickets) - dept_breached
            dept_pct = round((dept_met / len(dept_tickets)) * 100, 1)
            dept_breakdown.append({
                "department": dept.name,
                "total": len(dept_tickets),
                "met": dept_met,
                "breached": dept_breached,
                "compliance_pct": dept_pct
            })
        dept_breakdown.sort(key=lambda x: x["compliance_pct"])

        return jsonify({
            "success": True,
            "data": {
                "total_with_sla": total_sla,
                "met": met,
                "breached": breached,
                "compliance_pct": compliance_pct,
                "by_department": dept_breakdown
            }
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ─────────────────────────────────────────────
# 6. Feedback Summary
# ─────────────────────────────────────────────
@analytics_bp.route('/feedback-summary', methods=['GET'])
@jwt_required()
def get_feedback_summary():
    """Total feedback count, average rating and distribution per star."""
    try:
        from app.models.feedback import Feedback
        feedbacks = Feedback.query.all()
        total = len(feedbacks)

        if total == 0:
            return jsonify({
                "success": True,
                "data": {
                    "total_feedbacks": 0,
                    "avg_rating": 0.0,
                    "rating_distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
                    "top_suggestions": {}
                }
            }), 200

        avg_rating = round(sum(f.rating for f in feedbacks) / total, 2)

        rating_distribution = {str(i): 0 for i in range(1, 6)}
        for f in feedbacks:
            key = str(max(1, min(5, f.rating)))
            rating_distribution[key] = rating_distribution.get(key, 0) + 1

        suggestion_counts = {}
        for f in feedbacks:
            if f.suggestions:
                for s in f.suggestions:
                    suggestion_counts[s] = suggestion_counts.get(s, 0) + 1

        # Return top 5 suggestions
        top_suggestions = dict(sorted(suggestion_counts.items(), key=lambda x: x[1], reverse=True)[:5])

        return jsonify({
            "success": True,
            "data": {
                "total_feedbacks": total,
                "avg_rating": avg_rating,
                "rating_distribution": rating_distribution,
                "top_suggestions": top_suggestions
            }
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
