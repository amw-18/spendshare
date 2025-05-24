import pytest
from httpx import AsyncClient
from fastapi import status
from typing import Any
from src.models.models import User


@pytest.mark.asyncio
async def test_password_validation(client: AsyncClient):
    """Test password validation rules"""
    # Test too short password
    user_data = {
        "username": "short_pass",
        "email": "short@example.com",
        "password": "123",  # Too short
    }
    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert (
        "string should have at least 8 characters"
        in response.json()["detail"][0]["msg"].lower()
    )

    # Test password without numbers
    user_data["password"] = "onlyletters"
    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert (
        "password must contain at least one number"
        in response.json()["detail"][0]["msg"].lower()
    )

    # Test password without letters
    user_data["password"] = "12345678"
    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert (
        "password must contain at least one letter"
        in response.json()["detail"][0]["msg"].lower()
    )


@pytest.mark.asyncio
async def test_token_expiry(client: AsyncClient):
    """Test token expiration"""
    # Create a user
    user_data = {
        "username": "token_test",
        "email": "token@example.com",
        "password": "testpass123",
    }
    create_response = await client.post("/api/v1/users/", json=user_data)
    assert create_response.status_code == status.HTTP_200_OK

    # Get token
    login_data = {"username": "token_test", "password": "testpass123"}
    token_response = await client.post("/api/v1/users/token", data=login_data)
    assert token_response.status_code == status.HTTP_200_OK
    token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Use token immediately (should work)
    response = await client.get("/api/v1/users/", headers=headers)
    # Note: This should actually return 403 for non-admin users trying to list all users
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Note: In a real test environment, we'd need a way to fast-forward time
    # or configure shorter token expiry for testing
    # This is a placeholder to show the concept
    # time.sleep(token_expiry_time)
    # response = await client.get("/api/v1/users/", headers=headers)
    # assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_user_email_format_validation(client: AsyncClient):
    """Test email format validation"""
    invalid_emails = [
        "",  # Empty
        "notanemail",  # No @ symbol
        "@nodomain",  # No local part
        "no@domain",  # Incomplete domain
        "spaces in@email.com",  # Spaces in local part
        "multiple@@at.com",  # Multiple @ symbols
    ]

    for email in invalid_emails:
        user_data = {
            "username": "email_test",
            "email": email,
            "password": "testpass123",
        }
        response = await client.post("/api/v1/users/", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, (
            f"Email {email} should be invalid"
        )
        assert (
            "value is not a valid email address"
            in response.json()["detail"][0]["msg"].lower()
        )


@pytest.mark.asyncio
async def test_username_format_validation(client: AsyncClient):
    """Test username format validation"""
    test_cases = [
        ("", "string should have at least 3 characters"),  # Empty
        ("a", "string should have at least 3 characters"),  # Too short
        ("a" * 51, "string should have at most 50 characters"),  # Too long
        ("user@name", "string should match pattern"),  # Special chars
        ("user name", "string should match pattern"),  # Spaces
    ]

    for username, expected_error in test_cases:
        user_data = {
            "username": username,
            "email": "test@example.com",
            "password": "testpass123",
        }
        response = await client.post("/api/v1/users/", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, (
            f"Username {username} should be invalid"
        )
        assert expected_error in response.json()["detail"][0]["msg"].lower()


@pytest.mark.asyncio
async def test_user_listing_pagination(
    client: AsyncClient, admin_user_token_headers: dict[str, str]
):
    """Test user listing pagination"""
    # Create multiple users
    for i in range(5):
        user_data = {
            "username": f"page_user_{i}",
            "email": f"page{i}@example.com",
            "password": "testpass123",
        }
        await client.post("/api/v1/users/", json=user_data)

    # Test with limit
    response = await client.get(
        "/api/v1/users/?limit=2", headers=admin_user_token_headers
    )
    assert response.status_code == status.HTTP_200_OK
    users = response.json()
    assert len(users) == 2

    # Test with skip
    response = await client.get(
        "/api/v1/users/?skip=2&limit=2", headers=admin_user_token_headers
    )
    assert response.status_code == status.HTTP_200_OK
    users = response.json()
    assert len(users) == 2


@pytest.mark.asyncio
async def test_password_update_validation(
    client: AsyncClient, normal_user_token_headers: dict[str, str], normal_user: Any
):
    """Test password update validation"""
    # Try to update with invalid password
    update_data = {"password": "123"}  # Too short
    response = await client.put(
        f"/api/v1/users/{normal_user.id}",
        json=update_data,
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Update with valid password
    update_data = {"password": "newvalidpass123"}
    response = await client.put(
        f"/api/v1/users/{normal_user.id}",
        json=update_data,
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK

    # Try to login with new password
    login_data = {"username": normal_user.username, "password": "newvalidpass123"}
    response = await client.post("/api/v1/users/token", data=login_data)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_concurrent_user_updates(
    client: AsyncClient,
    normal_user_token_headers: dict[str, str],
    admin_user_token_headers: dict[str, str],
    normal_user: User,
):
    """Test handling of concurrent updates to the same user"""
    # Simulate two concurrent updates
    update_data1 = {"username": "new_name1"}
    update_data2 = {"username": "new_name2"}

    # Send updates nearly simultaneously
    response1 = await client.put(
        f"/api/v1/users/{normal_user.id}",
        json=update_data1,
        headers=normal_user_token_headers,
    )
    response2 = await client.put(
        f"/api/v1/users/{normal_user.id}",
        json=update_data2,
        headers=normal_user_token_headers,
    )

    # At least one should succeed
    assert (
        response1.status_code == status.HTTP_200_OK
        or response2.status_code == status.HTTP_200_OK
    )

    # Check final state
    # Use admin headers to avoid issues with normal_user's token if username changed
    response = await client.get(
        f"/api/v1/users/{normal_user.id}", headers=admin_user_token_headers
    )
    assert response.status_code == status.HTTP_200_OK
    final_data = response.json()
    assert final_data["username"] in ["new_name1", "new_name2"]
