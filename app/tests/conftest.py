import pytest
import os
from typing import AsyncGenerator
import pytest_asyncio  # For async fixtures
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app  # Your FastAPI application instance
from app.db.database import get_session  # The overridden get_session for testing

TEST_DATABASE_PATH = "./test_app_temp.db"
# Use a separate SQLite database for testing
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DATABASE_PATH}"

test_engine = create_async_engine(
    TEST_DATABASE_URL, echo=False, future=True
)  # echo=False for cleaner test output

# Async sessionmaker for tests
TestingSessionLocal = sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


# Fixture to override the get_session dependency in the main app
async def override_get_session() -> AsyncGenerator[AsyncSession]:
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


@pytest_asyncio.fixture(scope="session", autouse=True)
async def db_setup_session():
    # This fixture runs once per session.
    # Create tables before tests run, and drop them after.
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    # if os.path.exists(TEST_DATABASE_PATH):
    #     os.remove(TEST_DATABASE_PATH)


@pytest_asyncio.fixture(
    scope="function"
)  # "function" scope for client to ensure clean state per test
async def client() -> AsyncGenerator[AsyncClient]:
    # We need to ensure tables are created before client is used if db_setup_session isn't session-scoped autouse
    # However, with db_setup_session as autouse=True and scope="session", tables are handled globally.
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as ac:
        yield ac
