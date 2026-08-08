# app/api/v1/endpoints/ride_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
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




# ============================================
# 2. GET ALL RIDES
# ============================================
@ride_request_bp.route("/", methods=["GET"])
@jwt_required()
def list_rides():
    """
    Get all rides.
    ---
    tags:
      - Rides
    responses:
      200:
        description: List of all rides
      401:
        description: Unauthorized
    """
    try:
        rides = get_all_rides()
        return jsonify(response_schema_many.dump(rides)), 200
    except Exception as e:
        return jsonify({"message": "Failed to fetch rides", "error": str(e)}), 500


# ============================================
# 3. GET A SINGLE RIDE
# ============================================
@ride_request_bp.route("/<int:ride_id>", methods=["GET"])
@jwt_required()
def fetch_ride(ride_id):
    """
    Get a single ride by ID.
    ---
    tags:
      - Rides
    parameters:
      - in: path
        name: ride_id
        required: true
        type: integer
    responses:
      200:
        description: Ride found
      404:
        description: Ride not found
      401:
        description: Unauthorized
    """
    try:
        ride = get_ride(ride_id)
        return jsonify(response_schema.dump(ride)), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        return jsonify({"message": "Failed to fetch ride", "error": str(e)}), 500


# ============================================
# 4. UPDATE A RIDE
# ============================================
@ride_request_bp.route("/<int:ride_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_ride_endpoint(ride_id):
    """
    Update a ride by ID.
    ---
    tags:
      - Rides
    parameters:
      - in: path
        name: ride_id
        required: true
        type: integer
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            pickup_location:
              type: string
            destination:
              type: string
            base_fare:
              type: number
            status:
              type: string
              enum: ["PENDING", "COMPLETED", "FAILED"]
            reason:
              type: string
            matatu_identifier:
              type: string
    responses:
      200:
        description: Ride updated successfully
      400:
        description: Validation error
      404:
        description: Ride not found
      401:
        description: Unauthorized
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"message": "Request body is required"}), 400
    
    # Validate input
    errors = update_schema.validate(data)
    if errors:
        return jsonify({"errors": errors}), 400
        
    try:
        updated_ride, settlement_result = update_ride(ride_id, data)
        
        if settlement_result:
            return jsonify({
                "message": "Ride updated and settled",
                "ride": response_schema.dump(updated_ride),
                "settlement": settlement_result
            }), 200
        
        return jsonify({
            "message": "Ride updated successfully",
            "ride": response_schema.dump(updated_ride)
        }), 200
        
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": "Failed to update ride", "error": str(e)}), 500


# ============================================
# 5. DELETE A RIDE
# ============================================
@ride_request_bp.route("/<int:ride_id>", methods=["DELETE"])
@jwt_required()
def remove_ride(ride_id):
    """
    Delete a ride by ID.
    ---
    tags:
      - Rides
    parameters:
      - in: path
        name: ride_id
        required: true
        type: integer
    responses:
      200:
        description: Ride deleted successfully
      404:
        description: Ride not found
      401:
        description: Unauthorized
    """
    try:
        delete_ride(ride_id)
        return jsonify({"message": "Ride deleted successfully"}), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        return jsonify({"message": "Failed to delete ride", "error": str(e)}), 500


# ============================================
# 6. SETTLE A RIDE (Manually Trigger Settlement)
# ============================================
@ride_request_bp.route("/<int:ride_id>/settle", methods=["POST"])
@jwt_required()
def settle_ride_endpoint(ride_id):
    """
    Manually settle a completed ride.
    ---
    tags:
      - Rides
    parameters:
      - in: path
        name: ride_id
        required: true
        type: integer
    responses:
      200:
        description: Ride settled successfully
      400:
        description: Cannot settle ride
      404:
        description: Ride not found
      401:
        description: Unauthorized
    """
    try:
        from app.services.ride_request_service import settle_ride
        result = settle_ride(ride_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": "Failed to settle ride", "error": str(e)}), 500


