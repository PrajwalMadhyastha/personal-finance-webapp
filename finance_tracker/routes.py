# finance_tracker/routes.py
from flask import Blueprint, render_template, request, redirect, url_for
from .models import Expense
from . import db  # Import the db instance from the package

# A Blueprint is a way to organize a group of related views and other code.
# The first argument, 'main', is the Blueprint's name.
# The second argument, __name__, tells the Blueprint where it's defined.
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """Renders the homepage and displays expenses."""
    expenses = Expense.query.order_by(Expense.timestamp.desc()).all()
    return render_template('index.html', expenses=expenses)

@main_bp.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    """Handles adding a new expense."""
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

        new_expense = Expense(description=description, amount=amount, category=category)
        db.session.add(new_expense)
        db.session.commit()
        return redirect(url_for('main.home')) # Note: 'main.home' refers to the 'home' function in the 'main' blueprint
    else:
        return render_template('add_expense_form.html')