# finance_tracker/api_routes.py

from flask import Blueprint, request, jsonify, g
from functools import wraps
from .models import User, Transaction, Account, Category, Tag, ActivityLog
from . import db
from sqlalchemy import func, select
import decimal
from datetime import datetime, timezone, timedelta
from flask_login import login_user, logout_user, login_required, current_user

# 1. Define the new Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# 2. Create the Custom Authentication Decorator
def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = None
        # Check for the key in the 'Authorization' header (e.g., "Bearer <key>")
        if 'Authorization' in request.headers and request.headers['Authorization'].startswith('Bearer '):
            api_key = request.headers['Authorization'].split(' ')[1]
        
        if not api_key:
            return jsonify({"error": "Authorization header is missing or improperly formatted."}), 401

        # Find the user associated with the provided API key
        stmt = select(User).where(User.api_key == api_key)
        user = db.session.execute(stmt).scalar_one_or_none()
        
        if user is None:
            return jsonify({"error": "Invalid API key."}), 401
        
        # Store the authenticated user object in Flask's 'g' object,
        # which is available for the duration of the request.
        g.current_user = user
        
        return f(*args, **kwargs)
    return decorated_function


# 3. Create Your First API Endpoint
@api_bp.route('/transactions', methods=['GET', 'POST'])
@api_key_required
def manage_transactions():
    """
    Handles fetching (GET) and creating (POST) transactions for the authenticated user.
    """
    # The 'g.current_user' is set by the @api_key_required decorator
    user = g.current_user

    # --- Logic for POST (Creating a new transaction) ---
    if request.method == 'POST':
        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid JSON body."}), 400

        # --- 1. Validation ---
        required_fields = ['description', 'amount', 'type', 'account_id']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Validate transaction type
        if data['type'] not in ['expense', 'income']:
            return jsonify({"error": "Invalid transaction type. Must be 'expense' or 'income'."}), 400
        
        # Validate that the associated account exists and belongs to the user
        account = db.session.get(Account, data['account_id'])
        if not account or account.user_id != user.id:
            return jsonify({"error": "Invalid account_id."}), 400
            
        # Validate category if provided
        category = None
        if data.get('category_id'):
            category = db.session.get(Category, data['category_id'])
            if not category or category.user_id != user.id:
                return jsonify({"error": "Invalid category_id."}), 400

        # --- 2. Create the Transaction ---
        try:
            amount = decimal.Decimal(data['amount'])
            if amount <= 0: raise ValueError()
        except (ValueError, decimal.InvalidOperation):
            return jsonify({"error": "Amount must be a positive number."}), 400

        new_transaction = Transaction(
            description=data['description'],
            amount=amount,
            transaction_type=data['type'],
            notes=data.get('notes'),
            user_id=user.id,
            account_id=account.id,
            transaction_date=datetime.now(timezone.utc)
        )
        db.session.add(new_transaction)

        if category:
            new_transaction.categories.append(category)

        # --- 3. Handle Tags (Find or Create) ---
        if data.get('tags') and isinstance(data['tags'], list):
            for tag_name in data['tags']:
                stmt = select(Tag).where(func.lower(Tag.name) == func.lower(tag_name), Tag.user_id == user.id)
                tag = db.session.execute(stmt).scalar_one_or_none()
                if not tag:
                    tag = Tag(name=tag_name, user_id=user.id)
                    db.session.add(tag)
                new_transaction.tags.append(tag)

        # --- 4. Update Account Balance ---
        if new_transaction.transaction_type == 'income':
            account.balance += amount
        else: # expense
            account.balance -= amount

        # --- 5. Log Activity ---
        log_entry = ActivityLog(user_id=user.id, description=f"Added transaction via API: '{new_transaction.description}'")
        db.session.add(log_entry)

        # --- 6. Commit and Respond ---
        db.session.commit()
        
        return jsonify({"message": "Transaction created successfully", "id": new_transaction.id}), 201

    # --- Logic for GET (Fetching all transactions) ---
    else: # request.method == 'GET'
        trans_stmt = select(Transaction).filter_by(user_id=user.id).order_by(Transaction.transaction_date.desc())
        transactions = db.session.execute(trans_stmt).scalars().all()

        output = []
        for t in transactions:
            output.append({
                'id': t.id,
                'description': t.description,
                'amount': float(t.amount),
                'type': t.transaction_type,
                'date': t.transaction_date.isoformat()
            })

        return jsonify({'transactions': output})