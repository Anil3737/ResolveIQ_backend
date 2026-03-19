from flask import Blueprint, request, jsonify
from flask_jwt_extended import current_user
from app.models.system_activity_log import SystemActivityLog
from app.models.user import User, AgentProfile, TeamLeadProfile
from app.utils.decorators import roles_required
from app.extensions import db
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

activity_bp = Blueprint('activity', __name__)

@activity_bp.route('/team-lead/activity-log', methods=['GET'])
@roles_required('TEAM_LEAD')
def get_team_activity_log():
    """
    STRICT: Returns ONLY activity logs for users in the Team Lead's department.
    """
    if not current_user.team_lead_profile:
        return jsonify({"success": False, "message": "User is not a Team Lead or has no profile"}), 403
    
    dept_id = current_user.team_lead_profile.department_id
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    # Query logs
    # We join with User and then check AgentProfile or TeamLeadProfile for department_id
    query = SystemActivityLog.query.join(User, SystemActivityLog.user_id == User.id)
    
    # Filtering by department:
    # Action taken by someone in the same department
    # Note: System logs (user_id IS NULL) are excluded here as per "team activity" requirement
    # unless we want to show system actions related to their department's tickets.
    # The requirement says "team activity of the related team only".
    
    # Filter for users in the same department
    query = query.filter(
        db.or_(
            User.agent_profile.has(AgentProfile.department_id == dept_id),
            User.team_lead_profile.has(TeamLeadProfile.department_id == dept_id)
        )
    )
    
    pagination = query.order_by(SystemActivityLog.created_at.desc()).paginate(
        page=page, per_page=limit, error_out=False
    )
    
    logs = [log.to_dict() for log in pagination.items]
    
    return jsonify({
        "success": True,
        "total": pagination.total,
        "page": page,
        "pages": pagination.pages,
        "limit": limit,
        "logs": logs
    }), 200
