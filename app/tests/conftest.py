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

# Imports needed for the new fixtures from test_users.py
from fastapi import status, HTTPException # For status codes and exceptions
from src.models import schemas # For UserRegister, MessageResponse etc.
# from src.core import email # Not directly calling email functions, but mocking them
from src.core.security import get_password_hash # Already here, but good to note

from datetime import datetime, timedelta, timezone # For time manipulation
import secrets # For unique naming
from unittest.mock import patch, AsyncMock # For mocking email sending
from typing import Dict, Any # For type hinting fixture data (Dict, Any)
# End imports for new fixtures


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
        username="testuser_normal_fixture",
        email="testuser_normal_fixture@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test Normal User Fixture",
        email_verified=True,
        email_verification_token=None, # Explicitly None
        email_verification_token_expires_at=None, # Explicitly None
        new_email_pending_verification=None, # Explicitly None
        email_change_token=None, # Explicitly None
        email_change_token_expires_at=None # Explicitly None
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
            full_name=f"{username} FullName", # Ensure all required fields are present
            email_verified=True, # Assume factory creates verified users for simplicity
            email_verification_token=None,
            email_verification_token_expires_at=None,
            new_email_pending_verification=None,
            email_change_token=None,
            email_change_token_expires_at=None,
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

# --- Helper functions moved from test_users.py ---
async def get_user_by_email_from_db(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def get_user_by_username_from_db(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()

async def get_user_by_id_from_db(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

# --- Fixtures moved from test_users.py ---

# Note: Changed get_test_db to async_db_session (which is already defined in this conftest.py)
@pytest_asyncio.fixture(scope="function")
@patch('app.src.core.email.send_verification_email', new_callable=AsyncMock)
async def verified_user_data_and_headers(mock_send_reg_email: AsyncMock, client: AsyncClient, async_db_session: AsyncSession) -> AsyncGenerator[Dict[str, Any], None]:
    unique_suffix = secrets.token_hex(4)
    raw_password = "password123"
    user_data = {
        "username": f"verified_{unique_suffix}",
        "email": f"verified_{unique_suffix}@example.com",
        "password": raw_password,
        "full_name": f"Verified {unique_suffix.capitalize()}"
    }

    # Register user
    register_response = await client.post("/api/v1/users/register", json=user_data)
    assert register_response.status_code == status.HTTP_202_ACCEPTED, f"Registration failed: {register_response.text}"
    mock_send_reg_email.assert_called_once() # From the registration step

    # Retrieve token from DB
    user_in_db = await get_user_by_email_from_db(async_db_session, user_data["email"])
    assert user_in_db is not None, "User not found in DB after registration"
    assert user_in_db.email_verification_token is not None, "Email verification token not set"
    verification_token = user_in_db.email_verification_token

    # Verify email
    verify_response = await client.get(f"/api/v1/users/verify-email?token={verification_token}")
    assert verify_response.status_code == status.HTTP_200_OK, f"Email verification failed: {verify_response.text}"

    # Login
    login_payload = {"username": user_data["username"], "password": user_data["password"]}
    login_response = await client.post("/api/v1/users/token", data=login_payload)
    assert login_response.status_code == status.HTTP_200_OK, f"Login failed: {login_response.text}"
    token_data = login_response.json()
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}

    # Fetch the full user model instance again to ensure it's updated
    final_user_in_db = await get_user_by_email_from_db(async_db_session, user_data["email"])
    assert final_user_in_db is not None, "User not found in DB after verification"
    assert final_user_in_db.email_verified is True, "Email not marked as verified"

    yield {
        "user": final_user_in_db,
        "headers": headers,
        "raw_password": raw_password,
        "email": user_data["email"],
        "username": user_data["username"],
        "full_name": user_data["full_name"],
        "id": final_user_in_db.id
    }


@pytest_asyncio.fixture(scope="function")
async def test_user_2(new_user_with_token_factory) -> User:
    """Provides a second distinct user model instance."""
    data = await new_user_with_token_factory()
    return data["user"]

@pytest_asyncio.fixture(scope="function")
async def test_user_2_with_token(new_user_with_token_factory) -> dict:
    """Provides a second distinct user with their token headers."""
    return await new_user_with_token_factory()

@pytest_asyncio.fixture(scope="function")
async def test_user_3_with_token(new_user_with_token_factory) -> dict:
    """Provides a third distinct user with their token headers."""
    return await new_user_with_token_factory()


@pytest_asyncio.fixture(scope="function")
async def test_group(
    async_db_session: AsyncSession, normal_user: User, unique_id_generator
) -> Group:
    """Creates a group owned by normal_user."""
    group = Group(
        name=f"Test Group {unique_id_generator()}",
        created_by_user_id=normal_user.id,
        description="A test group",
    )
    async_db_session.add(group)
    # Add normal_user as a member automatically upon creation by them (if not handled by ORM)
    # Assuming UserGroupLink is needed if not automatically created by Relationship back_populates
    # However, the Group model's 'members' Relationship might require explicit linking for creator.
    # Let's assume for now that group creation implies creator is a member, or test setup handles it.
    # For safety, one might explicitly add:
    # link = UserGroupLink(user_id=normal_user.id, group_id=group.id) # group.id is None before commit
    # async_db_session.add(link)
    await async_db_session.commit()
    await async_db_session.refresh(group)

    # Manually add creator as member if not handled by ORM relationships automatically on group creation
    # Check if user is already a member (e.g. via back_populates or event listeners)
    # This is often handled by adding the creator to the members list before commit,
    # or the relationship handles it. For SQLModel, it often requires explicit link model instances.
    # Let's ensure the creator is linked.
    # Re-fetch to ensure group.id is available
    # await async_db_session.refresh(group) # Already did
    # Check if link exists
    link_stmt = select(UserGroupLink).where(UserGroupLink.user_id == normal_user.id, UserGroupLink.group_id == group.id)
    existing_link_result = await async_db_session.exec(link_stmt)
    if not existing_link_result.first():
        creator_link = UserGroupLink(user_id=normal_user.id, group_id=group.id)
        async_db_session.add(creator_link)
        await async_db_session.commit()
        await async_db_session.refresh(group) # Refresh group to potentially update its .members

    return group

@pytest_asyncio.fixture(scope="function")
async def test_group_shared_with_user2(
    async_db_session: AsyncSession, normal_user: User, test_user_2: User, unique_id_generator
) -> Group:
    """Creates a group by normal_user and adds test_user_2 as a member."""
    group_name = f"Shared Group {unique_id_generator()}"
    group = Group(
        name=group_name,
        created_by_user_id=normal_user.id,
        description="A test group shared between normal_user and test_user_2",
    )
    async_db_session.add(group)
    await async_db_session.commit() # Commit to get group.id
    await async_db_session.refresh(group)

    # Add normal_user (creator) as member
    link_creator = UserGroupLink(user_id=normal_user.id, group_id=group.id)
    async_db_session.add(link_creator)

    # Add test_user_2 as member
    link_user2 = UserGroupLink(user_id=test_user_2.id, group_id=group.id)
    async_db_session.add(link_user2)

    await async_db_session.commit()
    await async_db_session.refresh(group) # To load members if relationship is configured
    # To be absolutely sure members are loaded for tests that need it immediately:
    # stmt = select(Group).where(Group.id == group.id).options(selectinload(Group.members))
    # result = await async_db_session.exec(stmt)
    # group = result.one()
    return group


@pytest_asyncio.fixture(scope="function")
@patch('app.src.core.email.send_verification_email', new_callable=AsyncMock)
async def pending_user_and_token(mock_send_email: AsyncMock, client: AsyncClient, async_db_session: AsyncSession) -> AsyncGenerator[Dict[str, Any], None]:
    unique_suffix = secrets.token_hex(4)
    raw_password = "password123"
    user_data = {
        "username": f"pending_{unique_suffix}",
        "email": f"pending_{unique_suffix}@example.com",
        "password": raw_password,
        "full_name": f"Pending {unique_suffix.capitalize()}"
    }

    register_response = await client.post("/api/v1/users/register", json=user_data)
    assert register_response.status_code == status.HTTP_202_ACCEPTED, f"Pending user registration failed: {register_response.text}"
    mock_send_email.assert_called_once()

    user_in_db = await get_user_by_email_from_db(async_db_session, user_data["email"])
    assert user_in_db is not None, "Pending user not found in DB"
    assert user_in_db.email_verification_token is not None, "Pending user verification token not set"
    assert user_in_db.email_verified is False, "Pending user should not be verified"

    yield {
        "email": user_data["email"],
        "username": user_data["username"],
        "password": raw_password,
        "token": user_in_db.email_verification_token,
        "full_name": user_data["full_name"],
        "id": user_in_db.id,
        "user_model": user_in_db # include the model for direct db manipulations if needed
    }
