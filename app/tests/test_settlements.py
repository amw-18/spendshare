import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from src.models.models import User, Currency, Expense, ExpenseParticipant, Transaction
from src.services.expense_service import update_expense_settlement_status
from src.main import app # For client testing
from typing import AsyncGenerator, Dict, Any

# Fixtures for users, currency, expenses will be needed.
# These can be adapted from test_expenses.py or made more generic.

@pytest.mark.asyncio
async def test_update_expense_settlement_status_all_participants_settled(
    session: AsyncSession,
    test_user: User,
    test_user2: User,
    test_currency: Currency
):
    """
    Test update_expense_settlement_status when all participants are settled.
    """
    # 1. Create an Expense paid by test_user
    expense = Expense(
        description="Test Expense for Settlement Status",
        amount=100.0,
        paid_by_user_id=test_user.id,
        currency_id=test_currency.id,
    )
    session.add(expense)
    await session.flush()

    # 2. Create two participants, one is test_user2, other could be test_user himself (or a third user)
    ep1 = ExpenseParticipant(
        expense_id=expense.id, user_id=test_user2.id, share_amount=50.0
    )
    ep2 = ExpenseParticipant( # Payer also participates to make it simple
        expense_id=expense.id, user_id=test_user.id, share_amount=50.0
    )
    session.add_all([ep1, ep2])
    await session.commit() # Commit expense and participants first

    # 3. Create a transaction to "settle" these
    transaction = Transaction(
        amount=100.0, currency_id=test_currency.id, created_by_user_id=test_user.id
    )
    session.add(transaction)
    await session.commit() # Commit transaction

    # 4. "Settle" the participants
    ep1.settled_transaction_id = transaction.id
    ep1.settled_amount_in_transaction_currency = 50.0
    ep2.settled_transaction_id = transaction.id
    ep2.settled_amount_in_transaction_currency = 50.0
    session.add_all([ep1, ep2])
    await session.commit() # Commit settlement details

    await session.refresh(expense)
    assert not expense.is_settled # Initially should be false

    # 5. Call the service function
    await update_expense_settlement_status(expense.id, session)
    await session.commit() # Commit status update
    await session.refresh(expense)

    assert expense.is_settled


@pytest.mark.asyncio
async def test_update_expense_settlement_status_one_participant_not_settled(
    session: AsyncSession, test_user: User, test_user2: User, test_currency: Currency
):
    """
    Test update_expense_settlement_status when one participant is not settled.
    """
    expense = Expense(
        description="Test Expense Partial Settlement",
        amount=100.0,
        paid_by_user_id=test_user.id,
        currency_id=test_currency.id,
    )
    session.add(expense)
    await session.flush()

    ep1 = ExpenseParticipant(
        expense_id=expense.id, user_id=test_user2.id, share_amount=50.0
    )
    ep2 = ExpenseParticipant(
        expense_id=expense.id, user_id=test_user.id, share_amount=50.0
    )
    session.add_all([ep1, ep2])
    await session.commit()

    transaction = Transaction(
        amount=50.0, currency_id=test_currency.id, created_by_user_id=test_user.id
    )
    session.add(transaction)
    await session.commit()

    # Settle only ep1
    ep1.settled_transaction_id = transaction.id
    ep1.settled_amount_in_transaction_currency = 50.0
    session.add(ep1)
    await session.commit()

    await session.refresh(expense)
    assert not expense.is_settled

    await update_expense_settlement_status(expense.id, session)
    await session.commit()
    await session.refresh(expense)

    assert not expense.is_settled


@pytest.mark.asyncio
async def test_update_expense_settlement_status_participant_partially_settled(
    session: AsyncSession, test_user: User, test_user2: User, test_currency: Currency
):
    """
    Test update_expense_settlement_status when a participant's share is only partially settled.
    """
    expense = Expense(
        description="Test Expense Partial Share Settlement",
        amount=100.0,
        paid_by_user_id=test_user.id,
        currency_id=test_currency.id,
    )
    session.add(expense)
    await session.flush()

    ep1 = ExpenseParticipant(
        expense_id=expense.id, user_id=test_user2.id, share_amount=50.0
    )
    ep2 = ExpenseParticipant(
        expense_id=expense.id, user_id=test_user.id, share_amount=50.0
    )
    session.add_all([ep1, ep2])
    await session.commit()

    transaction = Transaction(
        amount=70.0, currency_id=test_currency.id, created_by_user_id=test_user.id
    ) # Covers ep2 fully, ep1 partially
    session.add(transaction)
    await session.commit()

    # Settle ep2 fully
    ep2.settled_transaction_id = transaction.id
    ep2.settled_amount_in_transaction_currency = 50.0
    session.add(ep2)

    # Partially settle ep1
    ep1.settled_transaction_id = transaction.id # Same transaction, but not enough amount
    ep1.settled_amount_in_transaction_currency = 20.0 # Share is 50, settled 20
    session.add(ep1)
    await session.commit()

    await session.refresh(expense)
    assert not expense.is_settled

    await update_expense_settlement_status(expense.id, session)
    await session.commit()
    await session.refresh(expense)

    assert not expense.is_settled


@pytest.mark.asyncio
async def test_update_expense_settlement_status_no_participants(
    session: AsyncSession, test_user: User, test_currency: Currency
):
    """
    Test update_expense_settlement_status for an expense with no participants.
    Amount > 0: Should not be settled.
    Amount = 0: Should be settled.
    """
    # Case 1: Amount > 0, no participants (though create logic usually prevents this)
    expense_with_amount = Expense(
        description="Expense No Participants Amount",
        amount=100.0,
        paid_by_user_id=test_user.id,
        currency_id=test_currency.id,
    )
    session.add(expense_with_amount)
    await session.commit()
    await session.refresh(expense_with_amount)

    assert not expense_with_amount.is_settled
    await update_expense_settlement_status(expense_with_amount.id, session)
    await session.commit()
    await session.refresh(expense_with_amount)
    # This behavior might be debatable: an expense with amount > 0 and no listed participants
    # implies the payer bears the full cost. Is it "settled" in terms of reimbursement? No.
    # The service function returns False if no participants and amount > 0.
    assert not expense_with_amount.is_settled

    # Case 2: Amount = 0, no participants
    expense_zero_amount = Expense(
        description="Expense No Participants Zero Amount",
        amount=0.0,
        paid_by_user_id=test_user.id,
        currency_id=test_currency.id,
    )
    session.add(expense_zero_amount)
    await session.commit()
    await session.refresh(expense_zero_amount)

    assert not expense_zero_amount.is_settled # Initial state
    await update_expense_settlement_status(expense_zero_amount.id, session)
    await session.commit()
    await session.refresh(expense_zero_amount)
    assert expense_zero_amount.is_settled


@pytest.mark.asyncio
async def test_update_expense_already_settled_no_change(
    session: AsyncSession, test_user: User, test_currency: Currency
):
    """
    Test that calling update_expense_settlement_status on an already settled expense
    where all participants are still settled doesn't change its state.
    """
    expense = Expense(
        description="Already Settled Expense",
        amount=50.0,
        paid_by_user_id=test_user.id,
        currency_id=test_currency.id,
        is_settled=True # Manually set to true for test setup
    )
    session.add(expense)
    await session.flush()

    ep = ExpenseParticipant(expense_id=expense.id, user_id=test_user.id, share_amount=50.0)
    session.add(ep)
    await session.commit()

    transaction = Transaction(amount=50.0, currency_id=test_currency.id, created_by_user_id=test_user.id)
    session.add(transaction)
    await session.commit()

    ep.settled_transaction_id = transaction.id
    ep.settled_amount_in_transaction_currency = 50.0
    session.add(ep)
    await session.commit()

    await session.refresh(expense)
    assert expense.is_settled

    await update_expense_settlement_status(expense.id, session)
    await session.commit() # service function calls flush, router would call commit
    await session.refresh(expense)

    assert expense.is_settled # Should remain true


