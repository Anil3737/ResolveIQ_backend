# Database table creation script
# Run this to create all tables in the database

from app.database import engine, Base
from app.models import (
    Role, User, Department, Team, TeamMember,
    TicketType, SLAPolicy, Ticket, TicketComment,
    TicketLog, Assignment
)

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ All tables created successfully!")
        print("\nTables created:")
        print("  - roles")
        print("  - departments")
        print("  - users")
        print("  - teams")
        print("  - team_members")
        print("  - ticket_types")
        print("  - sla_policies")
        print("  - tickets")
        print("  - ticket_comments")
        print("  - ticket_logs")
        print("  - assignments")
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_tables()


from app.database import Base, engine
import app.models  # important: loads all models

print("Creating ResolveIQ Stage 1 tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
