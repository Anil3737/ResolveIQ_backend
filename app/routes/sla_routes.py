from flask import Blueprint, request, jsonify
from app.services.sla_service import SLAService
from app.models.sla_rule import SLARule
from app.utils.decorators import roles_required
from app.extensions import db

sla_bp = Blueprint('sla', __name__)

@sla_bp.route('/rules', methods=['POST'])
@roles_required('ADMIN')
def create_rule():
    data = request.get_json()
    rule = SLAService.create_or_update_rule(
        data.get('department_id'),
        data.get('priority'),
        data.get('sla_hours')
    )
    return jsonify({"success": True, "data": rule.to_dict()}), 201

@sla_bp.route('/rules', methods=['GET'])
@roles_required('ADMIN', 'TEAM_LEAD')
def get_rules():
    rules = SLARule.query.all()
    return jsonify({"success": True, "data": [r.to_dict() for r in rules]}), 200

@sla_bp.route('/rules/<int:id>', methods=['PUT'])
@roles_required('ADMIN')
def update_rule(id):
    rule = SLARule.query.get_or_404(id)
    data = request.get_json()
    rule.sla_hours = data.get('sla_hours')
    db.session.commit()
    return jsonify({"success": True, "data": rule.to_dict()}), 200

@sla_bp.route('/rules/<int:id>', methods=['DELETE'])
@roles_required('ADMIN')
def delete_rule(id):
    rule = SLARule.query.get_or_404(id)
    db.session.delete(rule)
    db.session.commit()
    return jsonify({"success": True, "message": "Rule deleted"}), 200
