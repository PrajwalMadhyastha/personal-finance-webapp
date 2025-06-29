# tests/test_investments.py

from finance_tracker import db, bcrypt
from finance_tracker.models import User, Asset, InvestmentTransaction, ActivityLog
from sqlalchemy import select
import decimal
from datetime import datetime
import pytest

# NOTE: These tests rely on the 'test_app' and 'auth_client' fixtures
#       that are defined in your 'tests/conftest.py' file.


@pytest.mark.feature
def test_edit_investment_transaction(auth_client, test_app):
    """
    GIVEN an authenticated user with an existing investment transaction
    WHEN the user submits a valid edit form for that transaction
    THEN check that the transaction's details are updated in the database
    """
    with test_app.app_context():
        # --- GIVEN ---
        # The auth_client fixture already created a user with id=1
        asset = Asset(name="Test Inc.", ticker_symbol="TEST", asset_type="Stock")
        original_date = datetime.strptime("2025-01-05T10:00", "%Y-%m-%dT%H:%M")
        trans_to_edit = InvestmentTransaction(
            user_id=1,
            asset=asset,
            transaction_type="buy",
            quantity=10,
            price_per_unit=100,
            transaction_date=original_date,
        )
        db.session.add_all([asset, trans_to_edit])
        db.session.commit()

        # --- WHEN ---
        # --- THIS IS THE FIX ---
        # The transaction_date now sends a string in the correct 'datetime-local' format.
        form_data = {
            "transaction_type": "buy",
            "quantity": "12.5",
            "price_per_unit": "105.50",
            "transaction_date": "2025-01-10T14:30",  # Correct format with date and time
        }
        # --- END OF FIX ---
        response = auth_client.post(
            f"/portfolio/edit/{trans_to_edit.id}", data=form_data, follow_redirects=True
        )
        assert response.status_code == 200

        # --- THEN ---
        updated_trans = db.session.get(InvestmentTransaction, trans_to_edit.id)
        assert updated_trans is not None
        assert updated_trans.quantity == decimal.Decimal("12.5")
        assert updated_trans.price_per_unit == decimal.Decimal("105.50")
        assert (
            updated_trans.transaction_date.strftime("%Y-%m-%dT%H:%M")
            == "2025-01-10T14:30"
        )


@pytest.mark.feature
def test_delete_investment_transaction(auth_client, test_app):
    """
    GIVEN an authenticated user with an existing investment transaction
    WHEN the user deletes the transaction
    THEN check that the transaction is removed from the database
    """
    with test_app.app_context():
        # --- GIVEN ---
        asset = Asset(name="Delete Corp.", ticker_symbol="DEL", asset_type="Stock")
        trans_to_delete = InvestmentTransaction(
            user_id=1,
            asset=asset,
            transaction_type="sell",
            quantity=5,
            price_per_unit=50,
            transaction_date=datetime.now(),
        )
        db.session.add_all([asset, trans_to_delete])
        db.session.commit()

        trans_id = trans_to_delete.id  # Save the ID before we delete it

        # --- WHEN ---
        # Simulate the POST request to the delete route
        response = auth_client.post(
            f"/portfolio/delete/{trans_id}", follow_redirects=True
        )
        assert response.status_code == 200
        assert b"Investment transaction deleted." in response.data

        # --- THEN ---
        # Assert that the transaction no longer exists in the database
        deleted_trans = db.session.get(InvestmentTransaction, trans_id)
        assert deleted_trans is None

        # Assert that an activity log was created
        log_stmt = select(ActivityLog).order_by(ActivityLog.id.desc())
        latest_log = db.session.execute(log_stmt).scalars().first()
        assert latest_log is not None
        assert "Deleted sell of 5.00000000 DEL from portfolio" in latest_log.description


@pytest.mark.feature
def test_investment_authorization(client, test_app):
    """
    GIVEN two users, where User 2 tries to access User 1's data
    WHEN User 2 attempts to view or delete User 1's investment transaction
    THEN the application should return a 403 Forbidden error
    """
    with test_app.app_context():
        # --- FIX: Log out any pre-existing user to guarantee a clean slate ---
        client.get("/logout", follow_redirects=True)

        # --- GIVEN ---
        # Create two separate users with proper password hashes
        user_one = User(
            username="user_one",
            email="one@test.com",
            password_hash=bcrypt.generate_password_hash("pw1").decode("utf-8"),
        )
        user_two = User(
            username="user_two",
            email="two@test.com",
            password_hash=bcrypt.generate_password_hash("pw2").decode("utf-8"),
        )
        asset = Asset(name="Secure Stock", ticker_symbol="SEC", asset_type="Stock")

        # Create a transaction belonging ONLY to user_one
        trans_of_user_one = InvestmentTransaction(
            user=user_one,
            asset=asset,
            transaction_type="buy",
            quantity=1,
            price_per_unit=1,
            transaction_date=datetime.now(),
        )
        db.session.add_all([user_one, user_two, asset, trans_of_user_one])
        db.session.commit()

        # --- WHEN ---
        # Log in as user_two
        login_response = client.post(
            "/login", data={"email": "two@test.com", "password": "pw2"}
        )
        # Good practice to assert the login was successful
        assert login_response.status_code == 302  # 302 is a successful redirect

        # User two attempts to access user one's data
        edit_response = client.get(f"/portfolio/edit/{trans_of_user_one.id}")
        delete_response = client.post(f"/portfolio/delete/{trans_of_user_one.id}")

        # --- THEN ---
        # Assert that both attempts were forbidden
        assert edit_response.status_code == 403
        assert delete_response.status_code == 403
