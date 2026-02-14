from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta
from typing import Optional, List

from app.dependencies import get_db, get_current_user
from app.models.ticket import Ticket
from app.models.ticket_ai import TicketAI
from app.models.user import User
from app.schemas.ticket_schemas import TicketCreate, TicketUpdate

router = APIRouter(prefix="/api/v1/tickets", tags=["Tickets"])


@router.post("/")
def create_ticket(
    payload: TicketCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new ticket"""
    sla_deadline = datetime.utcnow() + timedelta(hours=payload.sla_hours)

    ticket = Ticket(
        title=payload.title,
        description=payload.description,
        department_id=payload.department_id,
        created_by=current_user.id,
        sla_hours=payload.sla_hours,
        sla_deadline=sla_deadline
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return {
        "message": "Ticket created successfully",
        "ticket_id": ticket.id,
        "status": ticket.status,
        "priority": ticket.priority,
        "sla_deadline": ticket.sla_deadline
    }


@router.get("/")
def list_tickets(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    search: Optional[str] = Query(None, description="Search in title/description"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all tickets with optional filters"""
    query = db.query(Ticket)
    
    # Apply filters
    if status:
        query = query.filter(Ticket.status == status)
    if priority:
        query = query.filter(Ticket.priority == priority)
    if department_id:
        query = query.filter(Ticket.department_id == department_id)
    if search:
        query = query.filter(
            or_(
                Ticket.title.ilike(f"%{search}%"),
                Ticket.description.ilike(f"%{search}%")
            )
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    tickets = query.order_by(Ticket.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "tickets": tickets
    }


@router.get("/{ticket_id}")
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific ticket by ID"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return ticket


@router.get("/{ticket_id}/with-ai")
def get_ticket_with_ai(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get ticket with AI analysis if available"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ai_analysis = db.query(TicketAI).filter(TicketAI.ticket_id == ticket_id).first()
    
    return {
        "ticket": ticket,
        "ai_analysis": ai_analysis
    }


@router.patch("/{ticket_id}")
def update_ticket(
    ticket_id: int,
    payload: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update ticket status, priority, or assignment"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Update fields
    if payload.status is not None:
        ticket.status = payload.status
        if payload.status == "RESOLVED":
            ticket.resolved_at = datetime.utcnow()
    
    if payload.priority is not None:
        ticket.priority = payload.priority
    
    if payload.assigned_to is not None:
        ticket.assigned_to = payload.assigned_to
    
    if payload.team_id is not None:
        ticket.team_id = payload.team_id
    
    db.commit()
    db.refresh(ticket)
    
    return {
        "message": "Ticket updated successfully",
        "ticket": ticket
    }


@router.delete("/{ticket_id}")
def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete a ticket (set status to CLOSED)"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket.status = "CLOSED"
    db.commit()
    
    return {"message": "Ticket closed successfully"}

