import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def add_indexes():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', '127.0.0.1'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'resolveiq')
        )
        cursor = conn.cursor()
        
        print("Adding indexes to 'tickets' table...")
        
        indexes = [
            ("idx_ai_score", "ai_score"),
            ("idx_status", "status"),
            ("idx_sla_deadline", "sla_deadline"),
            ("idx_escalation", "escalation_required")
        ]
        
        for index_name, column in indexes:
            try:
                cursor.execute(f"CREATE INDEX {index_name} ON tickets({column})")
                print(f"✅ Created index {index_name} on {column}")
            except mysql.connector.Error as err:
                if err.errno == 1061: # Duplicate key name
                    print(f"ℹ️  Index {index_name} already exists.")
                else:
                    print(f"❌ Error creating index {index_name}: {err}")
        
        conn.commit()
        print("✅ Indexing process completed.")
        
    except mysql.connector.Error as err:
        print(f"❌ Database Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    add_indexes()
