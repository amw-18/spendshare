import pytest
from httpx import AsyncClient
from fastapi import status
from typing import List, Dict, Any, Optional  # For type hints


# Helper function to create a user (can be moved to conftest if used by many test files)
async def create_test_user(
    client: AsyncClient, username: str, email: str, password: str = "password123" # Changed default password
) -> Dict[str, Any]:
    user_data = {"username": username, "email": email, "password": password}
    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == status.HTTP_200_OK
    return response.json()


# Helper function to create a group
async def create_test_group(
    client: AsyncClient, name: str, creator_id: int
) -> Dict[str, Any]:
    group_data = {"name": name, "created_by_user_id": creator_id}
    response = await client.post("/api/v1/groups/", json=group_data)
    assert response.status_code == status.HTTP_200_OK
    return response.json()


@pytest.mark.asyncio
async def test_create_simple_expense_success(client: AsyncClient):
    payer_data = await create_test_user(client, "exp_payer1", "exp_payer1@example.com")
    # Login payer to get token
    payer_login_data = {"username": payer_data["username"], "password": "password123"}
    login_res = await client.post("/api/v1/users/token", data=payer_login_data)
    assert login_res.status_code == status.HTTP_200_OK, f"Failed to log in payer: {login_res.text}"
    payer_token = login_res.json()["access_token"]
    payer_headers = {"Authorization": f"Bearer {payer_token}"}

    expense_data = {
        "description": "Lunch",
        "amount": 25.50,
        # "paid_by_user_id": payer_data["id"], # Removed: will be set from current_user via token
        "group_id": None, # Explicitly setting, though optional
    }
    response = await client.post("/api/v1/expenses/", json=expense_data, headers=payer_headers) # Added headers
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["description"] == expense_data["description"]
    assert data["amount"] == expense_data["amount"]
    # assert data["paid_by_user_id"] == payer_data["id"] # Removed: not in ExpenseRead
    assert data["id"] is not None
    assert "participant_details" in data # Check for participant_details as it's in ExpenseRead

# Fixtures normal_user, admin_user, normal_user_token_headers, admin_user_token_headers are from conftest.py
# User model for type hinting if needed
from app.models.models import User


