from typing import AsyncGenerator

import pytest
import pytest_asyncio  # For async fixtures
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

# import os # No longer needed after switching to in-memory DB
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.database import get_session  # The overridden get_session for testing
from src.main import app  # Your FastAPI application instance


from src.core.security import get_password_hash  # Added get_password_hash
from src.models.models import (  # Restore global imports for fixture type hints and instantiation
    User,
    Group,
    UserGroupLink,
    Expense,
    ExpenseParticipant,
    Currency,
    ConversionRate,
)

# TEST_DATABASE_PATH = "./test_app_temp.db" # Using in-memory database for tests
# Use a separate SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///file:testdb?mode=memory&cache=shared&uri=true"  # Using shared in-memory SQLite for tests

test_engine = create_async_engine(
    TEST_DATABASE_URL, echo=False, future=True
)  # echo=False for cleaner test output

# Async sessionmaker for tests
TestingSessionLocal = sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


# Fixture to override the get_session dependency in the main app
async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


@pytest_asyncio.fixture(scope="function", autouse=True)
async def db_setup_session():
    # Using in-memory database, no file pre-cleanup needed.
    # SQLModel.metadata.clear() # Clear global metadata

    # Models are already imported globally at the top of this file.
    # SQLModel.metadata.create_all will use those globally registered models.
    # No need to re-import here if global imports are comprehensive and correct.

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    # Using in-memory database, no file post-cleanup needed.


@pytest_asyncio.fixture(
    scope="function"
)  # "function" scope for client to ensure clean state per test
async def client() -> AsyncGenerator[AsyncClient, None]:
    # We need to ensure tables are created before client is used if db_setup_session isn't session-scoped autouse
    # However, with db_setup_session as autouse=True and scope="session", tables are handled globally.
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def async_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


# User Fixtures
@pytest_asyncio.fixture
async def normal_user() -> AsyncGenerator[User, None]:
    user = User(
        username="testuser",
        email="testuser_normal@example.com",
        hashed_password=get_password_hash("password123"),
    )
    async with TestingSessionLocal() as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)

        yield user

        # Teardown: Ensure user is re-fetched in this session context if necessary
        user_in_session = await session.get(User, user.id)
        if user_in_session:
            # Fetch and delete expenses paid by this user
            stmt_expenses = select(Expense).where(
                Expense.paid_by_user_id == user_in_session.id
            )
            result_expenses = await session.exec(stmt_expenses)
            expenses_paid_by_user = result_expenses.all()

            for expense_obj in expenses_paid_by_user:
                # Delete related ExpenseParticipant entries
                stmt_participants = select(ExpenseParticipant).where(
                    ExpenseParticipant.expense_id == expense_obj.id
                )
                result_participants = await session.exec(stmt_participants)
                participants = result_participants.all()
                for participant in participants:
                    await session.delete(participant)
                await session.delete(expense_obj)

            await session.delete(user_in_session)
            await session.commit()


# Currency Fixture / Factory
@pytest_asyncio.fixture
async def test_currency(async_db_session: AsyncSession) -> Currency:  # Default currency
    default_currency_code = "USD"
    # Attempt to fetch existing default currency to avoid conflicts if tests run in a way that state leaks (should not happen with function scope db)
    stmt = select(Currency).where(Currency.code == default_currency_code)
    result = await async_db_session.exec(stmt)
    currency = result.first()
    if not currency:
        currency = Currency(code=default_currency_code, name="US Dollar", symbol="$")
        async_db_session.add(currency)
        await async_db_session.commit()
        await async_db_session.refresh(currency)
    return currency


@pytest_asyncio.fixture
async def currency_factory(async_db_session: AsyncSession, unique_id_generator):
    created_currencies = []

    async def _factory(
        code: str = None, name: str = None, symbol: str = None
    ) -> Currency:
        if code is None:
            code = f"C{unique_id_generator()}"  # Generate unique code if not provided

        # Check if currency with this code already exists (important if factory is called multiple times with same code)
        stmt = select(Currency).where(Currency.code == code)
        result = await async_db_session.exec(stmt)
        existing_currency = result.first()
        if existing_currency:
            # print(f"Factory returning existing currency: {code}")
            return existing_currency

        _name = name or f"{code} Name"
        _symbol = symbol or f"{code[0]}"

        new_currency = Currency(code=code, name=_name, symbol=_symbol)
        async_db_session.add(new_currency)
        await async_db_session.commit()
        await async_db_session.refresh(new_currency)
        created_currencies.append(new_currency)
        # print(f"Factory created new currency: {new_currency.code}")
        return new_currency

    yield _factory

    # Teardown: delete currencies created by this factory instance if necessary,
    # though function-scoped db_setup_session should handle full cleanup.
    # This is more for safety or if db scope changes.
    # for cur in created_currencies:
    #     try:
    #         await async_db_session.delete(cur)
    #     except Exception as e:
    #         # print(f"Error deleting currency {cur.code} in factory teardown: {e}")
    #         pass # Ignore errors if already deleted or session closed
    # await async_db_session.commit()


# Fixture to generate unique IDs for usernames, emails, etc. (moved from test_transactions.py)
@pytest.fixture(scope="session")
def unique_id_generator():
    count = 0

    def _generate_id():
        nonlocal count
        count += 1
        return count

    return _generate_id


# Token Fixtures
@pytest_asyncio.fixture
async def normal_user_token_headers(
    client: AsyncClient, normal_user: User
) -> dict[str, str]:
    login_data = {"username": normal_user.username, "password": "password123"}
    res = await client.post("/api/v1/users/token", data=login_data)
    if res.status_code != 200:
        pytest.fail(
            f"Failed to log in normal_user. Status: {res.status_code}, Response: {res.text}"
        )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# Helper fixture (factory pattern) to create a new user and return user model and token headers
@pytest_asyncio.fixture
async def new_user_with_token_factory(
    client: AsyncClient, async_db_session: AsyncSession, unique_id_generator
):
    async def _factory():
        username = f"testuser_{unique_id_generator()}"
        email = f"{username}@example.com"
        password = "password123"

        user_create = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
        )
        async_db_session.add(user_create)
        await async_db_session.commit()
        await async_db_session.refresh(user_create)

        login_data = {"username": username, "password": password}
        res = await client.post("/api/v1/users/token", data=login_data)
        assert res.status_code == 200, (
            f"Failed to log in new_user {username}. Response: {res.text}"
        )
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        return {"user": user_create, "headers": headers, "password": password}

    return _factory
