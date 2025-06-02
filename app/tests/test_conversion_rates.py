import pytest
from httpx import AsyncClient
from fastapi import status
from typing import Optional

# Models and Schemas
from src.models.models import Currency

from tests.conftest import (
    TestingSessionLocal,
)  # Corrected path: To create sessions in helpers


# Helper to create currency for tests if not already in conftest or easily usable
async def create_test_currency_for_rates(
    code: str, name: str, symbol: Optional[str] = None
) -> Currency:
    currency = Currency(code=code, name=name, symbol=symbol)
    async with TestingSessionLocal() as session:
        session.add(currency)
        await session.commit()
        await session.refresh(currency)
        return currency


@pytest.mark.asyncio
async def test_create_conversion_rate_as_normal_user(
    client: AsyncClient, normal_user_token_headers: dict
):
    usd = await create_test_currency_for_rates(
        code="USX", name="US Dollar X"
    )  # Use different code to avoid conflicts if tests run in parallel or DB is not perfectly clean
    eur = await create_test_currency_for_rates(code="EUX", name="Euro X")

    rate_data = {"from_currency_id": usd.id, "to_currency_id": eur.id, "rate": 0.9}
    response = await client.post(
        "/api/v1/conversion-rates/", json=rate_data, headers=normal_user_token_headers
    )
    assert response.status_code == status.HTTP_201_CREATED  # Changed from 403
    data = response.json()
    assert data["rate"] == rate_data["rate"]
    assert data["from_currency"]["id"] == usd.id
    assert (
        data["from_currency"]["code"] == usd.code
    )  # Assuming usd object has code attribute
    assert data["to_currency"]["id"] == eur.id
    assert (
        data["to_currency"]["code"] == eur.code
    )  # Assuming eur object has code attribute
    assert "id" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_create_conversion_rate_same_currency(  # All users can attempt this
    client: AsyncClient,
    normal_user_token_headers: dict,
):
    jpy = await create_test_currency_for_rates(
        code="JPY", name="Japanese Yen", symbol="¥"
    )
    rate_data = {"from_currency_id": jpy.id, "to_currency_id": jpy.id, "rate": 1.0}
    response = await client.post(
        "/api/v1/conversion-rates/",
        json=rate_data,
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_create_conversion_rate_non_existent_from_currency(  # All users can attempt this
    client: AsyncClient,
    normal_user_token_headers: dict,
):
    cad = await create_test_currency_for_rates(code="CAD", name="Canadian Dollar")
    non_existent_id = 99999
    rate_data = {
        "from_currency_id": non_existent_id,
        "to_currency_id": cad.id,
        "rate": 0.75,
    }
    response = await client.post(
        "/api/v1/conversion-rates/",
        json=rate_data,
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_create_conversion_rate_non_existent_to_currency(  # All users can attempt this
    client: AsyncClient,
    normal_user_token_headers: dict,
):
    gbp = await create_test_currency_for_rates(code="GBP", name="British Pound")
    non_existent_id = 88888
    rate_data = {
        "from_currency_id": gbp.id,
        "to_currency_id": non_existent_id,
        "rate": 1.2,
    }
    response = await client.post(
        "/api/v1/conversion-rates/",
        json=rate_data,
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_create_conversion_rate_invalid_rate_zero(  # All users can attempt this
    client: AsyncClient,
    normal_user_token_headers: dict,
):
    aud = await create_test_currency_for_rates(code="AUD", name="Australian Dollar")
    nzd = await create_test_currency_for_rates(code="NZD", name="New Zealand Dollar")
    rate_data = {"from_currency_id": aud.id, "to_currency_id": nzd.id, "rate": 0}
    response = await client.post(
        "/api/v1/conversion-rates/",
        json=rate_data,
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_create_conversion_rate_invalid_rate_negative(  # All users can attempt this
    client: AsyncClient,
    normal_user_token_headers: dict,
):
    chf = await create_test_currency_for_rates(code="CHF", name="Swiss Franc")
    sek = await create_test_currency_for_rates(code="SEK", name="Swedish Krona")
    rate_data = {"from_currency_id": chf.id, "to_currency_id": sek.id, "rate": -0.5}
    response = await client.post(
        "/api/v1/conversion-rates/",
        json=rate_data,
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# Tests for GET /api/v1/conversion-rates/
@pytest.mark.asyncio
async def test_read_conversion_rates_empty(client: AsyncClient):  # Public endpoint
    response = await client.get("/api/v1/conversion-rates/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.asyncio
async def test_read_conversion_rates_with_data(  # Setup can be done by normal user
    client: AsyncClient,
    normal_user_token_headers: dict,
):
    # Create some currencies
    curr1 = await create_test_currency_for_rates(code="CR1", name="Rate Currency 1")
    curr2 = await create_test_currency_for_rates(code="CR2", name="Rate Currency 2")
    curr3 = await create_test_currency_for_rates(code="CR3", name="Rate Currency 3")

    # Create some rates - note that the default timestamp is utcnow()
    # To ensure order, we might need to create them with slight delays or manipulate timestamp if possible,
    # or rely on DB insertion order for this test if timestamps are too close.
    # For this test, we'll assume distinct enough timestamps or stable order for recent items.
    rate_data1 = {"from_currency_id": curr1.id, "to_currency_id": curr2.id, "rate": 1.1}
    await client.post(
        "/api/v1/conversion-rates/", json=rate_data1, headers=normal_user_token_headers
    )

    # A short delay might help ensure different timestamps if default_factory is second-level precision
    # import asyncio
    # await asyncio.sleep(0.01)

    rate_data2 = {"from_currency_id": curr2.id, "to_currency_id": curr3.id, "rate": 1.2}
    await client.post(
        "/api/v1/conversion-rates/", json=rate_data2, headers=normal_user_token_headers
    )

    response = await client.get("/api/v1/conversion-rates/")  # Public endpoint
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 2  # Could be more if other tests ran and didn't clean up fully

    # Check if the most recent ones are there (API orders by timestamp desc)
    # This assumes the last two created are the most recent.
    # A more robust test would sort by timestamp from response and check.
    codes_in_response = [
        (item["from_currency"]["code"], item["to_currency"]["code"]) for item in data
    ]
    assert (curr2.code, curr3.code) in codes_in_response
    assert (curr1.code, curr2.code) in codes_in_response
    if len(data) >= 2:  # Check order if possible
        # Assuming rate_data2 was created after rate_data1 and thus should appear first
        # This depends on the resolution of timestamp and speed of test execution.
        # A more robust way is to check exact timestamps if we controlled them.
        idx_cr2_cr3 = next(
            (
                i
                for i, item in enumerate(data)
                if item["from_currency"]["code"] == curr2.code
                and item["to_currency"]["code"] == curr3.code
            ),
            -1,
        )
        idx_cr1_cr2 = next(
            (
                i
                for i, item in enumerate(data)
                if item["from_currency"]["code"] == curr1.code
                and item["to_currency"]["code"] == curr2.code
            ),
            -1,
        )
        if idx_cr2_cr3 != -1 and idx_cr1_cr2 != -1:
            assert idx_cr2_cr3 < idx_cr1_cr2  # CR2->CR3 should be more recent


@pytest.mark.asyncio
async def test_read_conversion_rates_pagination(  # Setup can be done by normal user
    client: AsyncClient,
    normal_user_token_headers: dict,
):
    # Create a few currencies for pagination test
    curr_p1 = await create_test_currency_for_rates(code="CP1", name="Pag Cur 1")
    curr_p2 = await create_test_currency_for_rates(code="CP2", name="Pag Cur 2")
    # Create 3 rates
    await client.post(
        "/api/v1/conversion-rates/",
        json={
            "from_currency_id": curr_p1.id,
            "to_currency_id": curr_p2.id,
            "rate": 1.0,
        },
        headers=normal_user_token_headers,
    )  # Changed
    await client.post(
        "/api/v1/conversion-rates/",
        json={
            "from_currency_id": curr_p1.id,
            "to_currency_id": curr_p2.id,
            "rate": 1.1,
        },
        headers=normal_user_token_headers,
    )  # Changed
    await client.post(
        "/api/v1/conversion-rates/",
        json={
            "from_currency_id": curr_p1.id,
            "to_currency_id": curr_p2.id,
            "rate": 1.2,
        },
        headers=normal_user_token_headers,
    )  # Changed

    # Test limit
    response_limit_1 = await client.get(
        "/api/v1/conversion-rates/?limit=1"
    )  # Public endpoint
    assert response_limit_1.status_code == status.HTTP_200_OK
    data_limit_1 = response_limit_1.json()
    assert len(data_limit_1) == 1

    # Test skip (assuming at least 2 rates exist for CP1->CP2 from this test, plus any previous ones)
    # This part of test is a bit fragile due to data from other tests.
    # A better approach is to count total before adding, then add specific number, then test skip.
    # For now, just check if skip=1 returns fewer or different results if possible.
    response_all = await client.get("/api/v1/conversion-rates/")
    all_rates = response_all.json()

    if len(all_rates) > 1:
        response_skip_1 = await client.get("/api/v1/conversion-rates/?skip=1&limit=1")
        assert response_skip_1.status_code == status.HTTP_200_OK
        data_skip_1 = response_skip_1.json()
        assert len(data_skip_1) == 1
        assert (
            data_skip_1[0]["id"] != all_rates[0]["id"]
        )  # Assuming default order by timestamp desc


# Tests for GET /api/v1/conversion-rates/latest
@pytest.mark.asyncio
async def test_read_latest_conversion_rate_success(  # Setup can be done by normal user
    client: AsyncClient,
    normal_user_token_headers: dict,
):
    from datetime import datetime, timedelta, timezone

    curr_L1 = await create_test_currency_for_rates(code="CL1", name="Latest Cur 1")
    curr_L2 = await create_test_currency_for_rates(code="CL2", name="Latest Cur 2")

    # Create an older rate
    # We need to manually set timestamp for reliable testing of "latest"
    # The model uses default_factory=utcnow, so we can't directly set it via API.
    # This test will rely on the most recently POSTed rate for a pair being the "latest".

    await client.post(
        "/api/v1/conversion-rates/",
        json={
            "from_currency_id": curr_L1.id,
            "to_currency_id": curr_L2.id,
            "rate": 1.5,
        },
        headers=normal_user_token_headers,
    )  # Changed
    # await asyncio.sleep(0.01) # Ensure timestamp difference
    latest_rate_payload = {
        "from_currency_id": curr_L1.id,
        "to_currency_id": curr_L2.id,
        "rate": 1.55,
    }
    response_post_latest = await client.post(
        "/api/v1/conversion-rates/",
        json=latest_rate_payload,
        headers=normal_user_token_headers,
    )  # Changed
    assert response_post_latest.status_code == status.HTTP_201_CREATED
    latest_posted_id = response_post_latest.json()["id"]

    response = await client.get(
        f"/api/v1/conversion-rates/latest?from_code={curr_L1.code}&to_code={curr_L2.code}"
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["rate"] == 1.55
    assert data["from_currency"]["code"] == curr_L1.code
    assert data["to_currency"]["code"] == curr_L2.code
    assert data["id"] == latest_posted_id


@pytest.mark.asyncio
async def test_read_latest_conversion_rate_not_found(client: AsyncClient):
    response = await client.get(
        "/api/v1/conversion-rates/latest?from_code=NONEXIST1&to_code=NONEXIST2"
    )
    assert (
        response.status_code == status.HTTP_404_NOT_FOUND
    )  # Should be 404 if codes don't exist


@pytest.mark.asyncio
async def test_read_latest_conversion_rate_pair_not_found(client: AsyncClient):
    curr_NE1 = await create_test_currency_for_rates(code="CNE1", name="No Pair Cur 1")
    curr_NE2 = await create_test_currency_for_rates(code="CNE2", name="No Pair Cur 2")
    response = await client.get(
        f"/api/v1/conversion-rates/latest?from_code={curr_NE1.code}&to_code={curr_NE2.code}"
    )
    assert (
        response.status_code == status.HTTP_404_NOT_FOUND
    )  # Should be 404 if pair has no rates


@pytest.mark.asyncio
async def test_read_latest_conversion_rate_same_currency(client: AsyncClient):
    curr_SC = await create_test_currency_for_rates(
        code="CSAM", name="Same Currency Test"
    )
    response = await client.get(
        f"/api/v1/conversion-rates/latest?from_code={curr_SC.code}&to_code={curr_SC.code}"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
