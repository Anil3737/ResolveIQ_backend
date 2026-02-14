# direct_seed.py - Direct SQL insertion to avoid SQLAlchemy issues

import pymysql
from app.config import settings
from app.utils.password_utils import hash_password

def direct_seed():
    # Connect to database
    connection = pymysql.connect(
        host=settings.DB_HOST,
        port=int(settings.DB_PORT),
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    
    try:
        with connection.cursor() as cursor:
            print("\n🌱 Seeding database with SQL...")
            
            # Insert roles
            print("Creating roles...")
            cursor.execute("DELETE FROM roles")
            roles = [
                ("ADMIN",),
                ("TEAM_LEAD",),
                ("AGENT",),
                ("EMPLOYEE",)
            ]
            cursor.executemany("INSERT INTO roles (name) VALUES (%s)", roles)
            connection.commit()
            print("  ✅ Created 4 roles")
            
            # Insert departments
            print("Creating departments...")
            cursor.execute("DELETE FROM departments")
            departments = [
                ("IT", "Information Technology"),
                ("HR", "Human Resources"),
                ("Finance", "Finance and Accounting"),
                ("Operations", "Business Operations")
            ]
            cursor.executemany(
                "INSERT INTO departments (name, description) VALUES (%s, %s)",
                departments
            )
            connection.commit()
            print("  ✅ Created 4 departments")
            
            # Get role and department IDs
            cursor.execute("SELECT id, name FROM roles")
            role_map = {row['name']: row['id'] for row in cursor.fetchall()}
            
            cursor.execute("SELECT id, name FROM departments")
            dept_map = {row['name']: row['id'] for row in cursor.fetchall()}
            
            # Insert users
            print("Creating users...")
            cursor.execute("DELETE FROM users")
            
            # Hash passwords first
            admin_pwd = hash_password("Admin@123")
            lead_pwd = hash_password("TeamLead@123")
            agent_pwd = hash_password("Agent@123")
            employee_pwd = hash_password("Employee@123")
            
            users = [
                ("Admin User", "admin@resolveiq.com", "1111111111",
                 admin_pwd, role_map["ADMIN"], dept_map["IT"], True),
                ("Team Lead", "teamlead@resolveiq.com", "2222222222",
                 lead_pwd, role_map["TEAM_LEAD"], dept_map["IT"], True),
                ("Agent User", "agent@resolveiq.com", "3333333333",
                 agent_pwd, role_map["AGENT"], dept_map["IT"], True),
                ("Employee User", "employee@resolveiq.com", "4444444444",
                 employee_pwd, role_map["EMPLOYEE"], dept_map["Finance"], True),
            ]
            
            cursor.executemany(
                """INSERT INTO users 
                   (full_name, email, phone, password_hash, role_id, department_id, is_active)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                users
            )
            connection.commit()
            print("  ✅ Created 4 users")
            
            # Insert ticket types
            print("Creating ticket types...")
            cursor.execute("DELETE FROM ticket_types")
            ticket_types = [
                ("Bug", 3),
                ("Feature Request", 2),
                ("Question", 1),
                ("Incident", 4)
            ]
            cursor.executemany(
                "INSERT INTO ticket_types (name, severity_level) VALUES (%s, %s)",
                ticket_types
            )
            connection.commit()
            print("  ✅ Created 4 ticket types")
            
            print("\n✅ DATABASE SEEDED SUCCESSFULLY!")
            print("\n🔑 Test Credentials:")
            print("   Admin:     admin@resolveiq.com / Admin@123")
            print("   TeamLead:  teamlead@resolveiq.com / TeamLead@123")
            print("   Agent:     agent@resolveiq.com / Agent@123")
            print("   Employee:  employee@resolveiq.com / Employee@123")
            print()
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        connection.rollback()
    finally:
        connection.close()


if __name__ == "__main__":
    direct_seed()
