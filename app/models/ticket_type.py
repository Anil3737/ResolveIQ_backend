from app.extensions import db
from datetime import datetime

class TicketType(db.Model):
    __tablename__ = "ticket_types"

    id = db.Column(db.Integer, primary_key=True, index=True)

    name = db.Column(db.String(100), unique=True, nullable=False)
    severity_level = db.Column(db.Integer, nullable=False, default=1)  
    # 1=Low, 2=Medium, 3=High, 4=Critical

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
