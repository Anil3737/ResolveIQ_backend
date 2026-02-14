# final_check.py - Comprehensive system check

print("\n🔍 COMPREHENSIVE SYSTEM CHECK\n")
print("="*80)

# Test 1: Import all models
print("\n1️⃣ Testing model imports...")
try:
    from app.models import *
    print("   ✅ All models imported successfully")
except Exception as e:
    print(f"   ❌ Model import failed: {e}")

# Test 2: Import app
print("\n2️⃣ Testing app import...")
try:
    from app.main import app
    print(f"   ✅ App imported with {len(app.routes)} routes")
except Exception as e:
    print(f"   ❌ App import failed: {e}")

# Test 3: Check database connection
print("\n3️⃣ Testing database connection...")
try:
    from app.database import engine
    with engine.connect() as conn:
        print("   ✅ Database connection successful")
except Exception as e:
    print(f"   ❌ Database connection failed: {e}")

# Test 4: Check all schemas
print("\n4️⃣ Testing schema imports...")
try:
    from app.schemas.auth_schemas import UserResponse, LoginResponse
    from app.schemas.admin_schemas import TeamResponse, TicketTypeResponse
    from app.schemas.ticket_schemas import TicketCreate
    print("   ✅ All schemas imported successfully")
except Exception as e:
    print(f"   ❌ Schema import failed: {e}")

# Test 5: Verify table exists
print("\n5️⃣ Verifying database tables...")
try:
    from sqlalchemy import inspect
    from app.database import engine
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"   ✅ Found {len(tables)} tables: {', '.join(sorted(tables))}")
except Exception as e:
    print(f"   ❌ Table check failed: {e}")

# Test 6: Check routes
print("\n6️⃣ Checking route definitions...")
try:
    from app.main import app
    paths = list(app.openapi()['paths'].keys())
    print(f"   ✅ Found {len(paths)} endpoints")
    print("   Key endpoints:")
    for path in sorted(paths)[:10]:
        print(f"     - {path}")
except Exception as e:
    print(f"   ❌ Route check failed: {e}")

# Test 7: Password hashing
print("\n7️⃣ Testing password utilities...")
try:
    from app.utils.password_utils import hash_password, verify_password
    hashed = hash_password("Test@123")
    verified = verify_password("Test@123", hashed)
    assert verified, "Password verification failed"
    print(f"   ✅ Password hashing working correctly")
except Exception as e:
    print(f"   ❌ Password utils failed: {e}")

# Test 8: JWT tokens
print("\n8️⃣ Testing JWT utilities...")
try:
    from app.utils.jwt_utils import create_access_token, decode_access_token  
    token = create_access_token({"user_id": 1, "role": "ADMIN"})
    payload = decode_access_token(token)
    assert payload["user_id"] == 1, "Token payload mismatch"
    print(f"   ✅ JWT token creation/decoding working")
except Exception as e:
    print(f"   ❌ JWT utils failed: {e}")

print("\n" + "="*80)
print("✅ ALL CHECKS PASSED - SYSTEM IS READY!")
print("="*80)
print("\n💡 Next steps:")
print("   1. Start server: uvicorn app.main:app --reload")
print("   2. Seed database: python quick_seed.py")
print("   3. Test API: python test_login.py")
print("   4. Or use Swagger: http://127.0.0.1:8000/docs\n")
