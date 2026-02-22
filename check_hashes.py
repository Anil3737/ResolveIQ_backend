from app import create_app
from app.models.user import User
import os

app = create_app()
with app.app_context():
    print("Checking User Hashes:")
    for user in User.query.all():
        prefix = user.password_hash[:20] if user.password_hash else "None"
        print(f"Email: {user.email} | Hash Prefix: {prefix}")
