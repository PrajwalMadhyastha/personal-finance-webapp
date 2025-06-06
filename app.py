# app.py
from flask import Flask, render_template, request, redirect, url_for
import json
from finance_tracker.models import Expense, RecurringExpense, User # Assuming models.py is in finance_tracker/

# ==============================================================================
# File Handling Functions (Defined directly in the app script for simplicity)
# ==============================================================================

def save_expenses_to_file(user_object, filename="user_expenses.json"):
    """
    Saves the expenses of a given User object to a JSON file.
    """
    # Use a list comprehension to convert all expense objects to dictionaries
    expenses_as_dicts = [expense_obj.to_dict() for expense_obj in user_object.expenses]
    try:
        with open(filename, "w") as f:
            json.dump(expenses_as_dicts, f, indent=4)
    except IOError:
        # In a real app, you'd want more sophisticated logging here
        print(f"Error: Could not save expenses to {filename}")
    except TypeError as e:
        print(f"Error serializing expenses to JSON: {e}")

def load_expenses_from_file(filename="user_expenses.json"):
    """
    Loads expenses from a JSON file, returning a list of Expense/RecurringExpense objects.
    """
    loaded_expense_objects = []
    try:
        with open(filename, "r") as f:
            # Handle empty file case
            content = f.read()
            if not content:
                return []
            data = json.loads(content) # Use json.loads on the content
            
            for expense_dict in data:
                expense_type = expense_dict.get("expense_type")
                description = expense_dict.get("description")
                amount = float(expense_dict.get("amount", 0))
                category = expense_dict.get("category")
                timestamp = expense_dict.get("timestamp")

                if expense_type == RecurringExpense.EXPENSE_TYPE:
                    recurrence_period = expense_dict.get("recurrence_period")
                    expense_obj = RecurringExpense(description, amount, category, recurrence_period, timestamp)
                else: # Default to standard Expense if type is missing or "STANDARD"
                    expense_obj = Expense(description, amount, category, timestamp)
                loaded_expense_objects.append(expense_obj)
                
    except FileNotFoundError:
        return [] # It's normal for the file not to exist on first run.
    except (json.JSONDecodeError, TypeError):
        print(f"Warning: Could not decode {filename}. Starting with no expenses.")
        return [] # Return empty list if file is corrupted or not in the correct format.
    return loaded_expense_objects

# ==============================================================================
# Flask App Initialization and Routes
# ==============================================================================

# Initialize the Flask application
app = Flask(__name__)

# Define a constant for our data file to ensure consistency
USER_EXPENSES_FILE = "user_expenses.json"

@app.route('/')
def home():
    """Renders the homepage and displays the list of all expenses."""
    expenses_list = load_expenses_from_file(USER_EXPENSES_FILE)
    return render_template('index.html', expenses=expenses_list)

@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    """Handles both displaying the expense form (GET) and processing its submission (POST)."""
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

        existing_expenses = load_expenses_from_file(USER_EXPENSES_FILE)
        new_expense = Expense(description=description, amount=amount, category=category)
        
        # We need a temporary User object to use our existing save logic
        temp_user = User("temp_user")
        temp_user.expenses = existing_expenses
        temp_user.add_expense(new_expense) # This method also prints a console confirmation
        
        save_expenses_to_file(temp_user, USER_EXPENSES_FILE)

        return redirect(url_for('home'))
    else:
        # This is a GET request, so just show the form
        return render_template('add_expense_form.html')

# This block runs the app
if __name__ == '__main__':
    app.run(debug=True)