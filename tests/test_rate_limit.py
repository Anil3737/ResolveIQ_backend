import requests
import time

def test_rate_limit():
    url = "http://127.0.0.1:5000/api/auth/login"
    payload = {
        "email": "test@example.com",
        "password": "wrongpassword"
    }
    
    print(f"Testing rate limit on {url}...")
    for i in range(1, 15):
        try:
            response = requests.post(url, json=payload)
            print(f"Request {i}: Status {response.status_code}")
            if response.status_code == 429:
                print("✅ Success: Rate limit triggered!")
                return
        except requests.exceptions.ConnectionError:
            print("❌ Error: Could not connect to the server. Is it running?")
            return

    print("❌ Failure: Rate limit not triggered after 14 requests.")

if __name__ == "__main__":
    test_rate_limit()
