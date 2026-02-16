from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.decorators import roles_required
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.department import Department
from app.services.auth_service import AuthService
from app.extensions import db

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
    users = User.query.all()
    return jsonify({"success": True, "data": [u.to_dict() for u in users]}), 200

@admin_bp.route('/audit-logs', methods=['GET'])
@roles_required('ADMIN')
def get_audit_logs():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    return jsonify({"success": True, "data": [l.to_dict() for l in logs]}), 200

@admin_bp.route('/departments', methods=['GET', 'POST'])
@jwt_required()
def handle_departments():
    if request.method == 'POST':
        verify_jwt_in_request()
        if get_jwt_identity().get('role') != 'ADMIN':
            return jsonify({"success": False, "message": "Admin only"}), 403
        data = request.get_json()
        dept = Department(name=data.get('name'))
        db.session.add(dept)
        db.session.commit()
        return jsonify({"success": True, "data": dept.to_dict()}), 201
    
    depts = Department.query.all()
    return jsonify({"success": True, "data": [d.to_dict() for d in depts]}), 200
