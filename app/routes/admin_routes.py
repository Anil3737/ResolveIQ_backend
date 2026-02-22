from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, current_user
from app.utils.decorators import roles_required
from app.models.user import User
from app.models.role import Role
from app.models.audit_log import AuditLog
from app.models.department import Department
from app.services.auth_service import AuthService
from app.extensions import db
import re
import random
import string

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/create-user', methods=['POST'])
@roles_required('ADMIN')
def create_user():
    data = request.get_json()
    user, message = AuthService.register_user(data)
    if user:
        return jsonify({"success": True, "message": message, "data": user.to_dict()}), 201
    return jsonify({"success": False, "message": message}), 400

@admin_bp.route('/users', methods=['GET'])
@roles_required('ADMIN')
def get_users():
    role_filter = request.args.get('role')  # e.g., ?role=EMPLOYEE
    if role_filter:
        users = User.query.join(User.role).filter(Role.name == role_filter.upper()).all()
    else:
        users = User.query.all()
    return jsonify({"success": True, "data": [u.to_dict() for u in users]}), 200

@admin_bp.route('/teams', methods=['GET'])
@roles_required('ADMIN')
def get_teams():
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT t.id, t.name, t.description, 
                       d.name AS department_name,
                       u.full_name AS team_lead_name,
                       t.created_at
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
                    "department": row["department_name"] or "N/A",
                    "team_lead": row["team_lead_name"] or "Unassigned",
                    "created_at": str(row["created_at"]) if row["created_at"] else ""
                })
        return jsonify({"success": True, "data": teams}), 200
    except Exception as e:
        print(f"Error fetching teams: {e}")
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
        dept = Department(name=data.get('name'))
        db.session.add(dept)
        db.session.commit()
        return jsonify({"success": True, "data": dept.to_dict()}), 201
    
    depts = Department.query.all()
    return jsonify({"success": True, "data": [d.to_dict() for d in depts]}), 200

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

        # 3. Unique EMP ID (stored in users.phone column)
        if User.query.filter_by(phone=emp_id).first():
            return jsonify({"success": False, "message": "EMP ID already exists"}), 400

        # 4. Department: Must match specified list
        valid_depts = [
            "Network Issue",
            "Hardware Failure",
            "Software Installation",
            "Application Downtime / Application Issues",
            "Other"
        ]
        if dept_name not in valid_depts:
            return jsonify({"success": False, "message": f"Department must be one of: {', '.join(valid_depts)}"}), 400
        
        dept = Department.query.filter_by(name=dept_name).first()
        if not dept:
            # If not found, attempt to find by partial match or error out
            # Requirements say "Map dynamically", assuming they exist in DB
            return jsonify({"success": False, "message": f"Department '{dept_name}' not initialized in database"}), 400

        # 5. Role Lookup
        role_obj = Role.query.filter_by(name=role_name).first()
        if not role_obj:
            return jsonify({"success": False, "message": f"Role '{role_name}' not found in database"}), 400

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
            "phone": emp_id, # phone = emp_id
            "password": "Resolveiq@123",
            "role": role_name,
            "department_id": dept.id,
            "location": location
        }

        user, message = AuthService.register_user(staff_data)

        if user:
            # --- SUCCESS RESPONSE ---
            return jsonify({
                "success": True,
                "message": "Staff created successfully",
                "data": {
                    "full_name": user.full_name,
                    "email": user.email,
                    "emp_id": user.phone,
                    "role": role_name,
                    "department": dept_name
                }
            }), 201
        else:
            return jsonify({"success": False, "message": message}), 400

    except Exception as e:
        print(f"❌ ERROR in create_staff: {str(e)}")
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
        team_lead_id = data.get('team_lead_id')
        location = data.get('location', '').strip()

        # --- VALIDATION RULES ---
        if not full_name or len(full_name) < 3:
            return jsonify({"success": False, "message": "Full Name is required and must be at least 3 characters"}), 400
        
        if not re.match(r'^EMP\d{4}$', emp_id):
            return jsonify({"success": False, "message": "EMP ID must be in format EMPXXXX (e.g., EMP1001)"}), 400
        
        emp_num = int(emp_id[3:])
        if not (1000 <= emp_num <= 2000):
            return jsonify({"success": False, "message": "EMP ID number must be between 1000 and 2000 inclusive"}), 400

        # 3. Department
        dept = Department.query.filter_by(name=dept_name).first()
        if not dept:
            return jsonify({"success": False, "message": f"Department '{dept_name}' not found"}), 400

        # 4. Team Lead Validation
        if not team_lead_id:
            return jsonify({"success": False, "message": "Team Lead ID is required"}), 400
        
        team_lead = User.query.get(team_lead_id)
        if not team_lead:
            return jsonify({"success": False, "message": "Team Lead not found"}), 400
        
        if not team_lead.role or team_lead.role.name != 'TEAM_LEAD':
            return jsonify({"success": False, "message": "Assigned user is not a Team Lead"}), 400
        
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
            "phone": emp_id,
            "password": "Resolveiq@123",
            "role": "AGENT",
            "department_id": dept.id,
            "team_lead_id": team_lead_id,
            "location": location
        }

        user, message = AuthService.register_user(agent_data)

        if user:
            # --- SUCCESS RESPONSE ---
            return jsonify({
                "success": True,
                "message": "Support Agent created successfully",
                "data": {
                    "full_name": user.full_name,
                    "email": user.email,
                    "emp_id": user.phone,
                    "role": "AGENT",
                    "department": dept_name,
                    "team_lead": team_lead.full_name
                }
            }), 201
        else:
            return jsonify({"success": False, "message": message}), 400

    except Exception as e:
        print(f"❌ ERROR in create_agent: {str(e)}")
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR in create_agent: {str(e)}")
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500
