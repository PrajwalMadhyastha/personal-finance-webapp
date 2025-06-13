def test_login_page_loads(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/login' page is requested (GET)
    THEN check that the response is valid
    """
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Log In" in response.data
    assert b"Need an account?" in response.data


def test_dashboard_redirects_when_not_logged_in(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/dashboard' page is requested (GET) by an unauthenticated client
    THEN check that the user is redirected to the login page
    """
    response = client.get('/dashboard', follow_redirects=True)
    # A 302 status code indicates a redirect
    assert response.status_code == 200 # After following redirect
    assert b"Please log in to access this page." in response.data
    assert b"Log In" in response.data


def test_dashboard_loads_when_logged_in(auth_client):
    """
    GIVEN an authenticated client
    WHEN the '/dashboard' page is requested (GET)
    THEN check that the dashboard is displayed
    """
    response = auth_client.get('/dashboard')
    assert response.status_code == 200
    assert b"Dashboard" in response.data
    assert b"Welcome back, testclient!" in response.data
    assert b"This Month's Budget Progress" in response.data