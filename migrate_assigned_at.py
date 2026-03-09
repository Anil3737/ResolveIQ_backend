# migrate_assigned_at.py
import pymysql
import os
from dotenv import load_dotenv

# Load .env from the backend directory
backend_dir = r"C:\Users\DELL\OneDrive\Desktop\resolveiq_backend"
load_dotenv(os.path.join(backend_dir, ".env"))

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "resolveiq")

def migrate():
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        with connection.cursor() as cursor:
            # Check if assigned_at column exists
            cursor.execute("SHOW COLUMNS FROM tickets LIKE 'assigned_at'")
            result = cursor.fetchone()
            if not result:
                print("Adding 'assigned_at' column to 'tickets' table...")
                cursor.execute("ALTER TABLE tickets ADD COLUMN assigned_at DATETIME NULL AFTER approved_at")
                connection.commit()
                print("Column added successfully!")
            else:
                print("'assigned_at' column already exists.")
    except Exception as e:
        print(f"Error migrating database: {e}")
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    migrate()
