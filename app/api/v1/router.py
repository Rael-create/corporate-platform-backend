from flask import Blueprint

from app.api.v1.endpoints.corporates_routes import corporate_bp
from app.api.v1.endpoints.users_routes import users_bp
from app.api.v1.endpoints.ride_request_routes import ride_request_bp
from app.api.v1.endpoints.rates_route import rates_bp
from app.api.v1.endpoints.wallet_route import wallet_bp
from app.api.v1.endpoints.ledger_entry_route import ledger_bp
from app.api.v1.endpoints.gateway_payouts_route import gateway_payout_bp
from app.api.v1.endpoints.staff_route import staff_bp
from app.api.v1.endpoints.auth_route import auth_bp

def register_blueprints(app):
    app.register_blueprint(corporate_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(ride_request_bp)
    app.register_blueprint(rates_bp)
    app.register_blueprint(wallet_bp)
    app.register_blueprint(ledger_bp)
    app.register_blueprint(gateway_payout_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(auth_bp)
    