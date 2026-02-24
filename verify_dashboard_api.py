import requests
import json

BASE_URL = "http://127.0.0.1:5000/api"

def login(email, password):
    url = f"{BASE_URL}/auth/login"
    payload = {"email": email, "password": password}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def test_dashboard(token):
    url = f"{BASE_URL}/admin/dashboard"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    print(f"URL: {url}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("✅ Dashboard API Success!")
        print(f"Response: {json.dumps(data, indent=2)}")
    else:
        print(f"❌ Dashboard API Failed: {response.text}")

if __name__ == "__main__":
    # Use admin credentials
    token = login("admin@company.com", "password")
    if token:
        test_dashboard(token)
    else:
        print("❌ Login Failed.")
