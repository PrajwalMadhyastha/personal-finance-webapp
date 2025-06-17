# tests/test_admin.py
from finance_tracker.models import User
from finance_tracker import db
import pytest


@pytest.mark.feature
def test_admin_access_denied_for_regular_user(auth_client):
    """
    GIVEN a logged-in regular user
    WHEN the user attempts to access the /admin page
    THEN the response should be a 403 Forbidden error
    """
    response = auth_client.get("/admin")
    assert response.status_code == 403


@pytest.mark.feature
def test_admin_access_granted(logged_in_admin_client):
    """
    GIVEN a client logged in as an admin user
    WHEN the admin accesses the /admin page
    THEN the response should be successful (200 OK)
    """
    response = logged_in_admin_client.get("/admin")
    assert response.status_code == 200
    assert b"Admin Dashboard" in response.data


@pytest.mark.feature
def test_admin_link_not_visible_for_regular_user(auth_client):
    """
    GIVEN a logged-in regular user
    WHEN the user views the dashboard
    THEN the 'Admin' link should NOT be present
    """
    response = auth_client.get("/dashboard")
    assert response.status_code == 200
    assert b'href="/admin"' not in response.data


@pytest.mark.feature
def test_admin_link_is_visible_for_admin_user(logged_in_admin_client):
    """
    GIVEN a client logged in as an admin user
    WHEN the admin views the dashboard
    THEN the 'Admin' link SHOULD be present
    """
    response = logged_in_admin_client.get("/dashboard")
    assert response.status_code == 200
    assert b'href="/admin"' in response.data


@pytest.mark.feature
def test_admin_can_promote_user(logged_in_admin_client, test_app):
    """
    GIVEN a logged-in admin user and a regular user
    WHEN the admin makes a POST request to promote the regular user
    THEN the regular user's 'is_admin' flag should be set to True
    """
    # GIVEN: A second, regular user exists in the database
    with test_app.app_context():
        regular_user = User(
            username="regularuser", email="regular@test.com", password_hash="..."
        )
        db.session.add(regular_user)
        db.session.commit()
        regular_user_id = regular_user.id  # Get the ID for the URL

    # WHEN: The logged-in admin sends a POST request to the promote URL
    promote_url = f"/admin/user/promote/{regular_user_id}"
    response = logged_in_admin_client.post(promote_url, follow_redirects=True)

    # THEN: The request should be successful and the user should be promoted
    assert response.status_code == 200
    assert (
        b"has been promoted to an admin" in response.data
    )  # Check for the flash message

    with test_app.app_context():
        promoted_user = db.session.get(User, regular_user_id)
        assert promoted_user.is_admin is True


@pytest.mark.feature
def test_regular_user_cannot_promote(auth_client, test_app):
    """
    GIVEN a logged-in regular user
    WHEN the user attempts to make a POST request to the promote URL
    THEN the application should return a 403 Forbidden error
    """
    # GIVEN: A target user to be promoted exists
    with test_app.app_context():
        target_user = User(
            username="targetuser", email="target@test.com", password_hash="..."
        )
        db.session.add(target_user)
        db.session.commit()
        target_user_id = target_user.id

    # WHEN: The logged-in regular user (from auth_client) sends the POST request
    promote_url = f"/admin/user/promote/{target_user_id}"
    response = auth_client.post(promote_url)

    # THEN: The request is forbidden
    assert response.status_code == 403
