import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def create_table():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', '127.0.0.1'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'resolveiq')
        )
        cursor = conn.cursor()
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS system_activity_logs (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NULL,
            action_type VARCHAR(50) NOT NULL,
            entity_type VARCHAR(50) NOT NULL,
            entity_id INT NULL,
            description TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );
        """
        cursor.execute(create_table_sql)
        
        # Add indexes as requested
        try:
            cursor.execute("CREATE INDEX idx_action_type ON system_activity_logs(action_type)")
            cursor.execute("CREATE INDEX idx_created_at ON system_activity_logs(created_at)")
            cursor.execute("CREATE INDEX idx_user_id ON system_activity_logs(user_id)")
        except mysql.connector.Error as err:
            # If indexes already exist, skip
            print(f"Index creation notice: {err}")

        conn.commit()
        print("✅ Success: system_activity_logs table and indexes verified.")
        
    except mysql.connector.Error as err:
        print(f"❌ Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    create_table()
