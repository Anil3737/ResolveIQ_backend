from app.extensions import db
from datetime import datetime

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

    # Made nullable as per DB schema
    sla_hours = db.Column(db.Integer, nullable=True)
    sla_deadline = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
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
            "breach_risk": self.breach_risk,
            "sla_hours": self.sla_hours,
            "sla_deadline": self.sla_deadline.isoformat() if self.sla_deadline else None,
            "escalation_required": self.escalation_required,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }
