from app import create_app
from app.extensions import db
from app.models.user import User, TeamLeadProfile, AgentProfile, EmployeeProfile
from sqlalchemy import inspect, text

app = create_app()

with app.app_context():
    print("=" * 60)
    print("DATABASE INSPECTION - ROLE-BASED PROFILES")
    print("=" * 60)
    
    # Check tables
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"\nTables in database: {tables}")
    
    # 1. Audit Users Table
    if 'users' in tables:
        columns = [c['name'] for c in inspector.get_columns('users')]
        print(f"\nUsers table columns: {columns}")
        
        # Check if old columns are gone
        redundant = ['department_id', 'location', 'team_lead_id']
        still_there = [c for c in redundant if c in columns]
        if not still_there:
            print("✅ CLEAN: Redundant columns removed from 'users' table.")
        else:
            print(f"❌ WARNING: Redundant columns still exist: {still_there}")
            
        user_count = User.query.count()
        print(f"Total Users: {user_count}")
    
    # 2. Audit Profile Tables
    profile_tables = ['team_lead_profiles', 'agent_profiles', 'employee_profiles']
    for p_table in profile_tables:
        if p_table in tables:
            count = db.session.execute(text(f"SELECT count(*) FROM {p_table}")).scalar()
            print(f"\n✅ {p_table}: {count} records found")
            
            # Show a few sample records
            results = db.session.execute(text(f"SELECT * FROM {p_table} LIMIT 3")).fetchall()
            for r in results:
                print(f"   Record: {r}")
        else:
            print(f"\n❌ ERROR: {p_table} missing!")

    print("\n" + "=" * 60)
    print("MIGRATION VERIFICATION COMPLETE")
    print("=" * 60)
