# finance_tracker/__init__.py

import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from prometheus_flask_exporter import PrometheusMetrics
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from dotenv import load_dotenv
from config import config_by_name

# Load environment variables from .env file, especially for local development
load_dotenv()

# Create extension instances without initializing them on an app yet
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
metrics = PrometheusMetrics(app=None)
login_manager = LoginManager()
login_manager.login_view = 'main.login' # The route for your login page
login_manager.login_message_category = 'info' # For flash messages

# The user_loader function required by Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return db.session.get(User, int(user_id))


def create_app(config_name='development'):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # Load configuration from the config.py file based on the environment
    config_object = config_by_name.get(config_name)
    app.config.from_object(config_object)

    # --- THE KEY CHANGE IS HERE ---
    # This block allows us to override the database URI with a single environment
    # variable, which is perfect for cloud deployments and CI/CD pipelines.
    # If DATABASE_URL is set, it will be used. Otherwise, the app falls back
    # to the URI constructed in the DevelopmentConfig object from your config.py.
    database_url_env = os.getenv('DATABASE_URL')
    if database_url_env:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url_env
    # --- END OF KEY CHANGE ---

    # Initialize extensions with the configured app instance
    db.init_app(app)
    migrate.init_app(app, db) # Initialize migrate after db
    bcrypt.init_app(app)
    metrics.init_app(app)
    login_manager.init_app(app)

    # Configure logging
    app.logger.setLevel(logging.INFO)
    app.logger.info(f"Personal Finance App starting up with '{config_name}' config.")

    # Register blueprints for routes
    from .routes import main_bp
    app.register_blueprint(main_bp)

    from .api_routes import api_bp
    app.register_blueprint(api_bp)

    return app