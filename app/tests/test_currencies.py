import pytest
from httpx import AsyncClient
from fastapi import status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.models import Currency, User, Expense, ExpenseParticipant

API_PREFIX = "/api/v1/currencies"


@pytest.mark.asyncio
async def test_create_currency(
    client: AsyncClient, normal_user_token_headers: dict, async_db_session: AsyncSession
):  # Renamed and changed fixture
    currency_data = {"code": "USD", "name": "US Dollar", "symbol": "$"}
    response = await client.post(
        f"{API_PREFIX}/", headers=normal_user_token_headers, json=currency_data
    )  # Changed fixture
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "USD"
    assert data["name"] == "US Dollar"
    assert data["symbol"] == "$"
    assert "id" in data

    # Verify in DB
    currency_in_db = await async_db_session.get(Currency, data["id"])
    assert currency_in_db is not None
    assert currency_in_db.code == "USD"


@pytest.mark.asyncio
async def test_create_currency_duplicate_code(
    client: AsyncClient, normal_user_token_headers: dict, async_db_session: AsyncSession
):  # Changed fixture
    currency_data = {"code": "CAD", "name": "Canadian Dollar", "symbol": "C$"}
    response1 = await client.post(
        f"{API_PREFIX}/", headers=normal_user_token_headers, json=currency_data
    )  # Changed fixture
    assert response1.status_code == 201

    currency_data_dup = {"code": "CAD", "name": "Another CAD", "symbol": "C$"}
    response2 = await client.post(
        f"{API_PREFIX}/", headers=normal_user_token_headers, json=currency_data_dup
    )  # Changed fixture
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"]


