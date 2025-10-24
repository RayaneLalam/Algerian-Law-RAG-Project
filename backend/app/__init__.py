# app/__init__.py
from flask import Flask
from database import db_setup
from app.config import settings  # import your settings module

def create_app():
    app = Flask(__name__)

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
