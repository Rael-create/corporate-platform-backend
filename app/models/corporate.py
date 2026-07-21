from app.core.database import db
from datetime import datetime

WALLET_TYPES = [
    "PLATFORM WALLET",
    "CORPORATE WALLET"
]

class Corporate(db.Model):
    __tablename__ = 'corporates'

    corporate_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    corporate_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    contacts = db.Column(db.String(100), nullable=False)
    wallet_type = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    #One Corporate can have many Users
    users = db.relationship("User", backref="corporate", lazy=True, cascade="all, delete-orphan")

    #Relationship: Allows us to easily find all staff belonging to the corporate entity
    staff_members = db.relationship('Staff', backref='corporate', lazy=True, cascade="all, delete-orphan")
    #ride_requests = db.relationship('RideRequest', backref='corporate', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Corporate {self.corporate_name}>"