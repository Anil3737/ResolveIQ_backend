import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def check_depts():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', '127.0.0.1'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'resolveiq')
        )
        cursor = conn.cursor(dictionary=True)
        
        print("\n--- DEPARTMENTS ---")
        cursor.execute("SELECT id, name FROM departments ORDER BY id")
        for row in cursor.fetchall():
            print(f"ID: {row['id']} | Name: {row['name']}")
            
        print("\n--- USERS (Pushpa, Pratap, Gopi) ---")
        cursor.execute("SELECT u.full_name, u.email, u.role_id, r.name as role_name, u.department_id FROM users u JOIN roles r ON u.role_id = r.id WHERE u.full_name LIKE '%Pushpa%' OR u.full_name LIKE '%Pratap%' OR u.full_name LIKE '%Gopi%'")
        for row in cursor.fetchall():
            print(f"Name: {row['full_name']} | Role: {row['role_name']} | Dept ID: {row['department_id']}")

        print("\n--- TICKET COUNT BY DEPT ---")
        cursor.execute("SELECT department_id, COUNT(*) as count FROM tickets GROUP BY department_id")
        for row in cursor.fetchall():
            print(f"Dept ID: {row['department_id']} | Count: {row['count']}")
            
    except mysql.connector.Error as err:
        print(f"❌ Database Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    check_depts()
