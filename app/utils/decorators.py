from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, current_user
from flask import jsonify

def roles_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            if not current_user:
                return jsonify({"success": False, "message": "User not found"}), 404
            
            # Use the role object relationship we added to User model
            user_role = current_user.role.name if current_user.role else "EMPLOYEE"
            
            if user_role not in roles:
                return jsonify({"success": False, "message": f"Permission denied. Required: {roles}"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
