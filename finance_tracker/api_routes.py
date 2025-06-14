# finance_tracker/api_routes.py

from flask import Blueprint, request, jsonify, g
from functools import wraps
from .models import User, Transaction
from . import db
from sqlalchemy import select

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
@api_bp.route('/transactions', methods=['GET'])
@api_key_required  # Apply the custom decorator to protect this route
def get_transactions():
    """
    Returns a list of all transactions for the authenticated user.
    """
    # The 'g.current_user' was set by the @api_key_required decorator
    user = g.current_user
    
    # Query for the user's transactions
    trans_stmt = select(Transaction).filter_by(user_id=user.id).order_by(Transaction.transaction_date.desc())
    transactions = db.session.execute(trans_stmt).scalars().all()

    # Format the data for the JSON response
    output = []
    for t in transactions:
        output.append({
            'id': t.id,
            'description': t.description,
            'amount': float(t.amount),
            'type': t.transaction_type,
            'date': t.transaction_date.isoformat(),
            'notes': t.notes
        })

    return jsonify({'transactions': output})