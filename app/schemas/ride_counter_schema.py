from marshmallow import Schema, fields


class RideCounterSchema(Schema):
    counter_id = fields.Int(dump_only=True)

    staff_id = fields.Int(required=True)

    cumulative_no_of_rides = fields.Int(dump_only=True)

    cumulative_amount = fields.Float(dump_only=True)

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)