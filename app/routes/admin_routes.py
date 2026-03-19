from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, current_user
from app.utils.decorators import roles_required
from app.models.user import User
from app.models.role import Role
from app.models.audit_log import AuditLog
from app.models.system_activity_log import SystemActivityLog
from app.models.department import Department
from app.services.auth_service import AuthService
from app.models.team import Team
from app.models.team_member import TeamMember
from app.extensions import db
from app.utils.logging_utils import log_activity
from app.models import PasswordResetRequest
from app.utils.password_utils import hash_password
import logging
import re
import random
import string
import secrets
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/create-user', methods=['POST'])
@roles_required('ADMIN')
def create_user():
    data = request.get_json()
    user, message = AuthService.register_user(data, creator_id=current_user.id)
    if user:
        return jsonify({"success": True, "message": message, "data": user.to_dict()}), 201
    return jsonify({"success": False, "message": message}), 400

@admin_bp.route('/check-id', methods=['GET'])
@roles_required('ADMIN')
def check_id_exists():
    emp_id = request.args.get('emp_id', '').strip()
    if not emp_id:
        return jsonify({"success": False, "message": "emp_id is required"}), 400
    
    # Check emp_id column
    user = User.query.filter_by(emp_id=emp_id).first()
    return jsonify({"success": True, "exists": user is not None}), 200

@admin_bp.route('/users', methods=['GET'])
@roles_required('ADMIN')
def get_users():
    role_filter = request.args.get('role')
    dept_id = request.args.get('department_id', type=int)
    exclude_assigned = request.args.get('exclude_assigned', 'false').lower() == 'true'
    
    query = User.query
    
    if role_filter:
        query = query.join(User.role).filter(Role.name == role_filter.upper())
    
    if dept_id:
        # Join with AgentProfile or TeamLeadProfile depending on role if possible,
        # but User.to_dict() already handles role-specific data.
        # We'll filter based on the profile's department_id.
        from app.models.user import TeamLeadProfile, AgentProfile
        if role_filter == 'TEAM_LEAD':
            query = query.join(TeamLeadProfile).filter(TeamLeadProfile.department_id == dept_id)
        elif role_filter == 'AGENT':
            query = query.join(AgentProfile).filter(AgentProfile.department_id == dept_id)
            
    if exclude_assigned:
        if role_filter == 'TEAM_LEAD':
            # Exclude leads who are already leading a team
            from app.models.team import Team
            query = query.filter(~User.id.in_(db.session.query(Team.team_lead_id).filter(Team.team_lead_id != None)))
        elif role_filter == 'AGENT':
            # Exclude agents who are already members of any team
            from app.models.team_member import TeamMember
            query = query.filter(~User.id.in_(db.session.query(TeamMember.user_id)))
    
    users = query.all()
    return jsonify({
        "success": True, 
        "data": [u.to_dict() for u in users]
    }), 200

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@roles_required('ADMIN')
def update_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        full_name = data.get('full_name', '').strip()
        email = data.get('email', '').strip()
        emp_id = data.get('emp_id', '').strip() # emp_id column
        role_name = data.get('role', '').upper()
        department_id = data.get('department_id')

        if full_name: user.full_name = full_name
        if email: user.email = email
        if emp_id: user.emp_id = emp_id
        # Note: department_id is stored on TeamLeadProfile/AgentProfile, not User directly.

        if role_name:
            new_role = Role.query.filter_by(name=role_name).first()
            if new_role:
                user.role_id = new_role.id

        db.session.commit()
        
        log_activity(
            user_id=current_user.id,
            action_type="UPDATE",
            entity_type="USER",
            entity_id=user.id,
            description=f"Admin updated user: {user.full_name} ({role_name})"
        )
        
        return jsonify({"success": True, "message": "User updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@roles_required('ADMIN')
def delete_user(user_id):
    try:
        if user_id == current_user.id:
            return jsonify({"success": False, "message": "Cannot delete your own account"}), 400

        user = User.query.get_or_404(user_id)
        
        # Check for active dependencies
        from app.models.ticket import Ticket
        assigned_tickets = Ticket.query.filter(
            db.or_(Ticket.assigned_to == user_id, Ticket.created_by == user_id),
            Ticket.status.notin_(['RESOLVED', 'CLOSED'])
        ).first()

        if assigned_tickets:
            return jsonify({
                "success": False, 
                "message": "Cannot delete user with active/assigned tickets. Re-assign them first."
            }), 400

        user_name = user.full_name
        db.session.delete(user)
        db.session.commit()
        
        log_activity(
            user_id=current_user.id,
            action_type="DELETE",
            entity_type="USER",
            entity_id=user_id,
            description=f"Admin deleted user: {user_name}"
        )
        
        return jsonify({"success": True, "message": "User deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@admin_bp.route('/teams', methods=['GET'])
@roles_required('ADMIN')
def get_teams():
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT t.id, t.name, t.description, t.goal, t.issue_type,
                       d.name AS department_name,
                       u.full_name AS team_lead_name,
                       t.created_at,
                       (SELECT COUNT(*) FROM team_members tm WHERE tm.team_id = t.id) AS member_count
                FROM teams t
                LEFT JOIN departments d ON t.department_id = d.id
                LEFT JOIN users u ON t.team_lead_id = u.id
                ORDER BY t.created_at DESC
            """))
            teams = []
            for row in rows.mappings():
                teams.append({
                    "id": row["id"],
                    "name": row["name"],
                    "description": row["description"] or "",
                    "goal": row["goal"] or "",
                    "issue_type": row["issue_type"] or "",
                    "department": row["department_name"] or "N/A",
                    "team_lead": row["team_lead_name"] or "Unassigned",
                    "member_count": row["member_count"] or 0,
                    "created_at": str(row["created_at"]) if row["created_at"] else ""
                })
        return jsonify({"success": True, "data": teams}), 200
    except Exception as e:
        logger.error(f"Error fetching teams: {e}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500

@admin_bp.route('/teams', methods=['POST'])
@roles_required('ADMIN')
def create_team():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400

        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        goal = data.get('goal', '').strip()
        issue_type = data.get('issue_type', '').strip()
        department_id = data.get('department_id')
        team_lead_id = data.get('team_lead_id')
        agent_ids = data.get('agent_ids', []) # List of user IDs

        if not name:
            return jsonify({"success": False, "message": "Team name is required"}), 400

        # Check if team name already exists
        if Team.query.filter_by(name=name).first():
            return jsonify({"success": False, "message": f"Team '{name}' already exists"}), 400

        new_team = Team(
            name=name,
            description=description,
            goal=goal,
            issue_type=issue_type,
            department_id=department_id,
            team_lead_id=team_lead_id
        )

        db.session.add(new_team)
        db.session.flush() # Get the ID for auditing and members

        # Add assigned agents
        if agent_ids:
            logger.info(f"Processing {len(agent_ids)} agents for team {new_team.id}")
            from app.models.user import AgentProfile
            for agent_id in agent_ids:
                # 1. Store association in TeamMember table
                member = TeamMember(team_id=new_team.id, user_id=agent_id)
                db.session.add(member)
                
                # 2. Update AgentProfile to officially link to the Team Lead
                agent_profile = AgentProfile.query.filter_by(user_id=agent_id).first()
                if agent_profile:
                    agent_profile.team_lead_id = team_lead_id
                    logger.debug(f"Updated AgentProfile for User {agent_id} (Team Lead: {team_lead_id})")
                else:
                    logger.warning(f"No AgentProfile found for User {agent_id}")
        else:
            logger.info("No agent_ids provided in request")

        log_activity(
            user_id=current_user.id,
            action_type="CREATE",
            entity_type="TEAM",
            entity_id=new_team.id,
            description=f"Admin created team: {name}"
        )

        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": "Team created successfully",
            "data": {
                "id": new_team.id,
                "name": new_team.name,
                "description": new_team.description,
                "goal": new_team.goal,
                "issue_type": new_team.issue_type
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"ERROR in create_team: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500

@admin_bp.route('/teams/<int:team_id>', methods=['GET'])
@roles_required('ADMIN')
def get_team_detail(team_id):
    try:
        team = Team.query.get_or_404(team_id)
        from app.models.department import Department
        dept = db.session.get(Department, team.department_id) if team.department_id else None
        # Get lead for specific metrics
        lead = db.session.get(User, team.team_lead_id) if team.team_lead_id else None
        
        return jsonify({
            "success": True,
            "data": {
                "id": team.id,
                "name": team.name,
                "description": team.description or "",
                "goal": team.goal or "",
                "issue_type": team.issue_type or "",
                "department_id": team.department_id,
                "department_name": dept.name if dept else "N/A",
                "team_lead_id": team.team_lead_id,
                "team_lead_name": lead.full_name if lead else "Unassigned",
                "created_at": str(team.created_at)
            }
        }), 200
    except Exception as e:
        logger.error(f"Error fetching team detail: {e}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500

@admin_bp.route('/teams/<int:team_id>/members', methods=['GET'])
@roles_required('ADMIN')
def get_admin_team_members(team_id):
    try:
        # Fetch all users associated with this team via TeamMember table
        members = User.query.join(TeamMember, User.id == TeamMember.user_id)\
                            .filter(TeamMember.team_id == team_id).all()
        
        logger.info(f"Team {team_id}: Found {len(members)} members")
        
        return jsonify({
            "success": True,
            "data": [m.to_dict() for m in members]
        }), 200
    except Exception as e:
        logger.error(f"ERROR fetching team members: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500

@admin_bp.route('/teams/<int:team_id>', methods=['PUT'])
@roles_required('ADMIN')
def update_team(team_id):
    try:
        team = Team.query.get_or_404(team_id)
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400

        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        goal = data.get('goal', '').strip()
        issue_type = data.get('issue_type', '').strip()
        department_id = data.get('department_id')
        team_lead_id = data.get('team_lead_id')
        agent_ids = data.get('agent_ids', [])

        if not name:
            return jsonify({"success": False, "message": "Team name is required"}), 400

        # Check if name is taken by another team
        existing_team = Team.query.filter(Team.name == name, Team.id != team_id).first()
        if existing_team:
            return jsonify({"success": False, "message": f"Team name '{name}' already exists"}), 400

        # --- SYNC LOGIC FOR TEAM LEAD MODULE ---
        from app.models.user import AgentProfile
        
        # 1. Identify current members before clearing
        old_member_ids = [m.user_id for m in TeamMember.query.filter_by(team_id=team.id).all()]
        
        # 2. Clear existing associations for this team
        TeamMember.query.filter_by(team_id=team.id).delete()
        
        # 3. For members removed from the team, clear their team_lead_id in AgentProfile
        # But only if they were actually in THIS team
        removed_ids = set(old_member_ids) - set(agent_ids)
        for removed_id in removed_ids:
            agent_profile = AgentProfile.query.filter_by(user_id=removed_id).first()
            if agent_profile and agent_profile.team_lead_id == team.team_lead_id:
                agent_profile.team_lead_id = None
                logger.info(f"Cleared Team Lead for removed agent {removed_id}")

        # 4. Update team details
        team.name = name
        team.description = description
        team.goal = goal
        team.issue_type = issue_type
        team.department_id = department_id
        team.team_lead_id = team_lead_id

        # 5. Add/Update members
        for agent_id in agent_ids:
            # Re-add association
            new_member = TeamMember(team_id=team.id, user_id=agent_id)
            db.session.add(new_member)
            
            # Sync AgentProfile to the new Team Lead and Department
            agent_profile = AgentProfile.query.filter_by(user_id=agent_id).first()
            if agent_profile:
                agent_profile.team_lead_id = team_lead_id
                agent_profile.department_id = department_id
        
        log_activity(
            user_id=current_user.id,
            action_type="UPDATE",
            entity_type="TEAM",
            entity_id=team.id,
            description=f"Admin updated team: {name}"
        )

        db.session.commit()
        return jsonify({"success": True, "message": "Team updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"ERROR updating team: {e}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500

@admin_bp.route('/teams/<int:team_id>', methods=['DELETE'])
@roles_required('ADMIN')
def delete_team(team_id):
    try:
        team = Team.query.get_or_404(team_id)
        team_name = team.name

        from app.models.user import AgentProfile
        # Clear Team Lead linkage for all members of this team
        members = TeamMember.query.filter_by(team_id=team_id).all()
        for member in members:
            agent_profile = AgentProfile.query.filter_by(user_id=member.user_id).first()
            if agent_profile and agent_profile.team_lead_id == team.team_lead_id:
                agent_profile.team_lead_id = None

        # Clear associations
        TeamMember.query.filter_by(team_id=team_id).delete()
        
        db.session.delete(team)

        # Log Activity
        log_activity(
            user_id=current_user.id,
            action_type="DELETE",
            entity_type="TEAM",
            entity_id=team_id,
            description=f"Admin deleted team: {team_name}"
        )

        db.session.commit()
        return jsonify({"success": True, "message": f"Team '{team_name}' deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"ERROR deleting team: {e}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500

@admin_bp.route('/audit-logs', methods=['GET'])
@roles_required('ADMIN')
def get_audit_logs():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    return jsonify({"success": True, "data": [l.to_dict() for l in logs]}), 200

@admin_bp.route('/departments', methods=['GET', 'POST'])
@jwt_required()
def handle_departments():
    if request.method == 'POST':
        user_role = current_user.role.name if current_user.role else "EMPLOYEE"
        if user_role != 'ADMIN':
            return jsonify({"success": False, "message": "Admin only"}), 403
        data = request.get_json()
        dept = Department(
            name=data.get('name'),
            description=data.get('description', '')
        )
        db.session.add(dept)
        db.session.commit()
        
        log_activity(
            user_id=current_user.id,
            action_type="CREATE",
            entity_type="DEPARTMENT",
            entity_id=dept.id,
            description=f"Admin created department: {dept.name}"
        )
        
        return jsonify({"success": True, "data": dept.to_dict()}), 201
    
    from sqlalchemy import text
    with db.engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT d.id, d.name, d.description, d.created_at,
                   (SELECT COUNT(*) FROM teams t WHERE t.department_id = d.id) AS team_count,
                   (SELECT COUNT(*) FROM tickets tk WHERE tk.department_id = d.id) AS ticket_count
            FROM departments d
            ORDER BY d.name ASC
        """)).mappings().all()
        
        departments = []
        for row in rows:
            departments.append({
                "id": row["id"],
                "name": row["name"],
                "description": row["description"] or "",
                "created_at": str(row["created_at"]) if row["created_at"] else "",
                "team_count": row["team_count"] or 0,
                "ticket_count": row["ticket_count"] or 0
            })
            
    return jsonify({"success": True, "data": departments}), 200

@admin_bp.route('/departments/<int:dept_id>', methods=['PUT', 'DELETE'])
@roles_required('ADMIN')
def manage_department(dept_id):
    dept = Department.query.get_or_404(dept_id)
    
    if request.method == 'PUT':
        data = request.get_json()
        dept.name = data.get('name', dept.name)
        dept.description = data.get('description', dept.description)
        db.session.commit()
        
        log_activity(
            user_id=current_user.id,
            action_type="UPDATE",
            entity_type="DEPARTMENT",
            entity_id=dept.id,
            description=f"Admin updated department: {dept.name}"
        )
        
        return jsonify({"success": True, "data": dept.to_dict()}), 200
        
    if request.method == 'DELETE':
        # Check if department has associated teams or tickets
        team_exists = Team.query.filter_by(department_id=dept_id).first()
        ticket_exists = Ticket.query.filter_by(department_id=dept_id).first()
        
        if team_exists or ticket_exists:
            return jsonify({
                "success": False, 
                "message": "Cannot delete department with associated teams or tickets."
            }), 400
            
        dept_name = dept.name
        db.session.delete(dept)
        db.session.commit()
        
        log_activity(
            user_id=current_user.id,
            action_type="DELETE",
            entity_type="DEPARTMENT",
            entity_id=dept_id,
            description=f"Admin deleted department: {dept_name}"
        )
        
        return jsonify({"success": True, "message": "Department deleted successfully"}), 200

@admin_bp.route('/create-staff', methods=['POST'])
@roles_required('ADMIN')
def create_staff():
    """
    ADMIN only route to create Team Leads and Agents.
    Includes strict validation and automatic email generation.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400

        full_name = data.get('full_name', '').strip()
        emp_id = data.get('emp_id', '').strip()
        dept_name = data.get('department', '').strip()
        location = data.get('location', '').strip()
        role_input = data.get('role', '').strip()
        role_name = role_input.upper().replace(" ", "_")

        # --- VALIDATION RULES ---

        # 1. Full Name: Required, min 3 chars, only alphabets and spaces
        if not full_name or len(full_name) < 3:
            return jsonify({"success": False, "message": "Full Name is required and must be at least 3 characters"}), 400
        if not re.match(r'^[a-zA-Z\s]+$', full_name):
            return jsonify({"success": False, "message": "Full Name must contain only alphabets and spaces"}), 400

        # 2. EMP ID: Format EMPXXXX, exactly 7 chars
        if not re.match(r'^EMP\d{4}$', emp_id):
            return jsonify({"success": False, "message": "EMP ID must be in format EMPXXXX (e.g., EMP1001)"}), 400
        
        emp_num = int(emp_id[3:])
        
        # Role validation & Range check
        if role_name == 'TEAM_LEAD':
            if not (2000 <= emp_num <= 3000):
                return jsonify({"success": False, "message": "For TEAM_LEAD, EMP ID number must be between 2000 and 3000"}), 400
        elif role_name == 'AGENT':
            if not (1000 <= emp_num <= 1999):
                return jsonify({"success": False, "message": "For AGENT, EMP ID number must be between 1000 and 1999"}), 400
        else:
             return jsonify({"success": False, "message": "Role must be 'TEAM_LEAD' or 'AGENT'"}), 400

        # 3. Unique EMP ID (stored in users.emp_id column)
        if User.query.filter_by(emp_id=emp_id).first():
            return jsonify({"success": False, "message": "EMP ID already exists"}), 400

        # 4. Department: Flexible case-insensitive matching
        DEPT_NAME_MAP = {
            "network issue": "Network Issues",
            "network issues": "Network Issues",
            "hardware failure": "Hardware Failure",
            "software installation": "Software Installation",
            "application down/ application issue": "Application Down/ Application Issue",
            "application downtime / application issues": "Application Down/ Application Issue",
            "application issues": "Application Down/ Application Issue",
            "application issue": "Application Down/ Application Issue",
            "application down": "Application Down/ Application Issue",
            "others": "Others",
            "other": "Others"
        }
        
        normalized_dept = DEPT_NAME_MAP.get(dept_name.lower())
        if not normalized_dept:
             logger.warning(f"Department mapping failed for '{dept_name}'")
             return jsonify({
                 "success": False, 
                 "message": f"Invalid department '{dept_name}'. Use canonical names."
             }), 400
             
        dept = Department.query.filter_by(name=normalized_dept).first()
        if not dept:
            logger.warning(f"Department '{normalized_dept}' not in DB")
            return jsonify({"success": False, "message": f"Department '{normalized_dept}' not initialized"}), 400

        # 5. Role Lookup - Standardize names
        ROLE_MAP = {
            "TEAM_LEAD": "TEAM_LEAD",
            "TEAMLEAD": "TEAM_LEAD",
            "TEAM LEAD": "TEAM_LEAD",
            "AGENT": "AGENT",
            "SUPPORT_AGENT": "AGENT",
            "SUPPORT AGENT": "AGENT"
        }
        role_key = role_input.upper().replace(" ", "_").strip()
        role_name = ROLE_MAP.get(role_key, role_key)
        
        role_obj = Role.query.filter_by(name=role_name).first()
        if not role_obj:
            logger.warning(f"Role mapping failed for '{role_input}' -> '{role_name}'")
            return jsonify({"success": False, "message": f"Role '{role_name}' not found"}), 400

        logger.info(f"Creating staff {full_name} for dept {dept.name} with role {role_name}")

        # --- EMAIL GENERATION ---
        # Logic: first word of full name, lowercase, no spaces
        # If exists, append random 3-digit number
        first_word = full_name.split()[0].lower()
        generated_email = f"{first_word}@resolveiq.com"
        
        if User.query.filter_by(email=generated_email).first():
            # Uniqueness loop
            while True:
                random_suffix = "".join(random.choices(string.digits, k=3))
                generated_email = f"{first_word}{random_suffix}@resolveiq.com"
                if not User.query.filter_by(email=generated_email).first():
                    break
        
        # --- DATABASE SAVE ---
        staff_data = {
            "full_name": full_name,
            "email": generated_email,
            "emp_id": emp_id, # emp_id column
            "password": "Resolveiq@123",
            "role": role_name,
            "department_id": dept.id,
            "location": location,
            "require_password_change": True
        }

        user, message = AuthService.register_user(staff_data, creator_id=current_user.id)

        if user:
            # --- SUCCESS RESPONSE ---
            return jsonify({
                "success": True,
                "message": "Staff created successfully",
                "data": {
                    "full_name": user.full_name,
                    "email": user.email,
                    "emp_id": user.emp_id,
                    "role": role_name,
                    "department": dept_name
                }
            }), 201
        else:
            return jsonify({"success": False, "message": message}), 400

    except Exception as e:
        logger.error(f"ERROR in create_staff: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

@admin_bp.route('/create-agent', methods=['POST'])
@roles_required('ADMIN')
def create_agent():
    """
    ADMIN only route to create Support Agents.
    Includes strict validation for Team Leads and sequential company email generation.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400

        full_name = data.get('full_name', '').strip()
        emp_id = data.get('emp_id', '').strip()
        dept_name = data.get('department', '').strip()
        team_lead_id = data.get('team_lead_id') # Now optional
        location = data.get('location', '').strip()

        # --- VALIDATION RULES ---
        if not full_name or len(full_name) < 3:
            return jsonify({"success": False, "message": "Full Name is required and must be at least 3 characters"}), 400
        
        if not re.match(r'^EMP\d{4}$', emp_id):
            return jsonify({"success": False, "message": "EMP ID must be in format EMPXXXX (e.g., EMP1001)"}), 400
        
        emp_num = int(emp_id[3:])
        # For AGENT, EMP ID number must be between 1000 and 1999 (matches staff logic)
        if not (1000 <= emp_num <= 1999):
            return jsonify({"success": False, "message": "EMP ID number must be between 1000 and 1999"}), 400

        # 3. Department
        # Use same DEPT_NAME_MAP for consistency
        DEPT_NAME_MAP = {
            "network issue": "Network Issues",
            "network issues": "Network Issues",
            "hardware failure": "Hardware Failure",
            "software installation": "Software Installation",
            "application down/ application issue": "Application Down/ Application Issue",
            "application downtime / application issues": "Application Down/ Application Issue",
            "application issues": "Application Down/ Application Issue",
            "application issue": "Application Down/ Application Issue",
            "application down": "Application Down/ Application Issue",
            "others": "Others",
            "other": "Others"
        }
        normalized_dept = DEPT_NAME_MAP.get(dept_name.lower())
        dept = Department.query.filter_by(name=normalized_dept).first() if normalized_dept else None
        
        if not dept:
            return jsonify({"success": False, "message": f"Department '{dept_name}' not found or invalid"}), 400

        # 4. Team Lead Validation (Optional now)
        if team_lead_id:
            team_lead = db.session.get(User, team_lead_id)
            if not team_lead:
                return jsonify({"success": False, "message": "Team Lead not found"}), 400
            
            if not team_lead.role or team_lead.role.name != 'TEAM_LEAD':
                return jsonify({"success": False, "message": "Assigned user is not a Team Lead"}), 400
        else:
            team_lead = None
        
        # 5. Get Role Lookup (AGENT)
        agent_role = Role.query.filter_by(name="AGENT").first()
        if not agent_role:
             return jsonify({"success": False, "message": "Agent role not initialized"}), 500

        # --- SEQUENTIAL EMAIL GENERATION ---
        first_word = full_name.split()[0].lower()
        base_email = f"{first_word}@resolveiq.com"
        
        if not User.query.filter_by(email=base_email).first():
            generated_email = base_email
        else:
            suffix = 1
            while True:
                generated_email = f"{first_word}{suffix:03d}@resolveiq.com"
                if not User.query.filter_by(email=generated_email).first():
                    break
                suffix += 1
        
        # --- DATABASE SAVE ---
        agent_data = {
            "full_name": full_name,
            "email": generated_email,
            "emp_id": emp_id,
            "password": "Resolveiq@123",
            "role": "AGENT",
            "department_id": dept.id,
            "team_lead_id": team_lead_id,
            "location": location,
            "require_password_change": True
        }

        user, message = AuthService.register_user(agent_data, creator_id=current_user.id)

        if user:
            # --- SUCCESS RESPONSE ---
            return jsonify({
                "success": True,
                "message": "Support Agent created successfully",
                "data": {
                    "full_name": user.full_name,
                    "email": user.email,
                    "emp_id": user.emp_id,
                    "role": "AGENT",
                    "department": dept_name,
                    "team_lead": team_lead.full_name if team_lead else "Unassigned"
                }
            }), 201
        else:
            return jsonify({"success": False, "message": message}), 400

    except Exception as e:
        db.session.rollback()
        logger.error(f"ERROR in create_agent: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

# Redundant /tickets route removed - use ticket_routes.py instead

@admin_bp.route('/system-activity', methods=['GET'])
@roles_required('ADMIN')
def get_system_activity():
    """
    Fetch paginated and filterable system activity logs.
    """
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        action_type = request.args.get('action_type')
        user_id = request.args.get('user_id', type=int)
        entity_type = request.args.get('entity_type')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')

        query = SystemActivityLog.query.order_by(SystemActivityLog.created_at.desc())

        if action_type:
            query = query.filter(SystemActivityLog.action_type == action_type)
        if user_id:
            query = query.filter(SystemActivityLog.user_id == user_id)
        if entity_type:
            query = query.filter(SystemActivityLog.entity_type == entity_type)
        
        if date_from:
            try:
                df = datetime.fromisoformat(date_from)
                query = query.filter(SystemActivityLog.created_at >= df)
            except ValueError:
                pass
        
        if date_to:
            try:
                dt = datetime.fromisoformat(date_to)
                query = query.filter(SystemActivityLog.created_at <= dt)
            except ValueError:
                pass

        pagination = query.paginate(page=page, per_page=limit, error_out=False)
        logs = pagination.items

        return jsonify({
            "success": True,
            "total": pagination.total,
            "page": page,
            "pages": pagination.pages,
            "limit": limit,
            "logs": [log.to_dict() for log in logs]
        }), 200
    except Exception as e:
        logger.error(f"ERROR fetching activity logs: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500

@admin_bp.route('/dashboard', methods=['GET'])
@roles_required('ADMIN')
def get_dashboard_metrics():
    """
    Fetch comprehensive dashboard metrics, risk distribution, and top risky tickets.
    """
    try:
        from app.models.ticket import Ticket
        
        # 1. Total Tickets
        total_tickets = Ticket.query.count()
        
        # 2. High Risk Count (ai_score >= 70)
        # Matches the 'critical' + 'high' distribution logic
        high_risk_count = Ticket.query.filter(Ticket.ai_score >= 70).count()
        
        # 3. SLA Breached Count (deadline passed AND not RESOLVED/CLOSED)
        sla_breached_count = Ticket.query.filter(
            Ticket.sla_deadline < datetime.now(timezone.utc),
            Ticket.status.notin_(["RESOLVED", "CLOSED"])
        ).count()
        
        # 4. Escalated Count (escalation_required OR status == 'ESCALATED')
        escalated_count = Ticket.query.filter(
            db.or_(
                Ticket.escalation_required == True,
                Ticket.status == 'ESCALATED',
                Ticket.status == 'HIGH_RISK',
                Ticket.ai_score >= 80
            ),
            Ticket.status.notin_(["RESOLVED", "CLOSED"])
        ).count()
        
        # 5. Risk Distribution (Categorize by ai_score)
        critical = Ticket.query.filter(Ticket.ai_score >= 85).count()
        high = Ticket.query.filter(Ticket.ai_score.between(70, 84)).count()
        medium = Ticket.query.filter(Ticket.ai_score.between(40, 69)).count()
        low = Ticket.query.filter(Ticket.ai_score < 40).count()
        
        # 6. Top 5 Risky Tickets
        top_risky = Ticket.query.filter(
            Ticket.status != "CLOSED"
        ).order_by(
            Ticket.ai_score.desc()
        ).limit(5).all()
        
        return jsonify({
            "success": True,
            "metrics": {
                "total_tickets": total_tickets,
                "high_risk": high_risk_count,
                "sla_breached": sla_breached_count,
                "escalated": escalated_count,
                "pending_reset_count": PasswordResetRequest.query.filter_by(status='PENDING').count()
            },
            "risk_distribution": {
                "critical": critical,
                "high": high,
                "medium": medium,
                "low": low
            },
            "top_risky_tickets": [
                {
                    "id": t.id,
                    "ticket_number": t.ticket_number,
                    "title": t.title,
                    "status": t.status,
                    "ai_score": t.ai_score
                } for t in top_risky
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"ERROR fetching dashboard metrics: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500
@admin_bp.route('/reset-password/requests', methods=['GET'])
@roles_required('ADMIN')
def get_reset_requests():
    status = request.args.get('status', 'PENDING')
    requests = PasswordResetRequest.query.filter_by(status=status).order_by(PasswordResetRequest.requested_at.desc()).all()
    return jsonify({
        "success": True, 
        "data": [r.to_dict() for r in requests]
    }), 200

@admin_bp.route('/reset-password/approve', methods=['POST'])
@roles_required('ADMIN')
def approve_reset():
    try:
        data = request.get_json()
        request_id = data.get('request_id')
        if not request_id:
            return jsonify({"success": False, "message": "request_id is required"}), 400
            
        reset_req = db.session.get(PasswordResetRequest, request_id)
        if not reset_req:
            return jsonify({"success": False, "message": "Request not found"}), 404
            
        if reset_req.status != 'PENDING':
            return jsonify({"success": False, "message": "Request has already been processed"}), 400
            
        user = db.session.get(User, reset_req.user_id)
        if not user:
            return jsonify({"success": False, "message": "User associated with request not found"}), 404
            
        # Step 1 — Generate secure random 12-character password
        chars = string.ascii_letters + string.digits
        temp_pwd = ''.join(secrets.choice(chars) for _ in range(12))
        
        # Step 2 — Hash for user login
        user.password_hash = hash_password(temp_pwd)
        user.require_password_change = True
        
        # Step 3 — Update request record
        reset_req.temp_password = temp_pwd # Stored for user retrieval via Forgot Password page
        reset_req.temp_password_hash = user.password_hash
        reset_req.status = 'APPROVED'
        reset_req.processed_at = datetime.now(timezone.utc)
        reset_req.processed_by = current_user.id
        
        db.session.commit()
        
        log_activity(
            user_id=current_user.id,
            action_type="UPDATE",
            entity_type="USER",
            entity_id=user.id,
            description=f"Admin approved password reset for user: {user.email}"
        )
        
        return jsonify({
            "success": True,
            "message": "Password reset approved. User can now retrieve the temporary password from the Forgot Password page."
        }), 200
        
    except Exception as e:
        logger.error(f"❌ APPROVE RESET ERROR: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"success": False, "message": "Server error"}), 500

@admin_bp.route('/reset-password/reject', methods=['POST'])
@roles_required('ADMIN')
def reject_reset():
    try:
        data = request.get_json()
        request_id = data.get('request_id')
        if not request_id:
            return jsonify({"success": False, "message": "request_id is required"}), 400
            
        reset_req = db.session.get(PasswordResetRequest, request_id)
        if not reset_req:
            return jsonify({"success": False, "message": "Request not found"}), 404
            
        if reset_req.status != 'PENDING':
            return jsonify({"success": False, "message": "Request has already been processed"}), 400
            
        reset_req.status = 'DECLINED'
        reset_req.processed_at = datetime.now(timezone.utc)
        reset_req.processed_by = current_user.id
        
        db.session.commit()
        
        log_activity(
            user_id=current_user.id,
            action_type="UPDATE",
            entity_type="PASSWORD_RESET_REQUEST",
            entity_id=request_id,
            description=f"Admin declined password reset for request ID: {request_id}"
        )
        
        return jsonify({
            "success": True,
            "message": "Password reset request declined."
        }), 200
        
    except Exception as e:
        logger.error(f"❌ DECLINE RESET ERROR: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"success": False, "message": "Server error"}), 500
