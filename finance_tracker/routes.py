# finance_tracker/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from .models import Expense
from . import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """Renders the homepage and displays expenses."""
    current_app.logger.debug("Home page accessed.") # Use DEBUG for verbose, developer-level info
    expenses = Expense.query.order_by(Expense.timestamp.desc()).all()
    return render_template('index.html', expenses=expenses)

@main_bp.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        description = request.form['description']
        amount_str = request.form['amount']
        category = request.form['category']

        if not description or not amount_str or not category:
            current_app.logger.warning("Form validation failed: a required field was missing.") # Use WARNING for potential problems
            flash('Error: All fields are required.', 'error')
            return redirect(url_for('main.add_expense'))

        try:
            amount = float(amount_str)
        except ValueError:
            current_app.logger.warning(f"Form validation failed: invalid amount entered ('{amount_str}').")
            flash('Error: Amount must be a valid number.', 'error')
            return redirect(url_for('main.add_expense'))

        new_expense = Expense(description=description, amount=amount, category=category)
        
        try:
            db.session.add(new_expense)
            db.session.commit()
            # Use INFO for successful, normal operations
            current_app.logger.info(f"New expense added: '{new_expense.description}' for amount {new_expense.amount}")
            flash(f"Expense '{new_expense.description}' was added successfully!", 'success')
        except Exception as e:
            # Use ERROR for failures that prevent an operation from completing
            current_app.logger.error(f"Failed to add new expense to database: {e}")
            flash('Error: Failed to save expense to the database.', 'error')

        return redirect(url_for('main.home'))
    else:
        current_app.logger.debug("Add expense form page accessed.")
        return render_template('add_expense_form.html')