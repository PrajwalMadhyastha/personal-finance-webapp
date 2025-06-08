# run.py
from finance_tracker import create_app
from flask_migrate import upgrade # 1. Import the 'upgrade' command

# The create_app function now handles all initialization
app = create_app()

def run_database_migrations():
    """Ensures the database is up-to-date with all migrations."""
    # The 'with app.app_context()' is crucial for database operations
    with app.app_context():
        print("Ensuring database is up-to-date with all migrations...")
        
        # This command will apply any pending migrations.
        # If the database is empty, it will create all tables.
        # If the database is already up-to-date, it does nothing.
        upgrade()
        
        print("Database migration check complete.")


# This block runs the app for local development
if __name__ == '__main__':
    # Before running the app, we ensure the database schema is up-to-date.
    run_database_migrations()
    
    # We are keeping use_reloader=False for stability in your local env.
    app.run(debug=True, host='0.0.0.0', use_reloader=False)