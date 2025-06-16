# tests/test_features.py
from finance_tracker.models import ActivityLog, Account, Category, Transaction
from finance_tracker import db
from sqlalchemy import select
import decimal
import pytest

@pytest.mark.feature
def test_add_transaction_creates_activity_log(auth_client, test_app):
    """
    GIVEN an authenticated user
    WHEN they add a new valid transaction via a POST request
    THEN verify a new Transaction is created AND a corresponding ActivityLog is created
    """
    # Setup: We need an account and a category to create a transaction
    with test_app.app_context():
        test_account = Account(name="Test Bank", account_type="Checking", user_id=1)
        test_category = Category(name="Test Category", user_id=1)
        db.session.add_all([test_account, test_category])
        db.session.commit()
        
        # --- THIS IS THE FIX ---
        # The keys here must match the field names in your TransactionForm class
        form_data = {
            'description': 'Coffee Shop',
            'amount': '4.50',
            'transaction_type': 'expense',
            'account': test_account.id,   # Changed from account_id
            'category': test_category.id  # Changed from category_id
        }
        # --- END OF FIX ---
    
        # Action: Simulate the POST request
        response = auth_client.post('/add_transaction', data=form_data, follow_redirects=True)
        assert response.status_code == 200

        # Verification
        # 1. Assert that the transaction was created
        stmt = select(Transaction).filter_by(description='Coffee Shop')
        new_transaction = db.session.execute(stmt).scalar_one_or_none()
        assert new_transaction is not None
        assert new_transaction.amount == decimal.Decimal('4.50')

        # 2. Assert that the ActivityLog was created
        log_stmt = select(ActivityLog).order_by(ActivityLog.id.desc())
        latest_log = db.session.execute(log_stmt).scalars().first()
        assert latest_log is not None
        assert latest_log.user_id == 1
        assert "Added transaction: 'Coffee Shop'" in latest_log.description