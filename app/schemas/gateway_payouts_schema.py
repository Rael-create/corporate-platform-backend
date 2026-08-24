from marshmallow import Schema, fields, validate
from app.models.gateway_payouts import PayoutStatus, PaymentMethod  

class CreateGatewayPayoutSchema(Schema):
    ride_id = fields.Int(required=True)
    target_identifier = fields.Str(required=True)
    payment_method = fields.Str(
        required=True,
        validate=validate.OneOf(PaymentMethod)
    )
    amount_sent = fields.Float(required=True)
    status = fields.String(validate=validate.OneOf(PayoutStatus), load_default="PENDING")
    gateway_reference = fields.Str(allow_none=True)
    failure_reason = fields.Str(allow_none=True)

class UpdateGatewayPayoutSchema(Schema):
    status = fields.String(validate=validate.OneOf(PayoutStatus))
    gateway_reference = fields.Str()
    failure_reason = fields.Str()
    amount_sent = fields.Float()
    payment_method = fields.String(validate=validate.OneOf(PaymentMethod))   

class GatewayPayoutResponseSchema(Schema):
    payout_id = fields.Int(dump_only=True)
    ride_id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    
    target_identifier = fields.Str()
    payment_method = fields.Str()          
    amount_sent = fields.Float()
    status = fields.String()
    gateway_reference = fields.Str()
    failure_reason = fields.Str()