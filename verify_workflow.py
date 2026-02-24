import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000/api"

def get_token(email, password):
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    if resp.status_code == 200:
        return resp.json()["access_token"]
    return None

def test_workflow():
    print("🚀 Starting Advanced Workflow Verification...")
    
    # 1. Login as Employee
    emp_token = get_token("employee@resolveiq.com", "employee123")
    if not emp_token:
        print("❌ Employee login failed")
        return

    headers = {"Authorization": f"Bearer {emp_token}"}
    
    # 2. Create high risk ticket (Auto-escalation check)
    print("\n📝 Creating high risk ticket...")
    high_risk_data = {
        "title": "EMERGENCY: SECURITY BREACH DETECTED",
        "description": "Unauthorized access to server room. Security leak confirmed.",
        "department_id": 1
    }
    resp = requests.post(f"{BASE_URL}/tickets", json=high_risk_data, headers=headers)
    if resp.status_code == 201:
        ticket = resp.json()["data"]
        print(f"✅ Ticket Created: {ticket['id']}")
        print(f"   Priority: {ticket['priority']} (Expected: P1)")
        print(f"   Risk: {ticket['breach_risk']}% (Expected: > 70)")
        print(f"   Assigned To: {ticket.get('assigned_to')} (Expected: Team Lead ID)")
        ticket_id = ticket['id']
    else:
        print(f"❌ Ticket creation failed: {resp.text}")
        return

    # 3. Login as Team Lead to see assignment
    print("\n👑 Checking Team Lead visibility...")
    tl_token = get_token("lead@resolveiq.com", "lead123") # Assuming these exist from seed
    if not tl_token:
        print("❌ Team Lead login failed (Ensure lead@resolveiq.com exists with lead123)")
        return
    
    tl_headers = {"Authorization": f"Bearer {tl_token}"}
    resp = requests.get(f"{BASE_URL}/tickets", headers=tl_headers)
    if resp.status_code == 200:
        tickets = resp.json()["data"]
        found = any(t['id'] == ticket_id for t in tickets)
        print(f"✅ Team Lead can see ticket: {'Yes' if found else 'No'}")
    else:
        print(f"❌ TL fetch failed: {resp.text}")

    # 4. Team Lead assigns to Agent
    print("\n👷 Assigning to Agent...")
    # Need an agent ID. In real test we'd fetch one. Assuming 3 for now if possible.
    # Let's find an agent first
    agent_id = None
    resp = requests.get(f"{BASE_URL}/admin/users", headers={"Authorization": f"Bearer {get_token('admin@resolveiq.com', 'admin123')}"})
    if resp.status_code == 200:
        users = resp.json()
        for u in users:
            if u.get('role') == 'AGENT':
                agent_id = u['id']
                break
    
    if not agent_id:
        print("❌ No agent found to test assignment")
    else:
        assign_data = {"ticket_id": ticket_id, "agent_id": agent_id}
        resp = requests.post(f"{BASE_URL}/teamlead/assign-ticket", json=assign_data, headers=tl_headers)
        if resp.status_code == 200:
            print(f"✅ Successfully assigned to Agent {agent_id}")
        else:
            print(f"❌ Assignment failed: {resp.text}")

    print("\n✨ Workflow Verification Complete.")

if __name__ == "__main__":
    test_workflow()
