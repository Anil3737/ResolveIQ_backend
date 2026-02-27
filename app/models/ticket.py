from app.extensions import db
from datetime import datetime, timedelta, timezone
import json

def format_datetime(dt):
    """Return an ISO 8601 string with explicit UTC offset (+00:00), or None."""
    if dt:
        return dt.replace(tzinfo=timezone.utc).isoformat()
    return None

class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    ticket_number = db.Column(db.String(25), unique=True, nullable=True)  # Public display ID e.g. IQ-IT-2026-000001
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Updated Status Flow
    status = db.Column(db.Enum('OPEN', 'APPROVED', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', 'ESCALATED'), default='OPEN')
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
    
    # Workflow Timestamps
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    accepted_at = db.Column(db.DateTime, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_tickets')
    assigned_user = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_tickets')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_tickets')
    department = db.relationship('Department', backref='tickets')

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
            "ticket_number": self.ticket_number,
            "title": self.title,
            "description": self.description,
            "department_id": self.department_id,
            "department_name": self.department.name if self.department else None,
            "created_by": self.created_by,
            "created_by_name": self.creator.full_name if self.creator else None,
            "created_by_emp_id": self.creator.phone if self.creator else None,
            "assigned_to": self.assigned_to,
            "assigned_to_name": self.assigned_user.full_name if self.assigned_user else None,
            "status": self.status,
            "priority": self.priority,
            "ai_score": self.ai_score,
            "breach_risk": int(self.breach_risk * 100),
            "sla_hours": self.sla_hours,
            "sla_deadline": format_datetime(self.sla_deadline),
            "sla_remaining_seconds": sla_remaining,
            "sla_breached": sla_breached,
            "auto_close_in_seconds": auto_close_in,
            "escalation_required": self.escalation_required,
            "ai_explanation": self.ai_explanation if isinstance(self.ai_explanation, dict) else (json.loads(self.ai_explanation) if self.ai_explanation else None),
            "risk_percentage": int(self.breach_risk * 100),
            "created_at": format_datetime(self.created_at),
            "updated_at": format_datetime(self.updated_at),
            "approved_at": format_datetime(self.approved_at),
            "accepted_at": format_datetime(self.accepted_at),
            "resolved_at": format_datetime(self.resolved_at),
            "closed_at": format_datetime(self.closed_at)
        }
