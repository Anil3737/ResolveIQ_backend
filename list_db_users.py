import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def list_users():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', '127.0.0.1'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'resolveiq')
        )
        cursor = conn.cursor(dictionary=True)
        
        # We fetch email and name. Passwords should be hashed, so we won't try to "read" them as plain text.
        # But for this demo system, we can check if they are hashed or what.
        cursor.execute("SELECT u.name, u.email, r.name as role FROM users u JOIN roles r ON u.role_id = r.id")
        users = cursor.fetchall()
        
        print(f"{'NAME':<20} | {'EMAIL':<30} | {'ROLE':<10}")
        print("-" * 65)
        for user in users:
            print(f"{user['name']:<20} | {user['email']:<30} | {user['role']:<10}")
            
    except mysql.connector.Error as err:
        print(f"❌ Database Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    list_users()
