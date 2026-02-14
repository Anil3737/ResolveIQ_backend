# test_rbac.py - Comprehensive Role-Based Access Control Tests

import requests
from typing import Dict, Optional

# Configuration
BASE_URL = "http://localhost:8000"

# Test credentials (will be created in seed script)
USERS = {
    "admin": {"email": "admin@resolveiq.com", "password": "Admin@123"},
    "team_lead": {"email": "teamlead@resolveiq.com", "password": "TeamLead@123"},
    "agent": {"email": "agent@resolveiq.com", "password": "Agent@123"},
    "employee": {"email": "employee@resolveiq.com", "password": "Employee@123"},
}


class RBACTester:
    def __init__(self):
        self.tokens: Dict[str, str] = {}
        self.test_results = []
    
    def login(self, role: str) -> Optional[str]:
        """Login and get JWT token for a role"""
        try:
            response = requests.post(
                f"{BASE_URL}/auth/login",
                json=USERS[role]
            )
            if response.status_code == 200:
                token = response.json().get("access_token")
                self.tokens[role] = token
                return token
            else:
                print(f"❌ Failed to login as {role}: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error login as {role}: {e}")
            return None
    
    def make_request(self, method: str, endpoint: str, role: str, data: dict = None):
        """Make an authenticated request"""
        headers = {"Authorization": f"Bearer {self.tokens.get(role)}"}
        url = f"{BASE_URL}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data or {})
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                response = requests.patch(url, headers=headers, json=data or {})
            
            return response
        except Exception as e:
            print(f"Request error: {e}")
            return None
    
    def test(self, description: str, role: str, method: str, endpoint: str, 
             should_succeed: bool, data: dict = None):
        """Run a single RBAC test"""
        symbol = "✅" if should_succeed else "❌"
        
        response = self.make_request(method, endpoint, role, data)
        
        if response is None:
            print(f"{symbol} {description} - Connection Error")
            self.test_results.append(False)
            return
        
        success = response.status_code in [200, 201]
        forbidden = response.status_code == 403
        
        if should_succeed:
            if success:
                print(f"✅ PASS: {description} (200/201)")
                self.test_results.append(True)
            else:
                print(f"❌ FAIL: {description} (Expected 200/201, got {response.status_code})")
                print(f"   Response: {response.text[:200]}")
                self.test_results.append(False)
        else:
            if forbidden:
                print(f"✅ PASS: {description} (403 Forbidden)")
                self.test_results.append(True)
            elif not success:
                print(f"✅ PASS: {description} ({response.status_code})")
                self.test_results.append(True)
            else:
                print(f"❌ FAIL: {description} (Expected 403, got {response.status_code})")
                self.test_results.append(False)
    
    def run_all_tests(self):
        """Run comprehensive RBAC test suite"""
        print("\n" + "="*80)
        print("🔐 RBAC TEST SUITE - ResolveIQ")
        print("="*80)
        
        # Login all users
        print("\n📝 Logging in all test users...")
        for role in USERS.keys():
            token = self.login(role)
            if token:
                print(f"  ✅ Logged in as {role}")
            else:
                print(f"  ❌ Failed to login as {role}")
                return
        
        print("\n" + "-"*80)
        print("TEST 1: EMPLOYEE ROLE ACCESS CONTROL")
        print("-"*80)
        self.test("Employee CAN view tickets", "employee", "GET", "/tickets", True)
        self.test("Employee CANNOT access /admin/users", "employee", "GET", "/admin/users", False)
        self.test("Employee CANNOT create users", "employee", "POST", "/admin/users", False, {
            "full_name": "Test User",
            "email": "test@test.com",
            "role": "AGENT",
            "password": "Test@123"
        })
        self.test("Employee CANNOT access /admin/teams", "employee", "GET", "/admin/teams", False)
        self.test("Employee CANNOT access /admin/ticket-types", "employee", "GET", "/admin/ticket-types", False)
        self.test("Employee CANNOT access /admin/sla-policies", "employee", "GET", "/admin/sla-policies", False)
        
        print("\n" + "-"*80)
        print("TEST 2: AGENT ROLE ACCESS CONTROL")
        print("-"*80)
        self.test("Agent CAN view tickets", "agent", "GET", "/tickets", True)
        self.test("Agent CANNOT create users", "agent", "POST", "/admin/users", False, {
            "full_name": "Test User", 
            "email": "test2@test.com",
            "role": "AGENT",
            "password": "Test@123"
        })
        self.test("Agent CANNOT delete teams", "agent", "DELETE", "/admin/teams/1", False)
        self.test("Agent CANNOT access /admin/users", "agent", "GET", "/admin/users", False)
        
        print("\n" + "-"*80)
        print("TEST 3: TEAM LEAD ROLE ACCESS CONTROL")
        print("-"*80)
        self.test("TeamLead CAN view tickets", "team_lead", "GET", "/tickets", True)
        self.test("TeamLead CANNOT create users", "team_lead", "POST", "/admin/users", False, {
            "full_name": "Test User",
            "email": "test3@test.com",
            "role": "AGENT",
            "password": "Test@123"
        })
        self.test("TeamLead CANNOT delete departments", "team_lead", "DELETE", "/admin/departments/1", False)
        self.test("TeamLead CANNOT access /admin/teams", "team_lead", "GET", "/admin/teams", False)
        
        print("\n" + "-"*80)
        print("TEST 4: ADMIN ROLE ACCESS CONTROL")
        print("-"*80)
        self.test("Admin CAN access /admin/users", "admin", "GET", "/admin/users", True)
        self.test("Admin CAN access /admin/teams", "admin", "GET", "/admin/teams", True)
        self.test("Admin CAN access /admin/ticket-types", "admin", "GET", "/admin/ticket-types", True)
        self.test("Admin CAN access /admin/sla-policies", "admin", "GET", "/admin/sla-policies", True)
        self.test("Admin CAN create users", "admin", "POST", "/admin/users", True, {
            "full_name": "RBAC Test User",
            "email": "rbactest@resolveiq.com",
            "phone": "1234567890",
            "role": "EMPLOYEE",
            "password": "Test@123",
            "department_id": 1
        })
        
        # Summary
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        total = len(self.test_results)
        passed = sum(self.test_results)
        failed = total - passed
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! RBAC is configured correctly.")
        else:
            print(f"\n⚠️  {failed} tests failed. Please review the RBAC configuration.")
        
        print("="*80)
        return failed == 0


if __name__ == "__main__":
    print("\n🚀 Starting RBAC tests...")
    print("⚠️  Make sure the backend server is running: uvicorn app.main:app --reload")
    print("⚠️  Make sure the database is seeded: python seed_database.py\n")
    
    tester = RBACTester()
    success = tester.run_all_tests()
    
    exit(0 if success else 1)
