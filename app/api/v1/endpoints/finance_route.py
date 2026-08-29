from app.models.platform_settings import PlatformSettings
import xhtml2pdf.pisa as pisa
import io
import logging
from flask import (
    Blueprint,
    request,
    jsonify,
    render_template,
    make_response,
    current_app,
)
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.decorators import role_required
from app.models.users import User
from app.models.finance import Invoice
from datetime import datetime
from app.schemas.finance_schema import (
    CreateInvoiceSchema,
    InvoiceLineItemSchema,
    UpdateInvoiceStatusSchema,
    payment_schema,
    decline_invoice_schema,
)
from app.services.finance_service import (
    create_invoice,
    get_invoices_by_corporate,
    get_invoice,
    update_invoice_status,
    generate_invoice_from_rides,
    record_payment,
    send_invoice_reminder,
    confirm_invoice_payment,
    reverse_invoice_payment,
)

finance_bp = Blueprint("finance", __name__, url_prefix="/api/v1/finance")

create_schema = CreateInvoiceSchema()
update_status_schema = UpdateInvoiceStatusSchema()


@finance_bp.route("/", methods=["GET"])
@jwt_required()
def list_invoices():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    if user.role == "SUPER_ADMIN":
        corporate_id = request.args.get("corporate_id")
        if corporate_id:
            invoices = get_invoices_by_corporate(int(corporate_id))
        else:
            invoices = Invoice.query.order_by(Invoice.created_at.desc()).all()
    else:
        if not user.corporate_id:
            return jsonify({"message": "User has no corporate assigned."}), 400
        invoices = get_invoices_by_corporate(user.corporate_id)

    result = []
    for inv in invoices:
        result.append(
            {
                "invoice_id": inv.invoice_id,
                "invoice_number": inv.invoice_number,
                "corporate_id": inv.corporate_id,
                "corporate_name": inv.corporate.corporate_name,
                "total_amount": inv.total_amount,
                "status": inv.status,
                "due_date": inv.due_date.isoformat(),
                "created_at": inv.created_at.isoformat(),
                "transaction_reference": inv.transaction_reference,
            }
        )
    return jsonify(result), 200


