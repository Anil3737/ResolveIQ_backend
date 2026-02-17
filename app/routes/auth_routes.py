from flask import Blueprint, request, jsonify
from app.models import User, Role
from app.extensions import db
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, current_user
import sqlalchemy as sa

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/debug/jwt', methods=['GET'])
def debug_jwt():
    auth_header = request.headers.get('Authorization')
    return jsonify({
        "auth_header_present": auth_header is not None,
        "auth_header_prefix": auth_header[:10] if auth_header else None,
        "all_headers": dict(request.headers)
    }), 200

@auth_bp.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "Auth system is up"}), 200

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        print("=" * 50)
        print("📝 REGISTER REQUEST RECEIVED")
        print("Request JSON:", data)
        print("=" * 50)
        
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        # 1. Sanitize and Validate Data
        required_fields = ['full_name', 'email', 'password']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({"success": False, "message": f"Missing fields: {', '.join(missing_fields)}"}), 400
            
        full_name = data.get('full_name').strip()
        # FIX: Remove spaces from email (e.g., "anil@resolveiq. com" -> "anil@resolveiq.com")
        email = data.get('email').replace(" ", "").lower().strip()
        password = data.get('password')
        phone = data.get('phone')
        department_id = data.get('department_id')

        # 2. Prevent Multiple Registrations
        if User.query.filter_by(email=email).first():
            return jsonify({"success": False, "message": "Email already registered"}), 409

        # 3. DYNAMIC ROLE LOOKUP (No Hardcoding)
        employee_role = Role.query.filter_by(name="EMPLOYEE").first()
        if not employee_role:
            # Fallback/Error if database isn't seeded properly
            print("❌ SEVERE: 'EMPLOYEE' role missing from database!")
            return jsonify({
                "success": False, 
                "message": "System configuration error: Employee role not initialized. Please contact admin."
            }), 500

        # 4. Create User
        new_user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            role_id=employee_role.id,
            department_id=department_id,
            is_active=True
        )
        new_user.set_password(password)

        # 5. Commit to Database
        db.session.add(new_user)
        try:
            db.session.commit()
            return jsonify({
                "success": True, 
                "message": "Registration successful", 
                "data": new_user.to_dict()
            }), 201
        except sa.exc.IntegrityError as e:
            db.session.rollback()
            print(f"❌ Integrity Error: {str(e)}")
            return jsonify({
                "success": False, 
                "message": "Database constraint error. Check department ID or contact support."
            }), 400
            
    except Exception as e:
        print(f"❌ SERVER ERROR: {str(e)}")
        return jsonify({"success": False, "message": "An unexpected server error occurred."}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        print("=" * 50)
        print("🔐 LOGIN REQUEST RECEIVED")
        print("Request JSON:", data)
        print("=" * 50)
        
        # Validate required fields
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        email = data.get('email', '').replace(" ", "").lower().strip()
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"success": False, "message": "Email and password are required"}), 400
        
        # Find user
        print(f"🔍 Looking up user: {email}")
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            print(f"✅ Password correct for: {email}")
            
            # Generate Token
            # Using string ID for identity as required by JWT subject
            access_token = create_access_token(identity=str(user.id))
            
            # EXACT Login response structure
            response_data = {
                "success": True,
                "data": {
                    "access_token": access_token,
                    "user": user.to_dict()
                }
            }
            return jsonify(response_data), 200
        else:
            print(f"❌ Invalid credentials for: {email}")
            return jsonify({"success": False, "message": "Invalid email or password"}), 401
            
    except Exception as e:
        print(f"❌ LOGIN ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    try:
        if not current_user:
            return jsonify({"success": False, "message": "User not found"}), 404
            
        return jsonify({
            "success": True,
            "data": current_user.to_dict()
        }), 200
    except Exception as e:
        print(f"❌ ME ERROR: {str(e)}")
        return jsonify({"success": False, "message": "Server error"}), 500
