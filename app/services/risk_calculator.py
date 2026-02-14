# app/services/risk_calculator.py

"""
AI-Based SLA Breach Risk Calculation Service
Calculates the risk of SLA breach based on multiple factors with explainable AI.
Returns risk score (0-100), risk level, and detailed factor breakdown.
"""

from datetime import datetime
from typing import Tuple, List, Dict
from sqlalchemy.orm import Session
from app.models.ticket import Ticket


def calculate_risk_score(
    ticket: Ticket,
    db: Session
) -> Tuple[int, str, List[Dict]]:
    """
    Calculate SLA breach risk score (0-100) based on multiple AI factors.
    
    Args:
        ticket: Ticket object with all fields populated
        db: Database session for querying historical data
    
    Returns:
        Tuple of (risk_score, risk_level, factors_breakdown)
        - risk_score: 0-100 integer
        - risk_level: LOW, MEDIUM, HIGH, or CRITICAL
        - factors_breakdown: List of dicts with factor details
    """
    factors = []
    base_score = 0
    
    # Factor 1: Priority Baseline (0-30 points) - 30% weight
    priority_scores = {
        "P1_CRITICAL": 30,
        "P2_HIGH": 20,
        "P3_MEDIUM": 10,
        "P4_LOW": 5
    }
    priority_score = priority_scores.get(ticket.priority, 0)
    base_score += priority_score
    factors.append({
        "factor": "Priority Level",
        "value": ticket.priority,
        "score": priority_score,
        "weight": "30%",
        "explanation": "Higher priority tickets have higher risk baseline"
    })
    
    # Factor 2: SLA Deadline Proximity (0-35 points) - 35% weight
    if ticket.sla_resolution_due:
        time_until_due = (ticket.sla_resolution_due - datetime.now()).total_seconds() / 60
        
        if time_until_due < 0:
            deadline_score = 35  # Already breached!
            deadline_status = "BREACHED"
        elif time_until_due < 30:
            deadline_score = 30
            deadline_status = f"{int(time_until_due)} min remaining - CRITICAL"
        elif time_until_due < 120:
            deadline_score = 20
            deadline_status = f"{int(time_until_due)} min remaining - WARNING"
        elif time_until_due < 360:
            deadline_score = 10
            deadline_status = f"{int(time_until_due)} min remaining"
        else:
            deadline_score = 5
            deadline_status = f"{int(time_until_due / 60)} hours remaining"
        
        base_score += deadline_score
        factors.append({
            "factor": "SLA Deadline Proximity",
            "value": deadline_status,
            "score": deadline_score,
            "weight": "35%",
            "explanation": "Closer to deadline increases risk exponentially"
        })
    
    # Factor 3: Assignment Status (0-15 points) - 15% weight
    if ticket.assigned_agent_id is None:
        assignment_score = 15
        assignment_status = "Unassigned - needs immediate attention"
    elif ticket.status == "ASSIGNED":
        assignment_score = 10
        assignment_status = "Assigned but agent hasn't started"
    elif ticket.status == "IN_PROGRESS":
        assignment_score = 3
        assignment_status = "Agent actively working"
    else:
        assignment_score = 0
        assignment_status = "Being actively resolved"
    
    base_score += assignment_score
    factors.append({
        "factor": "Assignment Status",
        "value": assignment_status,
        "score": assignment_score,
        "weight": "15%",
        "explanation": "Unassigned tickets have highest risk"
    })
    
    # Factor 4: Agent Workload (0-10 points) - 10% weight
    if ticket.assigned_agent_id:
        agent_workload = calculate_agent_workload(ticket.assigned_agent_id, db)
        
        if agent_workload > 20:
            workload_score = 10
            workload_status = f"Very high workload ({agent_workload} points)"
        elif agent_workload > 10:
            workload_score = 5
            workload_status = f"High workload ({agent_workload} points)"
        else:
            workload_score = 0
            workload_status = f"Manageable workload ({agent_workload} points)"
        
        factors.append({
            "factor": "Agent Workload",
            "value": workload_status,
            "score": workload_score,
            "weight": "10%",
            "explanation": "Overloaded agents increase resolution time"
        })
        base_score += workload_score
    
    # Factor 5: Historical Performance (0-10 points) - 10% weight
    avg_resolution_time = get_avg_resolution_time(ticket.ticket_type, ticket.priority, db)
    if ticket.sla_resolution_due:
        time_until_due = (ticket.sla_resolution_due - datetime.now()).total_seconds() / 60
        
        if avg_resolution_time and avg_resolution_time > time_until_due:
            history_score = 10
            history_status = f"Similar tickets avg {int(avg_resolution_time)} min - likely to breach"
        elif avg_resolution_time and avg_resolution_time > (time_until_due * 0.7):
            history_score = 5
            history_status = f"Similar tickets avg {int(avg_resolution_time)} min - tight timeline"
        else:
            history_score = 0
            history_status = "Historical performance indicates on-time completion"
        
        factors.append({
            "factor": "Historical Performance",
            "value": history_status,
            "score": history_score,
            "weight": "10%",
            "explanation": "Past ticket resolution times predict future performance"
        })
        base_score += history_score
    
    # Ensure score is within 0-100 range
    final_score = min(100, max(0, base_score))
    
    # Determine risk level based on final score
    if final_score >= 86:
        risk_level = "CRITICAL"
    elif final_score >= 61:
        risk_level = "HIGH"
    elif final_score >= 31:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    return final_score, risk_level, factors


