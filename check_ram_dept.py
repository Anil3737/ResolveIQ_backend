from app import create_app
from app.models.user import User

app = create_app()
with app.app_context():
    ram = User.query.get(10)
    if ram and ram.team_lead_profile:
        print(f"Ram Dept ID: {ram.team_lead_profile.department_id}")
        dept = ram.team_lead_profile.department
        print(f"Ram Dept Name: {dept.name if dept else 'None'}")
    else:
        print("Ram or his profile not found")
