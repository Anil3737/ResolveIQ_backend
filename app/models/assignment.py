from app.extensions import db
from datetime import datetime

class Assignment(db.Model):
    __tablename__ = "assignments"

    id = db.Column(db.Integer, primary_key=True, index=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)  # Team Lead or Admin
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)  # Agent
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
