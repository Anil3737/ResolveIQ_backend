# app/services/ticket_code_generator.py

"""
Ticket Code Generator Service
Generates unique ticket codes in format: RIQ-YYYY-NNNN
Example: RIQ-2026-0001
"""

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.ticket import Ticket


def generate_ticket_code(db: Session) -> str:
    """
    Generate a unique ticket code in format RIQ-YYYY-NNNN.
    
    Args:
        db: Database session
    
    Returns:
        Unique ticket code string
    """
    current_year = datetime.now().year
    
    # Count tickets created this year
    count = db.query(func.count(Ticket.ticket_id)).filter(
        Ticket.ticket_code.like(f"RIQ-{current_year}-%")
    ).scalar()
    
    # Generate code with zero-padded sequential number
    next_number = (count or 0) + 1
    ticket_code = f"RIQ-{current_year}-{next_number:04d}"
    
    return ticket_code


def is_ticket_code_unique(ticket_code: str, db: Session) -> bool:
    """
    Check if a ticket code is unique.
    
    Args:
        ticket_code: Code to check
        db: Database session
    
    Returns:
        True if unique, False if already exists
    """
    existing = db.query(Ticket).filter(
        Ticket.ticket_code == ticket_code
    ).first()
    
    return existing is None
