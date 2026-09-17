import traceback
from sqlalchemy.exc import IntegrityError

from app.core.database import db
from app.models.staff import Staff
from app.models.users import User
from app.schemas.users_schema import NewUserSchema, UserSchema
from app.models.ride_counter import RideCounter

ALLOWED_ROLES = [
    "SUPER_ADMIN",
    "CORPORATE_ADMIN",
    "STAFF"
]

PROFILED_ROLES = [
    "SUPER_ADMIN",
    "CORPORATE_ADMIN",
    "STAFF"
]

staff_schema = NewUserSchema()
user_schema = UserSchema()

def create_user(data):
    
    # Check username uniqueness
    existing_user = User.query.filter_by(
        username=data['username']).first()
    
    if existing_user:
        raise ValueError("Username already exists."
    )
    
    #Validate role
    if data["role"] not in ALLOWED_ROLES:
        raise ValueError(f"Role must be one of {ALLOWED_ROLES}.")

    try:
        # Create new user
        # if currently logged in user is supe admin ,proceed default
        new_user = User(
            username=data['username'],
            role=data['role'],
            corporate_id=data.get('corporate_id')
        )
        # Hash the password before saving
        new_user.set_password(data['password'])
        db.session.add(new_user)
        db.session.flush()      # Flush the session to get the user_id without committing yet

        # ✅ Initialize so the return statement can't blow up
        new_staff = None


        if new_user.role in PROFILED_ROLES:
            # check email uniqueness
            existing_staff = Staff.query.filter_by(
                email=data.get('email')
            ).first()
            if existing_staff:
                raise ValueError("Email already exists.")

            # check phone uniqueness (needed since OTP login uses phone)
            existing_phone = Staff.query.filter_by(
                phone_number=data.get('phone_number')
            ).first()
            if existing_phone:
                raise ValueError("Phone number already exists.")

                
            # AFTER creating user ,we need to create a staff profile for the user if the role is STAFF or CORPORATE_ADMIN
            new_staff = Staff(
                first_name=data['first_name'],
                last_name=data['last_name'],
                staff_number=data['staff_number'],
                national_id=data['national_id'],
                email=data['email'],
                location=data['location'],
                address=data['address'],
                phone_number=data['phone_number'],

                rides_allocated = data['rides_allocated'],
                rides_used = data['rides_used'],
                max_fare_per_ride = data['max_fare_per_ride'],
                status = data['status'],


                user_id=new_user.user_id,
                corporate_id=new_user.corporate_id,
                
            )
            db.session.add(new_staff)    
        db.session.commit()
        return {
            "message": "User created successfully.",
            "user": user_schema.dump(new_user),
            "staff": staff_schema.dump(new_staff) if new_staff else None
        }
    except IntegrityError as e:
        db.session.rollback()
        raise ValueError("Username, email, staff number or phone number already exists.") from e

    except Exception as e:
        traceback.print_exc()
        db.session.rollback()
        raise ValueError(
            f"Failed to create user. {e}"
        ) from e
    



def get_user_by_id(user_id):
    """
    Get a user by their ID from the database.
    """
    from app.models import User  # Import your User model
    
    try:
        user = User.query.get(user_id)
        return user
    except Exception as e:
        print(f"Error fetching user {user_id}: {str(e)}")
        return None