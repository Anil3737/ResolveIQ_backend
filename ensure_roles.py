from app import create_app
from app.extensions import db
from app.models import Role

def ensure_roles():
    app = create_app()
    with app.app_context():
        mandatory_roles = ["ADMIN", "TEAM_LEAD", "AGENT", "EMPLOYEE"]
        print("\n" + "="*40)
        print("🛠️  ENSURING MANDATORY ROLES")
        print("="*40)
        
        for role_name in mandatory_roles:
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                print(f"➕ Creating role: {role_name}")
                role = Role(name=role_name)
                db.session.add(role)
            else:
                print(f"✅ Role already exists: {role_name} (ID: {role.id})")
        
        try:
            db.session.commit()
            print("\n✨ Database roles synchronized successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error committing roles: {e}")

if __name__ == "__main__":
    ensure_roles()
