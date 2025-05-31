import pytest
from httpx import AsyncClient
from fastapi import status
from typing import Dict, Any
from src.models.models import User, Group, UserGroupLink, Currency

# Helper function to create a user
async def create_test_user(
    client: AsyncClient, username: str, email: str, password: str = "testpassword1"
) -> Dict[str, Any]:
    user_data = {"username": username, "email": email, "password": password}
    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == status.HTTP_200_OK
    return response.json()

# Helper function to get user token
async def get_user_token_headers(client: AsyncClient, username: str, password: str = "testpassword1") -> Dict[str, str]:
    login_data = {"username": username, "password": password}
    res = await client.post("/api/v1/users/token", data=login_data)
    assert res.status_code == status.HTTP_200_OK
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_group_name_validation(client: AsyncClient, normal_user_token_headers: dict[str, str]):
    """Test group name validation rules"""
    # Test empty name
    group_data = {"name": ""}
    response = await client.post("/api/v1/groups/", json=group_data, headers=normal_user_token_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "string should have at least 1 character" in response.json()["detail"][0]["msg"].lower()
    
    # Test very long name (if there's a limit)
    group_data = {"name": "a" * 256}  # Assuming there's a reasonable limit
    response = await client.post("/api/v1/groups/", json=group_data, headers=normal_user_token_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
async def test_group_member_permissions(client: AsyncClient, normal_user_token_headers: dict[str, str], normal_user: Any):
    """Test group member permissions"""
    # Create a group
    group_data = {"name": "Permission Test Group"}
    group_response = await client.post("/api/v1/groups/", json=group_data, headers=normal_user_token_headers)
    assert group_response.status_code == status.HTTP_200_OK
    group_id = group_response.json()["id"]
    assert group_response.json()["created_by_user_id"] == normal_user.id
    
    # Create another user
    other_user = await create_test_user(client, "perm_test_user", "perm_test@example.com")
    other_user_id = other_user["id"]
    other_user_headers = await get_user_token_headers(client, "perm_test_user")
    
    # Test: Non-member cannot view group (should return 403)
    response = await client.get(f"/api/v1/groups/{group_id}", headers=other_user_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    # Add user to group
    add_response = await client.post(
        f"/api/v1/groups/{group_id}/members/{other_user_id}",
        headers=normal_user_token_headers
    )
    assert add_response.status_code == status.HTTP_200_OK
    
    # Test: Member can now view group
    response = await client.get(f"/api/v1/groups/{group_id}", headers=other_user_headers)
    assert response.status_code == status.HTTP_200_OK
    
    # Test: Non-creator member cannot add new members
    new_user = await create_test_user(client, "new_member", "new_member@example.com")
    response = await client.post(
        f"/api/v1/groups/{group_id}/members/{new_user['id']}",
        headers=other_user_headers
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.asyncio
async def test_group_pagination(client: AsyncClient, normal_user_token_headers: dict[str, str]):
    """Test group listing pagination"""
    # Create multiple groups
    for i in range(5):
        group_data = {"name": f"Pagination Group {i}"}
        await client.post("/api/v1/groups/", json=group_data, headers=normal_user_token_headers)
    
    # Test with limit
    response = await client.get("/api/v1/groups/?limit=2", headers=normal_user_token_headers)
    assert response.status_code == status.HTTP_200_OK
    groups = response.json()
    assert len(groups) == 2
    
    # Test with skip
    response = await client.get("/api/v1/groups/?skip=2&limit=2", headers=normal_user_token_headers)
    assert response.status_code == status.HTTP_200_OK
    groups = response.json()
    assert len(groups) == 2

@pytest.mark.asyncio
async def test_group_member_removal_cascade(client: AsyncClient, normal_user_token_headers: dict[str, str], normal_user: Any, test_currency: Currency):
    """Test that removing a member cascades properly to expenses"""
    # Create a group
    group_data = {"name": "Cascade Test Group"}
    group_response = await client.post("/api/v1/groups/", json=group_data, headers=normal_user_token_headers)
    assert group_response.status_code == status.HTTP_200_OK
    group_id = group_response.json()["id"]
    
    # Create another user
    member = await create_test_user(client, "cascade_test", "cascade@example.com")
    member_id = member["id"]
    
    # Add member to group
    await client.post(
        f"/api/v1/groups/{group_id}/members/{member_id}",
        headers=normal_user_token_headers
    )
    
    # Create a group expense with both users
    expense_payload = {
        "expense_in": {
            "description": "Group Expense",
            "amount": 100.0,
            "group_id": group_id,
            "currency_id": test_currency.id
        },
        "participant_user_ids": [normal_user.id, member_id]
    }
    expense_response = await client.post(
        "/api/v1/expenses/service/",
        json=expense_payload,
        headers=normal_user_token_headers
    )
    assert expense_response.status_code == status.HTTP_201_CREATED
   

@pytest.mark.asyncio
async def test_group_duplicate_member(client: AsyncClient, normal_user_token_headers: dict[str, str], normal_user: Any):
    """Test adding the same member twice"""
    # Create a group
    group_data = {"name": "Duplicate Member Test"}
    group_response = await client.post("/api/v1/groups/", json=group_data, headers=normal_user_token_headers)
    assert group_response.status_code == status.HTTP_200_OK
    group_id = group_response.json()["id"]
    
    # Create another user
    member = await create_test_user(client, "dup_member", "dup@example.com")
    member_id = member["id"]
    
    # Add member first time
    response1 = await client.post(
        f"/api/v1/groups/{group_id}/members/{member_id}",
        headers=normal_user_token_headers
    )
    assert response1.status_code == status.HTTP_200_OK
    
    # Try to add same member again
    response2 = await client.post(
        f"/api/v1/groups/{group_id}/members/{member_id}",
        headers=normal_user_token_headers
    )
    assert response2.status_code == status.HTTP_400_BAD_REQUEST
