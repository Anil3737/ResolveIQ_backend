import requests
import json

print("=" * 60)
print("Testing Registration API")
print("=" * 60)

# Test Registration
try:
    response = requests.post(
        'http://127.0.0.1:5000/api/auth/register',
        json={
            'name': 'Test User',
            'email': 'test@example.com',
            'password': '123456',
            'department_id': 1
        }
    )
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("Testing Login API")
print("=" * 60)

# Test Login
try:
    response = requests.post(
        'http://127.0.0.1:5000/api/auth/login',
        json={
            'email': 'test@example.com',
            'password': '123456'
        }
    )
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
