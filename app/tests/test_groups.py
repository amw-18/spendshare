import pytest
from httpx import AsyncClient
from fastapi import status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.models import User, Group


@pytest.mark.asyncio
async def test_create_group(authenticated_client: AsyncClient, normal_user: User):
    group_name = "Test Group"
    response = await authenticated_client.post("/api/v1/groups/", json={"name": group_name})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == group_name
    assert data["created_by_user_id"] == normal_user.id


@pytest.mark.asyncio
async def test_get_groups(authenticated_client: AsyncClient, normal_user: User):
    await authenticated_client.post("/api/v1/groups/", json={"name": "Test Group 1"})
    await authenticated_client.post("/api/v1/groups/", json={"name": "Test Group 2"})

    response = await authenticated_client.get("/api/v1/groups/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_get_group(authenticated_client: AsyncClient, normal_user: User):
    create_response = await authenticated_client.post("/api/v1/groups/", json={"name": "Test Group"})
    group_id = create_response.json()["id"]

    response = await authenticated_client.get(f"/api/v1/groups/{group_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == group_id


@pytest.mark.asyncio
async def test_update_group(authenticated_client: AsyncClient, normal_user: User):
    create_response = await authenticated_client.post("/api/v1/groups/", json={"name": "Test Group"})
    group_id = create_response.json()["id"]

    new_name = "Updated Test Group"
    response = await authenticated_client.put(f"/api/v1/groups/{group_id}", json={"name": new_name})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == new_name


@pytest.mark.asyncio
async def test_delete_group(authenticated_client: AsyncClient, normal_user: User):
    create_response = await authenticated_client.post("/api/v1/groups/", json={"name": "Test Group"})
    group_id = create_response.json()["id"]

    response = await authenticated_client.delete(f"/api/v1/groups/{group_id}")
    assert response.status_code == status.HTTP_200_OK

    get_response = await authenticated_client.get(f"/api/v1/groups/{group_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_add_group_member(authenticated_client: AsyncClient, normal_user: User, async_db_session: AsyncSession):
    create_response = await authenticated_client.post("/api/v1/groups/", json={"name": "Test Group"})
    group_id = create_response.json()["id"]

    new_user = User(
        clerk_id="user_2i5n5s3gH9Q8Q4G8b4k3d3f7k",
        username="newuser",
        email="newuser@example.com",
    )
    async_db_session.add(new_user)
    await async_db_session.commit()
    await async_db_session.refresh(new_user)

    response = await authenticated_client.post(f"/api/v1/groups/{group_id}/members/{new_user.id}")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_remove_group_member(authenticated_client: AsyncClient, normal_user: User, async_db_session: AsyncSession):
    create_response = await authenticated_client.post("/api/v1/groups/", json={"name": "Test Group"})
    group_id = create_response.json()["id"]

    new_user = User(
        clerk_id="user_2i5n5s3gH9Q8Q4G8b4k3d3f7k",
        username="newuser",
        email="newuser@example.com",
    )
    async_db_session.add(new_user)
    await async_db_session.commit()
    await async_db_session.refresh(new_user)

    await authenticated_client.post(f"/api/v1/groups/{group_id}/members/{new_user.id}")

    response = await authenticated_client.delete(f"/api/v1/groups/{group_id}/members/{new_user.id}")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_group_authorization(client: AsyncClient, normal_user: User, async_db_session: AsyncSession):
    # Create a group with normal_user
    group = Group(name="Test Group", created_by_user_id=normal_user.id)
    async_db_session.add(group)
    await async_db_session.commit()
    await async_db_session.refresh(group)

    # Create another user
    other_user = User(
        clerk_id="user_2i5n5s3gH9Q8Q4G8b4k3d3f7l",
        username="otheruser",
        email="otheruser@example.com",
    )
    async_db_session.add(other_user)
    await async_db_session.commit()
    await async_db_session.refresh(other_user)

    # Override get_current_user with other_user
    async def override_get_current_user() -> User:
        return other_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    client.headers["Authorization"] = "Bearer mock_token"

    # other_user should not be able to get the group
    response = await client.get(f"/api/v1/groups/{group.id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN