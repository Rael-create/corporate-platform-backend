import uuid
import logging
from app.services.mpesa_service import send_money, send_money_to_plb, send_to_till, send_to_paybill
from app.core.database import db



logger = logging.getLogger(__name__)


def dispatch_to_gateway(ride: int,payout: int,db,simulate_failure: bool = False,simulate_timeout: bool = False):


    # amount, target_identifier = ride.base_fare, ride.matatu_identifier

    ride_id = ride.ride_id

    try:
        #  Extract payment details
        payment_method = payout.payment_method
        target_identifier = payout.target_identifier
        amount = payout.amount_sent

        logger.info(
            f"[GATEWAY DISPATCH] Processing payout of KES {amount} for Ride #{ride_id} "
            f"via {payment_method} -> Target: {target_identifier}"
        )

        # Simulate timeout (if you want to handle it)
        if simulate_timeout:
            logger.warning(f"[GATEWAY DISPATCH] Simulated timeout for Ride #{ride_id}")
            payout.status = "FAILED"
            payout.failure_reason = "Simulated timeout – callback not received"
            db.session.commit()
            return False, payout, {"ResponseCode": "504", "ResponseDescription": "Timeout"}

        #  For testing: simulate failure
        if simulate_failure:
            logger.warning(f"[GATEWAY DISPATCH] Simulated failure for Ride #{ride_id}")
            payout.status = "FAILED"
            payout.failure_reason = "Simulated gateway failure for testing"
            db.session.commit()
            return False, payout, {"ResponseCode": "999", "ResponseDescription": "Simulated failure"}

        #  For PAYBILL, we need an account reference
        account_reference = getattr(payout, 'account_reference', None)
        if payment_method == "PAYBILL" and not account_reference:
            account_reference = f"RIDE{ride_id}"

        #  Call the appropriate M-Pesa API
        mpesa_response = None

        if payment_method == "SEND_MONEY":
            mpesa_response = send_money(
                phone_number=target_identifier,
                amount=amount,
                transaction_desc=f"Ride #{ride_id}"
            )
        elif payment_method == "POCHI_LA_BIASHARA":
            mpesa_response = send_money_to_plb(
                phone_number=target_identifier,
                amount=amount,
                transaction_desc=f"Ride #{ride_id}"
            )
        elif payment_method == "BUY_GOODS":
            if not account_reference:
                account_reference = f"RIDE{ride_id}"
            mpesa_response = send_to_till(
                till_number=target_identifier,
                amount=amount,
                account_reference=account_reference,
                transaction_desc=f"Ride #{ride_id}"
            )
        elif payment_method == "PAYBILL":
            # Split the target_identifier
            parts = target_identifier.split('|')
            if len(parts) !=2:
                raise ValueError(f"Invalid PAYBILL format. Expected 'paybill|account', got: {target_identifier}")

            paybill_number = parts[0]
            account_number = parts[1]

            # Remove leading zeros from account number if needed
            account_number = account_number.lstrip('0')

            mpesa_response = send_to_paybill(
                paybill_number=paybill_number,
                account_number=account_number,
                amount=amount,
                transaction_desc=f"Ride #{ride_id}"
            )
        else:
            raise ValueError(f"Unsupported payment method: {payment_method}")

        #  Check if M-Pesa accepted the request
        if mpesa_response.get("ResponseCode") == "0":
            # Update the payout with ConversationID
            payout.gateway_reference = mpesa_response.get("ConversationID")
            # Status remains PENDING – callback will change it to SUCCESS/FAILED
            db.session.commit()
            logger.info(
                f"[GATEWAY DISPATCH] Payout accepted by M-Pesa. "
                f"ConversationID: {payout.gateway_reference}"
            )
            return True, payout, mpesa_response
        else:
            # M-Pesa rejected the request immediately
            payout.status = "FAILED"
            payout.failure_reason = mpesa_response.get("ResponseDescription", "M-Pesa rejected")
            db.session.commit()
            logger.error(
                f"[GATEWAY DISPATCH] M-Pesa rejected payout for Ride #{ride_id}: "
                f"{payout.failure_reason}"
            )
            return False, payout, mpesa_response

    except Exception as e:
        db.session.rollback()
        logger.error(f"[GATEWAY DISPATCH] Error processing payout for Ride #{ride_id}: {str(e)}")
        payout.status = "FAILED"
        payout.failure_reason = str(e)
        db.session.commit()
        return False, payout, {"error": str(e)}
