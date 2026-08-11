from marshmallow import Schema, fields, validate
from app.models.staff import StaffStatus


class UpdateStaffSchema(Schema):
    # Allow updating limits (nullable so they can be removed/uncapped)
    rides_allocated = fields.Int(allow_none=True)
    max_fare_per_ride = fields.Float(allow_none=True)
    
    # Allow changing status
    status = fields.Str(validate=validate.OneOf(StaffStatus))
    
    # Special flag to reset the counter to 0
    reset_rides_counter = fields.Bool(load_only=True, load_default=False)


    # Required for security: Who is making this change?
    updated_by = fields.Int(required=True)

class StaffSchema(Schema):
    """Schema for returning staff data"""
    user_id = fields.Int(required=True)
    staff_id = fields.Int(dump_only=True)
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=150))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=150))
    staff_number = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    national_id = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    email = fields.Email(required=True)
    location = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    address = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    phone_number = fields.Str(required=True, validate=validate.Length(min=1, max=20))
    rides_allocated = fields.Int(allow_none=True)
    rides_used = fields.Int(allow_none=True)
    max_fare_per_ride = fields.Float(allow_none=True)
    status = fields.Str(validate=validate.OneOf(StaffStatus))
    user_id = fields.Int(dump_only=True)
    corporate_id = fields.Int(allow_none=True)
    created_at = fields.DateTime(dump_only=True)


    
class StaffCreateSchema(Schema):
    """Schema for creating a new staff member"""
    user_id = fields.Int(required=True)
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=150))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=150))
    staff_number = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    national_id = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    email = fields.Email(required=True)
    location = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    address = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    phone_number = fields.Str(required=True, validate=validate.Length(min=1, max=20))
    rides_allocated = fields.Int(allow_none=True)
    max_fare_per_ride = fields.Float(allow_none=True)
    status = fields.Str(validate=validate.OneOf(StaffStatus), load_default="ACTIVE")
    corporate_id = fields.Int(allow_none=True)