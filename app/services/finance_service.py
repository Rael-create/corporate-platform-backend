from datetime import datetime, timedelta

from app.core.database import db
from app.models.finance import Invoice, InvoiceLineItem, PlatformRevenue
from app.models.corporate import Corporate
from app.models.ride_request import RideRequest, RideStatus
from app.models.users import User
from app.models.wallet import Wallet
from app.services.wallet_service import top_up_wallet


def generate_invoice_number():
    """Generate a unique invoice number, e.g., INV-2026-08-001"""
    year = datetime.now().year
    month = datetime.now().strftime("%m")
    # Count invoices this month to get sequence
    count = Invoice.query.filter(
        Invoice.invoice_number.like(f"INV-{year}-{month}-%")
    ).count()
    seq = count + 1
    return f"INV-{year}-{month}-{seq:03d}"


def create_invoice(data):

    # Calculate total from line items
    payment_breakdown = data["inv_summary"]["Amount"]

    invoice = Invoice(
        corporate_id=data["corporate_id"],
        invoice_number=generate_invoice_number(),
        total_amount=payment_breakdown[3],
        base_fare=payment_breakdown[0],
        vat=payment_breakdown[2],
        commision=payment_breakdown[1],
        due_date=data["due_date"],
        status="UNPAID",
    )
    db.session.add(invoice)
    db.session.flush()  # get invoice_id

    # Add line items

    line_items = [
        InvoiceLineItem(
            invoice_id=invoice.invoice_id,
            ride_id=ride.ride_id,
            description=f"{ride.pickup_location} -> {ride.destination}",
            base_fare=ride.base_fare or 0,
            vat_amount=ride.vat_amount or 0,
            commission_amount=ride.commission_amount or 0,
            total=ride.total_fare or 0,
        )
        for ride in data["rides"]
    ]

    db.session.add_all(line_items)

    db.session.commit()
    return invoice


def get_invoices_by_corporate(corporate_id):
    return (
        Invoice.query.filter_by(corporate_id=corporate_id)
        .order_by(Invoice.created_at.desc())
        .all()
    )


def get_invoice(invoice_id, corporate_id=None):
    query = Invoice.query.options(db.joinedload(Invoice.line_items))
    query = Invoice.query.filter_by(invoice_id=invoice_id)
    if corporate_id:
        query = query.filter_by(corporate_id=corporate_id)
    invoice = query.first()
    if not invoice:
        raise ValueError("Invoice not found.")
    return invoice


def update_invoice_status(invoice_id, status, corporate_id=None):
    invoice = get_invoice(invoice_id, corporate_id)
    if status not in ["UNPAID", "PAID", "OVERDUE"]:
        raise ValueError("Invalid status.")
    invoice.status = status
    db.session.commit()
    return invoice


def generate_invoice_from_rides(corporate_id, start_date, end_date, due_date):
    """
    Automatically generate an invoice for a given period by aggregating completed rides.
    This is useful for monthly billing.
    """
    corporate = Corporate.query.get(corporate_id)
    if not corporate:
        raise ValueError("Corporate not found.")
    # Fetch completed rides in the period
    rides = RideRequest.query.filter(
        RideRequest.corporate_id == corporate_id,
        RideRequest.status == "COMPLETED",
        RideRequest.created_at >= start_date,
        RideRequest.created_at <= end_date,
    ).all()

    if not rides:
        raise ValueError("No completed rides found for this period.")

    inv_summary = {
        "Description": ["Base fare", "Commission", "VAT", "Total Fare"],
        "Amount": [
            sum(r.base_fare for r in rides),
            sum(r.commission_amount for r in rides),
            sum(r.vat_amount for r in rides),
            sum(r.total_fare for r in rides),
        ],
    }

    # Create invoice
    invoice_data = {
        "corporate_id": corporate_id,
        "due_date": due_date,
        "inv_summary": inv_summary,
        "rides": rides,
    }
    invoice = create_invoice(invoice_data)

    return invoice


