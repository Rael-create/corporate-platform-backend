from app.core.database import db
from app.models.staff import Staff
from app.models.users import User
from app.services.ride_counter_service import reset_ride_counter


def update_staff_by_admin(staff_id, data):
    #  Find the staff member
    staff = Staff.query.get(staff_id)
    if not staff:
        raise ValueError("Staff member not found.")

    admin_user = User.query.get(data['updated_by'])
    if not admin_user:
        raise ValueError("Admin user not found.")

    # Ensure the updater is a CORPORATE_ADMIN
    if admin_user.role != "CORPORATE_ADMIN":
        raise PermissionError("User is not a corporate admin.")

    # Ensure both belong to the same corporate
    if staff.corporate_id != admin_user.corporate_id:
        raise PermissionError("Admin does not belong to the same corporate as the staff.")

    #  Update fields if they are provided in the request
    if "rides_allocated" in data:
        staff.rides_allocated = data["rides_allocated"]
        
    if "max_fare_per_ride" in data:
        staff.max_fare_per_ride = float(data["max_fare_per_ride"])
        
    if "status" in data:
        staff.status = data["status"]

    #  Handle Ride Counter Reset (if the flag is explicitly set to True)
    if data.get("reset_rides_counter") is True: 
        staff.rides_used = 0

    if data.get("reset_rides_counter"):
        reset_ride_counter(staff.staff_id)

    # db.session.add()
    db.session.commit()
    return staff