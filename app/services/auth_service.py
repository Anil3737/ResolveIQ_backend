from flask_jwt_extended import create_access_token
from app.models.user import User, TeamLeadProfile, AgentProfile, EmployeeProfile
from app.models.role import Role
from app.extensions import db

class AuthService:
    @staticmethod
    def register_user(data):
        """
        Unified registration logic that handles User profile creation.
        Uses transactions to ensure both User and Profile are created successfully.
        """
        try:
            full_name = data.get('full_name') or data.get('name')
            email = data.get('email', '').replace(" ", "").lower().strip()
            password = data.get('password')
            phone = data.get('phone') 
            
            # Normalize role name: "Team Lead" -> "TEAM_LEAD"
            role_input = data.get('role', 'EMPLOYEE')
            role_name = role_input.strip().upper().replace(" ", "_")
            
            print(f"🛠️ AuthService: Registering {full_name} with role {role_name}")
            
            # Additional profile fields
            department_id = data.get('department_id')
            location = data.get('location')
            team_lead_id = data.get('team_lead_id')

            # 1. Check if user exists
            if User.query.filter_by(email=email).first():
                return None, f"Email {email} already exists"
            
            if phone and User.query.filter_by(phone=phone).first():
                return None, f"EMP ID/Phone {phone} already exists"

            # 2. Get Role
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                print(f"❌ Role '{role_name}' not found in database.")
                return None, f"Role {role_name} not found"

            # 3. Create User record (Core Identity)
            user = User(
                full_name=full_name,
                email=email,
                phone=phone,
                role_id=role.id,
                is_active=True
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.flush() # Get user.id for profile
            print(f"✅ User ID {user.id} created. Proceeding to profile...")

            # 4. Create Role-Specific Profile
            if role_name == 'TEAM_LEAD':
                if not department_id:
                    print("❌ Missing department_id for Team Lead")
                    db.session.rollback()
                    return None, "Department is required for Team Lead"
                
                profile = TeamLeadProfile(
                    user_id=user.id,
                    department_id=department_id,
                    location=location
                )
                db.session.add(profile)
                print(f"✅ TeamLeadProfile staged for user {user.id}")
            
            elif role_name == 'AGENT':
                if not department_id:
                    print("❌ Missing department_id for Agent")
                    db.session.rollback()
                    return None, "Department is required for Agent"
                
                profile = AgentProfile(
                    user_id=user.id,
                    department_id=department_id,
                    team_lead_id=team_lead_id,
                    location=location
                )
                db.session.add(profile)
                print(f"✅ AgentProfile staged for user {user.id}")
            
            elif role_name == 'EMPLOYEE':
                profile = EmployeeProfile(
                    user_id=user.id,
                    location=location
                )
                db.session.add(profile)
                print(f"✅ EmployeeProfile staged for user {user.id}")
            
            # 5. Commit Transaction
            db.session.commit()
            print(f"🎉 Successfully committed User and Profile for {email}")
            return user, "User and profile registered successfully"

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error during registration: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, f"Registration failure: {str(e)}"

    @staticmethod
    def login_user(email, password):
        try:
            user = User.query.filter_by(email=email).first()
            if not user or not user.check_password(password):
                return None, "Invalid email or password"
            
            # Return identity as string ID for JWT
            access_token = create_access_token(identity=str(user.id))
            return {
                "access_token": access_token,
                "user": user.to_dict()
            }, None
                
        except Exception as e:
            print(f"❌ Error during login: {str(e)}")
            return None, f"Login error: {str(e)}"
