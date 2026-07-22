from sqlalchemy import func

from app.core.database import db
from app.models.ride_request import RideRequest, RideStatus
from app.models.staff import Staff
from app.models.rates import Rate, RateType


def calculate_total_fare(base_fare):
    
    # write check to make sure commision and rates are available
    vat_type = RateType.query.filter_by(name='VAT').first()
    
    vat_rate = float(
                Rate.query
                .filter_by(rate_type_id=vat_type.rate_type_id)
                .order_by(Rate.created_at.desc())
                .first().rate
                )
    
    comm_type = RateType.query.filter_by(name='COMMISSION').first()
    
    commission_rate = float(
                Rate.query
                .filter_by(rate_type_id=comm_type.rate_type_id)
                .order_by(Rate.created_at.desc())
                .first().rate
                )

    
    vat_amount = base_fare * vat_rate
    commission_amount = base_fare * commission_rate
    
    total_fare = base_fare + vat_amount + commission_amount
    matatu_payout = base_fare
    
    return total_fare,vat_rate,commission_rate,vat_amount,commission_amount, matatu_payout


def create_ride(data):
    # 1. Verify staff exists
    staff = Staff.query.get(data["staff_id"])
    if not staff:
        raise ValueError("Staff not found")

    # 2. Calculate total fare using the helper function
    base_fare = float(data["base_fare"])
        # Check ride count limit
    if staff.max_rides is not None:
        current_rides = RideRequest.query.filter_by(staff_id=staff.staff_id).count()
        if current_rides >= staff.max_rides:
            raise ValueError(f"Staff has reached maximum ride limit of {staff.max_rides}")

    # Check amount limit
    if staff.max_amount is not None:
        total_spent = db.session.query(func.sum(RideRequest.base_fare))\
            .filter_by(staff_id=staff.staff_id).scalar() or 0.0
        if total_spent + base_fare > staff.max_amount:
            raise ValueError(f"Staff has exceeded maximum amount limit of {staff.max_amount}")

    
    total_fare, vat_rate, commission_rate, vat_amount, commission_amount, matatu_payout = calculate_total_fare(base_fare)
    
    # 3. Create the ride (Status is instantly APPROVED)
    new_ride = RideRequest(
        staff_id=staff.staff_id,
        corporate_id=staff.corporate_id, 
        pickup_location=data["pickup_location"],
        destination=data["destination"],
        matatu_identifier=data.get("matatu_identifier"),
        base_fare=base_fare,
        total_fare=total_fare,
        vat_rate=vat_rate,
        commission_rate=commission_rate,
        vat_amount=vat_amount,
        commission_amount=commission_amount,  
        matatu_payout=matatu_payout,  
        reason=data.get("reason"),
        status="PENDING"
    )
    
    #Implement payment triggers and notifications here in the future

    db.session.add(new_ride)
    db.session.commit()
    return new_ride


def get_all_rides():
    return RideRequest.query.order_by(RideRequest.created_at.desc()).all()


def get_ride(ride_id):
    ride = RideRequest.query.get(ride_id)
    if not ride:
        raise ValueError("Ride not found")
    return ride

def update_ride(ride_id, data):
    ride = RideRequest.query.get(ride_id)
    if not ride:
        raise ValueError("Ride not found")
        
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
    if "payment_status" in data:
        ride.payment_status = data["payment_status"]
        
    # If the base fare changes, recalculate all financial breakdowns
    if "base_fare" in data:
        base_fare = float(data["base_fare"])
        total_fare, vat_rate, commission_rate, vat_amount, commission_amount, matatu_payout = calculate_total_fare(base_fare)
        
        ride.base_fare = base_fare
        ride.total_fare = total_fare
        ride.vat_rate = vat_rate
        ride.commission_rate = commission_rate
        ride.vat_amount = vat_amount
        ride.commission_amount = commission_amount
        ride.matatu_payout = matatu_payout
        
    db.session.commit()
    return ride


def delete_ride(ride_id):
    ride = RideRequest.query.get(ride_id)
    if not ride:
        raise ValueError("Ride not found")

    db.session.delete(ride)
    db.session.commit()
    return True