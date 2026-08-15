from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.rates_service import (
    create_rate_type,
    get_all_rate_types,
    get_rate_type,
    update_rate_type,
    delete_rate_type,
    create_rate,
    get_all_rates,
    get_rate,
    update_rate,
    delete_rate
)
from app.schemas.rates_schema import RateTypeSchema, RateTypeUpdateSchema, RateSchema, RateUpdateSchema
from app.core.database import db

rates_bp = Blueprint(
    "rates",
    __name__,
    url_prefix="/api/v1"
)

type_schema = RateTypeSchema()
type_update_schema = RateTypeUpdateSchema()
rate_schema = RateSchema()
rate_update_schema = RateUpdateSchema()
rate_schema_many = RateSchema(many=True)

# Rate_type routes
@rates_bp.route("/rate-types", methods=["POST"])
@jwt_required()
def add_rate_type():
    data = request.get_json()
    errors = type_schema.validate(data)
    if errors:
        return jsonify(errors), 400
    
    try:
        new_type = create_rate_type(data)
        return jsonify(type_schema.dump(new_type)), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 409
    
@rates_bp.route("/rate-types", methods=["GET"])
@jwt_required()
def list_rate_types():
    types = get_all_rate_types()
    return jsonify(type_schema.dump(types, many=True)), 200

# ✅ GET Single Rate Type
@rates_bp.route("/rate-types/<int:rate_type_id>", methods=["GET"])
@jwt_required()
def get_rate_type_endpoint(rate_type_id):
    try:
        rate_type = get_rate_type(rate_type_id)
        return jsonify(type_schema.dump(rate_type)), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404


# ✅ UPDATE Rate Type
@rates_bp.route("/rate-types/<int:rate_type_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_rate_type_endpoint(rate_type_id):
    data = request.get_json()
    errors = type_update_schema.validate(data)
    if errors:
        return jsonify(errors), 400
    
    try:
        updated_type = update_rate_type(rate_type_id, data)
        return jsonify({
            "message": "Rate type updated successfully",
            "rate_type": type_schema.dump(updated_type)
        }), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400


# ✅ DELETE Rate Type
@rates_bp.route("/rate-types/<int:rate_type_id>", methods=["DELETE"])
@jwt_required()
def delete_rate_type_endpoint(rate_type_id):
    data = request.get_json()
    user_id = data.get('created_by')
    
    if not user_id:
        return jsonify({"message": "created_by is required"}), 400
    
    try:
        result = delete_rate_type(rate_type_id, user_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "message": "Failed to delete rate type",
            "error": str(e)
        }), 500


    
# Rate routes
@rates_bp.route("/rates", methods=["POST"])
@jwt_required()
def add_rate():
    data = request.get_json()
    errors = rate_schema.validate(data)
    if errors:
        return jsonify(errors), 400
    
    try:
        new_rate = create_rate(data)
        return jsonify(rate_schema.dump(new_rate)), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400


@rates_bp.route("/rates", methods=["GET"])
@jwt_required()
def list_rates():
    rates = get_all_rates()
    return jsonify(rate_schema_many.dump(rates)), 200

#  UPDATE Rate
@rates_bp.route("/rates/<int:rate_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_rate_endpoint(rate_id):
    data = request.get_json()
    errors = rate_update_schema.validate(data)
    if errors:
        return jsonify(errors), 400
    
    try:
        updated_rate = update_rate(rate_id, data)
        return jsonify({
            "message": "Rate updated successfully",
            "rate": rate_schema.dump(updated_rate)
        }), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400


#  DELETE Rate
@rates_bp.route("/rates/<int:rate_id>", methods=["DELETE"])
@jwt_required()
def delete_rate_endpoint(rate_id):
    data = request.get_json()
    user_id = data.get('created_by')
    
    if not user_id:
        return jsonify({"message": "created_by is required"}), 400
    
    try:
        result = delete_rate(rate_id, user_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "message": "Failed to delete rate",
            "error": str(e)
        }), 500
        
