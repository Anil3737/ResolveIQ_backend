from flask_jwt_extended import create_access_token
from app.models.user import User, TeamLeadProfile, AgentProfile, EmployeeProfile
from app.models.role import Role
from app.extensions import db
from app.utils.logging_utils import log_activity

class AuthService:
    @staticmethod
    def register_user(data, creator_id=None):
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
            
            print(f"AuthService: Registering {full_name} with role {role_name}")
            
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
                print(f"Role '{role_name}' not found in database.")
                return None, f"Role {role_name} not found"

            # 3. Create User record (Core Identity)
            user = User(
                full_name=full_name,
                email=email,
                phone=phone,
                role_id=role.id,
                is_active=True,
                require_password_change=data.get('require_password_change', False) if role_name != 'EMPLOYEE' else False
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.flush() # Get user.id for profile
            print(f"User ID {user.id} created. Proceeding to profile...")

            # 4. Create Role-Specific Profile
            if role_name == 'TEAM_LEAD':
                if not department_id:
                    print("Missing department_id for Team Lead")
                    db.session.rollback()
                    return None, "Department is required for Team Lead"
                
                profile = TeamLeadProfile(
                    user_id=user.id,
                    department_id=department_id,
                    location=location
                )
                db.session.add(profile)
                print(f"TeamLeadProfile staged for user {user.id}")
            
            elif role_name == 'AGENT':
                if not department_id:
                    print("Missing department_id for Agent")
                    db.session.rollback()
                    return None, "Department is required for Agent"
                
                profile = AgentProfile(
                    user_id=user.id,
                    department_id=department_id,
                    team_lead_id=team_lead_id,
                    location=location
                )
                db.session.add(profile)
                print(f"AgentProfile staged for user {user.id}")
            
            elif role_name == 'EMPLOYEE':
                profile = EmployeeProfile(
                    user_id=user.id,
                    location=location
                )
                db.session.add(profile)
                print(f"EmployeeProfile staged for user {user.id}")
            
            # 4.5 Log Activity
            log_activity(
                user_id=creator_id or user.id,
                action_type="USER_CREATED",
                entity_type="USER",
                entity_id=user.id,
                description=f"{role_name} account created for {user.full_name}"
            )

            # 5. Commit Transaction
            db.session.commit()
            print(f"Successfully committed User and Profile for {email}")
            return user, "User and profile registered successfully"

        except Exception as e:
            db.session.rollback()
            print(f"Error during registration: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, f"Registration failure: {str(e)}"

    @staticmethod
    def login_user(email, password):
        try:
            user = User.query.filter_by(email=email).first()
            if not user:
                return None, "Incorrect email"
            if not user.check_password(password):
                return None, "Incorrect password"
            
            # Log the login activity
            log_activity(
                user_id=user.id,
                action_type="USER_LOGIN",
                entity_type="USER",
                entity_id=user.id,
                description=f"User {user.full_name} logged in"
            )
            db.session.commit()

            # Generate JWT Token
            access_token = create_access_token(identity=str(user.id))

            return {
                "access_token": access_token,
                "user": user.to_dict()
            }, None
                
        except Exception as e:
            print(f"Error during login: {str(e)}")
            return None, f"Login error: {str(e)}"

    @staticmethod
    def change_password(user_id, new_password):
        """
        Updates the password for a given user ID.
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"
            
            user.set_password(new_password)
            user.require_password_change = False
            user.updated_at = db.func.now()
            
            log_activity(
                user_id=user_id,
                action_type="PASSWORD_CHANGED",
                entity_type="USER",
                entity_id=user_id,
                description=f"User {user.full_name} changed their password"
            )
            
            db.session.commit()
            return True, "Password updated successfully"
            
        except Exception as e:
            db.session.rollback()
            print(f"Error during password change: {str(e)}")
            return False, str(e)

    @staticmethod
    def update_profile(user_id, data):
        """
        Updates basic profile information for a user.
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"
            
            full_name = data.get('full_name')
            phone = data.get('phone')
            
            if full_name:
                user.full_name = full_name
            if phone:
                # Check if phone is already taken by another user
                existing = User.query.filter(User.phone == phone, User.id != user_id).first()
                if existing:
                    return False, f"Phone/EMP ID {phone} is already in use"
                user.phone = phone
                
            user.updated_at = db.func.now()
            
            log_activity(
                user_id=user_id,
                action_type="PROFILE_UPDATED",
                entity_type="USER",
                entity_id=user_id,
                description=f"User {user.full_name} updated their profile info"
            )
            
            db.session.commit()
            return True, "Profile updated successfully"
            
        except Exception as e:
            db.session.rollback()
            print(f"Error during profile update: {str(e)}")
            return False, str(e)
