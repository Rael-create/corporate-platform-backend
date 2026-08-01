class SMSNotification:
    def __init__(self, phone_number, message, message_type):
        self.phone_number = phone_number
        self.message = message
        self.message_type = message_type

    def send(self):
        """Simulates sending an SMS."""
        print("\n" + "="*60)
        print(f"📱 [SMS MOCK] Sending {self.message_type} to {self.phone_number}:")
        print(f"   Message: {self.message}")
        print("="*60 + "\n")
        return True


# HELPER FUNCTIONS


def send_otp(phone_number, otp_code):
    """Send OTP code to user."""
    sms = SMSNotification(
        phone_number=phone_number,
        message=f"Your login code is: {otp_code}. Valid for 5 minutes. Do not share this code.",
        message_type="OTP"
    )
    return sms.send()


def send_ride_confirmation(phone_number, destination, ride_id):
    """Send ride confirmation to staff."""
    sms = SMSNotification(
        phone_number=phone_number,
        message=f"Your ride to {destination} (ID: {ride_id}) has been confirmed. Safe travels!",
        message_type="RIDE_CONFIRMATION"
    )
    return sms.send()


def send_invoice_notification(phone_number, invoice_number, amount, due_date):
    """Send invoice notification to corporate admin."""
    sms = SMSNotification(
        phone_number=phone_number,
        message=f"Invoice {invoice_number} for KES {amount:,.2f} is due on {due_date}. Please pay promptly.",
        message_type="INVOICE"
    )
    return sms.send()


def send_payment_confirmation(phone_number, invoice_number, amount):
    """Send payment confirmation to corporate admin."""
    sms = SMSNotification(
        phone_number=phone_number,
        message=f"Payment of KES {amount:,.2f} for invoice {invoice_number} received. Thank you!",
        message_type="PAYMENT_CONFIRMATION"
    )
    return sms.send()


def send_staff_welcome(phone_number, first_name, corporate_name):
    """Send welcome message to new staff."""
    sms = SMSNotification(
        phone_number=phone_number,
        message=f"Welcome {first_name}! You have been registered with {corporate_name}. You can now book rides using your phone number.",
        message_type="WELCOME"
    )
    return sms.send()


def send_low_balance_alert(phone_number, corporate_name, remaining_rides):
    """Alert when staff has low ride balance."""
    sms = SMSNotification(
        phone_number=phone_number,
        message=f"Alert: You have {remaining_rides} rides remaining in your {corporate_name} account.",
        message_type="BALANCE_ALERT"
    )
    return sms.send()