import os
import logging
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from app.extensions import db
from app.models.ticket import Ticket
from app.models.user import User
from app.services.audit_service import AuditService
from app.utils.logging_utils import log_activity

logger = logging.getLogger(__name__)

# Module-level guards and state
_scheduler = None
_app = None

def check_sla_breaches():
    """Checks for breached SLAs and auto-escalates."""
    if not _app: return
    with _app.app_context():
        now = datetime.now(timezone.utc)
        # SLA Deadline Breach Check
        # To avoid naive/aware comparison issues in Python, we filter in SQL but also handle cautiously
        breached_tickets = Ticket.query.filter(
            Ticket.parent_ticket_id == None,
            Ticket.status.in_(['OPEN', 'IN_PROGRESS']),
            Ticket.sla_deadline.isnot(None)
        ).all()

        for ticket in breached_tickets:
            # Python-level comparison: make sure ticket.sla_deadline is aware if naive
            sla_deadline = ticket.sla_deadline.replace(tzinfo=timezone.utc) if ticket.sla_deadline.tzinfo is None else ticket.sla_deadline
            if sla_deadline > now and not (ticket.escalation_required and ticket.priority == 'P1'):
                 # Not breached or already escalated? Skip logic below if not actually breached
                 if sla_deadline > now: continue
            
            # Re-verify breach
            if sla_deadline <= now:
                try:
                    ticket.escalation_required = True
                    ticket.priority = 'P1'
                    ticket.updated_at = now
                    
                    # Resolve system user ID (admin@resolveiq.com)
                    admin = User.query.filter_by(email='admin@resolveiq.com').first()
                    admin_id = admin.id if admin else 1

                    AuditService.log_action(
                        "AUTO_ESCALATED: SLA Deadline Breached", 
                        admin_id,
                        ticket.id
                    )
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
                    logger.info(f"SLA BREACH: Escalated Ticket {ticket.id}")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error auto-escalating ticket {ticket.id}: {e}", exc_info=True)
                else:
                    db.session.commit()

def auto_approve_open_tickets():
    """Auto-approves OPEN tickets after 15 minutes."""
    if not _app: return
    with _app.app_context():
        now = datetime.now(timezone.utc)
        threshold = now - timedelta(minutes=15)

        pending_tickets = Ticket.query.filter(
            Ticket.parent_ticket_id == None,
            Ticket.status == 'OPEN',
            Ticket.assigned_to == None
        ).all()

        for ticket in pending_tickets:
            created_at = ticket.created_at.replace(tzinfo=timezone.utc) if ticket.created_at.tzinfo is None else ticket.created_at
            if created_at <= threshold:
                try:
                    ticket.status = 'APPROVED'
                    ticket.approved_at = now
                    ticket.updated_at = now
                    log_activity(
                        user_id=None,
                        action_type="AUTO_APPROVED",
                        entity_type="TICKET",
                        entity_id=ticket.id,
                        description="Ticket auto-approved after 15 minutes of inactivity"
                    )
                    logger.info(f"AUTO-APPROVE: Ticket {ticket.id} is now visible to agents")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error auto-approving ticket {ticket.id}: {e}", exc_info=True)
                else:
                    db.session.commit()

def auto_close_resolved_tickets():
    """Closes RESOLVED tickets after 10 minutes."""
    if not _app: return
    with _app.app_context():
        now = datetime.now(timezone.utc)
        threshold = now - timedelta(minutes=10)

        tickets_to_close = Ticket.query.filter(
            Ticket.parent_ticket_id == None,
            Ticket.status == 'RESOLVED'
        ).all()

        for ticket in tickets_to_close:
            resolved_at = ticket.resolved_at.replace(tzinfo=timezone.utc) if ticket.resolved_at and ticket.resolved_at.tzinfo is None else ticket.resolved_at
            if resolved_at and resolved_at <= threshold:
                try:
                    ticket.status = 'CLOSED'
                    ticket.closed_at = now
                    ticket.updated_at = now

                    # Synchronise children to CLOSED when the parent auto-closes
                    Ticket.query.filter_by(parent_ticket_id=ticket.id).update({
                        "status": "CLOSED",
                        "closed_at": now,
                        "updated_at": now
                    }, synchronize_session=False)

                    # Resolve system user ID (admin@resolveiq.com)
                    admin = User.query.filter_by(email='admin@resolveiq.com').first()
                    admin_id = admin.id if admin else 1

                    AuditService.log_action(
                        "AUTO_CLOSED: 10 minutes passed since resolution",
                        admin_id,
                        ticket.id
                    )
                    log_activity(
                        user_id=None,
                        action_type="AUTO_CLOSED",
                        entity_type="TICKET",
                        entity_id=ticket.id,
                        description="Ticket auto closed after 10 minutes of resolution"
                    )
                    logger.info(f"AUTO-CLOSE: Closed Ticket {ticket.id}")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error auto-closing ticket {ticket.id}: {e}", exc_info=True)
                else:
                    db.session.commit()

def init_scheduler(app):
    """
    Initializes and starts the background scheduler safely for multi-worker environments.
    Uses SQLAlchemyJobStore to coordinate jobs across processes.
    """
    global _scheduler, _app

    # Set app reference for top-level task functions
    _app = app

    # Werkzeug reloader guard
    if os.environ.get("WERKZEUG_RUN_MAIN") == "false":
        return

    # Prevent double-init
    if _scheduler is not None and _scheduler.running:
        return

    jobstores = {
        'default': SQLAlchemyJobStore(url=app.config['SQLALCHEMY_DATABASE_URI'])
    }
    executors = {
        'default': ThreadPoolExecutor(max_workers=3)
    }
    job_defaults = {
        'coalesce': True,
        'max_instances': 1,
        'misfire_grace_time': 30
    }

    _scheduler = BackgroundScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone="UTC"
    )

    # Use replace_existing=True to ensure jobs are correctly updated in the DB store
    _scheduler.add_job(
        func=check_sla_breaches,
        trigger="interval",
        minutes=5,
        id="sla_breach_check",
        replace_existing=True
    )
    _scheduler.add_job(
        func=auto_close_resolved_tickets,
        trigger="interval",
        minutes=1,
        id="auto_close_check",
        replace_existing=True
    )
    _scheduler.add_job(
        func=auto_approve_open_tickets,
        trigger="interval",
        minutes=1,
        id="auto_approve_check",
        replace_existing=True
    )

    _scheduler.start()
    logger.info("[Scheduler] Production-Safe Background Scheduler Started (SQLAlchemyJobStore active)")
