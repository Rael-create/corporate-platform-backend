from marshmallow import Schema, fields

class UserSchema(Schema):
    user_id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    password = fields.Str(load_only=True, required=True)
    role = fields.Str(required=True)

    corporate_id = fields.Int(required=False, allow_none=True)
    created_at = fields.DateTime(dump_only=True)


class NewUserSchema(Schema):
    user_id = fields.Int(dump_only=True)
    
    username = fields.Str(required=True)
    password = fields.Str(load_only=True, required=True)
    role = fields.Str(required=True)
    corporate_id = fields.Int(required=False, allow_none=True)
    
    # staff fields (optional, only if the user is a staff member)
    first_name = fields.Str(required=False)
    last_name = fields.Str(required=False)
    staff_number = fields.Str(required=False)
    national_id = fields.Str(required=False)
    email = fields.Email(required=False)
    location = fields.Str(required=False)
    address = fields.Str(required=False)
    phone_number = fields.Str(required=False)

    created_at = fields.DateTime(dump_only=True)