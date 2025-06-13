# ===================================================================
# IMPORTS (CONSOLIDATED AND COMPLETE)
# ===================================================================
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, 
    abort, jsonify, Response
)
from flask_login import login_user, logout_user, login_required, current_user
from . import db, bcrypt
import decimal
import csv
import io
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from .models import Transaction, User, Category, Account, Budget, Tag, transaction_categories
from sqlalchemy import func, select, or_
from sqlalchemy.orm import selectinload
import calendar

main_bp = Blueprint('main', __name__)

# ===================================================================
# CORE ROUTES (INDEX & DASHBOARD)
# ===================================================================

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    accounts_stmt = select(Account).filter_by(user_id=current_user.id)
    user_accounts = db.session.execute(accounts_stmt).scalars().all()
    
    trans_stmt = select(Transaction).options(selectinload(Transaction.categories), selectinload(Transaction.tags)).filter_by(user_id=current_user.id).order_by(Transaction.transaction_date.desc()).limit(10)
    recent_transactions = db.session.execute(trans_stmt).scalars().all()

    now_utc = datetime.now(timezone.utc)
    current_month = now_utc.month
    current_year = now_utc.year

    current_budgets_stmt = select(Budget).filter_by(user_id=current_user.id, month=current_month, year=current_year)
    current_budgets = db.session.execute(current_budgets_stmt).scalars().all()
    
    expenses_by_category_stmt = select(
        transaction_categories.c.category_id, func.sum(Transaction.amount)
    ).join(
        Transaction, Transaction.id == transaction_categories.c.transaction_id
    ).where(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == 'expense',
        func.extract('month', Transaction.transaction_date) == current_month,
        func.extract('year', Transaction.transaction_date) == current_year
    ).group_by(transaction_categories.c.category_id)
    
    spending_by_category = {row[0]: row[1] for row in db.session.execute(expenses_by_category_stmt).all()}

    budget_progress_data = []
    for budget in current_budgets:
        total_spent = spending_by_category.get(budget.category_id, decimal.Decimal(0))
        percentage_used = (total_spent / budget.amount) * 100 if budget.amount > 0 else 0
        
        color_var = 'var(--pico-primary)'
        if percentage_used > 100: color_var = 'var(--pico-color-red-500)'
        elif percentage_used > 85: color_var = 'var(--pico-color-amber-400)'

        budget_progress_data.append({
            'category_name': budget.category.name, 'budget_limit': budget.amount,
            'total_spent': total_spent, 'percentage_used': percentage_used,
            'color': color_var
        })
    
    return render_template('dashboard.html', 
                           accounts=user_accounts, 
                           transactions=recent_transactions,
                           budget_progress=budget_progress_data)


# ===================================================================
# TRANSACTION CRUD
# ===================================================================

@main_bp.route('/transactions')
@login_required
def transactions():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '').strip()
    stmt = select(Transaction).options(
        selectinload(Transaction.categories), 
        selectinload(Transaction.tags)
    ).filter(Transaction.user_id == current_user.id)
    if search_query:
        search_term = f"%{search_query}%"
        stmt = stmt.join(Transaction.categories, isouter=True).join(Transaction.tags, isouter=True).filter(
            or_(
                Transaction.description.ilike(search_term),
                Transaction.notes.ilike(search_term),
                Category.name.ilike(search_term),
                Tag.name.ilike(search_term)
            )
        ).distinct()
    stmt = stmt.order_by(Transaction.transaction_date.desc())
    all_transactions = db.paginate(stmt, page=page, per_page=15)
    return render_template('transactions.html', transactions=all_transactions, search_query=search_query)


