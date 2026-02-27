import sys
from app import create_app
from app.extensions import db
from app.models.ticket import Ticket
from sqlalchemy import text

# Canonical RANGES from dept_isolation.py
DEPARTMENT_RANGES = {
    1: (0,      99999),   # Network Issue
    2: (100000, 199999),  # Hardware Failure
    3: (200000, 299999),  # Software Installation
    4: (300000, 399999),  # Application Downtime / Application Issues
    5: (400000, 499999),  # Other
}

PREFIX = "IQ-IT-2026-"

def realign_ticket_numbers():
    # Ensure UTF-8 output
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        
    app = create_app()
    with app.app_context():
        print("🚀 Starting Ticket Number Realignment...")
        
        # Disable unique constraint check temporarily if possible, 
        # or just set them to NULL/temp values first to avoid collisions 
        # during the swap.
        print("Step 1: Setting all ticket numbers to NULL to avoid unique constraint collisions...")
        db.session.execute(text("UPDATE tickets SET ticket_number = NULL"))
        db.session.commit()

        # Step 2: Iterate through departments and assign fresh numbers
        for dept_id, (start, end) in DEPARTMENT_RANGES.items():
            print(f"Processing Dept {dept_id}...")
            
            # Fetch all tickets for this department, ordered by ID (to preserve some sense of order)
            tickets = Ticket.query.filter_by(department_id=dept_id).order_by(Ticket.id).all()
            
            current_num = start
            for ticket in tickets:
                new_ticket_no = f"{PREFIX}{current_num:06d}"
                ticket.ticket_number = new_ticket_no
                print(f"  Ticket ID {ticket.id} -> {new_ticket_no}")
                current_num += 1
                
                if current_num > end:
                    print(f"⚠️  WARNING: Range exhausted for Dept {dept_id}!")
                    break
        
        db.session.commit()
        print("✅ Realignment Complete!")

if __name__ == "__main__":
    realign_ticket_numbers()
