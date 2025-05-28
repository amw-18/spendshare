import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional

from src.models.models import User, Group, Expense, Currency, ExpenseParticipant # Corrected import
from src.models.schemas import UserRead, CurrencyRead # Corrected import
from src.main import app # Import your FastAPI app, Corrected import
from app.tests.conftest import TestingSessionLocal  # Import TestingSessionLocal
from app.src.core.security import get_password_hash # Import get_password_hash

# Helper function to create a user (can be moved to a conftest.py later)
async def create_test_user(
    # session: AsyncSession, # Session will be created internally
    username: str = "testuser", 
    email: str = "test@example.com", 
    password: str = "Testpassword123",
    is_admin: bool = False
) -> User:
    user = User(
        username=username, 
        email=email, 
        hashed_password=get_password_hash(password),  # Use get_password_hash
        is_admin=is_admin
    )
    async with TestingSessionLocal() as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

# Helper function to create a currency
async def create_test_currency(
    # session: AsyncSession, # Session will be created internally
    code: str = "USD", 
    name: str = "US Dollar", 
    symbol: str = "$"
) -> Currency:
    currency = Currency(code=code, name=name, symbol=symbol)
    async with TestingSessionLocal() as session:
        session.add(currency)
        await session.commit()
        await session.refresh(currency)
        return currency

# Helper function to create an expense
async def create_test_expense(
    # session: AsyncSession, # Session will be created internally
    description: str,
    amount: float,
    currency_id: int,
    paid_by_user_id: int,
    group_id: Optional[int] = None,
    participants: Optional[List[Dict[str, Any]]] = None # e.g., [{"user_id": 1, "share_amount": 10.0}]
) -> Expense:
    expense = Expense(
        description=description,
        amount=amount,
        currency_id=currency_id,
        paid_by_user_id=paid_by_user_id,
        group_id=group_id
    )
    async with TestingSessionLocal() as session:
        session.add(expense)
        await session.commit()
        await session.refresh(expense)

        if participants:
            for p_data in participants:
                participant = ExpenseParticipant(
                    expense_id=expense.id,
                    user_id=p_data["user_id"],
                    share_amount=p_data["share_amount"]
                )
                session.add(participant)
            await session.commit()
            await session.refresh(expense, attribute_names=['participants']) # Refresh to load participants
        return expense


@pytest.mark.asyncio
async def test_get_balances_no_expenses(client: AsyncClient, db_setup_session: AsyncSession, normal_user_token_headers: dict):
    # db_setup_session is an autouse fixture for setup/teardown, not for direct use here.
    # Helpers will use TestingSessionLocal.
    response = await client.get("/api/v1/balances/me", headers=normal_user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["balances"] == []


@pytest.mark.asyncio
async def test_get_balances_user_paid_no_participants(
    client: AsyncClient, db_setup_session: AsyncSession, normal_user_token_headers: dict, normal_user: User
):
    # Create a currency
    currency = await create_test_currency(code="USD", name="US Dollar") # Removed db_setup_session
    
    # Create an expense paid by the current user
    await create_test_expense(
        # db_setup_session, # Removed
        description="Lunch",
        amount=50.0,
        currency_id=currency.id,
        paid_by_user_id=normal_user.id,
        participants=[] # No other participants
    )

    response = await client.get("/api/v1/balances/me", headers=normal_user_token_headers)
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["balances"]) == 1
    balance = data["balances"][0]
    assert balance["currency"]["code"] == "USD"
    assert balance["total_paid"] == 50.0
    assert balance["net_owed_to_user"] == 0.0
    assert balance["net_user_owes"] == 0.0


@pytest.mark.asyncio
async def test_get_balances_user_paid_others_owe(
    client: AsyncClient, db_setup_session: AsyncSession, normal_user_token_headers: dict, normal_user: User
):
    user2 = await create_test_user(username="user2", email="user2@example.com") # Removed db_setup_session
    currency = await create_test_currency(code="EUR", name="Euro") # Removed db_setup_session

    await create_test_expense(
        # db_setup_session, # Removed
        description="Dinner",
        amount=100.0,
        currency_id=currency.id,
        paid_by_user_id=normal_user.id,
        participants=[
            {"user_id": user2.id, "share_amount": 40.0},
            # normal_user's share is implied (100 - 40 = 60)
        ]
    )

    response = await client.get("/api/v1/balances/me", headers=normal_user_token_headers)
    assert response.status_code == 200
    data = response.json()

    assert len(data["balances"]) == 1
    balance = data["balances"][0]
    assert balance["currency"]["code"] == "EUR"
    assert balance["total_paid"] == 100.0
    assert balance["net_owed_to_user"] == 40.0 
    assert balance["net_user_owes"] == 0.0


@pytest.mark.asyncio
async def test_get_balances_user_owes_others(
    client: AsyncClient, db_setup_session: AsyncSession, normal_user_token_headers: dict, normal_user: User
):
    payer_user = await create_test_user(username="payeruser", email="payer@example.com") # Removed db_setup_session
    currency = await create_test_currency(code="GBP", name="British Pound") # Removed db_setup_session

    await create_test_expense(
        # db_setup_session, # Removed
        description="Concert Tickets",
        amount=120.0,
        currency_id=currency.id,
        paid_by_user_id=payer_user.id,
        participants=[
            {"user_id": normal_user.id, "share_amount": 60.0},
            {"user_id": payer_user.id, "share_amount": 60.0} # Payer also listed as participant for their share
        ]
    )

    response = await client.get("/api/v1/balances/me", headers=normal_user_token_headers)
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["balances"]) == 1
    balance = data["balances"][0]
    assert balance["currency"]["code"] == "GBP"
    assert balance["total_paid"] == 0.0 # Current user paid nothing
    assert balance["net_owed_to_user"] == 0.0
    assert balance["net_user_owes"] == 60.0


