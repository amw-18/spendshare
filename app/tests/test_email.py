import pytest
from unittest.mock import patch, MagicMock, AsyncMock # Added AsyncMock
import httpx # Needed for httpx.RequestError and for mocking AsyncClient.post

from pydantic import EmailStr

from app.src.core.email import send_email_mailgun, send_verification_email
from app.src.config import Settings

# Sample data for testing
TEST_EMAIL_TO: EmailStr = "testrecipient@example.com"
TEST_SUBJECT: str = "Test Subject"
TEST_HTML_CONTENT: str = "<h1>Test HTML Content</h1>"
TEST_TOKEN: str = "test_verification_token"

@pytest.fixture
def mock_settings_mailgun_configured(monkeypatch):
    """Mocks settings to simulate Mailgun being fully configured."""
    mock = MagicMock(spec=Settings)
    mock.MAILGUN_API_KEY = "fake_api_key"
    mock.MAILGUN_DOMAIN_NAME = "fakedoman.example.com"
    mock.MAILGUN_API_BASE_URL = "https://api.mailgun.net/v3"
    mock.MAIL_FROM_EMAIL = "noreply@fakedoman.example.com"
    mock.FRONTEND_URL = "http://localhost:3000"

    monkeypatch.setattr("app.src.core.email.get_settings", lambda: mock)
    return mock

@pytest.fixture
def mock_settings_mailgun_not_configured(monkeypatch):
    """Mocks settings to simulate Mailgun NOT being configured (API key or domain missing)."""
    mock = MagicMock(spec=Settings)
    mock.MAILGUN_API_KEY = None # Key for this fixture
    mock.MAILGUN_DOMAIN_NAME = None # Key for this fixture
    mock.MAILGUN_API_BASE_URL = "https://api.mailgun.net/v3"
    mock.MAIL_FROM_EMAIL = "noreply@fakedoman.example.com" # From email might still exist
    mock.FRONTEND_URL = "http://localhost:3000"

    monkeypatch.setattr("app.src.core.email.get_settings", lambda: mock)
    return mock

@pytest.fixture
def mock_settings_mailgun_no_from_email(monkeypatch):
    """Mocks settings to simulate Mailgun configured but MAIL_FROM_EMAIL is missing."""
    mock = MagicMock(spec=Settings)
    mock.MAILGUN_API_KEY = "fake_api_key"
    mock.MAILGUN_DOMAIN_NAME = "fakedoman.example.com"
    mock.MAILGUN_API_BASE_URL = "https://api.mailgun.net/v3"
    mock.MAIL_FROM_EMAIL = None # Key for this fixture
    mock.FRONTEND_URL = "http://localhost:3000"

    monkeypatch.setattr("app.src.core.email.get_settings", lambda: mock)
    return mock


@pytest.mark.asyncio # Added asyncio mark
@patch("app.src.core.email.httpx.AsyncClient.post", new_callable=AsyncMock) # Mock httpx.AsyncClient.post
async def test_send_email_mailgun_success(mock_post, mock_settings_mailgun_configured): # Changed to async def
    """Test successful email sending via Mailgun."""
    mock_response = MagicMock(spec=httpx.Response) # Mock httpx.Response
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    result = await send_email_mailgun( # Added await
        email_to=TEST_EMAIL_TO,
        subject=TEST_SUBJECT,
        html_content=TEST_HTML_CONTENT
    )

    assert result is True
    mock_post.assert_called_once_with(
        f"{mock_settings_mailgun_configured.MAILGUN_API_BASE_URL}/{mock_settings_mailgun_configured.MAILGUN_DOMAIN_NAME}/messages",
        auth=("api", mock_settings_mailgun_configured.MAILGUN_API_KEY),
        data={
            "from": f"SpendShare <{mock_settings_mailgun_configured.MAIL_FROM_EMAIL}>",
            "to": [TEST_EMAIL_TO],
            "subject": TEST_SUBJECT,
            "html": TEST_HTML_CONTENT
        }
    )

@pytest.mark.asyncio # Added asyncio mark
@patch("app.src.core.email.httpx.AsyncClient.post", new_callable=AsyncMock) # Mock httpx.AsyncClient.post
async def test_send_email_mailgun_api_failure(mock_post, mock_settings_mailgun_configured): # Changed to async def
    """Test Mailgun API failure (e.g., 4xx or 5xx response)."""
    mock_response = MagicMock(spec=httpx.Response) # Mock httpx.Response
    mock_response.status_code = 400
    mock_response.text = "Bad Request - Invalid API Key or something"
    mock_post.return_value = mock_response

    result = await send_email_mailgun( # Added await
        email_to=TEST_EMAIL_TO,
        subject=TEST_SUBJECT,
        html_content=TEST_HTML_CONTENT
    )

    assert result is False
    assert mock_post.called # Ensure we attempted the API call

