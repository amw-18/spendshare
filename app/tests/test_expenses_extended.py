import pytest
from httpx import AsyncClient
from fastapi import status
from typing import Dict, Any
from src.models.models import Currency

# Helper function to create a user
async def create_test_user(
    client: AsyncClient, username: str, email: str, password: str = "testpassword1"
) -> Dict[str, Any]:
    user_data = {"username": username, "email": email, "password": password}
    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == status.HTTP_200_OK
    return response.json()


# Helper function to get user token
async def get_user_token_headers(
    client: AsyncClient, username: str, password: str = "testpassword1"
) -> Dict[str, str]:
    login_data = {"username": username, "password": password}
    res = await client.post("/api/v1/users/token", data=login_data)
    assert res.status_code == status.HTTP_200_OK
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_expense_negative_amount(
    client: AsyncClient, normal_user_token_headers: dict[str, str]
):
    """Test that expense creation fails with negative amount"""
    expense_data = {
        "description": "Negative Expense",
        "amount": -50.0,
        "group_id": None,
    }
    response = await client.post(
        "/api/v1/expenses/", json=expense_data, headers=normal_user_token_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert (
        "input should be greater than 0" in response.json()["detail"][0]["msg"].lower()
    )


@pytest.mark.asyncio
async def test_create_expense_zero_amount(
    client: AsyncClient, normal_user_token_headers: dict[str, str]
):
    """Test that expense creation fails with zero amount"""
    expense_data = {"description": "Zero Expense", "amount": 0.0}
    response = await client.post(
        "/api/v1/expenses/", json=expense_data, headers=normal_user_token_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert (
        "input should be greater than 0" in response.json()["detail"][0]["msg"].lower()
    )


@pytest.mark.asyncio
async def test_create_expense_empty_description(
    client: AsyncClient, normal_user_token_headers: dict[str, str]
):
    """Test that expense creation fails with empty description"""
    expense_data = {"description": "", "amount": 50.0}
    response = await client.post(
        "/api/v1/expenses/", json=expense_data, headers=normal_user_token_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_expense_filter_by_user(
    client: AsyncClient, 
    normal_user_token_headers: dict[str, str], 
    normal_user: Any,
    test_currency: Currency  
):
    """Test filtering expenses by user_id"""
    # Create a few expenses
    expense_data1 = {
        "description": "Filter Test 1", 
        "amount": 100.0, 
        "currency_id": test_currency.id  
    }
    expense_data2 = {
        "description": "Filter Test 2", 
        "amount": 200.0, 
        "currency_id": test_currency.id  
    }
    
    # Check response of creation, useful for debugging
    response1 = await client.post(
        "/api/v1/expenses/", json=expense_data1, headers=normal_user_token_headers
    )
    assert response1.status_code == status.HTTP_201_CREATED

    response2 = await client.post(
        "/api/v1/expenses/", json=expense_data2, headers=normal_user_token_headers
    )
    assert response2.status_code == status.HTTP_201_CREATED

    # Filter by user_id
    response = await client.get(
        f"/api/v1/expenses/?user_id={normal_user.id}", headers=normal_user_token_headers
    )
    assert response.status_code == status.HTTP_200_OK
    expenses = response.json()
    assert len(expenses) >= 2  # At least our 2 new expenses
    assert all(expense["paid_by_user_id"] == normal_user.id for expense in expenses)


@pytest.mark.asyncio
async def test_expense_filter_by_group(
    client: AsyncClient, 
    normal_user_token_headers: dict[str, str], 
    normal_user: Any,
    test_currency: Currency  
):
    """Test filtering expenses by group_id"""
    # Create a group first
    group_data = {"name": "Expense Filter Group"}
    group_response = await client.post(
        "/api/v1/groups/", json=group_data, headers=normal_user_token_headers
    )
    assert group_response.status_code == status.HTTP_200_OK
    group_id = group_response.json()["id"]

    # Create expenses in the group
    expense_data = {
        "description": "Group Expense",
        "amount": 150.0,
        "group_id": group_id,
        "currency_id": test_currency.id  
    }
    expense_creation_response = await client.post(
        "/api/v1/expenses/", json=expense_data, headers=normal_user_token_headers
    )
    assert expense_creation_response.status_code == status.HTTP_201_CREATED

    # Filter by group_id
    response = await client.get(
        f"/api/v1/expenses/?group_id={group_id}", headers=normal_user_token_headers
    )
    assert response.status_code == status.HTTP_200_OK
    expenses = response.json()
    assert len(expenses) >= 1
    assert all(expense["group_id"] == group_id for expense in expenses)


@pytest.mark.asyncio
async def test_expense_pagination(
    client: AsyncClient, 
    normal_user_token_headers: dict[str, str],
    test_currency: Currency  
):
    """Test expense listing pagination"""
    # Create multiple expenses
    for i in range(5):
        expense_data = {
            "description": f"Pagination Test {i}", 
            "amount": 50.0 + i,
            "currency_id": test_currency.id  
        }
        response_create = await client.post(
            "/api/v1/expenses/", json=expense_data, headers=normal_user_token_headers
        )
        assert response_create.status_code == status.HTTP_201_CREATED

    # Test with limit
    response = await client.get(
        "/api/v1/expenses/?limit=2", headers=normal_user_token_headers
    )
    assert response.status_code == status.HTTP_200_OK
    expenses = response.json()
    assert len(expenses) == 2

    # Test with skip
    response = await client.get(
        "/api/v1/expenses/?skip=2&limit=2", headers=normal_user_token_headers
    )
    assert response.status_code == status.HTTP_200_OK
    expenses = response.json()
    assert len(expenses) == 2


@pytest.mark.asyncio
async def test_expense_share_calculation(
    client: AsyncClient, 
    normal_user_token_headers: dict[str, str], 
    normal_user: Any,
    test_currency: Currency  
):
    """Test expense share calculation for multiple participants"""
    # Create another user as participant
    participant = await create_test_user(
        client, "share_participant", "share_part@example.com"
    )
    participant_id = participant["id"]

    # Create expense with participants
    expense_payload = {
        "expense_in": {
            "description": "Shared Expense",
            "amount": 100.0,
            "currency_id": test_currency.id  
        },
        "participant_user_ids": [normal_user.id, participant_id],
    }

    response = await client.post(
        "/api/v1/expenses/service/",
        json=expense_payload,
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED # Corrected assertion
    data = response.json()

    # Verify share calculations
    assert len(data["participant_details"]) == 2
    for participant_detail in data["participant_details"]: # Renamed for clarity
        assert participant_detail["share_amount"] == 50.0  # Equal split expected


@pytest.mark.asyncio
async def test_expense_update_validation(
    client: AsyncClient, 
    normal_user_token_headers: dict[str, str], 
    normal_user: Any,
    test_currency: Currency  
):
    """Test validation during expense updates"""
    # Create an initial expense
    initial_description = "Update Test"
    initial_amount = 100.0
    expense_data = {
        "description": initial_description,
        "amount": initial_amount,
        "currency_id": test_currency.id,  
        "paid_by_user_id": normal_user.id,  # Ensure paid_by_user_id is part of creation
    }
    create_response = await client.post(
        "/api/v1/expenses/", json=expense_data, headers=normal_user_token_headers
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    expense_id = create_response.json()["id"]

    # Test update with negative amount
    update_data_neg_amount = {
        "description": initial_description,
        "amount": -50.0,
        "currency_id": test_currency.id,  
        "paid_by_user_id": normal_user.id,
    }
    response_neg_amount = await client.put(
        f"/api/v1/expenses/{expense_id}",
        json=update_data_neg_amount,
        headers=normal_user_token_headers,
    )
    assert response_neg_amount.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Check that the error message is about the amount value, not missing fields
    assert any(
        err["type"] == "greater_than" and err["loc"] == ["body", "amount"]
        for err in response_neg_amount.json()["detail"]
    )

    # Test update with empty description
    update_data_empty_desc = {
        "description": "",
        "amount": initial_amount,
        "paid_by_user_id": normal_user.id,
    }
    response_empty_desc = await client.put(
        f"/api/v1/expenses/{expense_id}",
        json=update_data_empty_desc,
        headers=normal_user_token_headers,
    )
    assert response_empty_desc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Check that the error message is about the description length
    assert any(
        err["type"] == "string_too_short" and err["loc"] == ["body", "description"]
        for err in response_empty_desc.json()["detail"]
    )
