from sqlalchemy import func
from app.core.database import db
from app.models.finance import PlatformRevenue, Invoice
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


def create_ride_only(data):
    """Create ride + payout, but no gateway, revenue, or counters."""
    staff = Staff.query.get(data["staff_id"])
    if not staff:
        raise ValueError("Staff not found")

    base_fare = float(data["base_fare"])
    auth_ride = TripAuthorizationEngine(staff, base_fare, db_session=db, data=data)
    _, auth_message, new_ride, new_payout = auth_ride.authorize_and_create_ride()

    if not new_ride:
        raise ValueError(auth_message)

    return new_ride, new_payout


# Break this here


def process_ride_after_authorization(
    staff, new_ride, new_payout, auth_message, auth_ride
):
    # payment gateway
    gate_way_resp, _, _ = dispatch_to_gateway(
        ride=new_ride, payout=new_payout, db=db, simulate_failure=False
    )

    # create arecord in revenue table if successfull ride from croporate walet
    if gate_way_resp:
        # Update ride status to COMPLETED
        new_ride.status = "COMPLETED"

        #  Record the Commission your platform earned
        if new_ride.commission_amount > 0:
            wallet = Wallet.query.filter_by(corporate_id=new_ride.corporate_id).first()
            commission_revenue = PlatformRevenue(
                corporate_id=staff.corporate_id,
                staff_id=staff.staff_id,
                ride_id=new_ride.ride_id,
                amount=new_ride.commission_amount,
                revenue_type="COMMISSION",
                status=(
                    "PENDING"
                    if wallet.wallet_type == "PLATFORM_FUNDED"
                    else "CONFIRMED"
                ),
            )
            db.session.add(commission_revenue)

        #  Record the VAT your platform collected
        if new_ride.vat_amount > 0:
            vat_revenue = PlatformRevenue(
                corporate_id=staff.corporate_id,
                staff_id=staff.staff_id,
                ride_id=new_ride.ride_id,
                amount=new_ride.vat_amount,
                revenue_type="VAT",
                status=(
                    "PENDING"
                    if wallet.wallet_type == "PLATFORM_FUNDED"
                    else "CONFIRMED"
                ),
            )
            db.session.add(vat_revenue)


        # Update rides used
        auth_ride.update_rides_used()

        # update rides used
        update_ride_counter(staff.staff_id, new_ride.total_fare)

        db.session.commit()

        return {
            "message": auth_message,
            "new_ride": ride_req_resp.dump(new_ride),
            "gateway_payout": payoutschema.dump(new_payout),
            "staff_details": {
                "rides_used": staff.rides_used,
                "rides_allocated": staff.rides_allocated,
            },
            # "ledger_entry": ledger_entry_resp.dump(ledger_entry),
        }
    else:
        # return the deducted wallet amoun
        # reverse ledger
        create_ledger_entry(
            data={
                "corporate_id": staff.corporate_id,
                "ride_id": new_ride.ride_id,
                "transaction_type": "TRIP_REVERSAL",
                "transaction_class": "Credit",
                "amount": new_ride.total_fare,
            }
        )
        db.session.commit()
        return {
            "message": auth_message,
            "new_ride": ride_req_resp.dump(new_ride),
            "gateway_payout": payoutschema.dump(new_payout),
            "staff_details": {
                "rides_used": staff.rides_used,
                "rides_allocated": staff.rides_allocated,
            },
            # "ledger_entry": ledger_entry_resp.dump(ledger_entry),
        }


def get_all_rides():
    return RideRequest.query.order_by(RideRequest.created_at.desc()).all()


def get_ride(ride_id):
    ride = RideRequest.query.get(ride_id)
    if not ride:
        raise ValueError("Ride not found")
    return ride


def delete_ride(ride_id):
    ride = RideRequest.query.get(ride_id)
    if not ride:
        raise ValueError("Ride not found")

    db.session.delete(ride)
    db.session.commit()
    return True
