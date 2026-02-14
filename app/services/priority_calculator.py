# app/services/priority_calculator.py

"""
Explainable Priority Calculation Service
Calculates ticket priority based on severity, urgency, impact, keywords, and ticket type.
Returns both the priority level and detailed explanation of scoring factors.
"""

from typing import Tuple, List


def calculate_priority(
    severity: int,
    urgency: int,
    impact: int,
    title: str,
    description: str,
    ticket_type: str
) -> Tuple[str, List[str]]:
    """
    Calculate ticket priority with explainable scoring.
    
    Args:
        severity: 1-5 scale
        urgency: 1-5 scale
        impact: 1-5 scale (business impact)
        title: Ticket title
        description: Ticket description
        ticket_type: Type of ticket
    
    Returns:
        Tuple of (priority_level, factors_list)
        - priority_level: P1_CRITICAL, P2_HIGH, P3_MEDIUM, or P4_LOW
        - factors_list: List of explanation strings for the score
    """
    factors = []
    total_score = 0
    
    # Factor 1: Severity (0-5 points)
    total_score += severity
    factors.append(f"Severity level: {severity}/5")
    
    # Factor 2: Urgency (0-5 points)
    total_score += urgency
    factors.append(f"Urgency level: {urgency}/5")
    
    # Factor 3: Business Impact (0-5 points)
    total_score += impact
    factors.append(f"Business impact: {impact}/5")
    
    # Factor 4: Keyword Detection (0-5 bonus points)
    critical_keywords = [
        "down", "outage", "critical", "urgent", "security breach",
        "data loss", "server crash", "cannot access", "system failure"
    ]
    high_keywords = [
        "slow", "error", "bug", "issue", "problem", "not working",
        "broken", "failed", "timeout"
    ]
    
    text = (title + " " + description).lower()
    keyword_bonus = 0
    
    if any(keyword in text for keyword in critical_keywords):
        keyword_bonus = 5
        matched = [kw for kw in critical_keywords if kw in text]
        factors.append(f"Critical keywords detected: {', '.join(matched[:2])}")
    elif any(keyword in text for keyword in high_keywords):
        keyword_bonus = 2
        matched = [kw for kw in high_keywords if kw in text]
        factors.append(f"High-priority keywords detected: {', '.join(matched[:2])}")
    
    total_score += keyword_bonus
    
    # Factor 5: Ticket Type Bonus (0-3 points)
    critical_types = ["Security Incident", "Network Issue"]
    high_types = ["Hardware Issue", "Software Bug"]
    
    type_bonus = 0
    if ticket_type in critical_types:
        type_bonus = 3
        factors.append(f"Critical ticket type: {ticket_type}")
    elif ticket_type in high_types:
        type_bonus = 1
        factors.append(f"High-impact ticket type: {ticket_type}")
    
    total_score += type_bonus
    
    # Determine priority level based on total score
    # Max possible score: 5 + 5 + 5 + 5 + 3 = 23
    if total_score >= 18:
        priority = "P1_CRITICAL"
    elif total_score >= 13:
        priority = "P2_HIGH"
    elif total_score >= 8:
        priority = "P3_MEDIUM"
    else:
        priority = "P4_LOW"
    
    return priority, factors


def get_priority_score_breakdown(priority: str, factors: List[str]) -> dict:
    """
    Format the priority calculation explanation as a structured dict.
    
    Returns:
        Dictionary with priority calculation details
    """
    return {
        "final_priority": priority,
        "factors": factors,
        "algorithm": "Rule-based scoring (Severity + Urgency + Impact + Keywords + Type)"
    }
