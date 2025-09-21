import pytest
from httpx import AsyncClient
from fastapi import status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.models import Currency, ConversionRate


@pytest.mark.asyncio
async def test_create_conversion_rate(authenticated_client: AsyncClient, async_db_session: AsyncSession):
    currency1 = Currency(code="USD", name="US Dollar", symbol="$")
    currency2 = Currency(code="EUR", name="Euro", symbol="€")
    async_db_session.add_all([currency1, currency2])
    await async_db_session.commit()
    await async_db_session.refresh(currency1)
    await async_db_session.refresh(currency2)

    rate_data = {"from_currency_id": currency1.id, "to_currency_id": currency2.id, "rate": 0.9}
    response = await authenticated_client.post("/api/v1/conversion-rates/", json=rate_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["rate"] == 0.9


@pytest.mark.asyncio
async def test_get_conversion_rates(authenticated_client: AsyncClient, async_db_session: AsyncSession):
    currency1 = Currency(code="USD", name="US Dollar", symbol="$")
    currency2 = Currency(code="EUR", name="Euro", symbol="€")
    async_db_session.add_all([currency1, currency2])
    await async_db_session.commit()
    await async_db_session.refresh(currency1)
    await async_db_session.refresh(currency2)

    rate = ConversionRate(from_currency_id=currency1.id, to_currency_id=currency2.id, rate=0.9)
    async_db_session.add(rate)
    await async_db_session.commit()

    response = await authenticated_client.get("/api/v1/conversion-rates/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_latest_conversion_rate(authenticated_client: AsyncClient, async_db_session: AsyncSession):
    currency1 = Currency(code="USD", name="US Dollar", symbol="$")
    currency2 = Currency(code="EUR", name="Euro", symbol="€")
    async_db_session.add_all([currency1, currency2])
    await async_db_session.commit()
    await async_db_session.refresh(currency1)
    await async_db_session.refresh(currency2)

    rate1 = ConversionRate(from_currency_id=currency1.id, to_currency_id=currency2.id, rate=0.9)
    rate2 = ConversionRate(from_currency_id=currency1.id, to_currency_id=currency2.id, rate=0.95)
    async_db_session.add_all([rate1, rate2])
    await async_db_session.commit()

    response = await authenticated_client.get(f"/api/v1/conversion-rates/latest?from_code=USD&to_code=EUR")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["rate"] == 0.95


@pytest.mark.asyncio
async def test_unauthenticated_conversion_rate_access(client: AsyncClient):
    response = await client.post("/api/v1/conversion-rates/", json={})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED