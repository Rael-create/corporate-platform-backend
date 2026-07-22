from app.core.database import db
from datetime import datetime
import enum


WALLET_TYPES = [
    "CORPORATE_FUNDED",    # Company deposits their own money *CORPORATE PREPAID*
    "PLATFORM_WALLET",  # Platform gives them credit *MASTER WALLET*,,PLATFORM MASTER
    "PLATFORM_REVENUE"     # System wallet for platform earnings
]

class Wallet(db.Model):
    __tablename__ = 'wallet'
    
    wallet_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    corporate_id = db.Column(db.Integer, db.ForeignKey('corporates.corporate_id'), nullable=True)
    
    wallet_type = db.Column(db.Enum(*WALLET_TYPES), nullable=False, default="PLATFORM_WALLET")
    currency = db.Column(db.String(3), default='KES', nullable=False)
    
    current_balance = db.Column(db.Float, default=0.0, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    
    def __repr__(self):
        return f"<Wallet {self.wallet_id} - {self.wallet_type.value}>"
    