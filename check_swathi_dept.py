from app import create_app
from app.models.user import User

app = create_app()
with app.app_context():
    swathi = User.query.filter_by(full_name='Swathi').first()
    if swathi and swathi.agent_profile:
        print(f"Swathi Dept ID: {swathi.agent_profile.department_id}")
        dept = swathi.agent_profile.department
        print(f"Swathi Dept Name: {dept.name if dept else 'None'}")
    else:
        print("Swathi or her profile not found")
