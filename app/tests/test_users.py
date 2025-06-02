import pytest
from httpx import AsyncClient
from fastapi import status  # For status codes
from src.models.models import User


@pytest.mark.asyncio
async def test_create_user_success(client: AsyncClient):
    user_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "password123",
    }
    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert "id" in data
    assert "hashed_password" not in data  # Ensure password is not returned
    assert "is_admin" not in data # Ensure is_admin is not returned

    # Login as the created user
    login_data = {"username": user_data["username"], "password": user_data["password"]}
    login_response = await client.post("/api/v1/users/token", data=login_data)
    assert login_response.status_code == status.HTTP_200_OK
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify user is in DB by trying to get them
    user_id = data["id"]
    response = await client.get(f"/api/v1/users/{user_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == user_data["email"]


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client: AsyncClient):
    user_data = {
        "username": "testuser1",
        "email": "testuser1@example.com",
        "password": "password123",
    }
    response1 = await client.post("/api/v1/users/", json=user_data)
    assert response1.status_code == status.HTTP_200_OK

    user_data_duplicate_email = {
        "username": "testuser2",  # Different username
        "email": "testuser1@example.com",  # Same email
        "password": "password456",
    }
    response2 = await client.post("/api/v1/users/", json=user_data_duplicate_email)
    assert response2.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        "user with this email already exists" in response2.json()["detail"].lower()
    )  # Adjusted to match router message


@pytest.mark.asyncio
async def test_create_user_duplicate_username(client: AsyncClient):
    user_data = {
        "username": "testuser_unique_username",
        "email": "unique_email@example.com",
        "password": "password123",
    }
    response1 = await client.post("/api/v1/users/", json=user_data)
    assert response1.status_code == status.HTTP_200_OK

    user_data_duplicate_username = {
        "username": "testuser_unique_username",  # Same username
        "email": "another_unique_email@example.com",  # Different email
        "password": "password456",
    }
    response2 = await client.post("/api/v1/users/", json=user_data_duplicate_username)
    assert response2.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        "user with this username already exists" in response2.json()["detail"].lower()
    )  # Adjusted


@pytest.mark.asyncio
async def test_read_user_not_found(
    client: AsyncClient, normal_user_token_headers: dict[str, str] # Changed
):
    response = await client.get(
        "/api/v1/users/99999", headers=normal_user_token_headers # Changed
    )  # Non-existent user ID
    assert response.status_code == status.HTTP_404_NOT_FOUND


# --- START AUTHENTICATION/AUTHORIZATION TESTS ---
# Fixtures normal_user, admin_user, normal_user_token_headers, admin_user_token_headers are from conftest.py


# Helper function to create a user (can be moved to conftest if used by many test files)
# This helper is defined in other test files, ensure it's available or redefine.
# For now, assuming it's accessible or will be defined if needed.
async def create_test_user_for_auth(
    client: AsyncClient, username: str, email: str, password: str = "password123"
) -> dict:
    user_data = {"username": username, "email": email, "password": password}
    # This endpoint is public for user creation
    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == status.HTTP_200_OK, (
        f"Failed to create user {username}: {response.text}"
    )
    return response.json()


