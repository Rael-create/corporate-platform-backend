from app.core.database import db
from app.models.wallet import Wallet, WALLET_TYPES
from sqlalchemy.exc import IntegrityError

def create_wallet(data):


    
    new_wallet = Wallet(
        corporate_id=data.get('corporate_id'), #none for PLATFORM_ALLOCATED
        wallet_type=data['wallet_type'],
        currency=data.get('currency', 'KES'),
        current_balance=0.0,
        created_by=data['created_by']
        
    )
    
    try:
        db.session.add(new_wallet)
        db.session.commit()
        return new_wallet
    except IntegrityError:
        db.session.rollback()
        raise ValueError("Failed to create wallet. Check if corporate_id and created_by exist.")

def get_all_wallets():
    return Wallet.query.all()

def get_wallet(wallet_id):
    wallet = Wallet.query.get(wallet_id)
    if not wallet:
        raise ValueError("Wallet not found")
    return wallet