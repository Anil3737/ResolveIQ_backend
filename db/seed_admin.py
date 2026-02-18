# seed_admin.py - Set the admin user's password hash properly.
# Run AFTER executing resolveiq_full_recovery.sql in phpMyAdmin.
# Usage: python db/seed_admin.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.user import User

app = create_app()

with app.app_context():
    user = User.query.get(1)
    if user:
        user.set_password("admin123")
        db.session.commit()
        print("✅ Admin password updated successfully!")
        print(f"   Email   : {user.email}")
        print(f"   Password: admin123")
    else:
        print("❌ No user with id=1 found. Run the SQL script first.")