@pytest.mark.asyncio
async def test_get_balances_multiple_expenses_same_currency(
    client: AsyncClient, db_setup_session: AsyncSession, normal_user_token_headers: dict, normal_user: User
):
    user2 = await create_test_user(username="user2_multi_same", email="user2ms@example.com") # Removed db_setup_session
    payer_user = await create_test_user(username="payer_multi_same", email="payerms@example.com") # Removed db_setup_session
    currency_usd = await create_test_currency(code="USD", name="US Dollar") # Removed db_setup_session

    # Expense 1: Current user pays, user2 owes
    await create_test_expense(
        # db_setup_session, # Removed
        description="Groceries", amount=80.0, currency_id=currency_usd.id,
        paid_by_user_id=normal_user.id, participants=[{"user_id": user2.id, "share_amount": 30.0}]
    )
    # Expense 2: Payer_user pays, current_user owes
    await create_test_expense(
        # db_setup_session, # Removed
        description="Movies", amount=50.0, currency_id=currency_usd.id,
        paid_by_user_id=payer_user.id, participants=[{"user_id": normal_user.id, "share_amount": 25.0}]
    )
    # Expense 3: Current user pays for self only
    await create_test_expense(
        # db_setup_session, # Removed
        description="Coffee", amount=5.0, currency_id=currency_usd.id,
        paid_by_user_id=normal_user.id, participants=[]
    )

    response = await client.get("/api/v1/balances/me", headers=normal_user_token_headers)
    assert response.status_code == 200
    data = response.json()

    assert len(data["balances"]) == 1
    balance_usd = data["balances"][0]
    assert balance_usd["currency"]["code"] == "USD"
    assert balance_usd["total_paid"] == 80.0 + 5.0  # 85.0
    assert balance_usd["net_owed_to_user"] == 30.0
    assert balance_usd["net_user_owes"] == 25.0


@pytest.mark.asyncio
async def test_get_balances_expenses_in_different_currencies(
    client: AsyncClient, db_setup_session: AsyncSession, normal_user_token_headers: dict, normal_user: User
):
    user2 = await create_test_user(username="user2_multi_diff", email="user2md@example.com") # Removed db_setup_session
    payer_user_eur = await create_test_user(username="payer_eur", email="payereur@example.com") # Removed db_setup_session

    currency_usd = await create_test_currency(code="USD", name="US Dollar") # Removed db_setup_session
    currency_eur = await create_test_currency(code="EUR", name="Euro") # Removed db_setup_session

    # USD Expense: Current user pays, user2 owes
    await create_test_expense(
        # db_setup_session, # Removed
        description="Lunch USD", amount=60.0, currency_id=currency_usd.id,
        paid_by_user_id=normal_user.id, participants=[{"user_id": user2.id, "share_amount": 20.0}]
    )
    # EUR Expense: payer_user_eur pays, current_user owes
    await create_test_expense(
        # db_setup_session, # Removed
        description="Train Ticket EUR", amount=70.0, currency_id=currency_eur.id,
        paid_by_user_id=payer_user_eur.id, participants=[{"user_id": normal_user.id, "share_amount": 30.0}]
    )

    response = await client.get("/api/v1/balances/me", headers=normal_user_token_headers)
    assert response.status_code == 200
    data = response.json()

    assert len(data["balances"]) == 2
    
    usd_balance = next((b for b in data["balances"] if b["currency"]["code"] == "USD"), None)
    eur_balance = next((b for b in data["balances"] if b["currency"]["code"] == "EUR"), None)

    assert usd_balance is not None
    assert usd_balance["total_paid"] == 60.0
    assert usd_balance["net_owed_to_user"] == 20.0
    assert usd_balance["net_user_owes"] == 0.0

    assert eur_balance is not None
    assert eur_balance["total_paid"] == 0.0
    assert eur_balance["net_owed_to_user"] == 0.0
    assert eur_balance["net_user_owes"] == 30.0


@pytest.mark.asyncio
async def test_get_balances_user_payer_and_participant(
    client: AsyncClient, db_setup_session: AsyncSession, normal_user_token_headers: dict, normal_user: User
):
    # This tests an edge case. Typically, a payer's "share" is implied or they aren't listed as a participant for their own portion.
    # However, if they are explicitly listed, the logic should handle it.
    # The current logic in router for `net_owed_to_user` sums up shares of *other* users when normal_user is the payer.
    # If normal_user is also listed as a participant in an expense they paid, their share as a participant
    # won't be double-counted towards `net_owed_to_user` nor towards `net_user_owes`.
    
    user2 = await create_test_user(username="user2_edge", email="user2edge@example.com") # Removed db_setup_session
    currency = await create_test_currency(code="CAD", name="Canadian Dollar") # Removed db_setup_session

    await create_test_expense(
        # db_setup_session, # Removed
        description="Shared Software Subscription",
        amount=100.0,
        currency_id=currency.id,
        paid_by_user_id=normal_user.id, # Current user paid
        participants=[
            {"user_id": normal_user.id, "share_amount": 50.0}, # Current user's own share
            {"user_id": user2.id, "share_amount": 50.0}      # User2's share
        ]
    )

    response = await client.get("/api/v1/balances/me", headers=normal_user_token_headers)
    assert response.status_code == 200
    data = response.json()

    assert len(data["balances"]) == 1
    balance = data["balances"][0]
    assert balance["currency"]["code"] == "CAD"
    assert balance["total_paid"] == 100.0
    # net_owed_to_user should only include amounts from *other* participants
    assert balance["net_owed_to_user"] == 50.0 
    assert balance["net_user_owes"] == 0.0
