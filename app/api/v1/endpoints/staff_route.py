from flask import Blueprint, request, jsonify
from app.services.staff_service import( 
    update_staff_by_admin,
    get_all_staff,
    get_staff_by_id,
    get_staff_by_corporate,
    delete_staff,
    create_staff_from_user 
    )
from app.schemas.staff_schema import UpdateStaffSchema, StaffCreateSchema, StaffSchema
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.decorators import role_required
from app.models.staff import Staff
from app.models.users import User
from app.models.corporate import Corporate
from app.core.database import db

staff_bp = Blueprint(
    "staff",
    __name__,
    url_prefix="/api/v1/staff"
)

update_staff_schema = UpdateStaffSchema()
staff_schema = StaffSchema()
staff_schema_many = StaffSchema(many=True)
staff_create_schema = StaffCreateSchema()


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

#  GET ALL STAFF MEMBERS
@staff_bp.route("/", methods=["GET"])
@jwt_required()
@role_required("CORPORATE_ADMIN", "SUPER_ADMIN")
def get_all_staff_endpoint():

    try:
        # Get current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"message": "User not found"}), 404
        
        # Check if user is authorized (SUPER_ADMIN or CORPORATE_ADMIN)
        if current_user.role not in ["SUPER_ADMIN", "CORPORATE_ADMIN"]:
            return jsonify({"message": "Unauthorized. Admin access required."}), 403
        
        # If CORPORATE_ADMIN, only get staff from their corporate
        if current_user.role == "CORPORATE_ADMIN":
            staff_members = Staff.query.filter_by(corporate_id=current_user.corporate_id).all()
        else:
            # SUPER_ADMIN gets all staff
            staff_members = get_all_staff()
        
        return jsonify({
            "staff": staff_schema_many.dump(staff_members),
            "total": len(staff_members)
        }), 200
        
    except Exception as e:
        return jsonify({"message": "Failed to fetch staff", "error": str(e)}), 500

#  GET A SINGLE STAFF MEMBER
@staff_bp.route("/<int:staff_id>", methods=["GET"])
@jwt_required()
def get_staff_by_id_endpoint(staff_id):
    
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"message": "User not found"}), 404
        
        # Check if user is authorized
        if current_user.role not in ["SUPER_ADMIN", "CORPORATE_ADMIN"]:
            return jsonify({"message": "Unauthorized. Admin access required."}), 403
        
        # Get staff member
        staff = get_staff_by_id(staff_id)
        
        # If CORPORATE_ADMIN, ensure staff belongs to their corporate
        if current_user.role == "CORPORATE_ADMIN" and staff.corporate_id != current_user.corporate_id:
            return jsonify({"message": "Unauthorized. Staff does not belong to your corporate."}), 403
        
        return jsonify(staff_schema.dump(staff)), 200
        
    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        return jsonify({"message": "Failed to fetch staff", "error": str(e)}), 500


# 4. DELETE A STAFF MEMBER
@staff_bp.route("/<int:staff_id>", methods=["DELETE"])
@jwt_required()
def delete_staff_endpoint(staff_id):

    try:
        # Get current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"message": "User not found"}), 404
        
        # Check if user is authorized (SUPER_ADMIN or CORPORATE_ADMIN)
        if current_user.role not in ["SUPER_ADMIN", "CORPORATE_ADMIN"]:
            return jsonify({
                "message": "Unauthorized. Admin access required."
            }), 403
        
        # Get the staff member to delete
        staff = Staff.query.get(staff_id)
        if not staff:
            return jsonify({"message": "Staff member not found"}), 404
        
        # If CORPORATE_ADMIN, ensure staff belongs to their corporate
        if current_user.role == "CORPORATE_ADMIN":
            # Check if staff belongs to the admin's corporate
            if staff.corporate_id != current_user.corporate_id:
                return jsonify({
                    "message": "Unauthorized. You can only delete staff from your corporate."
                }), 403
            
            # Prevent deleting yourself (optional but recommended)
            if staff.user_id == current_user.user_id:
                return jsonify({
                    "message": "You cannot delete your own staff profile."
                }), 403
        
        # Get the associated user
        user = User.query.get(staff.user_id)
        
        # Delete staff record
        db.session.delete(staff)
        
        # Delete user record if it exists
        if user:
            db.session.delete(user)
        
        db.session.commit()
        
        return jsonify({
            "message": "Staff member deleted successfully",
            "staff_id": staff_id,
            "deleted_by": current_user.username,
            "deleted_by_role": current_user.role
        }), 200
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "message": "Failed to delete staff",
            "error": str(e)
        }), 500

# 5. GET STAFF BY CORPORATE
@staff_bp.route("/corporate/<int:corporate_id>", methods=["GET"])
@jwt_required()
def get_staff_by_corporate_endpoint(corporate_id):

    try:
        # Get current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"message": "User not found"}), 404
        
        # Check if user is authorized
        if current_user.role not in ["SUPER_ADMIN", "CORPORATE_ADMIN"]:
            return jsonify({"message": "Unauthorized. Admin access required."}), 403
        
        # Check if corporate exists
        corporate = Corporate.query.get(corporate_id)
        if not corporate:
            return jsonify({"message": "Corporate not found"}), 404
        
        # If CORPORATE_ADMIN, ensure they're accessing their own corporate
        if current_user.role == "CORPORATE_ADMIN" and corporate_id != current_user.corporate_id:
            return jsonify({"message": "Unauthorized. You can only view staff from your corporate."}), 403
        
        staff_members = get_staff_by_corporate(corporate_id)
        
        return jsonify({
            "corporate": corporate.corporate_name,
            "staff": staff_schema_many.dump(staff_members),
            "total": len(staff_members)
        }), 200
        
    except Exception as e:
        return jsonify({"message": "Failed to fetch staff", "error": str(e)}), 500


# 6. CREATE STAFF FROM USER
@staff_bp.route("/create", methods=["POST"])
@jwt_required()
def create_staff_endpoint():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"message": "Request body is required"}), 400
        
        # Validate input
        errors = staff_create_schema.validate(data)
        if errors:
            return jsonify({"errors": errors}), 400
        
        # Get current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({"message": "User not found"}), 404
        
        # Check if user is authorized
        if current_user.role not in ["SUPER_ADMIN", "CORPORATE_ADMIN"]:
            return jsonify({"message": "Unauthorized. Admin access required."}), 403
        
        # ✅ Get user_id from data
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({"message": "user_id is required"}), 400
        
        # ✅ If user is SUPER_ADMIN, corporate_id can be None
        # Get the user to check their role
        target_user = User.query.get(user_id)
        if not target_user:
            return jsonify({"message": "Target user not found"}), 404
        
        # ✅ If target user is SUPER_ADMIN, corporate_id is optional
        if target_user.role == 'SUPER_ADMIN':
            # corporate_id can be None or omitted
            pass
        elif not data.get('corporate_id'):
            return jsonify({"message": "corporate_id is required for STAFF and CORPORATE_ADMIN roles"}), 400
        
        # Create staff
        new_staff = create_staff_from_user(user_id, data)
        
        return jsonify({
            "message": "Staff created successfully",
            "staff": staff_schema.dump(new_staff)
        }), 201
        
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create staff", "error": str(e)}), 500