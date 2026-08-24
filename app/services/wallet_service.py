from app.core.database import db
from app.models.wallet import Wallet, WALLET_TYPES
from sqlalchemy.exc import IntegrityError
from app.models.ledger_entry import LedgerEntry
from app.schemas.wallet_schema import WalletResponseSchema
from app.schemas.ledger_entry_schema import LedgerEntryResponseSchema

wallet_response_schema = WalletResponseSchema()
legger_response_schema = LedgerEntryResponseSchema()


def top_up_wallet(wallet_id, amount, initial_top_up, type=None):
    wallet = Wallet.query.get(wallet_id)
    if not wallet:
        raise ValueError("Wallet not found")

    if not initial_top_up:
        # 1. Update the wallet balance
        wallet.current_balance += float(amount)

    # 2. Determine the correct transaction type based on wallet type
    if type:
        # OVERWRIDE THE ABOVE if dealing with invoice paymen
        transaction_type = type
    else:
        if wallet.wallet_type == "PLATFORM_FUNDED":
            transaction_type = "PLATFORM_TOPUP"
        elif wallet.wallet_type == "CORPORATE_FUNDED":
            transaction_type = "CORPORATE_TOPUP"
        else:
            transaction_type = "PLATFORM_TOPUP"  # Default for other platform wallets

    # 3. Create a ledger entry (the audit trail)
    ledger_entry = LedgerEntry(
        corporate_id=wallet.corporate_id,
        wallet_id=wallet.wallet_id,
        transaction_type=transaction_type,
        transaction_class="Credit",
        amount=float(amount),
    )

    db.session.add(ledger_entry)
    db.session.commit()

    return wallet, ledger_entry


def create_wallet(data):
    if data["wallet_type"] in ("PLATFORM_FUNDED", "CORPORATE_FUNDED"):
        try:
            initial_balance = float(data.get("current_balance", 0.0))
            # Step 1: Create the wallet with zero balance
            new_wallet = Wallet(
                corporate_id=data.get("corporate_id"),
                wallet_type=data["wallet_type"],
                currency=data.get("currency", "KES"),
                current_balance=initial_balance,  # 10K
                created_by=data["created_by"],
            )
            db.session.add(new_wallet)
            db.session.commit()

            # Step 2: If an initial balance was provided, top up

            if initial_balance > 0:
                _, ledger_entry = top_up_wallet(
                    wallet_id=new_wallet.wallet_id,
                    amount=initial_balance,
                    initial_top_up=True,
                )
                return {
                    "new_wallet": wallet_response_schema.dump(new_wallet),
                    "ledger_entry": legger_response_schema.dump(ledger_entry),
                }

            return {"new_wallet": wallet_response_schema.dump(new_wallet)}

        except IntegrityError:
            db.session.rollback()
            raise ValueError(
                "Failed to create wallet. Check if corporate_id and created_by exist."
            )
    else:
        raise ValueError(f"Unsupported wallet_type: {data['wallet_type']}")


def transfer_from_platform_to_corporate(corporate_wallet_id, amount, admin_user_id):
    # Get the platform wallet (corporate_id IS NULL)
    platform_wallet = Wallet.query.filter_by(
        corporate_id=None, wallet_type="PLATFORM_FUNDED"
    ).first()
    if not platform_wallet:
        raise ValueError("Platform master wallet not found")

    # Get the corporate wallet
    corporate_wallet = Wallet.query.get(corporate_wallet_id)
    if not corporate_wallet:
        raise ValueError("Corporate wallet not found")
    if corporate_wallet.wallet_type != "PLATFORM_FUNDED":
        raise ValueError(
            "Corporate wallet must be PLATFORM_FUNDED to receive platform funds"
        )

    # Check sufficient balance
    if platform_wallet.current_balance < amount:
        raise ValueError("Insufficient platform balance")

    # Perform transfer
    platform_wallet.current_balance -= amount
    corporate_wallet.current_balance += amount

    # Record ledger entries
    # Debit from platform
    ledger_entry_platform = LedgerEntry(
        corporate_id=None,  # Platform has no corporate
        wallet_id=platform_wallet.wallet_id,
        transaction_type="CORPORATE_TOPUP",
        transaction_class="Debit",
        amount=amount,
    )
    # Credit to corporate
    ledger_entry_corporate = LedgerEntry(
        corporate_id=corporate_wallet.corporate_id,
        wallet_id=corporate_wallet.wallet_id,
        transaction_type="CORPORATE_TOPUP",
        transaction_class="Credit",
        amount=amount,
    )

    db.session.add(ledger_entry_platform)
    db.session.add(ledger_entry_corporate)
    db.session.commit()

    return {
        "platform_wallet": platform_wallet,
        "corporate_wallet": corporate_wallet,
        "amount": amount,
    }


def get_all_wallets():
    return Wallet.query.all()


def get_wallet(wallet_id):
    wallet = Wallet.query.get(wallet_id)
    if not wallet:
        raise ValueError("Wallet not found")
    return wallet


# DELETE Wallet Service
def delete_wallet(wallet_id):
    wallet = Wallet.query.get(wallet_id)

    if not wallet:
        raise ValueError("Wallet not found")

    # Check if wallet has any associated ledger entries
    ledger_entries = LedgerEntry.query.filter_by(wallet_id=wallet_id).first()

    if ledger_entries:
        raise ValueError(
            "Cannot delete wallet with existing ledger entries. Please archive instead."
        )

    db.session.delete(wallet)
    db.session.commit()

    return {"message": f"Wallet {wallet_id} deleted successfully"}
