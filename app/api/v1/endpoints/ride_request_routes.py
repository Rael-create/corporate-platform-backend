from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.ride_request_service import (
    create_ride,
    get_all_rides,
    update_ride,
    get_ride,
    delete_ride,
)
from app.schemas.ride_request_schema import (
    CreateRideRequestSchema,
    UpdateRideRequestSchema,
    RideRequestResponseSchema
)

ride_request_bp = Blueprint("ride_requests", __name__, url_prefix="/api/v1/rides")

create_schema = CreateRideRequestSchema()
response_schema = RideRequestResponseSchema()
update_schema = UpdateRideRequestSchema()
response_schema_many = RideRequestResponseSchema(many=True)

@ride_request_bp.route("/create", methods=["POST"])
@jwt_required()
def add_ride():
    data = request.get_json()
    errors = create_schema.validate(data)
    if errors:
        return jsonify(errors), 400
        
    try:
        # Call the function directly!
        new_ride = create_ride(data)
        return jsonify(response_schema.dump(new_ride)), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": "Failed to create ride", "error": str(e)}), 500


#@ride_request_bp.route("/payment", methods=["POST"])


# UPDATE a ride (with settlement trigger)
@ride_request_bp.route("/<int:ride_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_ride_endpoint(ride_id):
    data = request.get_json()
    
    # Validate input
    errors = update_schema.validate(data)
    if errors:
        return jsonify(errors), 400
        
    try:
        # 1. Update the ride (now returns a tuple)
        updated_ride, settlement_result = update_ride(ride_id, data)
        
        # 2. If settlement happened, include it in the response
        if settlement_result:
            return jsonify({
                "message": "Ride updated and settled",
                "ride": response_schema.dump(updated_ride),
                "settlement": settlement_result
            }), 200
        
        return jsonify(response_schema.dump(updated_ride)), 200
        
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": "Failed to update ride", "error": str(e)}), 500



# @ride_request_bp.route("/<int:ride_id>", methods=["PUT", "PATCH"])
# def modify_ride(ride_id):
#     data = request.get_json()
#     errors = update_schema.validate(data)
#     if errors:
#         return jsonify(errors), 400

#     try:
#         updated_ride = update_ride(ride_id, data)
#         return jsonify(response_schema.dump(updated_ride)), 200
#     except ValueError as e:
#         return jsonify({"message": str(e)}), 404
#     except Exception as e:
#         return jsonify({"message": "Failed to update ride", "error": str(e)}), 500

# GET all rides
@ride_request_bp.route("/", methods=["GET"])
@jwt_required()
def list_rides():
    rides = get_all_rides()
    return jsonify(response_schema_many.dump(rides)), 200


# GET a single ride
@ride_request_bp.route("/<int:ride_id>", methods=["GET"])
@jwt_required()
def fetch_ride(ride_id):
    try:
        ride = get_ride(ride_id)
        return jsonify(response_schema.dump(ride)), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404


# DELETE a ride
@ride_request_bp.route("/<int:ride_id>", methods=["DELETE"])
@jwt_required()
def remove_ride(ride_id):
    try:
        delete_ride(ride_id)
        return jsonify({"message": "Ride deleted successfully"}), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404



