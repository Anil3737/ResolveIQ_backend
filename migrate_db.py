# migrate_db.py
import pymysql
import os
from dotenv import load_dotenv

# Load .env from the backend directory
backend_dir = r"c:\Users\DELL\OneDrive\Desktop\resolveiq_backend"
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
            # Check if location column exists
            cursor.execute("SHOW COLUMNS FROM users LIKE 'location'")
            result = cursor.fetchone()
            if not result:
                print("Adding 'location' column to 'users' table...")
                cursor.execute("ALTER TABLE users ADD COLUMN location VARCHAR(100) NULL AFTER phone")
                connection.commit()
                print("Column added successfully!")
            else:
                print("'location' column already exists.")
    except Exception as e:
        print(f"Error migrating database: {e}")
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    migrate()
