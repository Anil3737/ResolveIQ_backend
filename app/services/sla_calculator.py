# app/services/sla_calculator.py

"""
SLA Calculation Service
Calculates SLA response and resolution deadlines based on ticket priority and type.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.models.sla_policy import SLAPolicy


def calculate_sla_deadlines(
    ticket_type_id: int,
    priority: str,
    created_at: datetime,
    db: Session
) -> Tuple[Optional[datetime], Optional[datetime], Optional[int]]:
    """
    Calculate SLA response and resolution deadlines for a ticket.
    
    Args:
        ticket_type_id: ID of the ticket type
        priority: Priority level (P1_CRITICAL, P2_HIGH, etc.)
        created_at: Ticket creation timestamp
        db: Database session
    
    Returns:
        Tuple of (response_due, resolution_due, sla_policy_id)
    """
    # Find matching SLA policy
    sla_policy = db.query(SLAPolicy).filter(
        SLAPolicy.type_id == ticket_type_id,
        SLAPolicy.priority == priority
    ).first()
    
    if not sla_policy:
        # No SLA policy found - return None deadlines
        return None, None, None
    
    # Calculate deadlines
    response_due = created_at + timedelta(minutes=sla_policy.response_minutes)
    resolution_due = created_at + timedelta(minutes=sla_policy.resolution_minutes)
    
    return response_due, resolution_due, sla_policy.sla_id


def is_sla_breached(deadline: Optional[datetime], current_time: Optional[datetime] = None) -> bool:
    """
    Check if an SLA deadline has been breached.
    
    Args:
        deadline: SLA deadline
        current_time: Current time (defaults to now)
    
    Returns:
        True if breached, False otherwise
    """
    if deadline is None:
        return False
    
    if current_time is None:
        current_time = datetime.now()
    
    return current_time > deadline


def get_time_remaining(deadline: Optional[datetime], current_time: Optional[datetime] = None) -> Optional[int]:
    """
    Get time remaining until SLA deadline in minutes.
    
    Args:
        deadline: SLA deadline
        current_time: Current time (defaults to now)
    
    Returns:
        Minutes remaining (negative if breached), or None if no deadline
    """
    if deadline is None:
        return None
    
    if current_time is None:
        current_time = datetime.now()
    
    delta = deadline - current_time
    return int(delta.total_seconds() / 60)
