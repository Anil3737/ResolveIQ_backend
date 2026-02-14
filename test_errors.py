# test_errors.py - Simple error test

try:
    print("Step 1: Testing database connection...")
    from app.database import engine
    with engine.connect() as conn:
        result = conn.exec_driver_sql("SELECT 1")
        print("SUCCESS: Database connection works")
except Exception as e:
    print(f"ERROR in database connection: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

try:
    print("\nStep 2: Testing model imports...")
    from app.models import Role, User, Team
    print("SUCCESS: Model imports work")
except Exception as e:
    print(f"ERROR in model imports: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

try:
    print("\nStep 3: Creating tables...")
    from app.database import Base
    Base.metadata.create_all(bind=engine)
    print("SUCCESS: Tables created or already exist")
except Exception as e:
    print(f"ERROR creating tables: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

try:
    print("\nStep 4: Testing app import...")
    from app.main import app
    print("SUCCESS: App imported successfully")
    print(f"App title: {app.title}")
except Exception as e:
    print(f"ERROR importing app: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "="*50)
print("ALL TESTS PASSED!")
print("="*50)
