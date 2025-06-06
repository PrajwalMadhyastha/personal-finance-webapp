# finance_tracker/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # Configure the app
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # ADD THIS LINE: A secret key is required for session-based flash messages.
    # In production, this should be a long, random string loaded from a config file or environment variable.
    app.config['SECRET_KEY'] = 'a_very_secret_and_random_key_that_is_not_this_one'

    db.init_app(app)

    from .routes import main_bp
    app.register_blueprint(main_bp)

    from .reporting_routes import reporting_bp
    app.register_blueprint(reporting_bp)

    return app