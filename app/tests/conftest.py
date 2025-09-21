from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.database import get_session
from src.main import app
from src.models.models import User, Currency
from src.core.security import get_current_user

TEST_DATABASE_URL = "sqlite+aiosqlite:///file:testdb?mode=memory&cache=shared&uri=true"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)

TestingSessionLocal = sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


@pytest_asyncio.fixture(scope="function", autouse=True)
async def db_setup_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    yield


@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def async_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def normal_user(async_db_session: AsyncSession) -> User:
    user = User(
        clerk_id="user_2i5n5s3gH9Q8Q4G8b4k3d3f7j",
        username="testuser",
        email="testuser@example.com",
        full_name="Test User",
        email_verified=True,
    )
    async_db_session.add(user)
    await async_db_session.commit()
    await async_db_session.refresh(user)
    async_db_session.expunge(user)
    return user


@pytest_asyncio.fixture
async def authenticated_client(client: AsyncClient, normal_user: User) -> AsyncClient:
    async def override_get_current_user() -> User:
        return normal_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    client.headers["Authorization"] = "Bearer mock_token"
    return client


@pytest_asyncio.fixture
async def test_currency(async_db_session: AsyncSession) -> Currency:
    default_currency_code = "USD"
    stmt = select(Currency).where(Currency.code == default_currency_code)
    result = await async_db_session.exec(stmt)
    currency = result.first()
    if not currency:
        currency = Currency(code=default_currency_code, name="US Dollar", symbol="$")
        async_db_session.add(currency)
        await async_db_session.commit()
        await async_db_session.refresh(currency)
    return currency