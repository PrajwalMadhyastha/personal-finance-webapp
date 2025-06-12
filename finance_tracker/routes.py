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
from datetime import datetime, timedelta
from .models import Transaction, User, Category, Account, Budget
from sqlalchemy import func, select


# ===================================================================
# BLUEPRINT DEFINITION
# ===================================================================
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
    # Using modern db.session.execute(select(...)) syntax
    accounts_stmt = select(Account).filter_by(user_id=current_user.id)
    user_accounts = db.session.execute(accounts_stmt).scalars().all()
    
    trans_stmt = select(Transaction).filter_by(user_id=current_user.id).order_by(Transaction.transaction_date.desc()).limit(10)
    recent_transactions = db.session.execute(trans_stmt).scalars().all()

    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year

    budget_stmt = select(Budget).filter_by(user_id=current_user.id, month=current_month, year=current_year)
    current_budgets = db.session.execute(budget_stmt).scalars().all()
    
    budget_progress_data = []
    for budget in current_budgets:
        spent_stmt = select(func.sum(Transaction.amount)).where(
            Transaction.user_id == current_user.id,
            Transaction.categories.any(Category.id == budget.category_id),
            Transaction.transaction_type == 'expense',
            func.extract('month', Transaction.transaction_date) == current_month,
            func.extract('year', Transaction.transaction_date) == current_year
        )
        total_spent = db.session.execute(spent_stmt).scalar() or 0.0
        percentage_used = (total_spent / budget.amount) * 100 if budget.amount > 0 else 0
        budget_progress_data.append({
            'category_name': budget.category.name,
            'budget_limit': budget.amount,
            'total_spent': total_spent,
            'percentage_used': percentage_used
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
    stmt = select(Transaction).filter_by(user_id=current_user.id).order_by(Transaction.transaction_date.desc())
    all_transactions = db.paginate(stmt, page=page, per_page=15)
    return render_template('transactions.html', transactions=all_transactions)


@main_bp.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    accounts = db.session.execute(select(Account).filter_by(user_id=current_user.id)).scalars().all()
    categories = db.session.execute(select(Category).filter_by(user_id=current_user.id).order_by(Category.name)).scalars().all()

    if not accounts:
        flash('You must create an account first.', 'warning')
        return redirect(url_for('main.add_account'))

    if request.method == 'POST':
        amount = decimal.Decimal(request.form.get('amount'))
        trans_type = request.form.get('transaction_type')
        description = request.form.get('description')
        account_id = int(request.form.get('account_id'))
        category_id = request.form.get('category_id')
        notes = request.form.get('notes')
        
        new_transaction = Transaction(
            amount=amount, transaction_type=trans_type, description=description,
            notes=notes, user_id=current_user.id, account_id=account_id
        )

        if category_id:
            category = db.session.get(Category, int(category_id))
            if category: new_transaction.categories.append(category)

        account = db.session.get(Account, account_id)
        if account:
            if new_transaction.transaction_type == 'income':
                account.balance += amount
            else:
                account.balance -= amount

        db.session.add(new_transaction)
        db.session.commit()
        flash(f'{trans_type.capitalize()} added successfully!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('add_transaction.html', accounts=accounts, categories=categories)


@main_bp.route('/edit_transaction/<int:transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    transaction = db.session.get(Transaction, transaction_id)
    if not transaction: abort(404)
    if transaction.user_id != current_user.id: abort(403)
    
    accounts = db.session.execute(select(Account).filter_by(user_id=current_user.id)).scalars().all()
    categories = db.session.execute(select(Category).filter_by(user_id=current_user.id)).scalars().all()

    if request.method == 'POST':
        original_amount = transaction.amount
        original_type = transaction.transaction_type
        original_account = transaction.account

        if original_account:
            if original_type == 'income': original_account.balance -= original_amount
            else: original_account.balance += original_amount

        transaction.amount = decimal.Decimal(request.form.get('amount'))
        transaction.transaction_type = request.form.get('transaction_type')
        transaction.description = request.form.get('description')
        transaction.account_id = int(request.form.get('account_id'))
        transaction.notes = request.form.get('notes')
        
        new_account = db.session.get(Account, transaction.account_id)
        if new_account:
            if transaction.transaction_type == 'income': new_account.balance += transaction.amount
            else: new_account.balance -= transaction.amount
        
        category_id = request.form.get('category_id')
        transaction.categories.clear()
        if category_id:
            category = db.session.get(Category, int(category_id))
            if category: transaction.categories.append(category)

        db.session.commit()
        flash('Transaction updated successfully!', 'success')
        return redirect(url_for('main.transactions'))

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
    
    current_year = datetime.utcnow().year
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
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_new_password = request.form.get('confirm_new_password')

        if not bcrypt.check_password_hash(current_user.password_hash, current_password):
            flash('Your current password was incorrect.', 'error')
        elif new_password != confirm_new_password:
            flash('New passwords do not match.', 'error')
        else:
            current_user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
            db.session.commit()
            flash('Your password has been updated!', 'success')
        return redirect(url_for('main.profile'))

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

    return render_template('reports.html', monthly_summary=monthly_summary_final)


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
    stmt = select(Category.name, func.sum(Transaction.amount))\
        .join(Transaction.categories).where(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == 'expense'
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

    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=29)

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

    date_range = (start_date + timedelta(days=n) for n in range((end_date - start_date).days + 1))
    trend_data = {dt.strftime('%Y-%m-%d'): 0 for dt in date_range}

    for day in daily_expenses_query:
        trend_data[day.date.strftime('%Y-%m-%d')] = float(day.total_expenses)
        
    return jsonify({
        'labels': list(trend_data.keys()),
        'data': list(trend_data.values())
    })