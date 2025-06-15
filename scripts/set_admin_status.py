# scripts/set_admin_status.py

import sys
import os
from dotenv import load_dotenv

# This configuration allows the script to find and import your Flask app
# from anywhere in the project, which is crucial for loading the app context.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
load_dotenv(os.path.join(project_root, '.env'))

# Now we can import the app components
from finance_tracker import create_app, db
from finance_tracker.models import User

def set_admin_status(email, is_admin_status):
    """
    Finds a user by email and sets their admin status within the app context.
    """
    app = create_app()
    with app.app_context():
        # Find the user by their email address
        user = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
        
        if not user:
            print(f"Error: User with email '{email}' not found.", file=sys.stderr)
            sys.exit(1)
            
        # Update the is_admin flag and commit the change
        user.is_admin = is_admin_status
        db.session.commit()
        
        status_text = "promoted to admin" if is_admin_status else "demoted to regular user"
        print(f"Success: User '{user.username}' ({user.email}) has been {status_text}.")

if __name__ == "__main__":
    # This script expects exactly two command-line arguments: email and status
    if len(sys.argv) != 3:
        print("Usage: python set_admin_status.py <email> <true|false>", file=sys.stderr)
        sys.exit(1)
        
    user_email = sys.argv[1]
    status_str = sys.argv[2].lower()
    
    if status_str not in ['true', 'false']:
        print("Error: Status must be 'true' or 'false'.", file=sys.stderr)
        sys.exit(1)
        
    is_admin = (status_str == 'true')
    
    set_admin_status(user_email, is_admin)