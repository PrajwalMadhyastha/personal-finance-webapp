# run.py
from finance_tracker import create_app, db
from sqlalchemy import inspect # Import the inspector tool from SQLAlchemy

app = create_app()

def create_database_schema():
    """Ensures all database tables defined in the models are created."""
    # The 'with app.app_context()' is crucial for database operations
    with app.app_context():
        print("Ensuring database schema exists...")
        
        # db.create_all() is safe to run multiple times. It will only create
        # tables that do not already exist in the database.
        db.create_all()
        print("Database schema check complete.")

# This block runs the app
if __name__ == '__main__':
    # Before running the app, we ensure the database schema is created.
    create_database_schema()
    app.run(debug=True, host='0.0.0.0', use_reloader=False)