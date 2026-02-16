from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        print("=" * 50)
        print("📝 REGISTER REQUEST RECEIVED")
        print("Request JSON:", data)
        print("=" * 50)
        
        # Validate required fields
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        # Accept both 'name' and 'full_name', prefer 'full_name' if present
        if 'full_name' in data:
            data['name'] = data['full_name']
        required_fields = ['name', 'email', 'password']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            print(f"❌ Validation Error: {error_msg}")
            return jsonify({"success": False, "message": error_msg}), 400
        user, message = AuthService.register_user(data)
        
        if user:
            print(f"✅ User registered successfully: {user.email}")
            return jsonify({"success": True, "message": message, "data": user.to_dict()}), 201
        else:
            print(f"❌ Registration failed: {message}")
            return jsonify({"success": False, "message": message}), 400
            
    except Exception as e:
        print(f"❌ REGISTER ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

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
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            error_msg = "Email and password are required"
            print(f"❌ Validation Error: {error_msg}")
            return jsonify({"success": False, "message": error_msg}), 400
        
        result, error = AuthService.login_user(email, password)
        
        if result:
            print(f"✅ Login successful for: {email}")
            return jsonify({"success": True, "message": "Login successful", "data": result}), 200
        else:
            print(f"❌ Login failed for {email}: {error}")
            return jsonify({"success": False, "message": error}), 401
            
    except Exception as e:
        print(f"❌ LOGIN ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500
