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

@pytest.fixture(scope='function') # Change 'module' to 'function'
def auth_client(client, test_app):
    # The rest of the function remains the same
    with test_app.app_context():
        plain_password = 'password123'
        password_hash = bcrypt.generate_password_hash(plain_password).decode('utf-8')
        test_user = User(
            username='testclient',
            email='client@test.com',
            password_hash=password_hash
        )
        db.session.add(test_user)
        db.session.commit()

        client.post('/login', data={
            'email': 'client@test.com',
            'password': plain_password
        }, follow_redirects=True)

        yield client

        # The user is now cleaned up after each test function, not after the module
        db.session.delete(test_user)
        db.session.commit()

@pytest.fixture(scope='function')
def admin_user(test_app):
    """A fixture to create and yield an admin user, then clean it up."""
    with test_app.app_context():
        plain_password = 'admin_password'
        password_hash = bcrypt.generate_password_hash(plain_password).decode('utf-8')
        admin = User(
            username='testadmin',
            email='admin@test.com',
            password_hash=password_hash,
            is_admin=True  # User is created as an admin from the start
        )
        db.session.add(admin)
        db.session.commit()
        
        yield admin  # Provide the admin user object to the test
        
        db.session.delete(admin)
        db.session.commit()

@pytest.fixture(scope='function')
def logged_in_admin_client(client, admin_user):
    """A fixture that provides a client logged in as the admin user."""
    client.post('/login', data={
        'email': admin_user.email,
        'password': 'admin_password'
    }, follow_redirects=True)
    yield client