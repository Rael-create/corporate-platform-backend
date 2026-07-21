from app.core.database import db
from app.models.ride_request import RideRequest, RideStatus
from app.models.staff import Staff
from app.models.rates import Rate, RateType


def calculate_actual_fare(base_fare):
    
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
    
    actual_fare = base_fare + vat_amount + commission_amount
    
    return actual_fare,vat_rate,commission_rate,vat_amount,commission_amount


def create_ride(data):
    # 1. Verify staff exists
    staff = Staff.query.get(data["staff_id"])
    if not staff:
        raise ValueError("Staff not found")

    # 2. Calculate actual fare using the helper function
    base_fare = float(data["estimated_fare"])
    actual_fare, vat_rate, commission_rate, vat_amount, commission_amount = calculate_actual_fare(base_fare)
    
    # 3. Create the ride (Status is instantly APPROVED)
    new_ride = RideRequest(
        staff_id=staff.staff_id,
        corporate_id=staff.corporate_id, 
        pickup_location=data["pickup_location"],
        destination=data["destination"],
        estimated_fare=base_fare,
        actual_fare=actual_fare,
        vat_rate=vat_rate,
        commission_rate=commission_rate,
        vat_amount=vat_amount,
        commission_amount=commission_amount,    
        reason=data.get("reason"),
        ride_date=data["ride_date"],
        status=RideStatus.APPROVED
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


def delete_ride(ride_id):
    ride = RideRequest.query.get(ride_id)
    if not ride:
        raise ValueError("Ride not found")

    db.session.delete(ride)
    db.session.commit()
    return True