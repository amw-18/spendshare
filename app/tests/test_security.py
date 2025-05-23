import pytest
from app.core.security import get_password_hash, verify_password


def test_password_hashing_and_verification():
    password = "mYsEcReTpAsSwOrD123!"

    hashed_password = get_password_hash(password)

    # Check that the hashed password is not the same as the original password
    assert hashed_password != password

    # Check that the hashed password is a string
    assert isinstance(hashed_password, str)

    # Verify the correct password
    assert verify_password(password, hashed_password)

    # Verify an incorrect password
    assert not verify_password("wRoNgPaSsWoRd!321", hashed_password)


def test_verify_password_with_different_hashes_for_same_password():
    password = "another_secure_password"

    hashed_password1 = get_password_hash(password)
    hashed_password2 = get_password_hash(password)

    # bcrypt generates a different hash each time due to salting
    assert hashed_password1 != hashed_password2

    # Both hashes should still verify correctly against the original password
    assert verify_password(password, hashed_password1)
    assert verify_password(password, hashed_password2)


def test_get_password_hash_empty_password():
    # Test how get_password_hash handles an empty string.
    # Passlib's bcrypt usually handles this by hashing it.
    password = ""
    hashed_password = get_password_hash(password)
    assert isinstance(hashed_password, str)
    assert verify_password(password, hashed_password)


# Note: Since these are not async functions, the tests don't need @pytest.mark.asyncio
# If JWT token functions were added to security.py and they were async,
# their tests would need the asyncio marker.

import pytest
from httpx import AsyncClient
from app.models.models import User # For type hinting if needed, User fixture is from conftest

# Fixtures normal_user, admin_user, normal_user_token_headers, admin_user_token_headers are imported from conftest.py

@pytest.mark.asyncio
async def test_successful_login(client: AsyncClient, normal_user: User):
    login_data = {"username": normal_user.username, "password": "password123"}
    response = await client.post("/api/v1/users/token", data=login_data)
    assert response.status_code == 200
    json_response = response.json()
    assert "access_token" in json_response
    assert json_response["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_failed_login_incorrect_password(client: AsyncClient, normal_user: User):
    login_data = {"username": normal_user.username, "password": "wrongpassword"}
    response = await client.post("/api/v1/users/token", data=login_data)
    assert response.status_code == 401 # As per HTTPException in login endpoint

@pytest.mark.asyncio
async def test_failed_login_non_existent_user(client: AsyncClient):
    login_data = {"username": "nonexistentuser", "password": "somepassword"}
    response = await client.post("/api/v1/users/token", data=login_data)
    assert response.status_code == 401 # As per HTTPException in login endpoint


# Tests for basic protected route access (GET /api/v1/users/)

@pytest.mark.asyncio
async def test_protected_route_access_denied_no_token(client: AsyncClient):
    response = await client.get("/api/v1/users/")
    assert response.status_code == 401 # FastAPI's OAuth2PasswordBearer default

@pytest.mark.asyncio
async def test_protected_route_access_denied_invalid_token(client: AsyncClient):
    headers = {"Authorization": "Bearer invalidtokenstring"}
    response = await client.get("/api/v1/users/", headers=headers)
    assert response.status_code == 401 # JWT decode error leads to 401

@pytest.mark.asyncio
async def test_protected_route_access_granted_admin_user(client: AsyncClient, admin_user_token_headers: dict[str, str]):
    # GET /api/v1/users/ is admin-only
    response = await client.get("/api/v1/users/", headers=admin_user_token_headers)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_protected_route_access_denied_normal_user_for_admin_route(client: AsyncClient, normal_user_token_headers: dict[str, str]):
    # GET /api/v1/users/ is admin-only
    response = await client.get("/api/v1/users/", headers=normal_user_token_headers)
    # This should be 403 Forbidden because the user is authenticated but not authorized (not admin)
    assert response.status_code == 403
