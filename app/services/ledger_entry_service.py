from app.core.database import db
from app.models.ledger_entry import LedgerEntry
from app.models.wallet import Wallet
from sqlalchemy.exc import IntegrityError
from app.models.corporate import Corporate


def create_ledger_entry(data):
    # Get wallet: either from corporate_id or directly from wallet_id
    if data.get("wallet_id") is not None:
        wallet = Wallet.query.get(data["wallet_id"])
        if not wallet:
            raise ValueError("Wallet not found.")
        corporate_id = wallet.corporate_id  # may be None
    else:
        # Must have corporate_id
        if "corporate_id" not in data:
            raise ValueError("Either 'wallet_id' or 'corporate_id' must be provided.")
        corporate = Corporate.query.get(data["corporate_id"])
        if not corporate:
            raise ValueError("Corporate not found.")
        wallet = Wallet.query.filter(Wallet.corporate_id == data["corporate_id"]).first()
        if not wallet:
            raise ValueError("Wallet not found for this corporate.")
        corporate_id = corporate.corporate_id

    # Now wallet and corporate_id are defined
    new_entry = LedgerEntry(
        wallet_id=wallet.wallet_id,
        corporate_id=corporate_id,
        ride_id=data.get("ride_id"),
        transaction_type=data["transaction_type"],
        transaction_class=data["transaction_class"],
        amount=data["amount"] if data["transaction_class"] == "Credit" else -data["amount"],
    )

    # Update balance
    if data["transaction_class"] == "Credit":
        wallet.current_balance += data["amount"]
    else:
        if wallet.current_balance < data["amount"]:
            raise ValueError("Insufficient balance.")
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
