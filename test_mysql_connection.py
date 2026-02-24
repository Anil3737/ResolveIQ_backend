# Test Database Connection Script
# Tests MySQL connection with current credentials

import pymysql
import os
from dotenv import load_dotenv

# Load .env from the same directory as the script
script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(script_dir, ".env"))

print("="*60)
print("  MySQL Connection Test")
print("="*60)

host = os.getenv("DB_HOST", "127.0.0.1")
user = os.getenv("DB_USER", "root")
password = os.getenv("DB_PASSWORD", "")
database = os.getenv("DB_NAME", "resolveiq")

for port in [3306, 3307]:
    print(f"\n--- Testing Port {port} ---")
    print(f"Attempting connection with:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  User: {user}")
    print(f"  Password: {'*' * len(password) if password else '(empty)'}")
    print(f"  Database: {database}")

    # Test 1: Try with provided password
    print(f"Test 1: Connecting with password from .env on port {port}...")
    try:
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connect_timeout=5
        )
        print(f"✓ SUCCESS! Connection established on port {port}.")
        connection.close()
        continue # Move to next port or finish
    except pymysql.err.OperationalError as e:
        error_code = e.args[0]
        if error_code == 1045:
            print(f"✗ FAILED: Access denied (incorrect password) on port {port}")
            print("\nTrying with empty password (XAMPP default)...")
            
            # Test 2: Try with empty password (XAMPP default)
            try:
                connection = pymysql.connect(
                    host=host,
                    port=port,
                    user=user,
                    password="",
                    database=database,
                    connect_timeout=5
                )
                print(f"✓ SUCCESS! Connection works with EMPTY password on port {port}.")
                connection.close()
            except Exception as e2:
                print(f"✗ Also failed with empty password: {e2}")
        elif error_code == 2003:
            print(f"✗ FAILED: Cannot connect to MySQL server on port {port}")
        else:
            print(f"✗ FAILED on port {port}: {e}")
    except Exception as e:
        print(f"✗ ERROR on port {port}: {e}")

print("\n" + "="*60)
