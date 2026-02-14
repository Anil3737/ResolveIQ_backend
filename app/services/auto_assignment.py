# app/services/auto_assignment.py

"""
Auto-Assignment Service
Automatically assigns tickets to teams based on department and workload.
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.models.team import Team
from app.models.ticket import Ticket
from app.services.risk_calculator import calculate_agent_workload


def auto_assign_ticket_to_team(ticket: "Ticket", db: Session) -> Optional[int]:
    """
    Automatically assign a ticket to the best team in the department.
    
    Logic:
    1. Find all teams in the ticket's department
    2. Calculate workload for each team
    3. Assign to team with lowest workload
    
    Args:
        ticket: Ticket object with department_id set
        db: Database session
    
    Returns:
        team_id of assigned team, or None if no teams available
    """
    # Get all teams in this department
    teams = db.query(Team).filter(
        Team.department_id == ticket.department_id
    ).all()
    
    if not teams:
        return None
    
    # If only one team, assign to it
    if len(teams) == 1:
        return teams[0].id
    
    # Calculate workload for each team
    best_team = None
    lowest_workload = float('inf')
    
    for team in teams:
        workload = calculate_team_workload(team.id, db)
        if workload < lowest_workload:
            lowest_workload = workload
            best_team = team
    
    return best_team.id if best_team else teams[0].id


def calculate_team_workload(team_id: int, db: Session) -> int:
    """
    Calculate total workload for a team.
    
    Workload = sum of all assigned tickets' weighted priorities
    
    Args:
        team_id: ID of the team
        db: Database session
    
    Returns:
        Total workload score
    """
    from app.models.team_member import TeamMember
    
    # Get all agents in the team
    team_members = db.query(TeamMember).filter(
        TeamMember.team_id == team_id
    ).all()
    
    if not team_members:
        return 0
    
    # Sum workloads of all agents
    total_workload = 0
    for member in team_members:
        agent_workload = calculate_agent_workload(member.user_id, db)
        total_workload += agent_workload
    
    return total_workload


def find_best_agent_in_team(team_id: int, db: Session) -> Optional[int]:
    """
    Find the agent with the lowest workload in a team.
    
    Args:
        team_id: ID of the team
        db: Database session
    
    Returns:
        user_id of best agent, or None if no agents available
    """
    from app.models.team_member import TeamMember
    from app.models.user import User
    from app.models.role import Role
    
    # Get all agents in the team
    agents = db.query(User).join(TeamMember).join(Role).filter(
        TeamMember.team_id == team_id,
        Role.name == "AGENT"
    ).all()
    
    if not agents:
        return None
    
    # Find agent with lowest workload
    best_agent = None
    lowest_workload = float('inf')
    
    for agent in agents:
        workload = calculate_agent_workload(agent.id, db)
        if workload < lowest_workload:
            lowest_workload = workload
            best_agent = agent
    
    return best_agent.id if best_agent else None
