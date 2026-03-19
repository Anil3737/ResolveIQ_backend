from app.extensions import db
from datetime import datetime

class SLAPolicy(db.Model):
    __tablename__ = "sla_policies"

    id = db.Column(db.Integer, primary_key=True, index=True)

    type_id = db.Column(db.Integer, db.ForeignKey("ticket_types.id"), nullable=False)
    priority = db.Column(db.String(20), nullable=False)  # P1_CRITICAL, P2_HIGH, P3_MEDIUM, P4_LOW

    response_minutes = db.Column(db.Integer, nullable=False)
    resolution_minutes = db.Column(db.Integer, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("type_id", "priority", name="uq_sla_ticket_type_priority"),
    )
