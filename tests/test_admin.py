# tests/test_admin.py

def test_admin_access_denied_for_regular_user(auth_client):
    """
    GIVEN a logged-in regular user
    WHEN the user attempts to access the /admin page
    THEN the response should be a 403 Forbidden error
    """
    response = auth_client.get('/admin')
    assert response.status_code == 403

def test_admin_access_granted(logged_in_admin_client):
    """
    GIVEN a client logged in as an admin user
    WHEN the admin accesses the /admin page
    THEN the response should be successful (200 OK)
    """
    response = logged_in_admin_client.get('/admin')
    assert response.status_code == 200
    assert b"Admin Dashboard" in response.data

def test_admin_link_not_visible_for_regular_user(auth_client):
    """
    GIVEN a logged-in regular user
    WHEN the user views the dashboard
    THEN the 'Admin' link should NOT be present
    """
    response = auth_client.get('/dashboard')
    assert response.status_code == 200
    assert b'href="/admin"' not in response.data

def test_admin_link_is_visible_for_admin_user(logged_in_admin_client):
    """
    GIVEN a client logged in as an admin user
    WHEN the admin views the dashboard
    THEN the 'Admin' link SHOULD be present
    """
    response = logged_in_admin_client.get('/dashboard')
    assert response.status_code == 200
    assert b'href="/admin"' in response.data