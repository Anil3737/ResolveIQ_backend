"""Direct API test"""
import requests

try:
    # Test health endpoint
    resp = requests.get("http://127.0.0.1:8000/api/v1/health", timeout=3)
    print(f"Health check: {resp.status_code} - {resp.json()}")
    
    # Get OpenAPI schema
    resp = requests.get("http://127.0.0.1:8000/openapi.json", timeout=3)
    data = resp.json()
    
    # Count endpoints
    ticket_eps = [p for p in data['paths'] if '/tickets' in p]
    ai_eps = [p for p in data['paths'] if '/ai/' in p]
    
    print(f"\nTicket endpoints ({len(ticket_eps)}):")
    for ep in ticket_eps:
        print(f"  {ep}")
    
    print(f"\nAI endpoints ({len(ai_eps)}):")
    for ep in ai_eps:
        print(f"  {ep}")
    
except Exception as e:
    print(f"Error: {e}")
