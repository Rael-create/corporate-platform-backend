from marshmallow import Schema, fields, validate
from app.models.staff import StaffStatus

class UserSchema(Schema):
    user_id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    password = fields.Str(load_only=True, required=True)
    role = fields.Str(required=True)

    corporate_id = fields.Int(required=False, allow_none=True)
    created_at = fields.DateTime(dump_only=True)


class NewUserSchema(Schema):
    user_id = fields.Int(dump_only=True)
    
    username     = fields.Str(required=True)
    password     = fields.Str(load_only=True, required=True)
    role         = fields.Str(required=True)
    corporate_id = fields.Int(required=False, allow_none=True)
    
    # staff fields (optional, only if the user is a staff member)
    #staff_id     = fields.Str(required=True)
    first_name   = fields.Str(required=True)
    last_name    = fields.Str(required=True)
    staff_number = fields.Str(required=True)
    national_id  = fields.Str(required=True)
    email        = fields.Email(required=True)
    location     = fields.Str(required=True)
    address      = fields.Str(required=True)
    phone_number = fields.Str(required=True)

    rides_allocated = fields.Int(required=False)
    rides_used = fields.Int(required=False)
    max_fare_per_ride = fields.Int(required=False)
    status = fields.Str(
    load_default="ACTIVE",
    validate=validate.OneOf(
    StaffStatus,
    error="status must be ACTIVE or INACTIVE"
    ))
    
    created_at = fields.DateTime(dump_only=True)