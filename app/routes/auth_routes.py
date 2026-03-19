from flask import Blueprint, request, jsonify
from app.models import User, Role, PasswordResetRequest
from app.extensions import db, limiter
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, current_user
import sqlalchemy as sa

auth_bp = Blueprint('auth', __name__)


import logging
from app.schemas.auth_schemas import RegisterRequest, LoginRequest
from pydantic import ValidationError

logger = logging.getLogger(__name__)

@auth_bp.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "Auth system is up"}), 200

@auth_bp.route('/check-id', methods=['GET'])
def check_id_exists():
    emp_id = request.args.get('emp_id', '').strip()
    if not emp_id:
        return jsonify({"success": False, "message": "emp_id is required"}), 400
    
    # Check emp_id column
    user = User.query.filter_by(emp_id=emp_id).first()
    return jsonify({"success": True, "exists": user is not None}), 200

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("10 per minute")
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        # ── Pydantic Validation ──
        try:
            RegisterRequest(**data)
        except ValidationError as ve:
            return jsonify({"success": False, "message": ve.errors()[0].get('msg', 'Invalid data')}), 400
        
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
        logger.error(f"❌ SERVER ERROR: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": "An unexpected server error occurred."}), 500

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        # ── Pydantic Validation ──
        try:
            LoginRequest(**data)
        except ValidationError as ve:
            return jsonify({"success": False, "message": ve.errors()[0].get('msg', 'Invalid data')}), 400
        
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
        logger.error(f"❌ LOGIN ERROR: {str(e)}", exc_info=True)
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
        logger.error(f"❌ ME ERROR: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": "Server error"}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        new_password = data.get('password')
        if not new_password or len(new_password) < 8:
            return jsonify({"success": False, "message": "Password must be at least 8 characters long"}), 400
        
        from app.services.auth_service import AuthService
        success, message = AuthService.change_password(current_user.id, new_password)
        
        if success:
            return jsonify({"success": True, "message": message}), 200
        else:
            return jsonify({"success": False, "message": message}), 400
            
    except Exception as e:
        logger.error(f"❌ CHANGE PASSWORD ERROR: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": "Server error"}), 500

@auth_bp.route('/update-profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        from app.services.auth_service import AuthService
        success, message = AuthService.update_profile(current_user.id, data)
        
        if success:
            return jsonify({
                "success": True, 
                "message": message,
                "data": current_user.to_dict() # Return updated user data
            }), 200
        else:
            return jsonify({"success": False, "message": message}), 400
            
    except Exception as e:
        logger.error(f"❌ UPDATE PROFILE ERROR: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": "Server error"}), 500
@auth_bp.route('/request-password-reset', methods=['POST'])
@limiter.limit("10 per minute")
def request_password_reset():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        email = data.get('email', '').strip()
        emp_id = data.get('emp_id', '').strip()

        if not email or not emp_id:
            return jsonify({"success": False, "message": "Email and Employee ID are required"}), 400

        # Step 1 — Verify user (emp_id column stores the ID)
        user = User.query.filter_by(email=email, emp_id=emp_id).first()
        if not user:
            return jsonify({
                "success": False,
                "message": "Invalid Data" # Requirement: display text like "Invalid Data" in red color
            }), 404

        # Step 2 — Prevent duplicate reset requests
        existing_request = PasswordResetRequest.query.filter_by(
            user_id=user.id, 
            status='PENDING'
        ).first()
        
        if existing_request:
            return jsonify({
                "success": False,
                "message": "Request already pending admin approval."
            }), 400

        # Step 3 — Create reset request
        new_request = PasswordResetRequest(
            user_id=user.id,
            email=email,
            emp_id=emp_id,
            status='PENDING'
        )
        db.session.add(new_request)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Your password reset request has been sent to the administrator. Please check again after approval."
        }), 201

    except Exception as e:
        logger.error(f"PASSWORD RESET REQUEST ERROR: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"success": False, "message": "Server error"}), 500

@auth_bp.route('/check-reset-password', methods=['POST'])
def check_reset_password():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
            
        email = data.get('email', '').strip()
        emp_id = data.get('emp_id', '').strip()
        
        if not email or not emp_id:
            return jsonify({"success": False, "message": "Email and Employee ID are required"}), 400
            
        user = User.query.filter_by(email=email, emp_id=emp_id).first()
        if not user:
            return jsonify({"success": False, "message": "Invalid Data"}), 404
            
        reset_req = PasswordResetRequest.query.filter_by(
            user_id=user.id
        ).order_by(PasswordResetRequest.requested_at.desc()).first()
        
        if not reset_req:
            return jsonify({"success": False, "message": "No reset request found for this user."}), 404
            
        if reset_req.status == 'PENDING':
            return jsonify({
                "success": False, 
                "message": "Request pending admin approval"
            }), 200 # Status found but pending
            
        if reset_req.status == 'DECLINED':
             return jsonify({
                "success": False, 
                "message": "Reset request declined"
            }), 200
            
        if reset_req.status == 'APPROVED':
            # Capture the temp_password BEFORE clearing it
            temp_pwd = reset_req.temp_password

            if not temp_pwd:
                # Already retrieved once — temp_password was cleared after first use
                return jsonify({
                    "success": False,
                    "message": "Temporary password has already been retrieved. Please log in and change your password."
                }), 400

            # ── One-time retrieval: clear the plaintext temp_password immediately
            # after returning it so it cannot be fetched again via repeated polling.
            # temp_password_hash remains intact for login verification.
            reset_req.temp_password = None
            db.session.commit()

            return jsonify({
                "success": True,
                "message": "Request Approved",
                "temp_password": temp_pwd
            }), 200
            
        return jsonify({"success": False, "message": "Unknown request status"}), 400
        
    except Exception as e:
        logger.error(f"❌ CHECK RESET PASSWORD ERROR: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": "Server error"}), 500
