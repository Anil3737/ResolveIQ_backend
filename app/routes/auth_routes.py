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
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        # Default to employee for public registration
        data['role'] = 'EMPLOYEE'
        
        from app.services.auth_service import AuthService
        user, message = AuthService.register_user(data)
        
        if user:
            return jsonify({
                "success": True, 
                "message": message, 
                "data": user.to_dict()
            }), 201
        else:
            return jsonify({"success": False, "message": message}), 400
            
    except Exception as e:
        print(f"❌ SERVER ERROR: {str(e)}")
        return jsonify({"success": False, "message": "An unexpected server error occurred."}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        email = data.get('email', '').strip()
        password = data.get('password')
        
        from app.services.auth_service import AuthService
        result, error = AuthService.login_user(email, password)
        
        if result:
            return jsonify({
                "success": True,
                "message": "Login successful",
                "data": result
            }), 200
        else:
            return jsonify({"success": False, "message": error}), 401
            
    except Exception as e:
        print(f"❌ LOGIN ERROR: {str(e)}")
        return jsonify({"success": False, "message": "Server error"}), 500

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
