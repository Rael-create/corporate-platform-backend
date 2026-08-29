from marshmallow import Schema, fields, validate, post_load
from app.models.mpesa_transaction import TransactionStatus

#  REQUEST SCHEMA (for incoming STK Push from your frontend)
class STKPushRequestSchema(Schema):
    """
    Validates the JSON payload when your frontend calls /api/v1/mpesa/stk-push.
    Expected format:
    {
        "phone_number": "254708374149",
        "amount": 1,
        "account_reference": "TEST001",
        "transaction_desc": "Payment for order"
    }
    """
    phone_number = fields.Str(
        required=True,
        validate=validate.Regexp(
            r'^254[0-9]{9}$',
            error="Phone number must be in format 254XXXXXXXXX (e.g., 254708374149)"
        )
    )
    amount = fields.Float(
        required=True,
        validate=validate.Range(min=1, error="Amount must be at least 1")
    )
    account_reference = fields.Str(
        required=True,
        validate=validate.Length(max=12, error="Account reference must not exceed 12 characters")
    )
    transaction_desc = fields.Str(
        required=False,
        load_default="Payment",
        validate=validate.Length(max=100)
    )

#  RESPONSE SCHEMA (for M-Pesa STK Push response)
class STKPushResponseSchema(Schema):
    """
    Schema for the response returned by Safaricom after initiating STK Push.
    """
    MerchantRequestID = fields.Str()
    CheckoutRequestID = fields.Str()
    ResponseCode = fields.Str()
    ResponseDescription = fields.Str()
    CustomerMessage = fields.Str()


#  CALLBACK SCHEMA (for the webhook from M-Pesa)
class CallbackMetadataItemSchema(Schema):
    """
    Each item inside the CallbackMetadata array.
    e.g., {"Name": "MpesaReceiptNumber", "Value": "LGR123456"}
    """
    Name = fields.Str()
    Value = fields.Raw()  


class CallbackMetadataSchema(Schema):
    """
    The full metadata object containing the list of items.
    """
    Item = fields.List(fields.Nested(CallbackMetadataItemSchema))


class StkCallbackSchema(Schema):
    """
    The inner stkCallback object from Safaricom.
    """
    MerchantRequestID = fields.Str()
    CheckoutRequestID = fields.Str()
    ResultCode = fields.Int()
    ResultDesc = fields.Str()
    CallbackMetadata = fields.Nested(CallbackMetadataSchema, allow_none=True)


class MpesaCallbackBodySchema(Schema):
    """
    The 'Body' object inside the callback payload.
    """
    stkCallback = fields.Nested(StkCallbackSchema)


class MpesaCallbackSchema(Schema):
    """
    The FULL callback payload sent by Safaricom to your webhook.
    Example structure:
    {
        "Body": {
            "stkCallback": {
                "MerchantRequestID": "...",
                "CheckoutRequestID": "...",
                "ResultCode": 0,
                "ResultDesc": "Success",
                "CallbackMetadata": {
                    "Item": [
                        {"Name": "Amount", "Value": 1},
                        {"Name": "MpesaReceiptNumber", "Value": "LGR123456"},
                        ...
                    ]
                }
            }
        }
    }
    """
    Body = fields.Nested(MpesaCallbackBodySchema)


#  STATUS QUERY SCHEMA (for checking transaction status)
class STKQueryRequestSchema(Schema):
    """
    Validates the query params for /api/v1/mpesa/stk-status.
    Expected: ?checkout_request_id=ws_CO_...
    """
    checkout_request_id = fields.Str(required=True)