# app/models/role.py

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # ADMIN, TEAM_LEAD, AGENT, EMPLOYEE
    created_at = Column(DateTime(timezone=True), server_default=func.now())
