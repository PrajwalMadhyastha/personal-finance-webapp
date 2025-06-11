# finance_tracker/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from .models import Expense, User, Category
from datetime import date, datetime, timedelta
from . import db
from sqlalchemy import func
from urllib.parse import urlparse

main_bp = Blueprint('main', __name__)

def get_month_range(today=None):
    """Returns the first and last day of the current month."""
    if not today:
        today = date.today()
    first_day = today.replace(day=1)
    # Find the first day of the next month, then subtract one day
    next_month = first_day.replace(month=first_day.month % 12 + 1, year=first_day.year + (first_day.month // 12))
    last_day = next_month - timedelta(days=1)
    return first_day, last_day

@main_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    """Renders the main dashboard with summary statistics for a given date range."""
    
    start_date_str, end_date_str = None, None

    if request.method == 'POST':
        # Get dates from the submitted form
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
    
    # If it's a GET request or the form wasn't submitted, use the current month as default
    if not start_date_str or not end_date_str:
        start_date, end_date = get_month_range()
    else:
        # Convert form strings to datetime objects
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    # Base query for the current user's expenses within the date range
    user_expenses_query = db.session.query(Expense).filter(
        Expense.owner == current_user,
        Expense.timestamp.between(start_date, end_date + timedelta(days=1))
    )
    
    total_expense_count = user_expenses_query.count()
    total_spent = user_expenses_query.with_entities(func.sum(Expense.amount)).scalar() or 0.0
    recent_expense = user_expenses_query.order_by(Expense.timestamp.desc()).first()

    return render_template(
        'dashboard.html',
        total_expense_count=total_expense_count,
        total_spent=total_spent,
        recent_expense=recent_expense,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat()
    )


# --- UPDATE: The old home route now just redirects to the dashboard ---
@main_bp.route('/')
@login_required
def home():
    """Redirects to the main dashboard."""
    return redirect(url_for('main.dashboard'))

# --- Expense Routes ---

@main_bp.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    """Handles adding a new expense."""
    categories = Category.query.filter_by(creator=current_user).order_by(Category.name).all()
    
    if request.method == 'POST':
        description = request.form.get('description')
        amount_str = request.form.get('amount')
        category_id = request.form.get('category_id')

        if not all([description, amount_str, category_id]):
            flash('Error: All fields are required.', 'error')
            return render_template('add_expense_form.html', categories=categories)
        
        try:
            amount = float(amount_str)
        except ValueError:
            flash('Error: Amount must be a valid number.', 'error')
            return render_template('add_expense_form.html', categories=categories)
        
        new_expense = Expense(description=description, amount=amount, category_id=category_id, owner=current_user)
        db.session.add(new_expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('main.home'))

    return render_template('add_expense_form.html', categories=categories)


@main_bp.route('/edit/<int:expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    """Handles editing an existing expense."""
    expense_to_edit = db.get_or_404(Expense, expense_id)
    if expense_to_edit.owner != current_user:
        abort(403)

    categories = Category.query.filter_by(creator=current_user).order_by(Category.name).all()

    if request.method == 'POST':
        expense_to_edit.description = request.form.get('description')
        expense_to_edit.amount = float(request.form.get('amount'))
        expense_to_edit.category_id = request.form.get('category_id')
        db.session.commit()
        flash('Expense updated successfully!', 'success')
        return redirect(url_for('main.home'))
    
    return render_template('edit_expense.html', expense=expense_to_edit, categories=categories)


@main_bp.route('/delete/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    """Deletes an expense."""
    expense_to_delete = db.get_or_404(Expense, expense_id)
    
    if expense_to_delete.owner != current_user:
        abort(403)
        
    db.session.delete(expense_to_delete)
    db.session.commit()
    flash(f"Expense '{expense_to_delete.description}' has been deleted.", 'success')
    return redirect(url_for('main.home'))

# --- Category Management Route ---

@main_bp.route('/categories', methods=['GET', 'POST'])
@login_required
def manage_categories():
    """Handles creating and listing expense categories."""
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            existing_category = Category.query.filter_by(name=name, creator=current_user).first()
            if not existing_category:
                new_category = Category(name=name, creator=current_user)
                db.session.add(new_category)
                db.session.commit()
                flash(f"Category '{name}' added.", 'success')
            else:
                flash(f"Category '{name}' already exists.", 'error')
        return redirect(url_for('main.manage_categories'))

    categories = Category.query.filter_by(creator=current_user).order_by(Category.name).all()
    return render_template('categories.html', categories=categories)


# --- Authentication Routes ---

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            
            # Now, get the 'next' URL from the hidden form field
            next_page = request.form.get('next')
            
            # --- SECURITY CHECK ---
            # It's important to validate the redirect URL to prevent attackers
            # from redirecting users to malicious sites. This simple check
            # ensures the redirect stays within our own application.
            if next_page and urlparse(next_page).netloc == '':
                return redirect(next_page)
            else:
                return redirect(url_for('main.dashboard'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'error')

    next_page = request.args.get('next')
    return render_template('login.html', title="Log In", next_page=next_page)


@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))


@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('main.register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('main.register'))
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash(f"Account created for {username}! You can now log in.", 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', title="Register")

@main_bp.route('/api/expense_summary')
@login_required
def expense_summary_api():
    """Provides expense summary data as JSON for a given date range."""
    # Get date range from URL query parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    # Default to current month if no dates are provided
    if not start_date_str or not end_date_str:
        start_date, end_date = get_month_range()
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    # The query now filters by date range
    summary_query = db.session.query(
        Category.name,
        func.sum(Expense.amount).label('total_amount')
    ).join(Expense).filter(
        Expense.owner == current_user,
        Expense.timestamp.between(start_date, end_date + timedelta(days=1))
    ).group_by(Category.name).order_by(
        func.sum(Expense.amount).desc()
    ).all()
    
    labels = [row[0] for row in summary_query]
    data = [float(row[1]) for row in summary_query]
    
    return jsonify({"labels": labels, "data": data})