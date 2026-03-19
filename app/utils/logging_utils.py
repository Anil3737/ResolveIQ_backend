from app.extensions import db
from app.models.system_activity_log import SystemActivityLog
import logging

logger = logging.getLogger(__name__)

def log_activity(user_id, action_type, entity_type, entity_id, description):
    """
    Helper function to log system activity.
    Adds the log entry to the current database session.
    Does NOT commit the transaction.
    """
    try:
        log = SystemActivityLog(
            user_id=user_id,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description
        )
        db.session.add(log)
    except Exception as e:
        # We don't want logging to crash the main transaction, but we should know if it fails
        logger.warning(f"⚠️ Activity Logging Error: {str(e)}")
