# app.py
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

# We no longer need the User/Expense classes for this simplified DB interaction,
# nor the JSON file handlers. This makes the app script cleaner.
# from finance_tracker.models import Expense, User

# ==============================================================================
# Database Initialization
# ==============================================================================

def init_db():
    """
    Initializes the database and creates the 'expenses' table if it doesn't exist.
    """
    # sqlite3.connect() creates the file if it doesn't exist.
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    
    # Use IF NOT EXISTS to prevent an error if the table already exists.
    # This makes the function safe to run every time the app starts.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    
    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

# ==============================================================================
# Flask App Initialization and Routes
# ==============================================================================

app = Flask(__name__)

@app.route('/')
def home():
    """Renders the homepage and displays the list of all expenses from the database."""
    conn = sqlite3.connect('finance.db')
    # This line allows us to access columns by name, which is more readable.
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, description, amount, category, timestamp FROM expenses ORDER BY timestamp DESC")
    # .fetchall() retrieves all rows from the query result.
    expenses_from_db = cursor.fetchall()
    
    conn.close()
    
    # The database returns a list of sqlite3.Row objects, which act like dictionaries.
    # So, we can pass them directly to the template!
    # The 'index.html' template can still use `expense.description`, `expense.amount`, etc.
    return render_template('index.html', expenses=expenses_from_db)

@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    """Handles both displaying the form (GET) and adding a new expense to the DB (POST)."""
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

        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()
        
        # Use parameterized queries (?) to prevent SQL injection attacks.
        # This is the secure way to insert data.
        cursor.execute(
            "INSERT INTO expenses (description, amount, category, timestamp) VALUES (?, ?, ?, ?)",
            (description, amount, category, datetime.now().isoformat())
        )
        
        conn.commit()
        conn.close()

        # Redirect back to the homepage to see the newly added expense
        return redirect(url_for('home'))
    else:
        # For a GET request, just show the form
        return render_template('add_expense_form.html')

# This block runs the app
if __name__ == '__main__':
    # Initialize the database once when the app starts
    init_db()
    app.run(debug=True)