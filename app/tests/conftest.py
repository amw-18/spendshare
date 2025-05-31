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
from src.models.models import ( # Restore global imports for fixture type hints and instantiation
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
TEST_DATABASE_URL = "sqlite+aiosqlite:///file:testdb?mode=memory&cache=shared&uri=true" # Using shared in-memory SQLite for tests

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
        is_admin=False,
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


@pytest_asyncio.fixture
async def admin_user() -> AsyncGenerator[User, None]:
    admin = User(
        username="adminuser",
        email="adminuser_admin@example.com",
        hashed_password=get_password_hash("password123"),
        is_admin=True,
    )
    async with TestingSessionLocal() as session:
        session.add(admin)
        await session.commit()
        await session.refresh(admin)

        yield admin

        # Teardown
        admin_in_session = await session.get(User, admin.id)
        if admin_in_session:
            stmt_expenses = select(Expense).where(
                Expense.paid_by_user_id == admin_in_session.id
            )
            result_expenses = await session.exec(stmt_expenses)
            expenses_paid_by_user = result_expenses.all()

            for expense_obj in expenses_paid_by_user:
                stmt_participants = select(ExpenseParticipant).where(
                    ExpenseParticipant.expense_id == expense_obj.id
                )
                result_participants = await session.exec(stmt_participants)
                participants = result_participants.all()
                for participant in participants:
                    await session.delete(participant)
                await session.delete(expense_obj)

            await session.delete(admin_in_session)
            await session.commit()


# Currency Fixture
@pytest_asyncio.fixture
async def test_currency(async_db_session: AsyncSession) -> Currency:
    currency = Currency(code="USD", name="US Dollar", symbol="$")
    async_db_session.add(currency)
    await async_db_session.commit()
    await async_db_session.refresh(currency)
    return currency


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


@pytest_asyncio.fixture
async def admin_user_token_headers(
    client: AsyncClient, admin_user: User
) -> dict[str, str]:
    login_data = {"username": admin_user.username, "password": "password123"}
    res = await client.post("/api/v1/users/token", data=login_data)
    if res.status_code != 200:
        pytest.fail(
            f"Failed to log in admin_user. Status: {res.status_code}, Response: {res.text}"
        )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
