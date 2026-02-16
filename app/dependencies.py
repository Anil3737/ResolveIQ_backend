# app/dependencies.py

from functools import wraps
from flask import request, jsonify, g
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.utils.jwt_utils import decode_access_token


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"detail": "Missing or invalid token"}), 401
        
        token = auth_header.split(" ")[1]
        payload = decode_access_token(token)

        if not payload or "user_id" not in payload:
            return jsonify({"detail": "Invalid or expired token"}), 401

        db = get_db()
        user_id = payload["user_id"]
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return jsonify({"detail": "User not found"}), 401

        if not user.is_active:
            return jsonify({"detail": "User account is inactive"}), 403

        # Store user in Flask's global context 'g'
        g.current_user = user
        return f(*args, **kwargs)

    return decorated


def get_current_user():
    """Helper to get user from Flask global context"""
    return getattr(g, "current_user", None)
