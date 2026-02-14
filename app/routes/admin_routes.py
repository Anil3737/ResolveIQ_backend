# app/routes/admin_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.role import Role
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.ticket_type import TicketType
from app.models.sla_policy import SLAPolicy

from app.schemas.admin_schemas import (
    AdminCreateUserRequest,
    TeamCreateRequest,
    TeamUpdateRequest,
    AddTeamMemberRequest,
    TicketTypeCreateRequest,
    TicketTypeUpdateRequest,
    SLAPolicyCreateRequest,
    SLAPolicyUpdateRequest,
)

from app.schemas.auth_schemas import AdminResetPasswordRequest
from app.utils.password_utils import hash_password


router = APIRouter(tags=["Admin"])


# -------------------------
# Helper: Admin Role Check
# -------------------------
def ensure_admin(current_user: User, db: Session):
    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    if not role or role.name != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )


# ==========================================================
# USER MANAGEMENT
# ==========================================================

@router.post("/admin/users")
def admin_create_user(
    payload: AdminCreateUserRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Admin endpoint to create users with any role.
    
    Per requirements: Only admins can create users.
    Supports all roles: ADMIN, TEAM_LEAD, AGENT, EMPLOYEE
    """
    ensure_admin(current_user, db)

    # Check if email already exists
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists"
        )

    # Get role
    role = db.query(Role).filter(Role.name == payload.role).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{payload.role} role not found in database. Please seed roles first."
        )

    # Create new user
    new_user = User(
        role_id=role.id,
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        department_id=payload.department_id,
        is_active=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User created successfully",
        "user_id": new_user.id,
        "role": role.name,
        "email": new_user.email
    }


@router.get("/admin/users")
def admin_list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_admin(current_user, db)

    users = db.query(User).all()
    result = []

    for u in users:
        role = db.query(Role).filter(Role.id == u.role_id).first()
        result.append({
            "user_id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "phone": u.phone,
            "role": role.name if role else "UNKNOWN",
            "is_active": u.is_active,
        })

    return result


@router.patch("/admin/users/{user_id}/status")
def admin_update_user_status(
    user_id: int,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_admin(current_user, db)

    is_active = payload.get("is_active")
    if is_active is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="is_active is required"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_active = bool(is_active)
    db.commit()

    return {"message": "User status updated successfully"}


@router.post("/admin/users/{user_id}/reset-password")
def admin_reset_password(
    user_id: int,
    payload: AdminResetPasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_admin(current_user, db)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.password_hash = hash_password(payload.new_password)
    db.commit()

    return {"message": f"Password reset successfully for user_id {user_id}"}


# ==========================================================
# TEAMS CRUD
# ==========================================================

@router.post("/admin/teams")
def create_team(
    payload: TeamCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_admin(current_user, db)

    existing = db.query(Team).filter(Team.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Team name already exists"
        )

    team = Team(name=payload.name, description=payload.description)
    db.add(team)
    db.commit()
    db.refresh(team)

    return {"message": "Team created successfully", "team_id": team.id}


@router.get("/admin/teams")
def list_teams(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_admin(current_user, db)

    teams = db.query(Team).all()
    return teams


@router.get("/admin/teams/{team_id}")
def get_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_admin(current_user, db)

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    return team


@router.patch("/admin/teams/{team_id}")
def update_team(
    team_id: int,
    payload: TeamUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_admin(current_user, db)

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if payload.name:
        team.name = payload.name
    if payload.description is not None:
        team.description = payload.description

    db.commit()
    return {"message": "Team updated successfully"}


@router.delete("/admin/teams/{team_id}")
def delete_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_admin(current_user, db)

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    db.delete(team)
    db.commit()

    return {"message": "Team deleted successfully"}


# ==========================================================
# TEAM MEMBERS
# ==========================================================

@router.post("/admin/teams/{team_id}/members")
def add_team_member(
    team_id: int,
    payload: AddTeamMemberRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_admin(current_user, db)

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role = db.query(Role).filter(Role.id == user.role_id).first()
    if not role or role.name not in ["TEAM_LEAD", "AGENT"]:
        raise HTTPException(
            status_code=400,
            detail="Only TEAM_LEAD or AGENT can be added to a team"
        )

    existing = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == payload.user_id
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="User already in team")

    tm = TeamMember(team_id=team_id, user_id=payload.user_id)
    db.add(tm)
    db.commit()

    return {"message": "Team member added successfully"}


@router.get("/admin/teams/{team_id}/members")
def list_team_members(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_admin(current_user, db)

    members = db.query(TeamMember).filter(TeamMember.team_id == team_id).all()
    result = []

    for m in members:
        user = db.query(User).filter(User.id == m.user_id).first()
        role = db.query(Role).filter(Role.id == user.role_id).first() if user else None

        result.append({
            "team_id": team_id,
            "user_id": m.user_id,
            "full_name": user.full_name if user else "UNKNOWN",
            "email": user.email if user else "UNKNOWN",
            "role": role.name if role else "UNKNOWN"
        })

    return result


@router.delete("/admin/teams/{team_id}/members/{user_id}")
def remove_team_member(
    team_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_admin(current_user, db)

    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")

    db.delete(member)
    db.commit()

    return {"message": "Team member removed successfully"}


# ==========================================================
# TICKET TYPES CRUD
# ==========================================================

@router.post("/admin/ticket-types")
def create_ticket_type(
    payload: TicketTypeCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_admin(current_user, db)

    existing = db.query(TicketType).filter(TicketType.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Ticket type already exists")

    tt = TicketType(name=payload.name, severity_level=payload.severity_level)
    db.add(tt)
    db.commit()
    db.refresh(tt)

    return {"message": "Ticket type created successfully", "type_id": tt.id}


@router.get("/admin/ticket-types")
def list_ticket_types(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_admin(current_user, db)
    return db.query(TicketType).all()


@router.patch("/admin/ticket-types/{type_id}")
def update_ticket_type(
    type_id: int,
    payload: TicketTypeUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_admin(current_user, db)

    tt = db.query(TicketType).filter(TicketType.id == type_id).first()
    if not tt:
        raise HTTPException(status_code=404, detail="Ticket type not found")

    if payload.name:
        tt.name = payload.name
    if payload.severity_level:
        tt.severity_level = payload.severity_level

    db.commit()
    return {"message": "Ticket type updated successfully"}


@router.delete("/admin/ticket-types/{type_id}")
def delete_ticket_type(
    type_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_admin(current_user, db)

    tt = db.query(TicketType).filter(TicketType.id == type_id).first()
    if not tt:
        raise HTTPException(status_code=404, detail="Ticket type not found")

    db.delete(tt)
    db.commit()

    return {"message": "Ticket type deleted successfully"}


# ==========================================================
# SLA POLICIES CRUD
# ==========================================================

@router.post("/admin/sla-policies")
def create_sla_policy(
    payload: SLAPolicyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_admin(current_user, db)

    tt = db.query(TicketType).filter(TicketType.id == payload.type_id).first()
    if not tt:
        raise HTTPException(status_code=404, detail="Ticket type not found")

    existing = db.query(SLAPolicy).filter(SLAPolicy.type_id == payload.type_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="SLA already exists for this ticket type")

    sla = SLAPolicy(
        type_id=payload.type_id,
        response_minutes=payload.response_minutes,
        resolution_minutes=payload.resolution_minutes,
    )

    db.add(sla)
    db.commit()
    db.refresh(sla)

    return {"message": "SLA policy created successfully", "sla_id": sla.id}


@router.get("/admin/sla-policies")
def list_sla_policies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_admin(current_user, db)
    return db.query(SLAPolicy).all()


@router.patch("/admin/sla-policies/{sla_id}")
def update_sla_policy(
    sla_id: int,
    payload: SLAPolicyUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_admin(current_user, db)

    sla = db.query(SLAPolicy).filter(SLAPolicy.id == sla_id).first()
    if not sla:
        raise HTTPException(status_code=404, detail="SLA policy not found")

    if payload.response_minutes:
        sla.response_minutes = payload.response_minutes
    if payload.resolution_minutes:
        sla.resolution_minutes = payload.resolution_minutes

    db.commit()
    return {"message": "SLA policy updated successfully"}


@router.delete("/admin/sla-policies/{sla_id}")
def delete_sla_policy(
    sla_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_admin(current_user, db)

    sla = db.query(SLAPolicy).filter(SLAPolicy.id == sla_id).first()
    if not sla:
        raise HTTPException(status_code=404, detail="SLA policy not found")

    db.delete(sla)
    db.commit()

    return {"message": "SLA policy deleted successfully"}
