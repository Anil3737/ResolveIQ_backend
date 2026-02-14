from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TicketCreate(BaseModel):
    title: str
    description: str
    department_id: int
    sla_hours: int = 24


class TicketUpdate(BaseModel):
    """Schema for updating ticket fields"""
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[int] = None
    team_id: Optional[int] = None


class TicketOut(BaseModel):
    id: int
    title: str
    description: str
    department_id: int
    status: str
    priority: str
    created_at: datetime
    sla_deadline: Optional[datetime]

    class Config:
        from_attributes = True

