from app.extensions import db
from datetime import datetime

class TicketHistory(db.Model):
    __tablename__ = "ticket_history"

    id = db.Column(db.Integer, primary_key=True, index=True)

    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)

    action = db.Column(db.String(120), nullable=False)
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)

    performed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    performed_at = db.Column(db.DateTime, default=datetime.utcnow)
