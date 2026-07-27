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