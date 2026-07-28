from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.utils.decorators import role_required
from app.schemas.finance_schema import payment_schema, invoice_schema, platform_revenue_schema
from app.services.finance_service import record_payment, record_invoice, record_platform_revenue

finance_bp = Blueprint(
    "finance",
    __name__,
    url_prefix="/api/v1/finance"
)

# --- CREATE INVOICE ENDPOINT ---
@finance_bp.route("/invoices", methods=["POST"])
@jwt_required()
@role_required("SUPER_ADMIN", "CORPORATE_ADMIN")
def create_invoice():
    data = request.get_json()
    
    # Validate the incoming data
    errors = invoice_schema.validate(data)
    if errors:
        return jsonify(errors), 400
        
    try:
        # Call the service to create the invoice
        new_invoice = record_invoice(data)
        
        # Return the created invoice
        return jsonify({
            "message": "Invoice created successfully",
            "invoice": {
                "invoice_id": new_invoice.invoice_id,
                "invoice_number": new_invoice.invoice_number,
                "corporate_id": new_invoice.corporate_id,
                "total_amount": new_invoice.total_amount,
                "status": new_invoice.status,
                "due_date": new_invoice.due_date.isoformat()
            }
        }), 201
        
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": "Failed to create invoice", "error": str(e)}), 500
    

# ---  RECORD PAYMENT ENDPOINT ---
@finance_bp.route("/payments", methods=["POST"])
@jwt_required()
@role_required("SUPER_ADMIN", "CORPORATE_ADMIN")
def record_invoice_payment():
    """Endpoint to record a payment for an invoice and link it to a wallet."""
    data = request.get_json()
    
    # Validate the incoming data
    errors = payment_schema.validate(data)
    if errors:
        return jsonify(errors), 400
        
    try:
        # Call the service to process the payment
        new_payment, updated_invoice = record_payment(data)
        
        # Return the success response
        return jsonify({
            "message": "Payment recorded successfully",
            "payment": {
                "payment_id": new_payment.payment_id,
                "wallet_id": new_payment.wallet_id,       # Confirms wallet tracking
                "transaction_reference": new_payment.transaction_reference,
                "amount_paid": new_payment.amount_paid,
                "payment_method": new_payment.payment_method,
                "account_number": new_payment.account_number
            },
            "updated_invoice_status": updated_invoice.status
        }), 201
        
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": "Failed to record payment", "error": str(e)}), 500



# ---  RECORD PLATFORM REVENUE ENDPOINT ---
@finance_bp.route("/revenues", methods=["POST"])
@jwt_required()
@role_required("SUPER_ADMIN") # Only Super Admin can record platform profits
def record_revenue_endpoint():
    data = request.get_json()
    
    # 1. Validate data
    errors = platform_revenue_schema.validate(data)
    if errors:
        return jsonify(errors), 400
        
    try:
        # 2. Call your service
        new_revenue = record_platform_revenue(data)
        
        # 3. Return success
        return jsonify({
            "message": "Platform revenue recorded successfully",
            "revenue": {
                "revenue_id": new_revenue.revenue_id,
                "corporate_id": new_revenue.corporate_id,
                "amount": new_revenue.amount,
                "revenue_type": new_revenue.revenue_type,
                "status": new_revenue.status
            }
        }), 201
        
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": "Failed to record revenue", "error": str(e)}), 500
