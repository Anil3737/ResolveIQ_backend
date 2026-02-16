from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    print("=" * 60)
    print("Creating all database tables...")
    print("=" * 60)
    
    try:
        # Import all models to ensure they're registered
        from app.models.user import User
        from app.models.department import Department
        
        # Create all tables
        db.create_all()
        
        print("✓ All tables created successfully!")
        print("\nTables created:")
        print("  - users")
        print("  - departments")
        print("  - (and any other models)")
        
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
