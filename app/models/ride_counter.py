from app.core.database import db
from datetime import datetime


class RideCounter(db.Model):
    __tablename__ = "ride_counters"

    counter_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    staff_id = db.Column(
        db.Integer,
        db.ForeignKey("staff.staff_id"),
        nullable=False,
        unique=True
    )

    cumulative_no_of_rides = db.Column(db.Integer, default=0, nullable=False)
    cumulative_amount = db.Column(db.Float, default=0.0, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.now,
        onupdate=datetime.now
    )

    # Added db.backref with uselist=False for a true 1-to-1 relationship
    staff = db.relationship(
        "Staff", 
        backref=db.backref("ride_counter", uselist=False)
    )

    def __repr__(self):
        return f"<RideCounter Staff:{self.staff_id} Rides:{self.cumulative_no_of_rides} Amount:{self.cumulative_amount}>"