from decimal import Decimal

from app.models.corporate import Corporate
from app.models.gateway_payouts import GatewayPayout
from app.models.rates import Rate, RateType
from app.models.ride_request import RideRequest
from app.models.wallet import Wallet
from app.services.gateway_payouts_service import create_payout
from app.services.ledger_entry_service import create_ledger_entry


class TripAuthorizationEngine:
    """
    Evaluates trip requests against organization and staff policies
    before executing gateway payouts.
    """

    def __init__(self, staff, base_fare, db_session, data):
        self.staff = staff  # model object
        self.base_fare = base_fare
        self.db_session = db_session
        self.data = data

    def get_latest_rate(self, rate_type_name: str) -> float:
        """Fetch the most recent rate for a given rate type name."""
        rate_type = RateType.query.filter_by(name=rate_type_name).first()
        if not rate_type:
            raise ValueError(f"RateType '{rate_type_name}' not found")

        latest_rate = (
            Rate.query.filter_by(rate_type_id=rate_type.rate_type_id)
            .order_by(Rate.created_at.desc())
            .first()
        )
        if not latest_rate:
            raise ValueError(f"No Rate found for type '{rate_type_name}'")

        return float(latest_rate.rate)

    def calculate_cost_breakdown(self):
        """Calculates total corporate charge including tax and commission."""
        vat_rate = self.get_latest_rate("VAT")
        commission_rate = self.get_latest_rate("COMMISSION")

        base_fare = self.base_fare  # B
        commission_amount = base_fare * commission_rate  # C = B X Commision rate
        vat_amount = base_fare * vat_rate  # V = (b+c)xvat_rate

        total_fare = base_fare + vat_amount + commission_amount  # T = B+C+V

        matatu_payout = base_fare  # P = B

        return {
            "total_fare": total_fare,
            "vat_rate": vat_rate,
            "commission_rate": commission_rate,
            "vat_amount": vat_amount,
            "commission_amount": commission_amount,
            "matatu_payout": matatu_payout,
        }

    def authorize_and_create_ride(self):
        """
        Executes the 4-Gate Validation Sequence.
        Returns: (is_authorized, status_message, financial_breakdown)
        """
        data = self.data
        staff = self.staff
        org = Corporate.query.get(staff.corporate_id)
        # GATE 1: Organization Active Check
        if org.status != "ACTIVE":
            return False, "REJECT: Account Suspended", None, None

        # GATE 1.1 Staff id active
        if staff.status != "ACTIVE":
            return False, "REJECT:Staff is Suspended", None, None

        # GATE 2: Staff Trip Allowance Check
        if staff.rides_allocated is not None:
            if staff.rides_used >= staff.rides_allocated:
                return False, "REJECT: Trip Limit Reached", None, None

        # GATE 3: Single Trip Fare Cap Check
        if staff.max_fare_per_ride is not None:
            if self.base_fare > staff.max_fare_per_ride:
                return (
                    False,
                    f"REJECT: Exceeds Max Fare (Cap: KES {staff.max_fare_per_ride})",
                    None,
                    None,
                )

        # Calculate precise financial impact for Gate 4 check
        cost_bdown = self.calculate_cost_breakdown()

        # GATE 4: Corporate Credit Limit Check
        # CHeck if they use corporate wallet
        # if org.wallet_type == "CORPORATE_FUNDED":
        wallet = Wallet.query.filter_by(corporate_id=org.corporate_id).first()

        # wallet = Wallet.query.filter_by(wallet_type="PLATFORM_FUNDED").first()

        available_credit = wallet.current_balance
        if cost_bdown["total_fare"] > available_credit:
            return (
                False,
                f"REJECT: Your available Balance is Exceeded (Available: KES {available_credit})",
                None,
                None,
            )
        (
            total_fare,
            vat_rate,
            commission_rate,
            vat_amount,
            commission_amount,
            matatu_payout,
        ) = cost_bdown.values()

        # 3. Create the ride (Status is instantly APPROVED)
        new_ride = RideRequest(
            staff_id=staff.staff_id,
            corporate_id=staff.corporate_id,
            pickup_location=data["pickup_location"],
            destination=data["destination"],
            matatu_identifier=data.get("matatu_identifier"),
            base_fare=data["base_fare"],
            total_fare=total_fare,
            vat_rate=vat_rate,
            commission_rate=commission_rate,
            vat_amount=vat_amount,
            commission_amount=commission_amount,
            matatu_payout=matatu_payout,
            reason=data["reason"],
            status="PENDING",
        )

        self.db_session.session.add(new_ride)
        self.db_session.session.flush()

        # deduct the same amount from the walet provsionaly
        create_ledger_entry(
            data={
                "corporate_id": staff.corporate_id,
                "ride_id": new_ride.ride_id,
                "transaction_type": "TRIP_DEDUCTION",
                "transaction_class": "Debit",
                "amount": new_ride.total_fare,
            }
        )

        new_payout = create_payout(
            data={
                "ride_id": new_ride.ride_id,
                "target_identifier": new_ride.matatu_identifier,
                "payment_method": data["payment_method"],
                "amount_sent": new_ride.base_fare,
                "status": "PENDING",
                "gateway_reference": None,
                "failure_reason": None,
            }
        )

        # ALL GATES PASSED: Safe to proceed to gateway execution
        return True, "AUTHORIZED: Proceeding to Gateway Payout", new_ride, new_payout

    def update_rides_used(self, action="add"):
        rides_used = self.staff.rides_used
        if not rides_used:
            rides_used = 0

        if action == "add":
            rides_used += 1
        else:
            if rides_used > 0:
                rides_used -= 1

        self.db_session.session.add(self.staff)
        self.db_session.session.commit()

        return self.staff.rides_used, "New Counter updated"
