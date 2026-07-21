# from flask import Blueprint, request, jsonify
# from marshmallow import fields, validate
# from app.services.ride_request_service import RideRequestService
# from app.schemas.ride_request_schema import RideRequestResponseSchema

# ride_approval_bp = Blueprint(
#     "ride_approvals",
#     __name__,
#     url_prefix="/api/v1/ride-approvals"
# )

# response_schema = RideRequestResponseSchema()

# @ride_approval_bp.route("/<int:ride_id>", methods=["POST"])
# def approve_or_reject_ride(ride_id):
#     data = request.get_json()
    
#     errors = {}
#     if 'decision' not in data:
#         errors['decision'] = ['Missing data for required field.']
#     elif data['decision'] not in ["APPROVED", "REJECTED"]:
#         errors['decision'] = ['Must be either APPROVED or REJECTED.']
        
#     if errors:
#         return jsonify(errors), 400
    
#     try:
#         # 2. Call the service to update the status
#         updated_ride = RideRequestService.update_ride_status(ride_id, data['decision'])
        
#         # 3. Return the updated ride details
#         return jsonify(response_schema.dump(updated_ride)), 200
        
#     except ValueError as e:
#         return jsonify({"message": str(e)}), 400
#     except Exception as e:
#         return jsonify({"message": "Failed to update ride status"}), 500