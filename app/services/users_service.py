import traceback

from pymysql import IntegrityError

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

STAFF_ROLES = [
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
        # else use cop id of the user
        new_user = User(
            username=data['username'],
            role=data['role'],
            corporate_id=data.get('corporate_id')
        )
        # Hash the password before saving
        new_user.set_password(data['password'])
        db.session.add(new_user)
        db.session.flush()      # Flush the session to get the user_id without committing yet

        if new_user.role in STAFF_ROLES:
            # check email uniqueness
            existing_staff = Staff.query.filter_by(
                email=data.get('email')
            ).first()
            if existing_staff:
                raise ValueError("Email already exists.")

                
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
            "staff": staff_schema.dump(new_staff) if new_user.role in STAFF_ROLES else None
        }
    except IntegrityError as e:
        db.session.rollback()
        raise ValueError("Username, email, or staff number already exists.") from e

    except Exception as e:
        traceback.print_exc()
        db.session.rollback()
        raise ValueError(
            f"Failed to create user. {e}"
        ) from e
    
    