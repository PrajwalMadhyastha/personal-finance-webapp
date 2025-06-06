# run.py
from finance_tracker import create_app

# Call the factory function to create the app instance.
app = create_app()

# This block allows you to run the app by executing 'python run.py'
if __name__ == '__main__':
    # Make sure to run db.create_all() from the terminal first!
    app.run(debug=True)