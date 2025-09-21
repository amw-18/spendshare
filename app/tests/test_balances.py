import pytest
from httpx import AsyncClient
from fastapi import status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.models import User, Currency, Expense, ExpenseParticipant


@pytest.mark.asyncio
async def test_get_balances_no_expenses(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/v1/balances/me")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["balances"] == []


@pytest.mark.asyncio
async def test_get_balances_user_paid(authenticated_client: AsyncClient, normal_user: User, test_currency: Currency, async_db_session: AsyncSession):
    expense = Expense(
        description="Test Expense",
        amount=50.0,
        currency_id=test_currency.id,
        paid_by_user_id=normal_user.id,
    )
    async_db_session.add(expense)
    await async_db_session.commit()

    response = await authenticated_client.get("/api/v1/balances/me")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["balances"]) == 1
    balance = data["balances"][0]
    assert balance["currency"]["code"] == test_currency.code
    assert balance["total_paid"] == 50.0
    assert balance["net_owed_to_user"] == 0.0
    assert balance["net_user_owes"] == 0.0


@pytest.mark.asyncio
async def test_get_balances_user_owes(authenticated_client: AsyncClient, normal_user: User, test_currency: Currency, async_db_session: AsyncSession):
    payer = User(clerk_id="user_2i5n5s3gH9Q8Q4G8b4k3d3f7o", username="payer", email="payer@example.com")
    async_db_session.add(payer)
    await async_db_session.commit()
    await async_db_session.refresh(payer)

    expense = Expense(
        description="Test Expense",
        amount=100.0,
        currency_id=test_currency.id,
        paid_by_user_id=payer.id,
    )
    async_db_session.add(expense)
    await async_db_session.commit()
    await async_db_session.refresh(expense)

    participant = ExpenseParticipant(
        expense_id=expense.id, user_id=normal_user.id, share_amount=40.0
    )
    async_db_session.add(participant)
    await async_db_session.commit()

    response = await authenticated_client.get("/api/v1/balances/me")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["balances"]) == 1
    balance = data["balances"][0]
    assert balance["currency"]["code"] == test_currency.code
    assert balance["total_paid"] == 0.0
    assert balance["net_owed_to_user"] == 0.0
    assert balance["net_user_owes"] == 40.0


@pytest.mark.asyncio
async def test_get_balances_multiple_currencies(authenticated_client: AsyncClient, normal_user: User, test_currency: Currency, async_db_session: AsyncSession):
    # USD Expense
    expense_usd = Expense(
        description="USD Expense",
        amount=60.0,
        currency_id=test_currency.id,
        paid_by_user_id=normal_user.id,
    )
    async_db_session.add(expense_usd)

    # EUR Expense
    eur_currency = Currency(code="EUR", name="Euro", symbol="€")
    async_db_session.add(eur_currency)
    await async_db_session.commit()
    await async_db_session.refresh(eur_currency)

    payer_eur = User(clerk_id="user_2i5n5s3gH9Q8Q4G8b4k3d3f7p", username="payereur", email="payereur@example.com")
    async_db_session.add(payer_eur)
    await async_db_session.commit()
    await async_db_session.refresh(payer_eur)

    expense_eur = Expense(
        description="EUR Expense",
        amount=70.0,
        currency_id=eur_currency.id,
        paid_by_user_id=payer_eur.id,
    )
    async_db_session.add(expense_eur)
    await async_db_session.commit()
    await async_db_session.refresh(expense_eur)

    participant_eur = ExpenseParticipant(
        expense_id=expense_eur.id, user_id=normal_user.id, share_amount=30.0
    )
    async_db_session.add(participant_eur)
    await async_db_session.commit()

    response = await authenticated_client.get("/api/v1/balances/me")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["balances"]) == 2

    usd_balance = next((b for b in data["balances"] if b["currency"]["code"] == "USD"), None)
    eur_balance = next((b for b in data["balances"] if b["currency"]["code"] == "EUR"), None)

    assert usd_balance is not None
    assert usd_balance["total_paid"] == 60.0
    assert usd_balance["net_owed_to_user"] == 0.0
    assert usd_balance["net_user_owes"] == 0.0

    assert eur_balance is not None
    assert eur_balance["total_paid"] == 0.0
    assert eur_balance["net_owed_to_user"] == 0.0
    assert eur_balance["net_user_owes"] == 30.0