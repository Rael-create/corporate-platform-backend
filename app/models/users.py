from datetime import datetime

from app.core.database import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # e.g., 'admin','staff'
    created_at = db.Column(db.DateTime, default=datetime.now)


    corporate_id = db.Column(db.Integer, db.ForeignKey('corporates.corporate_id'), nullable=True)

    otp_code = db.Column(db.String(4), nullable=True)
    otp_expires_at = db.Column(db.DateTime, nullable=True)
    
    # --- Password Helper Methods ---
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"<User {self.username}>"
