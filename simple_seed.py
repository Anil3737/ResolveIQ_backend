# simple_seed.py - Simplified seed without complex tickets

from app.database import SessionLocal
from app.models import Role, User, Department, TicketType, SLAPolicy
from app.utils.password_utils import hash_password

def simple_seed():
    db = SessionLocal()
    
    try:
        print("\n🌱 Seeding basic data...")
        
        # Clear existing
        db.query(SLAPolicy).delete()
        db.query(TicketType).delete()
        db.query(User).delete()
        db.query(Department).delete()
        db.query(Role).delete()
        db.commit()
        
        # Roles
        print("Creating roles...")
        roles = {
            "ADMIN": Role(name="ADMIN"),
            "TEAM_LEAD": Role(name="TEAM_LEAD"),
            "AGENT": Role(name="AGENT"),
            "EMPLOYEE": Role(name="EMPLOYEE"),
        }
        for role in roles.values():
            db.add(role)
        db.commit()
        for role in roles.values():
            db.refresh(role)
        print(f"  ✅ Created {len(roles)} roles")
        
        # Departments
        print("Creating departments...")
        departments = {
            "IT": Department(name="IT", description="Information Technology"),
            "HR": Department(name="HR", description="Human Resources"),
            "Finance": Department(name="Finance", description="Finance"),
            "Operations": Department(name="Operations", description="Operations"),
        }
        for dept in departments.values():
            db.add(dept)
        db.commit()
        for dept in departments.values():
            db.refresh(dept)
        print(f"  ✅ Created {len(departments)} departments")
        
        # Users
        print("Creating users...")
        admin = User(
            full_name="Admin User",
            email="admin@resolveiq.com",
            phone="1111111111",
            password_hash=hash_password("Admin@123"),
            role_id=roles["ADMIN"].id,
            department_id=departments["IT"].id,
            is_active=True
        )
        db.add(admin)
        
        team_lead = User(
            full_name="Team Lead",
            email="teamlead@resolveiq.com",
            phone="2222222222",
            password_hash=hash_password("TeamLead@123"),
            role_id=roles["TEAM_LEAD"].id,
            department_id=departments["IT"].id,
            is_active=True
        )
        db.add(team_lead)
        
        agent = User(
            full_name="Agent User",
            email="agent@resolveiq.com",
            phone="3333333333",
            password_hash=hash_password("Agent@123"),
            role_id=roles["AGENT"].id,
            department_id=departments["IT"].id,
            is_active=True
        )
        db.add(agent)
        
        employee = User(
            full_name="Employee User",
            email="employee@resolveiq.com",
            phone="4444444444",
            password_hash=hash_password("Employee@123"),
            role_id=roles["EMPLOYEE"].id,
            department_id=departments["Finance"].id,
            is_active=True
        )
        db.add(employee)
        
        db.commit()
        print("  ✅ Created 4 users")
        
        # Ticket Types
        print("Creating ticket types...")
        ticket_types = {
            "Bug": TicketType(name="Bug", severity_level=3),
            "Feature": TicketType(name="Feature Request", severity_level=2),
            "Question": TicketType(name="Question", severity_level=1),
            "Incident": TicketType(name="Incident", severity_level=4),
        }
        for tt in ticket_types.values():
            db.add(tt)
        db.commit()
        print(f"  ✅ Created {len(ticket_types)} ticket types")
        
        print("\n✅ DATABASE SEEDED SUCCESSFULLY!")
        print("\n🔑 Test Credentials:")
        print("   Admin:     admin@resolveiq.com / Admin@123")
        print("   TeamLead:  teamlead@resolveiq.com / TeamLead@123")
        print("   Agent:     agent@resolveiq.com / Agent@123")
        print("   Employee:  employee@resolveiq.com / Employee@123")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    simple_seed()
