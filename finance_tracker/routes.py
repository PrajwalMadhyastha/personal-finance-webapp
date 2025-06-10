# finance_tracker/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort
from flask_login import login_user, logout_user, login_required, current_user
from .models import Expense, User
from . import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def home():
    # Only query expenses for the currently logged-in user
    expenses = Expense.query.filter_by(owner=current_user).order_by(Expense.timestamp.desc()).all()
    return render_template('index.html', expenses=expenses)


@main_bp.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        description = request.form['description']
        amount_str = request.form['amount']
        category = request.form['category']

        if not description or not amount_str or not category:
            flash('Error: All fields are required.', 'error')
            return redirect(url_for('main.add_expense'))
        
        try:
            amount = float(amount_str)
        except ValueError:
            flash('Error: Amount must be a valid number.', 'error')
            return redirect(url_for('main.add_expense'))

        # Associate the new expense with the current user
        new_expense = Expense(description=description, amount=amount, category=category, owner=current_user)
        
        db.session.add(new_expense)
        db.session.commit()
        flash(f"Expense '{new_expense.description}' was added successfully!", 'success')
        return redirect(url_for('main.home'))
    else:
        return render_template('add_expense_form.html')


@main_bp.route('/edit/<int:expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    expense_to_edit = db.get_or_404(Expense, expense_id)
    
    # Security Check: If the user is not the owner, forbid access.
    if expense_to_edit.owner != current_user:
        abort(403)
        
    if request.method == 'POST':
        expense_to_edit.description = request.form['description']
        expense_to_edit.amount = float(request.form['amount'])
        expense_to_edit.category = request.form['category']
        db.session.commit()
        flash(f"Expense '{expense_to_edit.description}' has been updated.", 'success')
        return redirect(url_for('main.home'))
    else:
        return render_template('edit_expense.html', expense=expense_to_edit, title="Edit Expense")


@main_bp.route('/delete/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense_to_delete = db.get_or_404(Expense, expense_id)

    # Security Check: If the user is not the owner, forbid access.
    if expense_to_delete.owner != current_user:
        abort(403)
        
    db.session.delete(expense_to_delete)
    db.session.commit()
    flash(f"Expense '{expense_to_delete.description}' has been deleted.", 'success')
    return redirect(url_for('main.home'))


# --- LOGIN/REGISTER/LOGOUT ROUTES ---
# (These remain the same as your working version)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
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
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'error')
            return redirect(url_for('main.register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please use a different one.', 'error')
            return redirect(url_for('main.register'))
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash(f"Account created for {username}! You can now log in.", 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', title="Register")