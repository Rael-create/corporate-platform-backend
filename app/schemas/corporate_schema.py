from marshmallow import Schema, fields, validate

WALLET_TYPES = ["PLATFORM WALLET", "CORPORATE WALLET"]

class CorporateSchema(Schema):
    corporate_id = fields.Int(dump_only =True)
    corporate_name = fields.Str(required=True)
    location = fields.Str(required=True)
    address = fields.Str()
    contacts = fields.Str()
    
    created_at = fields.DateTime(dump_only=True)
    
    wallet_type = fields.Str(
        allow_none=True, # It can be null if not provided
        validate=validate.OneOf(
            WALLET_TYPES, 
            error=f"wallet_type must be one of: {WALLET_TYPES}"
        )
    )