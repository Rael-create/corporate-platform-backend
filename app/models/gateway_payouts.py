from app.core.database import db
from datetime import datetime

PayoutStatus = [
    "PENDING",
    "SUCCESS",
    "FAILED"
]

PaymentMethod = [
    "SEND_MONEY",
    "POCHI_LA_BIASHARA",
    "BUY_GOODS",
    "PAYBILL"
]

class GatewayPayout(db.Model):
    __tablename__ = 'gateway_payouts'
    
    payout_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('ride_requests.ride_id'), nullable=False)
    target_identifier = db.Column(db.String(100), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    amount_sent = db.Column(db.Float, nullable=False)
    status = db.Column(db.Enum(*PayoutStatus), default="PENDING", nullable=False)
    gateway_reference = db.Column(db.String(100), nullable=True)
    failure_reason = db.Column(db.String(255), nullable=True)

    
    created_at = db.Column(db.DateTime, default=datetime.now)


    def __repr__(self):
        return f"<GatewayPayout {self.payout_id} - {self.status}>"