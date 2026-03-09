from app import create_app
from app.models.user import User
from app.models.ticket import Ticket
from app.models.role import Role
from app.extensions import db
import json

def simulate_pushpa_fetch():
    app = create_app()
    with app.app_context():
        # Find Pushpa
        pushpa = User.query.filter(User.full_name.like('%Pushpa%')).first()
        if not pushpa:
            print("❌ Pushpa not found!")
            return
            
        print(f"✅ Found Pushpa: ID {pushpa.id}, Role {pushpa.role.name}")
        
        # Check her profile
        profile = pushpa.team_lead_profile
        if not profile:
            print("❌ Pushpa has no TeamLeadProfile!")
            return
            
        print(f"✅ Profile Dept ID: {profile.department_id} ({profile.department.name})")
        
        # Simulating logic from ticket_routes.py
        dept_id = profile.department_id
        query = Ticket.query.filter(Ticket.department_id == dept_id).order_by(Ticket.created_at.desc())
        
        # Print the SQL query
        print(f"\n🔍 SQL Query:\n{query}")
        
        tickets = query.all()
        print(f"\n📦 Found {len(tickets)} tickets for Dept {dept_id}:")
        for t in tickets:
            print(f"   - [{t.ticket_number}] {t.title} (Dept: {t.department.name}, ID: {t.department_id})")

        # Check if any Dept 4 tickets are in the result (they shouldn't be!)
        dept_4_tickets = [t for t in tickets if t.department_id == 4]
        if dept_4_tickets:
            print(f"\n🔥 BUG ALERT! Found {len(dept_4_tickets)} Dept 4 tickets in Dept 3 results!")
        else:
            print("\n✅ No Dept 4 tickets found in Dept 3 results.")

if __name__ == "__main__":
    simulate_pushpa_fetch()
