
from app.core.database import db
from datetime import datetime


TRANSACTION_CLASSES = [
    "Debit",
    "Credit"
]

TRANSACTION_TYPES = [
    "TRIP_DEDUCTION",
    "TOPUP",
    "INVOICE_PAYMENT",
    "TRIP_REVERSAL",
    "COMMISSION_CHARGE"
]

    
class LedgerEntry(db.Model):
    __tablename__ = "ledger_entries"
    
    entry_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallet.wallet_id'), nullable=False)
    ride_id = db.Column(db.Integer, db.ForeignKey('ride_requests.ride_id'), nullable=True)
    transaction_type = db.Column(db.Enum(*TRANSACTION_TYPES), nullable=False)
    transaction_class = db.Column(db.Enum(*TRANSACTION_CLASSES), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)


    def __repr__(self):
        return f"<LedgerEntry {self.transaction_type.value} - {self.amount}>"
