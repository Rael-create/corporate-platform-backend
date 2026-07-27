from marshmallow import Schema, fields, validate
from app.models.rates import RATE_TYPES

class RateTypeSchema(Schema):
    rate_type_id = fields.Int(dump_only=True)
    name = fields.Str(
        required=True,
        validate=validate.OneOf(
            RATE_TYPES,
            error=f"Rate type must be one of: {RATE_TYPES}"
        )
    )
    created_by = fields.Int(required=True)

    

class RateSchema(Schema):
    rate_id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    
    rate = fields.Float(required=True)
    rate_type_id = fields.Int(required=True)
    created_by = fields.Int(required=True)
    