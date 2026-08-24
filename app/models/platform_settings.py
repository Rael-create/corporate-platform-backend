from app.core.database import db
from datetime import datetime

class PlatformSettings(db.Model):
    __tablename__ = "platform_settings"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    mpesa_paybill = db.Column(db.String(50), nullable=False, default="4135155")
    mpesa_account_prefix = db.Column(db.String(50), nullable=False, default="INV-")
    bank_name = db.Column(db.String(100), nullable=False, default="Kenya Commercial Bank")
    bank_account_name = db.Column(db.String(100), nullable=False, default="CoporatesRidesManagement")
    bank_account_number = db.Column(db.String(50), nullable=False, default="1219758643")
    bank_branch = db.Column(db.String(100), nullable=False, default="ThikaRoadMall")
    kra_pin = db.Column(db.String(50), nullable=False, default="P052258149G")
    company_name = db.Column(db.String(100), nullable=False, default="CoporatesRidesManagement")
    company_address = db.Column(db.String(255), nullable=False, default="Ideon Tower, Nairobi")
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<PlatformSettings {self.company_name}>"

    @classmethod
    def get_settings(cls):
        """Get the first settings record, or create default if none exists."""
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings








