# finance_tracker/__init__.py

import os
import urllib
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from prometheus_flask_exporter import PrometheusMetrics
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from config import config_by_name

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

    config_object = config_by_name.get(config_name)
    app.config.from_object(config_object)
    
    # --- THIS IS THE FIX ---
    # We move the import inside the function to break the circular import.
    from .utils import format_datetime
    app.jinja_env.filters['datetimeformat'] = format_datetime
    # --- END OF FIX ---

    if config_name != 'testing':
        db_uri = os.getenv('DATABASE_URL')
        if not db_uri:
            db_server = os.getenv('DB_SERVER')
            db_name = os.getenv('DB_NAME')
            db_admin_login = os.getenv('DB_ADMIN_LOGIN')
            db_admin_password = os.getenv('DB_ADMIN_PASSWORD')

            if not all([db_server, db_name, db_admin_login, db_admin_password]):
                raise ValueError("For local dev, DB_SERVER, DB_NAME, DB_ADMIN_LOGIN, and DB_ADMIN_PASSWORD must be set in .env")
            
            password_safe = urllib.parse.quote_plus(db_admin_password)
            driver_name = 'ODBC Driver 18 for SQL Server'
            db_uri = (
                f"mssql+pyodbc://{db_admin_login}:{password_safe}@{db_server}/{db_name}?"
                f"driver={urllib.parse.quote_plus(driver_name)}"
                f"&TrustServerCertificate=yes"
            )
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri

    # Initialize extensions with the app
    db.init_app(app)
    metrics.init_app(app)
    bcrypt.init_app(app)
    from . import models
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Configure logging and register blueprints
    app.logger.setLevel(logging.INFO)
    app.logger.info(f"Personal Finance App starting up with '{config_name}' config.")
    from .routes import main_bp
    app.register_blueprint(main_bp)
    from .api_routes import api_bp
    app.register_blueprint(api_bp)

    return app

@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return db.session.get(User, int(user_id))