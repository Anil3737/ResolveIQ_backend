from datetime import datetime, timedelta
from app.extensions import db
from app.models.ticket import Ticket
from app.models.sla_rule import SLARule
from app.services.ai_service import AIService
from app.services.audit_service import AuditService

class TicketService:
    @staticmethod
    def create_ticket(data, user_id):
        title = data.get('title')
        description = data.get('description')
        department_id = data.get('department_id')

        # AI Analysis
        ai_result = AIService.calculate_score(title, description)
        
        # Get SLA Rule
        sla_rule = SLARule.query.filter_by(
            department_id=department_id, 
            priority=ai_result['priority']
        ).first()
        
        sla_hours = sla_rule.sla_hours if sla_rule else 24
        sla_deadline = datetime.utcnow() + timedelta(hours=sla_hours)

        ticket = Ticket(
            title=title,
            description=description,
            department_id=department_id,
            created_by=user_id,
            priority=ai_result['priority'],
            ai_score=ai_result['score'],
            breach_risk=ai_result['breach_risk'],
            sla_hours=sla_hours,
            sla_deadline=sla_deadline,
            status='OPEN'
        )

        db.session.add(ticket)
        db.session.commit()

        AuditService.log_action(f"Created ticket: {title}", user_id, ticket.id)

        return ticket

    @staticmethod
    def assign_ticket(ticket_id, agent_id, lead_id):
        ticket = Ticket.query.get_or_404(ticket_id)
        ticket.assigned_to = agent_id
        ticket.status = 'IN_PROGRESS'
        db.session.commit()

        AuditService.log_action(f"Assigned ticket to agent {agent_id}", lead_id, ticket_id)
        return ticket

    @staticmethod
    def update_status(ticket_id, status, user_id):
        ticket = Ticket.query.get_or_404(ticket_id)
        ticket.status = status
        
        if status == 'RESOLVED':
            ticket.resolved_at = datetime.utcnow()
            
        db.session.commit()

        AuditService.log_action(f"Updated status to {status}", user_id, ticket_id)
        return ticket
