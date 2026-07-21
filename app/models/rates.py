from datetime import datetime
from app.core.database import db

RATE_TYPES = [
    "VAT",
    "COMMISSION"
]


class RateType(db.Model):
    __tablename__ = "rate_types"

    rate_type_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    rates = db.relationship("Rate", back_populates="rate_type", lazy=True)

    def __repr__(self):
        return f"<RateType {self.name}>"


class Rate(db.Model):
    __tablename__ = "rates"

    rate_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rate = db.Column(db.Float, nullable=False)
    
    rate_type_id = db.Column(db.Integer, db.ForeignKey("rate_types.rate_type_id"), nullable=False)
    
    created_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    rate_type = db.relationship("RateType", back_populates="rates")
    
    #creator = db.relationship("User", backref="rates")

    def __repr__(self):
        return f"<Rate {self.rate_type.name}: {self.rate}>"