@pytest.mark.asyncio
async def test_create_expense_normal_user(client: AsyncClient, normal_user_token_headers: dict[str, str], normal_user: User):
    expense_data = {
        "description": "Groceries", 
        "amount": 55.75,
        "paid_by_user_id": normal_user.id # Explicitly set paid_by_user_id
    } 
    response = await client.post("/api/v1/expenses/", json=expense_data, headers=normal_user_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["description"] == expense_data["description"]
    assert data["amount"] == expense_data["amount"]
    # assert data["paid_by_user_id"] == normal_user.id # Removed: not in ExpenseRead
    assert data["id"] is not None


# Read Expense (Detail View) Authorization Tests
@pytest.mark.asyncio
async def test_read_expense_authorization(
    client: AsyncClient,
    normal_user: User,
    admin_user: User,
    normal_user_token_headers: dict[str, str],
    admin_user_token_headers: dict[str, str],
):
    # Setup: Create other_user and third_user
    other_user_data = await create_test_user(client, "other_user_exp_read", "other_exp_read@example.com")
    other_user_id = other_user_data["id"]
    
    third_user_data = await create_test_user(client, "third_user_exp_read", "third_exp_read@example.com")
    # Login third_user to get their token
    third_user_login_data = {"username": "third_user_exp_read", "password": "password123"}
    res_third = await client.post("/api/v1/users/token", data=third_user_login_data)
    assert res_third.status_code == 200, "Failed to log in third_user"
    third_user_token = res_third.json()["access_token"]
    third_user_headers = {"Authorization": f"Bearer {third_user_token}"}

    # Login other_user to get their token
    other_user_login_data = {"username": "other_user_exp_read", "password": "password123"}
    res_other = await client.post("/api/v1/users/token", data=other_user_login_data)
    assert res_other.status_code == 200, "Failed to log in other_user"
    other_user_token = res_other.json()["access_token"]
    other_user_headers = {"Authorization": f"Bearer {other_user_token}"}

    # Setup: Create an expense by normal_user with other_user as a participant
    expense_payload = {
        "expense_in": {
            "description": "Shared Dinner",
            "amount": 120.0,
            # paid_by_user_id is implicit from normal_user_token_headers
        },
        "participant_user_ids": [normal_user.id, other_user_id],
    }
    response_create_exp = await client.post("/api/v1/expenses/service/", json=expense_payload, headers=normal_user_token_headers)
    assert response_create_exp.status_code == status.HTTP_200_OK
    created_expense = response_create_exp.json()
    expense_id = created_expense["id"]

    # Test: Payer (normal_user) can view
    response_payer_view = await client.get(f"/api/v1/expenses/{expense_id}", headers=normal_user_token_headers)
    assert response_payer_view.status_code == status.HTTP_200_OK
    assert response_payer_view.json()["description"] == expense_payload["expense_in"]["description"]

    # Test: Admin (admin_user) can view
    response_admin_view = await client.get(f"/api/v1/expenses/{expense_id}", headers=admin_user_token_headers)
    assert response_admin_view.status_code == status.HTTP_200_OK

    # Test: Participant (other_user) can view
    response_participant_view = await client.get(f"/api/v1/expenses/{expense_id}", headers=other_user_headers)
    assert response_participant_view.status_code == status.HTTP_200_OK

    # Test: Non-participant/non-payer/non-admin (third_user) cannot view (403)
    response_third_user_view = await client.get(f"/api/v1/expenses/{expense_id}", headers=third_user_headers)
    assert response_third_user_view.status_code == status.HTTP_403_FORBIDDEN


# Delete Expense Authorization Tests
@pytest.mark.asyncio
async def test_delete_expense_authorization(
    client: AsyncClient,
    normal_user: User,
    admin_user: User,
    normal_user_token_headers: dict[str, str],
    admin_user_token_headers: dict[str, str],
):
    # Setup: Create other_user for testing non-payer/non-admin deletion
    other_user_data = await create_test_user(client, "other_user_exp_del", "other_exp_del@example.com")
    other_user_login_data = {"username": "other_user_exp_del", "password": "password123"}
    res = await client.post("/api/v1/users/token", data=other_user_login_data)
    assert res.status_code == 200, "Failed to log in other_user"
    other_user_token = res.json()["access_token"]
    other_user_headers = {"Authorization": f"Bearer {other_user_token}"}

    # Test: Payer (normal_user) can delete
    expense_data_payer_del = {"description": "Expense For Payer Delete", "amount": 10.0}
    response_create_payer_del = await client.post("/api/v1/expenses/", json=expense_data_payer_del, headers=normal_user_token_headers)
    assert response_create_payer_del.status_code == status.HTTP_200_OK
    expense_id_payer_del = response_create_payer_del.json()["id"]
    
    response_payer_delete = await client.delete(f"/api/v1/expenses/{expense_id_payer_del}", headers=normal_user_token_headers)
    assert response_payer_delete.status_code == status.HTTP_200_OK
    # Verify deletion
    response_get_after_payer_delete = await client.get(f"/api/v1/expenses/{expense_id_payer_del}", headers=admin_user_token_headers) # Admin can try to get
    assert response_get_after_payer_delete.status_code == status.HTTP_404_NOT_FOUND

    # Test: Admin (admin_user) can delete an expense paid by normal_user
    expense_data_admin_del = {"description": "Expense For Admin Delete", "amount": 20.0}
    response_create_admin_del = await client.post("/api/v1/expenses/", json=expense_data_admin_del, headers=normal_user_token_headers) # normal_user creates
    assert response_create_admin_del.status_code == status.HTTP_200_OK
    expense_id_admin_del = response_create_admin_del.json()["id"]

    response_admin_delete = await client.delete(f"/api/v1/expenses/{expense_id_admin_del}", headers=admin_user_token_headers) # admin deletes
    assert response_admin_delete.status_code == status.HTTP_200_OK
    # Verify deletion
    response_get_after_admin_delete = await client.get(f"/api/v1/expenses/{expense_id_admin_del}", headers=normal_user_token_headers) # normal_user (payer) tries to get
    assert response_get_after_admin_delete.status_code == status.HTTP_404_NOT_FOUND

    # Test: Other user (non-payer/non-admin) cannot delete
    expense_data_other_del = {"description": "Expense For Other User Delete", "amount": 30.0}
    response_create_other_del = await client.post("/api/v1/expenses/", json=expense_data_other_del, headers=normal_user_token_headers) # normal_user creates
    assert response_create_other_del.status_code == status.HTTP_200_OK
    expense_id_other_del = response_create_other_del.json()["id"]

    response_other_delete = await client.delete(f"/api/v1/expenses/{expense_id_other_del}", headers=other_user_headers) # other_user tries to delete
    assert response_other_delete.status_code == status.HTTP_403_FORBIDDEN
    # Verify expense still exists
    response_get_after_other_delete_fail = await client.get(f"/api/v1/expenses/{expense_id_other_del}", headers=normal_user_token_headers)
    assert response_get_after_other_delete_fail.status_code == status.HTTP_200_OK


# Delete or update obsolete tests like test_create_simple_expense_success, etc.
# The new tests cover creation with auth, and specific auth tests for read/delete.
# Service expense creation tests (test_create_service_expense_success_individual, etc.) should be updated for auth.
@pytest.mark.asyncio
async def test_create_service_expense_success_auth(client: AsyncClient, normal_user_token_headers: dict[str, str], normal_user: User):
    participant1_data = await create_test_user(client, "srv_part1_auth", "srv_part1_auth@example.com")
    participant1_id = participant1_data["id"]

    service_expense_payload = {
        "expense_in": {
            "description": "Dinner via Service Auth",
            "amount": 100.0,
            # paid_by_user_id implicit from normal_user_token_headers
        },
        "participant_user_ids": [normal_user.id, participant1_id],
    }
    response = await client.post(
        "/api/v1/expenses/service/", json=service_expense_payload, headers=normal_user_token_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["description"] == service_expense_payload["expense_in"]["description"]
    # assert data["paid_by_user_id"] == normal_user.id # Removed: not in ExpenseRead
    assert data["id"] is not None
    assert len(data["participant_details"]) == len(service_expense_payload["participant_user_ids"])

# Listing expenses (GET /api/v1/expenses/) is also protected by get_current_user but has no further role/ownership checks by default.
# Adding a simple test for authenticated access.
@pytest.mark.asyncio
async def test_read_multiple_expenses_auth(client: AsyncClient, normal_user_token_headers: dict[str, str]):
    response = await client.get("/api/v1/expenses/", headers=normal_user_token_headers)
    assert response.status_code == status.HTTP_200_OK
    # Further assertions if needed

# Updating expenses (PUT /api/v1/expenses/{expense_id}) is protected by get_current_user.
# The current implementation does NOT check for ownership or admin status for updates.
# Any authenticated user can update any expense. This is a potential security flaw.
# This test will use normal_user (payer) to update.
@pytest.mark.asyncio
async def test_update_expense_success_auth(client: AsyncClient, normal_user_token_headers: dict[str, str], normal_user: User):
    expense_data = {"description": "Initial Desc Auth", "amount": 50.0}
    create_resp = await client.post("/api/v1/expenses/", json=expense_data, headers=normal_user_token_headers)
    assert create_resp.status_code == status.HTTP_200_OK
    expense_id = create_resp.json()["id"]

    update_payload = {"description": "Updated Desc Auth", "amount": 75.0}
    response = await client.put(f"/api/v1/expenses/{expense_id}", json=update_payload, headers=normal_user_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["description"] == "Updated Desc Auth"
    assert data["amount"] == 75.0
    # assert data["paid_by_user_id"] == normal_user.id # Removed: not in ExpenseRead
    assert data["id"] == expense_id
    assert "participant_details" in data
