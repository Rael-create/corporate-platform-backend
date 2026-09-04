from flask import Blueprint, request, jsonify
from app.models.gateway_payouts import GatewayPayout
from app.models.ride_request import RideRequest
from app.services.mpesa_service import stk_push, query_status, send_money
from app.models.mpesa_transaction import MpesaTransaction
from app.core.database import db
from app.schemas.mpesa_schema import STKPushRequestSchema

mpesa_bp = Blueprint("mpesa", __name__, url_prefix="/api/v1/mpesa")


@mpesa_bp.route("/stk-push", methods=["POST"])
def initiate_stk_push():
    """
    Receives phone, amount, and account_reference from the client.
    Triggers the STK Push and saves the transaction record.
    """
    # Validate incoming JSON using Marshmallow schema
    schema = STKPushRequestSchema()
    errors = schema.validate(request.json)
    if errors:
        return jsonify({"errors": errors}), 400

    # Get validated data
    data = schema.load(request.json)
    phone_number = data["phone_number"]
    amount = data["amount"]
    account_reference = data["account_reference"]
    transaction_desc = data.get("transaction_desc", "Payment")

    try:
        # Call the service function
        response = stk_push(phone_number, amount, account_reference, transaction_desc)

        # Save the transaction to the database
        new_tx = MpesaTransaction(
            checkout_request_id=response.get("CheckoutRequestID"),
            merchant_request_id=response.get("MerchantRequestID"),
            phone_number=phone_number,
            amount=amount,
            status="PENDING",
        )
        db.session.add(new_tx)
        db.session.commit()

        return jsonify(response), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@mpesa_bp.route("/stk-status", methods=["GET"])
def query_stk_push_status():
    """
    Checks the status of an STK Push using CheckoutRequestID.
    Updates the transaction record in the database.
    """
    checkout_id = request.args.get("checkout_request_id")
    if not checkout_id:
        return jsonify({"error": "checkout_request_id is required"}), 400

    try:
        # Call the service function
        response = query_status(checkout_id)

        # Update the database with the result
        tx = MpesaTransaction.query.filter_by(checkout_request_id=checkout_id).first()

        if tx:
            result_code = response.get("ResultCode")
            tx.result_code = result_code
            tx.result_desc = response.get("ResultDesc")

            if result_code == "0" or result_code == 0:
                tx.status = "COMPLETED"
            else:
                tx.status = "FAILED"

            db.session.commit()

        return jsonify(response), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@mpesa_bp.route("/callback", methods=["POST"])
def mpesa_callback():
    """
    Receives the final transaction result from Safaricom.
    Updates the transaction status and saves receipt details.
    """
    try:
        callback_data = request.get_json()

        # Safaricom wraps the data in Body.stkCallback
        stk_callback = callback_data.get("Body", {}).get("stkCallback", {})

        if not stk_callback:
            return (
                jsonify({"ResultCode": 1, "ResultDesc": "Invalid callback structure"}),
                400,
            )

        checkout_id = stk_callback.get("CheckoutRequestID")
        result_code = stk_callback.get("ResultCode")
        result_desc = stk_callback.get("ResultDesc")

        # Find the transaction in the database
        tx = MpesaTransaction.query.filter_by(checkout_request_id=checkout_id).first()

        if tx:
            tx.result_code = result_code
            tx.result_desc = result_desc

            if result_code == 0:
                # Success: Update status and extract metadata
                tx.status = "COMPLETED"

                # Extract receipt number and transaction date from CallbackMetadata
                metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])
                for item in metadata:
                    if item.get("Name") == "MpesaReceiptNumber":
                        tx.receipt_number = item.get("Value")
                    elif item.get("Name") == "TransactionDate":
                        # Safaricom sends date as integer like 20260829202145
                        tx.transaction_date = item.get("Value")
            else:
                tx.status = "FAILED"

            db.session.commit()
        else:
            # Transaction not found in our DB (should not happen)
            return (
                jsonify({"ResultCode": 1, "ResultDesc": "Transaction not found"}),
                200,
            )

        # Always return success to M-Pesa (they require ResultCode 0)
        return jsonify({"ResultCode": 0, "ResultDesc": "Success"}), 200

    except Exception as e:
        db.session.rollback()
        # Even if we error, M-Pesa expects a 200 with ResultCode 0 to stop retries.
        # Log the error, but return success to M-Pesa.
        print(f"Callback error: {e}")  # Replace with proper logging
        return jsonify({"ResultCode": 0, "ResultDesc": "Success"}), 200


