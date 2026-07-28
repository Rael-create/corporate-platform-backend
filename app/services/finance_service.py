from datetime import datetime

from app.core.database import db
from app.models.finance import Invoice, Payment, PlatformRevenue
from app.models.corporate import Corporate



def record_invoice(data):
    """Creates a new invoice for a corporate client."""

    # Verify the corporate exists
    corporate = Corporate.query.get(data["corporate_id"])
    if not corporate:
        raise ValueError("Corporate not found.")
    
    new_invoice = Invoice(
        corporate_id=data["corporate_id"],
        invoice_number=f"INV-{datetime.now().year}-{datetime.now().strftime('%H%M%S')}",  # auto-generate number
        total_amount=data["total_amount"],
        due_date=data["due_date"],
        status="UNPAID"
    )

    db.session.add(new_invoice)
    db.session.commit()
    return new_invoice

def record_payment(data):
    """Records a payment, links it to a wallet, marks the invoice as PAID."""

    # find the invoice
    invoice = Invoice.query.get(data["invoice_id"])
    if not invoice:
        raise ValueError("Invoice not founf.")

    #prevent double payment
    if invoice.status == "PAID":
        raise ValueError("This invoice has already been paid.")

    #Create payment record
    new_payment = Payment(
        corporate_id=invoice.corporate_id,
        invoice_id=invoice.invoice_id,
        wallet_id=data.get("wallet_id"),
        amount_paid=data["amount_paid"],
        payment_method=data["payment_method"],
        account_number=data.get("account_number"),
        transaction_reference=data["transaction_reference"]

    )

    #update the invoice status
    invoice.status = "PAID"

    db.session.add(new_payment)
    db.session.commit()

    return new_payment, invoice


def record_platform_revenue(data):
    """Records a specific revenue stream (Commission, VAT, etc.) for the platform."""
    
    # Create the revenue record
    new_revenue = PlatformRevenue(
        corporate_id=data["corporate_id"],
        staff_id=data.get("staff_id"),
        ride_id=data.get("ride_id"),
        invoice_id=data.get("invoice_id"),
        amount=data["amount"],
        revenue_type=data["revenue_type"],
        status="CONFIRMED" # Automatically confirmed when manually recorded by Admin
    )

    db.session.add(new_revenue)
    db.session.commit()

    return new_revenue