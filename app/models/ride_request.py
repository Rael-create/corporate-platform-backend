from app.core.database import db
from datetime import datetime
import enum

RideStatus = [
    "PENDING",
    "COMPLETED",
    "FAILED"
]
    

class RideRequest(db.Model):
    __tablename__ = 'ride_requests'

    ride_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    #Links this ride to a specific Staff member in the 'staff' table.
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id'), nullable=False)
    #Links this ride to a specific Corporate entity in the 'corporates' table.
    corporate_id = db.Column(db.Integer, db.ForeignKey('corporates.corporate_id'), nullable=False)
    
    pickup_location = db.Column(db.String(255), nullable=False)
    destination = db.Column(db.String(255), nullable=False) 
    reason = db.Column(db.Text, nullable=True)              
    
    # Matatu details
    matatu_identifier = db.Column(db.String(100), nullable=False) # Input target (Till Number, Paybill/Account, POCHI
    
    #Financial fields
    base_fare = db.Column(db.Float, nullable=True)
    vat_rate = db.Column(db.Float, nullable=True)
    commission_rate = db.Column(db.Float, nullable=True)
    vat_amount = db.Column(db.Float, nullable=True)
    commission_amount = db.Column(db.Float, nullable=True)
    total_fare = db.Column(db.Float, nullable=True)
    matatu_payout = db.Column(db.Float, nullable=True)
    
    status = db.Column(db.Enum(*RideStatus), default="PENDING", nullable=False)
    
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    staff = db.relationship("Staff", backref="ride_requests", lazy=True)
    corporate = db.relationship("Corporate", backref="ride_requests", lazy=True)

    def __repr__(self):
        return f"<RideRequest {self.ride_id} - {self.status}>"