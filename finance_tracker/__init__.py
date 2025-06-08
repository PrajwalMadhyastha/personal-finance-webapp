# finance_tracker/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
import urllib
import logging

load_dotenv()
db = SQLAlchemy()

def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # --- Construct the Database URI from Environment Variables ---
    db_server = os.getenv('DB_SERVER_FQDN')
    db_name = os.getenv('DB_NAME')
    db_user = os.getenv('DB_ADMIN_LOGIN')
    db_password = os.getenv('DB_ADMIN_PASSWORD')

    if not all([db_server, db_name, db_user, db_password]):
        raise ValueError("Database configuration is missing from environment variables.")
    
    # ======================================================================
    # THE CRITICAL CHANGE: We now use the 'ODBC Driver 18 for SQL Server' driver name.
    # ======================================================================
    driver_name = 'ODBC Driver 18 for SQL Server'
    
    password_safe = urllib.parse.quote_plus(db_password)

    # --- CONFIGURE LOGGING ---
    # Set the logging level. DEBUG is the most verbose. In production, you'd
    # likely set this to INFO or WARNING.
    app.logger.setLevel(logging.DEBUG)

    # Optional: You can add custom handlers and formatters here for file logging
    # or more complex setups. For now, the default console logger is fine.

    app.logger.info("Personal Finance App startup complete.")
    # --- END LOGGING CONFIGURATION ---

    # The URI now uses the simple driver name we configured in odbcinst.ini
    db_uri = f"mssql+pyodbc://{db_user}:{password_safe}@{db_server}/{db_name}?driver={urllib.parse.quote_plus(driver_name)}"
    
    # --- Configure the App ---
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a_default_fallback_secret_key')

    db.init_app(app)

    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app