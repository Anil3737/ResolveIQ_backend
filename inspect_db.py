from app import create_app
from app.extensions import db
from app.models.user import User
from sqlalchemy import inspect

app = create_app()

with app.app_context():
    print("=" * 60)
    print("DATABASE INSPECTION")
    print("=" * 60)
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Check if tables exist
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"\nTables in database: {tables}")
    
    if 'users' in tables:
        print("\n✓ 'users' table exists")
        
        # Check columns
        columns = inspector.get_columns('users')
        print("\nColumns in 'users' table:")
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")
        
        # Count users
        user_count = User.query.count()
        print(f"\nTotal users in database: {user_count}")
        
        # List all users
        if user_count > 0:
            print("\nExisting users:")
            users = User.query.all()
            for user in users:
                print(f"  - ID: {user.id}, Name: {user.name}, Email: {user.email}, Role: {user.role}")
    else:
        print("\n✗ 'users' table does NOT exist!")
        print("You need to run migrations or create_tables.py")
