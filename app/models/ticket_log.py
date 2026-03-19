from app.extensions import db
from datetime import datetime

class TicketLog(db.Model):
    __tablename__ = "ticket_logs"

    id = db.Column(db.Integer, primary_key=True, index=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # STATUS_CHANGED, ASSIGNED, PRIORITY_UPDATED, etc.
    old_value = db.Column(db.String(255), nullable=True)
    new_value = db.Column(db.String(255), nullable=True)
    performed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
