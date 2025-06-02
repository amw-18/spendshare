from collections.abc import Callable
from typing import Any, Dict, List  # For type hinting

import pytest
import pytest_asyncio  # For async fixtures
from fastapi import status
from httpx import AsyncClient

from sqlmodel.ext.asyncio.session import AsyncSession  # Import AsyncSession

from src.core.security import get_password_hash  # For creating users in fixtures
from src.models.models import (
    Currency,
    User,
)  # Add necessary model imports for fixtures


# Placeholder for API_V1_STR, adjust if your project uses a different prefix
API_V1_STR = "/api/v1"


@pytest_asyncio.fixture
async def new_user_with_token(
    new_user_with_token_factory: Callable,
):  # Keep one instance for tests that need just one "other" user
    return await new_user_with_token_factory()


@pytest_asyncio.fixture
async def expense_with_participants_setup(
    client: AsyncClient,
    async_db_session: AsyncSession,
    normal_user_token_headers: dict,
    normal_user: User,
    new_user_with_token_factory: Callable,  # Changed from new_user_with_token
    test_currency: Currency,
):
    payer_user_model = normal_user
    participant1_info = (
        await new_user_with_token_factory()
    )  # Changed from new_user_with_token
    participant2_info = (
        await new_user_with_token_factory()
    )  # Changed from new_user_with_token

    expense_create_payload = {
        "description": "Dinner with friends for settlement setup",
        "amount": 300.00,
        "currency_id": test_currency.id,
    }

    service_payload = {
        "expense_in": expense_create_payload,
        "participant_user_ids": [
            participant1_info["user"].id,
            participant2_info["user"].id,
            payer_user_model.id,
        ],
    }

    response = await client.post(
        f"{API_V1_STR}/expenses/service/",
        json=service_payload,
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED, (
        f"Failed to create expense with participants: {response.text}"
    )
    created_expense_details = response.json()

    participant1_record_id = None
    participant2_record_id = None
    payer_participant_record_id = None

    for pd in created_expense_details["participant_details"]:
        if pd["user"]["id"] == participant1_info["user"].id:
            participant1_record_id = pd["id"]
        elif pd["user"]["id"] == participant2_info["user"].id:
            participant2_record_id = pd["id"]
        elif pd["user"]["id"] == payer_user_model.id:
            payer_participant_record_id = pd["id"]

    assert participant1_record_id is not None, "Participant 1 EP record ID not found"
    assert participant2_record_id is not None, "Participant 2 EP record ID not found"
    assert payer_participant_record_id is not None, "Payer EP record ID not found"

    return {
        "payer_user": payer_user_model,
        "payer_headers": normal_user_token_headers,
        "participant1_data": {
            **participant1_info,
            "participant_record_id": participant1_record_id,
        },
        "participant2_data": {
            **participant2_info,
            "participant_record_id": participant2_record_id,
        },
        "payer_participant_data": {
            "user": payer_user_model,
            "headers": normal_user_token_headers,
            "participant_record_id": payer_participant_record_id,
        },
        "expense_details": created_expense_details,
        "expense_currency": test_currency,
    }


@pytest.mark.asyncio
async def test_create_transaction(
    client: AsyncClient, normal_user_token_headers: dict, test_currency: Currency
):
    currency_id = test_currency.id
    payload = {
        "amount": 100.50,
        "currency_id": currency_id,
        "description": "Payment for team lunch",
    }
    response = await client.post(
        f"{API_V1_STR}/transactions/", json=payload, headers=normal_user_token_headers
    )
    assert response.status_code == status.HTTP_201_CREATED, (
        f"Actual: {response.status_code}, Expected: {status.HTTP_201_CREATED}, Response: {response.text}"
    )
    data = response.json()
    assert data["amount"] == payload["amount"]
    assert data["currency_id"] == payload["currency_id"]
    assert data["description"] == payload["description"]
    assert "id" in data
    assert "timestamp" in data
    assert "created_by_user_id" in data
    assert "currency" in data
    assert data["currency"]["id"] == currency_id
    assert data["currency"]["code"] == test_currency.code


@pytest.mark.asyncio
async def test_create_transaction_without_description(
    client: AsyncClient, normal_user_token_headers: dict, test_currency: Currency
):
    currency_id = test_currency.id
    payload = {
        "amount": 50.25,
        "currency_id": currency_id,
        # No description
    }
    response = await client.post(
        f"{API_V1_STR}/transactions/", json=payload, headers=normal_user_token_headers
    )
    assert response.status_code == status.HTTP_201_CREATED, response.text
    data = response.json()
    assert data["amount"] == payload["amount"]
    assert data["currency_id"] == payload["currency_id"]
    # Assuming the model sets description to None or empty string if not provided
    assert data.get("description") is None or data.get("description") == "", (
        f"Description should be None or empty, but was: {data.get('description')}"
    )
    assert "id" in data
    assert "timestamp" in data
    assert "created_by_user_id" in data


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload_override, expected_status, description_for_test_case",
    [
        ({"amount": None}, status.HTTP_422_UNPROCESSABLE_ENTITY, "Missing amount"),
        (
            {"currency_id": None},
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Missing currency_id",
        ),
        ({"amount": -10.0}, status.HTTP_422_UNPROCESSABLE_ENTITY, "Negative amount"),
        ({"amount": 0.0}, status.HTTP_422_UNPROCESSABLE_ENTITY, "Zero amount"),
        (
            {"currency_id": 999999},
            status.HTTP_404_NOT_FOUND,
            "Non-existent currency_id",
        ),
    ],
)
async def test_create_transaction_invalid_inputs(
    client: AsyncClient,
    normal_user_token_headers: dict,
    test_currency: Currency,
    payload_override: dict,
    expected_status: int,
    description_for_test_case: str,  # For clarity in test output
):
    base_payload = {
        "amount": 100.00,
        "currency_id": test_currency.id,
        "description": f"Test for: {description_for_test_case}",
    }

    invalid_payload = {**base_payload, **payload_override}

    # For testing missing required fields, remove them if their override value is None
    if payload_override.get("amount") is None and "amount" in payload_override:
        if "amount" in invalid_payload:
            del invalid_payload["amount"]
    if (
        payload_override.get("currency_id") is None
        and "currency_id" in payload_override
    ):
        if "currency_id" in invalid_payload:
            del invalid_payload["currency_id"]

    response = await client.post(
        f"{API_V1_STR}/transactions/",
        json=invalid_payload,
        headers=normal_user_token_headers,
    )
    assert response.status_code == expected_status, (
        f"Test Case: '{description_for_test_case}'. Payload: {invalid_payload}. Actual: {response.status_code}, Expected: {expected_status}, Response: {response.text}"
    )


