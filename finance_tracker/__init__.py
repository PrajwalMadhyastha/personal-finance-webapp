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

def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        # Load the real configuration from environment variables
        db_server = os.getenv('DB_SERVER')
        db_name = os.getenv('DB_NAME')
        db_admin_login = os.getenv('DB_ADMIN_LOGIN')
        db_admin_password = os.getenv('DB_ADMIN_PASSWORD')
        secret_key = os.getenv('SECRET_KEY')

        if not all([db_server, db_name, db_admin_login, db_admin_password, secret_key]):
            raise ValueError("One or more required environment variables are not set.")
            
        password_safe = urllib.parse.quote_plus(db_admin_password)
        driver_name = 'ODBC Driver 18 for SQL Server'
        
        # --- THIS IS THE CORRECTED LINE ---
        # The Timeout parameter must be part of the query string arguments after the '?'.
        db_uri = f"mssql+pyodbc://{db_admin_login}:{password_safe}@{db_server}/{db_name}?driver={urllib.parse.quote_plus(driver_name)}&Timeout=60"
        
        app.config.from_mapping(
            SECRET_KEY=secret_key,
            SQLALCHEMY_DATABASE_URI=db_uri,
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            TASK_SECRET_KEY=os.getenv('TASK_SECRET_KEY')
        )
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # --- Initialize extensions with the app ---
    db.init_app(app)
    metrics.init_app(app)
    bcrypt.init_app(app)

    from . import models
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # --- Configure logging ---
    app.logger.setLevel(logging.INFO)
    app.logger.info("Personal Finance App startup complete.")

    # --- Register blueprints ---
    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app

@login_manager.user_loader
def load_user(user_id):
    from .models import User
    # Use the modern db.session.get() instead of the legacy .query.get()
    return db.session.get(User, int(user_id))