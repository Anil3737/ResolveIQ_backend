import pymysql
import sys

def test_connection():
    try:
        connection = pymysql.connect(
            host='127.0.0.1',
            user='root',
            password='',
            charset='utf8mb4'
        )
        print("Successfully connected to MySQL server.")
        with connection.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS resolveiq_db")
            print("Database 'resolveiq_db' checked/created.")
        connection.commit()
        connection.close()
    except Exception as e:
        print(f"FAILED to connect to MySQL: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    test_connection()