@pytest.mark.asyncio
async def test_update_expense_becomes_unsettled(
    session: AsyncSession, test_user: User, test_user2: User, test_currency: Currency
):
    """
    Test that if an expense was marked settled, but a participant becomes unsettled,
    the expense status is updated to not settled.
    """
    expense = Expense(
        description="Expense Becomes Unsettled",
        amount=100.0,
        paid_by_user_id=test_user.id,
        currency_id=test_currency.id,
        is_settled=True # Initially (perhaps erroneously) marked as settled
    )
    session.add(expense)
    await session.flush()

    ep1 = ExpenseParticipant(expense_id=expense.id, user_id=test_user2.id, share_amount=50.0)
    ep2 = ExpenseParticipant(expense_id=expense.id, user_id=test_user.id, share_amount=50.0)
    session.add_all([ep1, ep2])
    await session.commit()

    transaction = Transaction(amount=50.0, currency_id=test_currency.id, created_by_user_id=test_user.id)
    session.add(transaction)
    await session.commit()

    # ep1 is settled
    ep1.settled_transaction_id = transaction.id
    ep1.settled_amount_in_transaction_currency = 50.0
    session.add(ep1)
    # ep2 is NOT settled
    await session.commit()

    await session.refresh(expense)
    assert expense.is_settled # Still true from initial setup

    await update_expense_settlement_status(expense.id, session)
    await session.commit()
    await session.refresh(expense)

    assert not expense.is_settled # Should now be false


# --- Tests for the /settlements/record-direct-payment endpoint ---

