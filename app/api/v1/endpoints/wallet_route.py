from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.wallet_service import (
    create_wallet,
    get_wallet,
    get_all_wallets,
    top_up_wallet
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