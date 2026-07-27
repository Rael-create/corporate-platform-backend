from sqlalchemy import func
from app.core.database import db
from app.models.ride_request import RideRequest, RideStatus
from app.models.staff import Staff
from app.models.rates import Rate, RateType
from app.models.wallet import Wallet
from app.models.ledger_entry import LedgerEntry
from app.schemas.gateway_payouts_schema import GatewayPayoutResponseSchema
from app.services.dispatch_to_gateway import dispatch_to_gateway
from app.services.ledger_entry_service import create_ledger_entry
from app.services.auth_service import TripAuthorizationEngine
from app.services.ride_counter_service import update_ride_counter
from app.schemas.ledger_entry_schema import LedgerEntryResponseSchema
from app.schemas.ride_request_schema import RideRequestResponseSchema

# from app.schemas.users_schema import NewUserSchema

# instatiate schemas
ledger_entry_resp = LedgerEntryResponseSchema()
ride_req_resp = RideRequestResponseSchema()
payoutschema = GatewayPayoutResponseSchema()


def create_ride(data):
    # 1. Verify staff exists
    staff = Staff.query.get(data["staff_id"])
    base_fare = float(data["base_fare"])

    if not staff:
        raise ValueError("Staff not found")

    auth_ride = TripAuthorizationEngine(staff, base_fare, db_session=db, data=data)
    _, auth_message, new_ride, new_payout = auth_ride.authorize_and_create_ride()
    # add to rides_used counter

    if not new_ride:
        db.session.rollback()
        raise ValueError(auth_message)

    # payment gateway
    dispatch_to_gateway(ride=new_ride, payout=new_payout, db=db,simulate_failure=False)

    auth_ride.update_rides_used()

    # push info to ledger
    ledger_entry = create_ledger_entry(
        data={
            "corporate_id": staff.corporate_id,
            "ride_id": new_ride.ride_id,
            "transaction_type": "TRIP_DEDUCTION",
            "transaction_class": "Debit",
            "amount": new_ride.total_fare,
        }
    )
    # update rides used
    update_ride_counter(staff.staff_id, new_ride.total_fare)

    return {
        "message": auth_message,
        "new_ride": ride_req_resp.dump(new_ride),
        "gateway_payout": payoutschema.dump(new_payout),
        "staff_details": {
            "rides_used": staff.rides_used,
            "rides_allocated": staff.rides_allocated,
        },
        "ledger_entry": ledger_entry_resp.dump(ledger_entry),
    }


def get_all_rides():
    return RideRequest.query.order_by(RideRequest.created_at.desc()).all()


def get_ride(ride_id):
    ride = RideRequest.query.get(ride_id)
    if not ride:
        raise ValueError("Ride not found")
    return ride


def settle_ride(ride_id):
    ride = RideRequest.query.get(ride_id)
    if not ride:
        raise ValueError("Ride not found")
    if ride.status != "COMPLETED":
        raise ValueError("Ride must be marked as COMPLETED before settlement.")

    # 1. Find the Corporate's Wallet (Accepts either CORPORATE_FUNDED or PLATFORM_FUNDED)
    corp_wallet = Wallet.query.filter(
        Wallet.corporate_id == ride.corporate_id,
        Wallet.wallet_type.in_(["CORPORATE_FUNDED", "PLATFORM_FUNDED"]),
    ).first()

    if not corp_wallet:
        raise ValueError(
            f"Corporate wallet not found for corporate_id {ride.corporate_id}."
        )
    if corp_wallet.current_balance < ride.total_fare:
        raise ValueError(
            f"Insufficient funds. Required: {ride.total_fare}, Available: {corp_wallet.current_balance}"
        )

    # 2. Find the Platform's Wallet (For receiving commission/VAT)
    plat_wallet = Wallet.query.filter_by(wallet_type="PLATFORM_FUNDED").first()
    if not plat_wallet:
        raise ValueError("Platform wallet not configured.")

    # 3. Update Wallet Balances
    corp_wallet.current_balance -= ride.total_fare
    plat_wallet.current_balance += ride.commission_amount + ride.vat_amount

    # 4. Create Ledger Entries

    # Entry 1: TRIP_DEDUCTION (money leaving corporate wallet)
    db.session.add(
        LedgerEntry(
            corporate_id=ride.corporate_id,
            wallet_id=corp_wallet.wallet_id,
            ride_id=ride.ride_id,
            transaction_type="TRIP_DEDUCTION",
            transaction_class="Debit",
            amount=ride.total_fare,
        )
    )

    # Entry 2: COMMISSION_CHARGE (platform earning commission + VAT)
    db.session.add(
        LedgerEntry(
            corporate_id=ride.corporate_id,
            wallet_id=plat_wallet.wallet_id,
            ride_id=ride.ride_id,
            transaction_type="COMMISSION_CHARGE",
            transaction_class="Credit",
            amount=(ride.commission_amount + ride.vat_amount),
        )
    )

    db.session.commit()
    return {"message": "Ride settled successfully", "total_deducted": ride.total_fare}


def update_ride(ride_id, data):
    ride = RideRequest.query.get(ride_id)
    if not ride:
        raise ValueError("Ride not found")

    # Track if status is changing to COMPLETED
    old_status = ride.status

    # Update basic fields if they are provided in the request
    if "pickup_location" in data:
        ride.pickup_location = data["pickup_location"]
    if "destination" in data:
        ride.destination = data["destination"]
    if "matatu_identifier" in data:
        ride.matatu_identifier = data["matatu_identifier"]
    if "reason" in data:
        ride.reason = data["reason"]
    if "status" in data:
        ride.status = data["status"]

    # If the base fare changes, recalculate all financial breakdowns
    if "base_fare" in data:
        base_fare = float(data["base_fare"])
        (
            total_fare,
            vat_rate,
            commission_rate,
            vat_amount,
            commission_amount,
            matatu_payout,
        ) = calculate_total_fare(base_fare)

        ride.base_fare = base_fare
        ride.total_fare = total_fare
        ride.vat_rate = vat_rate
        ride.commission_rate = commission_rate
        ride.vat_amount = vat_amount
        ride.commission_amount = commission_amount
        ride.matatu_payout = matatu_payout

    db.session.commit()

    # TRIGGER SETTLEMENT IF STATUS CHANGED TO COMPLETED
    if old_status != "COMPLETED" and data.get("status") == "COMPLETED":
        settlement_result = settle_ride(ride_id)
        return ride, settlement_result

    return ride, None


def delete_ride(ride_id):
    ride = RideRequest.query.get(ride_id)
    if not ride:
        raise ValueError("Ride not found")

    db.session.delete(ride)
    db.session.commit()
    return True
