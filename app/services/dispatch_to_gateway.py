import uuid
import logging
from typing import Tuple, Dict, Any

# from app.core.database import db
# from app.models.gateway_payouts import GatewayPayout

logger = logging.getLogger(__name__)


def dispatch_to_gateway(ride: int,payout: int,db,simulate_failure: bool = False,simulate_timeout: bool = False):
    """
    Mock function to dispatch B2C/B2B payout request to a payment gateway (e.g., M-Pesa Daraja API).

    Args:
        ride_id: Database ID of the pending ride request
        target_identifier: Matatu Till Number, Paybill, or Phone Number
        amount: Base fare amount to be dispatched (matatu_payout)
        simulate_failure: Force a synchronous gateway rejection for testing
        simulate_timeout: Force a simulated timeout error for testing

    Returns:
        Tuple containing:
        - success (bool): True if gateway synchronously accepted request for processing
        - gateway_reference (str): Tracking ID assigned by gateway (or empty string)
        - raw_response (dict): Mock JSON response payload from the API gateway
    """

    amount, target_identifier = ride.base_fare, ride.matatu_identifier

    logger.info(
        f"[GATEWAY DISPATCH] Initiating payout of KES {amount} for Ride ID: {ride.ride_id} -> Target: {target_identifier}"
    )

    # ride = RideRequest.query.get(ride_id)
    # payout = GatewayPayout.query.filter_by(ride_id=ride_id).first()

    payload = {
        "InitiatorName": "MATATU_PLATFORM_API",
        "CommandID": "BusinessPayment",
        "Amount": str(amount),
        "PartyB": target_identifier,
        "Remarks": f"Matatu Trip Payment #{ride.ride_id}",
        "QueueTimeOutURL": "https://api.yourdomain.com/api/v1/webhooks/gateway/timeout",
        "ResultURL": "https://api.yourdomain.com/api/v1/webhooks/gateway/callback",
    }

    # Simulate Network Timeout / Connection Error
    if simulate_timeout:
        logger.error(
            f"[GATEWAY ERROR] Network timeout while connecting to gateway endpoint for Ride ID: {ride.ride_id}"
        )

        # Update payout status
        payout.status = "FAILED"
        payout.failure_reason = "Gateway Timeout. Request could not reach provider."
        db.session.commit()

        return (
            False,
            "",
            {
                "ResponseCode": "504",
                "ResponseDescription": "Gateway Timeout. Request could not reach provider.",
            },
        )

    # Simulate Synchronous Gateway Rejection (e.g., Invalid Till Number format)
    if simulate_failure:
        logger.warning(
            f"[GATEWAY REJECT] Gateway rejected payout payload for Ride ID: {ride.ride_id}"
        )

        # Mark payout and ride as FAILED in database
        payout.status = "FAILED"
        payout.failure_reason = "Invalid Receiver Identifier / Till Number."
        ride.status = "FAILED"
        db.session.commit()

        return (
            False,
            "",
            {
                "ResponseCode": "C2B00012",
                "ResponseDescription": "Invalid Receiver Identifier / Till Number.",
            },
        )

    # Simulate Successful Acceptance (HTTP 200 OK)
    # Generate mock Conversation / Tracking Reference ID (e.g., M-Pesa QWE123RTY)
    mock_conversation_id = f"MPESA_{uuid.uuid4().hex[:8].upper()}"

    mock_response = {
        "OriginatorConversationID": f"ORG_{uuid.uuid4().hex[:8].upper()}",
        "ConversationID": mock_conversation_id,
        "ResponseCode": "0",
        "ResponseDescription": "Accept the service request successfully.",
    }

    # Store initial tracking reference on the pending Payout record
    payout.gateway_reference = mock_conversation_id
    payout.status = "SUCCESS"  # Awaiting async webhook callback
    db.session.commit()

    logger.info(
        f"[GATEWAY SUCCESS] Payout queued successfully by Gateway. Ref: {mock_conversation_id}"
    )

    return True, mock_conversation_id, mock_response
