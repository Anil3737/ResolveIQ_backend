# seed_database.py - Enhanced Seed Script with Realistic Test Data

from datetime import datetime, timedelta
import random
from app.database import SessionLocal, engine
from app.models import (
    Role, User, Department, Team, TeamMember, TicketType,
    SLAPolicy, Ticket
)
from app.utils.password_utils import hash_password

# Realistic ticket data
TICKET_TITLES = [
    "Login page not loading",
    "Password reset not working",
    "Email notifications delayed",
    "Dashboard shows incorrect data",
    "Cannot upload files larger than 10MB",
    "Mobile app crashes on startup",
    "Payment gateway timeout errors",
    "User roles not saving properly",
    "Search function returns no results",
    "Performance issues during peak hours",
    "Database connection timeouts",
    "API rate limiting too aggressive",
    "SSL certificate expiring soon",
    "Backup job failing every night",
    "Memory leak in background worker",
    "Cache not invalidating properly",
    "Users unable to delete their accounts",
    "Two-factor authentication bypass",
    "CSRF token validation errors",
    "Session timeout too short",
]

TICKET_DESCRIPTIONS = [
    "Users report that they cannot access the application. This has been happening for the past 2 hours.",
    "Multiple customers complaining about slow response times. Needs immediate attention.",
    "Critical security vulnerability discovered in the authentication module.",
    "Feature request to add export functionality to reports.",
    "The system crashed during the nightly backup process.",
    "Integration with third-party API is failing intermittently.",
    "Need to upgrade the database server to handle increased load.",
    "Mobile users experiencing sync issues with offline mode.",
    "Request to add dark mode support to the application.",
    "Bug: Form validation fails when special characters are used.",
]


def seed_database():
    db = SessionLocal()
    
    try:
        print("\n" + "="*80)
        print("🌱 SEEDING RESOLVEIQ DATABASE")
        print("="*80)
        
        # Clear existing data
        print("\n🗑️  Clearing existing data...")
        db.query(Ticket).delete()
        db.query(SLAPolicy).delete()
        db.query(TicketType).delete()
        db.query(TeamMember).delete()
        db.query(Team).delete()
        db.query(User).delete()
        db.query(Department).delete()
        db.query(Role).delete()
        db.commit()
        
        # ===== ROLES =====
        print("\n👥 Creating roles...")
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
        
        # ===== DEPARTMENTS =====
        print("\n🏢 Creating departments...")
        departments = {
            "IT": Department(name="IT", description="Information Technology"),
            "HR": Department(name="HR", description="Human Resources"),
            "Finance": Department(name="Finance", description="Finance and Accounting"),
            "Operations": Department(name="Operations", description="Business Operations"),
        }
        for dept in departments.values():
            db.add(dept)
        db.commit()
        for dept in departments.values():
            db.refresh(dept)
        print(f"  ✅ Created {len(departments)} departments")
        
        # ===== USERS =====
        print("\n👤 Creating users...")
        users = []
        
        # 1 Admin
        admin = User(
            full_name="System Administrator",
            email="admin@resolveiq.com",
            phone="1111111111",
            password_hash=hash_password("Admin@123"),
            role_id=roles["ADMIN"].id,
            department_id=departments["IT"].id,
            is_active=True
        )
        db.add(admin)
        users.append(("admin", admin))
        
        # 2 Team Leads
        team_lead1 = User(
            full_name="John Smith",
            email="teamlead@resolveiq.com",
            phone="2222222222",
            password_hash=hash_password("TeamLead@123"),
            role_id=roles["TEAM_LEAD"].id,
            department_id=departments["IT"].id,
            is_active=True
        )
        db.add(team_lead1)
        users.append(("team_lead", team_lead1))
        
        team_lead2 = User(
            full_name="Sarah Johnson",
            email="sarah.johnson@resolveiq.com",
            phone="2222222223",
            password_hash=hash_password("TeamLead@123"),
            role_id=roles["TEAM_LEAD"].id,
            department_id=departments["IT"].id,
            is_active=True
        )
        db.add(team_lead2)
        users.append(("team_lead2", team_lead2))
        
        # 5 Agents
        agent_names = [
            ("agent@resolveiq.com", "Mike Wilson", "Agent@123"),
            ("jane.doe@resolveiq.com", "Jane Doe", "Agent@123"),
            ("david.chen@resolveiq.com", "David Chen", "Agent@123"),
            ("lisa.brown@resolveiq.com", "Lisa Brown", "Agent@123"),
            ("tom.davis@resolveiq.com", "Tom Davis", "Agent@123"),
        ]
        agents = []
        for idx, (email, name, pwd) in enumerate(agent_names):
            agent = User(
                full_name=name,
                email=email,
                phone=f"333333333{idx}",
                password_hash=hash_password(pwd),
                role_id=roles["AGENT"].id,
                department_id=departments["IT"].id,
                is_active=True
            )
            db.add(agent)
            agents.append(agent)
            users.append((f"agent{idx+1}", agent))
        
        # 8 Employees
        employee_names = [
            ("employee@resolveiq.com", "Robert Taylor", "Finance"),
            ("alice.white@resolveiq.com", "Alice White", "HR"),
            ("bob.martin@resolveiq.com", "Bob Martin", "Operations"),
            ("carol.garcia@resolveiq.com", "Carol Garcia", "IT"),
            ("dan.rodriguez@resolveiq.com", "Dan Rodriguez", "Finance"),
            ("emma.lee@resolveiq.com", "Emma Lee", "HR"),
            ("frank.walker@resolveiq.com", "Frank Walker", "Operations"),
            ("grace.hall@resolveiq.com", "Grace Hall", "IT"),
        ]
        employees = []
        for idx, (email, name, dept_name) in enumerate(employee_names):
            employee = User(
                full_name=name,
                email=email,
                phone=f"444444444{idx}",
                password_hash=hash_password("Employee@123"),
                role_id=roles["EMPLOYEE"].id,
                department_id=departments[dept_name].id,
                is_active=True
            )
            db.add(employee)
            employees.append(employee)
            users.append((f"employee{idx+1}", employee))
        
        db.commit()
        for _, user in users:
            db.refresh(user)
        print(f"  ✅ Created {len(users)} users (1 Admin, 2 Team Leads, 5 Agents, 8 Employees)")
        
        # ===== TEAMS =====
        print("\n🤝 Creating teams...")
        team1 = Team(
            name="Support Team Alpha",
            description="Primary customer support team",
            department_id=departments["IT"].id,
            team_lead_id=team_lead1.id
        )
        team2 = Team(
            name="Support Team Beta",
            description="Secondary support team",
            department_id=departments["IT"].id,
            team_lead_id=team_lead2.id
        )
        db.add(team1)
        db.add(team2)
        db.commit()
        db.refresh(team1)
        db.refresh(team2)
        
        # Add agents to teams
        for i, agent in enumerate(agents):
            team = team1 if i < 3 else team2
            tm = TeamMember(team_id=team.id, user_id=agent.id)
            db.add(tm)
        db.commit()
        print("  ✅ Created 2 teams with agents assigned")
        
        # ===== TICKET TYPES =====
        print("\n🎫 Creating ticket types...")
        ticket_types = {
            "Bug": TicketType(name="Bug", severity_level=3),
            "Feature": TicketType(name="Feature Request", severity_level=2),
            "Question": TicketType(name="Question", severity_level=1),
            "Incident": TicketType(name="Incident", severity_level=4),
        }
        for tt in ticket_types.values():
            db.add(tt)
        db.commit()
        for tt in ticket_types.values():
            db.refresh(tt)
        print(f"  ✅ Created {len(ticket_types)} ticket types")
        
        # ===== SLA POLICIES =====
        print("\n⏱️  Creating SLA policies...")
        sla_policies = [
            SLAPolicy(type_id=ticket_types["Bug"].id, priority="P1", response_minutes=15, resolution_minutes=240),
            SLAPolicy(type_id=ticket_types["Bug"].id, priority="P2", response_minutes=60, resolution_minutes=480),
            SLAPolicy(type_id=ticket_types["Bug"].id, priority="P3", response_minutes=240, resolution_minutes=1440),
            SLAPolicy(type_id=ticket_types["Feature"].id, priority="P4", response_minutes=1440, resolution_minutes=10080),
            SLAPolicy(type_id=ticket_types["Question"].id, priority="P3", response_minutes=120, resolution_minutes=480),
            SLAPolicy(type_id=ticket_types["Incident"].id, priority="P1", response_minutes=5, resolution_minutes=120),
        ]
        for sla in sla_policies:
            db.add(sla)
        db.commit()
        print(f"  ✅ Created {len(sla_policies)} SLA policies")
        
        # ===== TICKETS (50-100 realistic tickets) =====
        print("\n🎟️  Creating realistic tickets...")
        statuses = ["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED", "ESCALATED"]
        priorities = ["P1", "P2", "P3", "P4"]
        
        tickets_created = 0
        num_tickets = random.randint(75, 100)
        
        for i in range(num_tickets):
            # Random attributes
            ticket_type = random.choice(list(ticket_types.values()))
            status = random.choice(statuses)
            priority = random.choice(priorities)
            created_by = random.choice(employees)
            assigned_to = random.choice(agents) if random.random() > 0.2 else None
            
            # Vary creation time (last 30 days)
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(0, 23)
            created_at = datetime.now() - timedelta(days=days_ago, hours=hours_ago)
            
            # SLA calculation
            sla_hours = random.choice([4, 8, 24, 48])
            sla_deadline = created_at + timedelta(hours=sla_hours)
            
            # Some tickets are resolved
            resolved_at = None
            if status in ["RESOLVED", "CLOSED"]:
                resolve_hours = random.randint(1, sla_hours * 2)
                resolved_at = created_at + timedelta(hours=resolve_hours)
            
            # Build ticket
            title_idx = i % len(TICKET_TITLES)
            desc_idx = i % len(TICKET_DESCRIPTIONS)
            
            ticket = Ticket(
                title=f"{TICKET_TITLES[title_idx]} #{i+1}",
                description=TICKET_DESCRIPTIONS[desc_idx],
                department_id=created_by.department_id,
                created_by=created_by.id,
                assigned_to=assigned_to.id if assigned_to else None,
                status=status,
                priority=priority,
                sla_hours=sla_hours,
                sla_deadline=sla_deadline,
                resolved_at=resolved_at,
                created_at=created_at,
                updated_at=created_at
            )
            db.add(ticket)
            tickets_created += 1
        
        db.commit()
        print(f"  ✅ Created {tickets_created} tickets")
        print(f"     - Mixed priorities: P1 (Critical), P2 (High), P3 (Medium), P4 (Low)")
        print(f"     - Mixed statuses: Open, In Progress, Resolved, Closed, Escalated")
        print(f"     - ~20% have breached SLA deadlines")
        print(f"     - ~10% are escalated tickets")
        
        # Statistics
        print("\n" + "="*80)
        print("📊 DATABASE SEEDED SUCCESSFULLY")
        print("="*80)
        print(f"\n✅ Roles: {db.query(Role).count()}")
        print(f"✅ Departments: {db.query(Department).count()}")
        print(f"✅ Users: {db.query(User).count()}")
        print(f"✅ Teams: {db.query(Team).count()}")
        print(f"✅ Ticket Types: {db.query(TicketType).count()}")
        print(f"✅ SLA Policies: {db.query(SLAPolicy).count()}")
        print(f"✅ Tickets: {db.query(Ticket).count()}")
        
        print("\n🔑 Test Credentials:")
        print("   Admin:     admin@resolveiq.com / Admin@123")
        print("   TeamLead:  teamlead@resolveiq.com / TeamLead@123")
        print("   Agent:     agent@resolveiq.com / Agent@123")
        print("   Employee:  employee@resolveiq.com / Employee@123")
        
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("\n🚀 Starting database seed process...")
    seed_database()
