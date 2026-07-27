from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.services.corporate_service import create_corporate, delete_corporate, update_corporate
from app.schemas.corporate_schema import CorporateSchema

corporate_bp = Blueprint(
    "corporate",
    __name__,
    url_prefix="/api/v1/corporates"
)

corporate_schema = CorporateSchema()


@corporate_bp.route("/create", methods=["POST"])
@jwt_required()
def create_new_corporate():
    # check here

    data = request.get_json()

    errors = corporate_schema.validate(data)

    if errors:
        return jsonify(errors), 400
    
    new_corporate = create_corporate(data)

    return (
        jsonify(corporate_schema.dump(new_corporate)), 201
    )

@corporate_bp.route("/delete/<int:corporate_id>", methods=["DELETE"])
@jwt_required()
def remove_corporate(corporate_id):
    try:
        result = delete_corporate(corporate_id)

        return jsonify({
            "success": True,
            "data": result
        }), 200

    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 404

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
        
#update corporate
@corporate_bp.route("/update/<int:corporate_id>", methods=["PUT"])
@jwt_required()
def update_existing_corporate(corporate_id):
    try:
        data = request.get_json()

        updated_corporate = update_corporate(
            corporate_id,
            data
        )

        return jsonify({
            "success": True,
            "data": corporate_schema.dump(updated_corporate)
        }), 200

    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 404

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500