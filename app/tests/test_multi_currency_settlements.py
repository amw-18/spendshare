import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional

# Assuming models are importable like this, adjust if necessary
from app.models.user import User
from app.models.group import Group
from app.models.expense import Expense
from app.models.expense_participant import ExpenseParticipant
from app.models.currency import Currency
from app.models.conversion_rate import ConversionRate # Assuming this model exists
from app.models.transaction import Transaction # Assuming this model exists

# Placeholder for schemas if needed for request/response validation beyond status codes
# from app.schemas.transaction import TransactionCreate, TransactionSettlementItem

# --- Helper Data (Conceptual - to be replaced by fixtures or proper setup) ---

# Mock conversion rate data (in a real scenario, these would be fixture-generated or mocked DB responses)
MOCK_CONVERSION_RATES = {
    ("JPY", "USD"): ConversionRate(id=1, from_currency_id=2, to_currency_id=1, rate=0.0092, timestamp="2023-01-01T12:00:00Z"),
    ("EUR", "USD"): ConversionRate(id=2, from_currency_id=3, to_currency_id=1, rate=1.08, timestamp="2023-01-01T12:00:00Z"),
    ("USD", "EUR"): ConversionRate(id=3, from_currency_id=1, to_currency_id=3, rate=0.92, timestamp="2023-01-01T12:00:00Z"),
}

# Assume these fixtures are defined in conftest.py or similar
# test_user_one, test_user_two: User
# usd_currency, eur_currency, jpy_currency: Currency
# group_one (created by test_user_one): Group
# expense_one_usd (in group_one, paid by user_one, user_two participates): Expense
# expense_two_jpy (in group_one, paid by user_one, user_two participates): Expense
# ep_user_two_for_expense_one_usd: ExpenseParticipant
# ep_user_two_for_expense_two_jpy: ExpenseParticipant
# test_user_one_token, test_user_two_token: str


