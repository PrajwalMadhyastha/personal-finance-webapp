from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import db
import decimal
from collections import defaultdict
from datetime import datetime
# --- CORRECTED IMPORTS ---
# We now import the new Transaction and Account models
from .models import Transaction, User, Category, Account

# We can keep the blueprint name the same
main_bp = Blueprint('main', __name__)

@main_bp.route('/reports')
@login_required
def reports():
    """
    Generates data for and renders the monthly expense reports page.
    """
    # Fetch all expense transactions for the user
    expenses = Transaction.query.filter_by(
        user_id=current_user.id,
        transaction_type='expense'
    ).order_by(Transaction.transaction_date.desc()).all()

    # Use defaultdict to easily group expenses
    # Structure: { '2025-06': { 'Bills': 150.00, 'Food': 200.00 }, ... }
    monthly_summary_raw = defaultdict(lambda: defaultdict(float))

    for expense in expenses:
        # Format date to 'YYYY-MM, Month Name' for sorting and display
        month_key = expense.transaction_date.strftime('%Y-%m')
        
        if not expense.categories:
             # Handle uncategorized expenses
             category_name = 'Uncategorized'
             monthly_summary_raw[month_key][category_name] += float(expense.amount)
        else:
            # Add amount to each category associated with the expense
            for category in expense.categories:
                monthly_summary_raw[month_key][category.name] += float(expense.amount)

    # Convert the raw summary to the sorted list format the template expects
    # Structure: { 'June 2025': [('Food', 200.00), ('Bills', 150.00)], ... }
    monthly_summary_final = {}
    # Sort months chronologically
    for month_key in sorted(monthly_summary_raw.keys(), reverse=True):
        # Format month key for display
        month_name = datetime.strptime(month_key, '%Y-%m').strftime('%B %Y')
        # Sort categories by total amount for that month
        sorted_categories = sorted(monthly_summary_raw[month_key].items(), key=lambda item: item[1], reverse=True)
        monthly_summary_final[month_name] = sorted_categories

    return render_template('reports.html', monthly_summary=monthly_summary_final)

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    Handles displaying user profile and processing password changes.
    """
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_new_password = request.form.get('confirm_new_password')

        # Use the bcrypt object from our app factory (__init__.py)
        from . import bcrypt 

        # Verify current password
        if not bcrypt.check_password_hash(current_user.password_hash, current_password):
            flash('Your current password was incorrect. Please try again.', 'error')
            return redirect(url_for('main.profile'))
        
        # Verify new password confirmation
        if new_password != confirm_new_password:
            flash('The new passwords do not match.', 'error')
            return redirect(url_for('main.profile'))

        # Update to the new password
        current_user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()

        flash('Your password has been updated successfully!', 'success')
        return redirect(url_for('main.profile'))

    # For a GET request, just render the page
    return render_template('profile.html')

@main_bp.route('/categories', methods=['GET', 'POST'])
@login_required
def manage_categories():
    """
    Handles viewing and adding new categories.
    """
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            # Prevent duplicate categories for the same user
            existing_category = Category.query.filter(
                db.func.lower(Category.name) == db.func.lower(name),
                Category.user_id == current_user.id
            ).first()

            if not existing_category:
                new_category = Category(name=name, user_id=current_user.id)
                db.session.add(new_category)
                db.session.commit()
                flash('Category added successfully!', 'success')
            else:
                flash('A category with that name already exists.', 'warning')
        else:
            flash('Category name cannot be empty.', 'error')
        
        return redirect(url_for('main.manage_categories'))

    # For a GET request, display all user's categories
    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    return render_template('categories.html', categories=categories)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Logic now fetches transactions and accounts for the current user
    user_accounts = Account.query.filter_by(user_id=current_user.id).all()
    
    # Fetch recent transactions
    recent_transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.transaction_date.desc()).limit(10).all()

    return render_template('dashboard.html', accounts=user_accounts, transactions=recent_transactions)

# --- NEW UNIFIED TRANSACTION ROUTES ---

@main_bp.route('/transactions')
@login_required
def transactions():
    """Display a list of all transactions (both income and expense)."""
    page = request.args.get('page', 1, type=int)
    # Query the unified Transaction model
    all_transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(Transaction.transaction_date.desc())\
        .paginate(page=page, per_page=10)
    return render_template('transactions.html', transactions=all_transactions)

@main_bp.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    """A single route to add either an income or an expense."""
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()

    if not accounts:
        flash('You must create an account before you can add a transaction.', 'warning')
        return redirect(url_for('main.add_account'))

    if request.method == 'POST':
        # Convert form data to correct types
        amount = decimal.Decimal(request.form.get('amount'))
        trans_type = request.form.get('transaction_type')
        description = request.form.get('description')
        account_id = int(request.form.get('account_id'))
        category_id = request.form.get('category_id')
        notes = request.form.get('notes')
        
        # Create a new Transaction object
        new_transaction = Transaction(
            amount=amount,
            transaction_type=trans_type,
            description=description,
            notes=notes,
            user_id=current_user.id,
            account_id=account_id
        )

        if category_id:
            category = Category.query.get(category_id)
            if category:
                new_transaction.categories.append(category)

        # --- THIS IS THE NEW LOGIC ---
        # Fetch the associated account and update its balance
        account = Account.query.get(account_id)
        if account:
            if new_transaction.transaction_type == 'income':
                account.balance += amount
            else:  # 'expense'
                account.balance -= amount
        # --- END OF NEW LOGIC ---

        db.session.add(new_transaction)
        db.session.commit()
        flash(f'{trans_type.capitalize()} added successfully!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('add_transaction.html', accounts=accounts, categories=categories)


@main_bp.route('/edit_transaction/<int:transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    if transaction.user_id != current_user.id:
        flash('You do not have permission to edit this transaction.', 'danger')
        return redirect(url_for('main.transactions'))
    
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()

    if request.method == 'POST':
        # --- THIS IS THE NEW LOGIC ---
        # Store original values before they are changed
        original_amount = transaction.amount
        original_type = transaction.transaction_type
        original_account = transaction.account

        # Revert the original transaction from the original account's balance
        if original_account:
            if original_type == 'income':
                original_account.balance -= original_amount
            else:
                original_account.balance += original_amount
        # --- END OF REVERSAL LOGIC ---

        # Update transaction with new form data
        transaction.amount = decimal.Decimal(request.form.get('amount'))
        transaction.transaction_type = request.form.get('transaction_type')
        transaction.description = request.form.get('description')
        transaction.account_id = int(request.form.get('account_id'))
        transaction.notes = request.form.get('notes')
        
        # --- APPLY NEW TRANSACTION LOGIC ---
        # Get the new account and apply the updated transaction
        new_account = Account.query.get(transaction.account_id)
        if new_account:
            if transaction.transaction_type == 'income':
                new_account.balance += transaction.amount
            else:
                new_account.balance -= transaction.amount
        # --- END OF APPLY LOGIC ---
        
        # Handle category update
        category_id = request.form.get('category_id')
        transaction.categories.clear()
        if category_id:
            category = Category.query.get(category_id)
            if category:
                transaction.categories.append(category)

        db.session.commit()
        flash('Transaction updated successfully!', 'success')
        return redirect(url_for('main.transactions'))

    return render_template('edit_transaction.html', transaction=transaction, accounts=accounts, categories=categories)


@main_bp.route('/delete_transaction/<int:transaction_id>', methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    if transaction.user_id != current_user.id:
        flash('You do not have permission to delete this transaction.', 'danger')
        return redirect(url_for('main.transactions'))

    # --- THIS IS THE NEW LOGIC ---
    # Find the account and reverse the transaction's effect
    account = transaction.account
    if account:
        if transaction.transaction_type == 'income':
            account.balance -= transaction.amount  # Subtract the income
        else:  # 'expense'
            account.balance += transaction.amount  # Add back the expense
    # --- END OF NEW LOGIC ---
        
    db.session.delete(transaction)
    db.session.commit()
    flash('Transaction deleted successfully!', 'success')
    return redirect(url_for('main.transactions'))

# --- NEW ACCOUNT MANAGEMENT ROUTES ---

@main_bp.route('/accounts')
@login_required
def accounts():
    user_accounts = Account.query.filter_by(user_id=current_user.id).all()
    return render_template('accounts.html', accounts=user_accounts)

@main_bp.route('/add_account', methods=['GET', 'POST'])
@login_required
def add_account():
    if request.method == 'POST':
        name = request.form.get('name')
        acc_type = request.form.get('account_type')
        balance = request.form.get('balance', 0)

        new_account = Account(
            name=name,
            account_type=acc_type,
            balance=balance,
            user_id=current_user.id
        )
        db.session.add(new_account)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('main.accounts'))
    
    return render_template('add_account.html')

from flask_login import login_user, logout_user, login_required, current_user
from .models import User
from . import db, bcrypt
import csv
import io
from flask import Response, jsonify

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_by_email = User.query.filter_by(email=email).first()
        if user_by_email:
            flash('Email address already in use.', 'error')
            return redirect(url_for('main.register'))

        user_by_name = User.query.filter_by(username=username).first()
        if user_by_name:
            flash('Username already taken.', 'error')
            return redirect(url_for('main.register'))

        new_user = User(
            username=username,
            email=email,
            password_hash=bcrypt.generate_password_hash(password).decode('utf-8')
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html')


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('Login failed. Please check your email and password.', 'error')

    return render_template('login.html')


@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index'))


# --- REPORTING AND API ROUTES ---

@main_bp.route('/export-transactions')
@login_required
def export_transactions():
    """Exports all user transactions to a CSV file."""
    
    # Use an in-memory string buffer
    string_io = io.StringIO()
    csv_writer = csv.writer(string_io)
    
    # Header Row
    csv_writer.writerow(['Date', 'Description', 'Amount', 'Type', 'Account', 'Category', 'Notes'])
    
    # Data Rows
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.transaction_date).all()
    for t in transactions:
        category_names = ', '.join([c.name for c in t.categories])
        csv_writer.writerow([
            t.transaction_date.strftime('%Y-%m-%d'),
            t.description,
            t.amount,
            t.transaction_type,
            t.account.name,
            category_names,
            t.notes
        ])
        
    # Prepare response
    output = string_io.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition":
                 "attachment; filename=transactions.csv"})


@main_bp.route('/api/transaction-summary')
@login_required
def transaction_summary_api():
    """API endpoint to provide data for dashboard charts."""
    
    # This is a placeholder for a more advanced chart. 
    # For now, let's provide expense breakdown by category.
    summary = db.session.query(
        Category.name,
        db.func.sum(Transaction.amount)
    ).join(Transaction.categories).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == 'expense'
    ).group_by(Category.name).all()
    
    labels = [row[0] for row in summary]
    data = [float(row[1]) for row in summary]
    
    return jsonify({'labels': labels, 'data': data})