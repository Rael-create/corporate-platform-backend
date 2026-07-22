from app.core.database import db
from datetime import datetime
from app.models.ride_request import RideRequest

PayoutStatus = [
    "PENDING",
    "SUCCESS",
    "FAILED"
]

class GatewayPayout(db.Model):
    __tablename__ = 'gateway_payouts'
    
    payout_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('ride_requests.ride_id'), nullable=False)
    target_identifier = db.Column(db.String(100), nullable=False)
    amount_sent = db.Column(db.Float, nullable=False)
    status = db.Column(db.Enum(*PayoutStatus), default="PENDING", nullable=False)
    gateway_reference = db.Column(db.String(100), nullable=True)
    failure_reason = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationship back to RideRequest
    #ride = db.relationship("RideRequest", backref="gateway_payouts", lazy=True)

    def __repr__(self):
        return f"<GatewayPayout {self.payout_id} - {self.status}>"