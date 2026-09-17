# pyrefly: ignore [missing-import]
from flask_jwt_extended import JWTManager

# pyrefly: ignore [missing-import]
from flask import Flask
from flask_migrate import Migrate
# pyrefly: ignore [missing-import]
from flasgger import Swagger
from flask_cors import CORS

from app.core.database import db
from app.core.config import Config
from app.api.v1.router import register_blueprints

migrate = Migrate()

def create_app():
    app = Flask(__name__)

    CORS(app,
         origins=["http://localhost:5173", "http://127.0.0.1:5173"],
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
         ) 

    # Load configuration
    app.config.from_object(Config)

    app.config["JWT_SECRET_KEY"] = "super-secret-key-change-later-1234567890" 
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600 # Token lasts 1 hour
    JWTManager(app)

    # Initialize database
    db.init_app(app)

    # Initialize migration tool
    migrate.init_app(app, db)


    # Register blueprints
    register_blueprints(app)

    # Import models so Flask-Migrate sees them
    from app.models.users import User
    from app.models.corporate import Corporate
    from app.models.staff import Staff
    from app.models.ride_request import RideRequest
    from app.models.rates import RateType, Rate
    from app.models.wallet import Wallet
    from app.models.ride_counter import RideCounter
    from app.models.finance import PlatformRevenue, Invoice
    from app.models.platform_settings import PlatformSettings
    from app.models.mpesa_transaction import MpesaTransaction


    # Start scheduler
    from app.scheduler import start_scheduler
    start_scheduler(app)


    

    return app