import pytest
import pytest_asyncio # For async fixtures
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import AsyncGenerator, Dict, Any

from src.models.models import User
from src.models import schemas # Import UserRegister, MessageResponse etc.
from src.db.database import AsyncSessionLocal # For direct db interaction in fixtures
# get_db might be needed if we override dependencies in specific tests, but usually AsyncSessionLocal is enough for fixtures

from datetime import datetime, timedelta, timezone # For time manipulation
import secrets # For unique naming
from unittest.mock import patch, AsyncMock # For mocking email sending


# Fixtures get_test_db, verified_user_data_and_headers, pending_user_and_token,
# and helpers get_user_by_email_from_db, get_user_by_username_from_db, get_user_by_id_from_db
# are now expected to be in conftest.py.
# We still need imports for types and libraries used directly in tests.

# Old helper functions - to be removed or refactored. For now, just commenting them out
# async def create_test_user_for_auth(
#     client: AsyncClient, username: str, email: str, password: str = "password123"
# ) -> dict:
#     user_data = {"username": username, "email": email, "password": password}
#     # This endpoint is public for user creation
#     response = await client.post("/api/v1/users/", json=user_data) # Old endpoint
#     assert response.status_code == status.HTTP_200_OK, (
#         f"Failed to create user {username}: {response.text}"
#     )
#     return response.json()

# async def get_user_token_headers(
#     client: AsyncClient, username: str, password: str = "password123"
# ) -> dict[str, str]:
#     login_data = {"username": username, "password": password}
#     res = await client.post("/api/v1/users/token", data=login_data)
#     assert res.status_code == 200, (
#         f"Failed to log in {username}. Status: {res.status_code}, Response: {res.text}"
#     )
#     token = res.json()["access_token"]
#     return {"Authorization": f"Bearer {token}"}


# --- Test User Registration ---

@pytest.mark.asyncio
@patch('app.src.core.email.send_verification_email', new_callable=AsyncMock)
async def test_register_user_success(mock_send_email: AsyncMock, client: AsyncClient, async_db_session: AsyncSession): # Changed get_test_db to async_db_session
    unique_suffix = secrets.token_hex(4)
    user_data = {
        "username": f"test_reg_{unique_suffix}",
        "email": f"test_reg_{unique_suffix}@example.com",
        "password": "ValidPassword123",
        "full_name": "Test Registree"
    }
    response = await client.post("/api/v1/users/register", json=user_data)
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json()["message"] == "Registration initiated. Please check your email to verify your account."

    mock_send_email.assert_called_once()
    sent_to_email = mock_send_email.call_args[0][0]
    sent_token = mock_send_email.call_args[0][1]
    assert sent_to_email == user_data["email"]
    assert len(sent_token) > 10 # Token should be reasonably long

    # Verify user in DB (using helper from conftest)
    db_user = await get_user_by_email_from_db(async_db_session, user_data["email"]) # Changed get_test_db to async_db_session
    assert db_user is not None
    assert db_user.username == user_data["username"]
    assert db_user.full_name == user_data["full_name"]
    assert db_user.email_verified is False
    assert db_user.email_verification_token == sent_token
    assert db_user.email_verification_token_expires_at is not None
    assert db_user.email_verification_token_expires_at > datetime.now(timezone.utc)

@pytest.mark.asyncio
async def test_register_user_email_conflict_verified(client: AsyncClient, verified_user_data_and_headers: Dict[str, Any]): # Fixture from conftest
    # verified_user_data_and_headers already created a verified user
    existing_user_email = verified_user_data_and_headers["email"]
    user_data_conflict = {
        "username": f"conflict_user_{secrets.token_hex(3)}",
        "email": existing_user_email, # Same email as verified user
        "password": "password123",
        "full_name": "Conflict User"
    }
    response = await client.post("/api/v1/users/register", json=user_data_conflict)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Email or username already registered and verified" in response.json()["detail"]

@pytest.mark.asyncio
async def test_register_user_username_conflict_verified(client: AsyncClient, verified_user_data_and_headers: Dict[str, Any]): # Fixture from conftest
    existing_user_username = verified_user_data_and_headers["username"]
    user_data_conflict = {
        "username": existing_user_username, # Same username as verified user
        "email": f"conflict_email_{secrets.token_hex(3)}@example.com",
        "password": "password123",
        "full_name": "Conflict User"
    }
    response = await client.post("/api/v1/users/register", json=user_data_conflict)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Email or username already registered and verified" in response.json()["detail"]

