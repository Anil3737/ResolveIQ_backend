# app/schemas/admin_schemas.py

from typing import Literal
from pydantic import BaseModel, Field, EmailStr


# -------------------------
# User Management
# -------------------------
class AdminCreateUserRequest(BaseModel):
    """Schema for admin to create users.
    Only admins can create users - supports all roles."""
    full_name: str = Field(min_length=3, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)
    password: str = Field(min_length=6, max_length=50)
    role: Literal["ADMIN", "TEAM_LEAD", "AGENT", "EMPLOYEE"] = Field(
        description="User role - admins can create any role"
    )
    department_id: int | None = Field(default=None, description="Department ID for employees")
    team_id: int | None = Field(default=None, description="Team ID for agents/team leads")



# -------------------------
# Teams
# -------------------------
class TeamCreateRequest(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: str | None = Field(default=None, max_length=255)


class TeamUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=255)


class TeamResponse(BaseModel):
    id: int
    name: str
    description: str | None


# -------------------------
# Team Members
# -------------------------
class AddTeamMemberRequest(BaseModel):
    user_id: int


# -------------------------
# Ticket Types
# -------------------------
class TicketTypeCreateRequest(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    severity_level: int = Field(ge=1, le=4)


class TicketTypeUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    severity_level: int | None = Field(default=None, ge=1, le=4)


class TicketTypeResponse(BaseModel):
    id: int
    name: str
    severity_level: int


# -------------------------
# SLA Policies
# -------------------------
class SLAPolicyCreateRequest(BaseModel):
    type_id: int
    response_minutes: int = Field(gt=0)
    resolution_minutes: int = Field(gt=0)


class SLAPolicyUpdateRequest(BaseModel):
    response_minutes: int | None = Field(default=None, gt=0)
    resolution_minutes: int | None = Field(default=None, gt=0)


class SLAPolicyResponse(BaseModel):
    id: int
    type_id: int
    response_minutes: int
    resolution_minutes: int
