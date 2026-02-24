import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000/api"

def test_system_activity():
    print("🚀 Starting System Activity Verification Tests...")
    
    # 1. Login as Admin
    print("\n🔑 Logging in as Admin...")
    login_data = {
        "email": "admin@resolveiq.com",
        "password": "admin123"
    }
    login_res = requests.post(f"{BASE_URL}/v1/auth/login", json=login_data)
    if login_res.status_code != 200:
        print(f"❌ Login failed: {login_res.text}")
        return
    
    token = login_res.json()['data']['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Admin Login Successful.")

    # 2. Check System Activity Logs (Initial)
    print("\nlogs: Fetching initial system activity logs...")
    logs_res = requests.get(f"{BASE_URL}/admin/system-activity", headers=headers)
    if logs_res.status_code == 200:
        data = logs_res.json()
        print(f"✅ Fetched {data['total']} logs.")
    else:
        print(f"❌ Failed to fetch logs: {logs_res.text}")

    # 3. Trigger events to log
    print("\n📝 Triggering events to log...")
    
    # Trigger USER_LOGIN (happened above)
    
    # Trigger TICKET_CREATED
    print("🎟️ Creating a test ticket...")
    ticket_data = {
        "title": f"Test Ticket {datetime.now().timestamp()}",
        "description": "Verification of system activity logging",
        "department_id": 1,
        "sla_hours": 24
    }
    # Note: Ticket endpoint is usually /v1/tickets
    ticket_res = requests.post(f"{BASE_URL}/v1/tickets", json=ticket_data, headers=headers)
    if ticket_res.status_code == 201:
        print("✅ Ticket Created.")
    else:
        print(f"❌ Ticket creation failed: {ticket_res.text}")

    # 4. Verify Logs again
    print("\nlogs: Fetching updated system activity logs...")
    logs_res = requests.get(f"{BASE_URL}/admin/system-activity", headers=headers)
    if logs_res.status_code == 200:
        data = logs_res.json()
        print(f"✅ Total logs now: {data['total']}.")
        for log in data['logs'][:5]:
            print(f"   - [{log['created_at']}] {log['user']} ({log['role']}): {log['action_type']} - {log['description']}")
    else:
        print(f"❌ Failed to fetch logs: {logs_res.text}")

if __name__ == "__main__":
    test_system_activity()
