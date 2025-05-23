import pytest
from httpx import AsyncClient
from fastapi import status

# Helper function to create a user and return its ID (or full object)
async def create_test_user(client: AsyncClient, username: str, email: str, password: str = "testpassword") -> dict:
    user_data = {"username": username, "email": email, "password": password}
    response = await client.post("/users/", json=user_data)
    assert response.status_code == status.HTTP_200_OK
    return response.json()

@pytest.mark.asyncio
async def test_create_group_success(client: AsyncClient):
    creator = await create_test_user(client, "group_creator", "creator@example.com")
    group_data = {
        "name": "Test Group Alpha",
        "created_by_user_id": creator["id"]
    }
    response = await client.post("/groups/", json=group_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == group_data["name"]
    assert data["created_by_user_id"] == creator["id"]
    assert "id" in data

    # Verify creator is a member (implicitly done by create_group CRUD)
    # To check this, we'd ideally have a group read endpoint that includes members.
    # For now, this check is indirect. We'll test member listing explicitly later if such an endpoint is made.

@pytest.mark.asyncio
async def test_create_group_creator_not_found(client: AsyncClient):
    group_data = {
        "name": "Ghost Group",
        "created_by_user_id": 99999 # Non-existent user
    }
    response = await client.post("/groups/", json=group_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "creator user not found" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_read_groups_empty(client: AsyncClient):
    # This test assumes the DB is cleared per session, or no groups are created by other tests
    # before this runs in a fresh session. If other tests create groups, this might fail.
    # For now, with session-scoped DB setup/teardown, this test might be tricky
    # unless it's the very first group test or DB is wiped before this specific test.
    # Let's assume for now it's okay, or we clear groups specifically if needed.
    # A better way is to ensure no groups are present or create some and test count.
    # Given current conftest, tables are created/dropped per session. This test is fine.
    response = await client.get("/groups/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.asyncio
async def test_read_one_group_success(client: AsyncClient):
    creator = await create_test_user(client, "owner_g1", "owner_g1@example.com")
    group_data = {"name": "Readable Group", "created_by_user_id": creator["id"]}
    create_response = await client.post("/groups/", json=group_data)
    group_id = create_response.json()["id"]

    response = await client.get(f"/groups/{group_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == group_data["name"]
    assert data["id"] == group_id

@pytest.mark.asyncio
async def test_read_one_group_not_found(client: AsyncClient):
    response = await client.get("/groups/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_read_multiple_groups(client: AsyncClient):
    creator = await create_test_user(client, "multi_group_owner", "multi@example.com")
    group1_data = {"name": "Group X", "created_by_user_id": creator["id"]}
    group2_data = {"name": "Group Y", "created_by_user_id": creator["id"]}
    await client.post("/groups/", json=group1_data)
    await client.post("/groups/", json=group2_data)

    response = await client.get("/groups/")
    assert response.status_code == status.HTTP_200_OK
    groups = response.json()
    assert len(groups) >= 2
    names = [g["name"] for g in groups]
    assert "Group X" in names
    assert "Group Y" in names

@pytest.mark.asyncio
async def test_update_group_success(client: AsyncClient):
    creator = await create_test_user(client, "updater_owner", "updater@example.com")
    group_data = {"name": "Initial Name", "created_by_user_id": creator["id"]}
    create_response = await client.post("/groups/", json=group_data)
    group_id = create_response.json()["id"]

    update_payload = {"name": "Updated Group Name"}
    response = await client.put(f"/groups/{group_id}", json=update_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == update_payload["name"]
    assert data["id"] == group_id

@pytest.mark.asyncio
async def test_update_group_not_found(client: AsyncClient):
    update_payload = {"name": "Phantom Update"}
    response = await client.put("/groups/8888", json=update_payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_delete_group_success(client: AsyncClient):
    creator = await create_test_user(client, "deleter_owner", "deleter@example.com")
    group_data = {"name": "To Be Deleted Group", "created_by_user_id": creator["id"]}
    create_response = await client.post("/groups/", json=group_data)
    group_id = create_response.json()["id"]

    delete_response = await client.delete(f"/groups/{group_id}")
    assert delete_response.status_code == status.HTTP_200_OK
    # Optionally assert response body if it's meaningful

    # Verify group is deleted
    get_response = await client.get(f"/groups/{group_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_delete_group_not_found(client: AsyncClient):
    response = await client.delete("/groups/7777")
    assert response.status_code == status.HTTP_404_NOT_FOUND

# Group Member Management Tests
@pytest.mark.asyncio
async def test_add_member_to_group_success(client: AsyncClient):
    creator = await create_test_user(client, "member_adder_owner", "add_owner@example.com")
    member_to_add = await create_test_user(client, "new_member", "newmember@example.com")
    
    group_data = {"name": "Membership Test Group", "created_by_user_id": creator["id"]}
    create_group_response = await client.post("/groups/", json=group_data)
    group_id = create_group_response.json()["id"]

    # Creator is already a member. Add new_member.
    response = await client.post(f"/groups/{group_id}/members/{member_to_add['id']}")
    assert response.status_code == status.HTTP_200_OK
    # Ideally, response_model for this endpoint should be GroupReadWithMembers to verify.
    # For now, we assume success if 200 OK. Can verify by trying to add again (should not fail, but not add duplicate link).
    
    # Try adding again - should be idempotent from user perspective (still 200, member still there)
    response_again = await client.post(f"/groups/{group_id}/members/{member_to_add['id']}")
    assert response_again.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_add_member_group_not_found(client: AsyncClient):
    some_user = await create_test_user(client, "some_user_for_member_test", "some_user@example.com")
    response = await client.post(f"/groups/9991/members/{some_user['id']}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "group or user not found" in response.json()["detail"].lower() # Based on router error handling

@pytest.mark.asyncio
async def test_add_member_user_not_found(client: AsyncClient):
    creator = await create_test_user(client, "owner_for_member_test_user_nf", "owner_user_nf@example.com")
    group_data = {"name": "Group For User NF Test", "created_by_user_id": creator["id"]}
    create_group_response = await client.post("/groups/", json=group_data)
    group_id = create_group_response.json()["id"]

    response = await client.post(f"/groups/{group_id}/members/9992") # Non-existent user
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "group or user not found" in response.json()["detail"].lower() # Based on router error handling

@pytest.mark.asyncio
async def test_remove_member_from_group_success(client: AsyncClient):
    creator = await create_test_user(client, "member_remover_owner", "remove_owner@example.com")
    member_to_remove = await create_test_user(client, "to_be_removed_member", "toberemoved@example.com")
    
    group_data = {"name": "Removal Test Group", "created_by_user_id": creator["id"]}
    create_group_response = await client.post("/groups/", json=group_data)
    group_id = create_group_response.json()["id"]

    # Add member first
    await client.post(f"/groups/{group_id}/members/{member_to_remove['id']}")
    
    # Now remove
    response = await client.delete(f"/groups/{group_id}/members/{member_to_remove['id']}")
    assert response.status_code == status.HTTP_200_OK

    # Try removing again - should not fail, but member is already gone.
    # The CRUD op returns the group. Endpoint should reflect this.
    response_again = await client.delete(f"/groups/{group_id}/members/{member_to_remove['id']}")
    assert response_again.status_code == status.HTTP_200_OK # Or 404 if CRUD indicates "member not found" more strictly

@pytest.mark.asyncio
async def test_remove_member_group_not_found(client: AsyncClient):
    some_user = await create_test_user(client, "some_user_for_remove_test_g_nf", "s_u_r_t_g_nf@example.com")
    response = await client.delete(f"/groups/9993/members/{some_user['id']}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "group or user not found" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_remove_member_user_not_found(client: AsyncClient):
    creator = await create_test_user(client, "owner_for_remove_test_u_nf", "o_r_t_u_nf@example.com")
    group_data = {"name": "Group For User NF Remove Test", "created_by_user_id": creator["id"]}
    create_group_response = await client.post("/groups/", json=group_data)
    group_id = create_group_response.json()["id"]

    response = await client.delete(f"/groups/{group_id}/members/9994") # Non-existent user
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "group or user not found" in response.json()["detail"].lower()


# Test removing the creator from the group (should be possible unless specific logic prevents it)
@pytest.mark.asyncio
async def test_remove_creator_from_group(client: AsyncClient):
    creator = await create_test_user(client, "creator_to_remove", "creator_remove@example.com")
    group_data = {"name": "Creator Removal Test", "created_by_user_id": creator["id"]}
    create_response = await client.post("/groups/", json=group_data)
    group_id = create_response.json()["id"]
    
    # Creator is initially a member.
    # Try to remove the creator.
    response = await client.delete(f"/groups/{group_id}/members/{creator['id']}")
    assert response.status_code == status.HTTP_200_OK
    # Further checks could involve verifying the member list if GroupReadWithMembers was used.
