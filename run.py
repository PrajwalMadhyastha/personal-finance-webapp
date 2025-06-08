# run.py
from finance_tracker import create_app, db
from sqlalchemy import inspect # Import the inspector tool from SQLAlchemy

app = create_app()

def create_database_schema():
    """Checks if the database schema exists and creates it if it doesn't."""
    with app.app_context():
        # The 'inspector' allows us to look at the database's properties, like table names
        inspector = inspect(db.engine)
        
        # Check if a table named 'expense' exists.
        if not inspector.has_table("expense"):
            print("Database schema not found. Creating tables...")
            
            # db.create_all() will create all tables defined in your models
            # that don't already exist. It's safe to run multiple times.
            db.create_all()
            print("Database tables created successfully.")
        else:
            print("Database schema already exists. Skipping creation.")

# This block runs the app
if __name__ == '__main__':
    # Before running the app, we ensure the database schema is created.
    create_database_schema()
    app.run(debug=True, host='0.0.0.0', use_reloader=False)