@pytest.mark.asyncio
async def test_get_transaction(
    client: AsyncClient,
    normal_user_token_headers: dict,
    test_currency: Currency,
    normal_user: User,
):
    currency_id = test_currency.id
    payload_create = {
        "amount": 75.00,
        "currency_id": currency_id,
        "description": "Software subscription",
    }
    response_create = await client.post(
        f"{API_V1_STR}/transactions/",
        json=payload_create,
        headers=normal_user_token_headers,
    )
    assert response_create.status_code == status.HTTP_201_CREATED, response_create.text
    created_transaction_id = response_create.json()["id"]

    response_get = await client.get(
        f"{API_V1_STR}/transactions/{created_transaction_id}",
        headers=normal_user_token_headers,
    )
    assert response_get.status_code == status.HTTP_200_OK, (
        f"Actual: {response_get.status_code}, Expected: {status.HTTP_200_OK}, Response: {response_get.text}"
    )
    data = response_get.json()
    assert data["id"] == created_transaction_id
    assert data["amount"] == payload_create["amount"]
    assert data["currency_id"] == payload_create["currency_id"]
    assert data["description"] == payload_create["description"]
    assert data["created_by_user_id"] == normal_user.id
    assert "currency" in data
    assert data["currency"]["id"] == currency_id
    assert data["currency"]["code"] == test_currency.code


