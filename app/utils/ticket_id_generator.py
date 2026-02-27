from app.models.ticket import Ticket
from sqlalchemy import text
from app.extensions import db

# Department ID → (range_start, range_end)
# These ranges MUST NEVER overlap.
DEPARTMENT_RANGES = {
    1: (0,      99999),   # Network Issue
    2: (100000, 199999),  # Hardware Failure
    3: (200000, 299999),  # Software Installation
    4: (300000, 399999),  # Application Downtime / Application Issues
    5: (400000, 499999),  # Other
}

PREFIX = "IQ-IT-2026-"


def generate_ticket_number(department_id):
    """
    Generate the next sequential ticket number for a given department.

    RACE CONDITION SAFE:
      Uses SELECT ... FOR UPDATE to lock the highest current ticket in the 
      given department's range. This ensures concurrent requests wait 
      for the latest value before incrementing.
    """
    if department_id not in DEPARTMENT_RANGES:
        raise ValueError(
            f"Unknown department_id '{department_id}'. "
            f"Valid IDs: {list(DEPARTMENT_RANGES.keys())}"
        )

    start, end = DEPARTMENT_RANGES[department_id]

    # Find the highest existing ticket_number in this department's range.
    # CRITICAL: with_for_update() prevents race conditions.
    last_ticket = (
        db.session.query(Ticket)
        .filter(
            Ticket.department_id == department_id,
            Ticket.ticket_number.isnot(None),
            Ticket.ticket_number >= f"{PREFIX}{start:06d}",
            Ticket.ticket_number <= f"{PREFIX}{end:06d}"
        )
        .order_by(Ticket.ticket_number.desc())
        .with_for_update()  # <-- Database-level lock
        .first()
    )

    if last_ticket and last_ticket.ticket_number:
        try:
            # Extract numeric part IQ-IT-2026-XXXXXX -> XXXXXX
            last_number = int(last_ticket.ticket_number.split("-")[-1])
            new_number = last_number + 1
        except (ValueError, IndexError):
            new_number = start
    else:
        new_number = start

    if new_number > end:
        raise ValueError(
            f"Ticket number range exhausted for department_id={department_id}. "
            f"Range {start}–{end} is full."
        )

    formatted = f"{new_number:06d}"
    return PREFIX + formatted