@main_bp.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    accounts = db.session.execute(select(Account).filter_by(user_id=current_user.id)).scalars().all()
    categories = db.session.execute(select(Category).filter_by(user_id=current_user.id).order_by(Category.name)).scalars().all()

    if request.method == 'POST':
        errors = {}
        form_data = request.form
        description = form_data.get('description', '').strip()
        amount_str = form_data.get('amount', '').strip()
        account_id_str = form_data.get('account_id')
        trans_type = form_data.get('transaction_type')
        category_id = form_data.get('category_id')

        if not description: errors['description'] = 'Description is required.'
        if not amount_str: errors['amount'] = 'Amount is required.'
        if not account_id_str: errors['account'] = 'Account is required.'
        if trans_type == 'expense' and not category_id: errors['category'] = 'Category is required for expenses.'

        amount = None
        if not errors.get('amount'):
            try:
                amount = decimal.Decimal(amount_str)
                if amount <= 0: errors['amount'] = 'Amount must be positive.'
            except decimal.InvalidOperation:
                errors['amount'] = 'Invalid amount format.'

        if errors:
            flash('Please correct the errors below.', 'error')
            return render_template('add_transaction.html', errors=errors, form_data=form_data, accounts=accounts, categories=categories)
        
        new_transaction = Transaction(
            amount=amount, transaction_type=trans_type, description=description,
            notes=form_data.get('notes', '').strip(), user_id=current_user.id,
            account_id=int(account_id_str)
        )
        db.session.add(new_transaction)

        if category_id:
            category = db.session.get(Category, int(category_id))
            if category: new_transaction.categories.append(category)

        tags_string = form_data.get('tags', '').strip()
        if tags_string:
            tag_names = [name.strip() for name in tags_string.split(',') if name.strip()]
            for tag_name in tag_names:
                stmt = select(Tag).where(func.lower(Tag.name) == func.lower(tag_name), Tag.user_id == current_user.id)
                tag = db.session.execute(stmt).scalar_one_or_none()
                if not tag:
                    tag = Tag(name=tag_name, user_id=current_user.id)
                    db.session.add(tag)
                new_transaction.tags.append(tag)

        account = db.session.get(Account, int(account_id_str))
        if account:
            if new_transaction.transaction_type == 'income': account.balance += amount
            else: account.balance -= amount

        db.session.commit()
        flash(f'{trans_type.capitalize()} added successfully!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('add_transaction.html', errors={}, form_data={}, accounts=accounts, categories=categories)


@main_bp.route('/edit_transaction/<int:transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    transaction = db.session.get(Transaction, transaction_id)
    if not transaction or transaction.user_id != current_user.id:
        abort(404)
    
    if request.method == 'POST':
        # ... (logic to update balance, amount, description, etc. is correct) ...
        original_amount = transaction.amount
        original_type = transaction.transaction_type
        original_account = transaction.account

        if original_account:
            if original_type == 'income': original_account.balance -= original_amount
            else: original_account.balance += original_amount
        
        transaction.amount = decimal.Decimal(request.form.get('amount'))
        transaction.transaction_type = request.form.get('transaction_type')
        # ... etc.

        new_account = db.session.get(Account, transaction.account_id)
        if new_account:
            if transaction.transaction_type == 'income': new_account.balance += transaction.amount
            else: new_account.balance -= transaction.amount
            
        # --- THIS IS THE CRITICAL LOGIC THAT WAS MISSING ---
        # Clear old associations and add new ones
        transaction.categories.clear()
        category_id = request.form.get('category_id')
        if category_id:
            category = db.session.get(Category, int(category_id))
            if category:
                transaction.categories.append(category)

        transaction.tags.clear()
        tags_string = request.form.get('tags', '').strip()
        if tags_string:
            tag_names = [name.strip() for name in tags_string.split(',') if name.strip()]
            for tag_name in tag_names:
                stmt = select(Tag).where(func.lower(Tag.name) == func.lower(tag_name), Tag.user_id == current_user.id)
                tag = db.session.execute(stmt).scalar_one_or_none()
                if not tag:
                    tag = Tag(name=tag_name, user_id=current_user.id)
                    db.session.add(tag)
                transaction.tags.append(tag)
        # --- END OF CRITICAL LOGIC ---

        db.session.commit()
        flash('Transaction updated successfully!', 'success')
        return redirect(url_for('main.transactions'))

    # GET request logic
    accounts = db.session.execute(select(Account).filter_by(user_id=current_user.id)).scalars().all()
    categories = db.session.execute(select(Category).filter_by(user_id=current_user.id)).scalars().all()
    return render_template('edit_transaction.html', transaction=transaction, accounts=accounts, categories=categories)


@main_bp.route('/delete_transaction/<int:transaction_id>', methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    transaction = db.session.get(Transaction, transaction_id)
    if not transaction: abort(404)
    if transaction.user_id != current_user.id: abort(403)

    account = transaction.account
    if account:
        if transaction.transaction_type == 'income': account.balance -= transaction.amount
        else: account.balance += transaction.amount
        
    db.session.delete(transaction)
    db.session.commit()
    flash('Transaction deleted successfully!', 'success')
    return redirect(url_for('main.transactions'))


# ===================================================================
# ACCOUNT & BUDGET ROUTES
# ===================================================================

@main_bp.route('/accounts')
@login_required
def accounts():
    user_accounts = db.session.execute(select(Account).filter_by(user_id=current_user.id)).scalars().all()
    return render_template('accounts.html', accounts=user_accounts)


@main_bp.route('/account/<int:account_id>')
@login_required
def account_detail(account_id):
    account = db.session.get(Account, account_id)
    if not account: abort(404)
    if account.user_id != current_user.id: abort(403)
    
    stmt = select(Transaction).filter_by(account_id=account.id).order_by(Transaction.transaction_date.desc())
    transactions = db.session.execute(stmt).scalars().all()
    
    return render_template('account_detail.html', account=account, transactions=transactions)


@main_bp.route('/add_account', methods=['GET', 'POST'])
@login_required
def add_account():
    if request.method == 'POST':
        name = request.form.get('name')
        acc_type = request.form.get('account_type')
        balance = request.form.get('balance', 0)
        new_account = Account(
            name=name, account_type=acc_type, balance=balance, user_id=current_user.id
        )
        db.session.add(new_account)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('main.accounts'))
    
    return render_template('add_account.html')


@main_bp.route('/edit_account/<int:account_id>', methods=['GET', 'POST'])
@login_required
def edit_account(account_id):
    account = db.session.get(Account, account_id)
    if not account: abort(404)
    if account.user_id != current_user.id: abort(403)

    if request.method == 'POST':
        account.name = request.form.get('name')
        account.account_type = request.form.get('account_type')
        db.session.commit()
        flash('Account updated successfully!', 'success')
        return redirect(url_for('main.accounts'))

    return render_template('edit_account.html', account=account)


@main_bp.route('/delete_account/<int:account_id>', methods=['POST'])
@login_required
def delete_account(account_id):
    account = db.session.get(Account, account_id)
    if not account: abort(404)
    if account.user_id != current_user.id: abort(403)

    if account.transactions:
        flash('Cannot delete account with transactions.', 'error')
        return redirect(url_for('main.accounts'))

    db.session.delete(account)
    db.session.commit()
    flash('Account deleted successfully!', 'success')
    return redirect(url_for('main.accounts'))


@main_bp.route('/budgets', methods=['GET', 'POST'])
@login_required
def budgets():
    if request.method == 'POST':
        category_id = request.form.get('category_id')
        amount = request.form.get('amount')
        month = request.form.get('month')
        year = request.form.get('year')

        if not all([category_id, amount, month, year]):
            flash('All fields are required.', 'error')
            return redirect(url_for('main.budgets'))

        stmt = select(Budget).filter_by(
            user_id=current_user.id, category_id=int(category_id),
            month=int(month), year=int(year)
        )
        existing_budget = db.session.execute(stmt).scalar_one_or_none()

        if existing_budget:
            flash('A budget for this category and month already exists.', 'warning')
        else:
            new_budget = Budget(
                user_id=current_user.id, category_id=int(category_id),
                amount=decimal.Decimal(amount), month=int(month), year=int(year)
            )
            db.session.add(new_budget)
            db.session.commit()
            flash('Budget created successfully!', 'success')
        
        return redirect(url_for('main.budgets'))

    user_budgets = db.session.execute(select(Budget).filter_by(user_id=current_user.id).order_by(Budget.year.desc(), Budget.month.desc())).scalars().all()
    user_categories = db.session.execute(select(Category).filter_by(user_id=current_user.id).order_by(Category.name)).scalars().all()
    
    current_year = datetime.now(timezone.utc).year
    years_for_dropdown = range(current_year - 1, current_year + 5)
    month_names = {i: datetime(current_year, i, 1).strftime('%B') for i in range(1, 13)}

    return render_template('budgets.html', 
                           budgets=user_budgets, categories=user_categories, 
                           years=years_for_dropdown, month_names=month_names)


@main_bp.route('/edit_budget/<int:budget_id>', methods=['GET', 'POST'])
@login_required
def edit_budget(budget_id):
    """Handles editing an existing budget."""
    budget = db.session.get(Budget, budget_id)
    if not budget:
        abort(404)
    if budget.user_id != current_user.id:
        abort(403) # Forbidden

    if request.method == 'POST':
        new_amount = request.form.get('amount')
        # You could add logic here to allow changing month/year/category if desired,
        # but for simplicity, we'll focus on updating the amount.
        if new_amount:
            budget.amount = decimal.Decimal(new_amount)
            db.session.commit()
            flash('Budget updated successfully!', 'success')
            return redirect(url_for('main.budgets'))
        else:
            flash('Amount cannot be empty.', 'error')

    # For a GET request, pass the necessary data to the template
    current_year = datetime.utcnow().year
    years_for_dropdown = range(current_year - 1, current_year + 5)
    month_names = {i: datetime(current_year, i, 1).strftime('%B') for i in range(1, 13)}
    
    return render_template('edit_budget.html', 
                           budget=budget,
                           years=years_for_dropdown,
                           month_names=month_names)


@main_bp.route('/delete_budget/<int:budget_id>', methods=['POST'])
@login_required
def delete_budget(budget_id):
    """Handles deleting a budget."""
    budget = db.session.get(Budget, budget_id)
    if not budget:
        abort(404)
    if budget.user_id != current_user.id:
        abort(403)

    db.session.delete(budget)
    db.session.commit()
    flash('Budget deleted successfully!', 'success')
    return redirect(url_for('main.budgets'))


# ===================================================================
# CATEGORY, PROFILE & AUTH ROUTES
# ===================================================================

@main_bp.route('/categories', methods=['GET', 'POST'])
@login_required
def manage_categories():
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            stmt = select(Category).filter(
                func.lower(Category.name) == func.lower(name),
                Category.user_id == current_user.id
            )
            existing_category = db.session.execute(stmt).scalar_one_or_none()
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

    categories = db.session.execute(select(Category).filter_by(user_id=current_user.id).order_by(Category.name)).scalars().all()
    return render_template('categories.html', categories=categories)


@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Check which form was submitted based on the button's 'name' and 'value'
        action = request.form.get('action')

        if action == 'update_profile':
            new_email = request.form.get('email').strip()
            
            # Validation: Check if the new email is already taken by another user
            stmt = select(User).where(User.email == new_email)
            existing_user = db.session.execute(stmt).scalar_one_or_none()

            if existing_user and existing_user.id != current_user.id:
                flash('That email address is already in use by another account.', 'error')
            elif not new_email:
                flash('Email address cannot be empty.', 'error')
            else:
                current_user.email = new_email
                db.session.commit()
                flash('Your profile has been updated successfully!', 'success')

        elif action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_new_password = request.form.get('confirm_new_password')

            if not bcrypt.check_password_hash(current_user.password_hash, current_password):
                flash('Your current password was incorrect. Please try again.', 'error')
            elif new_password != confirm_new_password:
                flash('The new passwords do not match.', 'error')
            else:
                current_user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
                db.session.commit()
                flash('Your password has been updated successfully!', 'success')
        
        return redirect(url_for('main.profile'))

    # For a GET request, just render the page as usual
    return render_template('profile.html')


@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if db.session.execute(select(User).filter_by(email=email)).scalar_one_or_none():
            flash('Email address already in use.', 'error')
        elif db.session.execute(select(User).filter_by(username=username)).scalar_one_or_none():
            flash('Username already taken.', 'error')
        else:
            new_user = User(
                username=username, email=email,
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
        user = db.session.execute(select(User).filter_by(email=email)).scalar_one_or_none()
        
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

@main_bp.route('/tag/<tag_name>')
@login_required
def tag_detail(tag_name):
    """Displays all transactions for a specific tag."""
    
    # Find the tag by name, ensuring it belongs to the current user for security.
    # We use a case-insensitive comparison for a better user experience.
    stmt = select(Tag).where(func.lower(Tag.name) == func.lower(tag_name), Tag.user_id == current_user.id)
    tag = db.session.execute(stmt).scalar_one_or_none()

    if not tag:
        # If the tag doesn't exist or doesn't belong to the user, return a 404.
        abort(404)

    # The backref 'tag.transactions' automatically gives us a list of all transactions
    # associated with this tag. We can sort this list directly.
    transactions = sorted(tag.transactions, key=lambda t: t.transaction_date, reverse=True)
    
    return render_template('tag_detail.html', tag_name=tag.name, transactions=transactions)


# ===================================================================
# API & REPORTING ROUTES
# ===================================================================

@main_bp.route('/reports')
@login_required
def reports():
    stmt = select(Transaction).filter_by(user_id=current_user.id, transaction_type='expense').order_by(Transaction.transaction_date.desc())
    expenses = db.session.execute(stmt).scalars().all()
    
    monthly_summary_raw = defaultdict(lambda: defaultdict(float))
    for expense in expenses:
        month_key = expense.transaction_date.strftime('%Y-%m')
        if not expense.categories:
             monthly_summary_raw[month_key]['Uncategorized'] += float(expense.amount)
        else:
            for category in expense.categories:
                monthly_summary_raw[month_key][category.name] += float(expense.amount)
    
    monthly_summary_final = {}
    for month_key in sorted(monthly_summary_raw.keys(), reverse=True):
        month_name = datetime.strptime(month_key, '%Y-%m').strftime('%B %Y')
        sorted_categories = sorted(monthly_summary_raw[month_key].items(), key=lambda item: item[1], reverse=True)
        monthly_summary_final[month_name] = sorted_categories

    return render_template(
        'reports.html', 
        monthly_summary=monthly_summary_final,
        now=datetime.now(timezone.utc)  # FIXED: Use timezone-aware datetime
    )

@main_bp.route('/report/yearly/<int:year>')
@login_required
def yearly_report(year):
    """
    Generates and displays a year-at-a-glance report showing total income,
    expenses, and net balance for each month.
    """
    # 1. The SQLAlchemy query to get monthly totals grouped by transaction type
    stmt = select(
        func.extract('month', Transaction.transaction_date).label('month'),
        Transaction.transaction_type,
        func.sum(Transaction.amount).label('total_amount')
    ).where(
        Transaction.user_id == current_user.id,
        func.extract('year', Transaction.transaction_date) == year
    ).group_by(
        func.extract('month', Transaction.transaction_date),
        Transaction.transaction_type
    )
    
    query_results = db.session.execute(stmt).all()

    # 2. Process the query results into a structured dictionary
    # Initialize data for all 12 months to ensure every month is displayed
    report_data = {
        month_num: {
            'month_name': calendar.month_name[month_num],
            'income': decimal.Decimal(0),
            'expense': decimal.Decimal(0),
            'net': decimal.Decimal(0)
        } for month_num in range(1, 13)
    }

    for month_num, trans_type, total_amount in query_results:
        if trans_type == 'income':
            report_data[month_num]['income'] = total_amount
        else: # 'expense'
            report_data[month_num]['expense'] = total_amount

    # 3. Calculate the net balance for each month and grand totals
    grand_total = {'income': 0, 'expense': 0, 'net': 0}
    for month_data in report_data.values():
        month_data['net'] = month_data['income'] - month_data['expense']
        grand_total['income'] += month_data['income']
        grand_total['expense'] += month_data['expense']
    grand_total['net'] = grand_total['income'] - grand_total['expense']

    return render_template(
        'yearly_report.html', 
        report_data=report_data, 
        year=year,
        grand_total=grand_total
    )

@main_bp.route('/export-transactions')
@login_required
def export_transactions():
    string_io = io.StringIO()
    csv_writer = csv.writer(string_io)
    csv_writer.writerow(['Date', 'Description', 'Amount', 'Type', 'Account', 'Category', 'Notes'])
    
    stmt = select(Transaction).filter_by(user_id=current_user.id).order_by(Transaction.transaction_date)
    transactions = db.session.execute(stmt).scalars().all()

    for t in transactions:
        category_names = ', '.join([c.name for c in t.categories])
        csv_writer.writerow([
            t.transaction_date.strftime('%Y-%m-%d'), t.description, t.amount,
            t.transaction_type, t.account.name, category_names, t.notes
        ])
        
    output = string_io.getvalue()
    return Response(
        output, mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=transactions.csv"})


@main_bp.route('/api/transaction-summary')
@login_required
def transaction_summary_api():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    if not start_date_str or not end_date_str:
        return jsonify({'labels': [], 'data': []}) # Return empty if no dates

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    end_date_inclusive = datetime.combine(end_date, datetime.max.time())

    stmt = select(
        Category.name, func.sum(Transaction.amount)
    ).join(
        transaction_categories, Category.id == transaction_categories.c.category_id
    ).join(
        Transaction, Transaction.id == transaction_categories.c.transaction_id
    ).where(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == 'expense',
        Transaction.transaction_date.between(start_date, end_date_inclusive)
    ).group_by(Category.name)
    
    summary = db.session.execute(stmt).all()
    
    return jsonify({
        'labels': [row[0] for row in summary],
        'data': [float(row[1]) for row in summary]
    })


@main_bp.route('/api/daily_expense_trend')
@login_required
def daily_expense_trend():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    if not start_date_str or not end_date_str:
        return jsonify({'labels': [], 'data': []}) # Return empty if no dates

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    end_date_inclusive = datetime.combine(end_date, datetime.max.time())
    
    stmt = select(
        func.cast(Transaction.transaction_date, db.Date).label('date'),
        func.sum(Transaction.amount).label('total_expenses')
    ).where(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == 'expense',
        Transaction.transaction_date.between(start_date, end_date_inclusive)
    ).group_by(
        func.cast(Transaction.transaction_date, db.Date)
    ).order_by(
        func.cast(Transaction.transaction_date, db.Date)
    )
    daily_expenses_query = db.session.execute(stmt).all()

    # Build a complete date range to ensure all days are represented
    date_range = (start_date + timedelta(days=n) for n in range((end_date - start_date).days + 1))
    trend_data = {dt.strftime('%Y-%m-%d'): 0 for dt in date_range}

    for day in daily_expenses_query:
        trend_data[day.date.strftime('%Y-%m-%d')] = float(day.total_expenses)
        
    return jsonify({
        'labels': list(trend_data.keys()),
        'data': list(trend_data.values())
    })

@main_bp.route('/api/check-username')
def check_username():
    """Checks if a username is already taken."""
    username = request.args.get('username', '').strip()

    # Don't check for empty or very short usernames
    if len(username) < 3:
        # Return a neutral or empty response
        return jsonify({})

    # Query the database for an existing user with that username
    stmt = select(User).where(User.username == username)
    user = db.session.execute(stmt).scalar_one_or_none()

    # Return a JSON response indicating if the username is available
    if user:
        return jsonify({'available': False})
    else:
        return jsonify({'available': True})

@main_bp.route('/api/check-email')
def check_email():
    """Checks if an email is already taken."""
    email = request.args.get('email', '').strip().lower()

    # A simple check to see if it looks like an email
    if '@' not in email or '.' not in email or len(email) < 5:
        return jsonify({})

    stmt = select(User).where(User.email == email)
    user = db.session.execute(stmt).scalar_one_or_none()

    if user:
        return jsonify({'available': False})
    else:
        return jsonify({'available': True})