def calculate_agent_workload(agent_id: int, db: Session) -> int:
    """
    Calculate weighted workload for an agent.
    
    Args:
        agent_id: ID of the agent
        db: Database session
    
    Returns:
        Workload score (sum of weighted active tickets)
    """
    from app.models.ticket import Ticket
    
    # Get all active tickets assigned to this agent
    active_tickets = db.query(Ticket).filter(
        Ticket.assigned_agent_id == agent_id,
        Ticket.status.in_(["ASSIGNED", "IN_PROGRESS", "WAITING_FOR_USER"])
    ).all()
    
    # Weight by priority
    weight_map = {
        "P1_CRITICAL": 5,
        "P2_HIGH": 3,
        "P3_MEDIUM": 2,
        "P4_LOW": 1
    }
    
    total_workload = sum(weight_map.get(ticket.priority, 1) for ticket in active_tickets)
    return total_workload


def get_avg_resolution_time(ticket_type: str, priority: str, db: Session) -> float:
    """
    Get average resolution time for similar tickets from historical data.
    
    Args:
        ticket_type: Type of ticket
        priority: Priority level
        db: Database session
    
    Returns:
        Average resolution time in minutes, or None if no data
    """
    from app.models.ticket import Ticket
    from sqlalchemy import func
    
    # Query resolved tickets of same type and priority
    result = db.query(
        func.avg(
            func.timestampdiff(
                func.literal_column("MINUTE"),
                Ticket.created_at,
                Ticket.resolved_at
            )
        )
    ).filter(
        Ticket.ticket_type == ticket_type,
        Ticket.priority == priority,
        Ticket.status.in_(["RESOLVED", "CLOSED"]),
        Ticket.resolved_at.isnot(None)
    ).scalar()
    
    return float(result) if result else None


def get_risk_score_breakdown(risk_score: int, risk_level: str, factors: List[Dict]) -> dict:
    """
    Format the risk calculation explanation as a structured dict.
    
    Returns:
        Dictionary with risk calculation details
    """
    return {
        "final_score": risk_score,
        "risk_level": risk_level,
        "factors": factors,
        "algorithm": "Multi-factor rule-based AI (Priority + Deadline + Assignment + Workload + History)",
        "max_score": 100
    }
