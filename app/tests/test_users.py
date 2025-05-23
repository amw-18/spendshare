import pytest
from httpx import AsyncClient
from fastapi import status  # For status codes


@pytest.mark.asyncio
async def test_create_user_success(client: AsyncClient):
    user_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "password123",
    }
    response = await client.post("/api/v1/users/", json=user_data)
    assert (
        response.status_code == status.HTTP_200_OK
    )  # FastAPI default is 200 for POST if not specified
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert "id" in data
    assert "hashed_password" not in data  # Ensure password is not returned

    # Verify user is in DB by trying to get them
    user_id = data["id"]
    response = await client.get(f"/api/v1/users/{user_id}")
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
async def test_read_user_not_found(client: AsyncClient):
    response = await client.get("/api/v1/users/99999")  # Non-existent user ID
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User with id 99999 not found"


@pytest.mark.asyncio
async def test_read_users_with_data(client: AsyncClient):
    # Create a couple of users
    user1_data = {"username": "user_a", "email": "usera@example.com", "password": "pw1"}
    user2_data = {"username": "user_b", "email": "userb@example.com", "password": "pw2"}
    # Ensure these are created before fetching all users
    resp1 = await client.post("/api/v1/users/", json=user1_data)
    assert resp1.status_code == status.HTTP_200_OK
    resp2 = await client.post("/api/v1/users/", json=user2_data)
    assert resp2.status_code == status.HTTP_200_OK

    response = await client.get("/api/v1/users/")
    assert response.status_code == status.HTTP_200_OK
    users = response.json()

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
    user_data = {
        "username": "update_me",
        "email": "update_me@example.com",
        "password": "initial_password",
    }
    create_response = await client.post("/api/v1/users/", json=user_data)
    assert create_response.status_code == status.HTTP_200_OK
    user_id = create_response.json()["id"]

    update_data = {
        "username": "updated_username",
        "email": "updated_email@example.com",
        # Not updating password here, but could also test password update
    }
    update_response = await client.put(f"/api/v1/users/{user_id}", json=update_data)
    assert update_response.status_code == status.HTTP_200_OK
    updated_user = update_response.json()
    assert updated_user["username"] == update_data["username"]
    assert updated_user["email"] == update_data["email"]

    # Verify by getting the user again
    get_response = await client.get(f"/api/v1/users/{user_id}")
    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json()["username"] == update_data["username"]


@pytest.mark.asyncio
async def test_update_user_not_found(client: AsyncClient):
    update_data = {"username": "ghost_updater"}
    response = await client.put(
        "/api/v1/users/99999", json=update_data
    )  # Non-existent user ID
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_user_email_conflict(client: AsyncClient):
    user1 = {
        "username": "user1_conflict",
        "email": "user1_conflict@example.com",
        "password": "pw",
    }
    user2 = {
        "username": "user2_conflict",
        "email": "user2_conflict@example.com",
        "password": "pw",
    }
    resp1 = await client.post("/api/v1/users/", json=user1)
    assert resp1.status_code == status.HTTP_200_OK
    resp2 = await client.post("/api/v1/users/", json=user2)
    assert resp2.status_code == status.HTTP_200_OK
    user2_id = resp2.json()["id"]

    update_data = {
        "email": user1["email"]
    }  # Try to update user2's email to user1's email
    response = await client.put(f"/api/v1/users/{user2_id}", json=update_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_user_success(client: AsyncClient):
    user_data = {
        "username": "to_be_deleted",
        "email": "delete_me@example.com",
        "password": "shortlife",
    }
    create_response = await client.post("/api/v1/users/", json=user_data)
    assert create_response.status_code == status.HTTP_200_OK
    user_id = create_response.json()["id"]

    delete_response = await client.delete(f"/api/v1/users/{user_id}")
    assert delete_response.status_code == status.HTTP_200_OK
    # Optionally, assert the content of the deleted user response if it's meaningful
    # assert delete_response.json()["email"] == user_data["email"]

    # Verify user is actually deleted
    get_response = await client.get(f"/api/v1/users/{user_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_user_not_found(client: AsyncClient):
    response = await client.delete("/api/v1/users/99999")  # Non-existent user ID
    assert response.status_code == status.HTTP_404_NOT_FOUND
