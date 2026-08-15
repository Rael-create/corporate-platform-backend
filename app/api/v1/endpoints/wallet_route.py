from flask import Blueprint, request, jsonify
from app.core.database import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.users import User
from app.services.wallet_service import (
    create_wallet,
    get_wallet,
    get_all_wallets,
    top_up_wallet,
    delete_wallet,
    transfer_from_platform_to_corporate
)
from app.schemas.wallet_schema import (
    CreateWalletSchema,
    WalletResponseSchema
)

wallet_bp = Blueprint(
    "wallets",
    __name__,
    url_prefix="/api/v1/wallets"
)

create_schema = CreateWalletSchema()
response_schema = WalletResponseSchema()
response_schema_many = WalletResponseSchema(many=True)

@wallet_bp.route("/create", methods=["POST"])
@jwt_required()
def add_wallet():
    data = request.get_json()
    errors = create_schema.validate(data)
    if errors:
        return jsonify(errors), 400
    
    try:
        new_wallet = create_wallet(data)
        return jsonify(new_wallet), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

@wallet_bp.route("/<int:wallet_id>/top-up", methods=["POST"])
@jwt_required()
def top_up(wallet_id):
    data = request.get_json()
    try:
        updated_wallet, ledger_entry = top_up_wallet(
            wallet_id, 
            data['amount'],
            initial_top_up = False
        )
        return jsonify({
            "message": "Wallet topped up",
            "new_balance": updated_wallet.current_balance,
            "ledger_entry_id": ledger_entry.entry_id
        }), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

@wallet_bp.route("/transfer-from-platform", methods=["POST"])
@jwt_required()
def transfer_from_platform():
    data = request.get_json()
    corporate_wallet_id = data.get('corporate_wallet_id')
    amount = data.get('amount')
    if not corporate_wallet_id or not amount:
        return jsonify({"message": "corporate_wallet_id and amount are required"}), 400

    try:
        # Optionally check that the user is SUPER_ADMIN
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if current_user.role != "SUPER_ADMIN":
            return jsonify({"message": "Unauthorized. Super Admin access required."}), 403

        result = transfer_from_platform_to_corporate(corporate_wallet_id, float(amount), current_user_id)
        return jsonify({
            "message": "Transfer successful",
            "new_platform_balance": result["platform_wallet"].current_balance,
            "new_corporate_balance": result["corporate_wallet"].current_balance,
        }), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    
@wallet_bp.route("/", methods=["GET"])
@jwt_required()
def list_wallets():
    wallets = get_all_wallets()
    return jsonify(response_schema_many.dump(wallets)), 200

@wallet_bp.route("/<int:wallet_id>", methods=["GET"])
@jwt_required()
def fetch_wallet(wallet_id):
    try:
        wallet = get_wallet(wallet_id)
        return jsonify(response_schema.dump(wallet)), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404


@wallet_bp.route("/<int:wallet_id>", methods=["DELETE"])
@jwt_required()
def delete_wallet_endpoint(wallet_id):

    try:
        result = delete_wallet(wallet_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "message": "Failed to delete wallet",
            "error": str(e)
        }), 500