from app.models.corporate import Corporate
from app.core.database import db
from app.services.wallet_service import create_wallet
from app.models.wallet import Wallet
from app.models.ledger_entry import LedgerEntry
from app.models.staff import Staff
from app.models.users import User
from app.models.ride_request import RideRequest


def create_corporate(data, created_by):
    new_corporate = Corporate(
        corporate_name=data["corporate_name"],
        location=data["location"],
        address=data.get("address"),
        contacts=data.get("contacts"),
        wallet_type=data.get("wallet_type"),
    )

    try:
        db.session.add(new_corporate)
        db.session.flush()  # ✅ Flush to get the ID

        # Auto-create wallet for the corporate using existing wallet service
        wallet_data = {
            "corporate_id": new_corporate.corporate_id,
            "wallet_type": data.get("wallet_type", "CORPORATE_FUNDED"),
            "currency": "KES",
            "current_balance": 0.0,
            "created_by": created_by,
        }

        create_wallet(wallet_data)
        db.session.commit()
        print(f"✅ Corporate {new_corporate.corporate_id} created with wallet")
        return new_corporate
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating corporate: {e}")
        raise e


def get_all_corporates():
    """Get all corporates."""
    return Corporate.query.all()


def get_corporate(corporate_id):
    """Get a single corporate by ID."""
    corporate = Corporate.query.get(corporate_id)
    if not corporate:
        raise ValueError("Corporate not found")
    return corporate


def delete_corporate(corporate_id):
    corporate = Corporate.query.get(corporate_id)

    if not corporate:
        raise ValueError("Corporate not found")

    # Delete associated ride requests
    RideRequest.query.filter_by(corporate_id=corporate_id).delete()

    # Delete associated wallets
    wallets = Wallet.query.filter_by(corporate_id=corporate_id).all()
    for wallet in wallets:

        # Delete ledger entries for this wallet
        LedgerEntry.query.filter_by(wallet_id=wallet.wallet_id).delete()
        db.session.delete(wallet)

    # Delete associated staff/user
    staff_members = Staff.query.filter_by(corporate_id=corporate_id).all()
    for staff in staff_members:
        if staff.user_id:
            user = User.query.get(staff.user_id)
            if user:
                db.session.delete(user)
        db.session.delete(staff)

    db.session.delete(corporate)
    db.session.commit()
    print(f"✅ Corporate {corporate_id} deleted successfully")

    return {
        "message": f"Corporate {corporate_id} and all associated data deleted successfully"
    }


# update corporate details
def update_corporate(corporate_id, data):
    """Update a corporate."""
    corporate = Corporate.query.get(corporate_id)

    if not corporate:
        raise ValueError("Corporate not found")

    # Update all fields
    if "corporate_name" in data:
        corporate.corporate_name = data["corporate_name"]

    if "location" in data:
        corporate.location = data["location"]

    if "address" in data:
        corporate.address = data["address"]

    if "contacts" in data:
        corporate.contacts = data["contacts"]

    if "wallet_type" in data:
        corporate.wallet_type = data["wallet_type"]

    # ✅ FIX: Add status update
    if "status" in data:
        print(f"📊 Updating status from {corporate.status} to {data['status']}")
        corporate.status = data["status"]

    db.session.commit()
    print(
        f"✅ Corporate {corporate_id} updated successfully. New status: {corporate.status}"
    )
    return corporate
