from app import create_app
from app.models.user import User

app = create_app()
with app.app_context():
    users = User.query.all()
    print("ID | Name | Role | Team Lead ID")
    print("-" * 40)
    for u in users:
        role_name = u.role.name if u.role else "None"
        lead_id = u.agent_profile.team_lead_id if u.agent_profile else "None"
        print(f"{u.id} | {u.full_name} | {role_name} | {lead_id}")
