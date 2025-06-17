# wsgi.py

from finance_tracker import create_app

# The Gunicorn server will look for this 'app' variable by default.
app = create_app()
