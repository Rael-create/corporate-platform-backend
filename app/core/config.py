import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # STK Push 
    MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
    MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
    MPESA_PASSKEY = os.getenv("MPESA_PASSKEY")
    MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE", "174379")  
    MPESA_ENVIRONMENT = os.getenv("MPESA_ENVIRONMENT", "sandbox")
    MPESA_CALLBACK_BASE_URL = os.getenv("MPESA_CALLBACK_BASE_URL")

    # B2C / B2B 
    MPESA_INITIATOR_NAME = os.getenv("MPESA_INITIATOR_NAME")
    MPESA_INITIATOR_PASSWORD = os.getenv("MPESA_INITIATOR_PASSWORD")
    MPESA_B2C_SHORTCODE = os.getenv("MPESA_B2C_SHORTCODE")
    #MPESA_SECURITY_CREDENTIAL = os.getenv("MPESA_SECURITY_CREDENTIAL")
    MPESA_PUBLIC_CERT_PATH = os.getenv("MPESA_PUBLIC_CERT_PATH")

    @property
    def MPESA_BASE_URL(self):
        """Returns the correct Safaricom API base URL based on environment."""
        if self.MPESA_ENVIRONMENT == "sandbox":
            return "https://sandbox.safaricom.co.ke"
        return "https://api.safaricom.co.ke"

settings = Config()
