from marshmallow import Schema, fields, validate
from app.models.ledger_entry import TRANSACTION_CLASSES, TRANSACTION_TYPES

class CreateLedgerEntrySchema(Schema):
    wallet_id = fields.Int(required=True)
    ride_id = fields.Int(allow_none=True)
    
    transaction_type = fields.Str(
        required=True,
        validate=validate.OneOf(TRANSACTION_TYPES)
    )
    transaction_class = fields.Str(
        required=True,
        validate=validate.OneOf(TRANSACTION_CLASSES)
    ) 
    amount = fields.Float(required=True)

class LedgerEntryResponseSchema(Schema):
    entry_id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    
    wallet_id = fields.Int()
    ride_id = fields.Int()
    transaction_type = fields.Str()
    transaction_class = fields.Str()
    amount = fields.Float()