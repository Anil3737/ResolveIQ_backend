"""
Comprehensive test script for ResolveIQ API endpoints
Tests all admin, ticket, and AI endpoints with field validation
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"
API_V1 = f"{BASE_URL}/api/v1"

# Global variables for test data
admin_token = None
admin_user_id = None
test_department_id = None
test_team_id = None
test_ticket_type_id = None
test_sla_id = None
test_user_id = None
test_ticket_id = None


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_test(test_name, success, response=None, error=None):
    """Print test result"""
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"{status} | {test_name}")
    if error:
        print(f"       Error: {error}")
    if response and not success:
        print(f"       Response: {response}")
    print()


def test_health_check():
    """Test health check endpoint"""
    print_section("HEALTH CHECK")
    
    try:
        response = requests.get(f"{API_V1}/health")
        success = response.status_code == 200
        data = response.json() if success else None
        print_test("Health check endpoint", success, data)
        return success
    except Exception as e:
        print_test("Health check endpoint", False, error=str(e))
        return False


def test_admin_login():
    """Login as admin and store token"""
    print_section("ADMIN AUTHENTICATION")
    global admin_token, admin_user_id
    
    try:
        # Login with admin credentials
        login_data = {
            "email": "admin@resolveiq.com",
            "password": "admin123"
        }
        response = requests.post(f"{API_V1}/auth/login", json=login_data)
        success = response.status_code == 200
        
        if success:
            data = response.json()
            admin_token = data.get("access_token")
            admin_user_id = data.get("user", {}).get("id")
            print_test(f"Admin login (user_id: {admin_user_id})", True)
        else:
            print_test("Admin login", False, response.text)
        
        return success
    except Exception as e:
        print_test("Admin login", False, error=str(e))
        return False


def get_headers():
    """Get authorization headers"""
    return {"Authorization": f"Bearer {admin_token}"}


def test_admin_create_user():
    """Test creating users with different roles"""
    print_section("ADMIN - USER MANAGEMENT")
    global test_user_id
    
    test_users = [
        {
            "role": "EMPLOYEE",
            "full_name": "Test Employee",
            "email": f"employee_{datetime.now().timestamp()}@test.com",
            "phone": "1234567890",
            "password": "test123",
            "department_id": test_department_id
        },
        {
            "role": "AGENT",
            "full_name": "Test Agent",
            "email": f"agent_{datetime.now().timestamp()}@test.com",
            "phone": "1234567891",
            "password": "test123",
            "team_id": test_team_id
        }
    ]
    
    all_passed = True
    for user_data in test_users:
        try:
            response = requests.post(
                f"{API_V1}/admin/users",
                json=user_data,
                headers=get_headers()
            )
            success = response.status_code == 200
            
            if success:
                data = response.json()
                test_user_id = data.get("user_id")
                print_test(f"Create {user_data['role']} user", True)
            else:
                print_test(f"Create {user_data['role']} user", False, response.text)
                all_passed = False
        except Exception as e:
            print_test(f"Create {user_data['role']} user", False, error=str(e))
            all_passed = False
    
    # Test list users
    try:
        response = requests.get(f"{API_V1}/admin/users", headers=get_headers())
        success = response.status_code == 200
        print_test("List all users", success, response.json() if not success else None)
    except Exception as e:
        print_test("List all users", False, error=str(e))
        all_passed = False
    
    return all_passed


def test_admin_teams():
    """Test team CRUD operations"""
    print_section("ADMIN - TEAM MANAGEMENT")
    global test_team_id
    
    all_passed = True
    
    # Create team
    try:
        team_data = {
            "team_name": f"Test Team {datetime.now().timestamp()}",
            "description": "Test team for automated tests"
        }
        response = requests.post(
            f"{API_V1}/admin/teams",
            json=team_data,
            headers=get_headers()
        )
        success = response.status_code == 200
        
        if success:
            data = response.json()
            test_team_id = data.get("team_id")
            print_test(f"Create team (ID: {test_team_id})", True)
        else:
            print_test("Create team", False, response.text)
            all_passed = False
    except Exception as e:
        print_test("Create team", False, error=str(e))
        all_passed = False
    
    # List teams
    try:
        response = requests.get(f"{API_V1}/admin/teams", headers=get_headers())
        success = response.status_code == 200
        print_test("List teams", success)
        all_passed = all_passed and success
    except Exception as e:
        print_test("List teams", False, error=str(e))
        all_passed = False
    
    # Get specific team
    if test_team_id:
        try:
            response = requests.get(
                f"{API_V1}/admin/teams/{test_team_id}",
                headers=get_headers()
            )
            success = response.status_code == 200
            print_test(f"Get team {test_team_id}", success)
            all_passed = all_passed and success
        except Exception as e:
            print_test(f"Get team {test_team_id}", False, error=str(e))
            all_passed = False
    
    return all_passed


def test_admin_ticket_types():
    """Test ticket type CRUD operations"""
    print_section("ADMIN - TICKET TYPES")
    global test_ticket_type_id
    
    all_passed = True
    
    # Create ticket type
    try:
        ticket_type_data = {
            "type_name": f"Test Type {datetime.now().timestamp()}",
            "severity_level": "HIGH"
        }
        response = requests.post(
            f"{API_V1}/admin/ticket-types",
            json=ticket_type_data,
            headers=get_headers()
        )
        success = response.status_code == 200
        
        if success:
            data = response.json()
            test_ticket_type_id = data.get("type_id")
            print_test(f"Create ticket type (ID: {test_ticket_type_id})", True)
        else:
            print_test("Create ticket type", False, response.text)
            all_passed = False
    except Exception as e:
        print_test("Create ticket type", False, error=str(e))
        all_passed = False
    
    # List ticket types
    try:
        response = requests.get(
            f"{API_V1}/admin/ticket-types",
            headers=get_headers()
        )
        success = response.status_code == 200
        print_test("List ticket types", success)
        all_passed = all_passed and success
    except Exception as e:
        print_test("List ticket types", False, error=str(e))
        all_passed = False
    
    return all_passed


def test_admin_sla_policies():
    """Test SLA policy CRUD operations"""
    print_section("ADMIN - SLA POLICIES")
    global test_sla_id
    
    all_passed = True
    
    if not test_ticket_type_id:
        print_test("SLA policy tests", False, error="No ticket type ID available")
        return False
    
    # Create SLA policy
    try:
        sla_data = {
            "type_id": test_ticket_type_id,
            "response_minutes": 30,
            "resolution_minutes": 240
        }
        response = requests.post(
            f"{API_V1}/admin/sla-policies",
            json=sla_data,
            headers=get_headers()
        )
        success = response.status_code == 200
        
        if success:
            data = response.json()
            test_sla_id = data.get("sla_id")
            print_test(f"Create SLA policy (ID: {test_sla_id})", True)
        else:
            print_test("Create SLA policy", False, response.text)
            all_passed = False
    except Exception as e:
        print_test("Create SLA policy", False, error=str(e))
        all_passed = False
    
    # List SLA policies
    try:
        response = requests.get(
            f"{API_V1}/admin/sla-policies",
            headers=get_headers()
        )
        success = response.status_code == 200
        print_test("List SLA policies", success)
        all_passed = all_passed and success
    except Exception as e:
        print_test("List SLA policies", False, error=str(e))
        all_passed = False
    
    return all_passed


def test_tickets():
    """Test ticket CRUD operations"""
    print_section("TICKETS - CRUD OPERATIONS")
    global test_ticket_id, test_department_id
    
    # Get a department ID first
    if not test_department_id:
        test_department_id = 1  # Default department
    
    all_passed = True
    
    # Create ticket
    try:
        ticket_data = {
            "title": "Test Ticket - Network Issue",
            "description": "The wifi is not working and internet connection is down. This is urgent and blocking work.",
            "department_id": test_department_id,
            "sla_hours": 24
        }
        response = requests.post(
            f"{API_V1}/tickets/",
            json=ticket_data,
            headers=get_headers()
        )
        success = response.status_code == 200
        
        if success:
            data = response.json()
            test_ticket_id = data.get("ticket_id")
            print_test(f"Create ticket (ID: {test_ticket_id})", True)
        else:
            print_test("Create ticket", False, response.text)
            all_passed = False
    except Exception as e:
        print_test("Create ticket", False, error=str(e))
        all_passed = False
    
    # List tickets
    try:
        response = requests.get(f"{API_V1}/tickets/", headers=get_headers())
        success = response.status_code == 200
        if success:
            data = response.json()
            print_test(f"List tickets (found {data.get('total', 0)} tickets)", True)
        else:
            print_test("List tickets", False, response.text)
            all_passed = False
    except Exception as e:
        print_test("List tickets", False, error=str(e))
        all_passed = False
    
    # List tickets with filters
    try:
        response = requests.get(
            f"{API_V1}/tickets/?status=OPEN&search=network",
            headers=get_headers()
        )
        success = response.status_code == 200
        print_test("List tickets with filters", success)
        all_passed = all_passed and success
    except Exception as e:
        print_test("List tickets with filters", False, error=str(e))
        all_passed = False
    
    # Get specific ticket
    if test_ticket_id:
        try:
            response = requests.get(
                f"{API_V1}/tickets/{test_ticket_id}",
                headers=get_headers()
            )
            success = response.status_code == 200
            print_test(f"Get ticket {test_ticket_id}", success)
            all_passed = all_passed and success
        except Exception as e:
            print_test(f"Get ticket {test_ticket_id}", False, error=str(e))
            all_passed = False
        
        # Update ticket
        try:
            update_data = {
                "status": "IN_PROGRESS",
                "priority": "P2"
            }
            response = requests.patch(
                f"{API_V1}/tickets/{test_ticket_id}",
                json=update_data,
                headers=get_headers()
            )
            success = response.status_code == 200
            print_test(f"Update ticket {test_ticket_id}", success)
            all_passed = all_passed and success
        except Exception as e:
            print_test(f"Update ticket {test_ticket_id}", False, error=str(e))
            all_passed = False
    
    return all_passed


def test_ai_features():
    """Test AI analysis endpoints"""
    print_section("AI - TICKET ANALYSIS")
    
    if not test_ticket_id:
        print_test("AI analysis tests", False, error="No ticket ID available")
        return False
    
    all_passed = True
    
    # Run AI analysis
    try:
        response = requests.post(
            f"{API_V1}/ai/analyze/{test_ticket_id}",
            headers=get_headers()
        )
        success = response.status_code == 200
        
        if success:
            data = response.json()
            print_test(
                f"AI analysis complete - Category: {data.get('predicted_category')}, "
                f"Priority: {data.get('priority')}, "
                f"Risk: {data.get('sla_breach_risk')}%",
                True
            )
        else:
            print_test("Run AI analysis", False, response.text)
            all_passed = False
    except Exception as e:
        print_test("Run AI analysis", False, error=str(e))
        all_passed = False
    
    # Get AI analysis
    try:
        response = requests.get(
            f"{API_V1}/ai/analysis/{test_ticket_id}",
            headers=get_headers()
        )
        success = response.status_code == 200
        
        if success:
            data = response.json()
            print_test(
                f"Get existing AI analysis - Urgency: {data.get('urgency_score')}, "
                f"Severity: {data.get('severity_score')}",
                True
            )
        else:
            print_test("Get AI analysis", False, response.text)
            all_passed = False
    except Exception as e:
        print_test("Get AI analysis", False, error=str(e))
        all_passed = False
    
    # Get ticket with AI
    try:
        response = requests.get(
            f"{API_V1}/tickets/{test_ticket_id}/with-ai",
            headers=get_headers()
        )
        success = response.status_code == 200
        print_test("Get ticket with AI insights", success)
        all_passed = all_passed and success
    except Exception as e:
        print_test("Get ticket with AI insights", False, error=str(e))
        all_passed = False
    
    return all_passed


def run_all_tests():
    """Run all test suites"""
    print("\n" + "="*80)
    print("  RESOLVEIQ API - COMPREHENSIVE TEST SUITE")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*80 + "\n")
    
    results = {}
    
    # Run tests in order
    results["Health Check"] = test_health_check()
    results["Admin Login"] = test_admin_login()
    
    if results["Admin Login"]:
        # First ensure we have a department (from seed data)
        global test_department_id
        test_department_id = 1  # Assuming seed data has created this
        
        results["Team Management"] = test_admin_teams()
        results["Ticket Types"] = test_admin_ticket_types()
        results["SLA Policies"] = test_admin_sla_policies()
        results["User Management"] = test_admin_create_user()
        results["Ticket CRUD"] = test_tickets()
        results["AI Features"] = test_ai_features()
    
    # Print summary
    print_section("TEST SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} | {test_name}")
    
    print(f"\n{'='*80}")
    print(f"  TOTAL: {passed_tests}/{total_tests} test suites passed")
    print(f"  SUCCESS RATE: {(passed_tests/total_tests)*100:.1f}%")
    print(f"{'='*80}\n")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
