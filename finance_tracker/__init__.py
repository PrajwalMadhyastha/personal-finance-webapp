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

load_dotenv()

# Create extension instances
db = SQLAlchemy()
metrics = PrometheusMetrics(app=None)
bcrypt = Bcrypt()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'

def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # --- Configuration ---
    # FIXED: These now EXACTLY match the names in your .env file and Terraform config
    db_server = os.getenv('DB_SERVER')
    db_name = os.getenv('DB_NAME')
    db_admin_login = os.getenv('DB_ADMIN_LOGIN')
    db_admin_password = os.getenv('DB_ADMIN_PASSWORD')
    
    # This check is good practice!
    if not all([db_server, db_name, db_admin_login, db_admin_password]):
        raise ValueError("Database configuration is missing from environment variables.")
        
    driver_name = 'ODBC Driver 18 for SQL Server'
    # This is also good practice for passwords with special characters.
    password_safe = urllib.parse.quote_plus(db_admin_password)
    
    # FIXED: Using the corrected python variable names for clarity.
    db_uri = f"mssql+pyodbc://{db_admin_login}:{password_safe}@{db_server}/{db_name}?driver={urllib.parse.quote_plus(driver_name)}"
    
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'a_default_fallback_secret_key_for_dev'),
        SQLALCHEMY_DATABASE_URI=db_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TASK_SECRET_KEY=os.getenv('TASK_SECRET_KEY')

    )

    # --- Initialize extensions ---
    db.init_app(app)
    metrics.init_app(app)
    bcrypt.init_app(app)

    # Import models to ensure they are registered with SQLAlchemy
    from . import models
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # --- Configure logging ---
    app.logger.setLevel(logging.DEBUG)
    app.logger.info("Personal Finance App startup complete.")

    # --- Register blueprints ---
    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app

@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.query.get(int(user_id))