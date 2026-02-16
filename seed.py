from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.department import Department
from app.models.sla_rule import SLARule

def seed():
    app = create_app()
    with app.app_context():
        # Create Tables
        db.create_all()

        # Seed Departments
        departments = ['Engineering', 'HR', 'Finance', 'Sales & Marketing', 'Customer Support', 'Operations']
        for dept_name in departments:
            if not Department.query.filter_by(name=dept_name).first():
                db.session.add(Department(name=dept_name))
        db.session.commit()

        # Seed Users
        users = [
            {"name": "Admin User", "email": "admin@resolveiq.com", "password": "Admin@123", "role": "ADMIN"},
            {"name": "Team Lead", "email": "lead@resolveiq.com", "password": "Lead@123", "role": "TEAM_LEAD"},
            {"name": "Support Agent", "email": "agent@resolveiq.com", "password": "Agent@123", "role": "AGENT"},
            {"name": "Employee User", "email": "employee@resolveiq.com", "password": "Emp@123", "role": "EMPLOYEE"}
        ]

        for u_data in users:
            if not User.query.filter_by(email=u_data['email']).first():
                user = User(name=u_data['name'], email=u_data['email'], role=u_data['role'])
                user.set_password(u_data['password'])
                db.session.add(user)
        db.session.commit()

        # Seed SLA Rules
        # For Engineering (id 1)
        eng = Department.query.filter_by(name='Engineering').first()
        if eng:
            rules = [
                ('CRITICAL', 4),
                ('HIGH', 8),
                ('MEDIUM', 24),
                ('LOW', 48)
            ]
            for priority, hours in rules:
                if not SLARule.query.filter_by(department_id=eng.id, priority=priority).first():
                    db.session.add(SLARule(department_id=eng.id, priority=priority, sla_hours=hours))
        
        db.session.commit()
        print("Database seeded successfully!")

if __name__ == "__main__":
    seed()
