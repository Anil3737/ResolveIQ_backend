
import requests
import json

BASE_URL = "http://127.0.0.1:5000/api"

def test_team_members():
    # Login as Team Lead
    login_data = {
        "email": "tl@resolveiq.com", # Update with valid credentials
        "password": "password123"
    }
    
    print("Attempting to login...")
    login_resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if login_resp.status_code != 200:
        print(f"Login failed: {login_resp.text}")
        return

    token = login_resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    print("Fetching team members...")
    resp = requests.get(f"{BASE_URL}/team-lead/team-members", headers=headers)
    
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)}")

if __name__ == "__main__":
    test_team_members()
