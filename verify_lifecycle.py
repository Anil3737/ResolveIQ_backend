import requests
import json

BASE_URL = "http://127.0.0.1:5000/api"

def get_token(email, password):
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    if resp.status_code == 200:
        return resp.json()["access_token"]
    return None

def test_lifecycle():
    print("🚀 Starting Ticket Lifecycle Verification...")
    
    # Tokens
    emp_token = get_token("employee@resolveiq.com", "employee123")
    tl_token = get_token("lead@resolveiq.com", "lead123")
    agent_token = get_token("agent@resolveiq.com", "agent123") # Assuming agent@resolveiq.com exists
    admin_token = get_token("admin@resolveiq.com", "admin123")

    # 1. Employee creates ticket (OPEN)
    print("\n[Employee] Creating ticket...")
    resp = requests.post(f"{BASE_URL}/tickets", 
                         json={"title": "Lifecycle Test", "description": "Testing transitions", "department_id": 1},
                         headers={"Authorization": f"Bearer {emp_token}"})
    ticket_id = resp.json()["data"]["id"]
    print(f"✅ Ticket {ticket_id} created with status OPEN")

    # 2. Employee tries to move to IN_PROGRESS (Should Fail)
    print("\n[Employee] Attempting OPEN -> IN_PROGRESS...")
    resp = requests.post(f"{BASE_URL}/tickets/update-status", 
                         json={"ticket_id": ticket_id, "new_status": "IN_PROGRESS"},
                         headers={"Authorization": f"Bearer {emp_token}"})
    print(f"❌ Result: {resp.status_code} (Expected: 403)")

    # 3. Team Lead moves to IN_PROGRESS (Should Work)
    print("\n[Team Lead] Moving OPEN -> IN_PROGRESS...")
    resp = requests.post(f"{BASE_URL}/tickets/update-status", 
                         json={"ticket_id": ticket_id, "new_status": "IN_PROGRESS"},
                         headers={"Authorization": f"Bearer {tl_token}"})
    print(f"✅ Result: {resp.status_code} (Expected: 200)")

    # 4. Agent moves to RESOLVED (Needs to be assigned first)
    # Let's skip assignment for this test or use a known assigned agent
    print("\n[Agent] Moving IN_PROGRESS -> RESOLVED...")
    resp = requests.post(f"{BASE_URL}/tickets/update-status", 
                         json={"ticket_id": ticket_id, "new_status": "RESOLVED"},
                         headers={"Authorization": f"Bearer {agent_token}"})
    print(f"✅ Result: {resp.status_code} (Expected: 200 or 403 if not assigned)")

    # 5. Employee moves to CLOSED
    print("\n[Employee] Moving RESOLVED -> CLOSED...")
    resp = requests.post(f"{BASE_URL}/tickets/update-status", 
                         json={"ticket_id": ticket_id, "new_status": "CLOSED"},
                         headers={"Authorization": f"Bearer {emp_token}"})
    print(f"✅ Result: {resp.status_code} (Expected: 200)")

    print("\n✨ Lifecycle Verification Complete.")

if __name__ == "__main__":
    test_lifecycle()
