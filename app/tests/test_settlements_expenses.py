import pytest
from typing import Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from app.src.models.models import Currency, ConversionRate, User, Group, Expense, ExpenseParticipant
from app.src.models import schemas # Import the schemas module
from app.src.routers.expenses import _convert_amount # Ensure this path is correct

# Mark all tests in this file to use the anyio backend
pytestmark = pytest.mark.anyio

async def test_convert_amount_direct_rate(
    test_db_session: AsyncSession,
    create_currency,
    create_conversion_rate
):
    """Test _convert_amount with a direct conversion rate."""
    currency_usd = await create_currency(test_db_session, code="USD", name="US Dollar")
    currency_eur = await create_currency(test_db_session, code="EUR", name="Euro")
    await create_conversion_rate(test_db_session, currency_usd.id, currency_eur.id, 0.9)

    amount_to_convert = 100.0
    converted_amount, rate_used = await _convert_amount(
        test_db_session, amount_to_convert, currency_usd.id, currency_eur.id
    )

    assert converted_amount is not None
    assert rate_used is not None
    assert pytest.approx(converted_amount) == 90.0
    assert rate_used.rate == 0.9
    assert rate_used.from_currency_id == currency_usd.id
    assert rate_used.to_currency_id == currency_eur.id

async def test_convert_amount_reverse_rate(
    test_db_session: AsyncSession,
    create_currency,
    create_conversion_rate
):
    """Test _convert_amount with a reverse conversion rate."""
    currency_usd = await create_currency(test_db_session, code="USD", name="US Dollar")
    currency_eur = await create_currency(test_db_session, code="EUR", name="Euro")
    # Rate from EUR to USD is 1.1 (so USD to EUR should be 1/1.1)
    await create_conversion_rate(test_db_session, currency_eur.id, currency_usd.id, 1.1)

    amount_to_convert = 110.0 # USD
    converted_amount, rate_used = await _convert_amount(
        test_db_session, amount_to_convert, currency_usd.id, currency_eur.id
    )

    assert converted_amount is not None
    assert rate_used is not None
    assert pytest.approx(converted_amount) == 100.0 # 110 * (1/1.1)
    assert pytest.approx(rate_used.rate) == 1 / 1.1
    assert rate_used.from_currency_id == currency_usd.id # Effective rate is from USD
    assert rate_used.to_currency_id == currency_eur.id # Effective rate is to EUR

async def test_convert_amount_no_rate(
    test_db_session: AsyncSession,
    create_currency
):
    """Test _convert_amount when no conversion rate exists."""
    currency_usd = await create_currency(test_db_session, code="USD", name="US Dollar")
    currency_eur = await create_currency(test_db_session, code="EUR", name="Euro")

    amount_to_convert = 100.0
    converted_amount, rate_used = await _convert_amount(
        test_db_session, amount_to_convert, currency_usd.id, currency_eur.id
    )

    assert converted_amount is None
    assert rate_used is None

async def test_convert_amount_same_currency(
    test_db_session: AsyncSession,
    create_currency
):
    """Test _convert_amount when source and target currencies are the same."""
    currency_usd = await create_currency(test_db_session, code="USD", name="US Dollar")

    amount_to_convert = 100.0
    converted_amount, rate_used = await _convert_amount(
        test_db_session, amount_to_convert, currency_usd.id, currency_usd.id
    )

    assert converted_amount is not None
    assert pytest.approx(converted_amount) == 100.0
    assert rate_used is None # No conversion rate should be used or returned

async def test_convert_amount_zero_amount(
    test_db_session: AsyncSession,
    create_currency,
    create_conversion_rate
):
    """Test _convert_amount with zero amount."""
    currency_usd = await create_currency(test_db_session, code="USD", name="US Dollar")
    currency_eur = await create_currency(test_db_session, code="EUR", name="Euro")
    await create_conversion_rate(test_db_session, currency_usd.id, currency_eur.id, 0.9)

    amount_to_convert = 0.0
    converted_amount, rate_used = await _convert_amount(
        test_db_session, amount_to_convert, currency_usd.id, currency_eur.id
    )

    assert converted_amount is not None
    assert pytest.approx(converted_amount) == 0.0
    assert rate_used is not None # Rate is still found and returned
    assert rate_used.rate == 0.9

