# run.py
from finance_tracker import create_app, db

# Corrected import: We now import Transaction, not Expense.
# It's also good practice to import all models that might be used in CLI commands.
from finance_tracker.models import Transaction, User, Account
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


# This command has been updated to work with the new Transaction model.
@app.cli.command("clear-transactions")
def clear_transactions_command():
    """A custom command to clear all data from the transaction table."""
    with app.app_context():
        try:
            # The query now targets the Transaction model.
            num_deleted = db.session.query(Transaction).delete()
            db.session.commit()
            print(f"Success: Deleted {num_deleted} old transaction(s).")
        except Exception as e:
            db.session.rollback()
            print(f"Error clearing transactions: {e}")


# This block runs the app for local development
if __name__ == "__main__":
    # We do not run migrations automatically on startup.
    # This is a manual step via the manage.sh script.
    app.run(debug=True, host="0.0.0.0", use_reloader=True)
