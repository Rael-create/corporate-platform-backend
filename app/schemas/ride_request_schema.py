from marshmallow import Schema, fields, validate
from app.models.ride_request import RideStatus 


# 1. Schema for CREATING a ride (Strict validation)
class CreateRideRequestSchema(Schema):
    staff_id = fields.Int(required=True)
    pickup_location = fields.Str(required=True)
    destination = fields.Str(required=True)
    ride_date = fields.DateTime(required=True)
    estimated_fare = fields.Float(required=True)
    reason = fields.Str(allow_none=True)

# 2. Schema for UPDATING a ride (All fields optional)
class UpdateRideRequestSchema(Schema):
    pickup_location = fields.Str()
    destination = fields.Str()
    ride_date = fields.DateTime()
    estimated_fare = fields.Float()
    reason = fields.Str()

# 3. Schema for the RESPONSE (Hides internal logic, formats output)
class RideRequestResponseSchema(Schema):
    ride_id = fields.Int(dump_only=True)
    staff_id = fields.Int(dump_only=True)
    corporate_id = fields.Int(dump_only=True)
    status = fields.Enum(RideStatus, by_value=True, dump_only=True) 
    actual_fare = fields.Float(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    pickup_location = fields.Str()
    destination = fields.Str()
    ride_date = fields.DateTime()
    estimated_fare = fields.Float()
    reason = fields.Str()
    
    vat_rate = fields.Float(dump_only=True)
    commission_rate = fields.Float(dump_only=True)
    vat_amount = fields.Float(dump_only=True)
    commission_amount = fields.Float(dump_only=True)