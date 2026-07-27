from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.ledger_entry_service import (
    create_ledger_entry,
    get_all_ledger_entries,
    get_ledger_by_wallet
)
from app.schemas.ledger_entry_schema import (
    CreateLedgerEntrySchema,
    LedgerEntryResponseSchema
)

ledger_bp = Blueprint(
    "ledger",
    __name__,
    url_prefix="/api/v1/ledger"
)

create_schema = CreateLedgerEntrySchema()
response_schema = LedgerEntryResponseSchema()
response_schema_many = LedgerEntryResponseSchema(many=True)

@ledger_bp.route("/create", methods=["POST"])
@jwt_required()
def add_ledger_entry():
    data = request.get_json()
    errors = create_schema.validate(data)
    if errors:
        return jsonify(errors), 400
    try:
        new_entry = create_ledger_entry(data)
        return jsonify(response_schema.dump(new_entry)), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400


@ledger_bp.route("/", methods=["GET"])
@jwt_required()
def list_ledger_entries():
    entries = get_all_ledger_entries()
    return jsonify(response_schema_many.dump(entries)), 200

@ledger_bp.route("/wallet/<int:wallet_id>", methods=["GET"])
@jwt_required()
def list_wallet_ledger(wallet_id):
    entries = get_ledger_by_wallet(wallet_id)
    return jsonify(response_schema_many.dump(entries)), 200