@pytest.mark.asyncio
async def test_get_transaction_access_control(
    client: AsyncClient,
    normal_user: User,
    normal_user_token_headers: dict,
    new_user_with_token_factory: Callable,  # Use factory for multiple users
    expense_with_participants_setup: dict,
    test_currency: Currency,
):
    payload_create = {
        "amount": 50.00,
        "currency_id": test_currency.id,
        "description": "Access control test transaction",
    }
    response_create = await client.post(
        f"{API_V1_STR}/transactions/",
        json=payload_create,
        headers=normal_user_token_headers,
    )
    assert response_create.status_code == status.HTTP_201_CREATED
    transaction_id = response_create.json()["id"]

    response_get_creator = await client.get(
        f"{API_V1_STR}/transactions/{transaction_id}", headers=normal_user_token_headers
    )
    assert response_get_creator.status_code == status.HTTP_200_OK

    other_user_info = await new_user_with_token_factory()  # Call factory
    response_get_other = await client.get(
        f"{API_V1_STR}/transactions/{transaction_id}",
        headers=other_user_info["headers"],
    )
    assert response_get_other.status_code == status.HTTP_403_FORBIDDEN

    setup_data = expense_with_participants_setup
    payer_headers = setup_data["payer_headers"]
    participant1_ep_id = setup_data["participant1_data"]["participant_record_id"]
    participant1_headers = setup_data["participant1_data"]["headers"]
    participant2_headers = setup_data["participant2_data"]["headers"]

    settlement_tx_payload = {
        "amount": 100.00,
        "currency_id": test_currency.id,
        "description": "Tx for participant access test",
    }
    resp_settlement_tx = await client.post(
        f"{API_V1_STR}/transactions/", json=settlement_tx_payload, headers=payer_headers
    )
    assert resp_settlement_tx.status_code == status.HTTP_201_CREATED
    settlement_transaction_id = resp_settlement_tx.json()["id"]

    settle_p1_payload = {
        "transaction_id": settlement_transaction_id,
        "settlements": [
            {
                "expense_participant_id": participant1_ep_id,
                "settled_amount": 50.00,
                "settled_currency_id": test_currency.id,
            }
        ],
    }
    resp_settle_p1 = await client.post(
        f"{API_V1_STR}/expenses/settle", json=settle_p1_payload, headers=payer_headers
    )
    assert resp_settle_p1.status_code == status.HTTP_200_OK

    resp_get_p1 = await client.get(
        f"{API_V1_STR}/transactions/{settlement_transaction_id}",
        headers=participant1_headers,
    )
    assert resp_get_p1.status_code == status.HTTP_200_OK

    resp_get_p2 = await client.get(
        f"{API_V1_STR}/transactions/{settlement_transaction_id}",
        headers=participant2_headers,
    )
    assert resp_get_p2.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_get_transaction_not_found(
    client: AsyncClient, normal_user_token_headers: dict
):
    non_existent_id = 999999
    response = await client.get(
        f"{API_V1_STR}/transactions/{non_existent_id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, (
        f"Actual: {response.status_code}, Expected: {status.HTTP_404_NOT_FOUND}, Response: {response.text}"
    )


