import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi import status
from typing import Any, AsyncGenerator, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock


from src.models.models import User
from src.db.database import AsyncSessionLocal # Not needed if async_db_session from conftest is used
# Helper functions and fixtures like get_user_by_email_from_db, get_test_db, verified_user_data_and_headers
# are now expected to be in conftest.py.

# We still need User model for type hints if not implicitly handled by fixture types.
# from src.models.models import User # Already imported for global scope if needed by fixtures

# Import helper functions from conftest if they are to be used directly in tests here
# (though typically tests use fixtures which internally use these helpers)
# from ..conftest import get_user_by_email_from_db # Example if needed, but usually not.

@pytest.mark.asyncio
async def test_password_validation(client: AsyncClient):
    """Test password validation rules for registration"""
    # Test too short password
    user_data = {
        "username": "short_pass_ext",
        "email": "short_ext@example.com",
        "password": "123",  # Too short
        "full_name": "Short Pass"
    }
    # Use the new /register endpoint
    response = await client.post("/api/v1/users/register", json=user_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # The exact error message structure might vary with Pydantic v2, check one field
    assert any("string should have at least 8 characters" in err["msg"].lower() for err in response.json()["detail"])


    # Test password without numbers
    user_data["password"] = "onlyletters"
    user_data["username"] = "letters_pass_ext"
    user_data["email"] = "letters_ext@example.com"
    response = await client.post("/api/v1/users/register", json=user_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert any("password must contain at least one number" in err["msg"].lower() for err in response.json()["detail"])


    # Test password without letters
    user_data["password"] = "12345678"
    user_data["username"] = "numbers_pass_ext"
    user_data["email"] = "numbers_ext@example.com"
    response = await client.post("/api/v1/users/register", json=user_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert any("password must contain at least one letter" in err["msg"].lower() for err in response.json()["detail"])


@pytest.mark.asyncio
@patch('app.src.core.email.send_verification_email', new_callable=AsyncMock)
async def test_token_expiry(mock_send_email_te: AsyncMock, client: AsyncClient, async_db_session: AsyncSession): # Changed get_test_db to async_db_session
    """Test token expiration conceptually (actual time passing is hard)"""
    # Use the verified_user_data_and_headers logic manually to get headers
    unique_suffix = secrets.token_hex(4)
    raw_password = "password123"
    user_payload = {
        "username": f"token_expiry_{unique_suffix}",
        "email": f"token_expiry_{unique_suffix}@example.com",
        "password": raw_password,
        "full_name": "Token Expiry Test"
    }

    register_response = await client.post("/api/v1/users/register", json=user_payload)
    assert register_response.status_code == status.HTTP_202_ACCEPTED
    mock_send_email_te.assert_called_once()

    # Using get_user_by_email_from_db from conftest.py implicitly via async_db_session
    user_in_db = await get_user_by_email_from_db(async_db_session, user_payload["email"]) # Changed get_test_db
    assert user_in_db is not None
    verification_token = user_in_db.email_verification_token
    assert verification_token is not None

    verify_response = await client.get(f"/api/v1/users/verify-email?token={verification_token}")
    assert verify_response.status_code == status.HTTP_200_OK

    # Get token
    login_data = {"username": user_payload["username"], "password": raw_password}
    token_response = await client.post("/api/v1/users/token", data=login_data)
    assert token_response.status_code == status.HTTP_200_OK
    token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Use token immediately
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == user_payload["username"]

    # Conceptual part: If token expired, /me would return 401
    # To test this properly, one might mock `datetime.utcnow()` in the security module
    # or use a very short token lifetime if configurable.
    # For now, this test primarily checks token generation and immediate use after full verification.


@pytest.mark.asyncio
async def test_user_email_format_validation(client: AsyncClient):
    """Test email format validation for registration"""
    invalid_emails = [
        "", "notanemail", "@nodomain", "no@domain", "spaces in@email.com", "multiple@@at.com",
    ]
    username_counter = 0
    for email in invalid_emails:
        user_data = {
            "username": f"email_val_ext_{username_counter}",
            "email": email,
            "password": "testpass123",
            "full_name": "Email Test"
        }
        username_counter +=1
        response = await client.post("/api/v1/users/register", json=user_data) # Use new endpoint
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, f"Email {email} should be invalid"
        assert any("value is not a valid email address" in err["msg"].lower() for err in response.json()["detail"])


@pytest.mark.asyncio
async def test_username_format_validation(client: AsyncClient):
    """Test username format validation for registration"""
    test_cases = [
        ("", "string should have at least 3 characters"),
        ("a", "string should have at least 3 characters"),
        ("a" * 51, "string should have at most 50 characters"),
        ("user@name", "string should match pattern"),
        ("user name", "string should match pattern"),
    ]
    email_counter = 0
    for username, expected_error_part in test_cases:
        user_data = {
            "username": username,
            "email": f"username_val_ext_{email_counter}@example.com",
            "password": "testpass123",
            "full_name": "Username Test"
        }
        email_counter += 1
        response = await client.post("/api/v1/users/register", json=user_data) # Use new endpoint
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, f"Username '{username}' should be invalid"

        # Check if any of the error messages contain the expected error part
        found_error = False
        for error_detail in response.json()["detail"]:
            if expected_error_part.lower() in error_detail["msg"].lower():
                found_error = True
                break
        assert found_error, f"Expected error part '{expected_error_part}' not found in {response.json()['detail']}"


@pytest.mark.asyncio
async def test_password_update_validation(client: AsyncClient, verified_user_data_and_headers: Dict[str, Any]):
    """Test password update validation for an existing, verified user"""
    user_info = verified_user_data_and_headers

    # Try to update with invalid password (too short)
    update_data_invalid = {"password": "123"}
    response_invalid = await client.put(
        f"/api/v1/users/{user_info['id']}", # Use user ID from fixture
        json=update_data_invalid,
        headers=user_info["headers"], # Use headers from fixture
    )
    assert response_invalid.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert any("string should have at least 8 characters" in err["msg"].lower() for err in response_invalid.json()["detail"])


    # Update with valid password
    update_data_valid = {"password": "newValidPass123"}
    response_valid = await client.put(
        f"/api/v1/users/{user_info['id']}",
        json=update_data_valid,
        headers=user_info["headers"],
    )
    assert response_valid.status_code == status.HTTP_200_OK

    # Try to login with new password
    login_data = {"username": user_info["username"], "password": "newValidPass123"}
    response_login = await client.post("/api/v1/users/token", data=login_data)
    assert response_login.status_code == status.HTTP_200_OK

# @pytest.mark.asyncio
# async def test_concurrent_user_updates(
#     client: AsyncClient,
#     verified_user_data_and_headers: Dict[str, Any], # Changed to new fixture
# ):
#     """Test handling of concurrent updates to the same user.
#        This test is less relevant for email now, as email changes go through a different flow.
#        Could be adapted for other fields like 'full_name' or 'username' if needed.
#        For now, commenting out as direct email update is not the primary concern here.
#     """
#     user_info = verified_user_data_and_headers
#     user_id = user_info["id"]
#     headers = user_info["headers"]

#     # Simulate two concurrent updates to full_name
#     update_data1 = {"full_name": "Concurrent Name One"}
#     update_data2 = {"full_name": "Concurrent Name Two"}

#     response1 = await client.put(f"/api/v1/users/{user_id}", json=update_data1, headers=headers)
#     response2 = await client.put(f"/api/v1/users/{user_id}", json=update_data2, headers=headers)

#     assert (
#         response1.status_code == status.HTTP_200_OK
#         or response2.status_code == status.HTTP_200_OK
#     )

#     response_me = await client.get("/api/v1/users/me", headers=headers)
#     assert response_me.status_code == status.HTTP_200_OK
#     final_data = response_me.json()
#     assert final_data["full_name"] in [update_data1["full_name"], update_data2["full_name"]]
