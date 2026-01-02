# app/__init__.py
from flask import Flask
from flask_cors import CORS
from database import db_setup
from app.config.settings import settings

def create_app():
    app = Flask(__name__)

    # Enable CORS for all routes
    CORS(app, resources={
        r"/*": {
            "origins": ["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

    # Load settings
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['JWT_SECRET'] = settings.JWT_SECRET
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = settings.JWT_ACCESS_TOKEN_EXPIRES
    app.config['DATABASE'] = settings.DATABASE
    app.config['JSON_AS_ASCII'] = settings.JSON_AS_ASCII

    # Register blueprints
    from .chat.chat_routes import chat_bp
    from .auth import bp as auth_bp

    app.register_blueprint(chat_bp)
    app.register_blueprint(auth_bp)

    # Teardown
    app.teardown_appcontext(db_setup.close_connection)

    return app
