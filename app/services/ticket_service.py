from datetime import datetime, timedelta
from app.extensions import db
from app.models.ticket import Ticket
from app.services.ai_scoring import AIScoringService
from app.services.audit_service import AuditService
from app.utils.logging_utils import log_activity

class TicketService:
    @staticmethod
    def create_ticket(data, user_id):
        """
        Creates a ticket with auto-generated AI metrics and SLA details.
        Ensures transactional safety, auto-escalation, and Team Lead assignment.
        """
        try:
            from app.models.user import TeamLeadProfile
            from app.ai.risk_engine import RiskEngine
            
            title = data.get('title')
            description = data.get('description')
            department_id = data.get('department_id')

            if not all([title, description, department_id]):
                raise ValueError("Missing required fields: title, description, or department_id")

            # 1. NEW: Modular Risk Engine Analysis
            risk_result = RiskEngine.calculate(title, description)
            
            # Legacy fields for backward compatibility/internal logic
            # (Keeping AIScoringService call for SLA/Priority for now, OR migrating them here)
            ai_meta = AIScoringService.compute_scoring(title, description)
            
            # Override with improved Risk Engine results
            score = risk_result['score']
            breach_risk = risk_result['risk']
            ai_explanation = risk_result['explanation']
            
            # --- AUTO ESCALATION LOGIC ---
            escalation_required = bool(ai_meta['escalation_required'])
            priority = ai_meta['priority']
            
            if score > 70:
                escalation_required = True
                priority = "P1"
                print(f"🔥 AUTO-ESCALATING TICKET: {title} (Score: {score})")

            # --- TEAM LEAD ASSIGNMENT LOGIC ---
            assigned_to = None
            tl_profile = TeamLeadProfile.query.filter_by(department_id=department_id).first()
            if tl_profile:
                assigned_to = tl_profile.user_id
                print(f"📍 AUTO-ASSIGNING TO TEAM LEAD: {tl_profile.user_id} for Dept: {department_id}")

            # 2. Map and Commit to DB
            ticket = Ticket(
                title=title,
                description=description,
                department_id=department_id,
                created_by=user_id,
                assigned_to=assigned_to,
                priority=priority,
                ai_score=score,
                breach_risk=breach_risk,
                escalation_required=escalation_required,
                ai_explanation=ai_explanation,
                sla_hours=ai_meta.get('sla_hours', 24),
                sla_deadline=ai_meta.get('sla_deadline'),
                status='OPEN'
            )

            db.session.add(ticket)
            db.session.flush() # Get ticket.id

            # Log Activity
            log_activity(
                user_id=user_id,
                action_type="TICKET_CREATED",
                entity_type="TICKET",
                entity_id=ticket.id,
                description=f"Ticket created: {title}"
            )

            if escalation_required:
                log_activity(
                    user_id=None,
                    action_type="AUTO_ESCALATED",
                    entity_type="TICKET",
                    entity_id=ticket.id,
                    description=f"Ticket auto escalated due to high risk ({score}%)"
                )

            db.session.commit()
            
            # 3. Log Actions
            try:
                AuditService.log_action(f"Created ticket: {title}", user_id, ticket.id)
                if escalation_required:
                    AuditService.log_action(f"AUTO_ESCALATED: High risk level ({score}%)", 1, ticket.id) # 1 = System/Admin
            except Exception as audit_err:
                print(f"⚠️ AUDIT LOG ERROR: {str(audit_err)}")
            
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
        
        if current_status == "OPEN" and new_status == "IN_PROGRESS":
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
            ticket.updated_at = datetime.utcnow()
            
            if new_status == "RESOLVED":
                ticket.resolved_at = datetime.utcnow()
            
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
            raise e
