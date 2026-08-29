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


#  STK Push
def stk_push(phone_number, amount, account_reference, transaction_desc="Payment"):
    #  Get Access Token
    access_token = _get_access_token()
    
    #  Generate timestamp and password
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    password_str = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
    encoded_password = base64.b64encode(password_str.encode()).decode()

    # . Build the full callback URL
    callback_url = f"{settings.MPESA_CALLBACK_BASE_URL}/api/v1/mpesa/callback"

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
    """
    Check the status of an STK Push transaction using the CheckoutRequestID.
    """
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