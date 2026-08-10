# app/api/v1/endpoints/ride_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.ride_request_service import (
    create_ride,
    get_all_rides,
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
    
    # ✅ Add debug logging
    print(f"📥 Received ride request data: {data}")
    
    # ✅ Validate input
    errors = create_schema.validate(data)
    if errors:
        print(f"❌ Validation errors: {errors}")
        return jsonify({"errors": errors}), 400
    
    try:
        # ✅ Get current user ID from JWT
        current_user_id = get_jwt_identity()
        print(f"👤 Current user ID: {current_user_id}")
        
        # ✅ Add staff_id to data if not provided
        if 'staff_id' not in data:
            # Get staff_id from user
            from app.models.staff import Staff
            staff = Staff.query.filter_by(user_id=current_user_id).first()
            if not staff:
                return jsonify({"message": "Staff profile not found for this user"}), 400
            data['staff_id'] = staff.staff_id
            print(f"👤 Added staff_id: {staff.staff_id}")
        
        # ✅ Call create_ride - it returns a dictionary
        result = create_ride(data)
        print(f"✅ Ride created successfully: {result}")
        
        # ✅ Return the result directly (it's already a dict)
        return jsonify(result), 201
        
    except ValueError as e:
        print(f"❌ ValueError: {str(e)}")
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": "Failed to create ride", "error": str(e)}), 500

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


