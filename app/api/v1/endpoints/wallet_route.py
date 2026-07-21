from flask import Blueprint, request, jsonify
from app.services.wallet_service import (
    create_wallet,
    get_wallet,
    get_all_wallets
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
def add_wallet():
    data = request.get_json()
    errors = create_schema.validate(data)
    if errors:
        return jsonify(errors), 400
    
    try:
        new_wallet = create_wallet(data)
        return jsonify(response_schema.dump(new_wallet)), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    
@wallet_bp.route("/", methods=["GET"])
def list_wallets():
    wallets = get_all_wallets()
    return jsonify(response_schema_many.dump(wallets)), 200

@wallet_bp.route("/<int:wallet_id>", methods=["GET"])
def fetch_wallet(wallet_id):
    try:
        wallet = get_wallet(wallet_id)
        return jsonify(response_schema.dump(wallet)), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404