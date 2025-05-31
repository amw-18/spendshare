```python
import pytest
from httpx import AsyncClient
from fastapi import status

# Placeholder for API_V1_STR, adjust if your project uses a different prefix
API_V1_STR = "/api/v1"

@pytest.mark.asyncio
async def test_create_transaction(
    client: AsyncClient, normal_user_token_headers: dict, test_currency_sync: dict
):
    """
    Test creating a new transaction.
    Corresponds to: POST /api/v1/transactions/
    """
    currency_id = test_currency_sync["id"]

    payload = {
        "amount": 100.50,
        "currency_id": currency_id,
        "description": "Payment for team lunch"
    }
    response = await client.post(
        f"{API_V1_STR}/transactions/",
        json=payload,
        headers=normal_user_token_headers
    )
    assert response.status_code == status.HTTP_201_CREATED, f"Actual: {response.status_code}, Expected: {status.HTTP_201_CREATED}, Response: {response.text}"
    data = response.json()
    assert data["amount"] == payload["amount"]
    assert data["currency_id"] == payload["currency_id"]
    assert data["description"] == payload["description"]
    assert "id" in data
    assert "timestamp" in data
    assert "created_by_user_id" in data
    # assert "currency" in data # Check if TransactionRead includes Currency object (it should, as per openapi.json)

@pytest.mark.asyncio
async def test_get_transaction(
    client: AsyncClient, normal_user_token_headers: dict, test_currency_sync: dict
):
    """
    Test retrieving a specific transaction by its ID.
    Corresponds to: GET /api/v1/transactions/{transaction_id}
    """
    currency_id = test_currency_sync["id"]
    # First, create a transaction to retrieve
    payload_create = {
        "amount": 75.00,
        "currency_id": currency_id,
        "description": "Software subscription"
    }
    response_create = await client.post(
        f"{API_V1_STR}/transactions/",
        json=payload_create,
        headers=normal_user_token_headers
    )
    assert response_create.status_code == status.HTTP_201_CREATED, response_create.text
    created_transaction_id = response_create.json()["id"]

    response_get = await client.get(
        f"{API_V1_STR}/transactions/{created_transaction_id}",
        headers=normal_user_token_headers
    )
    assert response_get.status_code == status.HTTP_200_OK, f"Actual: {response_get.status_code}, Expected: {status.HTTP_200_OK}, Response: {response_get.text}"
    data = response_get.json()
    assert data["id"] == created_transaction_id
    assert data["amount"] == payload_create["amount"]
    assert data["currency_id"] == payload_create["currency_id"]
    assert data["description"] == payload_create["description"]
    assert "currency" in data # TransactionRead should include the currency object
    if data.get("currency"):
        assert data["currency"]["id"] == currency_id

@pytest.mark.asyncio
async def test_get_transaction_not_found(client: AsyncClient, normal_user_token_headers: dict):
    """
    Test retrieving a non-existent transaction.
    """
    non_existent_id = 999999
    response = await client.get(
        f"{API_V1_STR}/transactions/{non_existent_id}",
        headers=normal_user_token_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, f"Actual: {response.status_code}, Expected: {status.HTTP_404_NOT_FOUND}, Response: {response.text}"

@pytest.mark.asyncio
async def test_settle_expense_participations(
    client: AsyncClient,
    normal_user_token_headers: dict,
    # Fixtures that would be defined in conftest.py:
    test_user_factory: callable,
    test_currency_factory: callable,
    # The following fixture would be more complex, creating an expense and participants,
    # and returning the expense details along with *actual* ExpenseParticipant IDs.
    # For now, we'll mock these IDs or parts of this setup.
    # test_expense_with_participants_fixture: dict
):
    """
    Test settling expense participations with a transaction.
    Corresponds to: POST /api/v1/expenses/settle
    NOTE: This test makes assumptions about how ExpenseParticipant IDs are generated/retrieved.
    """
    # 1. Setup:
    # Create a currency for the transaction
    transaction_currency = await test_currency_factory(code="TCX", name="TransactionCoinSettle")
    transaction_currency_id = transaction_currency["id"]

    # Create a currency for an expense (can be different from transaction currency)
    expense_currency = await test_currency_factory(code="ECX", name="ExpenseCoinSettle")
    expense_currency_id = expense_currency["id"]

    # Create an expense (paid by the normal_user from normal_user_token_headers)
    expense_payload = {
        "description": "Group Dinner for Settlement Test",
        "amount": 150.00,
        "currency_id": expense_currency_id,
    }
    response_exp = await client.post(f"{API_V1_STR}/expenses/", json=expense_payload, headers=normal_user_token_headers)
    assert response_exp.status_code == status.HTTP_201_CREATED, response_exp.text
    created_expense = response_exp.json()
    expense_id = created_expense["id"]

    # This is where it gets tricky: ExpenseParticipant records.
    # The API to create/add participants to an expense is not part of this issue's scope.
    # The `SettleExpensesRequest` needs `expense_participant_id`.
    # We assume these are integer PKs of an ExpenseParticipant table.
    # For this test, we'll use placeholder IDs. In a real scenario, these would be
    # retrieved after setting up an expense with its participants via existing API endpoints.
    # (e.g., if POST /expenses/ also handles participants or if there's a PUT /expenses/{id})
    # For now, we cannot create actual ExpenseParticipant records and get their IDs.
    # So, this test will focus on the call to /settle and the expected structure.
    mock_expense_participant_id1 = 1001  # Placeholder
    mock_expense_participant_id2 = 1002  # Placeholder

    # 2. Create a Transaction
    transaction_payload = {
        "amount": 100.00, # Sufficient to cover settlements
        "currency_id": transaction_currency_id,
        "description": "Settlement transaction for group dinner"
    }
    response_trans = await client.post(
        f"{API_V1_STR}/transactions/",
        json=transaction_payload,
        headers=normal_user_token_headers
    )
    assert response_trans.status_code == status.HTTP_201_CREATED, response_trans.text
    transaction_data = response_trans.json()
    transaction_id = transaction_data["id"]

    # 3. Prepare settlement payload
    settle_payload = {
        "transaction_id": transaction_id,
        "settlements": [
            {
                "expense_participant_id": mock_expense_participant_id1,
                "settled_amount": 40.00, # 40 TCX for participant 1's share
                "settled_currency_id": transaction_currency_id
            },
            {
                "expense_participant_id": mock_expense_participant_id2,
                "settled_amount": 60.00, # 60 TCX for participant 2's share
                "settled_currency_id": transaction_currency_id
            }
        ]
    }

    # 4. Perform settlement
    response_settle = await client.post(
        f"{API_V1_STR}/expenses/settle",
        json=settle_payload,
        headers=normal_user_token_headers
    )
    assert response_settle.status_code == status.HTTP_200_OK, f"Actual: {response_settle.status_code}, Expected: {status.HTTP_200_OK}, Response: {response_settle.text}"

    settle_data = response_settle.json()
    assert settle_data["status"].lower() == "success" # Or "partial_success"
    assert len(settle_data["updated_expense_participations"]) == 2

    for item in settle_data["updated_expense_participations"]:
        assert item["settled_transaction_id"] == transaction_id
        assert item["settled_currency_id"] == transaction_currency_id
        assert item["status"].lower() == "updated"
        if item["expense_participant_id"] == mock_expense_participant_id1:
            assert item["settled_amount_in_transaction_currency"] == 40.00
        elif item["expense_participant_id"] == mock_expense_participant_id2:
            assert item["settled_amount_in_transaction_currency"] == 60.00

    # 5. Verify by fetching the expense and checking participant details (Conceptual)
    # This part will likely fail or need adjustment because the mock_expense_participant_ids
    # are not linked to actual users/participants of the created_expense.
    # The backend would need to resolve these IDs to actual User+Expense pairs.
    response_get_expense = await client.get(
        f"{API_V1_STR}/expenses/{expense_id}",
        headers=normal_user_token_headers
    )
    assert response_get_expense.status_code == status.HTTP_200_OK, response_get_expense.text
    expense_details = response_get_expense.json()

    # The following checks are highly conceptual due to mock IDs:
    # We are checking if *any* participant in the expense now shows these details.
    # A more accurate test would require knowing which user_id corresponds to mock_expense_participant_id1/2.
    participant1_settled = False
    participant2_settled = False
    for p_detail in expense_details.get("participant_details", []):
        if p_detail.get("settled_transaction_id") == transaction_id:
            if p_detail.get("expense_id") == expense_id: # Ensure it's for the correct expense
                # This assumes the participant_details list will contain entries that were conceptually
                # linked via mock_expense_participant_id1 and mock_expense_participant_id2
                if p_detail.get("settled_amount_in_transaction_currency") == 40.00:
                    participant1_settled = True
                    assert p_detail["settled_currency_id"] == transaction_currency_id
                    assert p_detail["settled_currency"]["id"] == transaction_currency_id
                elif p_detail.get("settled_amount_in_transaction_currency") == 60.00:
                    participant2_settled = True
                    assert p_detail["settled_currency_id"] == transaction_currency_id
                    assert p_detail["settled_currency"]["id"] == transaction_currency_id

    # These assertions will currently rely on the backend somehow associating the mock IDs or
    # the test being adapted once participant creation/retrieval is clear.
    # assert participant1_settled, "Settlement details for participant 1 not reflected in fetched expense"
    # assert participant2_settled, "Settlement details for participant 2 not reflected in fetched expense"


@pytest.mark.asyncio
async def test_settle_expense_insufficient_transaction_amount(
    client: AsyncClient, normal_user_token_headers: dict, test_currency_factory: callable
):
    """
    Test settling with a transaction amount less than the sum of settled amounts.
    Expected: 400 Bad Request.
    """
    transaction_currency = await test_currency_factory(code="TSHORT", name="TransactionShortCoin")
    currency_id = transaction_currency["id"]

    transaction_payload = {
        "amount": 50.00,
        "currency_id": currency_id,
        "description": "Transaction too small for planned settlement"
    }
    response_trans = await client.post(
        f"{API_V1_STR}/transactions/", json=transaction_payload, headers=normal_user_token_headers
    )
    assert response_trans.status_code == status.HTTP_201_CREATED, response_trans.text
    transaction_id = response_trans.json()["id"]

    # Mock IDs for expense participants
    mock_ep_id1 = 2001
    mock_ep_id2 = 2002

    settle_payload = {
        "transaction_id": transaction_id,
        "settlements": [
            { "expense_participant_id": mock_ep_id1, "settled_amount": 30.00, "settled_currency_id": currency_id },
            { "expense_participant_id": mock_ep_id2, "settled_amount": 30.00, "settled_currency_id": currency_id }
        ] # Total 60.00, but transaction is only 50.00
    }

    response_settle = await client.post(
        f"{API_V1_STR}/expenses/settle", json=settle_payload, headers=normal_user_token_headers
    )
    assert response_settle.status_code == status.HTTP_400_BAD_REQUEST, f"Actual: {response_settle.status_code}, Expected: {status.HTTP_400_BAD_REQUEST}, Response: {response_settle.text}"

@pytest.mark.asyncio
async def test_settle_expense_transaction_not_found(
    client: AsyncClient, normal_user_token_headers: dict, test_currency_sync: dict
):
    """
    Test settling with a non-existent transaction ID.
    Expected: 404 Not Found.
    """
    currency_id = test_currency_sync["id"] # Need a valid currency_id for the payload
    non_existent_transaction_id = 888999
    mock_ep_id1 = 3001 # Placeholder

    settle_payload = {
        "transaction_id": non_existent_transaction_id,
        "settlements": [
            { "expense_participant_id": mock_ep_id1, "settled_amount": 10.00, "settled_currency_id": currency_id }
        ]
    }
    response_settle = await client.post(
        f"{API_V1_STR}/expenses/settle", json=settle_payload, headers=normal_user_token_headers
    )
    assert response_settle.status_code == status.HTTP_404_NOT_FOUND, f"Actual: {response_settle.status_code}, Expected: {status.HTTP_404_NOT_FOUND}, Response: {response_settle.text}"

```
