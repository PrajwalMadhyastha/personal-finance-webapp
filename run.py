# run.py
from finance_tracker import create_app, db
from finance_tracker.models import Expense, User # Import models to use them
from flask_migrate import upgrade

# The create_app function handles all application setup
app = create_app()

# --- Custom CLI Commands ---
@app.cli.command("reset-db")
def reset_db_command():
    """Drops all database tables and re-applies all migrations."""
    with app.app_context():
        print("Dropping all database tables...")
        db.drop_all()
        print("Running all migrations to create a fresh schema...")
        upgrade()
        print("Database has been reset successfully.")

@app.cli.command("clear-expenses")
def clear_expenses_command():
    """A custom command to clear all data from the expense table."""
    with app.app_context():
        try:
            num_deleted = db.session.query(Expense).delete()
            db.session.commit()
            print(f"Success: Deleted {num_deleted} old expense(s).")
        except Exception as e:
            db.session.rollback()
            print(f"Error clearing expenses: {e}")


# This block runs the app for local development
if __name__ == '__main__':
    # We do not run migrations automatically on startup.
    # This is a manual step via the manage.sh script.
    app.run(debug=True, host='0.0.0.0', use_reloader=False)