@pytest.mark.asyncio
async def test_get_settlement_details_group_no_unsettled(
    async_client: AsyncClient, test_user_one: User, group_one: Group, usd_currency: Currency, test_user_one_token: str
):
    """User has no unsettled expenses in the group for the target currency."""
    # Setup: Ensure test_user_one has no unsettled participations FOR OTHERS in group_one
    # or that test_user_one owes nothing to others in group_one.
    # This might involve clearing existing ExpenseParticipant or creating settled ones.
    # For this test, we assume a clean state or specific setup by other fixtures.

    headers = {"Authorization": f"Bearer {test_user_one_token}"}
    response = await async_client.get(
        f"/api/v1/settlement-details/group/{group_one.id}/currency/{usd_currency.id}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["group_id"] == group_one.id
    assert data["target_currency_id"] == usd_currency.id
    assert data["target_currency_code"] == usd_currency.code # Assuming currency code is returned
    assert len(data["settlement_items"]) == 0
    assert data["total_in_target_currency"] == 0
    assert "suggested_transaction_description" in data

@pytest.mark.asyncio
async def test_get_settlement_details_group_same_currency(
    async_client: AsyncClient, db: AsyncSession, test_user_one: User, test_user_two: User,
    group_one: Group, usd_currency: Currency, expense_usd_user_one_owes_user_two: Expense, # User one is participant, user two is payer
    ep_user_one_for_expense_usd: ExpenseParticipant, # user_one's share for expense_usd_user_one_owes_user_two
    test_user_one_token: str
):
    """User has unsettled expenses, all in the target settlement currency."""
    # Setup: test_user_one owes for expense_usd_user_one_owes_user_two (paid by user_two) in USD.
    # ep_user_one_for_expense_usd should be unsettled.
    assert ep_user_one_for_expense_usd.settled_transaction_id is None
    assert expense_usd_user_one_owes_user_two.currency_id == usd_currency.id

    headers = {"Authorization": f"Bearer {test_user_one_token}"}
    response = await async_client.get(
        f"/api/v1/settlement-details/group/{group_one.id}/currency/{usd_currency.id}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["settlement_items"]) >= 1
    item_found = False
    for item in data["settlement_items"]:
        if item["expense_participant_id"] == ep_user_one_for_expense_usd.id:
            assert item["original_share_amount"] == ep_user_one_for_expense_usd.share_amount
            assert item["original_currency_id"] == usd_currency.id
            assert item["converted_share_amount_in_target_currency"] == ep_user_one_for_expense_usd.share_amount
            assert item["conversion_rate_id_used"] is None
            item_found = True
            break
    assert item_found, "Expense participant not found in settlement items"
    # Total needs to be calculated based on actual setup
    # assert data["total_in_target_currency"] == ep_user_one_for_expense_usd.share_amount

@pytest.mark.asyncio
async def test_get_settlement_details_group_different_currencies(
    async_client: AsyncClient, db: AsyncSession, test_user_one: User, test_user_two: User,
    group_one: Group, usd_currency: Currency, jpy_currency: Currency,
    expense_jpy_user_one_owes_user_two: Expense, # User one is participant, user two is payer in JPY
    ep_user_one_for_expense_jpy: ExpenseParticipant, # user_one's share for expense_jpy_user_one_owes_user_two
    test_user_one_token: str, mocker
):
    """User has unsettled expenses in currencies different from the target settlement currency (JPY -> USD)."""
    assert ep_user_one_for_expense_jpy.settled_transaction_id is None
    assert expense_jpy_user_one_owes_user_two.currency_id == jpy_currency.id
    
    mock_rate = MOCK_CONVERSION_RATES[("JPY", "USD")]
    # Mock the DB call that fetches conversion rates
    # This depends on how conversion rates are fetched in the actual endpoint
    # Example: mocker.patch("app.services.conversion_rates.get_latest_rate", return_value=mock_rate)
    # For now, assume the endpoint finds mock_rate.id when converting JPY to USD

    headers = {"Authorization": f"Bearer {test_user_one_token}"}
    response = await async_client.get(
        f"/api/v1/settlement-details/group/{group_one.id}/currency/{usd_currency.id}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["settlement_items"]) >= 1
    item_found = False
    for item in data["settlement_items"]:
        if item["expense_participant_id"] == ep_user_one_for_expense_jpy.id:
            assert item["original_currency_id"] == jpy_currency.id
            # Assuming the mock rate is used. This requires the endpoint to use a rate for JPY to USD.
            # The actual mock_rate.id might be different if it's dynamically created by a fixture.
            # This test needs a reliable way to inject/mock this.
            # assert item["conversion_rate_id_used"] is not None # Placeholder
            # assert item["converted_share_amount_in_target_currency"] == pytest.approx(ep_user_one_for_expense_jpy.share_amount * mock_rate.rate)
            item_found = True
            break
    assert item_found, "JPY Expense participant not found in settlement items"
    # Total needs to be calculated based on actual setup and mocked rates

@pytest.mark.asyncio
async def test_get_settlement_details_group_mixed_currencies(
    async_client: AsyncClient, db: AsyncSession, test_user_one: User, test_user_two: User,
    group_one: Group, usd_currency: Currency, jpy_currency: Currency,
    expense_usd_user_one_owes_user_two: Expense, ep_user_one_for_expense_usd: ExpenseParticipant,
    expense_jpy_user_one_owes_user_two: Expense, ep_user_one_for_expense_jpy: ExpenseParticipant,
    test_user_one_token: str, mocker
):
    """User has some expenses in target currency, some in others."""
    # Mock conversion rate for JPY to USD as in the previous test
    # mock_rate_jpy_usd = MOCK_CONVERSION_RATES[("JPY", "USD")]
    # mocker.patch("app.services.conversion_rates.get_latest_rate", ...) 

    headers = {"Authorization": f"Bearer {test_user_one_token}"}
    response = await async_client.get(
        f"/api/v1/settlement-details/group/{group_one.id}/currency/{usd_currency.id}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["settlement_items"]) >= 2 # Expecting at least two items

    # Check for USD item (no conversion)
    # Check for JPY item (with conversion)
    # Verify total

@pytest.mark.asyncio
async def test_get_settlement_details_group_unauthorized(
    async_client: AsyncClient, group_two: Group, usd_currency: Currency, test_user_one_token: str
):
    """User tries to get details for a group they are not part of."""
    # group_two should be a group test_user_one is not a member of.
    headers = {"Authorization": f"Bearer {test_user_one_token}"}
    response = await async_client.get(
        f"/api/v1/settlement-details/group/{group_two.id}/currency/{usd_currency.id}",
        headers=headers
    )
    assert response.status_code == 403 # Or 404 if groups not part of are hidden

@pytest.mark.asyncio
async def test_get_settlement_details_group_invalid_group_or_currency(
    async_client: AsyncClient, test_user_one_token: str, group_one: Group, usd_currency: Currency
):
    headers = {"Authorization": f"Bearer {test_user_one_token}"}
    response_invalid_group = await async_client.get(
        f"/api/v1/settlement-details/group/99999/currency/{usd_currency.id}",
        headers=headers
    )
    assert response_invalid_group.status_code == 404

    response_invalid_currency = await async_client.get(
        f"/api/v1/settlement-details/group/{group_one.id}/currency/99999",
        headers=headers
    )
    assert response_invalid_currency.status_code == 404


# --- Tests for GET /api/v1/settlement-details/expense/{expense_id}/currency/{currency_id} ---

@pytest.mark.asyncio
async def test_get_settlement_details_expense_already_settled(
    async_client: AsyncClient, db: AsyncSession, test_user_one: User,
    expense_usd_user_one_owes_user_two: Expense, # User one is participant
    ep_user_one_for_expense_usd_settled: ExpenseParticipant, # A pre-settled version
    usd_currency: Currency, test_user_one_token: str
):
    """User's participation in the expense is already settled."""
    # ep_user_one_for_expense_usd_settled should have settled_transaction_id set
    assert ep_user_one_for_expense_usd_settled.settled_transaction_id is not None

    headers = {"Authorization": f"Bearer {test_user_one_token}"}
    response = await async_client.get(
        f"/api/v1/settlement-details/expense/{expense_usd_user_one_owes_user_two.id}/currency/{usd_currency.id}",
        headers=headers
    )
    # Expecting an error or specific response indicating it's settled / nothing to show
    # This depends on implemented behavior. Let's assume 400 Bad Request for now.
    assert response.status_code == 400 # Or a 200 with a specific message/empty item

@pytest.mark.asyncio
async def test_get_settlement_details_expense_same_currency(
    async_client: AsyncClient, test_user_one: User, expense_usd_user_one_owes_user_two: Expense,
    ep_user_one_for_expense_usd: ExpenseParticipant, usd_currency: Currency, test_user_one_token: str
):
    """Expense currency is the same as the target settlement currency."""
    headers = {"Authorization": f"Bearer {test_user_one_token}"}
    response = await async_client.get(
        f"/api/v1/settlement-details/expense/{expense_usd_user_one_owes_user_two.id}/currency/{usd_currency.id}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["expense_id"] == expense_usd_user_one_owes_user_two.id
    assert data["target_currency_id"] == usd_currency.id
    item = data["settlement_item"]
    assert item["expense_participant_id"] == ep_user_one_for_expense_usd.id
    assert item["original_share_amount"] == ep_user_one_for_expense_usd.share_amount
    assert item["original_currency_id"] == usd_currency.id
    assert item["converted_share_amount_in_target_currency"] == ep_user_one_for_expense_usd.share_amount
    assert item["conversion_rate_id_used"] is None
    assert "suggested_transaction_description" in data

@pytest.mark.asyncio
async def test_get_settlement_details_expense_different_currency(
    async_client: AsyncClient, test_user_one: User, jpy_currency: Currency, usd_currency: Currency,
    expense_jpy_user_one_owes_user_two: Expense, ep_user_one_for_expense_jpy: ExpenseParticipant,
    test_user_one_token: str, mocker
):
    """Expense currency is different (JPY -> USD)."""
    # Mock conversion rate JPY to USD
    # mock_rate = MOCK_CONVERSION_RATES[("JPY", "USD")]
    # mocker.patch("app.services.conversion_rates.get_latest_rate", return_value=mock_rate)

    headers = {"Authorization": f"Bearer {test_user_one_token}"}
    response = await async_client.get(
        f"/api/v1/settlement-details/expense/{expense_jpy_user_one_owes_user_two.id}/currency/{usd_currency.id}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    item = data["settlement_item"]
    assert item["original_currency_id"] == jpy_currency.id
    # assert item["conversion_rate_id_used"] is not None # Placeholder for actual rate ID
    # assert item["converted_share_amount_in_target_currency"] == pytest.approx(ep_user_one_for_expense_jpy.share_amount * mock_rate.rate)

@pytest.mark.asyncio
async def test_get_settlement_details_expense_unauthorized(
    async_client: AsyncClient, expense_other_group: Expense, # An expense not involving test_user_one
    usd_currency: Currency, test_user_one_token: str
):
    """User not participant in the expense."""
    headers = {"Authorization": f"Bearer {test_user_one_token}"}
    response = await async_client.get(
        f"/api/v1/settlement-details/expense/{expense_other_group.id}/currency/{usd_currency.id}",
        headers=headers
    )
    assert response.status_code == 403 # Or 404

@pytest.mark.asyncio
async def test_get_settlement_details_expense_invalid_expense_or_currency(
    async_client: AsyncClient, test_user_one_token: str, expense_usd_user_one_owes_user_two: Expense, usd_currency: Currency
):
    headers = {"Authorization": f"Bearer {test_user_one_token}"}
    response_invalid_expense = await async_client.get(
        f"/api/v1/settlement-details/expense/99999/currency/{usd_currency.id}",
        headers=headers
    )
    assert response_invalid_expense.status_code == 404

    response_invalid_currency = await async_client.get(
        f"/api/v1/settlement-details/expense/{expense_usd_user_one_owes_user_two.id}/currency/99999",
        headers=headers
    )
    assert response_invalid_currency.status_code == 404


# --- Tests for POST /api/v1/transactions/ (for Settlement) ---

@pytest.mark.asyncio
async def test_create_transaction_settle_same_currency(
    async_client: AsyncClient, db: AsyncSession, test_user_one: User, test_user_two: User,
    ep_user_one_for_expense_usd: ExpenseParticipant, # User one owes user two for this USD expense part.
    usd_currency: Currency, test_user_one_token: str
):
    """Settle one ExpenseParticipant where expense currency is same as transaction currency."""
    assert ep_user_one_for_expense_usd.settled_transaction_id is None
    settlement_amount = ep_user_one_for_expense_usd.share_amount

    payload = {
        "amount": settlement_amount,
        "currency_id": usd_currency.id,
        "description": "Settling USD debt",
        "settlements": [
            {
                "expense_participant_id": ep_user_one_for_expense_usd.id,
                "amount_to_settle_in_transaction_currency": settlement_amount,
                "conversion_rate_id": None
            }
        ]
    }
    headers = {"Authorization": f"Bearer {test_user_one_token}"}
    response = await async_client.post("/api/v1/transactions/", headers=headers, json=payload)
    assert response.status_code == 201 # Assuming 201 Created for new transaction
    
    # Verify Transaction created (fetch from DB or use response if detailed)
    # Verify ExpenseParticipant updated in DB
    await db.refresh(ep_user_one_for_expense_usd)
    assert ep_user_one_for_expense_usd.settled_transaction_id is not None
    assert ep_user_one_for_expense_usd.settled_amount_in_transaction_currency == settlement_amount
    assert ep_user_one_for_expense_usd.settled_conversion_rate_id is None

@pytest.mark.asyncio
async def test_create_transaction_settle_different_currencies(
    async_client: AsyncClient, db: AsyncSession, test_user_one: User, test_user_two: User,
    ep_user_one_for_expense_jpy: ExpenseParticipant, # User one owes user two for this JPY expense part.
    jpy_currency: Currency, usd_currency: Currency,
    test_user_one_token: str, mocker
):
    """Settle an entry where expense currency (JPY) differs from transaction currency (USD)."""
    assert ep_user_one_for_expense_jpy.settled_transaction_id is None
    
    mock_rate_jpy_to_usd = MOCK_CONVERSION_RATES[("JPY", "USD")] # This needs to be a fixture-created rate
    # For this test, assume mock_rate_jpy_to_usd.id is a valid ID in the DB for a JPY to USD rate.
    # A fixture should create this ConversionRate instance.
    # Let's say a fixture `jpy_to_usd_conversion_rate` provides this.
    # conversion_rate_id_to_use = jpy_to_usd_conversion_rate.id

    # This requires a fixture `jpy_to_usd_conversion_rate` that creates this rate in DB.
    # For now, we'll use a placeholder ID and assume the logic can find it.
    # This part is tricky without actual fixture data.
    # We'll assume a valid `conversion_rate_id` (e.g., 1) is known and corresponds to JPY->USD.
    # And that the amount_to_settle is correctly pre-calculated.
    
    # Assume fixture `jpy_to_usd_rate_obj` exists and is in DB.
    # amount_in_jpy = ep_user_one_for_expense_jpy.share_amount
    # amount_in_usd_for_settlement = round(amount_in_jpy * jpy_to_usd_rate_obj.rate, 2)
    # conversion_rate_id_to_use = jpy_to_usd_rate_obj.id

    # Simplified for now:
    amount_in_usd_for_settlement = 10.0 # Placeholder, should be calculated via rate
    conversion_rate_id_to_use = 1 # Placeholder for a valid JPY to USD rate ID

    payload = {
        "amount": amount_in_usd_for_settlement,
        "currency_id": usd_currency.id,
        "description": "Settling JPY debt with USD",
        "settlements": [
            {
                "expense_participant_id": ep_user_one_for_expense_jpy.id,
                "amount_to_settle_in_transaction_currency": amount_in_usd_for_settlement,
                "conversion_rate_id": conversion_rate_id_to_use # ID of JPY to USD rate
            }
        ]
    }
    headers = {"Authorization": f"Bearer {test_user_one_token}"}
    response = await async_client.post("/api/v1/transactions/", headers=headers, json=payload)
    assert response.status_code == 201

    await db.refresh(ep_user_one_for_expense_jpy)
    assert ep_user_one_for_expense_jpy.settled_transaction_id is not None
    assert ep_user_one_for_expense_jpy.settled_amount_in_transaction_currency == amount_in_usd_for_settlement
    assert ep_user_one_for_expense_jpy.settled_conversion_rate_id == conversion_rate_id_to_use

@pytest.mark.asyncio
async def test_create_transaction_settle_insufficient_amount(
    async_client: AsyncClient, ep_user_one_for_expense_usd: ExpenseParticipant,
    usd_currency: Currency, test_user_one_token: str
):
    """Transaction amount is less than sum of amount_to_settle_in_transaction_currency."""
    payload = {
        "amount": 5.00, # Less than required for the settlement item
        "currency_id": usd_currency.id,
        "description": "Test insufficient amount",
        "settlements": [
            {
                "expense_participant_id": ep_user_one_for_expense_usd.id,
                "amount_to_settle_in_transaction_currency": 10.00, # Requires 10
                "conversion_rate_id": None
            }
        ]
    }
    headers = {"Authorization": f"Bearer {test_user_one_token}"}
    response = await async_client.post("/api/v1/transactions/", headers=headers, json=payload)
    assert response.status_code == 400 # Bad Request

@pytest.mark.asyncio
async def test_create_transaction_settle_invalid_conversion_rate_id(
    async_client: AsyncClient, ep_user_one_for_expense_jpy: ExpenseParticipant,
    usd_currency: Currency, test_user_one_token: str
):
    """A conversion_rate_id is provided that doesn't exist or doesn't match currencies."""
    payload = {
        "amount": 10.00,
        "currency_id": usd_currency.id, # Settling in USD
        "description": "Test invalid conversion rate",
        "settlements": [
            {
                "expense_participant_id": ep_user_one_for_expense_jpy.id, # Expense is JPY
                "amount_to_settle_in_transaction_currency": 10.00,
                "conversion_rate_id": 99999 # Non-existent or incorrect rate ID
            }
        ]
    }
    headers = {"Authorization": f"Bearer {test_user_one_token}"}
    response = await async_client.post("/api/v1/transactions/", headers=headers, json=payload)
    assert response.status_code == 400 # Or 422 if validation error

@pytest.mark.asyncio
async def test_create_transaction_settle_participant_not_found(
    async_client: AsyncClient, usd_currency: Currency, test_user_one_token: str
):
    payload = {
        "amount": 10.00,
        "currency_id": usd_currency.id,
        "description": "Test participant not found",
        "settlements": [
            {
                "expense_participant_id": 99999, # Non-existent
                "amount_to_settle_in_transaction_currency": 10.00,
                "conversion_rate_id": None
            }
        ]
    }
    headers = {"Authorization": f"Bearer {test_user_one_token}"}
    response = await async_client.post("/api/v1/transactions/", headers=headers, json=payload)
    assert response.status_code == 404 # Or 400/422

@pytest.mark.asyncio
async def test_create_transaction_settle_already_settled(
    async_client: AsyncClient, db: AsyncSession,
    ep_user_one_for_expense_usd_settled: ExpenseParticipant, # Already settled
    usd_currency: Currency, test_user_one_token: str
):
    """Attempt to settle an already settled ExpenseParticipant."""
    payload = {
        "amount": ep_user_one_for_expense_usd_settled.share_amount,
        "currency_id": usd_currency.id,
        "description": "Test already settled",
        "settlements": [
            {
                "expense_participant_id": ep_user_one_for_expense_usd_settled.id,
                "amount_to_settle_in_transaction_currency": ep_user_one_for_expense_usd_settled.share_amount,
                "conversion_rate_id": None
            }
        ]
    }
    headers = {"Authorization": f"Bearer {test_user_one_token}"}
    response = await async_client.post("/api/v1/transactions/", headers=headers, json=payload)
    assert response.status_code == 400 # Or specific error code

@pytest.mark.asyncio
async def test_create_transaction_settle_unauthorized_participant(
    async_client: AsyncClient, ep_user_two_for_expense_usd: ExpenseParticipant, # Belongs to user_two
    usd_currency: Currency, test_user_one_token: str # test_user_one trying to settle user_two's debt
):
    """Attempt to settle an ExpenseParticipant not belonging to the user (and user is not payer)."""
    # This assumes test_user_one is NOT the payer of the expense for ep_user_two_for_expense_usd
    payload = {
        "amount": ep_user_two_for_expense_usd.share_amount,
        "currency_id": usd_currency.id,
        "description": "Test unauthorized settlement",
        "settlements": [
            {
                "expense_participant_id": ep_user_two_for_expense_usd.id,
                "amount_to_settle_in_transaction_currency": ep_user_two_for_expense_usd.share_amount,
                "conversion_rate_id": None
            }
        ]
    }
    headers = {"Authorization": f"Bearer {test_user_one_token}"}
    response = await async_client.post("/api/v1/transactions/", headers=headers, json=payload)
    assert response.status_code == 403 # Forbidden


# --- Tests for Expense.is_settled Logic ---

@pytest.mark.asyncio
async def test_expense_becomes_settled(
    async_client: AsyncClient, db: AsyncSession, test_user_one: User, test_user_two: User,
    expense_for_settlement_test: Expense, # Expense with user_one and user_two as participants, user_three as payer
    ep_user_one_for_settlement_test: ExpenseParticipant,
    ep_user_two_for_settlement_test: ExpenseParticipant,
    usd_currency: Currency, test_user_one_token: str, test_user_two_token: str,
    # Assume expense_for_settlement_test is paid by a third user, or that users can settle debts they owe.
):
    """Settle all participants' shares; verify Expense.is_settled becomes True."""
    # Initial state: Expense is not settled
    await db.refresh(expense_for_settlement_test)
    assert not expense_for_settlement_test.is_settled

    # User one settles their share
    payload1 = {
        "amount": ep_user_one_for_settlement_test.share_amount, "currency_id": usd_currency.id,
        "description": "User one settling share",
        "settlements": [{"expense_participant_id": ep_user_one_for_settlement_test.id, "amount_to_settle_in_transaction_currency": ep_user_one_for_settlement_test.share_amount, "conversion_rate_id": None}]
    }
    headers1 = {"Authorization": f"Bearer {test_user_one_token}"} # Assuming user one is settling their own debt
    response1 = await async_client.post("/api/v1/transactions/", headers=headers1, json=payload1)
    assert response1.status_code == 201
    await db.refresh(expense_for_settlement_test)
    assert not expense_for_settlement_test.is_settled # Still not fully settled

    # User two settles their share
    payload2 = {
        "amount": ep_user_two_for_settlement_test.share_amount, "currency_id": usd_currency.id,
        "description": "User two settling share",
        "settlements": [{"expense_participant_id": ep_user_two_for_settlement_test.id, "amount_to_settle_in_transaction_currency": ep_user_two_for_settlement_test.share_amount, "conversion_rate_id": None}]
    }
    headers2 = {"Authorization": f"Bearer {test_user_two_token}"} # Assuming user two is settling their own debt
    response2 = await async_client.post("/api/v1/transactions/", headers=headers2, json=payload2)
    assert response2.status_code == 201
    
    # Now expense should be settled
    await db.refresh(expense_for_settlement_test)
    assert expense_for_settlement_test.is_settled

@pytest.mark.asyncio
async def test_expense_remains_not_settled(
    async_client: AsyncClient, db: AsyncSession, test_user_one: User,
    expense_for_settlement_test: Expense, # As above
    ep_user_one_for_settlement_test: ExpenseParticipant, # User one's part
    # ep_user_two_for_settlement_test is the other part, remains unsettled
    usd_currency: Currency, test_user_one_token: str
):
    """Settle some but not all participants; verify Expense.is_settled remains False."""
    await db.refresh(expense_for_settlement_test)
    assert not expense_for_settlement_test.is_settled

    # User one settles their share
    payload1 = {
        "amount": ep_user_one_for_settlement_test.share_amount, "currency_id": usd_currency.id,
        "description": "User one settling share",
        "settlements": [{"expense_participant_id": ep_user_one_for_settlement_test.id, "amount_to_settle_in_transaction_currency": ep_user_one_for_settlement_test.share_amount, "conversion_rate_id": None}]
    }
    headers1 = {"Authorization": f"Bearer {test_user_one_token}"}
    response1 = await async_client.post("/api/v1/transactions/", headers=headers1, json=payload1)
    assert response1.status_code == 201
    
    # Expense should still not be settled as ep_user_two_for_settlement_test is pending
    await db.refresh(expense_for_settlement_test)
    assert not expense_for_settlement_test.is_settled
```
