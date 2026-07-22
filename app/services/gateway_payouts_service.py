from app.core.database import db
from app.models.gateway_payouts import GatewayPayout
from app.models.ride_request import RideRequest

def create_payout(data):
    # 1. Verify the ride exists
    ride = RideRequest.query.get(data["ride_id"])
    if not ride:
        raise ValueError("Ride not found")

    # 2. Create the payout
    new_payout = GatewayPayout(
        ride_id=ride.ride_id,
        target_identifier=data["target_identifier"],
        amount_sent=float(data["amount_sent"]),
        status=data.get("status", "PENDING"),
        gateway_reference=data.get("gateway_reference"),
        failure_reason=data.get("failure_reason")
    )

    db.session.add(new_payout)
    db.session.commit()
    return new_payout

def get_all_payouts():
    return GatewayPayout.query.order_by(GatewayPayout.created_at.desc()).all()

def get_payout(payout_id):
    payout = GatewayPayout.query.get(payout_id)
    if not payout:
        raise ValueError("Payout not found")
    return payout

def update_payout(payout_id, data):
    payout = GatewayPayout.query.get(payout_id)
    if not payout:
        raise ValueError("Payout not found")
        
    # Update fields only if they are provided in the request
    if "status" in data:
        payout.status = data["status"]
    if "gateway_reference" in data:
        payout.gateway_reference = data["gateway_reference"]
    if "failure_reason" in data:
        payout.failure_reason = data["failure_reason"]
    if "amount_sent" in data:
        payout.amount_sent = float(data["amount_sent"])
        
    db.session.commit()
    return payout

def delete_payout(payout_id):
    payout = GatewayPayout.query.get(payout_id)
    if not payout:
        raise ValueError("Payout not found")

    db.session.delete(payout)
    db.session.commit()
    return True