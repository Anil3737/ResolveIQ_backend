# quick_seed.py - Simplest possible seed without password hashing issues

import pymysql
from app.config import settings

# Simple plain password hash for testing (NOT SECURE - just for testing)
import hashlib
def quick_hash(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def quick_seed():
    connection =pymysql.connect(
        host=settings.DB_HOST,
        port=int(settings.DB_PORT),
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME
    )
    
    try:
        with connection.cursor() as cursor:
            print("\n🌱 Quick seeding...")
            
            # Roles
            cursor.execute("DELETE FROM roles")
            cursor.execute("INSERT INTO roles (name) VALUES ('ADMIN'), ('TEAM_LEAD'), ('AGENT'), ('EMPLOYEE')")
            
            # Departments  
            cursor.execute("DELETE FROM departments")
            cursor.execute("INSERT INTO departments (name, description) VALUES ('IT', 'IT')")
            
            # Users
            cursor.execute("DELETE FROM users")
            cursor.execute("""
                INSERT INTO users (full_name, email, phone, password_hash, role_id, department_id, is_active)
                VALUES 
                ('Admin', 'admin@resolveiq.com', '1111', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/Lew.cRW6hUAJy0C1O', 1, 1, 1),
                ('TeamLead', 'teamlead@resolveiq.com', '2222', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/Lew.cRW6hUAJy0C1O', 2, 1, 1),
                ('Agent', 'agent@resolveiq.com', '3333', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/Lew.cRW6hUAJy0C1O', 3, 1, 1),
                ('Employee', 'employee@resolveiq.com', '4444', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/Lew.cRW6hUAJy0C1O', 4, 1, 1)
            """)
            
            connection.commit()
            print("✅ Seeded!")
            print("\nCredentials (all passwords: 'Admin@123'):")
            print("  admin@resolveiq.com")
            print("  teamlead@resolveiq.com")
            print("  agent@resolveiq.com") 
            print("  employee@resolveiq.com\n")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        connection.close()

if __name__ == "__main__":
    quick_seed()
