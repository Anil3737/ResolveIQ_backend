from flask import Blueprint, request, jsonify
from app.services.ai_service import AIService
from app.utils.decorators import roles_required

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    result = AIService.calculate_score(data.get('title'), data.get('description'))
    return jsonify({"success": True, "data": result}), 200

@ai_bp.route('/train', methods=['POST'])
@roles_required('ADMIN')
def train():
    result = AIService.train_model()
    return jsonify(result), 200