@pytest.mark.asyncio
async def test_settle_expense_participations(
    client: AsyncClient, expense_with_participants_setup: dict, test_currency: Currency
):
    setup_data = expense_with_participants_setup
    payer_headers = setup_data["payer_headers"]
    participant1_data = setup_data["participant1_data"]
    payer_ep_id = setup_data["payer_participant_data"]["participant_record_id"]
    participant1_ep_id = participant1_data["participant_record_id"]
    expense_id = setup_data["expense_details"]["id"]

    transaction_currency_id = test_currency.id

    transaction_payload = {
        "amount": 200.00,
        "currency_id": transaction_currency_id,
        "description": "Settlement transaction",
    }
    response_trans = await client.post(
        f"{API_V1_STR}/transactions/", json=transaction_payload, headers=payer_headers
    )
    assert response_trans.status_code == status.HTTP_201_CREATED, response_trans.text
    transaction_data = response_trans.json()
    transaction_id = transaction_data["id"]

    payer_share_amount_to_settle = 100.00
    settle_payload_payer = {
        "transaction_id": transaction_id,
        "settlements": [
            {
                "expense_participant_id": payer_ep_id,
                "settled_amount": payer_share_amount_to_settle,
                "settled_currency_id": transaction_currency_id,
            }
        ],
    }
    response_settle_payer = await client.post(
        f"{API_V1_STR}/expenses/settle",
        json=settle_payload_payer,
        headers=payer_headers,
    )
    assert response_settle_payer.status_code == status.HTTP_200_OK, (
        response_settle_payer.text
    )
    settle_data_payer = response_settle_payer.json()
    assert settle_data_payer["status"].lower() == "completed"
    assert len(settle_data_payer["updated_expense_participations"]) == 1
    payer_settlement_result = settle_data_payer["updated_expense_participations"][0]
    assert payer_settlement_result["expense_participant_id"] == payer_ep_id
    assert payer_settlement_result["settled_transaction_id"] == transaction_id
    assert (
        payer_settlement_result["settled_amount_in_transaction_currency"]
        == payer_share_amount_to_settle
    )
    assert payer_settlement_result["settled_currency_id"] == transaction_currency_id
    assert payer_settlement_result["status"].lower() == "success"

    participant1_share_amount_to_settle = 100.00
    participant1_transaction_payload = {
        "amount": participant1_share_amount_to_settle,
        "currency_id": transaction_currency_id,
        "description": "Participant1 settlement transaction",
    }
    response_trans_p1 = await client.post(
        f"{API_V1_STR}/transactions/",
        json=participant1_transaction_payload,
        headers=participant1_data["headers"],
    )
    assert response_trans_p1.status_code == status.HTTP_201_CREATED, (
        response_trans_p1.text
    )
    p1_transaction_id = response_trans_p1.json()["id"]

    settle_payload_participant1_own_tx = {
        "transaction_id": p1_transaction_id,
        "settlements": [
            {
                "expense_participant_id": participant1_ep_id,
                "settled_amount": participant1_share_amount_to_settle,
                "settled_currency_id": transaction_currency_id,
            }
        ],
    }
    response_settle_participant1 = await client.post(
        f"{API_V1_STR}/expenses/settle",
        json=settle_payload_participant1_own_tx,
        headers=participant1_data["headers"],
    )
    assert response_settle_participant1.status_code == status.HTTP_200_OK, (
        response_settle_participant1.text
    )
    settle_data_participant1 = response_settle_participant1.json()
    assert settle_data_participant1["status"].lower() == "completed"
    assert len(settle_data_participant1["updated_expense_participations"]) == 1
    p1_settlement_result = settle_data_participant1["updated_expense_participations"][0]
    assert p1_settlement_result["expense_participant_id"] == participant1_ep_id
    assert p1_settlement_result["settled_transaction_id"] == p1_transaction_id
    assert p1_settlement_result["status"].lower() == "success"

    response_get_expense = await client.get(
        f"{API_V1_STR}/expenses/{expense_id}", headers=payer_headers
    )
    assert response_get_expense.status_code == status.HTTP_200_OK, (
        response_get_expense.text
    )
    expense_details_after = response_get_expense.json()

    found_payer_settlement = False
    found_p1_settlement = False

    for p_detail in expense_details_after["participant_details"]:
        ep_id_in_detail = p_detail["id"]

        if ep_id_in_detail == payer_ep_id:
            assert p_detail["settled_transaction_id"] == transaction_id
            assert (
                p_detail["settled_amount_in_transaction_currency"]
                == payer_share_amount_to_settle
            )
            assert p_detail["settled_currency_id"] == transaction_currency_id
            assert p_detail["settled_currency"]["id"] == transaction_currency_id
            found_payer_settlement = True

        if ep_id_in_detail == participant1_ep_id:
            assert p_detail["settled_transaction_id"] == p1_transaction_id
            assert (
                p_detail["settled_amount_in_transaction_currency"]
                == participant1_share_amount_to_settle
            )
            assert p_detail["settled_currency_id"] == transaction_currency_id
            assert p_detail["settled_currency"]["id"] == transaction_currency_id
            found_p1_settlement = True

    assert found_payer_settlement, (
        "Payer settlement details not found or incorrect in fetched expense."
    )
    assert found_p1_settlement, (
        "Participant1 settlement details not found or incorrect in fetched expense."
    )


