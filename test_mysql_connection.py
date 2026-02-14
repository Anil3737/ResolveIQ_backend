# Test Database Connection Script
# Tests MySQL connection with current credentials

import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

print("="*60)
print("  MySQL Connection Test")
print("="*60)

host = os.getenv("DB_HOST", "localhost")
port = int(os.getenv("DB_PORT", "3307"))
user = os.getenv("DB_USER", "root")
password = os.getenv("DB_PASSWORD", "")
database = os.getenv("DB_NAME", "resolveiq")

print(f"\nAttempting connection with:")
print(f"  Host: {host}")
print(f"  Port: {port}")
print(f"  User: {user}")
print(f"  Password: {'*' * len(password) if password else '(empty)'}")
print(f"  Database: {database}")
print()

# Test 1: Try with provided password
print("Test 1: Connecting with password from .env...")
try:
    connection = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database
    )
    print("✓ SUCCESS! Connection established with provided password.")
    connection.close()
except pymysql.err.OperationalError as e:
    error_code = e.args[0]
    if error_code == 1045:
        print("✗ FAILED: Access denied (incorrect password)")
        print("\nTrying with empty password (XAMPP default)...")
        
        # Test 2: Try with empty password (XAMPP default)
        try:
            connection = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password="",
                database=database
            )
            print("✓ SUCCESS! Connection works with EMPTY password.")
            print("\n⚠️  ACTION REQUIRED:")
            print("   Update your .env file:")
            print("   Change: DB_PASSWORD=Chiru@143")
            print("   To:     DB_PASSWORD=")
            connection.close()
        except Exception as e2:
            print(f"✗ Also failed with empty password: {e2}")
            print("\n⚠️  SOLUTIONS:")
            print("   1. Check XAMPP MySQL is running on port 3307")
            print("   2. Find correct root password for your MySQL")
            print("   3. Or reset MySQL root password in XAMPP")
    elif error_code == 2003:
        print("✗ FAILED: Cannot connect to MySQL server")
        print("   Make sure XAMPP MySQL is running on port 3307")
    else:
        print(f"✗ FAILED: {e}")
except Exception as e:
    print(f"✗ ERROR: {e}")

print("\n" + "="*60)
