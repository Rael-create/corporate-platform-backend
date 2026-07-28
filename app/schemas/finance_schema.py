from marshmallow import Schema, fields, validate

class InvoiceSchema(Schema):
    """Schema to validate incoming invoice data."""
    corporate_id = fields.Int(required=True, error_messages={"required": "Corporate ID is required."})
    total_amount = fields.Float(required=True, error_messages={"required": "Total amount is required."})
    due_date = fields.DateTime(required=True, format="%Y-%m-%d", error_messages={"required": "Due date is required (Format: YYYY-MM-DD)."})

class PaymentSchema(Schema):
    """Schema to validate incoming payment data."""
    invoice_id = fields.Int(required=True, error_messages={"required": "Invoice ID is required."})
    wallet_id = fields.Int(required=False, allow_none=True, error_messages={"invalid": "Wallet ID must be an integer."})
    amount_paid = fields.Float(required=True, error_messages={"required": "Amount paid is required."})
    payment_method = fields.Str(required=True, validate=validate.OneOf(["PAYBILL", "BANK_TRANSFER"]), error_messages={"required": "Payment method is required."})
    account_number = fields.Str(required=False, allow_none=True) 
    transaction_reference = fields.Str(required=True, error_messages={"required": "Transaction reference (e.g., M-Pesa code) is required."})


class PlatformRevenueSchema(Schema):
    """Schema to validate incoming platform revenue data."""
    corporate_id = fields.Int(required=True, error_messages={"required": "Corporate ID is required."})
    staff_id = fields.Int(required=False, allow_none=True)
    ride_id = fields.Int(required=False, allow_none=True)
    invoice_id = fields.Int(required=False, allow_none=True)
    
    amount = fields.Float(required=True, error_messages={"required": "Revenue amount is required."})
    revenue_type = fields.Str(required=True, validate=validate.OneOf(["COMMISSION", "VAT", "PLATFORM_FEE"]), error_messages={"required": "Revenue type is required."})


# Instantiate the schemas
invoice_schema = InvoiceSchema()
payment_schema = PaymentSchema()
platform_revenue_schema = PlatformRevenueSchema()
