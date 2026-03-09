from app import create_app
from app.extensions import db
from app.models.user import User, TeamLeadProfile, AgentProfile, Department
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("--- DEPARTMENTS ---")
    depts = Department.query.all()
    for d in depts:
        print(f"ID: {d.id} | Name: {d.name}")
    
    print("\n--- SOFTWARE DEPARTMENT MEMBERS ---")
    # Search for departments containing "Software"
    software_depts = Department.query.filter(Department.name.like('%Software%')).all()
    if not software_depts:
        print("No department found with 'Software' in name.")
        # Try generic search for anyone with "Software" in their profile or issues
    else:
        for sd in software_depts:
            print(f"\nDepartment: {sd.name} (ID: {sd.id})")
            
            # Team Leads
            leads = User.query.join(TeamLeadProfile).filter(TeamLeadProfile.department_id == sd.id).all()
            print("  Team Leads:")
            for l in leads:
                print(f"    - {l.full_name} ({l.email})")
                
            # Agents
            agents = User.query.join(AgentProfile).filter(AgentProfile.department_id == sd.id).all()
            print("  Agents:")
            for a in agents:
                print(f"    - {a.full_name} ({a.email})")

    print("\n--- ALL TEAM LEADS ---")
    tls = User.query.join(TeamLeadProfile).all()
    for tl in tls:
        dept_name = tl.team_lead_profile.department.name if tl.team_lead_profile.department else "None"
        print(f"Name: {tl.full_name} | Email: {tl.email} | Dept: {dept_name}")

    print("\n--- ALL AGENTS ---")
    ags = User.query.join(AgentProfile).all()
    for ag in ags:
        dept_name = ag.agent_profile.department.name if ag.agent_profile.department else "None"
        print(f"Name: {ag.full_name} | Email: {ag.email} | Dept: {dept_name}")
