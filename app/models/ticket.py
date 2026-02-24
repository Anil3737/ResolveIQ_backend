from app.extensions import db
from datetime import datetime, timedelta
import json

class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Added 'ESCALATED' to match DB
    status = db.Column(db.Enum('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', 'ESCALATED'), default='OPEN')
    priority = db.Column(db.Enum('P1', 'P2', 'P3', 'P4'), default='P4')

    # Defaults matching DB schema
    ai_score = db.Column(db.Integer, nullable=False, default=0)
    breach_risk = db.Column(db.Float, nullable=False, default=0.0)
    escalation_required = db.Column(db.Boolean, nullable=False, default=False)
    ai_explanation = db.Column(db.JSON, nullable=True)

    # Made nullable as per DB schema
    sla_hours = db.Column(db.Integer, nullable=True)
    sla_deadline = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        now = datetime.utcnow()
        
        # SLA Countdown
        sla_remaining = 0
        if self.sla_deadline and self.sla_deadline > now:
            sla_remaining = int((self.sla_deadline - now).total_seconds())
        
        sla_breached = False
        if self.sla_deadline and now > self.sla_deadline and self.status not in ["RESOLVED", "CLOSED"]:
            sla_breached = True

        # Auto-close countdown (48h)
        auto_close_in = None
        if self.status == "RESOLVED" and self.resolved_at:
            close_deadline = self.resolved_at + timedelta(hours=48)
            if close_deadline > now:
                auto_close_in = int((close_deadline - now).total_seconds())
            else:
                auto_close_in = 0

        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "department_id": self.department_id,
            "created_by": self.created_by,
            "assigned_to": self.assigned_to,
            "status": self.status,
            "priority": self.priority,
            "ai_score": self.ai_score,
            "breach_risk": int(self.breach_risk * 100),
            "sla_hours": self.sla_hours,
            "sla_deadline": self.sla_deadline.isoformat() if self.sla_deadline else None,
            "sla_remaining_seconds": sla_remaining,
            "sla_breached": sla_breached,
            "auto_close_in_seconds": auto_close_in,
            "escalation_required": self.escalation_required,
            "ai_explanation": self.ai_explanation if isinstance(self.ai_explanation, dict) else (json.loads(self.ai_explanation) if self.ai_explanation else None),
            "risk_percentage": int(self.breach_risk * 100),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }
