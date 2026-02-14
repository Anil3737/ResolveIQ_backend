# app/models/ticket_type.py

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.database import Base


class TicketType(Base):
    __tablename__ = "ticket_types"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), unique=True, nullable=False)
    severity_level = Column(Integer, nullable=False, default=1)  
    # 1=Low, 2=Medium, 3=High, 4=Critical

    created_at = Column(DateTime, server_default=func.now())