@pytest.mark.asyncio
async def test_settle_by_non_transaction_creator(
    client: AsyncClient, expense_with_participants_setup: dict, test_currency: Currency
):
    setup_data = expense_with_participants_setup
    payer_headers = setup_data["payer_headers"]
    participant1_headers = setup_data["participant1_data"]["headers"]
    participant1_ep_id = setup_data["participant1_data"]["participant_record_id"]

    transaction_payload = {
        "amount": 100.00,
        "currency_id": test_currency.id,
        "description": "Payer's Transaction",
    }
    response_trans = await client.post(
        f"{API_V1_STR}/transactions/", json=transaction_payload, headers=payer_headers
    )
    assert response_trans.status_code == status.HTTP_201_CREATED
    payers_transaction_id = response_trans.json()["id"]

    settle_payload = {
        "transaction_id": payers_transaction_id,
        "settlements": [
            {
                "expense_participant_id": participant1_ep_id,
                "settled_amount": 50.00,
                "settled_currency_id": test_currency.id,
            }
        ],
    }
    response_settle = await client.post(
        f"{API_V1_STR}/expenses/settle",
        json=settle_payload,
        headers=participant1_headers,
    )
    assert response_settle.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_settle_other_user_expense_part(
    client: AsyncClient, expense_with_participants_setup: dict, test_currency: Currency
):
    setup_data = expense_with_participants_setup
    payer_headers = setup_data["payer_headers"]
    participant1_ep_id = setup_data["participant1_data"]["participant_record_id"]

    transaction_payload = {
        "amount": 100.00,
        "currency_id": test_currency.id,
        "description": "Payer's Transaction for settling other's share",
    }
    response_trans = await client.post(
        f"{API_V1_STR}/transactions/", json=transaction_payload, headers=payer_headers
    )
    assert response_trans.status_code == status.HTTP_201_CREATED
    transaction_id = response_trans.json()["id"]

    settle_payload = {
        "transaction_id": transaction_id,
        "settlements": [
            {
                "expense_participant_id": participant1_ep_id,
                "settled_amount": 50.00,
                "settled_currency_id": test_currency.id,
            }
        ],
    }
    response_settle = await client.post(
        f"{API_V1_STR}/expenses/settle", json=settle_payload, headers=payer_headers
    )
    assert response_settle.status_code == status.HTTP_200_OK
    settle_data = response_settle.json()
    assert (
        settle_data["updated_expense_participations"][0]["status"].lower() == "success"
    )
    assert (
        settle_data["updated_expense_participations"][0][
            "settled_amount_in_transaction_currency"
        ]
        == 50.00
    )
    assert (
        settle_data["updated_expense_participations"][0]["settled_transaction_id"]
        == transaction_id
    )


@pytest.mark.asyncio
async def test_settle_currency_mismatch(
    client: AsyncClient,
    expense_with_participants_setup: dict,
    test_currency: Currency,
    currency_factory: Callable,
):
    setup_data = expense_with_participants_setup
    payer_headers = setup_data["payer_headers"]
    payer_ep_id = setup_data["payer_participant_data"]["participant_record_id"]

    other_currency = await currency_factory(code="OTH", name="OtherCoin")

    transaction_payload = {
        "amount": 100.00,
        "currency_id": test_currency.id,
        "description": "Transaction in test_currency",
    }
    response_trans = await client.post(
        f"{API_V1_STR}/transactions/", json=transaction_payload, headers=payer_headers
    )
    assert response_trans.status_code == status.HTTP_201_CREATED
    transaction_id = response_trans.json()["id"]

    settle_payload = {
        "transaction_id": transaction_id,
        "settlements": [
            {
                "expense_participant_id": payer_ep_id,
                "settled_amount": 50.00,
                "settled_currency_id": other_currency.id,
            }
        ],
    }
    response_settle = await client.post(
        f"{API_V1_STR}/expenses/settle", json=settle_payload, headers=payer_headers
    )
    assert response_settle.status_code == status.HTTP_200_OK
    settle_data = response_settle.json()
    assert (
        settle_data["updated_expense_participations"][0]["status"].lower() == "failed"
    )
    assert (
        "does not match transaction currency id"
        in settle_data["updated_expense_participations"][0]["message"].lower()
    )