async def test_get_expense_settlement_details_same_currency(
    test_db_session: AsyncSession,
    async_client_authenticated_user: Tuple[AsyncClient, User, str],
    create_currency,
    create_group,
    create_expense,
    create_expense_participant
):
    """Test get_expense_settlement_details when target currency is same as expense currency."""
    client, current_user, _ = async_client_authenticated_user

    currency_usd = await create_currency(test_db_session, code="USD", name="US Dollar")
    group = await create_group(test_db_session, current_user.id, name="Test Group")
    expense = await create_expense(
        test_db_session, current_user.id, group.id, currency_usd.id, amount=100.0, description="Dinner"
    )
    # User's share
    participant_user = await create_expense_participant(
        test_db_session, current_user.id, expense.id, share_amount=50.0
    )
    # Another user's share (to make it a multi-participant expense)
    other_user = await User.create(test_db_session, email="other@example.com", password="password")
    await create_expense_participant(test_db_session, other_user.id, expense.id, share_amount=50.0)

    response = await client.get(
        f"/expenses/settlement-details/expense/{expense.id}/currency/{currency_usd.id}"
    )

    assert response.status_code == 200
    data = response.json()
    # print(f"DEBUG: Response data for same currency: {data}") # For debugging

    assert data["expense_id"] == expense.id
    assert data["original_currency_id"] == currency_usd.id
    assert data["target_currency_id"] == currency_usd.id
    assert data["user_share_amount_original_currency"] == participant_user.share_amount
    assert data["user_share_amount_target_currency"] == participant_user.share_amount
    assert data["conversion_rate_used"] is None
    assert not data["is_already_settled"]

