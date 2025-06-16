# scripts/run_migrations.py
import sys
from flask_migrate import upgrade
from finance_tracker import create_app, db

# Get the database URI from the command-line argument
# sys.argv[0] is the script name, sys.argv[1] is the first argument
if len(sys.argv) < 2:
    print("Error: Database URI not provided.")
    sys.exit(1)

db_uri = sys.argv[1]

print("Migration script started...")
print(f"Using database URI (hidden password): {db_uri.split('Password=')[0]}...")

# Create a Flask app instance specifically for the migration
app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri

# The 'with app.app_context()' is crucial
with app.app_context():
    print("Applying database migrations...")
    try:
        upgrade()
        print("Migrations applied successfully.")
    except Exception as e:
        print(f"An error occurred during migration: {e}")
        sys.exit(1)

sys.exit(0)