# app/ai/ai_routes.py

from flask import Blueprint, request, jsonify, g
from datetime import datetime
from app.database import get_db
from app.dependencies import token_required, get_current_user
from app.models.ticket import Ticket
from app.models.ticket_ai import TicketAI
from app.ai.ai_engine import run_ticket_ai

ai_bp = Blueprint("ai", __name__)

@ai_bp.route("/ai/analyze/<int:ticket_id>", methods=["POST"])
@token_required
def analyze_ticket(ticket_id):
    """Run AI analysis on a ticket and auto-update priority"""
    db = get_db()
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        return jsonify({"detail": "Ticket not found"}), 404

    # Load historical resolved tickets
    past_tickets = (
        db.query(Ticket)
        .filter(Ticket.resolved_at != None)
        .order_by(Ticket.resolved_at.desc())
        .limit(200)
        .all()
    )

    historical = []
    for t in past_tickets:
        breached = 0
        if t.resolved_at and t.sla_deadline:
            breached = 1 if t.resolved_at > t.sla_deadline else 0

        historical.append({
            "text": f"{t.title} {t.description}",
            "sla_breached": breached
        })

    try:
        ai_result = run_ticket_ai(ticket.title, ticket.description, historical)
    except Exception as e:
        return jsonify({"detail": f"AI analysis failed: {str(e)}"}), 500

    existing = db.query(TicketAI).filter(TicketAI.ticket_id == ticket.id).first()

    if existing:
        existing.predicted_category = ai_result["predicted_category"]
        existing.urgency_score = ai_result["urgency_score"]
        existing.severity_score = ai_result["severity_score"]
        existing.similarity_risk = ai_result["similarity_risk"]
        existing.sla_breach_risk = ai_result["sla_breach_risk"]
        existing.explanation_json = ai_result["explanation_json"]
        existing.analyzed_at = datetime.utcnow()
    else:
        ai_row = TicketAI(
            ticket_id=ticket.id,
            predicted_category=ai_result["predicted_category"],
            urgency_score=ai_result["urgency_score"],
            severity_score=ai_result["severity_score"],
            similarity_risk=ai_result["similarity_risk"],
            sla_breach_risk=ai_result["sla_breach_risk"],
            explanation_json=ai_result["explanation_json"],
            analyzed_at=datetime.utcnow()
        )
        db.add(ai_row)

    ticket.priority = ai_result["priority"]
    db.commit()

    return jsonify({
        "ticket_id": ticket.id,
        "updated_ticket_priority": ticket.priority,
        **ai_result
    })

@ai_bp.route("/ai/analysis/<int:ticket_id>", methods=["GET"])
@token_required
def get_ai_analysis(ticket_id):
    """Get existing AI analysis for a ticket without re-running"""
    db = get_db()
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        return jsonify({"detail": "Ticket not found"}), 404
    
    ai_analysis = db.query(TicketAI).filter(TicketAI.ticket_id == ticket_id).first()
    if not ai_analysis:
        return jsonify({"detail": "AI analysis not found. Run /ai/analyze/{ticket_id} first."}), 404
    
    return jsonify({
        "ticket_id": ticket_id,
        "predicted_category": ai_analysis.predicted_category,
        "urgency_score": ai_analysis.urgency_score,
        "severity_score": ai_analysis.severity_score,
        "similarity_risk": ai_analysis.similarity_risk,
        "sla_breach_risk": ai_analysis.sla_breach_risk,
        "explanation": ai_analysis.explanation_json,
        "analyzed_at": ai_analysis.analyzed_at.isoformat() if ai_analysis.analyzed_at else None
    })

