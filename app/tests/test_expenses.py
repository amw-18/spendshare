import pytest
import pytest_asyncio # Added for async fixture
from httpx import AsyncClient
from fastapi import status
from typing import Dict, Any, AsyncGenerator
from src.models.models import User, Currency # Added Currency
from src.main import app # For TestClient, if not using AsyncClient directly for all
# from fastapi.testclient import TestClient # No longer needed for test_currency_sync


# Helper function to create a user (can be moved to conftest if used by many test files)
async def create_test_user(
    client: AsyncClient,
    username: str,
    email: str,
    password: str = "password123",  # Changed default password
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


@pytest_asyncio.fixture
async def test_currency_sync(client: AsyncClient, admin_user_token_headers: dict) -> Currency:
    """
    Creates a test currency ("TST") using admin privileges.
    Uses TestClient for synchronous execution suitable for a module-scoped fixture.
    """
    # Need a synchronous client for this fixture if it's module-scoped
    # and other async fixtures depend on event_loop.
    # Alternatively, make this an async fixture if that's simpler.
    # For now, let's use TestClient from main app.
    currency_data = {"code": "TST", "name": "Test Currency", "symbol": "T"}
    response = await client.post("/api/v1/currencies/", headers=admin_user_token_headers, json=currency_data)
    if response.status_code == 400 and "already exists" in response.json().get("detail", ""):
        # If currency already exists from a previous partial run, try to fetch it
        # This is a workaround for potential issues if tests are interrupted.
        # A better solution might be to ensure DB cleanup or use unique codes per test run.
        existing_currencies_resp = await client.get("/api/v1/currencies/?limit=100") # Assuming default limit is enough
        existing_currencies = existing_currencies_resp.json()
        found = next((c for c in existing_currencies if c["code"] == "TST"), None)
        if found:
            return Currency(**found) # Return as Currency model instance
        else:
            raise Exception("Failed to create or find TST currency and it's needed for tests.")

    assert response.status_code == status.HTTP_201_CREATED, f"Failed to create TST currency: {response.text}"
    return Currency(**response.json()) # Return as Currency model instance


@pytest.mark.asyncio
async def test_create_expense_with_currency_auth(
    client: AsyncClient, 
    normal_user_token_headers: dict[str, str], 
    test_currency_sync: Currency
):
    expense_data = {
        "description": "Lunch with Currency",
        "amount": 25.50,
        "currency_id": test_currency_sync.id,
        "group_id": None,
    }
    response = await client.post(
        "/api/v1/expenses/", json=expense_data, headers=normal_user_token_headers
    )
    assert response.status_code == status.HTTP_201_CREATED, f"Failed to create expense: {response.text}"
    data = response.json()
    assert data["description"] == expense_data["description"]
    assert data["amount"] == expense_data["amount"]
    assert data["id"] is not None
    assert "participant_details" in data
    assert data["currency"] is not None
    assert data["currency"]["id"] == test_currency_sync.id
    assert data["currency"]["code"] == test_currency_sync.code
    assert data["currency"]["name"] == test_currency_sync.name


@pytest.mark.asyncio
async def test_create_expense_invalid_currency_id(
    client: AsyncClient, normal_user_token_headers: dict[str, str]
):
    expense_data = {
        "description": "Expense with Invalid Currency",
        "amount": 10.0,
        "currency_id": 99999,  # Non-existent currency ID
    }
    response = await client.post(
        "/api/v1/expenses/", json=expense_data, headers=normal_user_token_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND # Because currency is fetched with get_object_or_404


# Fixtures normal_user, admin_user, normal_user_token_headers, admin_user_token_headers are from conftest.py
# test_create_expense_normal_user is effectively replaced by test_create_expense_with_currency_auth

# Read Expense (Detail View) Authorization Tests
@pytest.mark.asyncio
async def test_read_expense_authorization(
    client: AsyncClient,
    normal_user: User,
    admin_user: User,
    normal_user_token_headers: dict[str, str],
    admin_user_token_headers: dict[str, str],
    test_currency_sync: Currency, # Add currency fixture
):
    # Setup: Create other_user and third_user
    other_user_data = await create_test_user(
        client, "other_user_exp_read", "other_exp_read@example.com"
    )
    other_user_id = other_user_data["id"]

    third_user_data = await create_test_user(
        client, "third_user_exp_read", "third_exp_read@example.com"
    )
    # Login third_user to get their token
    third_user_login_data = {
        "username": "third_user_exp_read",
        "password": "password123",
    }
    res_third = await client.post("/api/v1/users/token", data=third_user_login_data)
    assert res_third.status_code == 200, "Failed to log in third_user"
    third_user_token = res_third.json()["access_token"]
    third_user_headers = {"Authorization": f"Bearer {third_user_token}"}

    # Login other_user to get their token
    other_user_login_data = {
        "username": "other_user_exp_read",
        "password": "password123",
    }
    res_other = await client.post("/api/v1/users/token", data=other_user_login_data)
    assert res_other.status_code == 200, "Failed to log in other_user"
    other_user_token = res_other.json()["access_token"]
    other_user_headers = {"Authorization": f"Bearer {other_user_token}"}

    # Setup: Create an expense by normal_user with other_user as a participant
    expense_payload = {
        "expense_in": {
            "description": "Shared Dinner",
            "amount": 120.0,
            "currency_id": test_currency_sync.id, # Add currency_id
            # paid_by_user_id is implicit from normal_user_token_headers
        },
        "participant_user_ids": [normal_user.id, other_user_id],
    }
    response_create_exp = await client.post(
        "/api/v1/expenses/service/",
        json=expense_payload,
        headers=normal_user_token_headers,
    )
    assert response_create_exp.status_code == status.HTTP_201_CREATED # Changed from 200 OK
    created_expense = response_create_exp.json()
    expense_id = created_expense["id"]

    # Test: Payer (normal_user) can view
    response_payer_view = await client.get(
        f"/api/v1/expenses/{expense_id}", headers=normal_user_token_headers
    )
    assert response_payer_view.status_code == status.HTTP_200_OK
    payer_view_data = response_payer_view.json()
    assert payer_view_data["description"] == expense_payload["expense_in"]["description"]
    assert payer_view_data["currency"] is not None
    assert payer_view_data["currency"]["id"] == test_currency_sync.id

    # Test: Admin (admin_user) can view
    response_admin_view = await client.get(
        f"/api/v1/expenses/{expense_id}", headers=admin_user_token_headers
    )
    assert response_admin_view.status_code == status.HTTP_200_OK
    admin_view_data = response_admin_view.json()
    assert admin_view_data["currency"] is not None
    assert admin_view_data["currency"]["id"] == test_currency_sync.id


    # Test: Participant (other_user) can view
    response_participant_view = await client.get(
        f"/api/v1/expenses/{expense_id}", headers=other_user_headers
    )
    assert response_participant_view.status_code == status.HTTP_200_OK
    participant_view_data = response_participant_view.json()
    assert participant_view_data["currency"] is not None
    assert participant_view_data["currency"]["id"] == test_currency_sync.id

    # Test: Non-participant/non-payer/non-admin (third_user) cannot view (403)
    response_third_user_view = await client.get(
        f"/api/v1/expenses/{expense_id}", headers=third_user_headers
    )
    assert response_third_user_view.status_code == status.HTTP_403_FORBIDDEN


# Delete Expense Authorization Tests
@pytest.mark.asyncio
async def test_delete_expense_authorization(
    client: AsyncClient,
    normal_user: User,
    admin_user: User,
    normal_user_token_headers: dict[str, str],
    admin_user_token_headers: dict[str, str],
    test_currency_sync: Currency, # Add currency fixture
):
    # Setup: Create other_user for testing non-payer/non-admin deletion
    other_user_data = await create_test_user(
        client, "other_user_exp_del", "other_exp_del@example.com"
    )
    other_user_login_data = {
        "username": "other_user_exp_del",
        "password": "password123",
    }
    res = await client.post("/api/v1/users/token", data=other_user_login_data)
    assert res.status_code == 200, "Failed to log in other_user"
    other_user_token = res.json()["access_token"]
    other_user_headers = {"Authorization": f"Bearer {other_user_token}"}

    # Test: Payer (normal_user) can delete
    expense_data_payer_del = {
        "description": "Expense For Payer Delete", 
        "amount": 10.0,
        "currency_id": test_currency_sync.id,
    }
    response_create_payer_del = await client.post(
        "/api/v1/expenses/",
        json=expense_data_payer_del,
        headers=normal_user_token_headers,
    )
    assert response_create_payer_del.status_code == status.HTTP_201_CREATED # Changed from 200 OK
    expense_id_payer_del = response_create_payer_del.json()["id"]

    response_payer_delete = await client.delete(
        f"/api/v1/expenses/{expense_id_payer_del}", headers=normal_user_token_headers
    )
    assert response_payer_delete.status_code == status.HTTP_200_OK
    # Verify deletion
    response_get_after_payer_delete = await client.get(
        f"/api/v1/expenses/{expense_id_payer_del}", headers=admin_user_token_headers
    )  # Admin can try to get
    assert response_get_after_payer_delete.status_code == status.HTTP_404_NOT_FOUND

    # Test: Admin (admin_user) can delete an expense paid by normal_user
    expense_data_admin_del = {
        "description": "Expense For Admin Delete", 
        "amount": 20.0,
        "currency_id": test_currency_sync.id,
    }
    response_create_admin_del = await client.post(
        "/api/v1/expenses/",
        json=expense_data_admin_del,
        headers=normal_user_token_headers,
    )  # normal_user creates
    assert response_create_admin_del.status_code == status.HTTP_201_CREATED # Changed from 200 OK
    expense_id_admin_del = response_create_admin_del.json()["id"]

    response_admin_delete = await client.delete(
        f"/api/v1/expenses/{expense_id_admin_del}", headers=admin_user_token_headers
    )  # admin deletes
    assert response_admin_delete.status_code == status.HTTP_200_OK
    # Verify deletion
    response_get_after_admin_delete = await client.get(
        f"/api/v1/expenses/{expense_id_admin_del}", headers=normal_user_token_headers
    )  # normal_user (payer) tries to get
    assert response_get_after_admin_delete.status_code == status.HTTP_404_NOT_FOUND

    # Test: Other user (non-payer/non-admin) cannot delete
    expense_data_other_del = {
        "description": "Expense For Other User Delete",
        "amount": 30.0,
        "currency_id": test_currency_sync.id,
    }
    response_create_other_del = await client.post(
        "/api/v1/expenses/",
        json=expense_data_other_del,
        headers=normal_user_token_headers,
    )  # normal_user creates
    assert response_create_other_del.status_code == status.HTTP_201_CREATED # Changed from 200 OK
    expense_id_other_del = response_create_other_del.json()["id"]

    response_other_delete = await client.delete(
        f"/api/v1/expenses/{expense_id_other_del}", headers=other_user_headers
    )  # other_user tries to delete
    assert response_other_delete.status_code == status.HTTP_403_FORBIDDEN
    # Verify expense still exists
    response_get_after_other_delete_fail = await client.get(
        f"/api/v1/expenses/{expense_id_other_del}", headers=normal_user_token_headers
    )
    assert response_get_after_other_delete_fail.status_code == status.HTTP_200_OK


# Delete or update obsolete tests like test_create_simple_expense_success, etc.
# The new tests cover creation with auth, and specific auth tests for read/delete.
# Service expense creation tests (test_create_service_expense_success_individual, etc.) should be updated for auth.
@pytest.mark.asyncio
async def test_create_service_expense_success_auth(
    client: AsyncClient, 
    normal_user_token_headers: dict[str, str], 
    normal_user: User,
    test_currency_sync: Currency, # Add currency fixture
):
    participant1_data = await create_test_user(
        client, "srv_part1_auth", "srv_part1_auth@example.com"
    )
    participant1_id = participant1_data["id"]

    service_expense_payload = {
        "expense_in": {
            "description": "Dinner via Service Auth",
            "amount": 100.0,
            "currency_id": test_currency_sync.id, # Add currency_id
            # paid_by_user_id implicit from normal_user_token_headers
        },
        "participant_user_ids": [normal_user.id, participant1_id],
    }
    response = await client.post(
        "/api/v1/expenses/service/",
        json=service_expense_payload,
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED, f"Failed to create service expense: {response.text}"
    data = response.json()
    assert data["description"] == service_expense_payload["expense_in"]["description"]
    assert data["id"] is not None
    assert len(data["participant_details"]) == len(
        service_expense_payload["participant_user_ids"]
    )
    assert data["currency"] is not None
    assert data["currency"]["id"] == test_currency_sync.id


# Listing expenses (GET /api/v1/expenses/) is also protected by get_current_user but has no further role/ownership checks by default.
# Adding a simple test for authenticated access.
@pytest.mark.asyncio
async def test_read_multiple_expenses_auth(
    client: AsyncClient, 
    normal_user_token_headers: dict[str, str],
    test_currency_sync: Currency, # To create an expense to list
):
    # Create at least one expense to ensure the list is not empty
    expense_data = {
        "description": "Expense for Listing",
        "amount": 10.0,
        "currency_id": test_currency_sync.id,
    }
    await client.post("/api/v1/expenses/", json=expense_data, headers=normal_user_token_headers)
    
    response = await client.get("/api/v1/expenses/", headers=normal_user_token_headers)
    assert response.status_code == status.HTTP_200_OK
    expenses = response.json()
    assert isinstance(expenses, list)
    if len(expenses) > 0:
        # Check currency details in the first expense found for this user
        # This check is basic; more detailed checks are in specific read tests
        first_expense = next((exp for exp in expenses if exp["currency"] is not None), None)
        if first_expense: # Check if any expense has currency details
             assert first_expense["currency"]["id"] == test_currency_sync.id


# Updating expenses (PUT /api/v1/expenses/{expense_id}) is protected by get_current_user.
@pytest.mark.asyncio
async def test_update_expense_success_auth(
    client: AsyncClient, 
    normal_user_token_headers: dict[str, str], 
    normal_user: User,
    test_currency_sync: Currency, # Original currency
    admin_user_token_headers: dict # To create a second currency for update
):
    # Create another currency for updating to
    new_currency_data = {"code": "UCU", "name": "Update Test Currency", "symbol": "U"}
    res_new_curr = await client.post("/api/v1/currencies/", headers=admin_user_token_headers, json=new_currency_data)
    # Handle if UCU already exists (e.g. from a previous failed run)
    if res_new_curr.status_code == 400 and "already exists" in res_new_curr.json().get("detail", ""):
        existing_currencies_resp = await client.get("/api/v1/currencies/?limit=100")
        existing_currencies = existing_currencies_resp.json()
        found_ucu = next((c for c in existing_currencies if c["code"] == "UCU"), None)
        if found_ucu:
            new_currency_id = found_ucu["id"]
        else:
            raise Exception("Failed to create or find UCU currency for update test.")
    else:
        assert res_new_curr.status_code == status.HTTP_201_CREATED, f"Failed to create UCU currency: {res_new_curr.text}"
        new_currency_id = res_new_curr.json()["id"]


    expense_data = {
        "description": "Initial Desc Auth", 
        "amount": 50.0,
        "currency_id": test_currency_sync.id
    }
    create_resp = await client.post(
        "/api/v1/expenses/", json=expense_data, headers=normal_user_token_headers
    )
    assert create_resp.status_code == status.HTTP_201_CREATED # Changed from 200 OK
    expense_id = create_resp.json()["id"]

    update_payload = {
        "description": "Updated Desc Auth", 
        "amount": 75.0,
        "currency_id": new_currency_id # Update to new currency
    }
    response = await client.put(
        f"/api/v1/expenses/{expense_id}",
        json=update_payload,
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK, f"Failed to update expense: {response.text}"
    data = response.json()
    assert data["description"] == "Updated Desc Auth"
    assert data["amount"] == 75.0
    assert data["id"] == expense_id
    assert "participant_details" in data
    assert data["currency"] is not None
    assert data["currency"]["id"] == new_currency_id
    assert data["currency"]["code"] == "UCU"


@pytest.mark.asyncio
async def test_update_expense_invalid_currency_id(
    client: AsyncClient, 
    normal_user_token_headers: dict[str, str], 
    test_currency_sync: Currency
):
    expense_data = {
        "description": "Expense for Currency Update Test", 
        "amount": 60.0,
        "currency_id": test_currency_sync.id
    }
    create_resp = await client.post(
        "/api/v1/expenses/", json=expense_data, headers=normal_user_token_headers
    )
    assert create_resp.status_code == status.HTTP_201_CREATED # Changed from 200 OK
    expense_id = create_resp.json()["id"]

    update_payload = {"currency_id": 88888} # Invalid currency ID
    response = await client.put(
        f"/api/v1/expenses/{expense_id}",
        json=update_payload,
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND # Currency check is get_object_or_404