@pytest.mark.asyncio
async def test_settle_expense_participant_not_found(
    client: AsyncClient, normal_user_token_headers: dict, test_currency: Currency
):
    transaction_payload = {
        "amount": 100.00,
        "currency_id": test_currency.id,
        "description": "Tx for non-existent EP",
    }
    response_trans = await client.post(
        f"{API_V1_STR}/transactions/",
        json=transaction_payload,
        headers=normal_user_token_headers,
    )
    assert response_trans.status_code == status.HTTP_201_CREATED
    transaction_id = response_trans.json()["id"]

    fake_ep_id = 99999
    settle_payload = {
        "transaction_id": transaction_id,
        "settlements": [
            {
                "expense_participant_id": fake_ep_id,
                "settled_amount": 50.00,
                "settled_currency_id": test_currency.id,
            }
        ],
    }
    response_settle = await client.post(
        f"{API_V1_STR}/expenses/settle",
        json=settle_payload,
        headers=normal_user_token_headers,
    )
    assert response_settle.status_code == status.HTTP_200_OK
    settle_data = response_settle.json()
    assert (
        settle_data["updated_expense_participations"][0]["status"].lower() == "failed"
    )
    assert (
        "expenseparticipant record not found"
        in settle_data["updated_expense_participations"][0]["message"].lower()
    )


@pytest.mark.asyncio
async def test_settle_already_settled_expense_part(
    client: AsyncClient, expense_with_participants_setup: dict, test_currency: Currency
):
    setup_data = expense_with_participants_setup
    payer_headers = setup_data["payer_headers"]
    payer_ep_id = setup_data["payer_participant_data"]["participant_record_id"]

    tx_a_payload = {
        "amount": 50.00,
        "currency_id": test_currency.id,
        "description": "Transaction A",
    }
    resp_tx_a = await client.post(
        f"{API_V1_STR}/transactions/", json=tx_a_payload, headers=payer_headers
    )
    assert resp_tx_a.status_code == status.HTTP_201_CREATED
    tx_a_id = resp_tx_a.json()["id"]

    settle_with_tx_a_payload = {
        "transaction_id": tx_a_id,
        "settlements": [
            {
                "expense_participant_id": payer_ep_id,
                "settled_amount": 50.00,
                "settled_currency_id": test_currency.id,
            }
        ],
    }
    resp_settle_a = await client.post(
        f"{API_V1_STR}/expenses/settle",
        json=settle_with_tx_a_payload,
        headers=payer_headers,
    )
    assert resp_settle_a.status_code == status.HTTP_200_OK
    assert (
        resp_settle_a.json()["updated_expense_participations"][0]["status"].lower()
        == "success"
    )

    tx_b_payload = {
        "amount": 50.00,
        "currency_id": test_currency.id,
        "description": "Transaction B",
    }
    resp_tx_b = await client.post(
        f"{API_V1_STR}/transactions/", json=tx_b_payload, headers=payer_headers
    )
    assert resp_tx_b.status_code == status.HTTP_201_CREATED
    tx_b_id = resp_tx_b.json()["id"]

    settle_with_tx_b_payload = {
        "transaction_id": tx_b_id,
        "settlements": [
            {
                "expense_participant_id": payer_ep_id,
                "settled_amount": 50.00,
                "settled_currency_id": test_currency.id,
            }
        ],
    }
    resp_settle_b = await client.post(
        f"{API_V1_STR}/expenses/settle",
        json=settle_with_tx_b_payload,
        headers=payer_headers,
    )
    assert resp_settle_b.status_code == status.HTTP_200_OK
    settle_data_b = resp_settle_b.json()
    assert (
        settle_data_b["updated_expense_participations"][0]["status"].lower() == "failed"
    )
    assert (
        "already settled by transaction"
        in settle_data_b["updated_expense_participations"][0]["message"].lower()
    )


