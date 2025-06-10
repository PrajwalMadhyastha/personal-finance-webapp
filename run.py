# run.py
from finance_tracker import create_app

# The create_app function handles all application setup.
app = create_app()

# This block runs the app for local development.
# All database tasks are now handled explicitly via the manage.sh script.
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', use_reloader=False)