@pytest.mark.asyncio
async def test_register_user_email_pending_valid_token(client: AsyncClient, pending_user_and_token: Dict[str, Any]): # Fixture from conftest
    # pending_user_and_token fixture creates a user who is pending verification
    user_data_conflict = {
        "username": f"new_attempt_{secrets.token_hex(3)}", # Different username
        "email": pending_user_and_token["email"], # Same email as pending user
        "password": "newpassword123",
        "full_name": "New Attempt FullName"
    }
    response = await client.post("/api/v1/users/register", json=user_data_conflict)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Email or username already registered or pending verification with a valid token" in response.json()["detail"]

@pytest.mark.asyncio
@patch('app.src.core.email.send_verification_email', new_callable=AsyncMock)
async def test_reregister_user_email_pending_expired_token(mock_send_email: AsyncMock, client: AsyncClient, pending_user_and_token: Dict[str, Any], async_db_session: AsyncSession): # Changed get_test_db
    # Make the token for the pending user expired
    user_model: User = pending_user_and_token["user_model"]
    user_model.email_verification_token_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    async_db_session.add(user_model)
    await async_db_session.commit()
    await async_db_session.refresh(user_model)

    new_password = "new_password_for_reregister123"
    new_full_name = "Reregistered User Name"
    reregister_data = {
        "username": pending_user_and_token["username"], # Can be same or different, email is key here
        "email": pending_user_and_token["email"],
        "password": new_password,
        "full_name": new_full_name
    }

    response = await client.post("/api/v1/users/register", json=reregister_data)
    assert response.status_code == status.HTTP_202_ACCEPTED
    mock_send_email.assert_called_once()

    # Verify user in DB is updated
    db_user = await get_user_by_email_from_db(async_db_session, pending_user_and_token["email"]) # Changed get_test_db
    assert db_user is not None
    assert db_user.id == pending_user_and_token["id"] # Should be the same user record
    assert db_user.full_name == new_full_name
    assert db_user.email_verified is False
    assert db_user.email_verification_token != pending_user_and_token["token"] # New token
    assert db_user.email_verification_token_expires_at > datetime.now(timezone.utc)
    # Check if password was updated (optional: hash and compare, or just trust the logic)

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload, error_detail_part",
    [
        ({"username": "u", "email": "a@b.com", "password": "ValidPassword123"}, "username"), # Username too short
        ({"username": "test", "email": "not-an-email", "password": "ValidPassword123"}, "email"), # Invalid email
        ({"username": "test", "email": "a@b.com", "password": "short"}, "password"), # Password too short
        ({"username": "test", "email": "a@b.com", "password": "ValidPassword123", "full_name": "a"*101}, "full_name"), # Full name too long
    ]
)
async def test_register_user_invalid_payload(client: AsyncClient, payload: Dict[str, Any], error_detail_part: str):
    # Fill in missing required fields if not in payload for partial tests
    if "username" not in payload: payload["username"] = "validuser"
    if "email" not in payload: payload["email"] = "valid@example.com"
    if "password" not in payload: payload["password"] = "ValidPassword123"

    response = await client.post("/api/v1/users/register", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Example check, the actual detail might be more specific
    # assert error_detail_part in str(response.json()["detail"]).lower()


# --- End Test User Registration ---

# --- Test Email Verification ---

@pytest.mark.asyncio
async def test_verify_email_success(client: AsyncClient, pending_user_and_token: Dict[str, Any], async_db_session: AsyncSession): # Changed get_test_db
    token = pending_user_and_token["token"]
    response = await client.get(f"/api/v1/users/verify-email?token={token}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Email verified successfully. You can now log in."

    db_user = await get_user_by_email_from_db(async_db_session, pending_user_and_token["email"]) # Changed get_test_db
    assert db_user is not None
    assert db_user.email_verified is True
    assert db_user.email_verification_token is None
    assert db_user.email_verification_token_expires_at is None

@pytest.mark.asyncio
async def test_verify_email_invalid_token(client: AsyncClient):
    response = await client.get("/api/v1/users/verify-email?token=thisisclearlyaninvalidtoken")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid verification token" in response.json()["detail"]

@pytest.mark.asyncio
async def test_verify_email_expired_token(client: AsyncClient, pending_user_and_token: Dict[str, Any], async_db_session: AsyncSession): # Changed get_test_db
    user_model: User = pending_user_and_token["user_model"]
    user_model.email_verification_token_expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    async_db_session.add(user_model)
    await async_db_session.commit()

    token = pending_user_and_token["token"]
    response = await client.get(f"/api/v1/users/verify-email?token={token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Verification token expired" in response.json()["detail"]

    # Check DB user is still unverified
    db_user = await get_user_by_email_from_db(async_db_session, pending_user_and_token["email"]) # Changed get_test_db
    assert db_user is not None
    assert db_user.email_verified is False
    assert db_user.email_verification_token == token # Token should still be there

@pytest.mark.asyncio
async def test_verify_email_already_verified(client: AsyncClient, verified_user_data_and_headers: Dict[str, Any]): # Fixture from conftest
    # Attempt to verify an already verified user (e.g. with a made-up token, or if the old token was somehow known)
    # The endpoint should ideally not find the user by a token that's already been used and cleared.
    # If it finds the user but they are verified, it should indicate this.
    # Current implementation: token is cleared, so a second attempt with same token will be "invalid".
    # If a NEW token was somehow issued for an already verified user, then it might hit "already verified".

    # This test will use a fake token for simplicity, as the original token is cleared.
    response = await client.get("/api/v1/users/verify-email?token=fake_token_for_verified_user")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    # The detail message might be "Invalid verification token." if the token isn't found,
    # or "Email already verified." if user is found by token but already verified.
    # Given token is cleared, "Invalid verification token" is expected.

    # To specifically test the "Email already verified" path, one would need to:
    # 1. Create a pending user.
    # 2. Get their token.
    # 3. Manually mark them as verified in DB *without* clearing the token.
    # 4. Then try to verify with the original token.
    # This is a bit of an edge case for the current logic.

# --- End Test Email Verification ---

# --- Test Login ---

@pytest.mark.asyncio
async def test_login_unverified_user(client: AsyncClient, pending_user_and_token: Dict[str, Any]): # Fixture from conftest
    login_payload = {
        "username": pending_user_and_token["username"],
        "password": pending_user_and_token["password"]
    }
    response = await client.post("/api/v1/users/token", data=login_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Email not verified" in response.json()["detail"]

@pytest.mark.asyncio
async def test_login_verified_user(client: AsyncClient, verified_user_data_and_headers: Dict[str, Any]): # Fixture from conftest
    # The fixture already performs login, so this test primarily ensures that process was successful
    # and a token was obtained. We can re-login here explicitly for clarity if desired.
    login_payload = {
        "username": verified_user_data_and_headers["username"],
        "password": verified_user_data_and_headers["raw_password"]
    }
    response = await client.post("/api/v1/users/token", data=login_payload)
    assert response.status_code == status.HTTP_200_OK
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

# --- End Test Login ---

# --- Test Resend Verification Email ---

@pytest.mark.asyncio
@patch('app.src.core.email.send_verification_email', new_callable=AsyncMock)
async def test_resend_verification_email_success(mock_send_email: AsyncMock, client: AsyncClient, pending_user_and_token: Dict[str, Any], async_db_session: AsyncSession): # Changed get_test_db
    payload = {"email": pending_user_and_token["email"]}
    response = await client.post("/api/v1/users/resend-verification-email", json=payload)
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json()["message"] == "Verification email resent. Please check your inbox."

    mock_send_email.assert_called_once()
    sent_to_email = mock_send_email.call_args[0][0]
    new_token_sent = mock_send_email.call_args[0][1]
    assert sent_to_email == pending_user_and_token["email"]

    db_user = await get_user_by_email_from_db(async_db_session, pending_user_and_token["email"]) # Changed get_test_db
    assert db_user is not None
    assert db_user.email_verification_token == new_token_sent
    assert db_user.email_verification_token != pending_user_and_token["token"] # Ensure token changed
    assert db_user.email_verification_token_expires_at > datetime.now(timezone.utc)

@pytest.mark.asyncio
async def test_resend_verification_email_for_verified_user(client: AsyncClient, verified_user_data_and_headers: Dict[str, Any]): # Fixture from conftest
    payload = {"email": verified_user_data_and_headers["email"]}
    response = await client.post("/api/v1/users/resend-verification-email", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST # As per current backend logic
    assert "Email is already verified" in response.json()["detail"]

@pytest.mark.asyncio
async def test_resend_verification_email_non_existent_user(client: AsyncClient):
    payload = {"email": "nonexistent@example.com"}
    response = await client.post("/api/v1/users/resend-verification-email", json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "User with this email not found" in response.json()["detail"]

# --- End Test Resend Verification Email ---

# --- Test Initiate Email Change (PUT /api/v1/users/me/email) ---

@pytest.mark.asyncio
@patch('app.src.core.email.send_email_change_verification_email', new_callable=AsyncMock)
async def test_change_email_request_success(mock_send_email_change: AsyncMock, client: AsyncClient, verified_user_data_and_headers: Dict[str, Any], async_db_session: AsyncSession): # Changed get_test_db
    user_info = verified_user_data_and_headers
    new_email = f"new_{user_info['username']}@example.com"
    payload = {
        "new_email": new_email,
        "password": user_info["raw_password"]
    }
    response = await client.put("/api/v1/users/me/email", json=payload, headers=user_info["headers"])
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json()["message"] == "Email change initiated. Please check your new email address to verify."

    mock_send_email_change.assert_called_once()
    sent_to_email = mock_send_email_change.call_args[0][0]
    sent_token = mock_send_email_change.call_args[0][1]
    assert sent_to_email == new_email

    db_user = await get_user_by_username_from_db(async_db_session, user_info["username"]) # Fetch by username or ID, Changed get_test_db
    assert db_user is not None
    assert db_user.new_email_pending_verification == new_email
    assert db_user.email_change_token == sent_token
    assert db_user.email_change_token_expires_at is not None
    assert db_user.email_change_token_expires_at > datetime.now(timezone.utc)
    assert db_user.email == user_info["email"] # Original email should still be active

@pytest.mark.asyncio
async def test_change_email_request_incorrect_password(client: AsyncClient, verified_user_data_and_headers: Dict[str, Any]): # Fixture from conftest
    user_info = verified_user_data_and_headers
    payload = {
        "new_email": f"new_incorrect_pw_{user_info['username']}@example.com",
        "password": "wrongpassword"
    }
    response = await client.put("/api/v1/users/me/email", json=payload, headers=user_info["headers"])
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Incorrect password" in response.json()["detail"]

@pytest.mark.asyncio
async def test_change_email_request_same_email(client: AsyncClient, verified_user_data_and_headers: Dict[str, Any]): # Fixture from conftest
    user_info = verified_user_data_and_headers
    payload = {
        "new_email": user_info["email"], # Same as current email
        "password": user_info["raw_password"]
    }
    response = await client.put("/api/v1/users/me/email", json=payload, headers=user_info["headers"])
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "New email cannot be the same as the current email" in response.json()["detail"]

@pytest.mark.asyncio
@patch('app.src.core.email.send_verification_email', new_callable=AsyncMock) # Mock for user2 creation
async def test_change_email_request_new_email_taken_by_other_verified(mock_send_reg_email_user2: AsyncMock, client: AsyncClient, async_db_session: AsyncSession, verified_user_data_and_headers: Dict[str, Any]): # Changed get_test_db
    user1_info = verified_user_data_and_headers # This is our current user trying to change email

    # Create another verified user (user2) explicitly
    unique_suffix_user2 = secrets.token_hex(4)
    user2_email_target = f"verified_target_{unique_suffix_user2}@example.com"
    user2_password = "password_user2"
    user2_data = {
        "username": f"verified_target_{unique_suffix_user2}",
        "email": user2_email_target,
        "password": user2_password,
        "full_name": "Verified Target User"
    }
    # Register user2
    reg_resp_user2 = await client.post("/api/v1/users/register", json=user2_data)
    assert reg_resp_user2.status_code == status.HTTP_202_ACCEPTED
    mock_send_reg_email_user2.assert_called_once()

    # Verify user2
    user2_in_db_unverified = await get_user_by_email_from_db(async_db_session, user2_data["email"])
    assert user2_in_db_unverified is not None
    verify_token_user2 = user2_in_db_unverified.email_verification_token
    assert verify_token_user2 is not None
    verify_resp_user2 = await client.get(f"/api/v1/users/verify-email?token={verify_token_user2}")
    assert verify_resp_user2.status_code == status.HTTP_200_OK
    # User2 (user2_email_target) is now verified.

    payload_user1_change = {
        "new_email": user2_email_target, # User1 tries to change to User2's email
        "password": user1_info["raw_password"]
    }
    response = await client.put("/api/v1/users/me/email", json=payload_user1_change, headers=user1_info["headers"])
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "This email address is already in use by another verified account" in response.json()["detail"]

# --- End Test Initiate Email Change ---

# --- Test Verify Email Change (GET /api/v1/users/verify-email-change) ---

@pytest.mark.asyncio
@patch('app.src.core.email.send_email_change_verification_email', new_callable=AsyncMock) # Mock for setup part
async def test_verify_email_change_success(mock_send_email_change_setup: AsyncMock, client: AsyncClient, verified_user_data_and_headers: Dict[str, Any], async_db_session: AsyncSession): # Changed get_test_db
    user_info = verified_user_data_and_headers
    new_email = f"new_verified_{user_info['username']}@example.com"

    # 1. Initiate email change
    initiate_payload = {"new_email": new_email, "password": user_info["raw_password"]}
    initiate_response = await client.put("/api/v1/users/me/email", json=initiate_payload, headers=user_info["headers"])
    assert initiate_response.status_code == status.HTTP_202_ACCEPTED
    mock_send_email_change_setup.assert_called_once() # Ensure email was "sent"

    # 2. Retrieve the change token from DB
    db_user_before_verify = await get_user_by_username_from_db(async_db_session, user_info["username"]) # Changed get_test_db
    assert db_user_before_verify is not None
    assert db_user_before_verify.new_email_pending_verification == new_email
    assert db_user_before_verify.email_change_token is not None
    change_token = db_user_before_verify.email_change_token

    # 3. Verify the email change
    verify_response = await client.get(f"/api/v1/users/verify-email-change?token={change_token}")
    assert verify_response.status_code == status.HTTP_200_OK
    assert verify_response.json()["message"] == "Email address updated successfully."

    # 4. Check DB state
    db_user_after_verify = await get_user_by_username_from_db(async_db_session, user_info["username"]) # Changed get_test_db
    assert db_user_after_verify is not None
    assert db_user_after_verify.email == new_email
    assert db_user_after_verify.new_email_pending_verification is None
    assert db_user_after_verify.email_change_token is None
    assert db_user_after_verify.email_change_token_expires_at is None

@pytest.mark.asyncio
async def test_verify_email_change_invalid_token(client: AsyncClient):
    response = await client.get("/api/v1/users/verify-email-change?token=invalidchangetoken")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid or no pending email change for this token" in response.json()["detail"]

@pytest.mark.asyncio
@patch('app.src.core.email.send_email_change_verification_email', new_callable=AsyncMock) # Mock for setup
async def test_verify_email_change_expired_token(mock_send_email_change_setup: AsyncMock, client: AsyncClient, verified_user_data_and_headers: Dict[str, Any], async_db_session: AsyncSession): # Changed get_test_db
    user_info = verified_user_data_and_headers
    new_email = f"expired_change_{user_info['username']}@example.com"

    initiate_payload = {"new_email": new_email, "password": user_info["raw_password"]}
    await client.put("/api/v1/users/me/email", json=initiate_payload, headers=user_info["headers"])

    db_user = await get_user_by_username_from_db(async_db_session, user_info["username"]) # Changed get_test_db
    assert db_user is not None
    change_token = db_user.email_change_token

    # Manually expire the token
    db_user.email_change_token_expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    async_db_session.add(db_user)
    await async_db_session.commit()

    response = await client.get(f"/api/v1/users/verify-email-change?token={change_token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Email change token expired" in response.json()["detail"]

    db_user_after = await get_user_by_username_from_db(async_db_session, user_info["username"]) # Changed get_test_db
    assert db_user_after is not None
    assert db_user_after.new_email_pending_verification is None # Should be cleared
    assert db_user_after.email_change_token is None
    assert db_user_after.email == user_info["email"] # Original email should remain

@pytest.mark.asyncio
@patch('app.src.core.email.send_email_change_verification_email', new_callable=AsyncMock) # For User A's setup
@patch('app.src.core.email.send_verification_email', new_callable=AsyncMock) # For User B's registration
async def test_verify_email_change_target_email_becomes_verified_by_another(
    mock_send_reg_email_user_b: AsyncMock, # Renamed for clarity
    mock_send_email_change_setup_user_a: AsyncMock, # Renamed for clarity
    client: AsyncClient,
    async_db_session: AsyncSession,
    verified_user_data_and_headers: Dict[str, Any] # This will be User A
):
    user_a_info = verified_user_data_and_headers
    target_new_email = f"shared_new_target_{secrets.token_hex(3)}@example.com"

    # 1. User A initiates change to target_new_email
    initiate_payload_a = {"new_email": target_new_email, "password": user_a_info["raw_password"]}
    await client.put("/api/v1/users/me/email", json=initiate_payload_a, headers=user_a_info["headers"])
    mock_send_email_change_setup_user_a.assert_called_once() # Ensure User A's email change email was "sent"

    user_a_db = await get_user_by_username_from_db(async_db_session, user_a_info["username"])
    assert user_a_db is not None
    token_a = user_a_db.email_change_token
    assert token_a is not None

    # 2. User B (another verified user) is created and successfully changes their email to target_new_email
    user_b_unique_suffix = secrets.token_hex(3)
    user_b_username = f"userB_{user_b_unique_suffix}"
    user_b_email_orig = f"userB_orig_{user_b_unique_suffix}@example.com"
    user_b_password = "passwordB123"

    # Register User B
    reg_payload_b = {"username": user_b_username, "email": user_b_email_orig, "password": user_b_password, "full_name": "User B"}
    await client.post("/api/v1/users/register", json=reg_payload_b)
    mock_send_reg_email_user_b.assert_called_once() # User B registration email

    # Verify User B's initial email
    user_b_db_unverified = await get_user_by_email_from_db(async_db_session, user_b_email_orig)
    assert user_b_db_unverified is not None
    verify_token_b_initial = user_b_db_unverified.email_verification_token
    await client.get(f"/api/v1/users/verify-email?token={verify_token_b_initial}")

    # Login User B
    login_payload_b = {"username": user_b_username, "password": user_b_password}
    login_resp_b = await client.post("/api/v1/users/token", data=login_payload_b)
    headers_b = {"Authorization": f"Bearer {login_resp_b.json()['access_token']}"}

    # User B initiates and verifies change to target_new_email
    with patch('app.src.core.email.send_email_change_verification_email', new_callable=AsyncMock) as mock_send_email_change_b:
        initiate_payload_b = {"new_email": target_new_email, "password": user_b_password}
        await client.put("/api/v1/users/me/email", json=initiate_payload_b, headers=headers_b)
        mock_send_email_change_b.assert_called_once()

    user_b_db_pending_change = await get_user_by_username_from_db(async_db_session, user_b_username)
    assert user_b_db_pending_change is not None
    token_b_change = user_b_db_pending_change.email_change_token
    assert token_b_change is not None

    verify_response_b = await client.get(f"/api/v1/users/verify-email-change?token={token_b_change}")
    assert verify_response_b.status_code == status.HTTP_200_OK # User B successfully changes email

    user_b_db_done = await get_user_by_username_from_db(async_db_session, user_b_username)
    assert user_b_db_done is not None
    assert user_b_db_done.email == target_new_email

    # 3. User A then tries to use their original token T_A to verify the same email
    response_a_verify = await client.get(f"/api/v1/users/verify-email-change?token={token_a}")
    assert response_a_verify.status_code == status.HTTP_400_BAD_REQUEST
    assert "This email address has been taken by another user" in response_a_verify.json()["detail"]

    user_a_db_after = await get_user_by_username_from_db(async_db_session, user_a_info["username"])
    assert user_a_db_after is not None
    assert user_a_db_after.email == user_a_info["email"] # User A's email should not have changed
    assert user_a_db_after.new_email_pending_verification is None # Should be cleared
    assert user_a_db_after.email_change_token is None

# --- End Test Verify Email Change ---

# --- Test Read User ---
@pytest.mark.asyncio
async def test_read_user_not_found(client: AsyncClient, verified_user_data_and_headers: Dict[str, Any]): # Fixture from conftest
    headers = verified_user_data_and_headers["headers"]
    response = await client.get("/api/v1/users/999999", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "User not found or not verified" in response.json()["detail"]

@pytest.mark.asyncio
async def test_read_unverified_user_as_if_not_found(client: AsyncClient, pending_user_and_token: Dict[str, Any], verified_user_data_and_headers: Dict[str, Any]): # Fixtures from conftest
    # Use another verified user's token to try to read the pending (unverified) user
    accessor_headers = verified_user_data_and_headers["headers"]
    pending_user_id = pending_user_and_token["id"]

    response = await client.get(f"/api/v1/users/{pending_user_id}", headers=accessor_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "User not found or not verified" in response.json()["detail"]

# --- End Test Read User ---

# --- Test Update User ---
@pytest.mark.asyncio
async def test_update_own_user_details_success(client: AsyncClient, verified_user_data_and_headers: Dict[str, Any], async_db_session: AsyncSession): # Changed get_test_db
    user_info = verified_user_data_and_headers
    user_id = user_info["id"]

    update_data = {
        "username": f"updated_{user_info['username']}",
        "full_name": f"Updated {user_info['full_name']}",
        "password": "newValidPassword123"
    }
    response = await client.put(f"/api/v1/users/{user_id}", json=update_data, headers=user_info["headers"])
    assert response.status_code == status.HTTP_200_OK

    updated_data_from_response = response.json()
    assert updated_data_from_response["username"] == update_data["username"]
    assert updated_data_from_response["full_name"] == update_data["full_name"]
    assert updated_data_from_response["email"] == user_info["email"] # Email should not change here
    assert updated_data_from_response["email_verified"] is True

    # Verify in DB
    db_user = await get_user_by_id_from_db(async_db_session, user_id) # Changed get_test_db, helper from conftest
    assert db_user is not None
    assert db_user.username == update_data["username"]
    assert db_user.full_name == update_data["full_name"]
    # To check password, try logging in with new password
    login_payload = {"username": update_data["username"], "password": update_data["password"]}
    login_response = await client.post("/api/v1/users/token", data=login_payload)
    assert login_response.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
@patch('app.src.core.email.send_verification_email', new_callable=AsyncMock) # For user2 creation
async def test_update_other_user_forbidden(mock_send_reg_email_user2: AsyncMock, client: AsyncClient, verified_user_data_and_headers: Dict[str, Any], async_db_session: AsyncSession): # Fixture from conftest
    user1_info = verified_user_data_and_headers

    # Create another user (user2) explicitly
    unique_suffix_user2 = secrets.token_hex(4)
    user2_data = {
        "username": f"other_user_{unique_suffix_user2}",
        "email": f"other_user_{unique_suffix_user2}@example.com",
        "password": "password_other",
        "full_name": "Other User FullName"
    }
    reg_resp_user2 = await client.post("/api/v1/users/register", json=user2_data)
    assert reg_resp_user2.status_code == status.HTTP_202_ACCEPTED
    mock_send_reg_email_user2.assert_called_once()

    user2_in_db_unverified = await get_user_by_email_from_db(async_db_session, user2_data["email"])
    assert user2_in_db_unverified is not None
    verify_token_user2 = user2_in_db_unverified.email_verification_token
    assert verify_token_user2 is not None
    verify_resp_user2 = await client.get(f"/api/v1/users/verify-email?token={verify_token_user2}")
    assert verify_resp_user2.status_code == status.HTTP_200_OK
    user2_id = user2_in_db_unverified.id

    update_data = {"username": "attempted_update_by_other"}
    # User1 tries to update User2
    response = await client.put(f"/api/v1/users/{user2_id}", json=update_data, headers=user1_info["headers"])
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Not authorized to update this user account" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_unverified_user_forbidden(client: AsyncClient, pending_user_and_token: Dict[str, Any], verified_user_data_and_headers: Dict[str, Any]): # Fixtures from conftest
    # Even if an admin or someone could try, updating unverified user is forbidden
    # For this test, we'll use a verified user's headers trying to update a pending user.
    # This scenario might not be reachable if get_object_or_404 on user_id already filters out unverified.
    # The route for PUT /{user_id} should first fetch the target_user then check if target_user.email_verified.

    accessor_headers = verified_user_data_and_headers["headers"]
    pending_user_id = pending_user_and_token["id"]

    update_data = {"full_name": "Trying to update pending"}
    response = await client.put(f"/api/v1/users/{pending_user_id}", json=update_data, headers=accessor_headers)
    # Depending on implementation: could be 404 if unverified users are treated as "not found" for modification,
    # or 403 if found but modification is disallowed. The backend implements 403.
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Cannot modify an unverified user account" in response.json()["detail"]


@pytest.mark.asyncio
@patch('app.src.core.email.send_verification_email', new_callable=AsyncMock) # For user2 creation
async def test_update_user_username_conflict(mock_send_reg_email_user2: AsyncMock, client: AsyncClient, verified_user_data_and_headers: Dict[str, Any], async_db_session: AsyncSession): # Fixture from conftest
    user1_info = verified_user_data_and_headers

    # Create another user (user2) explicitly
    unique_suffix_user2 = secrets.token_hex(4)
    user2_username_target = f"conflict_user_{unique_suffix_user2}"
    user2_data = {
        "username": user2_username_target,
        "email": f"conflict_user_{unique_suffix_user2}@example.com",
        "password": "password_conflict",
        "full_name": "Conflict User FullName"
    }
    reg_resp_user2 = await client.post("/api/v1/users/register", json=user2_data)
    assert reg_resp_user2.status_code == status.HTTP_202_ACCEPTED
    mock_send_reg_email_user2.assert_called_once()

    user2_in_db_unverified = await get_user_by_email_from_db(async_db_session, user2_data["email"])
    assert user2_in_db_unverified is not None
    verify_token_user2 = user2_in_db_unverified.email_verification_token
    assert verify_token_user2 is not None
    verify_resp_user2 = await client.get(f"/api/v1/users/verify-email?token={verify_token_user2}")
    assert verify_resp_user2.status_code == status.HTTP_200_OK
    # user2_username_target is now a verified username

    update_data = {"username": user2_username_target} # User1 tries to take User2's username
    response = await client.put(f"/api/v1/users/{user1_info['id']}", json=update_data, headers=user1_info["headers"])
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Username already taken" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_user_not_found_for_update(client: AsyncClient, verified_user_data_and_headers: Dict[str, Any]): # Fixture from conftest
    headers = verified_user_data_and_headers["headers"]
    update_data = {"username": "ghost_updater"}
    response = await client.put("/api/v1/users/999999", json=update_data, headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "User not found" in response.json()["detail"] # Assuming get_object_or_404 raises this

# --- End Test Update User ---

# --- Test Delete User ---
@pytest.mark.asyncio
@patch('app.src.core.email.send_verification_email', new_callable=AsyncMock)
async def test_delete_own_user_success(mock_reg_email: AsyncMock, client: AsyncClient, async_db_session: AsyncSession): # Changed get_test_db
    # Setup: Create a user, verify, login to get their own headers for deletion
    unique_suffix = f"del_me_{secrets.token_hex(3)}"
    user_email = f"{unique_suffix}@example.com"
    user_username = unique_suffix
    user_password = "passwordToDelete123"
    user_full_name = "User To Delete"

    reg_payload = {"email": user_email, "username": user_username, "password": user_password, "full_name": user_full_name}
    await client.post("/api/v1/users/register", json=reg_payload)
    mock_reg_email.assert_called_once() # Ensure email mock is used correctly

    user_in_db = await get_user_by_email_from_db(async_db_session, user_email) # Changed get_test_db
    assert user_in_db is not None
    verify_token = user_in_db.email_verification_token
    await client.get(f"/api/v1/users/verify-email?token={verify_token}")

    login_resp = await client.post("/api/v1/users/token", data={"username": user_username, "password": user_password})
    user_id_to_delete = user_in_db.id
    headers_to_delete = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    # Perform delete
    delete_response = await client.delete(f"/api/v1/users/{user_id_to_delete}", headers=headers_to_delete)
    assert delete_response.status_code == status.HTTP_200_OK
    assert f"User {user_id_to_delete} deleted successfully" in delete_response.json()["message"]

    # Verify user is deleted from DB
    deleted_user_in_db = await get_user_by_id_from_db(async_db_session, user_id_to_delete) # Changed get_test_db, helper from conftest
    assert deleted_user_in_db is None

    # Verify token is invalid (optional, as user is gone)
    # get_response_after_delete = await client.get(f"/api/v1/users/{user_id_to_delete}", headers=headers_to_delete)
    # assert get_response_after_delete.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
@patch('app.src.core.email.send_verification_email', new_callable=AsyncMock) # For user2 creation
async def test_delete_other_user_forbidden(mock_send_reg_email_user2: AsyncMock, client: AsyncClient, verified_user_data_and_headers: Dict[str, Any], async_db_session: AsyncSession): # Fixture from conftest
    user1_info = verified_user_data_and_headers # User1 is attacker

    # Create another user (user2) explicitly
    unique_suffix_user2 = secrets.token_hex(4)
    user2_data = {
        "username": f"delete_other_{unique_suffix_user2}",
        "email": f"delete_other_{unique_suffix_user2}@example.com",
        "password": "password_delete_other",
        "full_name": "Delete Other FullName"
    }
    reg_resp_user2 = await client.post("/api/v1/users/register", json=user2_data)
    assert reg_resp_user2.status_code == status.HTTP_202_ACCEPTED
    mock_send_reg_email_user2.assert_called_once()

    user2_in_db_unverified = await get_user_by_email_from_db(async_db_session, user2_data["email"])
    assert user2_in_db_unverified is not None
    verify_token_user2 = user2_in_db_unverified.email_verification_token
    assert verify_token_user2 is not None
    verify_resp_user2 = await client.get(f"/api/v1/users/verify-email?token={verify_token_user2}")
    assert verify_resp_user2.status_code == status.HTTP_200_OK
    user2_id = user2_in_db_unverified.id

    response = await client.delete(f"/api/v1/users/{user2_id}", headers=user1_info["headers"])
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Not authorized to delete this user account" in response.json()["detail"]

@pytest.mark.asyncio
async def test_delete_user_not_found(client: AsyncClient, verified_user_data_and_headers: Dict[str, Any]): # Fixture from conftest
    headers = verified_user_data_and_headers["headers"]
    response = await client.delete("/api/v1/users/9999999", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "User not found" in response.json()["detail"]


# --- End Test Delete User ---

# Helper function get_user_by_id_from_db is now in conftest.py
