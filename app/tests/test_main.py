import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.conftest import test_engine


@pytest.mark.asyncio
async def test_read_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Welcome to the Expense Tracker API!"}


@pytest.mark.asyncio
async def test_db_tables_created_on_startup():
    async def table_exists(table_name: str, engine: AsyncEngine) -> bool:
        async with engine.connect() as connection:
            return await connection.run_sync(
                lambda sync_conn: inspect(sync_conn).has_table(table_name)
            )

    assert await table_exists("user", test_engine)
    assert await table_exists("group", test_engine)
    assert await table_exists("expense", test_engine)
    assert await table_exists("usergrouplink", test_engine)
    assert await table_exists("expenseparticipant", test_engine)


@pytest.mark.asyncio
async def test_authenticated_endpoint_available(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/v1/users/me")
    assert response.status_code == status.HTTP_200_OK
    assert "username" in response.json()