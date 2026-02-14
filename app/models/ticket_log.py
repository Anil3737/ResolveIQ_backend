# app/models/ticket_log.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from app.database import Base


class TicketLog(Base):
    __tablename__ = "ticket_logs"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    action = Column(String(100), nullable=False)  # STATUS_CHANGED, ASSIGNED, PRIORITY_UPDATED, etc.
    old_value = Column(String(255), nullable=True)
    new_value = Column(String(255), nullable=True)
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
