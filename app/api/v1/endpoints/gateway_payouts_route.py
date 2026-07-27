from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.gateway_payouts_service import (
    create_payout,
    get_all_payouts,
    get_payout,
    update_payout,
    delete_payout
)
from app.schemas.gateway_payouts_schema import (
    CreateGatewayPayoutSchema,
    UpdateGatewayPayoutSchema,
    GatewayPayoutResponseSchema
)

gateway_payout_bp = Blueprint("gateway_payouts", __name__, url_prefix="/api/v1/payouts")

# Initialize schemas
create_schema = CreateGatewayPayoutSchema()
update_schema = UpdateGatewayPayoutSchema()
response_schema = GatewayPayoutResponseSchema()
response_schema_many = GatewayPayoutResponseSchema(many=True)

# --- CREATE ---
@gateway_payout_bp.route("/create", methods=["POST"])
@jwt_required()
def add_payout():
    data = request.get_json()
    errors = create_schema.validate(data)
    if errors:
        return jsonify(errors), 400
        
    try:
        new_payout = create_payout(data)
        return jsonify(response_schema.dump(new_payout)), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": "Failed to create payout", "error": str(e)}), 500

# --- UPDATE ---
@gateway_payout_bp.route("/<int:payout_id>", methods=["PUT", "PATCH"])
@jwt_required()
def modify_payout(payout_id):
    data = request.get_json()
    errors = update_schema.validate(data)
    if errors:
        return jsonify(errors), 400
        
    try:
        updated_payout = update_payout(payout_id, data)
        return jsonify(response_schema.dump(updated_payout)), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        return jsonify({"message": "Failed to update payout", "error": str(e)}), 500

# --- GET ALL ---
@gateway_payout_bp.route("/", methods=["GET"])
@jwt_required()
def list_payouts():
    payouts = get_all_payouts()
    return jsonify(response_schema_many.dump(payouts)), 200

# --- GET SINGLE ---
@gateway_payout_bp.route("/<int:payout_id>", methods=["GET"])
@jwt_required()
def fetch_payout(payout_id):
    try:
        payout = get_payout(payout_id)
        return jsonify(response_schema.dump(payout)), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404

# --- DELETE ---
@gateway_payout_bp.route("/<int:payout_id>", methods=["DELETE"])
@jwt_required()
def remove_payout(payout_id):
    try:
        delete_payout(payout_id)
        return jsonify({"message": "Payout deleted successfully"}), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404