from marshmallow import Schema, fields, validate
from app.models.ride_request import RideStatus 


# Schema for CREATING a ride 
class CreateRideRequestSchema(Schema):
    staff_id = fields.Int(required=True)
    pickup_location = fields.Str(required=True)
    destination = fields.Str(required=True)
    base_fare = fields.Float(required=True)
    matatu_identifier = fields.Str(required=True)
    reason = fields.Str(allow_none=True)

#  Schema for UPDATING a ride 
class UpdateRideRequestSchema(Schema):
    pickup_location = fields.Str()
    destination = fields.Str()
    matatu_identifier = fields.Str()
    base_fare = fields.Float()
    status = fields.String(validate=validate.OneOf(RideStatus))
    reason = fields.Str()


# Schema for the RESPONSE 
class RideRequestResponseSchema(Schema):
    ride_id = fields.Int(dump_only=True)
    staff_id = fields.Int(dump_only=True)
    corporate_id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    status = fields.String(dump_only=True) 

    pickup_location = fields.Str()
    destination = fields.Str()
    reason = fields.Str()
    matatu_identifier = fields.Str()
    
    base_fare = fields.Float()
    vat_rate = fields.Float()
    commission_rate = fields.Float()
    vat_amount = fields.Float()
    commission_amount = fields.Float()
    total_fare = fields.Float()
    matatu_payout = fields.Float()