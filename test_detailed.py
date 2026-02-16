import requests
import json

print("=" * 60)
print("DETAILED REGISTRATION TEST")
print("=" * 60)

try:
    url = 'http://127.0.0.1:5000/api/auth/register'
    data = {
        'name': 'Jane Smith',
        'email': 'jane.smith@example.com',
        'password': 'password123',
        'department_id': 1
    }
    
    print(f"\nURL: {url}")
    print(f"Request Data: {json.dumps(data, indent=2)}")
    
    response = requests.post(url, json=data, timeout=10)
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"\nResponse Body:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
        
except requests.exceptions.ConnectionError as e:
    print(f"\n✗ CONNECTION ERROR: Cannot connect to backend server")
    print(f"   Make sure Flask server is running on port 5000")
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
