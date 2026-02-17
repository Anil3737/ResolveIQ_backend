from datetime import datetime, timedelta
from app.extensions import db
from app.models.ticket import Ticket
from app.services.ai_scoring import AIScoringService
from app.services.audit_service import AuditService

class TicketService:
    @staticmethod
    def create_ticket(data, user_id):
        """
        Input: title, description, department_id
        Auto-generates: ai_score, breach_risk, priority, sla_hours, sla_deadline, escalation_required
        """
        title = data.get('title')
        description = data.get('description')
        department_id = data.get('department_id')
        
        # 1. Auto-generate AI metrics and SLA details via deterministic service
        ai_result = AIScoringService.compute_scoring(title, description)

        # 2. Map and Commit to DB
        ticket = Ticket(
            title=title,
            description=description,
            department_id=department_id,
            created_by=user_id,
            priority=ai_result['priority'],
            ai_score=ai_result['ai_score'],
            breach_risk=ai_result['breach_risk'],
            escalation_required=bool(ai_result['escalation_required']),
            sla_hours=ai_result['sla_hours'],
            sla_deadline=ai_result['sla_deadline'],
            status='OPEN'
        )

        try:
            db.session.add(ticket)
            db.session.commit()
            
            # 3. Log Action
            AuditService.log_action(f"Created ticket: {title}", user_id, ticket.id)
            return ticket
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ DATABASE ERROR: {str(e)}")
            raise e

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
        
        # Validation if necessary (e.g. Ensure status is in allowed Enum)
        ticket.status = status
        
        if status == 'RESOLVED':
            ticket.resolved_at = datetime.utcnow()
            
        db.session.commit()

        AuditService.log_action(f"Updated status to {status}", user_id, ticket_id)
        return ticket
