import pytest
from httpx import AsyncClient
from fastapi import status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.models import Currency


@pytest.mark.asyncio
async def test_create_currency(authenticated_client: AsyncClient):
    currency_data = {"code": "USD", "name": "US Dollar", "symbol": "$"}
    response = await authenticated_client.post("/api/v1/currencies/", json=currency_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["code"] == "USD"


@pytest.mark.asyncio
async def test_get_currencies(authenticated_client: AsyncClient, async_db_session: AsyncSession):
    currency1 = Currency(code="USD", name="US Dollar", symbol="$")
    currency2 = Currency(code="EUR", name="Euro", symbol="€")
    async_db_session.add_all([currency1, currency2])
    await async_db_session.commit()

    response = await authenticated_client.get("/api/v1/currencies/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_get_currency(authenticated_client: AsyncClient, test_currency: Currency):
    response = await authenticated_client.get(f"/api/v1/currencies/{test_currency.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["code"] == test_currency.code


@pytest.mark.asyncio
async def test_update_currency(authenticated_client: AsyncClient, test_currency: Currency):
    new_name = "United States Dollar"
    response = await authenticated_client.put(
        f"/api/v1/currencies/{test_currency.id}", json={"name": new_name}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == new_name


@pytest.mark.asyncio
async def test_delete_currency(authenticated_client: AsyncClient, test_currency: Currency):
    response = await authenticated_client.delete(f"/api/v1/currencies/{test_currency.id}")
    assert response.status_code == status.HTTP_200_OK

    get_response = await authenticated_client.get(f"/api/v1/currencies/{test_currency.id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_unauthenticated_currency_access(client: AsyncClient):
    response = await client.post("/api/v1/currencies/", json={})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = await client.put("/api/v1/currencies/1", json={})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = await client.delete("/api/v1/currencies/1")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED