from app.extensions import db
from datetime import datetime, timezone

class PasswordResetRequest(db.Model):
    __tablename__ = 'password_reset_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    emp_id = db.Column(db.String(50), nullable=False)
    temp_password = db.Column(db.String(50), nullable=True) # Plain for user retrieval
    temp_password_hash = db.Column(db.String(255), nullable=True) # Hashed for checking
    status = db.Column(db.Enum('PENDING', 'APPROVED', 'DECLINED'), default='PENDING')
    requested_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    processed_at = db.Column(db.DateTime, nullable=True)
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('reset_requests', lazy=True))
    processor = db.relationship('User', foreign_keys=[processed_by])

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.full_name if self.user else "Unknown",
            "role": self.user.role.name if self.user and self.user.role else "EMPLOYEE",
            "email": self.email,
            "emp_id": self.emp_id,
            "status": self.status,
            "temp_password": self.temp_password,
            "requested_at": self.requested_at.isoformat() if self.requested_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "processed_by": self.processed_by
        }
