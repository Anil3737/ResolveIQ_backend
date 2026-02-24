from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from app.extensions import db
from app.models.ticket import Ticket
from app.services.audit_service import AuditService
from app.utils.logging_utils import log_activity

def check_sla_breaches():
    """
    Background job to check for breached SLAs and auto-escalate.
    """
    with db.app.app_context():
        now = datetime.utcnow()
        # Find tickets that passed deadline, not resolved/closed, and not yet flagged as high-risk/P1
        # This prevents redundant updates and logs
        breached_tickets = Ticket.query.filter(
            Ticket.status.in_(['OPEN', 'IN_PROGRESS']),
            Ticket.sla_deadline <= now,
            (Ticket.escalation_required == False) | (Ticket.priority != 'P1')
        ).all()

        for ticket in breached_tickets:
            try:
                ticket.escalation_required = True
                ticket.priority = 'P1'
                ticket.updated_at = now
                
                AuditService.log_action(
                    "AUTO_ESCALATED: SLA Deadline Breached", 
                    1, # System/Admin user_id
                    ticket.id
                )
                
                # New System Activity Log
                log_activity(
                    user_id=None,
                    action_type="SLA_BREACHED",
                    entity_type="TICKET",
                    entity_id=ticket.id,
                    description="SLA deadline exceeded"
                )
                
                log_activity(
                    user_id=None,
                    action_type="AUTO_ESCALATED",
                    entity_type="TICKET",
                    entity_id=ticket.id,
                    description="Ticket auto escalated due to SLA breach"
                )
                print(f"⏰ SLA BREACH: Escalated Ticket {ticket.id}")
            except Exception as e:
                print(f"❌ Error auto-escalating ticket {ticket.id}: {e}")
        
        db.session.commit()

def auto_close_resolved_tickets():
    """
    Background job to close RESOLVED tickets after 48 hours.
    """
    with db.app.app_context():
        threshold = datetime.utcnow() - timedelta(hours=48)

        # Find RESOLVED tickets where resolved_at is older than 48h
        tickets_to_close = Ticket.query.filter(
            Ticket.status == 'RESOLVED',
            Ticket.resolved_at <= threshold
        ).all()

        for ticket in tickets_to_close:
            try:
                ticket.status = 'CLOSED'
                ticket.updated_at = datetime.utcnow()
                
                AuditService.log_action(
                    "AUTO_CLOSED: 48 hours passed since resolution", 
                    1, # System/Admin user_id
                    ticket.id
                )
                
                # New System Activity Log
                log_activity(
                    user_id=None,
                    action_type="AUTO_CLOSED",
                    entity_type="TICKET",
                    entity_id=ticket.id,
                    description="Ticket auto closed after 48 hours of resolution"
                )
                print(f"✅ AUTO-CLOSE: Closed Ticket {ticket.id}")
            except Exception as e:
                print(f"❌ Error auto-closing ticket {ticket.id}: {e}")

        db.session.commit()

def init_scheduler(app):
    """
    Initializes and starts the background scheduler.
    """
    # Attach app context to db for background tasks
    db.app = app
    
    scheduler = BackgroundScheduler()
    
    # Run SLA check every 5 minutes
    scheduler.add_job(
        func=check_sla_breaches,
        trigger="interval",
        minutes=5,
        id="sla_breach_check"
    )
    
    # Run auto-close check every 30 minutes
    scheduler.add_job(
        func=auto_close_resolved_tickets,
        trigger="interval",
        minutes=30,
        id="auto_close_check"
    )
    
    scheduler.start()
    print("🚀 Background Scheduler Started (SLA & Auto-Close Jobs active)")
