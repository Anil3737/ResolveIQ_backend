from app import create_app
from app.extensions import db
from app.models.department import Department

app = create_app()

with app.app_context():
    print("=" * 60)
    print("CREATING DEFAULT DEPARTMENT")
    print("=" * 60)
    
    try:
        # Check if department exists
        dept = Department.query.filter_by(id=1).first()
        
        if dept:
            print(f"✓ Department already exists: ID={dept.id}, Name={dept.name}")
        else:
            # Create default department
            dept = Department(id=1, name="General")
            db.session.add(dept)
            db.session.commit()
            print(f"✓ Created default department: ID={dept.id}, Name={dept.name}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
