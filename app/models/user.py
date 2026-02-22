from app.extensions import db
from datetime import datetime
from app.utils.password_utils import hash_password, verify_password

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # phone is used as EMP ID according to requirements
    phone = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False, default=4) # 4 = EMPLOYEE
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    role = db.relationship('Role', backref=db.backref('users', lazy=True))

    def set_password(self, password):
        self.password_hash = hash_password(password)

    def check_password(self, password):
        is_valid = verify_password(password, self.password_hash)
        
        # If valid and still using legacy hash, upgrade it to bcrypt
        if is_valid and self.password_hash.startswith("pbkdf2:sha256:"):
            from app.utils.password_utils import hash_password
            self.password_hash = hash_password(password)
            db.session.commit()
            print(f"✅ Upgraded hash to bcrypt for: {self.email}")
            
        return is_valid

    def to_dict(self):
        data = {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role.name if self.role else "EMPLOYEE",
            "role_id": self.role_id
        }
        
        # Dynamically include profile data based on role
        if self.role_id == 2: # TEAM_LEAD
            if self.team_lead_profile:
                data["department_id"] = self.team_lead_profile.department_id
                data["department_name"] = self.team_lead_profile.department.name if self.team_lead_profile.department else None
                data["location"] = self.team_lead_profile.location
        
        elif self.role_id == 3: # AGENT
            if self.agent_profile:
                data["department_id"] = self.agent_profile.department_id
                data["department_name"] = self.agent_profile.department.name if self.agent_profile.department else None
                data["location"] = self.agent_profile.location
                if self.agent_profile.team_lead:
                    data["team_lead_id"] = self.agent_profile.team_lead_id
                    data["team_lead_name"] = self.agent_profile.team_lead.full_name
        
        elif self.role_id == 4: # EMPLOYEE
            if self.employee_profile:
                data["location"] = self.employee_profile.location
                
        return data

class TeamLeadProfile(db.Model):
    __tablename__ = 'team_lead_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    location = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('team_lead_profile', uselist=False))
    department = db.relationship('Department', backref=db.backref('team_lead_profiles', lazy=True))

class AgentProfile(db.Model):
    __tablename__ = 'agent_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    team_lead_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # References users.id (must be a TEAM_LEAD)
    location = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('agent_profile', uselist=False))
    team_lead = db.relationship('User', foreign_keys=[team_lead_id])
    department = db.relationship('Department', backref=db.backref('agent_profiles', lazy=True))

class EmployeeProfile(db.Model):
    __tablename__ = 'employee_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    location = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('employee_profile', uselist=False))
