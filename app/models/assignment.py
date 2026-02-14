# app/models/assignment.py

from sqlalchemy import Column, Integer, DateTime, ForeignKey, func
from app.database import Base


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Team Lead or Admin
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=False)  # Agent
    assigned_at = Column(DateTime, server_default=func.now(), nullable=False)
