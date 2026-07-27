from app.core.database import db 
from app.models.ride_counter import RideCounter

def update_ride_counter(staff_id, amount):
    """
    Increase ride count and cumulative amount after a successful ride.
    """
    # Ensure amount is a clean float to prevent database type errors
    safe_amount = float(amount) if amount else 0.0

    #  Find existing counter
    counter = RideCounter.query.filter_by(staff_id=staff_id).first()
    
    if counter is None:
        # Create new counter if it doesn't exist
        counter = RideCounter(
            staff_id=staff_id,
            cumulative_no_of_rides=1,
            cumulative_amount=safe_amount
        )
        db.session.add(counter)
    else:
        # Update existing counter
        counter.cumulative_no_of_rides += 1
        counter.cumulative_amount += safe_amount


    db.session.commit()

    return counter

def reset_ride_counter(staff_id):
    """
    Reset a staff member's ride statistics.
    """

    counter = RideCounter.query.filter_by(
        staff_id=staff_id
    ).first()

    if not counter:
        raise ValueError("Ride counter not found.")

    counter.cumulative_no_of_rides = 0
    counter.cumulative_amount = 0

    db.session.commit()

    return counter

def get_ride_counter(staff_id):

    counter = RideCounter.query.filter_by(
        staff_id=staff_id
    ).first()

    if not counter:
        raise ValueError("Ride counter not found.")

    return counter