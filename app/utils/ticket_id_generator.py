"""
app/utils/ticket_id_generator.py

Generates sequential, race-condition-safe ticket numbers per department.
Format:  IQ-IT-2026-XXXXXX

CHANGE: Department ID ranges are now built DYNAMICALLY from the DB so this
works after any migration or DB reset (IDs are no longer hardcoded as 6-10).

Each department owns a numeric range of 100,000 numbers, indexed by the
alphabetical order of department names (for stability across resets):
  Slot 0  → 000000–099999
  Slot 1  → 100000–199999
  Slot 2  → 200000–299999
  Slot 3  → 300000–399999
  Slot 4  → 400000–499999
"""

from app.models.ticket import Ticket
from app.extensions import db

PREFIX = "IQ-IT-2026-"
RANGE_SIZE = 100_000

# Stable canonical sort order of the 5 department names
DEPT_NAME_SORT_ORDER = [
    "Application Down/ Application Issue",  # slot 0
    "Hardware Failure",                       # slot 1
    "Network Issues",                         # slot 2
    "Others",                                 # slot 3
    "Software Installation",                  # slot 4
]

# Cache: {dept_id: (range_start, range_end)}
_dept_ranges_cache = {}


def _build_ranges():
    """
    Build and cache the dept_id → (start, end) range map.
    Queries the DB once and maps names → IDs using DEPT_NAME_SORT_ORDER
    so each department always owns the same range slot.
    """
    from app.models.department import Department

    depts = Department.query.all()
    name_to_id = {d.name: d.id for d in depts}

    for slot, name in enumerate(DEPT_NAME_SORT_ORDER):
        dept_id = name_to_id.get(name)
        if dept_id is not None:
            start = slot * RANGE_SIZE
            end = start + RANGE_SIZE - 1
            _dept_ranges_cache[dept_id] = (start, end)


def _get_range(department_id: int):
    """
    Return (range_start, range_end) for the given department ID.
    Builds the cache on first call.
    """
    if not _dept_ranges_cache:
        _build_ranges()
    if department_id not in _dept_ranges_cache:
        # Try rebuilding (DB may have been seeded after first call)
        _dept_ranges_cache.clear()
        _build_ranges()
    if department_id not in _dept_ranges_cache:
        raise ValueError(
            f"Unknown department_id '{department_id}'. "
            "Make sure departments are seeded (run setup_db.py)."
        )
    return _dept_ranges_cache[department_id]


def clear_range_cache():
    """Clear the cached ranges — useful after DB resets in tests."""
    global _dept_ranges_cache
    _dept_ranges_cache = {}


def generate_ticket_number(department_id: int) -> str:
    """
    Generate the next sequential ticket number for a given department.

    RACE CONDITION SAFE:
      Uses SELECT ... FOR UPDATE to lock the highest current ticket in the
      given department's range. This ensures concurrent requests wait
      for the latest value before incrementing.
    """
    start, end = _get_range(department_id)

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
            # Extract numeric part: IQ-IT-2026-XXXXXX → XXXXXX
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

    return f"{PREFIX}{new_number:06d}"
