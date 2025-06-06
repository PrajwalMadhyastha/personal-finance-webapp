# app.py
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# --- Configuration and Initialization ---

# 1. Initialize the Flask application
app = Flask(__name__)

# 2. Configure SQLAlchemy
# The URI specifies the database engine (sqlite) and path (/// for relative path).
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
# This is optional but suppresses a warning and is good practice.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 3. Initialize the SQLAlchemy object, linking it to our Flask app
db = SQLAlchemy(app)

# --- Database Model Definition ---

# 4. Define the Expense model class directly in app.py.
# As you correctly noted, this avoids a circular import issue for now.
# In larger apps, this is often handled with an "Application Factory" pattern.
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        # A developer-friendly representation of the object.
        return f'<Expense ID: {self.id}, Desc: {self.description}>'

# --- Flask Routes (Refactored to use SQLAlchemy) ---

@app.route('/')
def home():
    """Renders the homepage and displays expenses queried via SQLAlchemy."""
    # 5. Query the database using the Expense model.
    # 'Expense.query' is the base for all queries.
    # '.order_by()' sorts the results.
    # '.all()' executes the query and returns all results as a list of objects.
    expenses = Expense.query.order_by(Expense.timestamp.desc()).all()
    
    # The 'expenses' variable is now a list of Expense objects.
    # The template `index.html` works without changes because Jinja2 can access
    # object attributes (e.g., `expense.description`) with the same dot notation.
    return render_template('index.html', expenses=expenses)

@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    """Handles both displaying the form and adding a new expense via SQLAlchemy."""
    if request.method == 'POST':
        description = request.form['description']
        amount_str = request.form['amount']
        category = request.form['category']

        if not description or not amount_str or not category:
            return "Error: All fields are required.", 400

        try:
            amount = float(amount_str)
        except ValueError:
            return "Error: Amount must be a valid number.", 400

        # 6. Create an Expense object and add it to the database session.
        new_expense = Expense(description=description, amount=amount, category=category)
        
        # The 'db.session' is like a staging area for your database changes.
        db.session.add(new_expense) # Add the new object to the session.
        db.session.commit()         # Commit the session to write the changes to the DB.

        return redirect(url_for('home'))
    else:
        # For a GET request, just show the form
        return render_template('add_expense_form.html')

# This block is for running the app directly
if __name__ == '__main__':
    # NOTE: The db.create_all() is now done from the command line, not here.
    # The old init_db() function is no longer needed and should be deleted.
    app.run(debug=True)