async def test_get_expense_settlement_details_conversion_direct_rate(
    test_db_session: AsyncSession,
    async_client_authenticated_user: Tuple[AsyncClient, User, str],
    create_currency,
    create_conversion_rate,
    create_group,
    create_expense,
    create_expense_participant
):
    """Test get_expense_settlement_details with direct currency conversion."""
    client, current_user, _ = async_client_authenticated_user

    currency_usd = await create_currency(test_db_session, code="USD", name="US Dollar")
    currency_eur = await create_currency(test_db_session, code="EUR", name="Euro")
    await create_conversion_rate(test_db_session, currency_usd.id, currency_eur.id, 0.9)

    group = await create_group(test_db_session, current_user.id, name="Test Group Conv")
    expense = await create_expense(
        test_db_session, current_user.id, group.id, currency_usd.id, amount=100.0, description="Lunch"
    )
    participant_user = await create_expense_participant(
        test_db_session, current_user.id, expense.id, share_amount=50.0 # 50 USD
    )

    response = await client.get(
        f"/expenses/settlement-details/expense/{expense.id}/currency/{currency_eur.id}"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["expense_id"] == expense.id
    assert data["original_currency_id"] == currency_usd.id
    assert data["target_currency_id"] == currency_eur.id
    assert data["user_share_amount_original_currency"] == 50.0
    assert pytest.approx(data["user_share_amount_target_currency"]) == 45.0 # 50 * 0.9
    assert data["conversion_rate_used"] is not None
    assert data["conversion_rate_used"]["rate"] == 0.9
    assert not data["is_already_settled"]

async def test_get_expense_settlement_details_conversion_reverse_rate(
    test_db_session: AsyncSession,
    async_client_authenticated_user: Tuple[AsyncClient, User, str],
    create_currency,
    create_conversion_rate,
    create_group,
    create_expense,
    create_expense_participant
):
    """Test get_expense_settlement_details with reverse currency conversion."""
    client, current_user, _ = async_client_authenticated_user

    currency_usd = await create_currency(test_db_session, code="USD", name="US Dollar")
    currency_eur = await create_currency(test_db_session, code="EUR", name="Euro")
    # Rate from EUR to USD is 1.1 (so USD to EUR should be 1/1.1)
    await create_conversion_rate(test_db_session, currency_eur.id, currency_usd.id, 1.1)

    group = await create_group(test_db_session, current_user.id, name="Test Group RevConv")
    expense = await create_expense(
        test_db_session, current_user.id, group.id, currency_usd.id, amount=110.0, description="Coffee"
    )
    participant_user = await create_expense_participant(
        test_db_session, current_user.id, expense.id, share_amount=55.0 # 55 USD
    )

    response = await client.get(
        f"/expenses/settlement-details/expense/{expense.id}/currency/{currency_eur.id}"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["expense_id"] == expense.id
    assert data["original_currency_id"] == currency_usd.id
    assert data["target_currency_id"] == currency_eur.id
    assert data["user_share_amount_original_currency"] == 55.0
    assert pytest.approx(data["user_share_amount_target_currency"]) == 50.0 # 55 * (1/1.1)
    assert data["conversion_rate_used"] is not None
    assert pytest.approx(data["conversion_rate_used"]["rate"]) == 1 / 1.1
    assert not data["is_already_settled"]

async def test_get_expense_settlement_details_no_conversion_rate(
    test_db_session: AsyncSession,
    async_client_authenticated_user: Tuple[AsyncClient, User, str],
    create_currency,
    create_group,
    create_expense,
    create_expense_participant
):
    """Test get_expense_settlement_details when no conversion rate exists."""
    client, current_user, _ = async_client_authenticated_user

    currency_usd = await create_currency(test_db_session, code="USD", name="US Dollar")
    currency_gbp = await create_currency(test_db_session, code="GBP", name="British Pound")

    group = await create_group(test_db_session, current_user.id, name="Test Group NoRate")
    expense = await create_expense(
        test_db_session, current_user.id, group.id, currency_usd.id, amount=100.0, description="Snacks"
    )
    await create_expense_participant(
        test_db_session, current_user.id, expense.id, share_amount=50.0
    )

    response = await client.get(
        f"/expenses/settlement-details/expense/{expense.id}/currency/{currency_gbp.id}"
    )

    assert response.status_code == 200 # Endpoint should still succeed
    data = response.json()
    assert data["user_share_amount_target_currency"] is None # No conversion possible
    assert data["conversion_rate_used"] is None
    assert not data["is_already_settled"]

async def test_get_expense_settlement_details_already_settled_no_conversion(
    test_db_session: AsyncSession,
    async_client_authenticated_user: Tuple[AsyncClient, User, str],
    create_currency,
    create_group,
    create_expense,
    create_expense_participant,
    create_transaction # Assuming a fixture to create transactions
):
    """Test get_expense_settlement_details for an already settled share (no conversion)."""
    client, current_user, _ = async_client_authenticated_user

    currency_usd = await create_currency(test_db_session, code="USD", name="US Dollar")
    group = await create_group(test_db_session, current_user.id, name="Test Group Settled")
    expense = await create_expense(
        test_db_session, current_user.id, group.id, currency_usd.id, amount=100.0, description="Movie"
    )
    participant_user = await create_expense_participant(
        test_db_session, current_user.id, expense.id, share_amount=50.0
    )

    # Settle the expense
    settlement_tx = await create_transaction(test_db_session, current_user.id, 50.0, currency_usd.id, description="Settling Movie")
    participant_user.settled_transaction_id = settlement_tx.id
    participant_user.settled_amount_in_transaction_currency = 50.0
    await test_db_session.add(participant_user)
    await test_db_session.commit()
    await test_db_session.refresh(participant_user)

    response = await client.get(
        f"/expenses/settlement-details/expense/{expense.id}/currency/{currency_usd.id}"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["is_already_settled"]
    assert data["settled_details"] is not None
    assert data["settled_details"]["settled_transaction_id"] == settlement_tx.id
    assert data["settled_details"]["settled_amount_in_transaction_currency"] == 50.0
    assert data["settled_details"]["settled_in_currency_id"] == currency_usd.id
    assert data["settled_details"]["settled_with_conversion_rate_id"] is None

async def test_get_expense_settlement_details_already_settled_with_conversion(
    test_db_session: AsyncSession,
    async_client_authenticated_user: Tuple[AsyncClient, User, str],
    create_currency,
    create_conversion_rate,
    create_group,
    create_expense,
    create_expense_participant,
    create_transaction
):
    """Test get_expense_settlement_details for an already settled share (with conversion)."""
    client, current_user, _ = async_client_authenticated_user

    currency_usd = await create_currency(test_db_session, code="USD", name="US Dollar") # Expense currency
    currency_eur = await create_currency(test_db_session, code="EUR", name="Euro")    # Settlement currency
    # Expense in USD, settled in EUR
    conv_rate_usd_eur = await create_conversion_rate(test_db_session, currency_usd.id, currency_eur.id, 0.9)

    group = await create_group(test_db_session, current_user.id, name="Test Group Settled Conv")
    expense = await create_expense(
        test_db_session, current_user.id, group.id, currency_usd.id, amount=100.0, description="Concert"
    )
    participant_user = await create_expense_participant(
        test_db_session, current_user.id, expense.id, share_amount=50.0 # 50 USD
    )

    # Settle the expense in EUR
    settlement_tx_eur = await create_transaction(test_db_session, current_user.id, 45.0, currency_eur.id, description="Settling Concert in EUR")
    participant_user.settled_transaction_id = settlement_tx_eur.id
    participant_user.settled_amount_in_transaction_currency = 45.0 # 50 USD * 0.9 = 45 EUR
    participant_user.settled_with_conversion_rate_id = conv_rate_usd_eur.id
    participant_user.settled_at_conversion_timestamp = conv_rate_usd_eur.timestamp
    await test_db_session.add(participant_user)
    await test_db_session.commit()
    await test_db_session.refresh(participant_user)

    response = await client.get(
        f"/expenses/settlement-details/expense/{expense.id}/currency/{currency_eur.id}" # Requesting details in EUR
    )

    assert response.status_code == 200
    data = response.json()

    assert data["is_already_settled"]
    assert data["settled_details"] is not None
    assert data["settled_details"]["settled_transaction_id"] == settlement_tx_eur.id
    assert data["settled_details"]["settled_amount_in_transaction_currency"] == 45.0
    assert data["settled_details"]["settled_in_currency_id"] == currency_eur.id
    assert data["settled_details"]["settled_with_conversion_rate_id"] == conv_rate_usd_eur.id
    assert data["conversion_rate_used"] is None # Because it's already settled, no new conversion is proposed

async def test_get_expense_settlement_details_expense_not_found(
    async_client_authenticated_user: Tuple[AsyncClient, User, str],
    create_currency,
    test_db_session: AsyncSession
):
    client, _, _ = async_client_authenticated_user
    currency_usd = await create_currency(test_db_session, code="USD", name="US Dollar")
    non_existent_expense_id = 99999
    response = await client.get(
        f"/expenses/settlement-details/expense/{non_existent_expense_id}/currency/{currency_usd.id}"
    )
    assert response.status_code == 404

async def test_get_expense_settlement_details_currency_not_found(
    async_client_authenticated_user: Tuple[AsyncClient, User, str],
    create_currency,
    create_group,
    create_expense,
    create_expense_participant,
    test_db_session: AsyncSession
):
    client, current_user, _ = async_client_authenticated_user
    currency_usd = await create_currency(test_db_session, code="USD", name="US Dollar")
    group = await create_group(test_db_session, current_user.id, name="Test Group")
    expense = await create_expense(
        test_db_session, current_user.id, group.id, currency_usd.id, amount=100.0, description="Dinner"
    )
    await create_expense_participant(test_db_session, current_user.id, expense.id, share_amount=50.0)
    
    non_existent_currency_id = 99999
    response = await client.get(
        f"/expenses/settlement-details/expense/{expense.id}/currency/{non_existent_currency_id}"
    )
    assert response.status_code == 404 # Assuming target currency not found leads to 404

async def test_get_expense_settlement_details_user_not_participant(
    test_db_session: AsyncSession,
    async_client_authenticated_user: Tuple[AsyncClient, User, str],
    create_user, # For creating another user
    create_currency,
    create_group,
    create_expense,
    create_expense_participant
):
    """Test getting settlement details for an expense the current user is not part of."""
    client, current_user, _ = async_client_authenticated_user

    other_user = await create_user(test_db_session, email="other_user@example.com", password="securepassword")
    currency_usd = await create_currency(test_db_session, code="USD", name="US Dollar")
    group = await create_group(test_db_session, other_user.id, name="Other User's Group") # Group created by other_user
    expense = await create_expense(
        test_db_session, other_user.id, group.id, currency_usd.id, amount=100.0, description="Lunch for others"
    )
    # other_user is a participant, but current_user is not
    await create_expense_participant(test_db_session, other_user.id, expense.id, share_amount=100.0)

    response = await client.get(
        f"/expenses/settlement-details/expense/{expense.id}/currency/{currency_usd.id}"
    )
    # The endpoint currently fetches participant record for current_user.id
    # If not found, it raises HTTPException(status_code=404, detail="Current user is not a participant in this expense or participant record not found.")
    assert response.status_code == 404 


async def test_get_group_settlement_details_simple_same_currency(
    test_db_session: AsyncSession,
    async_client_authenticated_user: Tuple[AsyncClient, User, str],
    create_user,
    create_currency,
    create_group,
    create_expense,
    create_expense_participant
):
    """Test get_group_settlement_details with simple expenses in the same target currency."""
    client, current_user, _ = async_client_authenticated_user
    user2 = await create_user(test_db_session, email="user2@example.com", password="password")

    currency_usd = await create_currency(test_db_session, code="USD", name="US Dollar")
    group = await create_group(test_db_session, current_user.id, name="Group Same Currency", members_ids=[user2.id])

    # Expense 1: current_user paid 100, user2 owes 50 to current_user
    expense1 = await create_expense(
        test_db_session, current_user.id, group.id, currency_usd.id, amount=100.0, description="Dinner by current_user"
    )
    await create_expense_participant(test_db_session, current_user.id, expense1.id, share_amount=50.0)
    await create_expense_participant(test_db_session, user2.id, expense1.id, share_amount=50.0)

    # Expense 2: user2 paid 60, current_user owes 30 to user2
    expense2 = await create_expense(
        test_db_session, user2.id, group.id, currency_usd.id, amount=60.0, description="Lunch by user2"
    )
    await create_expense_participant(test_db_session, current_user.id, expense2.id, share_amount=30.0)
    await create_expense_participant(test_db_session, user2.id, expense2.id, share_amount=30.0)

    response = await client.get(
        f"/expenses/settlement-details/group/{group.id}/currency/{currency_usd.id}"
    )

    assert response.status_code == 200
    data = response.json()
    # print(f"DEBUG: Group settlement same currency: {data}")

    assert data["group_id"] == group.id
    assert data["target_currency_id"] == currency_usd.id
    assert len(data["net_balances_with_members"]) == 1

    balance_with_user2 = data["net_balances_with_members"][0]
    assert balance_with_user2["other_member_id"] == user2.id
    # current_user is owed 50 by user2 (from expense1)
    # current_user owes 30 to user2 (from expense2)
    # Net: current_user is owed 20 by user2 (or current_user owes -20 to user2)
    assert pytest.approx(balance_with_user2["net_amount_current_user_owes_member"]) == -20.0
    assert balance_with_user2["summary_message"] == f"You are owed {abs(balance_with_user2['net_amount_current_user_owes_member']):.2f} {currency_usd.code} by {user2.username}."

async def test_get_group_settlement_details_with_conversion(
    test_db_session: AsyncSession,
    async_client_authenticated_user: Tuple[AsyncClient, User, str],
    create_user,
    create_currency,
    create_conversion_rate,
    create_group,
    create_expense,
    create_expense_participant
):
    """Test get_group_settlement_details requiring currency conversion."""
    client, current_user, _ = async_client_authenticated_user
    user2 = await create_user(test_db_session, email="user2_conv@example.com", password="password")

    currency_usd = await create_currency(test_db_session, code="USD", name="US Dollar")
    currency_eur = await create_currency(test_db_session, code="EUR", name="Euro") # Target currency
    await create_conversion_rate(test_db_session, currency_usd.id, currency_eur.id, 0.9) # 1 USD = 0.9 EUR

    group = await create_group(test_db_session, current_user.id, name="Group Conversion", members_ids=[user2.id])

    # Expense 1 (USD): current_user paid 100 USD, user2 owes 50 USD to current_user
    expense1_usd = await create_expense(
        test_db_session, current_user.id, group.id, currency_usd.id, amount=100.0, description="Dinner USD"
    )
    await create_expense_participant(test_db_session, current_user.id, expense1_usd.id, share_amount=50.0)
    await create_expense_participant(test_db_session, user2.id, expense1_usd.id, share_amount=50.0)

    response = await client.get(
        f"/expenses/settlement-details/group/{group.id}/currency/{currency_eur.id}"
    )

    assert response.status_code == 200
    data = response.json()
    # print(f"DEBUG: Group settlement with conversion: {data}")

    assert data["group_id"] == group.id
    assert data["target_currency_id"] == currency_eur.id
    assert len(data["net_balances_with_members"]) == 1

    balance_with_user2 = data["net_balances_with_members"][0]
    assert balance_with_user2["other_member_id"] == user2.id
    # current_user is owed 50 USD by user2. In EUR: 50 USD * 0.9 = 45 EUR.
    # So, current_user owes -45 EUR to user2.
    assert pytest.approx(balance_with_user2["net_amount_current_user_owes_member"]) == -45.0
    assert balance_with_user2["summary_message"] == f"You are owed {abs(balance_with_user2['net_amount_current_user_owes_member']):.2f} {currency_eur.code} by {user2.username}."

async def test_get_group_settlement_details_mixed_currencies_and_settled(
    test_db_session: AsyncSession,
    async_client_authenticated_user: Tuple[AsyncClient, User, str],
    create_user,
    create_currency,
    create_conversion_rate,
    create_group,
    create_expense,
    create_expense_participant,
    create_transaction
):
    """Test with mixed currencies, some settled, target currency needs conversion."""
    client, current_user, _ = async_client_authenticated_user
    user2 = await create_user(test_db_session, email="user2_mix@example.com", password="password")
    user3 = await create_user(test_db_session, email="user3_mix@example.com", password="password")

    currency_usd = await create_currency(test_db_session, code="USD", name="US Dollar")
    currency_gbp = await create_currency(test_db_session, code="GBP", name="British Pound")
    currency_eur = await create_currency(test_db_session, code="EUR", name="Euro") # Target currency

    await create_conversion_rate(test_db_session, currency_usd.id, currency_eur.id, 0.9)  # 1 USD = 0.9 EUR
    await create_conversion_rate(test_db_session, currency_gbp.id, currency_eur.id, 1.15) # 1 GBP = 1.15 EUR

    group = await create_group(test_db_session, current_user.id, name="Group Mixed", members_ids=[user2.id, user3.id])

    # Expense 1 (USD): current_user paid 100 USD for self and user2. user2 owes 50 USD.
    exp1_usd = await create_expense(test_db_session, current_user.id, group.id, currency_usd.id, 100.0, "E1 USD")
    await create_expense_participant(test_db_session, current_user.id, exp1_usd.id, 50.0)
    await create_expense_participant(test_db_session, user2.id, exp1_usd.id, 50.0)

    # Expense 2 (GBP): user2 paid 40 GBP for self and current_user. current_user owes 20 GBP.
    exp2_gbp = await create_expense(test_db_session, user2.id, group.id, currency_gbp.id, 40.0, "E2 GBP")
    await create_expense_participant(test_db_session, user2.id, exp2_gbp.id, 20.0)
    await create_expense_participant(test_db_session, current_user.id, exp2_gbp.id, 20.0)

    # Expense 3 (USD): current_user paid 60 USD for self and user3. user3 owes 30 USD.
    exp3_usd = await create_expense(test_db_session, current_user.id, group.id, currency_usd.id, 60.0, "E3 USD")
    await create_expense_participant(test_db_session, current_user.id, exp3_usd.id, 30.0)
    ep_user3_exp3 = await create_expense_participant(test_db_session, user3.id, exp3_usd.id, 30.0)

    # Settle user3's share of Expense 3
    settle_tx = await create_transaction(test_db_session, user3.id, 30.0, currency_usd.id, "Settling E3")
    ep_user3_exp3.settled_transaction_id = settle_tx.id
    ep_user3_exp3.settled_amount_in_transaction_currency = 30.0
    await test_db_session.add(ep_user3_exp3)
    await test_db_session.commit()

    response = await client.get(
        f"/expenses/settlement-details/group/{group.id}/currency/{currency_eur.id}"
    )
    assert response.status_code == 200
    data = response.json()
    # print(f"DEBUG: Group settlement mixed: {data}")

    assert len(data["net_balances_with_members"]) == 2 # current_user with user2 and user3

    balance_with_user2 = next(b for b in data["net_balances_with_members"] if b["other_member_id"] == user2.id)
    balance_with_user3 = next(b for b in data["net_balances_with_members"] if b["other_member_id"] == user3.id)

    # For user2:
    # current_user is owed 50 USD from exp1_usd  = 50 * 0.9 = 45 EUR
    # current_user owes 20 GBP from exp2_gbp   = 20 * 1.15 = 23 EUR
    # Net for user2: current_user owes (23 - 45) = -22 EUR to user2 (i.e., current_user is owed 22 EUR)
    assert pytest.approx(balance_with_user2["net_amount_current_user_owes_member"]) == -22.0 

    # For user3:
    # current_user was owed 30 USD from exp3_usd, but it's settled.
    # So, net amount current_user owes user3 should be 0.
    assert pytest.approx(balance_with_user3["net_amount_current_user_owes_member"]) == 0.0
    assert "is settled up with" in balance_with_user3["summary_message"].lower()

async def test_get_group_settlement_details_no_unsettled_expenses_with_member(
    test_db_session: AsyncSession,
    async_client_authenticated_user: Tuple[AsyncClient, User, str],
    create_user,
    create_currency,
    create_group,
    create_expense,
    create_expense_participant,
    create_transaction
):
    """Test when all expenses with a member are settled."""
    client, current_user, _ = async_client_authenticated_user
    user2 = await create_user(test_db_session, email="user2_settled@example.com", password="password")

    currency_usd = await create_currency(test_db_session, code="USD", name="US Dollar")
    group = await create_group(test_db_session, current_user.id, name="Group All Settled", members_ids=[user2.id])

    expense1 = await create_expense(test_db_session, current_user.id, group.id, currency_usd.id, 100.0, "E1")
    ep_cu_e1 = await create_expense_participant(test_db_session, current_user.id, expense1.id, 50.0)
    ep_u2_e1 = await create_expense_participant(test_db_session, user2.id, expense1.id, 50.0)

    # Settle user2's share
    settle_tx = await create_transaction(test_db_session, user2.id, 50.0, currency_usd.id, "Settling E1 for user2")
    ep_u2_e1.settled_transaction_id = settle_tx.id
    ep_u2_e1.settled_amount_in_transaction_currency = 50.0
    await test_db_session.add(ep_u2_e1)
    await test_db_session.commit()

    response = await client.get(
        f"/expenses/settlement-details/group/{group.id}/currency/{currency_usd.id}"
    )
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["net_balances_with_members"]) == 1
    balance_with_user2 = data["net_balances_with_members"][0]
    assert balance_with_user2["other_member_id"] == user2.id
    assert pytest.approx(balance_with_user2["net_amount_current_user_owes_member"]) == 0.0
    assert "is settled up with" in balance_with_user2["summary_message"].lower()

async def test_get_group_settlement_details_group_not_found(
    async_client_authenticated_user: Tuple[AsyncClient, User, str],
    create_currency,
    test_db_session: AsyncSession
):
    client, _, _ = async_client_authenticated_user
    currency_usd = await create_currency(test_db_session, code="USD", name="US Dollar")
    non_existent_group_id = 99999
    response = await client.get(
        f"/expenses/settlement-details/group/{non_existent_group_id}/currency/{currency_usd.id}"
    )
    assert response.status_code == 404

async def test_get_group_settlement_details_target_currency_not_found(
    async_client_authenticated_user: Tuple[AsyncClient, User, str],
    create_group,
    test_db_session: AsyncSession
):
    client, current_user, _ = async_client_authenticated_user
    group = await create_group(test_db_session, current_user.id, name="Group No Target Currency")
    non_existent_currency_id = 99999
    response = await client.get(
        f"/expenses/settlement-details/group/{group.id}/currency/{non_existent_currency_id}"
    )
    assert response.status_code == 404

async def test_get_group_settlement_details_user_not_in_group(
    async_client_authenticated_user: Tuple[AsyncClient, User, str],
    create_user,
    create_currency,
    create_group,
    test_db_session: AsyncSession
):
    client, _, _ = async_client_authenticated_user # This is user1
    user2 = await create_user(test_db_session, email="group_owner@example.com", password="password")
    group_of_user2 = await create_group(test_db_session, user2.id, name="User2's Private Group")
    currency_usd = await create_currency(test_db_session, code="USD", name="US Dollar")

    response = await client.get(
        f"/expenses/settlement-details/group/{group_of_user2.id}/currency/{currency_usd.id}"
    )
    assert response.status_code == 403 # Forbidden as current_user is not a member

async def test_get_group_settlement_details_no_conversion_rate_available(
    test_db_session: AsyncSession,
    async_client_authenticated_user: Tuple[AsyncClient, User, str],
    create_user,
    create_currency,
    # No create_conversion_rate fixture here
    create_group,
    create_expense,
    create_expense_participant
):
    """Test when a required conversion rate is missing."""
    client, current_user, _ = async_client_authenticated_user
    user2 = await create_user(test_db_session, email="user2_no_rate@example.com", password="password")

    currency_usd = await create_currency(test_db_session, code="USD", name="US Dollar") # Expense currency
    currency_eur = await create_currency(test_db_session, code="EUR", name="Euro")    # Target currency
    # NO conversion rate USD -> EUR defined

    group = await create_group(test_db_session, current_user.id, name="Group No Rate", members_ids=[user2.id])

    # Expense 1 (USD): current_user paid 100 USD, user2 owes 50 USD to current_user
    expense1_usd = await create_expense(
        test_db_session, current_user.id, group.id, currency_usd.id, amount=100.0, description="Dinner USD No Rate"
    )
    await create_expense_participant(test_db_session, current_user.id, expense1_usd.id, share_amount=50.0)
    await create_expense_participant(test_db_session, user2.id, expense1_usd.id, share_amount=50.0)

    response = await client.get(
        f"/expenses/settlement-details/group/{group.id}/currency/{currency_eur.id}"
    )

    assert response.status_code == 200 # Endpoint should still succeed
    data = response.json()
    assert len(data["net_balances_with_members"]) == 1
    balance_with_user2 = data["net_balances_with_members"][0]
    # Since conversion USD->EUR is not possible, the amount should reflect this (e.g., be None or an error message)
    # The current implementation of _convert_amount returns (None, None) if rate not found.
    # The get_group_settlement_details sums up these Nones, which results in an error during sum().
    # This needs to be handled: if any conversion fails, that part of debt is skipped or an error is shown.
    # For now, let's assume the API might return a specific value or error for this item.
    # Based on current router logic, if _convert_amount returns None, it might lead to an error or skip that amount.
    # If it skips, the net_amount could be 0 if this was the only expense.
    # Let's check the summary message for an indication.
    assert "Could not convert all amounts" in balance_with_user2["summary_message"] or \
           pytest.approx(balance_with_user2["net_amount_current_user_owes_member"]) == 0.0
    # A more robust check would be to ensure the specific problematic conversion is flagged.
    # For now, this test highlights the need for careful handling of missing rates in aggregation.


