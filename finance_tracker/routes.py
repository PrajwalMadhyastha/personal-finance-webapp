# finance_tracker/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort
from flask_login import login_required, current_user
from .models import Expense, User, Category # Import new Category model
from . import db

main_bp = Blueprint('main', __name__)

# --- Main Routes ---

@main_bp.route('/')
@login_required
def home():
    """Renders the homepage and displays expenses for the current user."""
    expenses = Expense.query.filter_by(owner=current_user).order_by(Expense.timestamp.desc()).all()
    return render_template('index.html', expenses=expenses)

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
            next_page = request.args.get('next')
            flash('Logged in successfully!', 'success')
            return redirect(next_page or url_for('main.home'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'error')
    return render_template('login.html', title="Log In")


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