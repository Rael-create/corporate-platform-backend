from app.core.database import db
from datetime import datetime, timedelta

InvoiceStatus = [
    "UNPAID",
    "PAID",
    "OVERDUE"
]

RevenueType = [
    "COMMISSION",
    "VAT",
    "PLATFORM_FEE"
]

RevenueStatus = [
    "PENDING",
    "CONFIRMED"
]

class Invoice(db.Model):
    __tablename__ = "invoice" 

    invoice_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    corporate_id = db.Column(db.Integer, db.ForeignKey('corporates.corporate_id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.Enum(*InvoiceStatus), default="UNPAID", nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    corporate = db.relationship("Corporate", backref="invoices")
    payments = db.relationship("Payment", backref="invoice", lazy=True)
    revenues = db.relationship("PlatformRevenue", backref="invoice", lazy=True)

    def __repr__(self):
        return f"<Invoice {self.invoice_number} - {self.status}>"


class Payment(db.Model):
    __tablename__ = "payment" 

    payment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    corporate_id = db.Column(db.Integer, db.ForeignKey('corporates.corporate_id'), nullable=False)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallet.wallet_id'), nullable=True) 
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.invoice_id'), nullable=False) 
    
    amount_paid = db.Column(db.Float, nullable=False)

    payment_method = db.Column(db.String(50), nullable=False)  
    account_number = db.Column(db.String(100), nullable=True)  
    transaction_reference = db.Column(db.String(100), unique=True, nullable=False) 
    paid_at = db.Column(db.DateTime, default=datetime.now)

    corporate = db.relationship("Corporate", backref="payments")
    wallet = db.relationship("Wallet", backref="payments")  

    def __repr__(self):
        return f"<Payment {self.transaction_reference} - {self.amount_paid}>"


class PlatformRevenue(db.Model):
    __tablename__ = "platform_revenue"

    revenue_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id'), nullable=True)
    corporate_id = db.Column(db.Integer, db.ForeignKey('corporates.corporate_id'), nullable=False)
    ride_id = db.Column(db.Integer, db.ForeignKey('ride_requests.ride_id'), nullable=True) 
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.invoice_id'), nullable=True) 
    
    amount = db.Column(db.Float, nullable=False) 
    
    revenue_type = db.Column(db.Enum(*RevenueType), nullable=False)
    status = db.Column(db.Enum(*RevenueStatus), default="PENDING", nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    corporate = db.relationship("Corporate", backref="platform_revenues")
    staff = db.relationship("Staff", backref="platform_revenues")
    ride = db.relationship("RideRequest", backref="platform_revenues")

    def __repr__(self):
        return f"<PlatformRevenue {self.revenue_type} - {self.amount}>"