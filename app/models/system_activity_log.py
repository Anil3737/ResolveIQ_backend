from datetime import datetime, timezone
from app.extensions import db

def format_datetime(dt):
    if dt:
        return dt.replace(tzinfo=timezone.utc).isoformat()
    return None

class SystemActivityLog(db.Model):
    __tablename__ = 'system_activity_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action_type = db.Column(db.String(50), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('activity_logs', lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "user": self.user.full_name if self.user else "System",
            "role": self.user.role.name if self.user and self.user.role else "N/A",
            "action_type": self.action_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "description": self.description,
            "created_at": format_datetime(self.created_at)
        }

    def to_dict_full(self):
        result = self.to_dict()
        if self.user:
            result["user_email"] = self.user.email
        return result
