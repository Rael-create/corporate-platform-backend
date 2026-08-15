from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.corporate import Corporate
from app.models.users import User
from app.core.database import db
from app.services.corporate_service import (
    create_corporate,
    delete_corporate,
    update_corporate,
    get_all_corporates,
    get_corporate,
)
from app.schemas.corporate_schema import (
    CorporateSchema,
    CorporateCreateSchema,
    CorporateUpdateSchema,
)
import traceback

corporate_bp = Blueprint("corporate", __name__, url_prefix="/api/v1/corporates")

corporate_schema = CorporateSchema()
corporate_schema_many = CorporateSchema(many=True)
corporate_create_schema = CorporateCreateSchema()
corporate_update_schema = CorporateUpdateSchema()


#  CREATE A CORPORATE
@corporate_bp.route("/create", methods=["POST"])
@jwt_required()
def create_corporate_endpoint():

    try:
        # Get current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({"message": "User not found"}), 404

        # ✅ Only SUPER_ADMIN can create corporates
        if current_user.role != "SUPER_ADMIN":
            return (
                jsonify({"message": "Unauthorized. Super Admin access required."}),
                403,
            )

        data = request.get_json()

        if not data:
            return jsonify({"message": "Request body is required"}), 400

        # Validate input
        errors = corporate_create_schema.validate(data)
        if errors:
            return jsonify({"errors": errors}), 400

        # Create corporate
        new_corporate = create_corporate(data, created_by=current_user.user_id)

        return (
            jsonify(
                {
                    "message": "Corporate created successfully",
                    "corporate": corporate_schema.dump(new_corporate),
                }
            ),
            201,
        )

    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create corporate", "error": str(e)}), 500


#  GET ALL CORPORATES
@corporate_bp.route("/", methods=["GET"])
@jwt_required()
def get_all_corporates_endpoint():

    try:
        # Get current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({"message": "User not found"}), 404

        # ✅ Only SUPER_ADMIN can access all corporates
        if current_user.role != "SUPER_ADMIN":
            return (
                jsonify({"message": "Unauthorized. Super Admin access required."}),
                403,
            )

        corporates = get_all_corporates()

        return (
            jsonify(
                {
                    "corporates": corporate_schema_many.dump(corporates),
                    "total": len(corporates),
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"message": "Failed to fetch corporates", "error": str(e)}), 500


#  GET A SINGLE CORPORATE
@corporate_bp.route("/<int:corporate_id>", methods=["GET"])
@jwt_required()
def get_corporate_endpoint(corporate_id):

    try:
        # Get current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({"message": "User not found"}), 404

        # ✅ Only SUPER_ADMIN can access corporate details
        if current_user.role != "SUPER_ADMIN":
            return (
                jsonify({"message": "Unauthorized. Super Admin access required."}),
                403,
            )

        corporate = get_corporate(corporate_id)

        return jsonify(corporate_schema.dump(corporate)), 200

    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        return jsonify({"message": "Failed to fetch corporate", "error": str(e)}), 500


# UPDATE A CORPORATE
@corporate_bp.route("/update/<int:corporate_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_corporate_endpoint(corporate_id):

    try:
        # Get current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({"message": "User not found"}), 404

        # ✅ Only SUPER_ADMIN can update corporates
        if current_user.role != "SUPER_ADMIN":
            return (
                jsonify({"message": "Unauthorized. Super Admin access required."}),
                403,
            )

        data = request.get_json()

        if not data:
            return jsonify({"message": "Request body is required"}), 400

        # Validate input
        errors = corporate_update_schema.validate(data)
        if errors:
            return jsonify({"errors": errors}), 400

        # Update corporate
        updated_corporate = update_corporate(corporate_id, data)

        return (
            jsonify(
                {
                    "message": "Corporate updated successfully",
                    "corporate": corporate_schema.dump(updated_corporate),
                }
            ),
            200,
        )

    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update corporate", "error": str(e)}), 500


#  DELETE A CORPORATE
@corporate_bp.route("/delete/<int:corporate_id>", methods=["DELETE"])
@jwt_required()
def delete_corporate_endpoint(corporate_id):

    try:
        # Get current user
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({"message": "User not found"}), 404

        # ✅ Only SUPER_ADMIN can delete corporates
        if current_user.role != "SUPER_ADMIN":
            return (
                jsonify({"message": "Unauthorized. Super Admin access required."}),
                403,
            )

        result = delete_corporate(corporate_id)

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({"message": "Failed to delete corporate", "error": str(e)}), 500
