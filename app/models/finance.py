from app.core.database import db
from datetime import datetime, timedelta

InvoiceStatus = [
    "UNPAID",
    "PAID",
    "PENDING",
    "OVERDUE"
]

RevenueType = [
    "COMMISSION",
    "VAT"
    ]

RevenueStatus = [
    "PENDING", 
    "CONFIRMED" #-- paid 
]

class Invoice(db.Model):
    __tablename__ = "invoice" 

    invoice_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    corporate_id = db.Column(db.Integer, db.ForeignKey('corporates.corporate_id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    base_fare = db.Column(db.Float, nullable=False)
    commision = db.Column(db.Float, nullable=False)
    vat = db.Column(db.Float, nullable=False)
    status = db.Column(db.Enum(*InvoiceStatus), default="UNPAID", nullable=False)

    payment_method = db.Column(db.String(50), nullable=True)  
    account_number = db.Column(db.String(100), nullable=True)  
    Bank_name = db.Column(db.String(100), nullable=True)
    Paybill_number = db.Column(db.String(100), nullable=True)
    transaction_reference = db.Column(db.String(100), unique=True, nullable=True) 

    paid_at = db.Column(db.DateTime, default=datetime.now)
    due_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


    # Relationships
    corporate = db.relationship("Corporate", backref="invoices")
    line_items = db.relationship("InvoiceLineItem", backref="invoice", lazy=True, cascade="all, delete-orphan")
    revenues = db.relationship("PlatformRevenue", backref="invoice", lazy=True)

    def __repr__(self):
        return f"<Invoice {self.invoice_number} - {self.status}>"

class InvoiceLineItem(db.Model):
    __tablename__ = "invoice_line_items"

    line_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.invoice_id'), nullable=False)
    ride_id = db.Column(db.Integer, db.ForeignKey('ride_requests.ride_id'), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    base_fare = db.Column(db.Float, nullable=False)
    vat_amount = db.Column(db.Float, nullable=False)
    commission_amount = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)

    ride = db.relationship("RideRequest", backref="invoice_line_items")

    def __repr__(self):
        return f"<InvoiceLineItem {self.line_item_id} - ride {self.ride_id}>"


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