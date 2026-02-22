import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_login():
    url = f"{BASE_URL}/api/auth/login"
    payload = {
        "email": "admin@resolveiq.com",
        "password": "Admin@123"
    }
    
    print(f"Testing Login at {url}")
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        
        data_resp = response.json()
        print("Response JSON:")
        print(json.dumps(data_resp, indent=4))
        
        if response.status_code == 200:
            if "data" in data_resp:
                nested_data = data_resp["data"]
                if "access_token" in nested_data and "user" in nested_data:
                    print("[SUCCESS] 'access_token' and 'user' found in data")
                    user = nested_data["user"]
                    print(f"User: {user.get('full_name')} ({user.get('role')})")
                    print(f"Phone: {user.get('phone')}")
                    print(f"Location: {user.get('location')}")
                    
                    # Check for all required fields in User model
                    required_user_fields = ["id", "full_name", "email", "role", "phone", "location"]
                    missing = [f for f in required_user_fields if f not in user]
                    if not missing:
                        print("[SUCCESS] All expected user fields present")
                    else:
                        print(f"[FAILURE] Missing user fields: {missing}")
                else:
                    print("[FAILURE] 'access_token' or 'user' missing from data field")
            else:
                print("[FAILURE] 'data' wrapper missing from response")
        else:
            print(f"[FAILURE] Server returned {response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    test_login()
