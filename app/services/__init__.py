# app/services/__init__.py

"""
Services module - Business logic and AI calculations
"""

from app.services.priority_calculator import calculate_priority, get_priority_score_breakdown
from app.services.risk_calculator import calculate_risk_score, get_risk_score_breakdown, calculate_agent_workload
from app.services.sla_calculator import calculate_sla_deadlines, is_sla_breached, get_time_remaining
from app.services.auto_assignment import auto_assign_ticket_to_team, find_best_agent_in_team, calculate_team_workload
from app.services.ticket_code_generator import generate_ticket_code, is_ticket_code_unique

__all__ = [
    # Priority calculation
    "calculate_priority",
    "get_priority_score_breakdown",
    
    # Risk calculation
    "calculate_risk_score",
    "get_risk_score_breakdown",
    "calculate_agent_workload",
    
    # SLA calculation
    "calculate_sla_deadlines",
    "is_sla_breached",
    "get_time_remaining",
    
    # Auto-assignment
    "auto_assign_ticket_to_team",
    "find_best_agent_in_team",
    "calculate_team_workload",
    
    # Ticket code
    "generate_ticket_code",
    "is_ticket_code_unique",
]
