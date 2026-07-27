from flask import Blueprint, request, jsonify
from app.services.staff_service import update_staff_by_admin
from app.schemas.staff_schema import UpdateStaffSchema
from flask_jwt_extended import jwt_required
from app.utils.decorators import role_required

staff_bp = Blueprint(
    "staff",
    __name__,
    url_prefix="/api/v1/staff"
)

update_staff_schema = UpdateStaffSchema()


@staff_bp.route("/<int:staff_id>", methods=["PATCH"])
@jwt_required()
@role_required("CORPORATE_ADMIN", "SUPER_ADMIN")
def manage_staff(staff_id):
    
    data = request.get_json()
    
    # 1. Validate incoming data
    errors = update_staff_schema.validate(data)
    if errors:
        return jsonify(errors), 400
        
    try:
        # 2. Call the service function you provided
        updated_staff = update_staff_by_admin(staff_id, data)

        return jsonify({
            "message": "Staff updated successfully",
            "staff": {
                "staff_id": updated_staff.staff_id,
                "first_name": updated_staff.first_name,
                "last_name": updated_staff.last_name,
                "rides_allocated": updated_staff.rides_allocated,
                "rides_used": updated_staff.rides_used,
                "max_fare_per_ride": updated_staff.max_fare_per_ride,
                "status": updated_staff.status
            }
        }), 200

    except ValueError as e:
        return jsonify({"message": str(e)}), 403
    except Exception as e:
        return jsonify({"message":"failed to update staff", "error": str(e)}), 500

        