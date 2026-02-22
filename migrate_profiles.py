from app import create_app
from app.extensions import db
from app.models.user import User, TeamLeadProfile, AgentProfile, EmployeeProfile
from app.models.role import Role
from sqlalchemy import text, inspect

app = create_app()

def migrate():
    with app.app_context():
        print("🚀 Starting Professional Profile Migration...")
        
        # 1. Create tables if they don't exist
        print("📋 Creating profile tables...")
        db.create_all()
        
        inspector = inspect(db.engine)
        user_columns = [c['name'] for c in inspector.get_columns('users')]
        
        # 2. Add 'updated_at' to users if missing
        if 'updated_at' not in user_columns:
            print("🔧 Adding 'updated_at' column to 'users' table...")
            db.session.execute(text("ALTER TABLE users ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
            db.session.commit()

        # 3. Handle 'phone' uniqueness (EMP ID requirement)
        print("🔧 Ensuring 'phone' column has uniqueness constraint...")
        try:
            db.session.execute(text("ALTER TABLE users ADD UNIQUE (phone)"))
            db.session.commit()
            print("✅ Uniqueness constraint added to 'phone'.")
        except Exception as e:
            print(f"⚠️ Note: Unique constraint on 'phone' might already exist or failed: {e}")

        # 4. Data Migration: users -> profiles
        print("💾 Migrating existing user data to profiles...")
        
        users = User.query.all()
        migrated_count = 0
        
        for user in users:
            role_name = user.role.name if user.role else "EMPLOYEE"
            
            # Use raw SQL to get data from columns that might be removed soon or are not in current model
            try:
                # We need to get department_id and location while they still exist in the DB
                result = db.session.execute(text(f"SELECT department_id, location FROM users WHERE id = {user.id}")).fetchone()
                dept_id = result[0]
                loc = result[1]
                
                if role_name == 'TEAM_LEAD':
                    if not TeamLeadProfile.query.filter_by(user_id=user.id).first():
                        profile = TeamLeadProfile(user_id=user.id, department_id=dept_id or 1, location=loc)
                        db.session.add(profile)
                        migrated_count += 1
                
                elif role_name == 'AGENT':
                    if not AgentProfile.query.filter_by(user_id=user.id).first():
                        profile = AgentProfile(user_id=user.id, department_id=dept_id or 1, location=loc)
                        db.session.add(profile)
                        migrated_count += 1
                
                elif role_name == 'EMPLOYEE':
                    if not EmployeeProfile.query.filter_by(user_id=user.id).first():
                        profile = EmployeeProfile(user_id=user.id, location=loc)
                        db.session.add(profile)
                        migrated_count += 1
                
                elif role_name == 'ADMIN':
                    # Admins don't have separate profiles in this requirement but we could add one if needed
                    pass
                    
            except Exception as e:
                print(f"❌ Error migrating user {user.id}: {e}")

        db.session.commit()
        print(f"✅ Successfully migrated {migrated_count} user profiles.")

        # 5. Cleanup: Drop old columns
        print("🧹 Cleaning up old columns from 'users' table...")
        try:
            if 'department_id' in user_columns:
                print("   - Dropping 'department_id'...")
                # We need to drop the foreign key first if it exists
                try:
                    # Generic drop for MySQL, might need specific name if it fails
                    # Let's try to find the constraint name first
                    constraints = inspector.get_foreign_keys('users')
                    for fk in constraints:
                        if fk['constrained_columns'] == ['department_id']:
                            db.session.execute(text(f"ALTER TABLE users DROP FOREIGN KEY {fk['name']}"))
                except:
                    pass
                db.session.execute(text("ALTER TABLE users DROP COLUMN department_id"))
            
            if 'location' in user_columns:
                print("   - Dropping 'location'...")
                db.session.execute(text("ALTER TABLE users DROP COLUMN location"))
                
            db.session.commit()
            print("✅ Cleanup complete.")
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
            print("⚠️ You may need to manually drop 'department_id' and 'location' if they still exist.")

        print("\n✨ Migration Finished Successfully!")

if __name__ == "__main__":
    migrate()