@mpesa_bp.route("/b2c/send", methods=["POST"])
def test_b2c_send():
    """
    Test B2C send money.
    Expected JSON:
    {
        "phone_number": "254708374149",
        "amount": 10,
        "transaction_desc": "Test payment",
        "ride_id": 123   # 👈 Must be a valid ride ID
    }
    """
    try:
        data = request.json

        phone_number = data.get("phone_number")
        amount = data.get("amount")
        transaction_desc = data.get("transaction_desc", "Test B2C payment")
        ride_id = data.get("ride_id")

        if not phone_number or amount is None:
            return jsonify({"error": "phone_number and amount required"}), 400

        if not ride_id:
            return jsonify({"error": "ride_id is required"}), 400

        # Verify the ride exists
        ride = RideRequest.query.get(ride_id)
        if not ride:
            return jsonify({"error": f"Ride with ID {ride_id} not found"}), 404

        # Call the B2C function
        response = send_money(
            phone_number=phone_number, amount=amount, transaction_desc=transaction_desc
        )

        # Save to GatewayPayout with the ride_id
        payout = GatewayPayout(
            ride_id=ride_id,
            target_identifier=phone_number,
            amount_sent=amount,
            payment_method="SEND_MONEY",
            status="PENDING",
            gateway_reference=response.get("ConversationID"),
        )
        db.session.add(payout)
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "B2C request sent successfully",
                    "response": response,
                    "payout_id": payout.payout_id,
                    "ride_id": ride_id,
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@mpesa_bp.route("/b2c/result", methods=["POST"])
def b2c_result():
    """B2C Result URL – called when platform pays a driver."""
    try:
        data = request.get_json()
        result = data.get("Result", {})

        conversation_id = result.get("ConversationID")
        result_code = result.get("ResultCode")
        result_desc = result.get("ResultDesc")

        print(
            f"✅ B2C Callback received: {conversation_id} -> ResultCode: {result_code}"
        )

        # Update GatewayPayout status
        payout = GatewayPayout.query.filter_by(
            gateway_reference=conversation_id
        ).first()
        if payout:
            if result_code == 0:
                payout.status = "SUCCESS"
            else:
                payout.status = "FAILED"
                payout.failure_reason = result_desc
            db.session.commit()

        return jsonify({"ResultCode": 0, "ResultDesc": "Success"}), 200
    except Exception as e:
        print(f"❌ B2C Result error: {e}")
        return jsonify({"ResultCode": 0, "ResultDesc": "Success"}), 200


@mpesa_bp.route("/b2c/timeout", methods=["POST"])
def b2c_timeout():
    """B2C Timeout URL – called if M-Pesa doesn't get a response."""
    print("⏰ B2C Timeout received")
    try:
        data = request.get_json()
        conversation_id = data.get("ConversationID")

        # Update GatewayPayout to FAILED
        payout = GatewayPayout.query.filter_by(
            gateway_reference=conversation_id
        ).first()
        if payout:
            payout.status = "FAILED"
            payout.failure_reason = (
                "Transaction timeout – callback not received from M-Pesa"
            )
            db.session.commit()
            print(f"⏰ Payout {payout.payout_id} marked as FAILED due to timeout")

        return jsonify({"ResultCode": 0, "ResultDesc": "Success"}), 200
    except Exception as e:
        print(f"❌ B2C Timeout error: {e}")
        return jsonify({"ResultCode": 0, "ResultDesc": "Success"}), 200
