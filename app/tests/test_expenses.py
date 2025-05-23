import pytest
from httpx import AsyncClient
from fastapi import status
from typing import List, Dict, Any, Optional # For type hints

# Helper function to create a user (can be moved to conftest if used by many test files)
async def create_test_user(client: AsyncClient, username: str, email: str, password: str = "testpassword") -> Dict[str, Any]:
    user_data = {"username": username, "email": email, "password": password}
    response = await client.post("/users/", json=user_data)
    assert response.status_code == status.HTTP_200_OK
    return response.json()

# Helper function to create a group
async def create_test_group(client: AsyncClient, name: str, creator_id: int) -> Dict[str, Any]:
    group_data = {"name": name, "created_by_user_id": creator_id}
    response = await client.post("/groups/", json=group_data)
    assert response.status_code == status.HTTP_200_OK
    return response.json()

@pytest.mark.asyncio
async def test_create_simple_expense_success(client: AsyncClient):
    payer = await create_test_user(client, "exp_payer1", "exp_payer1@example.com")
    expense_data = {
        "description": "Lunch",
        "amount": 25.50,
        "paid_by_user_id": payer["id"],
        "group_id": None 
    }
    response = await client.post("/expenses/", json=expense_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["description"] == expense_data["description"]
    assert data["amount"] == expense_data["amount"]
    assert data["paid_by_user_id"] == payer["id"]
    assert "id" in data

@pytest.mark.asyncio
async def test_create_simple_expense_payer_not_found(client: AsyncClient):
    expense_data = {"description": "Ghost Expense", "amount": 10.0, "paid_by_user_id": 9998}
    response = await client.post("/expenses/", json=expense_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "payer user with id 9998 not found" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_create_simple_expense_group_not_found(client: AsyncClient):
    payer = await create_test_user(client, "exp_payer_group_nf", "exp_payer_group_nf@example.com")
    expense_data = {
        "description": "Group NF Expense", 
        "amount": 15.0, 
        "paid_by_user_id": payer["id"],
        "group_id": 8888 # Non-existent group
    }
    response = await client.post("/expenses/", json=expense_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "group with id 8888 not found" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_create_service_expense_success_individual(client: AsyncClient):
    payer = await create_test_user(client, "srv_payer1", "srv_payer1@example.com")
    participant1 = await create_test_user(client, "srv_part1", "srv_part1@example.com")
    
    service_expense_payload = {
        "expense_in": {"description": "Dinner via Service", "amount": 100.0},
        "paid_by_user_id": payer["id"],
        "participant_user_ids": [payer["id"], participant1["id"]],
        "group_id": None
    }
    response = await client.post("/expenses/service/", json=service_expense_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["description"] == service_expense_payload["expense_in"]["description"]
    assert data["amount"] == service_expense_payload["expense_in"]["amount"]
    assert data["paid_by_user_id"] == payer["id"]
    
    # Further checks could involve fetching the expense and its participants if an endpoint for that exists
    # or checking the ExpenseParticipant table directly in the test DB if necessary.

@pytest.mark.asyncio
async def test_create_service_expense_with_group(client: AsyncClient):
    payer = await create_test_user(client, "srv_payer_grp", "srv_payer_grp@example.com")
    participant1 = await create_test_user(client, "srv_part_grp", "srv_part_grp@example.com")
    group = await create_test_group(client, "Service Test Group", payer["id"])
    # Assume payer and participant1 are members of the group (not enforced by this test yet)

    service_expense_payload = {
        "expense_in": {"description": "Group Dinner via Service", "amount": 150.0},
        "paid_by_user_id": payer["id"],
        "participant_user_ids": [payer["id"], participant1["id"]],
        "group_id": group["id"]
    }
    response = await client.post("/expenses/service/", json=service_expense_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["group_id"] == group["id"]

@pytest.mark.asyncio
async def test_create_service_expense_participant_not_found(client: AsyncClient):
    payer = await create_test_user(client, "srv_payer_part_nf", "srv_payer_part_nf@example.com")
    service_expense_payload = {
        "expense_in": {"description": "Missing Friend Dinner", "amount": 50.0},
        "paid_by_user_id": payer["id"],
        "participant_user_ids": [payer["id"], 99977], # Non-existent participant
        "group_id": None
    }
    response = await client.post("/expenses/service/", json=service_expense_payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST # Or 404 if service returns that for missing users
    assert "failed to create expense" in response.json()["detail"].lower() # Based on router

@pytest.mark.asyncio
async def test_read_expenses_empty(client: AsyncClient):
    response = await client.get("/expenses/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

@pytest.mark.asyncio
async def test_read_one_expense_success(client: AsyncClient):
    payer = await create_test_user(client, "exp_reader_payer", "exp_reader_payer@example.com")
    expense_data = {"description": "Test Read", "amount": 10.0, "paid_by_user_id": payer["id"]}
    create_resp = await client.post("/expenses/", json=expense_data)
    expense_id = create_resp.json()["id"]

    response = await client.get(f"/expenses/{expense_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["description"] == "Test Read"
    assert data["id"] == expense_id

@pytest.mark.asyncio
async def test_read_one_expense_not_found(client: AsyncClient):
    response = await client.get("/expenses/99966")
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_read_expenses_filters(client: AsyncClient):
    user1 = await create_test_user(client, "filter_user1", "f_user1@example.com")
    user2 = await create_test_user(client, "filter_user2", "f_user2@example.com")
    group1 = await create_test_group(client, "Filter Group 1", user1["id"])
    group2 = await create_test_group(client, "Filter Group 2", user2["id"])

    # Expenses for user1
    await client.post("/expenses/", json={"description": "U1G1E1", "amount": 10, "paid_by_user_id": user1["id"], "group_id": group1["id"]})
    await client.post("/expenses/", json={"description": "U1E2", "amount": 20, "paid_by_user_id": user1["id"]})
    # Expense for user2
    await client.post("/expenses/", json={"description": "U2G2E1", "amount": 30, "paid_by_user_id": user2["id"], "group_id": group2["id"]})

    # Filter by user_id
    response_user1 = await client.get(f"/expenses/?user_id={user1['id']}")
    assert response_user1.status_code == status.HTTP_200_OK
    user1_expenses = response_user1.json()
    assert len(user1_expenses) == 2 # Assuming get_expenses_for_user only gets paid_by for now
    assert all(e["paid_by_user_id"] == user1["id"] for e in user1_expenses)

    # Filter by group_id
    response_group1 = await client.get(f"/expenses/?group_id={group1['id']}")
    assert response_group1.status_code == status.HTTP_200_OK
    group1_expenses = response_group1.json()
    assert len(group1_expenses) == 1
    assert group1_expenses[0]["description"] == "U1G1E1"

@pytest.mark.asyncio
async def test_update_expense_success(client: AsyncClient):
    payer = await create_test_user(client, "exp_updater_payer", "exp_updater_payer@example.com")
    expense_data = {"description": "Initial Desc", "amount": 50.0, "paid_by_user_id": payer["id"]}
    create_resp = await client.post("/expenses/", json=expense_data)
    expense_id = create_resp.json()["id"]

    update_payload = {"description": "Updated Desc", "amount": 75.0}
    response = await client.put(f"/expenses/{expense_id}", json=update_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["description"] == "Updated Desc"
    assert data["amount"] == 75.0

@pytest.mark.asyncio
async def test_update_expense_not_found(client: AsyncClient):
    response = await client.put("/expenses/99955", json={"description": "No one home"})
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_delete_expense_success(client: AsyncClient):
    payer = await create_test_user(client, "exp_deleter_payer", "exp_deleter_payer@example.com")
    expense_data = {"description": "To Delete", "amount": 5.0, "paid_by_user_id": payer["id"]}
    create_resp = await client.post("/expenses/", json=expense_data)
    expense_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/expenses/{expense_id}")
    assert delete_resp.status_code == status.HTTP_200_OK

    get_resp = await client.get(f"/expenses/{expense_id}")
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_delete_expense_not_found(client: AsyncClient):
    response = await client.delete("/expenses/99944")
    assert response.status_code == status.HTTP_404_NOT_FOUND

# Participant Management Tests
@pytest.mark.asyncio
async def test_add_participant_to_expense_success(client: AsyncClient):
    payer = await create_test_user(client, "exp_owner_for_part_add", "eo_fpa@ex.com")
    participant = await create_test_user(client, "exp_part_to_add", "ep_ta@ex.com")
    expense_data = {"description": "Expense for Adding Parts", "amount": 100.0, "paid_by_user_id": payer["id"]}
    create_resp = await client.post("/expenses/", json=expense_data)
    expense_id = create_resp.json()["id"]

    response = await client.post(f"/expenses/{expense_id}/participants/{participant['id']}", json={"share_amount": 50.0})
    assert response.status_code == status.HTTP_200_OK
    # Ideally check if participant is now linked, maybe by reading expense with details if such endpoint exists

@pytest.mark.asyncio
async def test_add_participant_expense_not_found(client: AsyncClient):
    user = await create_test_user(client, "user_for_part_exp_nf", "u_fpenf@ex.com")
    response = await client.post(f"/expenses/9900/participants/{user['id']}", json={"share_amount": 10.0})
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "expense or user not found" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_add_participant_user_not_found(client: AsyncClient):
    payer = await create_test_user(client, "exp_owner_for_part_usr_nf", "eo_fpunf@ex.com")
    expense_data = {"description": "Expense for User NF Part", "amount": 10.0, "paid_by_user_id": payer["id"]}
    create_resp = await client.post("/expenses/", json=expense_data)
    expense_id = create_resp.json()["id"]
    response = await client.post(f"/expenses/{expense_id}/participants/9901", json={"share_amount": 10.0})
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "expense or user not found" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_remove_participant_from_expense_success(client: AsyncClient):
    payer = await create_test_user(client, "exp_owner_for_part_rem", "eo_fpr@ex.com")
    participant = await create_test_user(client, "exp_part_to_rem", "ep_tr@ex.com")
    expense_data = {"description": "Expense for Removing Parts", "amount": 100.0, "paid_by_user_id": payer["id"]}
    create_resp = await client.post("/expenses/", json=expense_data)
    expense_id = create_resp.json()["id"]

    # Add participant first
    await client.post(f"/expenses/{expense_id}/participants/{participant['id']}", json={"share_amount": 50.0})
    
    # Now remove
    response = await client.delete(f"/expenses/{expense_id}/participants/{participant['id']}")
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_remove_participant_expense_not_found(client: AsyncClient):
    user = await create_test_user(client, "user_for_part_rem_enf", "u_fpenfr@ex.com")
    response = await client.delete(f"/expenses/9902/participants/{user['id']}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "expense or user not found" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_remove_participant_user_not_found(client: AsyncClient):
    payer = await create_test_user(client, "exp_owner_for_part_rem_unf", "eo_fprunf@ex.com")
    expense_data = {"description": "Expense for User NF Part Rem", "amount": 10.0, "paid_by_user_id": payer["id"]}
    create_resp = await client.post("/expenses/", json=expense_data)
    expense_id = create_resp.json()["id"]
    response = await client.delete(f"/expenses/{expense_id}/participants/9903")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "expense or user not found" in response.json()["detail"].lower()
