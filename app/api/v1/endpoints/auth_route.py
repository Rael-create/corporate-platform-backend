from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app.models.staff import Staff
from app.models.users import User
from app.services.otp_service import request_staff_otp, verify_staff_otp

auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/v1/auth"
)

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Passwordless login endpoint.
    Accepts only username and returns JWT token with full user details.
    """
    data = request.get_json()
    username = data.get("username")

    if not username:
        return jsonify({"message": "Username is required"}), 400

    # Find the user by username
    user = User.query.filter_by(username=username).first()


    access_token = create_access_token(
        identity=str(user.user_id), 
        additional_claims={"role": user.role}
    )

    # Build user info dictionary
    user_info = {
        "user_id": user.user_id,
        "username": user.username,
        "role": user.role
    }

    # If user is STAFF or CORPORATE_ADMIN, add staff details
    if user.role in ["STAFF", "CORPORATE_ADMIN"]:
        staff = Staff.query.filter_by(user_id=user.user_id).first()
        if staff:
            user_info["first_name"] = staff.first_name
            user_info["last_name"] = staff.last_name
            user_info["staff_id"] = staff.staff_id

    # Build final response
    response = {
        "message": "Login successful",
        "access_token": access_token,
        "user": user_info
    }

    return jsonify(response), 200


@auth_bp.route("/request-otp", methods=["POST"])
def get_otp():
    """Staff requests an OTP to their phone number."""
    data = request.get_json()
    phone_number = data["phone_number"]

    if not phone_number:
        return jsonify({"message": "Phone number is required"}), 400

    phone_number = "0" + str(data["phone_number"])[-9:]

    try:
        result = request_staff_otp(phone_number)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

@auth_bp.route("/login-otp", methods=["POST"])
def login_with_otp():
    """Staff logs in using the OTP they received."""

    data = request.get_json()
    phone_number = "0" + str(data["phone_number"])[-9:]
    otp_code = data.get("otp_code")

    if not phone_number or not otp_code:
        return jsonify({"message": "Phone number and OTP code are required"}), 400

    try:
        result = verify_staff_otp(phone_number, otp_code)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 401