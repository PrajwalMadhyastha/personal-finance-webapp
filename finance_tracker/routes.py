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
    
@main_bp.route('/delete/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    """Deletes an expense from the database."""
    
    # db.get_or_404() is a handy Flask-SQLAlchemy shortcut.
    # It tries to get the object by its primary key (id) or
    # automatically responds with a 404 Not Found error if it doesn't exist.
    expense_to_delete = db.get_or_404(Expense, expense_id)
    
    try:
        # Use the SQLAlchemy session to delete the object
        db.session.delete(expense_to_delete)
        # Commit the transaction to make the change permanent
        db.session.commit()
        # Send a success message to the user on the next page
        flash(f"Expense '{expense_to_delete.description}' has been deleted.", 'success')
        current_app.logger.info(f"Deleted expense ID {expense_id}")
    except Exception as e:
        # If anything goes wrong, roll back the transaction to be safe
        db.session.rollback()
        flash(f"Error deleting expense: {e}", 'error')
        current_app.logger.error(f"Error deleting expense ID {expense_id}: {e}")
        
    # Redirect the user back to the homepage to see the updated list
    return redirect(url_for('main.home'))

@main_bp.route('/edit/<int:expense_id>', methods=['GET', 'POST'])
def edit_expense(expense_id):
    """
    Handles both displaying the edit form (GET) and updating the expense (POST).
    """
    # Get the expense object from the DB or return a 404 error
    expense_to_edit = db.get_or_404(Expense, expense_id)

    # If the form is being submitted
    if request.method == 'POST':
        # Get updated data from the form
        description = request.form['description']
        amount_str = request.form['amount']
        category = request.form['category']

        # Validate the data
        if not description or not amount_str or not category:
            flash('Error: All fields are required.', 'error')
            # Redirect back to the edit page if there's an error
            return redirect(url_for('main.edit_expense', expense_id=expense_id))
        
        try:
            amount = float(amount_str)
        except ValueError:
            flash('Error: Amount must be a valid number.', 'error')
            return redirect(url_for('main.edit_expense', expense_id=expense_id))

        # Update the object's attributes with the new data
        expense_to_edit.description = description
        expense_to_edit.amount = amount
        expense_to_edit.category = category
        
        try:
            # Commit the session to save the changes to the database
            db.session.commit()
            flash(f"Expense '{expense_to_edit.description}' has been updated.", 'success')
            current_app.logger.info(f"Updated expense ID {expense_id}")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating expense: {e}", 'error')
            current_app.logger.error(f"Error updating expense ID {expense_id}: {e}")

        # Redirect back to the homepage after a successful update
        return redirect(url_for('main.home'))

    # If it's a GET request, just show the pre-populated form
    else:
        return render_template('edit_expense.html', expense=expense_to_edit, title="Edit Expense")