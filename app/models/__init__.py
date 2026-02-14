# Import all models for SQLAlchemy relationship mapping
from .role import Role
from .user import User
from .department import Department
from .team import Team
from .team_member import TeamMember
from .ticket_type import TicketType
from .sla_policy import SLAPolicy
from .ticket import Ticket
from .ticket_comment import TicketComment
from .ticket_log import TicketLog
from .assignment import Assignment
from .ticket_ai import TicketAI
from .ticket_history import TicketHistory

__all__ = [
    "Role",
    "User",
    "Department",
    "Team",
    "TeamMember",
    "TicketType",
    "SLAPolicy",
    "Ticket",
    "TicketComment",
    "TicketLog",
    "Assignment",
    "TicketAI",
    "TicketHistory",
]

