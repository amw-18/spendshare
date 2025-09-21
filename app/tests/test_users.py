import pytest
from httpx import AsyncClient
from fastapi import status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.models import User


@pytest.mark.asyncio
async def test_get_current_user(authenticated_client: AsyncClient, normal_user: User):
    response = await authenticated_client.get("/api/v1/users/me")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == normal_user.username
    assert data["email"] == normal_user.email
    assert data["clerk_id"] == normal_user.clerk_id


@pytest.mark.asyncio
async def test_update_current_user(authenticated_client: AsyncClient, normal_user: User, async_db_session: AsyncSession):
    new_username = "newusername"
    new_full_name = "New Full Name"
    response = await authenticated_client.put(
        "/api/v1/users/me",
        json={"username": new_username, "full_name": new_full_name},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == new_username
    assert data["full_name"] == new_full_name

    # Verify in DB
    updated_user = await async_db_session.get(User, normal_user.id)
    assert updated_user.username == new_username
    assert updated_user.full_name == new_full_name


@pytest.mark.asyncio
async def test_search_users(authenticated_client: AsyncClient, normal_user: User):
    response = await authenticated_client.get(f"/api/v1/users/search?query={normal_user.username}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) > 0
    assert data[0]["username"] == normal_user.username


@pytest.mark.asyncio
async def test_get_user_by_id(authenticated_client: AsyncClient, normal_user: User):
    response = await authenticated_client.get(f"/api/v1/users/{normal_user.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == normal_user.username


@pytest.mark.asyncio
async def test_unauthenticated_access(client: AsyncClient):
    response = await client.get("/api/v1/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = await client.put("/api/v1/users/me", json={})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = await client.get("/api/v1/users/search?query=test")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = await client.get("/api/v1/users/1")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED