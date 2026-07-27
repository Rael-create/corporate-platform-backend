from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.rates_service import (
    create_rate_type,
    get_all_rate_types,
    create_rate,
    get_all_rates
)
from app.schemas.rates_schema import RateTypeSchema,RateSchema

rates_bp = Blueprint(
    "rates",
    __name__,
    url_prefix="/api/v1"
)

type_schema = RateTypeSchema()
rate_schema = RateSchema()
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
        
