import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def verify_table():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', '127.0.0.1'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'resolveiq')
        )
        cursor = conn.cursor()
        
        cursor.execute("SHOW TABLES LIKE 'system_activity_logs'")
        result = cursor.fetchone()
        
        if result:
            print("✅ Success: Table 'system_activity_logs' exists.")
            cursor.execute("DESCRIBE system_activity_logs")
            columns = cursor.fetchall()
            for col in columns:
                print(f"   - {col[0]}: {col[1]}")
        else:
            print("❌ Error: Table 'system_activity_logs' still does not exist.")
            
    except Exception as e:
        print(f"❌ Verification Error: {str(e)}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    verify_table()
