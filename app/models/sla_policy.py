# app/models/sla_policy.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.sql import func

from app.database import Base


class SLAPolicy(Base):
    __tablename__ = "sla_policies"

    id = Column(Integer, primary_key=True, index=True)

    type_id = Column(Integer, ForeignKey("ticket_types.id"), nullable=False)
    priority = Column(String(20), nullable=False)  # P1_CRITICAL, P2_HIGH, P3_MEDIUM, P4_LOW

    response_minutes = Column(Integer, nullable=False)
    resolution_minutes = Column(Integer, nullable=False)

    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("type_id", "priority", name="uq_sla_ticket_type_priority"),
    )
