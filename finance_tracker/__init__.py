# finance_tracker/__init__.py (CORRECT VERSION)
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Create the extension instance, but don't attach it to an app yet.
db = SQLAlchemy()

def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # Configure the app
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize the extension with our app instance.
    # This is the point where SQLAlchemy gets configured and attaches
    # helpers like .query to your db.Model classes.
    db.init_app(app)

    # ======================================================================
    # CRITICAL: Import and register the blueprint *inside* the function.
    # This ensures that the import happens AFTER db.init_app() is called.
    # ======================================================================
    from .routes import main_bp
    app.register_blueprint(main_bp)

    # You could also register other blueprints here if you had them.

    return app