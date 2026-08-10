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

    db.session.commit()
    return staff

def get_all_staff():
    return Staff.query.all()

def get_staff_by_id(staff_id):
    staff = Staff.query.get(staff_id)
    if not staff:
        raise ValueError("Staff member not found")
    return staff

def get_staff_by_corporate(corporate_id):
    """Get all staff members for a corporate"""
    return Staff.query.filter_by(corporate_id=corporate_id).all()

def delete_staff(staff_id):

    staff = Staff.query.get(staff_id)
    if not staff:
        raise ValueError("Staff member not found")
    
    # Get the associated user
    user = User.query.get(staff.user_id)
    
    # Delete staff record
    db.session.delete(staff)
    
    # Delete user record if it exists
    if user:
        db.session.delete(user)
    
    db.session.commit()
    return {"message": "Staff member deleted successfully", "staff_id": staff_id}


def create_staff_from_user(user_id, staff_data):
    """
    Create a staff profile from an existing user.
    """
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found")
    
    # Check if staff already exists
    existing_staff = Staff.query.filter_by(user_id=user_id).first()
    if existing_staff:
        raise ValueError("Staff profile already exists for this user")
    
    # Check email uniqueness
    existing_staff_email = Staff.query.filter_by(email=staff_data.get('email')).first()
    if existing_staff_email:
        raise ValueError("Email already exists")
    
    # Create staff profile
    new_staff = Staff(
        first_name=staff_data['first_name'],
        last_name=staff_data['last_name'],
        staff_number=staff_data['staff_number'],
        national_id=staff_data['national_id'],
        email=staff_data['email'],
        location=staff_data['location'],
        address=staff_data['address'],
        phone_number=staff_data['phone_number'],
        rides_allocated=staff_data.get('rides_allocated'),
        rides_used=0,
        max_fare_per_ride=staff_data.get('max_fare_per_ride'),
        status=staff_data.get('status', 'ACTIVE'),
        user_id=user_id,
        corporate_id=user.corporate_id,
    )
    
    db.session.add(new_staff)
    db.session.commit()
    
    return new_staff