async def get_user_token_headers(
    client: AsyncClient, username: str, password: str = "password123"
) -> dict[str, str]:
    login_data = {"username": username, "password": password}
    res = await client.post("/api/v1/users/token", data=login_data)
    assert res.status_code == 200, (
        f"Failed to log in {username}. Status: {res.status_code}, Response: {res.text}"
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# User Update Authorization Tests
@pytest.mark.asyncio
async def test_update_own_user_details(
    client: AsyncClient, normal_user_token_headers: dict[str, str], normal_user: User
):
    update_data = {"email": "updated_normal_user@example.com"}
    response = await client.put(
        f"/api/v1/users/{normal_user.id}",
        json=update_data,
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == update_data["email"]
    assert "is_admin" not in response.json()


@pytest.mark.asyncio
async def test_normal_user_cannot_update_other_user(
    client: AsyncClient, normal_user_token_headers: dict[str, str], normal_user: User
):
    # Create 'other_user'
    other_user_data = await create_test_user_for_auth(
        client, "otheruser_update_target", "other_update_target@example.com"
    )
    other_user_id = other_user_data["id"]

    assert normal_user.id != other_user_id, (
        "Normal user and other user should have different IDs"
    )

    update_data = {"email": "other_user_hacked@example.com"}
    response = await client.put(
        f"/api/v1/users/{other_user_id}",
        json=update_data,
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_normal_user_cannot_make_self_admin( # Test remains relevant
    client: AsyncClient, normal_user_token_headers: dict[str, str], normal_user: User
):
    # User trying to set is_admin to True for themselves
    update_data = {"is_admin": True}
    response = await client.put(
        f"/api/v1/users/{normal_user.id}", # Use normal_user.id
        json=update_data,
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK # The request is successful, but is_admin is ignored
    # The user is not made admin because UserUpdate schema doesn't have is_admin,
    # and the User model itself doesn't have is_admin.
    # We can also check that the response does not contain is_admin.
    assert "is_admin" not in response.json()


# User Delete Authorization Tests
@pytest.mark.asyncio
async def test_normal_user_can_delete_self(client: AsyncClient):
    # Create a new user specifically for this test to avoid issues with existing fixtures' tokens
    user_to_delete_data = await create_test_user_for_auth(
        client, "user_self_delete", "self_delete@example.com"
    )
    user_to_delete_id = user_to_delete_data["id"]
    user_to_delete_headers = await get_user_token_headers(client, "user_self_delete")

    response = await client.delete(
        f"/api/v1/users/{user_to_delete_id}", headers=user_to_delete_headers
    )
    assert response.status_code == status.HTTP_200_OK

    # Verify deletion
    get_response = await client.get(
        f"/api/v1/users/{user_to_delete_id}", headers=user_to_delete_headers
    )  # Token won't work anymore
    assert get_response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_normal_user_cannot_delete_other_user(
    client: AsyncClient, normal_user_token_headers: dict[str, str], normal_user: User
):
    # Create 'other_user' to be the target
    other_user_data = await create_test_user_for_auth(
        client, "otheruser_delete_target", "other_delete_target@example.com"
    )
    other_user_id = other_user_data["id"]

    assert normal_user.id != other_user_id, (
        "Normal user and other user should have different IDs"
    )

    response = await client.delete(
        f"/api/v1/users/{other_user_id}", headers=normal_user_token_headers
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


# The original tests for creating users (test_create_user_success, etc.) are still valid as user creation is public.
# The original tests for reading/updating/deleting specific users without auth tokens (e.g., test_read_user_not_found)
# should now fail with 401 if they target protected endpoints, or be adapted if they are still relevant
# (e.g., testing 404 for a non-existent user with an admin token).
# For example, test_read_user_not_found should now use normal_user_token_headers.

# All tests below this line are effectively removed by this diff if they were part of the search block.
# This includes:
# - test_read_user_not_found_authed
# - test_read_users_with_data_authed
# - All Admin Impersonation Tests
# - test_read_users_with_data (the second one)

@pytest.mark.asyncio
async def test_update_user_success(client: AsyncClient):
    # Create initial user
    user_data = {
        "username": "update_me",
        "email": "update_me@example.com",
        "password": "P@ssw0rd",  # Changed to a valid password
    }
    create_response = await client.post("/api/v1/users/", json=user_data)
    assert create_response.status_code == status.HTTP_200_OK
    user_id = create_response.json()["id"]

    # Get auth token for the created user
    login_response = await client.post(
        "/api/v1/users/token",
        data={"username": user_data["username"], "password": user_data["password"]},
    )
    assert login_response.status_code == status.HTTP_200_OK
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    update_data = {
        "username": "updated_username",
        "email": "updated_email@example.com",
    }
    update_response = await client.put(
        f"/api/v1/users/{user_id}", json=update_data, headers=headers
    )
    assert update_response.status_code == status.HTTP_200_OK
    updated_user = update_response.json()
    assert updated_user["username"] == update_data["username"]
    assert updated_user["email"] == update_data["email"]

    # Verify by getting the user again, re-login to get a new token with the updated username
    new_login_data = {
        "username": update_data["username"],  # Use the new username
        "password": user_data["password"],  # Original password
    }
    new_login_response = await client.post("/api/v1/users/token", data=new_login_data)
    assert new_login_response.status_code == status.HTTP_200_OK
    new_token = new_login_response.json()["access_token"]
    new_headers = {"Authorization": f"Bearer {new_token}"}

    get_response = await client.get(
        f"/api/v1/users/{user_id}", headers=new_headers
    )  # Use new headers
    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json()["username"] == update_data["username"]
    assert "is_admin" not in get_response.json()


@pytest.mark.asyncio
async def test_update_user_not_found(
    client: AsyncClient, normal_user_token_headers: dict[str, str] # Changed
):
    update_data = {"username": "ghost_updater"}
    response = await client.put(
        "/api/v1/users/99999", json=update_data, headers=normal_user_token_headers # Changed
    )  # Non-existent user ID
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_user_email_conflict(client: AsyncClient):
    user1 = {
        "username": "user1_conflict",
        "email": "user1_conflict@example.com",
        "password": "password123",
    }
    user2 = {
        "username": "user2_conflict",
        "email": "user2_conflict@example.com",
        "password": "password123",
    }
    resp1 = await client.post("/api/v1/users/", json=user1)
    assert resp1.status_code == status.HTTP_200_OK
    resp2 = await client.post("/api/v1/users/", json=user2)
    assert resp2.status_code == status.HTTP_200_OK
    user2_id = resp2.json()["id"]

    # Get auth token for user2
    login_response = await client.post(
        "/api/v1/users/token",
        data={"username": user2["username"], "password": user2["password"]},
    )
    assert login_response.status_code == status.HTTP_200_OK
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    update_data = {
        "email": user1["email"]
    }  # Try to update user2's email to user1's email
    response = await client.put(
        f"/api/v1/users/{user2_id}", json=update_data, headers=headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_user_success(
    client: AsyncClient, normal_user_token_headers: dict[str, str] # Added normal_user_token_headers for verification
):
    # Create user to be deleted
    user_data = {
        "username": "to_be_deleted",
        "email": "delete_me@example.com",
        "password": "password123",
    }
    create_response = await client.post("/api/v1/users/", json=user_data)
    assert create_response.status_code == status.HTTP_200_OK
    user_id = create_response.json()["id"]

    # Get auth token for the created user ("to_be_deleted")
    login_data_tobedeleted = {"username": user_data["username"], "password": user_data["password"]}
    login_response_tobedeleted = await client.post("/api/v1/users/token", data=login_data_tobedeleted)
    assert login_response_tobedeleted.status_code == status.HTTP_200_OK
    token_tobedeleted = login_response_tobedeleted.json()["access_token"]
    headers_tobedeleted = {"Authorization": f"Bearer {token_tobedeleted}"}

    # Delete user with their own token
    delete_response = await client.delete(f"/api/v1/users/{user_id}", headers=headers_tobedeleted)
    assert delete_response.status_code == status.HTTP_200_OK

    # Verify user's token is now invalid
    get_response_after_delete = await client.get(f"/api/v1/users/{user_id}", headers=headers_tobedeleted)
    assert get_response_after_delete.status_code == status.HTTP_401_UNAUTHORIZED

    # Verify user is actually deleted using another authenticated user's token
    get_response_with_other_user = await client.get(
        f"/api/v1/users/{user_id}", headers=normal_user_token_headers # normal_user is presumably different
    )
    assert get_response_with_other_user.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_user_not_found(
    client: AsyncClient, normal_user_token_headers: dict[str, str] # Changed
):
    response = await client.delete(
        "/api/v1/users/99999", headers=normal_user_token_headers # Changed
    )  # Non-existent user ID
    assert response.status_code == status.HTTP_404_NOT_FOUND
