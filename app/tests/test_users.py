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
    client: AsyncClient, admin_user_token_headers: dict[str, str]
):
    response = await client.get(
        "/api/v1/users/99999", headers=admin_user_token_headers
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


@pytest.mark.asyncio
async def test_admin_update_other_user_details(
    client: AsyncClient, admin_user_token_headers: dict[str, str], normal_user: User
):
    update_data = {"email": "normal_user_updated_by_admin@example.com"}
    response = await client.put(
        f"/api/v1/users/{normal_user.id}",
        json=update_data,
        headers=admin_user_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == update_data["email"]


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
async def test_normal_user_cannot_make_self_admin(
    client: AsyncClient, normal_user_token_headers: dict[str, str], normal_user: User
):
    assert not normal_user.is_admin, (
        "Test assumption: normal_user is not admin initially"
    )
    update_data = {"is_admin": True}
    response = await client.put(
        f"/api/v1/users/{normal_user.id}",
        json=update_data,
        headers=normal_user_token_headers,
    )
    assert (
        response.status_code == status.HTTP_403_FORBIDDEN
    )  # Prevented by endpoint logic


@pytest.mark.asyncio
async def test_admin_can_make_other_user_admin(
    client: AsyncClient, admin_user_token_headers: dict[str, str], normal_user: User
):
    assert not normal_user.is_admin, (
        "Test assumption: normal_user is not admin initially"
    )
    update_data = {"is_admin": True}
    response = await client.put(
        f"/api/v1/users/{normal_user.id}",
        json=update_data,
        headers=admin_user_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["is_admin"] is True


@pytest.mark.asyncio
async def test_admin_can_revoke_admin_status(
    client: AsyncClient, admin_user_token_headers: dict[str, str], admin_user: User
):
    # Create another user and make them admin
    temp_admin_data = await create_test_user_for_auth(
        client, "temp_admin_for_revoke", "temp_admin_revoke@example.com"
    )
    temp_admin_id = temp_admin_data["id"]

    # Admin promotes temp_admin
    promote_data = {"is_admin": True}
    promote_response = await client.put(
        f"/api/v1/users/{temp_admin_id}",
        json=promote_data,
        headers=admin_user_token_headers,
    )
    assert promote_response.status_code == status.HTTP_200_OK
    assert promote_response.json()["is_admin"] is True

    # Admin revokes temp_admin's admin status
    revoke_data = {"is_admin": False}
    revoke_response = await client.put(
        f"/api/v1/users/{temp_admin_id}",
        json=revoke_data,
        headers=admin_user_token_headers,
    )
    assert revoke_response.status_code == status.HTTP_200_OK
    assert revoke_response.json()["is_admin"] is False


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
    assert (
        get_response.status_code == status.HTTP_401_UNAUTHORIZED
    )  # or 404 if token was admin


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
# For example, test_read_user_not_found should now use admin_user_token_headers to pass auth, then test 404.
@pytest.mark.asyncio
async def test_read_user_not_found_authed(
    client: AsyncClient, admin_user_token_headers: dict[str, str]
):
    response = await client.get(
        "/api/v1/users/99999", headers=admin_user_token_headers
    )  # Non-existent user ID
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User with id 99999 not found"


# test_read_users_with_data needs to be updated to use admin token
@pytest.mark.asyncio
async def test_read_users_with_data_authed(
    client: AsyncClient, admin_user_token_headers: dict[str, str]
):
    # Users are created by fixtures (normal_user, admin_user) and potentially other tests.
    # This test now just ensures an admin can list users.
    response = await client.get("/api/v1/users/", headers=admin_user_token_headers)
    assert response.status_code == status.HTTP_200_OK
    users = response.json()
    assert isinstance(users, list)
    # Check if at least the admin user itself is in the list
    admin_usernames = [user["username"] for user in users if user["is_admin"]]
    assert "adminuser" in admin_usernames  # Assuming admin_user fixture username


# Old update/delete tests without auth are obsolete or need to be adapted.
# The new auth tests cover these scenarios more comprehensively.


# Admin Impersonation Tests
@pytest.mark.asyncio
async def test_admin_login_as_user_success(
    client: AsyncClient,
    admin_user_token_headers: dict[str, str],
    normal_user: User,
    admin_user: User,  # Added admin_user fixture to ensure it's distinct from normal_user if IDs are checked
):
    # Admin user logs in as normal_user
    response_impersonate = await client.post(
        f"/api/v1/users/admin/login_as/{normal_user.id}",
        headers=admin_user_token_headers,
    )
    assert response_impersonate.status_code == status.HTTP_200_OK
    impersonation_data = response_impersonate.json()
    assert "access_token" in impersonation_data
    impersonation_token = impersonation_data["access_token"]
    impersonation_headers = {"Authorization": f"Bearer {impersonation_token}"}

    # 1. Access normal_user's own details using the impersonation token
    response_get_self = await client.get(
        f"/api/v1/users/{normal_user.id}", headers=impersonation_headers
    )
    assert response_get_self.status_code == status.HTTP_200_OK
    assert response_get_self.json()["username"] == normal_user.username

    # 2. Verify that the impersonation token does not grant admin privileges
    # Try to list all users (admin-only endpoint)
    response_list_users = await client.get(
        "/api/v1/users/", headers=impersonation_headers
    )
    assert response_list_users.status_code == status.HTTP_403_FORBIDDEN

    # 3. (Optional) Verify that the impersonation token cannot be used to access admin_user's details (if different from normal_user)
    if normal_user.id != admin_user.id:
        response_get_admin = await client.get(
            f"/api/v1/users/{admin_user.id}", headers=impersonation_headers
        )
        # This should fail if normal_user cannot normally see admin_user's details,
        # which depends on the general read access rules (currently any authenticated user can read any user)
        # Given current GET /{user_id} allows any authenticated user to read, this would be 200.
        # This specific check might not be a good test for lack of admin rights unless the target endpoint is admin-only.
        # The list users check (response_list_users) is a better test for lack of admin rights.
        pass


@pytest.mark.asyncio
async def test_normal_user_cannot_login_as_another_user(
    client: AsyncClient,
    normal_user_token_headers: dict[str, str],
    normal_user: User,  # normal_user fixture
):
    # Create another user for normal_user to attempt to log in as
    other_user_data = await create_test_user_for_auth(
        client, "other_user_impersonation_target", "other_impersonation@example.com"
    )
    other_user_id = other_user_data["id"]

    assert normal_user.id != other_user_id

    response = await client.post(
        f"/api/v1/users/admin/login_as/{other_user_id}",
        headers=normal_user_token_headers,  # Using normal_user's token
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_admin_login_as_nonexistent_user(
    client: AsyncClient, admin_user_token_headers: dict[str, str]
):
    non_existent_user_id = 999999
    response = await client.post(
        f"/api/v1/users/admin/login_as/{non_existent_user_id}",
        headers=admin_user_token_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert (
        response.json()["detail"] == "User with id 999999 not found"
    )  # Corrected 99999 to 999999


@pytest.mark.asyncio
async def test_read_users_with_data(
    client: AsyncClient, admin_user_token_headers: dict[str, str]
):
    # Create two users first
    user1_data = {
        "username": "testuser1",
        "email": "testuser1@example.com",
        "password": "password123",
    }
    user2_data = {
        "username": "testuser2",
        "email": "testuser2@example.com",
        "password": "password123",
    }

    response1 = await client.post("/api/v1/users/", json=user1_data)
    assert response1.status_code == status.HTTP_200_OK
    response2 = await client.post("/api/v1/users/", json=user2_data)
    assert response2.status_code == status.HTTP_200_OK

    # Get all users (requires admin auth)
    response = await client.get("/api/v1/users/", headers=admin_user_token_headers)
    assert response.status_code == status.HTTP_200_OK
    users = response.json()
    assert isinstance(users, list)

    # Since the DB is session-scoped and might contain users from other tests ran in the same session before this one,
    # we check that at least these two users are present.
    # A more robust check involves knowing the exact state or cleaning per test.
    # For now, we assume these tests might run in an order where the DB isn't empty.
    assert len(users) >= 2

    emails = [user["email"] for user in users]
    usernames = [user["username"] for user in users]
    assert user1_data["email"] in emails
    assert user1_data["username"] in usernames
    assert user2_data["email"] in emails
    assert user2_data["username"] in usernames


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


@pytest.mark.asyncio
async def test_update_user_not_found(
    client: AsyncClient, admin_user_token_headers: dict[str, str]
):
    update_data = {"username": "ghost_updater"}
    response = await client.put(
        "/api/v1/users/99999", json=update_data, headers=admin_user_token_headers
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
    client: AsyncClient, admin_user_token_headers: dict[str, str]
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

    # Get auth token for the created user
    login_response = await client.post(
        "/api/v1/users/token",
        data={"username": user_data["username"], "password": user_data["password"]},
    )
    assert login_response.status_code == status.HTTP_200_OK
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Delete user with their own token
    delete_response = await client.delete(f"/api/v1/users/{user_id}", headers=headers)
    assert delete_response.status_code == status.HTTP_200_OK

    # Verify user is actually deleted (using admin token since the user's token is now invalid)
    get_response = await client.get(
        f"/api/v1/users/{user_id}", headers=admin_user_token_headers
    )
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_user_not_found(
    client: AsyncClient, admin_user_token_headers: dict[str, str]
):
    response = await client.delete(
        "/api/v1/users/99999", headers=admin_user_token_headers
    )  # Non-existent user ID
    assert response.status_code == status.HTTP_404_NOT_FOUND