@pytest.mark.asyncio
async def test_settle_expense_insufficient_transaction_amount(
    client: AsyncClient, normal_user_token_headers: dict, test_currency: Currency
):
    currency_id = test_currency.id
    transaction_payload = {
        "amount": 50.00,
        "currency_id": currency_id,
        "description": "Transaction too small for planned settlement",
    }
    response_trans = await client.post(
        f"{API_V1_STR}/transactions/",
        json=transaction_payload,
        headers=normal_user_token_headers,
    )
    assert response_trans.status_code == status.HTTP_201_CREATED, response_trans.text
    transaction_id = response_trans.json()["id"]

    mock_ep_id1 = 2001
    mock_ep_id2 = 2002

    settle_payload = {
        "transaction_id": transaction_id,
        "settlements": [
            {
                "expense_participant_id": mock_ep_id1,
                "settled_amount": 30.00,
                "settled_currency_id": currency_id,
            },
            {
                "expense_participant_id": mock_ep_id2,
                "settled_amount": 30.00,
                "settled_currency_id": currency_id,
            },
        ],
    }
    response_settle = await client.post(
        f"{API_V1_STR}/expenses/settle",
        json=settle_payload,
        headers=normal_user_token_headers,
    )
    assert response_settle.status_code == status.HTTP_400_BAD_REQUEST, (
        f"Actual: {response_settle.status_code}, Expected: {status.HTTP_400_BAD_REQUEST}, Response: {response_settle.text}"
    )


@pytest.mark.asyncio
async def test_settle_expense_transaction_not_found(
    client: AsyncClient, normal_user_token_headers: dict, test_currency: Currency
):
    currency_id = test_currency.id
    non_existent_transaction_id = 888999
    mock_ep_id1 = 3001

    settle_payload = {
        "transaction_id": non_existent_transaction_id,
        "settlements": [
            {
                "expense_participant_id": mock_ep_id1,
                "settled_amount": 10.00,
                "settled_currency_id": currency_id,
            }
        ],
    }
    response_settle = await client.post(
        f"{API_V1_STR}/expenses/settle",
        json=settle_payload,
        headers=normal_user_token_headers,
    )
    assert response_settle.status_code == status.HTTP_404_NOT_FOUND, (
        f"Actual: {response_settle.status_code}, Expected: {status.HTTP_404_NOT_FOUND}, Response: {response_settle.text}"
    )


@pytest.mark.asyncio
async def test_settle_partial_transaction_amount(
    client: AsyncClient, expense_with_participants_setup: dict, test_currency: Currency
):
    setup_data = expense_with_participants_setup
    payer_headers = setup_data["payer_headers"]
    payer_ep_id = setup_data["payer_participant_data"]["participant_record_id"]
    # Payer's share is 100.00 in this setup

    transaction_payload = {
        "amount": 100.00,
        "currency_id": test_currency.id,
        "description": "Transaction for partial settlement",
    }
    response_trans = await client.post(
        f"{API_V1_STR}/transactions/", json=transaction_payload, headers=payer_headers
    )
    assert response_trans.status_code == status.HTTP_201_CREATED
    transaction_id = response_trans.json()["id"]

    # Settle only 30.00 out of 100.00 share using the 100.00 transaction
    settle_payload = {
        "transaction_id": transaction_id,
        "settlements": [
            {
                "expense_participant_id": payer_ep_id,
                "settled_amount": 30.00,
                "settled_currency_id": test_currency.id,
            }
        ],
    }
    response_settle = await client.post(
        f"{API_V1_STR}/expenses/settle", json=settle_payload, headers=payer_headers
    )
    assert response_settle.status_code == status.HTTP_200_OK, response_settle.text
    settle_data = response_settle.json()
    assert (
        settle_data["updated_expense_participations"][0]["status"].lower() == "success"
    )
    assert (
        settle_data["updated_expense_participations"][0][
            "settled_amount_in_transaction_currency"
        ]
        == 30.00
    )
    assert (
        settle_data["updated_expense_participations"][0]["settled_transaction_id"]
        == transaction_id
    )

    # Verify the expense participant record reflects this partial settlement
    # This might require fetching the EP record again if the settle response isn't detailed enough
    # For now, we trust the response from the settle endpoint.
    # A future test could verify that the remaining transaction amount is 70.00 if that's tracked.


