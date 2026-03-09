# verify_assigned_at.py
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

def verify():
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        with connection.cursor() as cursor:
            cursor.execute("DESCRIBE tickets")
            columns = [col[0] for col in cursor.fetchall()]
            if 'assigned_at' in columns:
                print("Column 'assigned_at' exists in 'tickets' table.")
            else:
                print("Column 'assigned_at' NOT found in 'tickets' table.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    verify()
