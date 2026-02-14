# test_login.py - Quick login test

import requests

BASE_URL = "http://127.0.0.1:8000"

print("\n🧪 Testing login endpoint...\n")

# Test login
response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    json={"email": "admin@resolveiq.com", "password": "Admin@123"}
)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}\n")

if response.status_code == 200:
    print("✅ LOGIN SUCCESSFUL!")
    print(f"Token: {response.json()['access_token'][:50]}...")
    print(f"User: {response.json()['user']}")
else:
    print(f"❌ Login failed: {response.text}")
