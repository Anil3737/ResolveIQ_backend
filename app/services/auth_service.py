from flask_jwt_extended import create_access_token
from app.models.user import User
from app.extensions import db

class AuthService:
    @staticmethod
    def register_user(data):
        try:
            name = data.get('name')
            email = data.get('email')
            password = data.get('password')
            role = data.get('role', 'EMPLOYEE')
            department_id = data.get('department_id')
            phone = data.get('phone')

            print(f"🔍 Checking if email exists: {email}")
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                print(f"⚠️ Email already exists: {email}")
                return None, "Email already exists"

            print(f"🆕 Creating new user: {name} ({email})")
            user = User(name=name, email=email, role=role, department_id=department_id)
            user.set_password(password)
            # If User model supports phone, set it
            if hasattr(user, 'phone') and phone:
                user.phone = phone

            print(f"💾 Adding user to database session")
            db.session.add(user)

            print(f"💾 Committing to database...")
            db.session.commit()

            print(f"✅ User created successfully with ID: {user.id}")
            return user, "User registered successfully"

        except Exception as e:
            print(f"❌ Database error during registration: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return None, f"Database error: {str(e)}"

    @staticmethod
    def login_user(email, password):
        try:
            print(f"🔍 Looking up user: {email}")
            user = User.query.filter_by(email=email).first()
            
            if not user:
                print(f"❌ User not found: {email}")
                return None, "Invalid email or password"
            
            print(f"🔐 Checking password for: {email}")
            if user.check_password(password):
                print(f"✅ Password correct, generating token")
                access_token = create_access_token(identity={"id": user.id, "role": user.role})
                return {
                    "access_token": access_token,
                    "user": user.to_dict()
                }, None
            else:
                print(f"❌ Invalid password for: {email}")
                return None, "Invalid email or password"
                
        except Exception as e:
            print(f"❌ Error during login: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, f"Login error: {str(e)}"
