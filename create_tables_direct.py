# create_tables_direct.py - Create all tables using SQLAlchemy directly

from app.database import engine, Base
from app.models import *  # Import all models

print("\n🔨 Creating all database tables...")
print("Importing models...")

# Create all tables
Base.metadata.create_all(bind=engine)

print("✅ All tables created successfully!")
print("\nVerifying tables...")

from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()

print(f"\nCreated {len(tables)} tables:")
for table in sorted(tables):
    print(f"  - {table}")

print("\n✅ Database schema is ready!")
print("Now run: python direct_seed.py")
