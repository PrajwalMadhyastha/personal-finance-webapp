# finance_tracker/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash # Import flash
from .models import Expense
from . import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    expenses = Expense.query.order_by(Expense.timestamp.desc()).all()
    return render_template('index.html', expenses=expenses)

@main_bp.route('/add_expense', methods=['GET', 'POST'])
def add_expense(): # Renamed function to match endpoint
    if request.method == 'POST':
        description = request.form['description']
        amount_str = request.form['amount']
        category = request.form['category']

        if not description or not amount_str or not category:
            flash('Error: All fields are required.', 'error') # Flash an error message
            return redirect(url_for('main.add_expense'))

        try:
            amount = float(amount_str)
        except ValueError:
            flash('Error: Amount must be a valid number.', 'error') # Flash an error message
            return redirect(url_for('main.add_expense'))

        new_expense = Expense(description=description, amount=amount, category=category)
        db.session.add(new_expense)
        db.session.commit()
        
        # ADD THIS LINE: Flash a success message to the user.
        # The second argument is a "category," which we use in the HTML for styling.
        flash(f"Expense '{new_expense.description}' was added successfully!", 'success')
        
        return redirect(url_for('main.home'))
    else:
        return render_template('add_expense_form.html')