@pytest.mark.asyncio
async def test_settle_with_zero_settled_amount(
    client: AsyncClient, expense_with_participants_setup: dict, test_currency: Currency
):
    setup_data = expense_with_participants_setup
    payer_headers = setup_data["payer_headers"]
    payer_ep_id = setup_data["payer_participant_data"]["participant_record_id"]
    # Payer's share is 100.00

    transaction_payload = {
        "amount": 50.00,
        "currency_id": test_currency.id,
        "description": "Transaction for zero settlement",
    }
    response_trans = await client.post(
        f"{API_V1_STR}/transactions/", json=transaction_payload, headers=payer_headers
    )
    assert response_trans.status_code == status.HTTP_201_CREATED
    transaction_id = response_trans.json()["id"]

    settle_payload = {
        "transaction_id": transaction_id,
        "settlements": [
            {
                "expense_participant_id": payer_ep_id,
                "settled_amount": 0.00,  # Settling with zero amount
                "settled_currency_id": test_currency.id,
            }
        ],
    }
    response_settle = await client.post(
        f"{API_V1_STR}/expenses/settle", json=settle_payload, headers=payer_headers
    )
    assert response_settle.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, (
        response_settle.text
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "settlements_override, expected_status, description",
    [
        (
            [
                {
                    "expense_participant_id": 1,
                    "settled_amount": -10.00,
                    "settled_currency_id": 1,
                }
            ],
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Negative settled_amount",
        ),
        (
            [],
            status.HTTP_422_UNPROCESSABLE_ENTITY,  # Pydantic validator for non-empty list returns 422
            "Empty settlements array",
        ),
        (
            [
                {
                    "expense_participant_id": 1,
                    "settled_amount": 10.00,
                    "settled_currency_id": 1,
                },
                {
                    "expense_participant_id": 1,
                    "settled_amount": 5.00,
                    "settled_currency_id": 1,
                },
            ],
            status.HTTP_400_BAD_REQUEST,
            "Duplicate expense_participant_id in settlements",
        ),
    ],
)
async def test_settle_invalid_settlement_inputs(
    client: AsyncClient,
    expense_with_participants_setup: dict,
    test_currency: Currency,
    settlements_override: List[Dict[str, Any]],
    expected_status: int,
    description: str,
):
    setup_data = expense_with_participants_setup
    payer_headers = setup_data["payer_headers"]
    # Use a real EP ID from setup if needed, but for some tests (like negative amount) it might not matter
    # For duplicate test, we need a valid EP ID to use.
    valid_ep_id = setup_data["payer_participant_data"]["participant_record_id"]
    valid_currency_id = test_currency.id

    transaction_payload = {
        "amount": 100.00,
        "currency_id": valid_currency_id,
        "description": f"Transaction for {description}",
    }
    response_trans = await client.post(
        f"{API_V1_STR}/transactions/", json=transaction_payload, headers=payer_headers
    )
    assert response_trans.status_code == status.HTTP_201_CREATED
    transaction_id = response_trans.json()["id"]

    # Adjust payload for test cases
    final_settlements = []
    if description == "Negative settled_amount":
        final_settlements = [
            {
                **settlements_override[0],
                "expense_participant_id": valid_ep_id,
                "settled_currency_id": valid_currency_id,
            }
        ]
    elif description == "Empty settlements array":
        final_settlements = settlements_override
    elif description == "Duplicate expense_participant_id in settlements":
        final_settlements = [
            {
                "expense_participant_id": valid_ep_id,
                "settled_amount": 10.00,
                "settled_currency_id": valid_currency_id,
            },
            {
                "expense_participant_id": valid_ep_id,
                "settled_amount": 5.00,
                "settled_currency_id": valid_currency_id,
            },
        ]
    else:
        final_settlements = (
            settlements_override  # Should not happen with current param list
        )

    settle_payload = {
        "transaction_id": transaction_id,
        "settlements": final_settlements,
    }

    response_settle = await client.post(
        f"{API_V1_STR}/expenses/settle", json=settle_payload, headers=payer_headers
    )
    assert response_settle.status_code == expected_status, (
        f"Test Case: '{description}'. Payload: {settle_payload}. Actual: {response_settle.status_code}, Expected: {expected_status}, Response: {response_settle.text}"
    )
