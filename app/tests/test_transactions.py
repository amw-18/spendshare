import pytest
from httpx import AsyncClient
from fastapi import status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.models import User, Currency, Expense, ExpenseParticipant, Transaction
from src.main import app
from src.core.security import get_current_user


@pytest.mark.asyncio
async def test_create_transaction(authenticated_client: AsyncClient, normal_user: User, test_currency: Currency):
    transaction_data = {
        "amount": 100.0,
        "currency_id": test_currency.id,
        "description": "Test Transaction",
    }
    response = await authenticated_client.post("/api/v1/transactions/", json=transaction_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["amount"] == transaction_data["amount"]
    assert data["created_by_user_id"] == normal_user.id


@pytest.mark.asyncio
async def test_get_transaction(authenticated_client: AsyncClient, normal_user: User, test_currency: Currency, async_db_session: AsyncSession):
    transaction = Transaction(
        amount=100.0, currency_id=test_currency.id, description="Test", created_by_user_id=normal_user.id
    )
    async_db_session.add(transaction)
    await async_db_session.commit()
    await async_db_session.refresh(transaction)

    response = await authenticated_client.get(f"/api/v1/transactions/{transaction.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == transaction.id


@pytest.mark.asyncio
async def test_settle_expense(authenticated_client: AsyncClient, normal_user: User, test_currency: Currency, async_db_session: AsyncSession):
    expense = Expense(
        description="Test Expense",
        amount=20.0,
        currency_id=test_currency.id,
        paid_by_user_id=normal_user.id,
    )
    async_db_session.add(expense)
    await async_db_session.commit()
    await async_db_session.refresh(expense)

    other_user = User(clerk_id="user_2i5n5s3gH9Q8Q4G8b4k3d3f7n", username="otheruser2", email="otheruser2@example.com")
    async_db_session.add(other_user)
    await async_db_session.commit()
    await async_db_session.refresh(other_user)

    participant = ExpenseParticipant(
        expense_id=expense.id, user_id=other_user.id, share_amount=10.0
    )
    async_db_session.add(participant)
    await async_db_session.commit()
    await async_db_session.refresh(participant)

    transaction = Transaction(
        amount=10.0, currency_id=test_currency.id, description="Settlement", created_by_user_id=normal_user.id
    )
    async_db_session.add(transaction)
    await async_db_session.commit()
    await async_db_session.refresh(transaction)

    settle_data = {
        "transaction_id": transaction.id,
        "settlements": [
            {
                "expense_participant_id": participant.id,
                "settled_amount": 10.0,
                "settled_currency_id": test_currency.id,
            }
        ],
    }
    response = await authenticated_client.post("/api/v1/expenses/settle", json=settle_data)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_transaction_authorization(
    client: AsyncClient, normal_user: User, test_currency: Currency, async_db_session: AsyncSession
):
    transaction = Transaction(
        amount=100.0, currency_id=test_currency.id, description="Test", created_by_user_id=normal_user.id
    )
    async_db_session.add(transaction)
    await async_db_session.commit()
    await async_db_session.refresh(transaction)

    other_user = User(
        clerk_id="user_2i5n5s3gH9Q8Q4G8b4k3d3f7l",
        username="otheruser",
        email="otheruser@example.com",
    )
    async_db_session.add(other_user)
    await async_db_session.commit()
    await async_db_session.refresh(other_user)

    async def override_get_current_user() -> User:
        return other_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    client.headers["Authorization"] = "Bearer mock_token"

    response = await client.get(f"/api/v1/transactions/{transaction.id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN
