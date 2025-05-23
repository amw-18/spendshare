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


from app.models.models import User # Added User model
from app.core.security import get_password_hash # Added get_password_hash

# Fixture to override the get_session dependency in the main app
async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
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
async def client() -> AsyncGenerator[AsyncClient, None]:
    # We need to ensure tables are created before client is used if db_setup_session isn't session-scoped autouse
    # However, with db_setup_session as autouse=True and scope="session", tables are handled globally.
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as ac:
        yield ac


# User Fixtures
@pytest_asyncio.fixture
async def normal_user(session: AsyncSession = TestingSessionLocal()) -> User: # Use TestingSessionLocal directly for fixture setup
    async with session.begin(): # Ensure session is active for db operations
        user = User(
            username="testuser",
            email="testuser@example.com",
            hashed_password=get_password_hash("password123"),
            is_admin=False,
        )
        session.add(user)
    await session.commit() # Commit the user to the database
    await session.refresh(user) # Refresh to get ID and other defaults
    return user

@pytest_asyncio.fixture
async def admin_user(session: AsyncSession = TestingSessionLocal()) -> User:
    async with session.begin():
        admin = User(
            username="adminuser",
            email="adminuser@example.com",
            hashed_password=get_password_hash("password123"),
            is_admin=True,
        )
        session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin


# Token Fixtures
@pytest_asyncio.fixture
async def normal_user_token_headers(client: AsyncClient, normal_user: User) -> dict[str, str]:
    login_data = {"username": normal_user.username, "password": "password123"}
    res = await client.post("/api/v1/users/token", data=login_data)
    if res.status_code != 200:
        pytest.fail(f"Failed to log in normal_user. Status: {res.status_code}, Response: {res.text}")
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest_asyncio.fixture
async def admin_user_token_headers(client: AsyncClient, admin_user: User) -> dict[str, str]:
    login_data = {"username": admin_user.username, "password": "password123"}
    res = await client.post("/api/v1/users/token", data=login_data)
    if res.status_code != 200:
        pytest.fail(f"Failed to log in admin_user. Status: {res.status_code}, Response: {res.text}")
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
