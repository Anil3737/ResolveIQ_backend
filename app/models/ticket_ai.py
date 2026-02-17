from app.extensions import db
from datetime import datetime

class TicketAI(db.Model):
    __tablename__ = "ticket_ai"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False, unique=True)
    predicted_category = db.Column(db.String(100), nullable=True)
    urgency_score = db.Column(db.Integer, default=0)
    severity_score = db.Column(db.Integer, default=0)
    similarity_risk = db.Column(db.Integer, default=0)
    sla_breach_risk = db.Column(db.Integer, default=0)
    explanation_json = db.Column(db.JSON, nullable=True)
    analyzed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "predicted_category": self.predicted_category,
            "urgency_score": self.urgency_score,
            "severity_score": self.severity_score,
            "similarity_risk": self.similarity_risk,
            "sla_breach_risk": self.sla_breach_risk,
            "explanation": self.explanation_json,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None
        }
