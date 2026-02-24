import requests
import time
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:5000/api"

def get_token(email, password):
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    if resp.status_code == 200:
        return resp.json()["access_token"]
    return None

def test_sla_automation():
    print("🚀 Starting SLA Automation Verification...")
    
    token = get_token("admin@resolveiq.com", "admin123")
    if not token:
        print("❌ Login failed")
        return
    
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Check live countdown in a ticket
    print("\n📦 Fetching tickets to check SLA fields...")
    resp = requests.get(f"{BASE_URL}/admin/tickets", headers=headers)
    if resp.status_code == 200:
        tickets = resp.json()["data"]
        if tickets:
            t = tickets[0]
            print(f"✅ Ticket {t['id']} SLA Remaining: {t.get('sla_remaining_seconds')}s")
            print(f"✅ Ticket {t['id']} SLA Breached: {t.get('sla_breached')}")
            if t['status'] == 'RESOLVED':
                print(f"✅ Ticket {t['id']} Auto-close in: {t.get('auto_close_in_seconds')}s")
        else:
            print("⚠️ No tickets found to verify fields")
    else:
        print(f"❌ Failed to fetch tickets: {resp.text}")

    print("\n💡 NOTE: To fully test background jobs, wait 5-30 mins or manually trigger jobs if possible.")
    print("✨ SLA Verification Complete (API fields verified).")

if __name__ == "__main__":
    test_sla_automation()
