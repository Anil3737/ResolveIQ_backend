"""
app/utils/dept_isolation.py

Department Isolation Utility
─────────────────────────────
Provides:
  1. ISSUE_TYPE_DEPT_MAP  — canonical Issue Type → department_id mapping (IDs 1–5)
  2. resolve_department_id() — returns overridden dept_id from issue_type string
  3. apply_dept_filter()  — attaches role-aware dept isolation to a SQLAlchemy query

CRITICAL: This is the single source of truth for department isolation.
All ticket queries that are not ADMIN must go through apply_dept_filter().
"""

# ─────────────────────────────────────────────────────────────────────────────
# Canonical Issue Type → Department ID Mapping
# DO NOT change these IDs — they must match the departments table in the DB.
# ─────────────────────────────────────────────────────────────────────────────
ISSUE_TYPE_DEPT_MAP = {
    "Network Issue": 1,
    "Hardware Failure": 2,
    "Software Installation": 3,
    "Application Downtime / Application Issues": 4,
    "Other": 5,
}


def resolve_department_id(issue_type: str) -> int:
    """
    Returns the correct department_id for a given issue_type string.

    Args:
        issue_type: One of the 5 canonical issue type strings.

    Returns:
        int: The department_id that must be used for this ticket.

    Raises:
        ValueError: If issue_type is not one of the 5 valid values.
    """
    dept_id = ISSUE_TYPE_DEPT_MAP.get(issue_type)
    if dept_id is None:
        valid = ", ".join(f'"{k}"' for k in ISSUE_TYPE_DEPT_MAP)
        raise ValueError(
            f"Invalid issue_type '{issue_type}'. Must be one of: {valid}"
        )
    return dept_id


def apply_dept_filter(query, user, Ticket):
    """
    Applies strict department isolation to a Ticket SQLAlchemy query.

    Rules:
      ADMIN     → no restriction
      TEAM_LEAD → filter by team_lead_profile.department_id
      AGENT     → filter by agent_profile.department_id
      EMPLOYEE  → filter by created_by == user.id
      default   → filter by created_by == user.id

    Args:
        query:  An active SQLAlchemy query on the Ticket model.
        user:   The current_user object (Flask-JWT-Extended).
        Ticket: The Ticket model class (avoids circular imports).

    Returns:
        The filtered SQLAlchemy query.
    """
    role = user.role.name if user.role else "EMPLOYEE"

    if role == "ADMIN":
        # No restriction — admin sees everything
        return query

    if role == "TEAM_LEAD":
        dept_id = (
            user.team_lead_profile.department_id
            if user.team_lead_profile else None
        )
        return query.filter(Ticket.department_id == dept_id)

    if role == "AGENT":
        dept_id = (
            user.agent_profile.department_id
            if user.agent_profile else None
        )
        return query.filter(Ticket.department_id == dept_id)

    # EMPLOYEE or fallback
    return query.filter(Ticket.created_by == user.id)


def assert_dept_access(ticket, user):
    """
    Raises PermissionError if user's department does not match the ticket's
    department.  Used in single-ticket detail and action endpoints.

    ADMIN always passes.

    Raises:
        PermissionError: with a 403-friendly message.
    """
    role = user.role.name if user.role else "EMPLOYEE"

    if role == "ADMIN":
        return  # unrestricted

    if role == "TEAM_LEAD":
        dept_id = (
            user.team_lead_profile.department_id
            if user.team_lead_profile else None
        )
        if ticket.department_id != dept_id:
            raise PermissionError("Access denied: ticket belongs to a different department")

    elif role == "AGENT":
        dept_id = (
            user.agent_profile.department_id
            if user.agent_profile else None
        )
        if ticket.department_id != dept_id:
            raise PermissionError("Access denied: ticket belongs to a different department")

    elif role == "EMPLOYEE":
        if ticket.created_by != user.id:
            raise PermissionError("Access denied: you did not create this ticket")
