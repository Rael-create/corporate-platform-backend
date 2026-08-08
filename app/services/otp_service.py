import random
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token
from app.core.database import db
from app.models.users import User
from app.models.staff import Staff
from app.services.sms_service import SMSNotification

ALLOWED_ROLES = ["SUPER_ADMIN", "CORPORATE_ADMIN", "STAFF"]


def generate_otp():
    """Gerates a random 4-digit OTP code."""
    return str(random.randint(1000, 9999))


def request_staff_otp(phone_number):
    """Generates and sends an OTP to any registered user's phone number"""
    # Find the staff member by phone number
    staff = Staff.query.filter_by(phone_number=phone_number).first()
    if not staff:
        raise ValueError("Phone number not registered.")

    # Get the linked User Account
    user = User.query.get(staff.user_id)
    if not user:
        raise ValueError("User Account not found.")

    # Verify the user's role is allowed
    if user.role not in ALLOWED_ROLES:
        raise ValueError(f"OTP login is only available for {ALLOWED_ROLES}.")

    # Verify the staff status is active
    if staff.status != "ACTIVE":
        raise ValueError("Your account is not active. Please contact support.")

    # Generate a random 4-digit OTP
    otp = generate_otp()
    expires_at = datetime.now() + timedelta(minutes=5)

    # Save to database
    user.otp_code = otp
    user.otp_expires_at = expires_at
    db.session.commit()

    # Send SMS
    sms = SMSNotification(
        phone_number=phone_number,
        message=f"Your login code is: {otp}. Valid for 5 minutes. Do not share this code.",
        message_type="otp",
    )
    sms.send()

    return {
        "message": "OTP sent successfully to your phone number.",
        "phone_number": phone_number,
        "otp": otp,
    }


def verify_staff_otp(phone_number, otp_code):
    """Verifies the OTP and returns a JWT if valid."""

    # Find the staff member
    staff = Staff.query.filter_by(phone_number=phone_number).first()
    if not staff:
        raise ValueError("Invalid phone number.")

    user = User.query.get(staff.user_id)
    if not user:
        raise ValueError("User account not found.")

    # Check if OTP matches
    if not user.otp_code or user.otp_code != otp_code:
        raise ValueError("Invalid OTP code.")

    # Check if OTP has expired
    if user.otp_expires_at < datetime.now():
        raise ValueError("OTP has expired. Please request a new one.")

    # OTP is Valid, Clear it from the database
    user.otp_code = None
    user.otp_expires_at = None
    db.session.commit()

    # Generate the JWT Access Token
    access_token = create_access_token(
        identity=str(user.user_id), additional_claims={"role": user.role}
    )

    return {
        "message": "Login successful",
        "access_token": access_token,
        "user": {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role,
            "staff_id": staff.staff_id,
            "first_name": staff.first_name,
            "last_name": staff.last_name,
        },
    }