def record_payment(data):
    # Fetch invoice
    invoice = Invoice.query.get(data.get("invoice_id"))
    if not invoice:
        raise ValueError("Invoice not found.")

    # Prevent double payment
    if invoice.status == "PAID":
        raise ValueError("This invoice has already been paid.")

    # Validate amount
    amount_paid = float(data["amount_paid"])
    if amount_paid != invoice.total_amount:
        raise ValueError(
            f"Payment amount {amount_paid} does not match invoice total {invoice.total_amount}."
        )

    # Update invoice with payment details (optional, can be provided at payment time)
    invoice.payment_method = data.get("payment_method", invoice.payment_method)
    invoice.account_number = data.get("account_number", invoice.account_number)
    invoice.transaction_reference = data.get(
            "transaction_reference", invoice.transaction_reference
        )
    if invoice.payment_method == "BANK_TRANSFER":
        invoice.Bank_name = data.get("Bank_name", invoice.Bank_name)
    else:
        invoice.Paybill_number = data.get("Paybill_number", invoice.Paybill_number)

    # Find the platform master wallet
    master_wallet = Wallet.query.filter_by(
        corporate_id=None, wallet_type="PLATFORM_FUNDED"
    ).first()
    if not master_wallet:
        raise ValueError("Platform master wallet not found. Please create one.")

    # Credit the master wallet (platform revenue)
    top_up_wallet(
        wallet_id=master_wallet.wallet_id,
        amount=amount_paid,
        initial_top_up=False,
        type="INVOICE_PAYMENT",
    )

    # Mark associated PlatformRevenue records as CONFIRMED
    line_items = InvoiceLineItem.query.filter_by(invoice_id=invoice.invoice_id).all()
    ride_ids = [item.ride_id for item in line_items]  #  Use the foreign key directly
    if ride_ids:
        PlatformRevenue.query.filter(PlatformRevenue.ride_id.in_(ride_ids)).update(
            {"status": "CONFIRMED"}, synchronize_session=False
        )

    # Update invoice status and timestamp
    invoice.status = "PENDING"
    # if invoice.payment_method == "BANK_TRANSFER":
    #     invoice.status = "PENDING"
    # else:
    #     invoice.status = "PAID"
    #     invoice.paid_at = datetime.now()

    db.session.commit()

    return invoice

# finance_service.py



def send_invoice_reminder(invoice_id):
    """
    Send an email reminder to all corporate admins of the invoice's corporate.
    Returns a message string on success, raises ValueError on failure.
    """
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        raise ValueError("Invoice not found.")

    if invoice.status != "UNPAID":
        raise ValueError("Reminders can only be sent for UNPAID invoices.")

    # Fetch corporate admins (users with role 'CORPORATE_ADMIN' and matching corporate_id)
    admins = User.query.filter_by(
        corporate_id=invoice.corporate_id,
        role="CORPORATE_ADMIN"
    ).all()

    if not admins:
        raise ValueError("No corporate admins found for this corporate.")

    # TODO: Implement actual email sending logic here.
    # Example: send_email(
    #     subject=f"Invoice {invoice.invoice_number} Reminder",
    #     recipients=[admin.email for admin in admins],
    #     body=f"Dear team, this is a reminder that invoice {invoice.invoice_number} is still unpaid..."
    # )

    # Return a success message (can be used by the endpoint)
    return f"Reminder sent for invoice {invoice.invoice_number}"


def confirm_invoice_payment(invoice_id, transaction_reference=None):
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        raise ValueError("Invoice not found.")

    if invoice.status != "PENDING":
        raise ValueError("Only PENDING invoices can be confirmed.")

    invoice.status = "PAID"
    invoice.paid_at = datetime.now()
    if transaction_reference:
        invoice.transaction_reference = transaction_reference
    db.session.commit()

    return invoice