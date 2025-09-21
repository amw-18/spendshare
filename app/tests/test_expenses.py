import pytest
from httpx import AsyncClient
from fastapi import status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.models import User, Group, Currency, Expense


@pytest.mark.asyncio
async def test_create_simple_expense(authenticated_client: AsyncClient, normal_user: User, test_currency: Currency):
    expense_data = {
        "description": "Test Expense",
        "amount": 10.0,
        "currency_id": test_currency.id,
    }
    response = await authenticated_client.post("/api/v1/expenses/", json=expense_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["description"] == expense_data["description"]
    assert data["paid_by_user_id"] == normal_user.id


@pytest.mark.asyncio
async def test_create_expense_with_participants(
    authenticated_client: AsyncClient, normal_user: User, test_currency: Currency, async_db_session: AsyncSession
):
    other_user = User(clerk_id="user_2i5n5s3gH9Q8Q4G8b4k3d3f7m", username="otheruser", email="otheruser@example.com")
    async_db_session.add(other_user)
    await async_db_session.commit()
    await async_db_session.refresh(other_user)

    expense_data = {
        "description": "Shared Expense",
        "amount": 20.0,
        "currency_id": test_currency.id,
        "participant_shares": [
            {"user_id": normal_user.id, "share_amount": 10.0},
            {"user_id": other_user.id, "share_amount": 10.0},
        ],
    }
    response = await authenticated_client.post("/api/v1/expenses/service/", json=expense_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert len(data["participant_details"]) == 2


@pytest.mark.asyncio
async def test_get_expenses(authenticated_client: AsyncClient, normal_user: User, test_currency: Currency):
    await authenticated_client.post(
        "/api/v1/expenses/",
        json={"description": "Expense 1", "amount": 10.0, "currency_id": test_currency.id},
    )
    await authenticated_client.post(
        "/api/v1/expenses/",
        json={"description": "Expense 2", "amount": 20.0, "currency_id": test_currency.id},
    )

    response = await authenticated_client.get("/api/v1/expenses/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_get_expense(authenticated_client: AsyncClient, normal_user: User, test_currency: Currency):
    create_response = await authenticated_client.post(
        "/api/v1/expenses/",
        json={"description": "Test Expense", "amount": 10.0, "currency_id": test_currency.id},
    )
    expense_id = create_response.json()["id"]

    response = await authenticated_client.get(f"/api/v1/expenses/{expense_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == expense_id


@pytest.mark.asyncio
async def test_update_expense(authenticated_client: AsyncClient, normal_user: User, test_currency: Currency):
    create_response = await authenticated_client.post(
        "/api/v1/expenses/",
        json={"description": "Test Expense", "amount": 10.0, "currency_id": test_currency.id},
    )
    expense_id = create_response.json()["id"]

    new_description = "Updated Test Expense"
    response = await authenticated_client.put(
        f"/api/v1/expenses/{expense_id}", json={"description": new_description}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["description"] == new_description


@pytest.mark.asyncio
async def test_delete_expense(authenticated_client: AsyncClient, normal_user: User, test_currency: Currency):
    create_response = await authenticated_client.post(
        "/api/v1/expenses/",
        json={"description": "Test Expense", "amount": 10.0, "currency_id": test_currency.id},
    )
    expense_id = create_response.json()["id"]

    response = await authenticated_client.delete(f"/api/v1/expenses/{expense_id}")
    assert response.status_code == status.HTTP_200_OK

    get_response = await authenticated_client.get(f"/api/v1/expenses/{expense_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_expense_authorization(
    client: AsyncClient, normal_user: User, test_currency: Currency, async_db_session: AsyncSession
):
    # Create an expense with normal_user
    expense = Expense(
        description="Test Expense",
        amount=10.0,
        currency_id=test_currency.id,
        paid_by_user_id=normal_user.id,
    )
    async_db_session.add(expense)
    await async_db_session.commit()
    await async_db_session.refresh(expense)

    # Create another user
    other_user = User(
        clerk_id="user_2i5n5s3gH9Q8Q4G8b4k3d3f7l",
        username="otheruser",
        email="otheruser@example.com",
    )
    async_db_session.add(other_user)
    await async_db_session.commit()
    await async_db_session.refresh(other_user)

    # Override get_current_user with other_user
    async def override_get_current_user() -> User:
        return other_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    client.headers["Authorization"] = "Bearer mock_token"

    # other_user should not be able to get the expense
    response = await client.get(f"/api/v1/expenses/{expense.id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN