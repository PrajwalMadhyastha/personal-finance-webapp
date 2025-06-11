# finance_tracker/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from .models import Expense, User, Category, Income
from datetime import date, datetime, timedelta
from . import db
from sqlalchemy import func, extract
from collections import defaultdict
from urllib.parse import urlparse

main_bp = Blueprint('main', __name__)

@main_bp.route('/reports')
@login_required
def reports():
    """Renders a page with monthly expense reports grouped by category."""
    current_app.logger.info(f"User {current_user.username} accessed reports page.")

    # The SQLAlchemy query remains the same
    year_expr = extract('year', Expense.timestamp)
    month_expr = extract('month', Expense.timestamp)
    sum_expr = func.sum(Expense.amount)

    monthly_data_query = db.session.query(
        year_expr.label('year'),
        month_expr.label('month'),
        Category.name.label('category_name'),
        sum_expr.label('total_amount')
    ).join(Category).filter(
        Expense.owner == current_user
    ).group_by(
        year_expr,
        month_expr,
        Category.name
    ).order_by(
        db.desc(year_expr),
        db.desc(month_expr)
    ).all()

    # --- THIS LOGIC IS CHANGED ---
    # Process the results into a nested dictionary with a formatted month name as the key
    monthly_summary = defaultdict(list)
    for row in monthly_data_query:
        # Create a Python datetime object from the year and month
        month_object = datetime(year=row.year, month=row.month, day=1)
        # Format it into a user-friendly string like "June 2025"
        month_key = month_object.strftime('%B %Y')
        monthly_summary[month_key].append((row.category_name, row.total_amount))

    return render_template('reports.html', monthly_summary=monthly_summary)

@main_bp.route('/expenses')
@login_required
def expenses_list():
    """Renders the paginated list of all expenses for the current user."""
    # Get the current page number from the URL's query string (e.g., /expenses?page=2)
    # Default to page 1 if not specified, and ensure it's an integer.
    page = request.args.get('page', 1, type=int)
    
    # Instead of .all(), we use .paginate().
    # This creates a pagination object. We'll show 10 items per page.
    expenses_pagination = Expense.query.filter_by(
        owner=current_user
    ).order_by(
        Expense.timestamp.desc()
    ).paginate(
        page=page, per_page=10, error_out=False
    )
    
    # We pass this pagination object directly to the template.
    return render_template('expenses.html', expenses_pagination=expenses_pagination)

@main_bp.route('/profile')
@login_required
def profile():
    """Renders the user profile page."""
    return render_template('profile.html', title="User Profile")


@main_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    """Processes the change password form submission."""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_new_password = request.form.get('confirm_new_password')

    # 1. Verify the user's current password is correct
    if not current_user.check_password(current_password):
        flash('Your current password was incorrect. Please try again.', 'error')
        return redirect(url_for('main.profile'))

    # 2. Verify the new password and confirmation match
    if new_password != confirm_new_password:
        flash('The new password and confirmation password do not match.', 'error')
        return redirect(url_for('main.profile'))
    
    # Optional: Add password strength validation here if desired
    if len(new_password) < 8:
        flash('New password must be at least 8 characters long.', 'error')
        return redirect(url_for('main.profile'))

    # 3. If all checks pass, set the new password and save it
    try:
        current_user.set_password(new_password)
        db.session.commit()
        flash('Your password has been updated successfully.', 'success')
        current_app.logger.info(f"User {current_user.username} successfully changed their password.")
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while updating your password. Please try again.', 'error')
        current_app.logger.error(f"Error changing password for user {current_user.username}: {e}")

    return redirect(url_for('main.profile'))

@main_bp.route('/edit_income/<int:income_id>', methods=['GET', 'POST'])
@login_required
def edit_income(income_id):
    """Handles editing an existing income record."""
    income_to_edit = db.get_or_404(Income, income_id)
    
    # Crucial security check: ensure the user owns this income record
    if income_to_edit.owner != current_user:
        abort(403) # Forbidden

    if request.method == 'POST':
        income_to_edit.description = request.form.get('description')
        income_to_edit.amount = float(request.form.get('amount'))
        
        db.session.commit()
        flash('Income record updated successfully!', 'success')
        return redirect(url_for('main.view_incomes'))

    # For a GET request, show the pre-populated form
    return render_template('edit_income.html', income=income_to_edit)


@main_bp.route('/delete_income/<int:income_id>', methods=['POST'])
@login_required
def delete_income(income_id):
    """Deletes an income record."""
    income_to_delete = db.get_or_404(Income, income_id)

    # Crucial security check
    if income_to_delete.owner != current_user:
        abort(403)
    
    db.session.delete(income_to_delete)
    db.session.commit()
    flash(f"Income record '{income_to_delete.description}' has been deleted.", 'success')
    return redirect(url_for('main.view_incomes'))

@main_bp.route('/incomes')
@login_required
def view_incomes():
    """Renders a page listing all incomes for the current user."""
    incomes = Income.query.filter_by(owner=current_user).order_by(Income.timestamp.desc()).all()
    return render_template('incomes.html', incomes=incomes)

@main_bp.route('/add_income', methods=['GET', 'POST'])
@login_required
def add_income():
    """Handles adding a new income record."""
    if request.method == 'POST':
        description = request.form.get('description')
        amount_str = request.form.get('amount')

        if not description or not amount_str:
            flash('Error: All fields are required.', 'error')
            return redirect(url_for('main.add_income'))
        
        try:
            amount = float(amount_str)
            if amount <= 0:
                flash('Error: Amount must be a positive number.', 'error')
                return redirect(url_for('main.add_income'))
        except ValueError:
            flash('Error: Amount must be a valid number.', 'error')
            return redirect(url_for('main.add_income'))

        new_income = Income(description=description, amount=amount, owner=current_user)
        db.session.add(new_income)
        db.session.commit()
        flash('Income record added successfully!', 'success')
        return redirect(url_for('main.view_incomes'))

    # For a GET request, just show the form
    return render_template('add_income_form.html')

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
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
    
    if not start_date_str or not end_date_str:
        start_date, end_date = get_month_range()
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    # --- THIS SECTION IS UPDATED ---
    
    # 1. Calculate Total Expenses for the period
    user_expenses_query = db.session.query(Expense).filter(
        Expense.owner == current_user,
        Expense.timestamp.between(start_date, end_date + timedelta(days=1))
    )
    total_expenses = user_expenses_query.with_entities(func.sum(Expense.amount)).scalar() or 0.0

    # 2. Calculate Total Income for the period
    user_incomes_query = db.session.query(Income).filter(
        Income.owner == current_user,
        Income.timestamp.between(start_date, end_date + timedelta(days=1))
    )
    total_income = user_incomes_query.with_entities(func.sum(Income.amount)).scalar() or 0.0

    # 3. Calculate Net Balance
    net_balance = total_income - total_expenses
    
    # We no longer need these queries here as they are handled by the API and other pages
    # total_expense_count = user_expenses_query.count()
    # recent_expense = user_expenses_query.order_by(Expense.timestamp.desc()).first()

    # 4. Pass the new values to the template
    return render_template(
        'dashboard.html',
        total_income=total_income,
        total_expenses=total_expenses,
        net_balance=net_balance,
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