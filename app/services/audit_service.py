from app.extensions import db
from app.models.audit_log import AuditLog

class AuditService:
    @staticmethod
    def log_action(action, user_id, ticket_id=None):
        log = AuditLog(
            action=action,
            performed_by=user_id,
            ticket_id=ticket_id
        )
        db.session.add(log)
        db.session.commit()
