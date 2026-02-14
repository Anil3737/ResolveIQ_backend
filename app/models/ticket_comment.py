# app/models/ticket_comment.py

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Boolean, func
from app.database import Base


class TicketComment(Base):
    __tablename__ = "ticket_comments"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)  # Internal notes visible only to team
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