@pytest.mark.asyncio
async def test_record_direct_payment_success(
    async_client: AsyncClient,
    session: AsyncSession,
    test_user: User, # Debtor
    test_user2: User, # Creditor (original payer of expense)
    test_currency: Currency,
    test_user_auth_headers: Dict[str, str], # Auth for test_user (debtor)
    test_user2_auth_headers: Dict[str, str] # Auth for test_user2 (creditor)
):
    """
    Test successful recording of a direct payment.
    test_user (debtor) pays test_user2 (creditor) for an expense.
    Payment recorded by test_user.
    """
    # 1. Create an expense paid by test_user2, with test_user as a participant
    expense = Expense(
        description="Expense for Direct Payment Test",
        amount=75.0,
        paid_by_user_id=test_user2.id, # test_user2 is the creditor
        currency_id=test_currency.id,
    )
    session.add(expense)
    await session.flush()

    ep = ExpenseParticipant(
        expense_id=expense.id,
        user_id=test_user.id, # test_user is the debtor
        share_amount=75.0
    )
    session.add(ep)
    await session.commit()
    await session.refresh(expense)
    await session.refresh(ep)

    assert not expense.is_settled
    assert ep.settled_transaction_id is None

    # 2. Prepare request for record-direct-payment
    payment_data = {
        "debtor_user_id": test_user.id,
        "creditor_user_id": test_user2.id,
        "amount_paid": 75.0,
        "currency_paid_id": test_currency.id,
        "expense_participant_ids_to_settle": [ep.id]
    }

    # test_user (debtor) records the payment
    response = await async_client.post(
        "/api/v1/settlements/record-direct-payment",
        json=payment_data,
        headers=test_user_auth_headers # Authenticated as debtor
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "Completed"
    assert len(response_data["updated_expense_participations"]) == 1
    settlement_result = response_data["updated_expense_participations"][0]
    assert settlement_result["expense_participant_id"] == ep.id
    assert settlement_result["settled_amount_in_transaction_currency"] == 75.0
    assert settlement_result["settled_currency_id"] == test_currency.id
    new_transaction_id = settlement_result["settled_transaction_id"]

    # 3. Verify database state
    await session.refresh(ep)
    await session.refresh(expense)

    assert ep.settled_transaction_id == new_transaction_id
    assert ep.settled_amount_in_transaction_currency == 75.0
    assert expense.is_settled # Expense should now be settled

    # Verify the created transaction
    created_transaction = await session.get(Transaction, new_transaction_id)
    assert created_transaction is not None
    assert created_transaction.amount == 75.0
    assert created_transaction.currency_id == test_currency.id
    assert created_transaction.created_by_user_id == test_user.id # Recorded by test_user


@pytest.mark.asyncio
async def test_record_direct_payment_creditor_records(
    async_client: AsyncClient,
    session: AsyncSession,
    test_user: User, # Debtor
    test_user2: User, # Creditor
    test_currency: Currency,
    test_user2_auth_headers: Dict[str, str] # Auth for test_user2 (creditor)
):
    """
    Test successful recording of a direct payment, recorded by the creditor.
    """
    expense = Expense(
        description="Expense Creditor Records Payment",
        amount=30.0,
        paid_by_user_id=test_user2.id,
        currency_id=test_currency.id,
    )
    session.add(expense)
    await session.flush()
    ep = ExpenseParticipant(expense_id=expense.id, user_id=test_user.id, share_amount=30.0)
    session.add(ep)
    await session.commit()

    payment_data = {
        "debtor_user_id": test_user.id,
        "creditor_user_id": test_user2.id,
        "amount_paid": 30.0,
        "currency_paid_id": test_currency.id,
        "expense_participant_ids_to_settle": [ep.id]
    }

    # test_user2 (creditor) records the payment
    response = await async_client.post(
        "/api/v1/settlements/record-direct-payment",
        json=payment_data,
        headers=test_user2_auth_headers
    )
    assert response.status_code == 200
    await session.refresh(ep)
    await session.refresh(expense)
    assert ep.settled_transaction_id is not None
    assert expense.is_settled

    # Verify transaction creator
    settlement_result = response.json()["updated_expense_participations"][0]
    created_transaction = await session.get(Transaction, settlement_result["settled_transaction_id"])
    assert created_transaction.created_by_user_id == test_user2.id


@pytest.mark.asyncio
async def test_record_direct_payment_unauthorized_recorder(
    async_client: AsyncClient,
    session: AsyncSession,
    test_user: User, # Debtor
    test_user2: User, # Creditor
    test_user3: User, # Uninvolved user
    test_currency: Currency,
    test_user3_auth_headers: Dict[str, str] # Auth for test_user3
):
    """
    Test recording payment fails if recorder is neither debtor nor creditor.
    """
    expense = Expense(description="E", amount=10.0, paid_by_user_id=test_user2.id, currency_id=test_currency.id)
    session.add(expense)
    await session.flush()
    ep = ExpenseParticipant(expense_id=expense.id, user_id=test_user.id, share_amount=10.0)
    session.add(ep)
    await session.commit()

    payment_data = {
        "debtor_user_id": test_user.id,
        "creditor_user_id": test_user2.id,
        "amount_paid": 10.0,
        "currency_paid_id": test_currency.id,
        "expense_participant_ids_to_settle": [ep.id]
    }

    response = await async_client.post(
        "/api/v1/settlements/record-direct-payment",
        json=payment_data,
        headers=test_user3_auth_headers # Authenticated as uninvolved user
    )
    assert response.status_code == 403 # Forbidden


@pytest.mark.asyncio
async def test_record_direct_payment_amount_mismatch(
    async_client: AsyncClient,
    session: AsyncSession,
    test_user: User,
    test_user2: User,
    test_currency: Currency,
    test_user_auth_headers: Dict[str, str]
):
    """
    Test recording payment fails if amount_paid does not match sum of shares.
    """
    expense = Expense(description="E", amount=50.0, paid_by_user_id=test_user2.id, currency_id=test_currency.id)
    session.add(expense)
    await session.flush()
    ep = ExpenseParticipant(expense_id=expense.id, user_id=test_user.id, share_amount=50.0)
    session.add(ep)
    await session.commit()

    payment_data = {
        "debtor_user_id": test_user.id,
        "creditor_user_id": test_user2.id,
        "amount_paid": 40.0, # Mismatch with share_amount of 50.0
        "currency_paid_id": test_currency.id,
        "expense_participant_ids_to_settle": [ep.id]
    }
    response = await async_client.post("/api/v1/settlements/record-direct-payment", json=payment_data, headers=test_user_auth_headers)
    assert response.status_code == 400
    assert "does not match the total sum of shares" in response.json()["detail"]

@pytest.mark.asyncio
async def test_record_direct_payment_participant_not_debtors(
    async_client: AsyncClient,
    session: AsyncSession,
    test_user: User, # Intended Debtor
    test_user2: User, # Creditor
    test_user3: User, # Actual participant, not the debtor
    test_currency: Currency,
    test_user_auth_headers: Dict[str, str]
):
    """
    Test recording payment fails if an expense_participant_id does not belong to the debtor.
    """
    expense = Expense(description="E", amount=20.0, paid_by_user_id=test_user2.id, currency_id=test_currency.id)
    session.add(expense)
    await session.flush()
    # Participant is test_user3, but request says debtor is test_user
    ep = ExpenseParticipant(expense_id=expense.id, user_id=test_user3.id, share_amount=20.0)
    session.add(ep)
    await session.commit()

    payment_data = {
        "debtor_user_id": test_user.id, # test_user is debtor in request
        "creditor_user_id": test_user2.id,
        "amount_paid": 20.0,
        "currency_paid_id": test_currency.id,
        "expense_participant_ids_to_settle": [ep.id] # ep belongs to test_user3
    }
    response = await async_client.post("/api/v1/settlements/record-direct-payment", json=payment_data, headers=test_user_auth_headers)
    assert response.status_code == 422 # Unprocessable Entity
    assert f"does not belong to debtor user ID {test_user.id}" in response.json()["detail"]


@pytest.mark.asyncio
async def test_record_direct_payment_expense_not_creditors(
    async_client: AsyncClient,
    session: AsyncSession,
    test_user: User, # Debtor
    test_user2: User, # Intended Creditor
    test_user3: User, # Actual Payer of expense
    test_currency: Currency,
    test_user_auth_headers: Dict[str, str]
):
    """
    Test recording payment fails if an expense was not paid by the specified creditor.
    """
    # Expense paid by test_user3, but request says creditor is test_user2
    expense = Expense(description="E", amount=25.0, paid_by_user_id=test_user3.id, currency_id=test_currency.id)
    session.add(expense)
    await session.flush()
    ep = ExpenseParticipant(expense_id=expense.id, user_id=test_user.id, share_amount=25.0)
    session.add(ep)
    await session.commit()

    payment_data = {
        "debtor_user_id": test_user.id,
        "creditor_user_id": test_user2.id, # test_user2 is creditor in request
        "amount_paid": 25.0,
        "currency_paid_id": test_currency.id,
        "expense_participant_ids_to_settle": [ep.id] # Expense was paid by test_user3
    }
    response = await async_client.post("/api/v1/settlements/record-direct-payment", json=payment_data, headers=test_user_auth_headers)
    assert response.status_code == 422 # Unprocessable Entity
    assert f"was not paid by creditor user ID {test_user2.id}" in response.json()["detail"]


@pytest.mark.asyncio
async def test_record_direct_payment_participant_already_settled(
    async_client: AsyncClient,
    session: AsyncSession,
    test_user: User,
    test_user2: User,
    test_currency: Currency,
    test_user_auth_headers: Dict[str, str]
):
    """
    Test recording payment fails if a participant is already settled by another transaction.
    """
    expense = Expense(description="E", amount=60.0, paid_by_user_id=test_user2.id, currency_id=test_currency.id)
    session.add(expense)
    await session.flush()
    ep = ExpenseParticipant(expense_id=expense.id, user_id=test_user.id, share_amount=60.0)
    session.add(ep)

    # Existing transaction that settles this participant
    existing_tx = Transaction(amount=60.0, currency_id=test_currency.id, created_by_user_id=test_user.id)
    session.add(existing_tx)
    await session.commit() # Get ID for existing_tx

    ep.settled_transaction_id = existing_tx.id
    ep.settled_amount_in_transaction_currency = 60.0
    await session.commit()


    payment_data = {
        "debtor_user_id": test_user.id,
        "creditor_user_id": test_user2.id,
        "amount_paid": 60.0,
        "currency_paid_id": test_currency.id,
        "expense_participant_ids_to_settle": [ep.id]
    }
    response = await async_client.post("/api/v1/settlements/record-direct-payment", json=payment_data, headers=test_user_auth_headers)
    assert response.status_code == 422
    assert "is already settled by transaction" in response.json()["detail"]

@pytest.mark.asyncio
async def test_record_direct_payment_multiple_participants(
    async_client: AsyncClient,
    session: AsyncSession,
    test_user: User, # Debtor
    test_user2: User, # Creditor
    test_currency: Currency,
    test_user_auth_headers: Dict[str, str]
):
    """
    Test recording a single payment that settles multiple participations for the same debtor to the same creditor.
    """
    # Expense 1, paid by test_user2, test_user owes 20
    expense1 = Expense(description="E1", amount=20.0, paid_by_user_id=test_user2.id, currency_id=test_currency.id)
    session.add(expense1)
    await session.flush()
    ep1 = ExpenseParticipant(expense_id=expense1.id, user_id=test_user.id, share_amount=20.0)
    session.add(ep1)

    # Expense 2, paid by test_user2, test_user owes 30
    expense2 = Expense(description="E2", amount=30.0, paid_by_user_id=test_user2.id, currency_id=test_currency.id)
    session.add(expense2)
    await session.flush()
    ep2 = ExpenseParticipant(expense_id=expense2.id, user_id=test_user.id, share_amount=30.0)
    session.add(ep2)
    await session.commit()

    await session.refresh(ep1)
    await session.refresh(ep2)
    await session.refresh(expense1)
    await session.refresh(expense2)

    payment_data = {
        "debtor_user_id": test_user.id,
        "creditor_user_id": test_user2.id,
        "amount_paid": 50.0, # 20 (for ep1) + 30 (for ep2)
        "currency_paid_id": test_currency.id,
        "expense_participant_ids_to_settle": [ep1.id, ep2.id]
    }

    response = await async_client.post("/api/v1/settlements/record-direct-payment", json=payment_data, headers=test_user_auth_headers)
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data["updated_expense_participations"]) == 2

    await session.refresh(ep1)
    await session.refresh(ep2)
    await session.refresh(expense1)
    await session.refresh(expense2)

    assert ep1.settled_transaction_id is not None
    assert ep1.settled_amount_in_transaction_currency == 20.0
    assert expense1.is_settled

    assert ep2.settled_transaction_id is not None
    assert ep2.settled_amount_in_transaction_currency == 30.0
    assert expense2.is_settled

    assert ep1.settled_transaction_id == ep2.settled_transaction_id # Both settled by the same new transaction

    created_transaction = await session.get(Transaction, ep1.settled_transaction_id)
    assert created_transaction.amount == 50.0
    assert created_transaction.created_by_user_id == test_user.id

