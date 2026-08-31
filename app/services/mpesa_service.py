import base64
import datetime
import requests
from app.core.config import settings

# HELPER: Get Access Token
def _get_access_token():
    url = f"{settings.MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    auth_string = f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    
    headers = {"Authorization": f"Basic {encoded_auth}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["access_token"]


# HELPER: Encrypt Initiator Password (For B2C/B2B)
def encrypt_initiator_password(password, cert_path):
    """
    Encrypt the Initiator Password using M-Pesa's public certificate.
    Returns base64 encoded string.
    """
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.backends import default_backend
    
    with open(cert_path, "rb") as f:
        cert_data = f.read()
    
    cert = serialization.load_pem_x509_certificate(cert_data, default_backend())
    public_key = cert.public_key()
    
    encrypted = public_key.encrypt(
        password.encode('utf-8'),
        padding.PKCS1v15()
    )
    
    return base64.b64encode(encrypted).decode('utf-8')

#  STK Push
def stk_push(phone_number, amount, account_reference, transaction_desc="Payment"):
    #  Get Access Token
    access_token = _get_access_token()
    
    #  Generate timestamp and password
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    password_str = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
    encoded_password = base64.b64encode(password_str.encode()).decode()

    #  Build the full callback URL
    callback_url = f"{settings.MPESA_CALLBACK_BASE_URL}/api/v1/mpesa/callback"

    print(f"🔗 CALLBACK URL BEING SENT: {callback_url}")

    # Build the request payload
    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": encoded_password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone_number,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url,
        "AccountReference": account_reference,
        "TransactionDesc": transaction_desc,
    }

    # Send the request
    url = f"{settings.MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


#  Query STK Status
def query_status(checkout_request_id):
    """Check the status of an STK Push transaction."""

    #  Get Access Token
    access_token = _get_access_token()
    
    #  Generate timestamp and password
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    password_str = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
    encoded_password = base64.b64encode(password_str.encode()).decode()

    # Build the request payload
    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": encoded_password,
        "Timestamp": timestamp,
        "CheckoutRequestID": checkout_request_id,
    }

    #  Send the request
    url = f"{settings.MPESA_BASE_URL}/mpesa/stkpushquery/v1/query"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()



# B2C - Send Money to Personal M-Pesa Number

def send_money(phone_number, amount, transaction_desc="Payment", command_id="BusinessPayment"):
    """
    Send money from platform to a personal M-Pesa number (B2C).
    - phone_number: e.g., '254712345678' (no leading '+')
    """
    access_token = _get_access_token()
    
    # Encrypt initiator password
    security_credential = encrypt_initiator_password(
        settings.MPESA_INITIATOR_PASSWORD,
        settings.MPESA_PUBLIC_CERT_PATH
    )

    payload = {
        "InitiatorName": settings.MPESA_INITIATOR_NAME,
        "SecurityCredential": security_credential,
        "CommandID": command_id,
        "Amount": int(amount),
        "PartyA": settings.MPESA_B2C_SHORTCODE,
        "PartyB": phone_number,
        "Remarks": transaction_desc[:50],
        "QueueTimeOutURL": f"{settings.MPESA_CALLBACK_BASE_URL}/api/v1/mpesa/b2c/timeout",
        "ResultURL": f"{settings.MPESA_CALLBACK_BASE_URL}/api/v1/mpesa/b2c/result",
        "Occassion": transaction_desc[:50]
    }

    url = f"{settings.MPESA_BASE_URL}/mpesa/b2c/v3/paymentrequest"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

#  B2C - Send Money to Pochi La Biashara Wallet
def send_money_to_plb(phone_number, amount, transaction_desc="Payment"):
    """Send money from platform to a Pochi La Biashara wallet (B2Pochi)."""
    access_token = _get_access_token()
    
    security_credential = encrypt_initiator_password(
        settings.MPESA_INITIATOR_PASSWORD,
        settings.MPESA_PUBLIC_CERT_PATH
    )

    payload = {
        "InitiatorName": settings.MPESA_INITIATOR_NAME,
        "SecurityCredential": security_credential,
        "CommandID": "BusinessPayment",  # PLB uses BusinessPayment
        "Amount": int(amount),
        "PartyA": settings.MPESA_B2C_SHORTCODE,
        "PartyB": phone_number,  # Phone number linked to PLB
        "Remarks": transaction_desc[:50],
        "QueueTimeOutURL": f"{settings.MPESA_CALLBACK_BASE_URL}/api/v1/mpesa/b2c/timeout",
        "ResultURL": f"{settings.MPESA_CALLBACK_BASE_URL}/api/v1/mpesa/b2c/result",
        "Occassion": transaction_desc[:50]
    }

    url = f"{settings.MPESA_BASE_URL}/mpesa/b2c/v3/paymentrequest"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


#  B2B - Send Money to Till Number (Buy Goods)
def send_to_till(till_number, amount, account_reference, transaction_desc="Payment"):
    """
    Send money from platform to a Till number (B2B BusinessBuyGoods).
    - till_number: The Till number (e.g., '123456')
    """
    access_token = _get_access_token()
    
    security_credential = encrypt_initiator_password(
        settings.MPESA_INITIATOR_PASSWORD,
        settings.MPESA_PUBLIC_CERT_PATH
    )

    payload = {
        "Initiator": settings.MPESA_INITIATOR_NAME,
        "SecurityCredential": security_credential,
        "CommandID": "BusinessBuyGoods",
        "Sender": settings.MPESA_B2C_SHORTCODE,
        "Receiver": till_number,
        "Amount": int(amount),
        "ReceiverIdentifierType": "4",  # 4 = Till Number
        "SenderIdentifierType": "4",
        "AccountReference": account_reference[:12],
        "Remarks": transaction_desc[:50],
        "QueueTimeOutURL": f"{settings.MPESA_CALLBACK_BASE_URL}/api/v1/mpesa/b2b/timeout",
        "ResultURL": f"{settings.MPESA_CALLBACK_BASE_URL}/api/v1/mpesa/b2b/result",
    }

    url = f"{settings.MPESA_BASE_URL}/mpesa/b2b/v1/paymentrequest"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


#  B2B - Send Money to PayBill + Account Number
def send_to_paybill(paybill_number, account_number, amount, transaction_desc="Payment"):
    """
    Send money from platform to a PayBill + Account Number (B2B BusinessPayBill).
    - paybill_number: The PayBill number (e.g., '123456')
    - account_number: The Account Number (e.g., 'ACC001')
    """
    access_token = _get_access_token()
    
    security_credential = encrypt_initiator_password(
        settings.MPESA_INITIATOR_PASSWORD,
        settings.MPESA_PUBLIC_CERT_PATH
    )

    payload = {
        "Initiator": settings.MPESA_INITIATOR_NAME,
        "SecurityCredential": security_credential,
        "CommandID": "BusinessPayBill",
        "Sender": settings.MPESA_B2C_SHORTCODE,
        "Receiver": paybill_number,
        "Amount": int(amount),
        "ReceiverIdentifierType": "2",  # 2 = PayBill Number
        "SenderIdentifierType": "2",
        "AccountReference": account_number[:12],
        "Remarks": transaction_desc[:50],
        "QueueTimeOutURL": f"{settings.MPESA_CALLBACK_BASE_URL}/api/v1/mpesa/b2b/timeout",
        "ResultURL": f"{settings.MPESA_CALLBACK_BASE_URL}/api/v1/mpesa/b2b/result",
    }

    url = f"{settings.MPESA_BASE_URL}/mpesa/b2b/v1/paymentrequest"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()