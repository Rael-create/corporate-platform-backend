from app.core.database import db
import datetime


TransactionStatus = [
    "PENDING",
    "COMPLETED",
    "FAILED"
]

class MpesaTransaction(db.Model):
    __tablename__ = "mpesa_transactions"

    id = db.Column(db.Integer, primary_key=True, index=True)
    checkout_request_id = db.Column(db.String(50), unique=True, index=True)
    merchant_request_id = db.Column(db.String(50))
    phone_number = db.Column(db.String(15))
    amount = db.Column(db.Float)
    status = db.Column(db.String(20), default="PENDING")  # pending, completed, failed
    result_code = db.Column(db.Integer, nullable=True)
    result_desc = db.Column(db.String(255), nullable=True)
    receipt_number = db.Column(db.String(50), nullable=True)
    transaction_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow
    )
