from marshmallow import Schema, fields, validate 
from app.models.finance import InvoiceStatus

INVOICE_PAYMENT_METHODS = [
    "PAYBILL",
    "BANK_TRANSFER"
]

class InvoiceLineItemSchema(Schema):
    ride_id = fields.Int(required=True)
    description = fields.Str(allow_none=True)
    base_fare = fields.Float(required=True)
    vat_amount = fields.Float(required=True)
    commission_amount = fields.Float(required=True)
    total = fields.Float(required=True)


class CreateInvoiceSchema(Schema):
    corporate_id = fields.Int(required=True, error_messages={"required": "Corporate ID is required."})
    due_date = fields.DateTime(required=True, format="%Y-%m-%d", error_messages={"required": "Due date is required (Format: YYYY-MM-DD)."})
    payment_method = fields.Str(required=False,validate=validate.OneOf(INVOICE_PAYMENT_METHODS, error="Invalid payment method selected."),error_messages={"required": "Payment method is required."})
    account_number = fields.Str(required=True, error_messages={"required": "Account number is required."})
    Bank_name = fields.Str(required=True, error_messages={"required": "Bank name is required."})
    Paybill_number = fields.Str(required=False, allow_none=True)
    line_items = fields.List(fields.Nested(InvoiceLineItemSchema), required=True, error_messages={"required": "Line items are required."})

class UpdateInvoiceStatusSchema(Schema):
    status = fields.Str(required=True, validate=validate.OneOf(InvoiceStatus))


class PlatformRevenueSchema(Schema):
    """Schema to validate incoming platform revenue data."""
    corporate_id = fields.Int(required=True, error_messages={"required": "Corporate ID is required."})
    staff_id = fields.Int(required=False, allow_none=True)
    ride_id = fields.Int(required=False, allow_none=True)
    invoice_id = fields.Int(required=False, allow_none=True)
    
    amount = fields.Float(required=True, error_messages={"required": "Revenue amount is required."})
    revenue_type = fields.Str(required=True, validate=validate.OneOf(["COMMISSION", "VAT"]), error_messages={"required": "Revenue type is required."})


# Instantiate the schemas
platform_revenue_schema = PlatformRevenueSchema()
