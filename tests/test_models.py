# tests/test_models.py

import pytest
from finance_tracker import create_app, db
from finance_tracker.models import User
from finance_tracker import bcrypt

@pytest.fixture(scope='module')
def test_app():
    """
    A pytest fixture to set up a test Flask application.
    This creates an in-memory SQLite database for testing.
    """
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing forms
        'SECRET_KEY': 'test-secret'
    })
    
    with app.app_context():
        db.create_all()
        yield app  # this is where the testing happens
        db.drop_all()

@pytest.fixture(scope='module')
def test_client(test_app):
    """A pytest fixture for the Flask test client."""
    return test_app.test_client()

# ===============================================
# Your First Test Functions
# ===============================================

def test_new_user(test_app):
    """
    GIVEN a User model
    WHEN a new User is created
    THEN check the username, email, and password_hash fields are defined correctly
    """
    with test_app.app_context():
        # Create a new user instance
        user = User(
            username='testuser', 
            email='test@example.com', 
            password_hash=bcrypt.generate_password_hash('password123').decode('utf-8')
        )
        
        # Use assert to verify the attributes
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.password_hash is not None


def test_password_hashing(test_app):
    """
    GIVEN a User model
    WHEN a password is set
    THEN check the password is not stored in plain text and can be verified
    """
    with test_app.app_context():
        # Create a user with a hashed password
        plain_password = 'my-super-secret-password'
        password_hash = bcrypt.generate_password_hash(plain_password).decode('utf-8')
        user = User(
            username='anotheruser', 
            email='another@example.com', 
            password_hash=password_hash
        )

        # Assert that the stored hash is NOT the same as the plain password
        assert user.password_hash != plain_password
        
        # Assert that the correct plain password successfully validates against the hash
        assert bcrypt.check_password_hash(user.password_hash, plain_password)
        
        # Assert that an incorrect password fails validation
        assert not bcrypt.check_password_hash(user.password_hash, 'wrongpassword')