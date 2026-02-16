from app.extensions import db

class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # ADMIN, TEAM_LEAD, AGENT, EMPLOYEE

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name
        }
