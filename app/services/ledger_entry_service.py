from app.core.database import db
from app.models.ledger_entry import LedgerEntry
from app.models.wallet import Wallet
from sqlalchemy.exc import IntegrityError

def create_ledger_entry(data):
    wallet = Wallet.query.get(data['wallet_id'])
    if not wallet:
        raise ValueError("Wallet not found.")
    
    new_entry = LedgerEntry(
        wallet_id=data['wallet_id'],
        ride_id=data.get('ride_id'),
        transaction_type=data['transaction_type'],
        transaction_class=data['transaction_class'],
        amount=data['amount']
    )
    
    if data['transaction_class'] == 'Credit':
        wallet.current_balance += data['amount']
    elif data['transaction_class'] == 'Debit':
        wallet.current_balance -= data['amount']
        
    try:
        db.session.add(new_entry)
        db.session.commit()
        return new_entry
    except IntegrityError:
        db.session.rollback()
        raise  ValueError("Failed to create ledger entry.")
    
def get_all_ledger_entries():
    return LedgerEntry.query.order_by(LedgerEntry.created_at.desc()).all()

def get_ledger_by_wallet(wallet_id):
    return LedgerEntry.query.filter_by(wallet_id=wallet_id).order_by(LedgerEntry.created_at.desc()).all()
