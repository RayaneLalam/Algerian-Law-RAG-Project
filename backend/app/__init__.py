# app/__init__.py
from flask import Flask
from flask_cors import CORS
import logging
from database import db_setup
from app.config.settings import settings
from app.evaluation.api import evaluation_bp
# Register blueprints
from .chat.chat_routes import chat_bp, get_language_service, get_search_service
from .auth import bp as auth_bp
from flask_cors import CORS

logger = logging.getLogger(__name__)

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


    app.register_blueprint(chat_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(evaluation_bp)
    

    # Pre-load models at startup
    with app.app_context():
        try:
            logger.info(" Loading language service...")
            get_language_service()
            logger.info("✓ Language service loaded")
            
            logger.info(" Loading search service and embedding model...")
            get_search_service()
            logger.info("✓ Search service and embedding model loaded")
            
            logger.info("✓ All models ready for requests!")
        except Exception as e:
            logger.error(f" Error loading models: {e}", exc_info=True)
            raise

    # Pre-load models at startup
    with app.app_context():
        try:
            logger.info(" Loading language service...")
            get_language_service()
            logger.info("✓ Language service loaded")
            
            logger.info(" Loading search service and embedding model...")
            get_search_service()
            logger.info("✓ Search service and embedding model loaded")
            
            logger.info("✓ All models ready for requests!")
        except Exception as e:
            logger.error(f" Error loading models: {e}", exc_info=True)
            raise

    # Teardown
    app.teardown_appcontext(db_setup.close_connection)

    return app