# TODO: Add tests for /expenses/settle to ensure Expense.is_settled is updated.
# This will require adapting existing tests or adding new ones in test_expenses.py.
# For now, focusing on the new service and endpoint.
# Helper fixtures from conftest.py (like test_user, async_client etc.) are assumed to be available.
# If they are not, they'd need to be defined or imported.
# The conftest.py provided in the project already has these.
# Make sure to add necessary imports at the top of this file if new models are used.
# (User, Currency, Expense, ExpenseParticipant, Transaction are used)
# from src.main import app is needed for AsyncClient to work against.
# from typing import AsyncGenerator, Dict, Any for type hints.
# import pytest at the top.
# from httpx import AsyncClient
# from sqlmodel.ext.asyncio.session import AsyncSession
# from sqlmodel import select
# from src.models.models import User, Currency, Expense, ExpenseParticipant, Transaction
# from src.services.expense_service import update_expense_settlement_status
# from src.main import app
# from typing import AsyncGenerator, Dict, Any
# All these imports are added.
# One final check, conftest.py usually provides test_user, test_user2, test_user3, test_currency,
# async_client (instantiated with app), session (db session), test_user_auth_headers etc.
# These are assumed to be correctly set up as per the project's testing structure.
# The tests for `update_expense_settlement_status` directly interact with the session and models.
# The tests for the endpoint use `async_client` and auth headers.
# Looks reasonable.
# Added a test case for duplicate participant IDs in record-direct-payment request.
# Added a test case for participant share being zero.

