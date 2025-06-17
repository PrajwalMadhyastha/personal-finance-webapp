# tests/test_api.py

import pytest
import secrets
import json
from finance_tracker import db
from finance_tracker.models import User, Account, Transaction, ActivityLog

# This fixture creates a user with a known API key specifically for these tests.
# It runs once per function, ensuring a clean state for each test.
@pytest.fixture(scope='function')
def api_user(test_app):
    """Creates a user with a predictable API key and an associated account."""
    with test_app.app_context():
        api_key = secrets.token_hex(32)
        user = User(
            username='apiuser',
            email='api@test.com',
            password_hash='...', # Password not needed for API key tests
            api_key=api_key
        )
        account = Account(name='API Test Account', account_type='Savings', user=user)
        db.session.add(user)
        db.session.add(account)
        db.session.commit()
        
        # Yield the user and account so the test can use their IDs and keys
        yield user, account

        # Teardown logic to clean up the database after the test
        # We need to manually delete the transaction created in the POST test
        Transaction.query.delete()
        ActivityLog.query.delete()
        db.session.delete(account)
        db.session.delete(user)
        db.session.commit()


@pytest.mark.feature
def test_api_unauthenticated_access(client):
    """
    GIVEN a client without an API key
    WHEN a request is made to a protected API endpoint
    THEN the response should be 401 Unauthorized
    """
    response = client.get('/api/v1/transactions')
    assert response.status_code == 401
    data = response.get_json()
    assert "Authorization header is missing" in data['error']


@pytest.mark.feature
def test_api_get_transactions_authenticated(client, api_user):
    """
    GIVEN a user with a valid API key and an existing transaction
    WHEN a GET request is made with the correct Authorization header
    THEN the response should be 200 OK and contain the user's transaction
    """
    user, account = api_user
    with client.application.app_context():
        # Create a transaction that belongs to our API user
        t1 = Transaction(description='API Test 1', amount=123.45, transaction_type='income', user_id=user.id, account_id=account.id)
        db.session.add(t1)
        db.session.commit()

    # Make the authenticated API request
    headers = {
        'Authorization': f'Bearer {user.api_key}'
    }
    response = client.get('/api/v1/transactions', headers=headers)

    # Assert success and that the correct data was returned
    assert response.status_code == 200
    data = response.get_json()
    assert 'transactions' in data
    assert len(data['transactions']) == 1
    assert data['transactions'][0]['description'] == 'API Test 1'
    assert data['transactions'][0]['amount'] == 123.45


@pytest.mark.feature
def test_api_post_transaction_authenticated(client, api_user):
    """
    GIVEN a user with a valid API key
    WHEN a POST request is made with valid transaction data
    THEN a new transaction should be created in the database for that user
    """
    user, account = api_user
    
    # Prepare the POST request data
    headers = {
        'Authorization': f'Bearer {user.api_key}',
        'Content-Type': 'application/json'
    }
    payload = {
        "description": "New API Expense",
        "amount": 75.50,
        "type": "expense",
        "account_id": account.id
    }
    
    # Make the POST request
    response = client.post('/api/v1/transactions', headers=headers, data=json.dumps(payload))
    
    # Assert that the API response is correct (201 Created)
    assert response.status_code == 201
    data = response.get_json()
    assert data['message'] == "Transaction created successfully"
    new_transaction_id = data['id']

    # Assert that the transaction was actually created in the database
    with client.application.app_context():
        new_trans = db.session.get(Transaction, new_transaction_id)
        assert new_trans is not None
        assert new_trans.description == "New API Expense"
        assert new_trans.user_id == user.id
        
        # Assert that the account balance was updated correctly
        updated_account = db.session.get(Account, account.id)
        # Assuming starting balance of 0, an expense of 75.50 should result in -75.50
        assert updated_account.balance == -75.50