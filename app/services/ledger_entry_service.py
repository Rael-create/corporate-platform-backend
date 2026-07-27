from app.core.database import db
from app.models.ledger_entry import LedgerEntry
from app.models.wallet import Wallet
from sqlalchemy.exc import IntegrityError
from app.models.corporate import Corporate

def create_ledger_entry(data):
    # get walet type from corporates table linked by corporate id
    corporate = Corporate.query.get(data["corporate_id"])
    if not corporate:
        raise ValueError("Corporate not found in the database!")

    wallet_type = corporate.wallet_type

    if wallet_type in ["PLATFORM_FUNDED","PLATFORM_REVENUE"]:
        # wallet = Wallet.query.get(data["wallet_id"])
        wallet = Wallet.query.filter(
            Wallet.wallet_type == wallet_type
            ).first()
    else:
        wallet = Wallet.query.filter(
            Wallet.corporate_id == data["corporate_id"]
        ).first()
    

    new_entry = LedgerEntry(
        wallet_id=wallet.wallet_id,
        corporate_id = corporate.corporate_id,
        ride_id=data.get("ride_id"),
        transaction_type=data["transaction_type"],
        transaction_class=data["transaction_class"],
        amount= data["amount"] if data["transaction_class"] == "Credit" else data["amount"] * -1.0
        ,
    )

    if data["transaction_class"] == "Credit":
        wallet.current_balance += data["amount"]
    elif data["transaction_class"] == "Debit":
        wallet.current_balance -= data["amount"] 

    try:
        db.session.add(new_entry)
        db.session.commit()
        return new_entry
    except IntegrityError:
        db.session.rollback()
        raise ValueError("Failed to create ledger entry.")


def get_all_ledger_entries():
    return LedgerEntry.query.order_by(LedgerEntry.created_at.desc()).all()


def get_ledger_by_wallet(wallet_id):
    return (
        LedgerEntry.query.filter_by(wallet_id=wallet_id)
        .order_by(LedgerEntry.created_at.desc())
        .all()
    )
