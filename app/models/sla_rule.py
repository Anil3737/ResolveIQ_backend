from app.extensions import db

class SLARule(db.Model):
    __tablename__ = 'sla_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    priority = db.Column(db.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL'), nullable=False)
    sla_hours = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "department_id": self.department_id,
            "priority": self.priority,
            "sla_hours": self.sla_hours
        }
