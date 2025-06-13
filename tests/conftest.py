import pytest
from finance_tracker import create_app, db
from finance_tracker.models import User
from finance_tracker import bcrypt

@pytest.fixture(scope='module')
def test_app():
    """
    A pytest fixture to set up and tear down a test Flask application.
    This creates an in-memory SQLite database for clean testing.
    """
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })
    
    with app.app_context():
        db.create_all()
        yield app  # The test session runs here
        db.drop_all()

@pytest.fixture(scope='module')
def client(test_app):
    """A pytest fixture for the Flask test client."""
    return test_app.test_client()

@pytest.fixture(scope='module')
def auth_client(client, test_app):
    """
    A pytest fixture that creates a user, logs them in, and returns
    an authenticated test client.
    """
    with test_app.app_context():
        # Create a test user
        plain_password = 'password123'
        password_hash = bcrypt.generate_password_hash(plain_password).decode('utf-8')
        test_user = User(
            username='testclient',
            email='client@test.com',
            password_hash=password_hash
        )
        db.session.add(test_user)
        db.session.commit()

        # Log the user in using the test client
        client.post('/login', data={
            'email': 'client@test.com',
            'password': plain_password
        }, follow_redirects=True)

        yield client # The test session runs with the logged-in client

        # Teardown: Clean up the user after tests
        db.session.delete(test_user)
        db.session.commit()