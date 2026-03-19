import logging
from datetime import datetime, timedelta, timezone
from app.extensions import db
from app.models.ticket import Ticket
from app.services.ai_scoring import AIScoringService
from app.services.audit_service import AuditService
from app.utils.logging_utils import log_activity
from app.utils.ticket_id_generator import generate_ticket_number
from app.utils.dept_isolation import resolve_department_id

logger = logging.getLogger(__name__)

class TicketService:
    @staticmethod
    def create_ticket(data, user_id):
        """
        Creates a ticket with auto-generated AI metrics and SLA details.
        Ensures transactional safety, auto-escalation, and Team Lead assignment.

        DUPLICATE DETECTION:
            If a ticket with the same issue_type, location, and department_id
            already exists (OPEN/APPROVED/IN_PROGRESS, within 15 min, and is a
            parent ticket), the new ticket is linked as a CHILD of that parent.

        DEPARTMENT OVERRIDE:
            The department_id is ALWAYS derived from issue_type regardless of what
            the frontend sends.  This prevents cross-department ticket injection.
        """
        MAX_RETRIES = 3
        last_error = None
        
        for attempt in range(MAX_RETRIES):
            try:
                from app.models.user import TeamLeadProfile
                from app.ai.risk_engine import RiskEngine
                import time

                title = data.get('title')
                description = data.get('description')
                issue_type = data.get('issue_type')        # New field (enforced override)
                department_id = data.get('department_id')  # Legacy field (fallback)
                expected_res_time_str = data.get('expected_resolution_time') 

                # ── STEP 1: Validate required fields ────────────────────────────
                if not all([title, description]):
                    raise ValueError("Missing required fields: title and description")

                # ── STEP 2: Enforce Issue Type → Department mapping ──────────────
                if issue_type:
                    department_id = resolve_department_id(issue_type)
                elif not department_id:
                    raise ValueError("Missing required field: provide either 'issue_type' or 'department_id'")

                if len(title) > 200:
                    raise ValueError("Title must be 200 characters or less")

                # ── STEP 3: Get location (from request, or from user profile) ────
                # location is stored on the ticket for duplicate detection purposes.
                location = data.get('location', '').strip() or None
                if not location:
                    # Fallback: resolve from the submitting employee's profile
                    from app.models.user import User
                    submitter = db.session.get(User, user_id)
                    if submitter and submitter.employee_profile:
                        location = submitter.employee_profile.location or None

                # ── STEP 4: Duplicate Detection ──────────────────────────────────
                # A duplicate exists when ALL of:
                #   - same issue_type
                #   - same location (skip detection if location is empty)
                #   - same department_id
                #   - status is OPEN, APPROVED, or IN_PROGRESS (not RESOLVED/CLOSED)
                #   - parent_ticket_id IS NULL (only look for root parent tickets)
                #   - created within the last 15 minutes
                parent_ticket = None
                if issue_type and location:
                    existing_ticket = (
                        Ticket.query
                        .filter(
                            Ticket.issue_type == issue_type,
                            Ticket.location == location,
                            Ticket.department_id == department_id,
                            Ticket.status.in_(["OPEN", "APPROVED", "IN_PROGRESS"]),
                            Ticket.parent_ticket_id.is_(None),
                            Ticket.created_at >= datetime.now(timezone.utc) - timedelta(minutes=15)
                        )
                        .order_by(Ticket.created_at.asc())
                        .first()
                    )

                    if existing_ticket:
                        # Always attach to the ROOT parent to prevent nested children.
                        # Edge case guard: if existing_ticket is somehow itself a child
                        # (race condition), resolve to its parent.
                        if existing_ticket.parent_ticket_id:
                            parent_ticket = db.session.get(Ticket, existing_ticket.parent_ticket_id)
                        else:
                            parent_ticket = existing_ticket

                # 1. AI Analysis
                risk_result = RiskEngine.calculate(title, description)
                ai_meta = AIScoringService.compute_scoring(title, description, department_id=department_id)
                
                score = risk_result['score']
                breach_risk = risk_result['risk']
                ai_explanation = risk_result['explanation']
                
                escalation_required = bool(ai_meta['escalation_required'])
                priority = ai_meta['priority']
                
                if score > 70:
                    escalation_required = True
                    priority = "P1"

                # 2. Map and Commit to DB
                ticket = Ticket(
                    title=title,
                    description=description,
                    department_id=department_id,
                    created_by=user_id,
                    status='OPEN',
                    priority=priority,
                    ai_score=score,
                    breach_risk=breach_risk,
                    escalation_required=escalation_required,
                    ai_explanation=ai_explanation,
                    sla_hours=ai_meta.get('sla_hours', 24),
                    sla_deadline=ai_meta.get('sla_deadline'),
                    # ── New fields ──
                    issue_type=issue_type or 'Other',
                    location=location,
                    parent_ticket_id=parent_ticket.id if parent_ticket else None,
                )

                # ── STEP 5: Override SLA if user provided expected resolution time ──
                if expected_res_time_str:
                    import re
                    match = re.search(r'(\d+)', str(expected_res_time_str))
                    if match:
                        user_sla_hours = int(match.group(1))
                        if user_sla_hours > 0:
                            ticket.sla_hours = user_sla_hours
                            ticket.sla_deadline = datetime.now(timezone.utc) + timedelta(hours=user_sla_hours)

                db.session.add(ticket)
                db.session.flush() 

                # 3. Generate ticket number (locks for update)
                ticket.ticket_number = generate_ticket_number(ticket.department_id)

                # 4. Logs
                if parent_ticket:
                    log_description = (
                        f"Child ticket created: {title} [{ticket.ticket_number}]"
                        f" linked to parent [{parent_ticket.ticket_number}]"
                    )
                else:
                    log_description = f"Ticket created: {title} [{ticket.ticket_number}]"

                log_activity(user_id=user_id, action_type="TICKET_CREATED", entity_type="TICKET", entity_id=ticket.id, description=log_description)
                AuditService.log_action(f"Created ticket: {title}", user_id, ticket.id)

                db.session.commit()

                # Attach parent_ticket reference for route layer to use in response
                ticket._parent_ticket = parent_ticket
                return ticket

            except Exception as e:
                db.session.rollback()
                # Check for MySQL Deadlock (OperationalError 1213)
                # We handle both sqlalchemy.exc.OperationalError and pymysql.err.OperationalError
                error_str = str(e)
                if ("1213" in error_str or "Deadlock found" in error_str) and attempt < MAX_RETRIES - 1:
                    logger.warning(f"DEADLOCK DETECTED (Attempt {attempt + 1}/{MAX_RETRIES}). Retrying in 0.5s...")
                    time.sleep(0.5)
                    continue
                
                logger.error(f"TICKET CREATION ERROR: {error_str}", exc_info=True)
                raise e

    @staticmethod
    def assign_ticket(ticket_id, agent_id, lead_id):
        ticket = Ticket.query.get_or_404(ticket_id)
        ticket.assigned_to = agent_id
        ticket.assigned_at = datetime.now(timezone.utc)
        ticket.accepted_at = datetime.now(timezone.utc) # Automatically accept for visibility
        if not ticket.approved_at:
            ticket.approved_at = datetime.now(timezone.utc)
        ticket.status = 'IN_PROGRESS'
        
        # ── Propagate assignment to all child tickets ────────────────────────────
        # Child tickets inherit the same agent and status as the parent
        Ticket.query.filter_by(parent_ticket_id=ticket_id).update({
            "assigned_to": agent_id,
            "status": "IN_PROGRESS",
            "assigned_at": datetime.now(timezone.utc),
            "accepted_at": datetime.now(timezone.utc), # Sync accepted_at
            "updated_at": datetime.now(timezone.utc)
        }, synchronize_session=False)

        # Log Activity
        log_activity(
            user_id=lead_id,
            action_type="TICKET_ASSIGNED",
            entity_type="TICKET",
            entity_id=ticket_id,
            description=f"Assigned to agent {agent_id}"
        )
        
        db.session.commit()

        AuditService.log_action(f"Assigned ticket to agent {agent_id}", lead_id, ticket_id)
        return ticket

    @staticmethod
    def update_ticket_status(ticket_id, new_status, user):
        """
        Updates ticket status with strict role-based transition rules.
        When a parent ticket reaches RESOLVED or CLOSED, all child tickets
        are automatically synchronized to the same status.
        """
        ticket = Ticket.query.get_or_404(ticket_id)
        current_status = ticket.status.upper() if ticket.status else "OPEN"
        new_status = new_status.upper()
        role = user.role.name if user.role else "EMPLOYEE"

        # 1. Prevent updates on CLOSED tickets
        if current_status == "CLOSED":
            raise ValueError("Cannot update status of a CLOSED ticket")

        # 2. Strict Transition Validation
        allowed = False
        
        if (current_status == "OPEN" and new_status == "APPROVED"):
            if role in ["TEAM_LEAD", "ADMIN"]: # TL or Admin can approve
                allowed = True
        
        elif (current_status in ["OPEN", "APPROVED"]) and new_status == "IN_PROGRESS":
            if role in ["TEAM_LEAD", "AGENT"]:
                allowed = True
        
        elif current_status == "IN_PROGRESS" and new_status == "RESOLVED":
            if role == "AGENT" and ticket.assigned_to == user.id:
                allowed = True
        
        elif current_status == "RESOLVED" and new_status == "CLOSED":
            if role in ["ADMIN"] or (role == "EMPLOYEE" and ticket.created_by == user.id):
                allowed = True

        # Custom handles for ESCALATED (treat as OPEN or IN_PROGRESS depending on logic)
        elif current_status == "ESCALATED" and new_status == "IN_PROGRESS":
             if role in ["TEAM_LEAD", "AGENT"]:
                allowed = True

        if not allowed:
            raise PermissionError(f"Invalid transition from {current_status} to {new_status} for role {role}")

        # 3. Update execution
        try:
            ticket.status = new_status
            ticket.updated_at = datetime.now(timezone.utc)
            
            if new_status == "RESOLVED":
                ticket.resolved_at = datetime.now(timezone.utc)
            
            if new_status == "CLOSED":
                ticket.closed_at = datetime.now(timezone.utc)

            # ── Propagate status to child tickets (RESOLVED and CLOSED) ─────────
            # Child tickets are informational — they always mirror the parent's status.
            if new_status in ("RESOLVED", "CLOSED"):
                child_updates = {
                    "status": new_status,
                    "updated_at": datetime.now(timezone.utc),
                }
                if new_status == "RESOLVED":
                    child_updates["resolved_at"] = datetime.now(timezone.utc)
                if new_status == "CLOSED":
                    child_updates["closed_at"] = datetime.now(timezone.utc)

                Ticket.query.filter_by(parent_ticket_id=ticket.id).update(
                    child_updates, synchronize_session=False
                )

            # Log Activity
            action_type = "STATUS_UPDATED"
            description = f"Status changed from {current_status} to {new_status}"
            
            if new_status == "CLOSED":
                action_type = "MANUAL_CLOSED"
                description = f"Ticket manually closed by user"
            
            log_activity(
                user_id=user.id,
                action_type=action_type,
                entity_type="TICKET",
                entity_id=ticket.id,
                description=description
            )
            
            db.session.commit()
            
            # Log the change
            AuditService.log_action(
                f"STATUS_UPDATED: {current_status} -> {new_status}", 
                user.id, 
                ticket.id
            )
            
            return ticket
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating ticket status: {str(e)}", exc_info=True)
            raise e

    @staticmethod
    def resolve_escalation(ticket_id, user_id):
        """
        Clears escalation flags from a ticket.
        """
        ticket = Ticket.query.get_or_404(ticket_id)
        ticket.escalation_required = False
        if ticket.status == 'ESCALATED':
            # Revert to OPEN or APPROVED if it was manually escalated
            # logic: if it has an approver, it's APPROVED, else OPEN
            ticket.status = 'APPROVED' if ticket.approved_at else 'OPEN'
            
        description = f"Escalation resolved by Admin {user_id}"
        log_activity(
            user_id=user_id,
            action_type="ESCALATION_RESOLVED",
            entity_type="TICKET",
            entity_id=ticket.id,
            description=description
        )
        AuditService.log_action(description, user_id, ticket.id)
        db.session.commit()
        return ticket
