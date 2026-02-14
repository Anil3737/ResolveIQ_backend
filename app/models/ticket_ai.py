from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.database import Base


class TicketAI(Base):
    __tablename__ = "ticket_ai"

    id = Column(Integer, primary_key=True, index=True)

    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, unique=True)

    predicted_category = Column(String(100), nullable=True)

    urgency_score = Column(Integer, default=0)
    severity_score = Column(Integer, default=0)
    similarity_risk = Column(Integer, default=0)
    sla_breach_risk = Column(Integer, default=0)

    explanation_json = Column(JSON, nullable=True)

    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())
