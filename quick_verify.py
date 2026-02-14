"""Quick API verification script"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

print("=" * 80)
print("ResolveIQ API - Quick Verification")
print("=" * 80 + "\n")

# Test 1: Health Check
print("1. Health Check...")
try:
    resp = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
    if resp.status_code == 200:
        print(f"   ✓ PASS - {resp.json()}\n")
    else:
        print(f"   ✗ FAIL - Status: {resp.status_code}\n")
except Exception as e:
    print(f"   ✗ FAIL - {str(e)}\n")

# Test 2: Get OpenAPI schema to verify endpoints
print("2. Checking available endpoints...")
try:
    resp = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
    if resp.status_code == 200:
        data = resp.json()
        paths = sorted(data['paths'].keys())
        
        # Group by category
        auth_endpoints = [p for p in paths if '/auth/' in p]
        admin_endpoints = [p for p in paths if '/admin/' in p]
        ticket_endpoints = [p for p in paths if '/tickets' in p]
        ai_endpoints = [p for p in paths if '/ai/' in p]
        
        print(f"   ✓ Total endpoints: {len(paths)}")
        print(f"   ✓ Auth endpoints: {len(auth_endpoints)}")
        print(f"   ✓ Admin endpoints: {len(admin_endpoints)}")
        print(f"   ✓ Ticket endpoints: {len(ticket_endpoints)}")
        print(f"   ✓ AI endpoints: {len(ai_endpoints)}")
        
        print("\n   Ticket endpoints:")
        for ep in ticket_endpoints:
            methods = list(data['paths'][ep].keys())
            print(f"     - {ep}: {', '.join([m.upper() for m in methods])}")
        
        print("\n   AI endpoints:")
        for ep in ai_endpoints:
            methods = list(data['paths'][ep].keys())
            print(f"     - {ep}: {', '.join([m.upper() for m in methods])}")
        
        print()
    else:
        print(f"   ✗ FAIL - Status: {resp.status_code}\n")
except Exception as e:
    print(f"   ✗ FAIL - {str(e)}\n")

# Test 3: Login test
print("3. Testing admin login...")
try:
    resp = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": "admin@resolveiq.com", "password": "admin123"},
        timeout=5
    )
    if resp.status_code == 200:
        data = resp.json()
        token = data.get('access_token')
        print(f"   ✓ PASS - User ID: {data.get('user_id')}, Token: {token[:20]}...\n")
        
        # Test 4: Test authenticated endpoint
        print("4. Testing authenticated endpoint (list users)...")
        headers = {"Authorization": f"Bearer {token}"}
        resp2 = requests.get(f"{BASE_URL}/api/v1/admin/users", headers=headers, timeout=5)
        if resp2.status_code == 200:
            users = resp2.json()
            print(f"   ✓ PASS - Found {len(users)} users\n")
        else:
            print(f"   ✗ FAIL - Status: {resp2.status_code}\n")
        
    else:
        print(f"   ✗ FAIL - Status: {resp.status_code}, {resp.text}\n")
except Exception as e:
    print(f"   ✗ FAIL - {str(e)}\n")

print("=" * 80)
print("Verification complete!")
print("=" * 80)
