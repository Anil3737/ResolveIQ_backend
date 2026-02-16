from app.extensions import db
from app.models.sla_rule import SLARule

class SLAService:
    @staticmethod
    def create_or_update_rule(department_id, priority, sla_hours):
        rule = SLARule.query.filter_by(department_id=department_id, priority=priority).first()
        if rule:
            rule.sla_hours = sla_hours
        else:
            rule = SLARule(department_id=department_id, priority=priority, sla_hours=sla_hours)
            db.session.add(rule)
        
        db.session.commit()
        return rule