@pytest.mark.asyncio
async def test_read_currencies_empty(client: AsyncClient):
    response = await client.get(f"{API_PREFIX}/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_read_currencies_multiple(
    client: AsyncClient, normal_user_token_headers: dict, async_db_session: AsyncSession
):  # Changed fixture
    c1_data = {"code": "GBP", "name": "British Pound", "symbol": "£"}
    await client.post(
        f"{API_PREFIX}/", headers=normal_user_token_headers, json=c1_data
    )  # Changed fixture
    c2_data = {"code": "JPY", "name": "Japanese Yen", "symbol": "¥"}
    await client.post(
        f"{API_PREFIX}/", headers=normal_user_token_headers, json=c2_data
    )  # Changed fixture

    response = await client.get(f"{API_PREFIX}/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    codes_in_response = {item["code"] for item in data}
    assert "GBP" in codes_in_response
    assert "JPY" in codes_in_response

    # Test pagination (limit)
    response_limit = await client.get(f"{API_PREFIX}/?limit=1")
    assert response_limit.status_code == 200
    data_limit = response_limit.json()
    assert len(data_limit) == 1


@pytest.mark.asyncio
async def test_read_specific_currency(
    client: AsyncClient, normal_user_token_headers: dict, async_db_session: AsyncSession
):  # Changed fixture
    currency_data = {"code": "AUD", "name": "Australian Dollar", "symbol": "A$"}
    response_create = await client.post(
        f"{API_PREFIX}/", headers=normal_user_token_headers, json=currency_data
    )  # Changed fixture
    currency_id = response_create.json()["id"]

    response_read = await client.get(f"{API_PREFIX}/{currency_id}")
    assert response_read.status_code == 200
    data = response_read.json()
    assert data["id"] == currency_id
    assert data["code"] == "AUD"


@pytest.mark.asyncio
async def test_read_specific_currency_not_found(client: AsyncClient):
    response = await client.get(f"{API_PREFIX}/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_currency(
    client: AsyncClient, normal_user_token_headers: dict, async_db_session: AsyncSession
):  # Renamed and changed fixture
    currency_data = {"code": "CHF", "name": "Swiss Franc", "symbol": "CHF"}
    response_create = await client.post(
        f"{API_PREFIX}/", headers=normal_user_token_headers, json=currency_data
    )  # Changed fixture
    assert response_create.status_code == 201
    currency_id = response_create.json()["id"]

    update_data = {"name": "Swiss Franc Updated", "symbol": "SFr"}
    response_update = await client.put(
        f"{API_PREFIX}/{currency_id}",
        headers=normal_user_token_headers,
        json=update_data,
    )  # Changed fixture
    assert response_update.status_code == 200
    data = response_update.json()
    assert data["name"] == "Swiss Franc Updated"
    assert data["symbol"] == "SFr"
    assert data["code"] == "CHF"  # Code should not change unless specified

    # Verify in DB
    currency_in_db = await async_db_session.get(Currency, currency_id)
    assert currency_in_db is not None
    assert currency_in_db.name == "Swiss Franc Updated"


@pytest.mark.asyncio
async def test_update_currency_change_code(
    client: AsyncClient, normal_user_token_headers: dict, async_db_session: AsyncSession
):  # Renamed and changed fixture
    currency_data = {"code": "NZD", "name": "New Zealand Dollar", "symbol": "NZ$"}
    response_create = await client.post(
        f"{API_PREFIX}/", headers=normal_user_token_headers, json=currency_data
    )  # Changed fixture
    assert response_create.status_code == 201
    currency_id = response_create.json()["id"]

    update_data = {"code": "NZZ", "name": "New Zealand Dollar Updated", "symbol": "N$$"}
    response_update = await client.put(
        f"{API_PREFIX}/{currency_id}",
        headers=normal_user_token_headers,
        json=update_data,
    )  # Changed fixture
    assert response_update.status_code == 200
    updated_currency = response_update.json()
    assert updated_currency["code"] == "NZZ"
    assert updated_currency["name"] == "New Zealand Dollar Updated"
    assert updated_currency["symbol"] == "N$$"


@pytest.mark.asyncio
async def test_update_currency_new_code_duplicate(
    client: AsyncClient, normal_user_token_headers: dict, async_db_session: AsyncSession
):  # Changed fixture
    currency1_data = {"code": "CRA", "name": "Currency Alpha", "symbol": "CA"}
    response_create1 = await client.post(
        f"{API_PREFIX}/", headers=normal_user_token_headers, json=currency1_data
    )  # Changed fixture
    assert response_create1.status_code == status.HTTP_201_CREATED, (
        f"Failed to create CRA: {response_create1.json()}"
    )

    currency2_data = {"code": "CRB", "name": "Currency Bravo", "symbol": "CB"}
    response_create2 = await client.post(
        f"{API_PREFIX}/", headers=normal_user_token_headers, json=currency2_data
    )  # Changed fixture
    assert response_create2.status_code == status.HTTP_201_CREATED, (
        f"Failed to create CRB: {response_create2.json()}"
    )
    currency2_id = response_create2.json()["id"]

    update_data = {"code": "CRA"}
    response_update = await client.put(
        f"{API_PREFIX}/{currency2_id}",
        headers=normal_user_token_headers,
        json=update_data,
    )  # Changed fixture
    assert response_update.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in response_update.json()["detail"]


@pytest.mark.asyncio
async def test_update_currency_not_found(
    client: AsyncClient, normal_user_token_headers: dict
):  # Changed fixture
    update_data = {"name": "Non Existent Currency Updated"}
    response = await client.put(
        f"{API_PREFIX}/88888", headers=normal_user_token_headers, json=update_data
    )  # Changed fixture
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_currency_unused(
    client: AsyncClient, normal_user_token_headers: dict, async_db_session: AsyncSession
):  # Renamed and changed fixture
    currency_data = {"code": "NOK", "name": "Norwegian Krone", "symbol": "kr"}
    response_create = await client.post(
        f"{API_PREFIX}/", headers=normal_user_token_headers, json=currency_data
    )  # Changed fixture
    currency_id = response_create.json()["id"]

    response_delete = await client.delete(
        f"{API_PREFIX}/{currency_id}", headers=normal_user_token_headers
    )  # Changed fixture
    assert response_delete.status_code == 200
    assert response_delete.json()["message"] == "Currency deleted"

    # Verify in DB
    currency_in_db = await async_db_session.get(Currency, currency_id)
    assert currency_in_db is None


@pytest.mark.asyncio
async def test_delete_currency(client: AsyncClient, normal_user_token_headers: dict):
    currency_data = {"code": "SEK", "name": "Swedish Krona", "symbol": "kr"}
    response_create = await client.post(
        f"{API_PREFIX}/", headers=normal_user_token_headers, json=currency_data
    )
    assert response_create.status_code == status.HTTP_201_CREATED
    currency_id = response_create.json()["id"]

    response_delete = await client.delete(
        f"{API_PREFIX}/{currency_id}", headers=normal_user_token_headers
    )
    assert response_delete.status_code == status.HTTP_200_OK
    assert response_delete.json()["message"] == "Currency deleted"

    # Verify deletion by trying to get it
    response_get = await client.get(
        f"{API_PREFIX}/{currency_id}", headers=normal_user_token_headers
    )
    assert response_get.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_currency_not_found(
    client: AsyncClient, normal_user_token_headers: dict
):
    response = await client.delete(
        f"{API_PREFIX}/77777", headers=normal_user_token_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_currency_used(
    client: AsyncClient,
    normal_user_token_headers: dict,  # Changed fixture
    async_db_session: AsyncSession,
    normal_user: User,  # Changed fixture
):
    currency_data = {"code": "TST", "name": "Test Currency", "symbol": "T"}
    response_currency = await client.post(
        f"{API_PREFIX}/", headers=normal_user_token_headers, json=currency_data
    )  # Changed fixture
    assert response_currency.status_code == 201
    currency_id = response_currency.json()["id"]

    expense_data = {
        "description": "Test Expense for Currency",
        "amount": 100.0,
        "currency_id": currency_id,
    }
    response_expense = await client.post(
        "/api/v1/expenses/",
        headers=normal_user_token_headers,  # Changed fixture
        json=expense_data,
    )
    assert response_expense.status_code == 201
    expense_id = response_expense.json()["id"]

    response_delete = await client.delete(
        f"{API_PREFIX}/{currency_id}", headers=normal_user_token_headers
    )  # Changed fixture
    assert response_delete.status_code == 400
    assert "associated with existing expenses" in response_delete.json()["detail"]

    currency_in_db = await async_db_session.get(Currency, currency_id)
    assert currency_in_db is not None
    assert currency_in_db.code == "TST"

    stmt_participants = select(ExpenseParticipant).where(
        ExpenseParticipant.expense_id == expense_id
    )
    result_participants = await async_db_session.exec(stmt_participants)
    participants = result_participants.all()
    for participant in participants:
        await async_db_session.delete(participant)

    expense_to_delete = await async_db_session.get(Expense, expense_id)
    if expense_to_delete:
        await async_db_session.delete(expense_to_delete)
        await async_db_session.commit()

