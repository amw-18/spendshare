import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy import inspect  # To check if tables exist
from sqlalchemy.ext.asyncio import AsyncEngine  # For type hinting

from .conftest import test_engine  # Import the test_engine from conftest


@pytest.mark.asyncio
async def test_read_root(client: AsyncClient):
    response = await client.get(
        "/api/v1/"
    )  # Assuming /api/v1 is the prefix for the root in main
    # If the root endpoint in main.py is just "/", then use client.get("/")
    # Let's adjust based on the main.py setup which has routers under /api/v1
    # and a separate root GET /

    # Test the actual root endpoint defined in main.py
    response_root = await client.get("/")
    assert response_root.status_code == status.HTTP_200_OK
    assert response_root.json() == {"message": "Welcome to the Expense Tracker API!"}


@pytest.mark.asyncio
async def test_db_tables_created_on_startup(client: AsyncClient):
    # The 'client' fixture implicitly handles app startup due to how AsyncClient works with FastAPI apps.
    # The lifespan event should have run. We can check if tables were created.
    # We need an async way to inspect the database.

    # We'll use the test_engine directly from conftest to inspect the DB.
    # This is a bit of a lower-level check but confirms table creation.

    async def table_exists(table_name: str, engine: AsyncEngine) -> bool:
        async with engine.connect() as connection:
            # For async, run_sync is used to run SQLAlchemy sync inspection code
            return await connection.run_sync(
                lambda sync_conn: inspect(sync_conn).has_table(table_name)
            )

    assert await table_exists("user", test_engine)  # Check for 'user' table
    assert await table_exists("group", test_engine)  # Check for 'group' table
    assert await table_exists("expense", test_engine)  # Check for 'expense' table
    assert await table_exists(
        "usergrouplink", test_engine
    )  # Check for 'usergrouplink' table
    assert await table_exists(
        "expenseparticipant", test_engine
    )  # Check for 'expenseparticipant' table


# You could also add a test for a known endpoint from one of the routers (e.g., /api/v1/users/)
# to ensure routers are included and working after startup.
@pytest.mark.asyncio
async def test_users_endpoint_available_after_startup(
    client: AsyncClient, admin_user_token_headers: dict[str, str]
):
    response = await client.get(
        "/api/v1/users/", headers=admin_user_token_headers
    )  # This is a known endpoint from users router
    assert response.status_code == status.HTTP_200_OK
    # The response might be an empty list if no users, which is fine for this test.
    assert isinstance(response.json(), list)
