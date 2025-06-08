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

load_dotenv()

# Create extension instances
db = SQLAlchemy()
metrics = PrometheusMetrics(app=None)
bcrypt = Bcrypt()
migrate = Migrate()

def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # --- Configuration ---
    db_server = os.getenv('DB_SERVER_FQDN')
    db_name = os.getenv('DB_NAME')
    db_user = os.getenv('DB_ADMIN_LOGIN')
    db_password = os.getenv('DB_ADMIN_PASSWORD')
    if not all([db_server, db_name, db_user, db_password]):
        raise ValueError("Database configuration is missing from environment variables.")
    driver_name = 'ODBC Driver 18 for SQL Server'
    password_safe = urllib.parse.quote_plus(db_password)
    db_uri = f"mssql+pyodbc://{db_user}:{password_safe}@{db_server}/{db_name}?driver={urllib.parse.quote_plus(driver_name)}"
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a_default_fallback_secret_key')

    # --- Initialize extensions ---
    db.init_app(app)
    metrics.init_app(app)
    bcrypt.init_app(app)

    # Import models to ensure they are registered with SQLAlchemy
    from . import models
    migrate.init_app(app, db) # Initialize Flask-Migrate

    # --- Configure logging ---
    app.logger.setLevel(logging.DEBUG)
    app.logger.info("Personal Finance App startup complete.")

    # --- Register blueprints ---
    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app