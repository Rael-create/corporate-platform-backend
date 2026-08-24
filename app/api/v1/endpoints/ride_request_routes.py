# app/api/v1/endpoints/ride_routes.py
from flask import Blueprint, redirect, request, jsonify,url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.core.database import db
from app.models.gateway_payouts import GatewayPayout
from app.models.ride_request import RideRequest
from app.models.staff import Staff
from app.services.ride_request_service import (
    create_ride_only,
    get_all_rides,
    get_ride,
    delete_ride,
    process_ride_after_authorization,
)
from app.schemas.ride_request_schema import (
    CreateRideRequestSchema,
    UpdateRideRequestSchema,
    RideRequestResponseSchema,
)

ride_request_bp = Blueprint("ride_requests", __name__, url_prefix="/api/v1/rides")

create_ride_schema = CreateRideRequestSchema()
response_schema = RideRequestResponseSchema()
update_schema = UpdateRideRequestSchema()
response_schema_many = RideRequestResponseSchema(many=True)


@ride_request_bp.route("/create", methods=["POST"])
@jwt_required()
def add_ride():
    data = request.get_json()
    errors = create_ride_schema.validate(data)
    if errors:
        return jsonify({"errors": errors}), 400

    try:
        current_user_id = get_jwt_identity()
        # ensure staff_id is present (if missing, add it)
        if "staff_id" not in data:
            staff = Staff.query.filter_by(user_id=current_user_id).first()
            if not staff:
                return jsonify({"message": "Staff profile not found"}), 400
            data["staff_id"] = staff.staff_id

        # ✅ Create ONLY the ride and payout
        new_ride, new_payout = create_ride_only(data)
        db.session.commit()

        

        # ✅ Redirect to processing endpoint
        return redirect(
            url_for('ride_requests.process_ride', ride_id=new_ride.ride_id),
            code=307
        )

    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create ride", "error": str(e)}), 500

@ride_request_bp.route("/<int:ride_id>/process", methods=["GET", "POST"])
@jwt_required()
def process_ride(ride_id):

    try:
        current_user_id = get_jwt_identity()

        # Fetch ride
        ride = RideRequest.query.get(ride_id)
        if not ride:
            return jsonify({"message": "Ride not found"}), 404

        # Security: ensure the ride belongs to the current user's staff
        staff = Staff.query.filter_by(user_id=current_user_id).first()
        if not staff or ride.staff_id != staff.staff_id:
            return jsonify({"message": "Unauthorized"}), 403

        # Fetch the associated payout
        payout = GatewayPayout.query.filter_by(ride_id=ride_id).first()
        if not payout:
            return jsonify({"message": "Payout not found"}), 404

        # Re‑create a minimal auth_ride engine
        from app.services.auth_service import TripAuthorizationEngine
        auth_ride = TripAuthorizationEngine(staff, ride.base_fare, db_session=db, data={})

        # Call the processing function
        result = process_ride_after_authorization(
            staff=staff,
            new_ride=ride,
            new_payout=payout,
            auth_message="Ride processed successfully",
            auth_ride=auth_ride
        )

        return jsonify(result), 200

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error processing ride: {str(e)}")
        return jsonify({"message": "Failed to process ride", "error": str(e)}), 500

# GET ALL RIDES
@ride_request_bp.route("/", methods=["GET"])
@jwt_required()
def list_rides():

    try:
        rides = get_all_rides()
        return jsonify(response_schema_many.dump(rides)), 200
    except Exception as e:
        return jsonify({"message": "Failed to fetch rides", "error": str(e)}), 500


# GET A SINGLE RIDE
@ride_request_bp.route("/<int:ride_id>", methods=["GET"])
@jwt_required()
def fetch_ride(ride_id):

    try:
        ride = get_ride(ride_id)
        return jsonify(response_schema.dump(ride)), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        return jsonify({"message": "Failed to fetch ride", "error": str(e)}), 500


# DELETE A RIDE
@ride_request_bp.route("/<int:ride_id>", methods=["DELETE"])
@jwt_required()
def remove_ride(ride_id):

    try:
        delete_ride(ride_id)
        return jsonify({"message": "Ride deleted successfully"}), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        return jsonify({"message": "Failed to delete ride", "error": str(e)}), 500
