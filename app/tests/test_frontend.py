import pytest
import httpx # httpx is used directly by the client fixture
from fastapi import status # Import status
from app.main import app # Import your FastAPI app

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

# Note: The conftest.py provides a 'client' fixture, not 'async_client'.
# The tests below will use 'client' as per conftest.py.

async def test_get_login_page(client: httpx.AsyncClient): # Changed async_client to client
    response = await client.get("/login")
    assert response.status_code == status.HTTP_200_OK
    assert "<h1>Login</h1>" in response.text # Check for case-sensitive match as in template

async def test_get_signup_page(client: httpx.AsyncClient): # Changed async_client to client
    response = await client.get("/signup")
    assert response.status_code == status.HTTP_200_OK
    assert "<h1>Sign Up</h1>" in response.text # Check for case-sensitive match

async def test_get_dashboard_unauthenticated(client: httpx.AsyncClient): # Changed async_client to client
    response = await client.get("/dashboard", follow_redirects=False) # Don't follow redirects
    assert response.status_code == status.HTTP_302_FOUND
    # Check if the location header is present and contains /login
    assert "location" in response.headers
    assert "/login" in response.headers["location"]

# More advanced test: Signup, Login, then Dashboard access
# This requires the test database to be active and sessions to work with httpx.AsyncClient.
# IMPORTANT: This test relies on a clean database state. The current conftest.py only cleans
# the database per session, not per function. This test might fail or affect other tests
# if run multiple times or alongside other tests that modify user data, unless a
# function-scoped database cleaning fixture (like the placeholder 'clean_db_session_for_test')
# is implemented and used.
async def test_full_auth_flow_and_dashboard_access(client: httpx.AsyncClient): # Changed async_client to client. Removed non-existent fixture.
    # The clean_db_session_for_test fixture was specified but does not exist in conftest.py.
    # This test will proceed without it, which may lead to issues if data persists.

    # 1. Sign Up a new user
    # Use a unique username/email for each test run if DB is not cleaned per test.
    # For now, using fixed values and relying on session-level cleanup.
    signup_data = {
        "username": "testfrontenduser_fullflow", # Made username unique for this test
        "email": "testfrontend_fullflow@example.com", # Made email unique
        "password": "testpassword"
    }
    response = await client.post("/signup", data=signup_data, follow_redirects=False)
    assert response.status_code == status.HTTP_303_SEE_OTHER # Redirect after POST
    assert "location" in response.headers
    assert "/login" in response.headers["location"]
    assert "Signup+successful" in response.headers["location"]

    # 2. Login with the new user
    login_data = {
        "username": signup_data["username"], 
        "password": "testpassword"
    }
    response = await client.post("/login", data=login_data, follow_redirects=False)
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert "location" in response.headers
    assert "/dashboard" in response.headers["location"]
    
    # Check for the session cookie
    assert "fake_session_user_id" in response.cookies
    # session_cookie = response.cookies["fake_session_user_id"] # Not used directly later

    # 3. Access Dashboard with the session cookie
    # httpx.AsyncClient automatically handles cookies set by the server for subsequent requests.
    dashboard_response = await client.get("/dashboard", follow_redirects=False)
    
    assert dashboard_response.status_code == status.HTTP_200_OK
    assert "<h1>Dashboard</h1>" in dashboard_response.text
    assert f"Welcome, {signup_data['username']}!" in dashboard_response.text # Check for username

    # 4. Logout
    logout_response = await client.get("/logout", follow_redirects=False)
    assert logout_response.status_code == status.HTTP_303_SEE_OTHER
    assert "location" in logout_response.headers
    assert "/login" in logout_response.headers["location"]
    assert "Logged+out+successfully" in logout_response.headers["location"]
    
    # Check that cookie is cleared (httpx typically shows it as expired or max-age=0)
    assert "fake_session_user_id" in logout_response.cookies
    # A common way to "delete" a cookie is to set its Max-Age to 0 or Expires to a past date.
    # httpx will reflect this. For example, its value might be empty or attributes might indicate deletion.
    # For this test, we rely on the application correctly instructing the browser to clear it.

    # Verify dashboard is no longer accessible (client should not send the session cookie anymore if logout was effective)
    # However, the cookie might still be in the client's cookie jar but marked as expired.
    # The server should ignore an invalid/expired cookie.
    dashboard_after_logout = await client.get("/dashboard", follow_redirects=False)
    assert dashboard_after_logout.status_code == status.HTTP_302_FOUND
    assert "location" in dashboard_after_logout.headers
    assert "/login" in dashboard_after_logout.headers["location"]
