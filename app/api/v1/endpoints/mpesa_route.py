from flask import Blueprint, request, jsonify
from app.services.mpesa_service import stk_push, query_status
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
            status="PENDING"
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
        tx = MpesaTransaction.query.filter_by(
            checkout_request_id=checkout_id
        ).first()
        
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
            return jsonify({"ResultCode": 1, "ResultDesc": "Invalid callback structure"}), 400

        checkout_id = stk_callback.get("CheckoutRequestID")
        result_code = stk_callback.get("ResultCode")
        result_desc = stk_callback.get("ResultDesc")

        # Find the transaction in the database
        tx = MpesaTransaction.query.filter_by(
            checkout_request_id=checkout_id
        ).first()

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
            return jsonify({"ResultCode": 1, "ResultDesc": "Transaction not found"}), 200

        # Always return success to M-Pesa (they require ResultCode 0)
        return jsonify({"ResultCode": 0, "ResultDesc": "Success"}), 200
    
    except Exception as e:
        db.session.rollback()
        # Even if we error, M-Pesa expects a 200 with ResultCode 0 to stop retries.
        # Log the error, but return success to M-Pesa.
        print(f"Callback error: {e}")  # Replace with proper logging
        return jsonify({"ResultCode": 0, "ResultDesc": "Success"}), 200