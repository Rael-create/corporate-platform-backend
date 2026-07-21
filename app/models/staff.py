from app.core.database import db
from datetime import datetime


class  Staff(db.Model):
    __tablename__ = 'staff'

    staff_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    staff_number = db.Column(db.String(50), unique=True, nullable=False)
    national_id = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    #Link Connects the Staff profile to a User login
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, unique=True)

    # Link Connects the Staff member to their Corporate entity
    corporate_id = db.Column(db.Integer, db.ForeignKey('corporates.corporate_id'), nullable=False)

    user = db.relationship("User", backref="staff", uselist=False)

    def __repr__(self):
        return f"<Staff {self.first_name} {self.last_name} {self.staff_number}>"