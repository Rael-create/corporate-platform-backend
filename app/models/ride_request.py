from app.core.database import db
from datetime import datetime
import enum

class RideStatus(enum.Enum):
       PENDING = "PENDING"
       APPROVED = "APPROVED"
       REJECTED = "REJECTED"
       COMPLETED = "COMPLETED"
       CANCELLED = "CANCELLED"
    

class RideRequest(db.Model):
    __tablename__ = 'ride_requests'

    ride_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    #Links this ride to a specific Staff member in the 'staff' table.
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id'), nullable=False)
    #Links this ride to a specific Corporate entity in the 'corporates' table.
    corporate_id = db.Column(db.Integer, db.ForeignKey('corporates.corporate_id'), nullable=False)
    
    pickup_location = db.Column(db.String(255), nullable=False)
    destination = db.Column(db.String(255), nullable=False) 
    ride_date = db.Column(db.DateTime, nullable=False)       
    reason = db.Column(db.Text, nullable=True)              
    
    status = db.Column(db.Enum(RideStatus), default=RideStatus.PENDING, nullable=False)
    estimated_fare = db.Column(db.Float, nullable=True)
    actual_fare = db.Column(db.Float, nullable=True)
    
    vat_rate = db.Column(db.Float, nullable=True)
    commission_rate = db.Column(db.Float, nullable=True)
    
    vat_amount = db.Column(db.Float, nullable=True)
    commission_amount = db.Column(db.Float, nullable=True)
    
    payment_status =db.Column
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    staff = db.relationship("Staff", backref="ride_requests", lazy=True)
    corporate = db.relationship("Corporate", backref="ride_requests", lazy=True)

    def __repr__(self):
        return f"<RideRequest {self.ride_id} - {self.status.value}>"