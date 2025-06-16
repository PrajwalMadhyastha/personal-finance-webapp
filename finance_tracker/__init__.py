# finance_tracker/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from prometheus_flask_exporter import PrometheusMetrics
from flask_bcrypt import Bcrypt
import os
from dotenv import load_dotenv
import urllib
import logging
from flask_login import LoginManager
from config import config_by_name

load_dotenv()

# Create extension instances
db = SQLAlchemy()
metrics = PrometheusMetrics(app=None)
bcrypt = Bcrypt()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'

def create_app(config_name='development'):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # Load configuration from the config.py file
    config_object = config_by_name.get(config_name)
    app.config.from_object(config_object)

    # Initialize extensions with the app
    db.init_app(app)
    metrics.init_app(app)
    bcrypt.init_app(app)
    from . import models
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Configure logging
    app.logger.setLevel(logging.INFO)
    app.logger.info(f"Personal Finance App starting up with '{config_name}' config.")

    # Register blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)
    from .api_routes import api_bp
    app.register_blueprint(api_bp)

    return app

@login_manager.user_loader
def load_user(user_id):
    from .models import User
    # Use the modern db.session.get() instead of the legacy .query.get()
    return db.session.get(User, int(user_id))