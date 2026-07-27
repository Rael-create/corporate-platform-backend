from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app.models.users import User

auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/v1/auth"
)

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()

    if not user :#or not user.check_password(password):
        return jsonify({"message": "Invalid username"}), 401

    access_token = create_access_token(
        identity=str(user.user_id), 
        additional_claims={"role": user.role}
    )

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user": {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role
        }
    }), 200