import sys
from app import create_app
from app.extensions import db
from sqlalchemy import text

def migrate_departments():
    # Ensure UTF-8 output
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        
    app = create_app()
    with app.app_context():
        print("🚀 Starting Department ID Re-indexing...")
        
        # 0. Disable foreign key checks
        db.session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        print("Disabled FOREIGN_KEY_CHECKS.")

        # 1. Re-assign any tickets from "IT Support" (ID 1) to "Other" (ID 6, which will stay ID 5)
        # However, ID 1 is the one we want to DELETE.
        # Let's see if anyone is in ID 1.
        print("Checking for references to ID 1...")
        
        tables_to_scrub = [
            ("tickets", "department_id"),
            ("team_lead_profiles", "department_id"),
            ("agent_profiles", "department_id"),
            ("teams", "department_id")
        ]
        
        for table, col in tables_to_scrub:
            # Re-assign any ID 1 to ID 6 (Other) first, so they don't get lost or cause errors
            db.session.execute(text(f"UPDATE {table} SET {col} = 6 WHERE {col} = 1"))
            print(f"  Scrubbed ID 1 from {table}.{col}")

        # 2. Delete "IT Support" (ID 1)
        print("Deleting IT Support (ID 1)...")
        db.session.execute(text("DELETE FROM departments WHERE id = 1"))
        
        # 3. Re-index IDs 2-6 to 1-5
        # Mapping: old_id -> new_id
        mapping = {
            2: 1, # Network Issue
            3: 2, # Hardware Failure
            4: 3, # Software Installation
            5: 4, # Application Downtime
            6: 5  # Other
        }
        
        for old_id, new_id in mapping.items():
            print(f"Migrating {old_id} -> {new_id}...")
            # Update departments first
            db.session.execute(text("UPDATE departments SET id = :new_id WHERE id = :old_id"), {"new_id": new_id, "old_id": old_id})
            
            # Update all references
            for table, col in tables_to_scrub:
                sql = f"UPDATE {table} SET {col} = :new_id WHERE {col} = :old_id"
                db.session.execute(text(sql), {"new_id": new_id, "old_id": old_id})
        
        # 4. Re-enable foreign key checks
        db.session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        db.session.commit()
        print("✅ Migration Complete!")
        
        # Verify the result
        print("\nNew Department List:")
        rows = db.session.execute(text("SELECT id, name FROM departments ORDER BY id")).fetchall()
        for r in rows:
            print(f"  ID: {r[0]} | Name: {r[1]}")

if __name__ == "__main__":
    migrate_departments()
