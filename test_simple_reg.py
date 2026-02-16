import requests
import json

print("TESTING REGISTRATION WITH NULL DEPARTMENT")
print("=" * 60)

try:
    response = requests.post(
        'http://127.0.0.1:5000/api/auth/register',
        json={
            'name': 'Alice Johnson',
            'email': 'alice@example.com',
            'password': 'test123'
            # No department_id - should default to None
        },
        timeout=10
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message')}")
    if result.get('data'):
        print(f"User Data: {json.dumps(result['data'], indent=2)}")
        
except Exception as e:
    print(f"Error: {e}")
