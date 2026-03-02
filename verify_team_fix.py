
import requests
import json

BASE_URL = "http://127.0.0.1:5000/api"

def test_team_update():
    # 1. Login as Admin
    print("Logging in as Admin...")
    login_data = {
        "email": "admin@resolveiq.com",
        "password": "Password@123"
    }
    resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
    
    token = resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get existing teams to find ID 16 or any other
    print("Fetching teams...")
    resp = requests.get(f"{BASE_URL}/admin/teams", headers=headers)
    teams = resp.json().get("data", [])
    if not teams:
        print("No teams found")
        return
    
    team_to_update = None
    for t in teams:
        if t['id'] == 16:
            team_to_update = t
            break
    
    if not team_to_update:
        team_to_update = teams[0]
    
    team_id = team_to_update['id']
    print(f"Updating team ID: {team_id} ({team_to_update['name']})...")

    # 3. Update the team
    # Need to get department_id and team_lead_id
    # For testing, we'll try to keep them same or pick from available ones
    
    update_data = {
        "name": team_to_update['name'] + " Updated",
        "description": "Updated via script",
        "department_id": 2, # Common dept ID
        "team_lead_id": 2,  # Common TL ID
        "agent_ids": [3, 4] # Common agent IDs
    }

    resp = requests.put(f"{BASE_URL}/admin/teams/{team_id}", json=update_data, headers=headers)
    print(f"Update Status: {resp.status_code}")
    print(f"Update Response: {json.dumps(resp.json(), indent=2)}")

    if resp.status_code == 200:
        print("Verification Successful: Team updated without 404!")
    else:
        print(f"Verification Failed: Received {resp.status_code}")

if __name__ == "__main__":
    test_team_update()
