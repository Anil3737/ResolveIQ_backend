import requests
import json
import sys

def test_registration():
    print("=" * 60)
    print("TEST 1: Registration API")
    print("=" * 60)
    
    try:
        response = requests.post(
            'http://127.0.0.1:5000/api/auth/register',
            json={
                'name': 'John Doe',
                'email': 'john.doe@example.com',
                'password': 'password123',
                'department_id': 1
            },
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response:")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 201
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_login():
    print("\n" + "=" * 60)
    print("TEST 2: Login API")
    print("=" * 60)
    
    try:
        response = requests.post(
            'http://127.0.0.1:5000/api/auth/login',
            json={
                'email': 'john.doe@example.com',
                'password': 'password123'
            },
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response:")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    reg_success = test_registration()
    login_success = test_login()
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Registration: {'✓ PASSED' if reg_success else '✗ FAILED'}")
    print(f"Login:        {'✓ PASSED' if login_success else '✗ FAILED'}")
    
    sys.exit(0 if (reg_success and login_success) else 1)
