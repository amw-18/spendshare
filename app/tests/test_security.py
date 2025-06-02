import pytest
from httpx import AsyncClient
from src.core.security import get_password_hash, verify_password
from src.models.models import User


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
    assert response.status_code == 401  # As per HTTPException in login endpoint


@pytest.mark.asyncio
async def test_failed_login_non_existent_user(client: AsyncClient):
    login_data = {"username": "nonexistentuser", "password": "somepassword"}
    response = await client.post("/api/v1/users/token", data=login_data)
    assert response.status_code == 401  # As per HTTPException in login endpoint


# Tests for basic protected route access (e.g. GET /api/v1/users/me)
# The original tests targeted GET /api/v1/users/ which has been removed.
# New tests can be added here for /me or other protected routes if desired.


# For example, testing /api/v1/users/me:
@pytest.mark.asyncio
async def test_me_route_access_denied_no_token(client: AsyncClient):
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_route_access_denied_invalid_token(client: AsyncClient):
    headers = {"Authorization": "Bearer invalidtokenstring"}
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_route_access_granted_normal_user(
    client: AsyncClient, normal_user_token_headers: dict[str, str]
):
    response = await client.get("/api/v1/users/me", headers=normal_user_token_headers)
    assert response.status_code == 200
    # Add more assertions based on expected response, e.g., username
    # assert response.json()["username"] == "normaluser" # depends on fixture username
