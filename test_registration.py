# Test Role-Based Registration
# This script tests the role-based registration implementation

import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_employee_registration():
    print_section("TEST 1: Employee Self-Registration (Public)")
    
    url = f"{BASE_URL}/auth/register"
    payload = {
        "full_name": "Test Employee",
        "email": f"employee_test_{hash('test')}@example.com",
        "phone": "1234567890",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✓ SUCCESS: Employee self-registration works!")
            return response.json().get("user_id")
        else:
            print("✗ FAILED: Employee registration failed")
            return None
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return None

def get_admin_token():
    print_section("Getting Admin Token")
    print("NOTE: This requires an admin user to exist in the database")
    print("If this fails, create an admin user manually:")
    print("INSERT INTO roles (role_name) VALUES ('ADMIN');")
    print("INSERT INTO users (role_id, full_name, email, password_hash, is_active)")
    print("VALUES (1, 'Admin User', 'admin@example.com', <hashed_password>, 1);")
    print()
    
    # Try to login as admin
    # You'll need to replace these with actual admin credentials
    url = f"{BASE_URL}/auth/login"
    payload = {
        "email": "admin@example.com",
        "password": "admin123"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"✓ Admin login successful")
            return token
        else:
            print(f"✗ Admin login failed: {response.json()}")
            return None
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return None

def test_admin_create_team_lead(token):
    print_section("TEST 2: Admin Creates Team Lead")
    
    if not token:
        print("⊗ SKIPPED: No admin token available")
        return
    
    url = f"{BASE_URL}/admin/users"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "full_name": "Test Team Lead",
        "email": f"teamlead_test_{hash('test')}@example.com",
        "phone": "9876543210",
        "password": "leadpass123",
        "role": "TEAM_LEAD"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✓ SUCCESS: Admin can create team lead!")
        else:
            print("✗ FAILED: Could not create team lead")
    except Exception as e:
        print(f"✗ ERROR: {e}")

def test_admin_create_agent(token):
    print_section("TEST 3: Admin Creates Agent")
    
    if not token:
        print("⊗ SKIPPED: No admin token available")
        return
    
    url = f"{BASE_URL}/admin/users"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "full_name": "Test Agent",
        "email": f"agent_test_{hash('test')}@example.com",
        "phone": "5555555555",
        "password": "agentpass123",
        "role": "AGENT"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✓ SUCCESS: Admin can create agent!")
        else:
            print("✗ FAILED: Could not create agent")
    except Exception as e:
        print(f"✗ ERROR: {e}")

def test_invalid_role(token):
    print_section("TEST 4: Admin Tries to Create EMPLOYEE (Should Fail)")
    
    if not token:
        print("⊗ SKIPPED: No admin token available")
        return
    
    url = f"{BASE_URL}/admin/users"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "full_name": "Invalid Employee",
        "email": "invalid@example.com",
        "phone": "1111111111",
        "password": "invalid123",
        "role": "EMPLOYEE"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 422:  # Validation error
            print("✓ SUCCESS: Validation correctly rejects EMPLOYEE role!")
        else:
            print("⊗ UNEXPECTED: Expected 422 validation error")
    except Exception as e:
        print(f"✗ ERROR: {e}")

if __name__ == "__main__":
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     ROLE-BASED REGISTRATION TESTING                      ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    # Test 1: Employee self-registration
    test_employee_registration()
    
    # Get admin token for protected endpoints
    admin_token = get_admin_token()
    
    # Test 2: Admin creates team lead
    test_admin_create_team_lead(admin_token)
    
    # Test 3: Admin creates agent
    test_admin_create_agent(admin_token)
    
    # Test 4: Try to create invalid role
    test_invalid_role(admin_token)
    
    print_section("Testing Complete")
    print("\nNote: Some tests may be skipped if admin credentials are not configured.")
    print("To fully test, ensure an admin user exists in the database.\n")