@pytest.mark.asyncio
async def test_update_expense_settlement_status_participant_share_zero(
    session: AsyncSession, test_user: User, test_user2: User, test_currency: Currency
):
    """
    Test update_expense_settlement_status when a participant's share is zero.
    Such a participant should be considered settled by default.
    """
    expense = Expense(
        description="Test Expense Zero Share",
        amount=50.0, # Total amount
        paid_by_user_id=test_user.id,
        currency_id=test_currency.id,
    )
    session.add(expense)
    await session.flush()

    # ep1 has a share of 0
    ep1 = ExpenseParticipant(
        expense_id=expense.id, user_id=test_user2.id, share_amount=0.0
    )
    # ep2 has the full share
    ep2 = ExpenseParticipant(
        expense_id=expense.id, user_id=test_user.id, share_amount=50.0
    )
    session.add_all([ep1, ep2])
    await session.commit()

    # Settle ep2 (the one with actual share)
    transaction = Transaction(
        amount=50.0, currency_id=test_currency.id, created_by_user_id=test_user.id
    )
    session.add(transaction)
    await session.commit()

    ep2.settled_transaction_id = transaction.id
    ep2.settled_amount_in_transaction_currency = 50.0
    session.add(ep2)
    await session.commit()

    await session.refresh(expense)
    assert not expense.is_settled # Initially false

    await update_expense_settlement_status(expense.id, session)
    await session.commit()
    await session.refresh(expense)

    # Since ep1's share is 0 (considered settled) and ep2 is settled, expense should be settled.
    assert expense.is_settled


@pytest.mark.asyncio
async def test_record_direct_payment_duplicate_participant_ids_in_request(
    async_client: AsyncClient,
    session: AsyncSession,
    test_user: User,
    test_user2: User,
    test_currency: Currency,
    test_user_auth_headers: Dict[str, str]
):
    expense = Expense(description="E_dup", amount=10.0, paid_by_user_id=test_user2.id, currency_id=test_currency.id)
    session.add(expense)
    await session.flush()
    ep = ExpenseParticipant(expense_id=expense.id, user_id=test_user.id, share_amount=10.0)
    session.add(ep)
    await session.commit()
    await session.refresh(ep)

    payment_data = {
        "debtor_user_id": test_user.id,
        "creditor_user_id": test_user2.id,
        "amount_paid": 10.0, # This would be 20 if sum was respected, but validation is for duplication first
        "currency_paid_id": test_currency.id,
        "expense_participant_ids_to_settle": [ep.id, ep.id] # Duplicate ID
    }

    response = await async_client.post(
        "/api/v1/settlements/record-direct-payment",
        json=payment_data,
        headers=test_user_auth_headers
    )
    assert response.status_code == 400
    assert "Duplicate expense_participant_id" in response.json()["detail"]