@finance_bp.route("/<int:invoice_id>", methods=["GET"])
@jwt_required()
def fetch_invoice(invoice_id):
    """Get a single invoice with its line items."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    if user.role == "SUPER_ADMIN":
        invoice = get_invoice(invoice_id)
    else:
        if not user.corporate_id:
            return jsonify({"message": "User has no corporate assigned."}), 400
        invoice = get_invoice(invoice_id, user.corporate_id)

    #  Fetch fresh settings
    settings = PlatformSettings.get_settings()

    line_items = []
    for item in invoice.line_items:
        line_items.append(
            {
                "line_item_id": item.line_item_id,
                "ride_id": item.ride_id,
                "description": item.description,
                "base_fare": item.base_fare,
                "vat_amount": item.vat_amount,
                "commission_amount": item.commission_amount,
                "total": item.total,
            }
        )

    return (
        jsonify(
            {
                "invoice_id": invoice.invoice_id,
                "invoice_number": invoice.invoice_number,
                "corporate_id": invoice.corporate_id,
                "corporate_name": invoice.corporate.corporate_name,
                "corporate_address": invoice.corporate.address,
                "total_amount": invoice.total_amount,
                "status": invoice.status,
                "due_date": invoice.due_date.isoformat(),
                "created_at": invoice.created_at.isoformat(),
                "line_items": line_items,
                "payment_details": {
                    "mpesa_paybill": settings.mpesa_paybill,
                    "mpesa_account_prefix": settings.mpesa_account_prefix,
                    "bank_name": settings.bank_name,
                    "bank_account_name": settings.bank_account_name,
                    "bank_account_number": settings.bank_account_number,
                    "bank_branch": settings.bank_branch,
                    "kra_pin": settings.kra_pin,
                    "company_name": settings.company_name,
                    "company_address": settings.company_address,
                },
                "payment_method": invoice.payment_method,
                "account_number": invoice.account_number,
                "Bank_name": invoice.Bank_name,
                "Paybill_number": invoice.Paybill_number,
                "transaction_reference": invoice.transaction_reference,
            }
        ),
        200,
    )


@finance_bp.route("/", methods=["POST"])
@jwt_required()
@role_required("SUPER_ADMIN")
def create_invoice_endpoint():
    """Create a new invoice with line items."""
    data = request.get_json()
    errors = create_schema.validate(data)
    if errors:
        return jsonify({"errors": errors}), 400

    try:
        invoice = create_invoice(data)
        return (
            jsonify(
                {
                    "message": "Invoice created successfully",
                    "invoice_id": invoice.invoice_id,
                    "invoice_number": invoice.invoice_number,
                }
            ),
            201,
        )
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": "Failed to create invoice", "error": str(e)}), 500


@finance_bp.route("/<int:invoice_id>/status", methods=["PATCH"])
@jwt_required()
@role_required("SUPER_ADMIN")
def update_invoice_status_endpoint(invoice_id):
    """Update invoice status."""
    data = request.get_json()
    errors = update_status_schema.validate(data)
    if errors:
        return jsonify({"errors": errors}), 400

    try:
        invoice = update_invoice_status(invoice_id, data["status"])
        return (
            jsonify(
                {
                    "message": f"Invoice {invoice.invoice_number} status updated to {invoice.status}",
                    "status": invoice.status,
                }
            ),
            200,
        )
    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        return jsonify({"message": "Failed to update invoice", "error": str(e)}), 500


@finance_bp.route("/generate", methods=["POST"])
@jwt_required()
@role_required("SUPER_ADMIN")
def generate_invoice_from_rides_endpoint():
    """
    Auto-generate an invoice from completed rides in a date range.
    Body: { corporate_id, start_date, end_date, due_date }
    """
    data = request.get_json()
    required = ["corporate_id", "start_date", "end_date", "due_date"]
    if not all(k in data for k in required):
        return (
            jsonify(
                {
                    "message": "Missing required fields: corporate_id, start_date, end_date, due_date"
                }
            ),
            400,
        )

    try:
        start = datetime.fromisoformat(data["start_date"])
        end = datetime.fromisoformat(data["end_date"])
        due = datetime.fromisoformat(data["due_date"])
        invoice = generate_invoice_from_rides(data["corporate_id"], start, end, due)
        return (
            jsonify(
                {
                    "message": "Invoice generated successfully",
                    "invoice_id": invoice.invoice_id,
                    "invoice_number": invoice.invoice_number,
                }
            ),
            201,
        )
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": "Failed to generate invoice", "error": str(e)}), 500


@finance_bp.route("/<int:invoice_id>/pdf", methods=["GET"])
@jwt_required()
def generate_invoice_pdf(invoice_id):
    try:
        user = User.query.get(get_jwt_identity())
        if not user:
            return jsonify({"message": "User not found"}), 404

        from sqlalchemy.orm import joinedload

        query = Invoice.query.options(joinedload(Invoice.line_items))

        if user.role == "SUPER_ADMIN":
            invoice = query.filter_by(invoice_id=invoice_id).first()
        else:
            invoice = query.filter_by(
                invoice_id=invoice_id, corporate_id=user.corporate_id
            ).first()

        if not invoice:
            return jsonify({"message": "Invoice not found"}), 404

        #  Fetch fresh settings for PDF
        settings = PlatformSettings.get_settings()

        corporate_address = invoice.corporate.address if invoice.corporate else None
        data = {
            "invoice": invoice,
            "corporate_name": invoice.corporate.corporate_name,
            "corporate_address": corporate_address,
            "subtotal": sum(item.base_fare for item in invoice.line_items),
            "total_vat": sum(item.vat_amount for item in invoice.line_items),
            "total_commission": sum(
                item.commission_amount for item in invoice.line_items
            ),
            "currency": "KES",
            "settings": settings,  #  pass to template
        }

        html_content = render_template("invoice_pdf.html", **data)

        pdf_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)

        if pisa_status.err:
            logging.error(f"PDF generation error: {pisa_status.err}")
            return jsonify({"message": "PDF generation failed"}), 500

        pdf_buffer.seek(0)
        response = make_response(pdf_buffer.getvalue())
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = (
            f"attachment; filename=invoice_{invoice.invoice_number}.pdf"
        )
        return response

    except Exception as e:
        logging.exception("PDF generation crashed")
        return jsonify({"message": f"PDF generation failed: {str(e)}"}), 500


# PAYMENT
@finance_bp.route("/payments", methods=["POST"])
@jwt_required()
@role_required("SUPER_ADMIN", "CORPORATE_ADMIN")
def record_invoice_payment():
    """Record a payment for an invoice."""
    data = request.get_json()

    # Validate input
    errors = payment_schema.validate(data)
    if errors:
        return jsonify({"errors": errors}), 400

    try:
        # Call the service – returns the updated invoice
        updated_invoice = record_payment(data)

        return (
            jsonify(
                {
                    "message": "Payment recorded successfully",
                    "invoice_id": updated_invoice.invoice_id,
                    "status": updated_invoice.status,
                    "transaction_reference": updated_invoice.transaction_reference,
                    "payment_method": updated_invoice.payment_method,
                    "account_number": updated_invoice.account_number,
                    "bank_name": updated_invoice.Bank_name,
                    "paybill_number": updated_invoice.Paybill_number,
                    "paid_at": (
                        updated_invoice.paid_at.isoformat()
                        if updated_invoice.paid_at
                        else None
                    ),
                }
            ),
            201,
        )

    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": f"Failed to record payment: {str(e)}"}), 500


@finance_bp.route("/<int:invoice_id>/remind", methods=["POST"])
@jwt_required()
@role_required("SUPER_ADMIN")
def send_invoice_reminder_endpoint(invoice_id):
    try:
        message = send_invoice_reminder(invoice_id)
        return jsonify({"message": message}), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": f"Failed to send reminder: {str(e)}"}), 500


@finance_bp.route("/<int:invoice_id>/confirm", methods=["POST"])
@jwt_required()
@role_required("SUPER_ADMIN")
def confirm_invoice_payment_endpoint(invoice_id):
    data = request.get_json() or {}
    transaction_reference = data.get("transaction_reference")
    try:
        invoice = confirm_invoice_payment(invoice_id)
        return (
            jsonify(
                {
                    "message": f"Invoice {invoice.invoice_number} confirmed as PAID.",
                    "invoice_id": invoice.invoice_id,
                    "status": invoice.status,
                    "paid_at": invoice.paid_at.isoformat() if invoice.paid_at else None,
                    "transaction_reference": invoice.transaction_reference,

                }
            ),
            200,
        )
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": f"Failed to confirm payment: {str(e)}"}), 500


@finance_bp.route("/<int:invoice_id>/reverse", methods=["POST"])
@jwt_required()
@role_required("SUPER_ADMIN")
def reverse_invoice_endpoint(invoice_id):

    data = request.get_json()
    
    # Validate the request body
    errors = decline_invoice_schema.validate(data)
    if errors:
        return jsonify({"errors": errors}), 400

    try:
        # Get the current user for auditing
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        # Call the service function
        invoice = reverse_invoice_payment(
            invoice_id=invoice_id,
            decline_reason=data["decline_reason"],
            reversed_by=user.user_id if user else None
        )

        return jsonify({
            "message": f"Invoice {invoice.invoice_number} reversed successfully.",
            "invoice_id": invoice.invoice_id,
            "status": invoice.status,
            "decline_reason": invoice.decline_reason,
        }), 200

    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": f"Failed to reverse payment: {str(e)}"}), 500