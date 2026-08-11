from marshmallow import Schema, fields, validate
from app.models.corporate import CorporateStatus

WALLET_TYPES = [
    "CORPORATE_FUNDED",    # Company deposits their own money
    "PLATFORM_FUNDED",  # Platform gives them credit
    "PLATFORM_REVENUE"     # System wallet for platform earnings
]
 
class CorporateSchema(Schema):
    """Schema for returning corporate data."""
    corporate_id = fields.Int(dump_only =True)
    corporate_name = fields.Str(required=True)
    location = fields.Str(required=True)
    address = fields.Str(required=True)
    contacts = fields.Str(required=True)
    status = fields.Str(
    load_default="ACTIVE",
    validate=validate.OneOf(
        CorporateStatus,
        error="status must be ACTIVE or INACTIVE"
    )
)

    
    
    wallet_type = fields.Str(
        allow_none=True, # It can be null if not provided
        validate=validate.OneOf(
            WALLET_TYPES, 
            error=f"wallet_type must be one of: {WALLET_TYPES}"
        )
    )

    created_at = fields.DateTime(dump_only=True)

class CorporateCreateSchema(Schema):
    """Schema for creating a new corporate."""
    corporate_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    location = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    address = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    contacts = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    wallet_type = fields.Str(required=True, validate=validate.OneOf(WALLET_TYPES))
    status = fields.Str(validate=validate.OneOf(CorporateStatus), load_default="ACTIVE")


class CorporateUpdateSchema(Schema):
    """Schema for updating a corporate."""
    corporate_name = fields.Str(validate=validate.Length(min=1, max=100))
    location = fields.Str(validate=validate.Length(min=1, max=100))
    address = fields.Str(validate=validate.Length(min=1, max=200))
    contacts = fields.Str(validate=validate.Length(min=1, max=100))
    wallet_type = fields.Str(validate=validate.OneOf(WALLET_TYPES))
    status = fields.Str(validate=validate.OneOf(CorporateStatus))