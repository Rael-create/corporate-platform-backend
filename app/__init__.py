from flask_jwt_extended import JWTManager

from flask import Flask
from flask_migrate import Migrate
from flasgger import Swagger

from app.core.database import db
from app.core.config import Config
from app.api.v1.router import register_blueprints

migrate = Migrate()

def create_app():
    app = Flask(__name__)


    # Load configuration
    app.config.from_object(Config)

    app.config["JWT_SECRET_KEY"] = "super-secret-key-change-later" 
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600 # Token lasts 1 hour
    JWTManager(app)

    # Initialize database
    db.init_app(app)

    # Initialize migration tool
    migrate.init_app(app, db)

    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "swagger_ui": True,
        "specs_route": "/docs/"
    }
    Swagger(app, config=swagger_config)
    
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
    from app.models.finance import PlatformRevenue, Payment, Invoice


    return app