"""
app/utils/dept_isolation.py

Department Isolation Utility
─────────────────────────────
Provides:
  1. ISSUE_TYPE_TO_NAME  — canonical Issue Type → department NAME mapping
  2. resolve_department_id() — dynamically looks up the correct dept_id from the DB
  3. apply_dept_filter()  — attaches role-aware dept isolation to a SQLAlchemy query

CRITICAL: Uses DB name lookup (not hardcoded IDs) so this works regardless of
which IDs MySQL assigns after a fresh migration.
"""

# ─────────────────────────────────────────────────────────────────────────────
# Canonical Issue Type → Department NAME Mapping
# These names must exactly match what is inserted into the departments table.
# ─────────────────────────────────────────────────────────────────────────────
ISSUE_TYPE_TO_NAME = {
    "Network Issues": "Network Issues",
    "Network Issue": "Network Issues",
    "Hardware Failure": "Hardware Failure",
    "Software Installation": "Software Installation",
    "Application Down/ Application Issue": "Application Down/ Application Issue",
    "Application Downtime / Application Issues": "Application Down/ Application Issue",
    "Application Down": "Application Down/ Application Issue",
    "Application Issues": "Application Down/ Application Issue",
    "Others": "Others",
    "Other": "Others",
}

# In-process cache: populated on first use to avoid repeated DB queries.
_dept_id_cache = {}  # { "Network Issues": 1, "Hardware Failure": 2, ... }


def _get_dept_id_by_name(dept_name: str) -> int:
    """
    Fetch and cache the department ID for the given canonical department name.
    Raises ValueError if the department is not found in the database.
    """
    if dept_name in _dept_id_cache:
        return _dept_id_cache[dept_name]

    from app.models.department import Department
    dept = Department.query.filter_by(name=dept_name).first()
    if dept is None:
        raise ValueError(
            f"Department '{dept_name}' not found in the database. "
            "Make sure you have run the setup/seed script first."
        )
    _dept_id_cache[dept_name] = dept.id
    return dept.id


def resolve_department_id(issue_type: str) -> int:
    """
    Returns the correct department_id for a given issue_type string.
    Looks up the departments table dynamically — never relies on hardcoded IDs.

    Args:
        issue_type: One of the 5 canonical issue type strings.

    Returns:
        int: The department_id from the DB for this issue type.

    Raises:
        ValueError: If issue_type is not one of the valid values.
    """
    dept_name = ISSUE_TYPE_TO_NAME.get(issue_type)
    if dept_name is None:
        valid = ", ".join(f'"{k}"' for k in ISSUE_TYPE_TO_NAME)
        raise ValueError(
            f"Invalid issue_type '{issue_type}'. Must be one of: {valid}"
        )
    return _get_dept_id_by_name(dept_name)


def clear_dept_cache():
    """
    Clears the in-process department ID cache.
    Useful during tests or after DB resets.
    """
    global _dept_id_cache
    _dept_id_cache = {}


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
