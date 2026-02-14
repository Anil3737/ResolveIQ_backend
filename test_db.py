import sys
import traceback
import pymysql

# First test direct connection
try:
    print("=" * 50)
    print("TEST 1: Direct PyMySQL Connection")
    print("=" * 50)
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='Chiru@143',
        database='resolveiq'
    )
    print("✓ Direct PyMySQL connection successful!")
    conn.close()
except Exception as e:
    print(f"✗ Direct connection failed: {e}")
    sys.exit(1)

# Test SQLAlchemy connection
try:
    print("\n" + "=" * 50)
    print("TEST 2: SQLAlchemy Engine Connection")
    print("=" * 50)
    from app.database import engine
    print(f"Database URL: {engine.url}")
    with engine.connect() as conn:
        print("✓ SQLAlchemy engine connection successful!")
except Exception as e:
    print(f"✗ SQLAlchemy connection failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test model imports
try:
    print("\n" + "=" * 50)
    print("TEST 3: Model Imports")
    print("=" * 50)
    from app.models import Role, User, Team, TeamMember, TicketType, SLAPolicy
    print("✓ All models imported successfully!")
except Exception as e:
    print(f"✗ Model import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test table creation
try:
    print("\n" + "=" * 50)
    print("TEST 4: Create Database Tables")
    print("=" * 50)
    from app.database import Base
    Base.metadata.create_all(bind=engine)
    print("✓ All tables created successfully!")
    
    # List tables
    with engine.connect() as conn:
        result = conn.execute("SHOW TABLES")
        tables = result.fetchall()
        print(f"\nCreated tables: {[t[0] for t in tables]}")
    
except Exception as e:
    print(f"✗ Table creation failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 50)
print("ALL TESTS PASSED! ✓")
print("=" * 50)
