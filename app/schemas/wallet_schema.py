from marshmallow import Schema, fields, validate
from app.models.wallet import WALLET_TYPES

class CreateWalletSchema(Schema):
    corporate_id = fields.Int(allow_none=True)
    wallet_type = fields.Str(
        required=True,
        validate=validate.OneOf(
            WALLET_TYPES,
            error=f"wallet_type must be one of: {WALLET_TYPES}"
        )
    )
    currency = fields.Str(load_default='KES')
    created_by = fields.Int(required=True)
    
    
class WalletResponseSchema(Schema):
    wallet_id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True) 
    
    corporate_id = fields.Int(dump_only=True)
    wallet_type = fields.Str()   
    currency = fields.Str()
    current_balance = fields.Float()
    created_by = fields.Int()