@pytest.mark.asyncio # Added asyncio mark
@patch("app.src.core.email.httpx.AsyncClient.post", new_callable=AsyncMock) # Mock httpx.AsyncClient.post
async def test_send_email_mailgun_request_exception(mock_post, mock_settings_mailgun_configured): # Changed to async def
    """Test scenario where httpx.post raises an exception (e.g., network error)."""
    mock_post.side_effect = httpx.RequestError("Simulated connection error") # Use httpx.RequestError

    result = await send_email_mailgun( # Added await
        email_to=TEST_EMAIL_TO,
        subject=TEST_SUBJECT,
        html_content=TEST_HTML_CONTENT
    )
    assert result is False

@pytest.mark.asyncio # Added asyncio mark
async def test_send_email_mailgun_not_configured_apikey_domain(mock_settings_mailgun_not_configured): # Changed to async def
    """Test send_email_mailgun when API key or domain is not configured."""
    # This fixture specifically sets API_KEY and DOMAIN_NAME to None
    with patch("app.src.core.email.httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post: # Mock httpx.AsyncClient.post
        result = await send_email_mailgun( # Added await
            email_to=TEST_EMAIL_TO,
            subject=TEST_SUBJECT,
            html_content=TEST_HTML_CONTENT
        )
        assert result is False
        mock_post.assert_not_called()

@pytest.mark.asyncio # Added asyncio mark
async def test_send_email_mailgun_not_configured_from_email(mock_settings_mailgun_no_from_email): # Changed to async def
    """Test send_email_mailgun when MAIL_FROM_EMAIL is not configured."""
    with patch("app.src.core.email.httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post: # Mock httpx.AsyncClient.post
        result = await send_email_mailgun( # Added await
            email_to=TEST_EMAIL_TO,
            subject=TEST_SUBJECT,
            html_content=TEST_HTML_CONTENT
        )
        assert result is False
        mock_post.assert_not_called()


# Test for one of the higher-level functions, e.g., send_verification_email
@pytest.mark.asyncio
@patch("app.src.core.email.send_email_mailgun", new_callable=AsyncMock) # Mock the actual call to Mailgun, ensure it's an AsyncMock
async def test_send_verification_email_calls_mailgun_function(mock_send_email_mailgun_actual, mock_settings_mailgun_configured):
    """
    Test that send_verification_email (as an example high-level func)
    calls the core send_email_mailgun function with correctly formatted parameters.
    """
    # For an async mock, the return value of the coroutine should be set.
    # If send_email_mailgun is an async function, its mock should also behave like one.
    # AsyncMock automatically handles this if you set return_value.
    mock_send_email_mailgun_actual.return_value = True # Assume internal call to Mailgun "succeeds"

    # Call the function being tested
    await send_verification_email(to_email=TEST_EMAIL_TO, token=TEST_TOKEN)

    # Define expected values based on how send_verification_email constructs them
    expected_subject = "Verify your email for Your SpendShare Account"
    # Access FRONTEND_URL from the mock_settings_mailgun_configured fixture directly
    frontend_url = mock_settings_mailgun_configured.FRONTEND_URL
    expected_verification_link = f"{frontend_url}/verify-email?token={TEST_TOKEN}"

    # Assert that our mock of send_email_mailgun was called once
    mock_send_email_mailgun_actual.assert_called_once()

    # Inspect the call arguments to send_email_mailgun
    # call_args is a tuple (args, kwargs) or a named tuple CallArgs(args, kwargs)
    # In our case, send_email_mailgun is called with keyword arguments.
    actual_call_kwargs = mock_send_email_mailgun_actual.call_args.kwargs

    assert actual_call_kwargs.get("email_to") == TEST_EMAIL_TO
    assert actual_call_kwargs.get("subject") == expected_subject

    # Check that the generated HTML content contains key elements
    html_content = actual_call_kwargs.get("html_content")
    assert html_content is not None
    assert "Please verify your email address by clicking the link below:" in html_content
    assert f'<a href="{expected_verification_link}">{expected_verification_link}</a>' in html_content
    assert "If you did not request this, please ignore this email." in html_content

# Instructions for running tests:
# From the project root:
# 1. Ensure venv is active: `source app/.venv/bin/activate` (if .venv is in app/)
# 2. Run pytest: `pytest app/tests/test_email.py`
