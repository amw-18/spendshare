import pytest
from httpx import AsyncClient
from fastapi import status
from unittest.mock import patch, AsyncMock
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.src.models.models import BetaInterest
from app.src.models.schemas import BetaInterestCreate
from app.src.config import settings # To access settings.SUPPORT_EMAIL

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio

async def test_register_interest_success(
    client: AsyncClient,
    async_db_session: AsyncSession # Use this fixture for DB assertions
):
    payload_dict = {"email": "test@example.com", "description": "I am very interested!"}

    with patch("app.src.routers.beta.send_beta_interest_email", autospec=True) as mock_send_email:
        response = await client.post("/beta/interest", json=payload_dict)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"message": "Successfully registered interest."}

    # Verify database record
    stmt = select(BetaInterest).where(BetaInterest.email == payload_dict["email"])
    result = await async_db_session.exec(stmt)
    db_record = result.one_or_none()

    assert db_record is not None
    assert db_record.email == payload_dict["email"]
    assert db_record.description == payload_dict["description"]

    # Verify email was called
    mock_send_email.assert_called_once_with(
        email_to=settings.SUPPORT_EMAIL,
        interested_email=payload_dict["email"],
        description=payload_dict["description"],
    )

async def test_register_interest_success_no_description(
    client: AsyncClient,
    async_db_session: AsyncSession
):
    payload_dict = {"email": "test_nodesc@example.com"} # No description

    with patch("app.src.routers.beta.send_beta_interest_email", autospec=True) as mock_send_email:
        response = await client.post("/beta/interest", json=payload_dict)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"message": "Successfully registered interest."}

    # Verify database record
    stmt = select(BetaInterest).where(BetaInterest.email == payload_dict["email"])
    result = await async_db_session.exec(stmt)
    db_record = result.one_or_none()

    assert db_record is not None
    assert db_record.email == payload_dict["email"]
    assert db_record.description is None # Description should be None

    # Verify email was called
    mock_send_email.assert_called_once_with(
        email_to=settings.SUPPORT_EMAIL,
        interested_email=payload_dict["email"],
        description=None, # Description is None
    )

async def test_register_interest_invalid_email(client: AsyncClient):
    payload_dict = {"email": "not-an-email", "description": "Test"}
    response = await client.post("/beta/interest", json=payload_dict)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Optionally, check the detail of the error
    error_detail = response.json()["detail"][0]
    assert error_detail["type"] == "value_error" # Pydantic v2 uses "value_error" for EmailStr
    assert "invalid email format" in error_detail["msg"].lower()
    assert error_detail["loc"] == ["body", "email"]


async def test_register_interest_missing_email(client: AsyncClient):
    payload_dict = {"description": "Test"} # Email is missing
    response = await client.post("/beta/interest", json=payload_dict)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_detail = response.json()["detail"][0]
    assert error_detail["type"] == "missing"
    assert error_detail["loc"] == ["body", "email"]

async def test_register_interest_db_error_on_add(client: AsyncClient):
    payload_dict = {"email": "db_error_test@example.com", "description": "DB error test"}

    # Mock db.add to raise SQLAlchemyError
    # We need to patch 'db.add' where it's used, which is inside the endpoint.
    # The actual session object 'db' is an instance of AsyncSession.
    # So we patch 'AsyncSession.add'.
    with patch("app.src.routers.beta.AsyncSession.add", side_effect=SQLAlchemyError("Simulated DB error on add")) as mock_db_add, \
         patch("app.src.routers.beta.send_beta_interest_email") as mock_send_email: # also mock email to prevent it from running

        response = await client.post("/beta/interest", json=payload_dict)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "An error occurred while registering interest. Please try again later."}
    mock_db_add.assert_called_once() # Ensure db.add was called
    mock_send_email.assert_not_called() # Email should not be sent if DB operation fails


async def test_register_interest_db_error_on_commit(client: AsyncClient):
    payload_dict = {"email": "db_commit_error@example.com", "description": "DB commit error test"}

    # Mock db.commit to raise SQLAlchemyError
    # Similar to above, we patch 'AsyncSession.commit'.
    # We use AsyncMock for async methods if we need to inspect awaitables or return values from the mock.
    # Here, side_effect is enough.
    with patch("app.src.routers.beta.AsyncSession.commit", side_effect=SQLAlchemyError("Simulated DB error on commit")) as mock_db_commit, \
         patch("app.src.routers.beta.send_beta_interest_email") as mock_send_email:

        response = await client.post("/beta/interest", json=payload_dict)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "An error occurred while registering interest. Please try again later."}
    mock_db_commit.assert_called_once() # Ensure db.commit was called
    mock_send_email.assert_not_called()
