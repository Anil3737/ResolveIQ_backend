import sys
import os

# Add backend to sys.path
backend_path = r"c:\Users\DELL\OneDrive\Desktop\resolveiq_backend"
sys.path.append(backend_path)

from app import create_app
from app.models.ticket import Ticket
from app.extensions import db

def cleanup_tickets():
    app = create_app()
    with app.app_context():
        print("\n--- Starting Department ID Cleanup ---")
        
        # Mapping based on Title Prefixes
        mapping = {
            "[Network Issue]": 1,
            "[Hardware Failure]": 2,
            "[Software Installation]": 3,
            "[Application Downtime / Application Issues]": 4,
            "[Other]": 5
        }
        
        updated_count = 0
        all_tickets = Ticket.query.all()
        
        for ticket in all_tickets:
            original_dept = ticket.department_id
            target_dept = None
            
            for prefix, dept_id in mapping.items():
                if prefix in ticket.title:
                    target_dept = dept_id
                    break
            
            if target_dept and target_dept != original_dept:
                print(f"Updating Ticket {ticket.ticket_number}: {original_dept} -> {target_dept}")
                ticket.department_id = target_dept
                updated_count += 1
        
        if updated_count > 0:
            db.session.commit()
            print(f"\nSuccessfully updated {updated_count} tickets.")
        else:
            print("\nNo tickets required update.")

if __name__ == "__main__":
    cleanup_tickets()
