import pytest
from httpx import AsyncClient
from fastapi import status
from src.models.models import User


# Helper function to create a user and return its ID (or full object)
async def create_test_user(
    client: AsyncClient, username: str, email: str, password: str = "testpassword1"
) -> dict:
    user_data = {"username": username, "email": email, "password": password}
    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == status.HTTP_200_OK
    return response.json()


@pytest.mark.asyncio
async def test_create_group_success(
    client: AsyncClient, normal_user_token_headers: dict[str, str], normal_user: User
):
    # creator = await create_test_user(client, "group_creator", "creator@example.com") # No longer needed, user comes from token
    group_data = {"name": "Test Group Alpha"}  # created_by_user_id removed
    response = await client.post(
        "/api/v1/groups/", json=group_data, headers=normal_user_token_headers
    )
    assert (
        response.status_code == status.HTTP_200_OK
    )  # Expect 200 for successful creation
    data = response.json()
    assert data["name"] == group_data["name"]
    assert data["created_by_user_id"] == normal_user.id  # User ID from token
    assert "id" in data


# Fixtures normal_user, admin_user, normal_user_token_headers, admin_user_token_headers are from conftest.py
# User model for type hinting if needed


@pytest.mark.asyncio
async def test_create_group_normal_user(
    client: AsyncClient, normal_user_token_headers: dict[str, str], normal_user: User
):
    group_data = {"name": "Normal User Group"}  # No created_by_user_id needed
    response = await client.post(
        "/api/v1/groups/", json=group_data, headers=normal_user_token_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == group_data["name"]
    assert (
        data["created_by_user_id"] == normal_user.id
    )  # Should match the token user's ID
    assert "id" in data


# Read Group (Detail View) Authorization Tests
@pytest.mark.asyncio
async def test_read_group_authorization(
    client: AsyncClient,
    normal_user: User,
    admin_user: User,
    normal_user_token_headers: dict[str, str],
    admin_user_token_headers: dict[str, str],
):
    # Setup: Create a group by normal_user
    group_data = {"name": "Group For Read Auth Test"}
    response = await client.post(
        "/api/v1/groups/", json=group_data, headers=normal_user_token_headers
    )
    assert response.status_code == status.HTTP_200_OK
    created_group = response.json()
    group_id = created_group["id"]

    # Setup: Create other_user
    other_user_data = await create_test_user(
        client, "other_user_grp_read", "other_grp_read@example.com"
    )
    other_user_id = other_user_data["id"]

    # Login other_user to get their token (or use admin to add them if no self-login for test util)
    # For simplicity, assume create_test_user doesn't auto-login or provide token.
    # We'll test non-member access first.
    other_user_login_data = {
        "username": "other_user_grp_read",
        "password": "testpassword1",
    }
    res = await client.post("/api/v1/users/token", data=other_user_login_data)
    assert res.status_code == 200, "Failed to log in other_user"
    other_user_token = res.json()["access_token"]
    other_user_headers = {"Authorization": f"Bearer {other_user_token}"}

    # Test: Creator (normal_user) can view
    response_creator_view = await client.get(
        f"/api/v1/groups/{group_id}", headers=normal_user_token_headers
    )
    assert response_creator_view.status_code == status.HTTP_200_OK
    assert response_creator_view.json()["name"] == group_data["name"]

    # Test: Admin (admin_user) can view
    response_admin_view = await client.get(
        f"/api/v1/groups/{group_id}", headers=admin_user_token_headers
    )
    assert response_admin_view.status_code == status.HTTP_200_OK

    # Test: Non-member/non-creator/non-admin (other_user) cannot view (403)
    response_other_view_non_member = await client.get(
        f"/api/v1/groups/{group_id}", headers=other_user_headers
    )
    assert response_other_view_non_member.status_code == status.HTTP_403_FORBIDDEN

    # Setup: Add other_user to the group (admin or creator can do this, use admin for simplicity)
    add_member_response = await client.post(
        f"/api/v1/groups/{group_id}/members/{other_user_id}",
        headers=admin_user_token_headers,
    )
    assert add_member_response.status_code == status.HTTP_200_OK

    # Test: Group member (other_user) can now view
    response_other_view_member = await client.get(
        f"/api/v1/groups/{group_id}", headers=other_user_headers
    )
    assert response_other_view_member.status_code == status.HTTP_200_OK


# Delete Group Authorization Tests
@pytest.mark.asyncio
async def test_delete_group_authorization(
    client: AsyncClient,
    normal_user: User,
    admin_user: User,
    normal_user_token_headers: dict[str, str],
    admin_user_token_headers: dict[str, str],
):
    # Setup: Create other_user for testing non-creator/non-admin deletion
    other_user_data = await create_test_user(
        client, "other_user_grp_del", "other_grp_del@example.com"
    )
    other_user_login_data = {
        "username": "other_user_grp_del",
        "password": "testpassword1",
    }
    res = await client.post("/api/v1/users/token", data=other_user_login_data)
    assert res.status_code == 200, "Failed to log in other_user for delete test"
    other_user_token = res.json()["access_token"]
    other_user_headers = {"Authorization": f"Bearer {other_user_token}"}

    # Test: Creator (normal_user) can delete
    group_data_creator_del = {"name": "Group For Creator Delete Test"}
    response_create_creator_del = await client.post(
        "/api/v1/groups/",
        json=group_data_creator_del,
        headers=normal_user_token_headers,
    )
    assert response_create_creator_del.status_code == status.HTTP_200_OK
    group_id_creator_del = response_create_creator_del.json()["id"]

    response_creator_delete = await client.delete(
        f"/api/v1/groups/{group_id_creator_del}", headers=normal_user_token_headers
    )
    assert response_creator_delete.status_code == status.HTTP_200_OK
    # Verify deletion
    response_get_after_creator_delete = await client.get(
        f"/api/v1/groups/{group_id_creator_del}", headers=admin_user_token_headers
    )  # Admin can try to get
    assert response_get_after_creator_delete.status_code == status.HTTP_404_NOT_FOUND

    # Test: Admin (admin_user) can delete a group created by normal_user
    group_data_admin_del = {"name": "Group For Admin Delete Test"}
    response_create_admin_del = await client.post(
        "/api/v1/groups/", json=group_data_admin_del, headers=normal_user_token_headers
    )  # normal_user creates
    assert response_create_admin_del.status_code == status.HTTP_200_OK
    group_id_admin_del = response_create_admin_del.json()["id"]

    response_admin_delete = await client.delete(
        f"/api/v1/groups/{group_id_admin_del}", headers=admin_user_token_headers
    )  # admin deletes
    assert response_admin_delete.status_code == status.HTTP_200_OK

    # Verify deletion by trying to get the group with the creator's token
    response_get_after_admin_delete = await client.get(
        f"/api/v1/groups/{group_id_admin_del}", headers=normal_user_token_headers
    )  # normal_user (creator) tries to get
    assert response_get_after_admin_delete.status_code == status.HTTP_404_NOT_FOUND

    # Test: Other user (non-creator/non-admin) cannot delete
    group_data_other_del = {"name": "Group For Other User Delete Test"}
    response_create_other_del = await client.post(
        "/api/v1/groups/", json=group_data_other_del, headers=normal_user_token_headers
    )  # normal_user creates
    assert response_create_other_del.status_code == status.HTTP_200_OK
    group_id_other_del = response_create_other_del.json()["id"]

    response_other_delete = await client.delete(
        f"/api/v1/groups/{group_id_other_del}", headers=other_user_headers
    )  # other_user tries to delete
    assert response_other_delete.status_code == status.HTTP_403_FORBIDDEN
    # Verify group still exists
    response_get_after_other_delete_fail = await client.get(
        f"/api/v1/groups/{group_id_other_del}", headers=normal_user_token_headers
    )
    assert response_get_after_other_delete_fail.status_code == status.HTTP_200_OK


# Delete obsolete tests that don't use authentication or new group creation logic
# For example, test_create_group_success, test_create_group_creator_not_found, etc.
# The tests above cover the creation with auth. Read tests for specific groups are covered by auth tests.
# Listing groups might still be relevant but needs auth.
# Update and delete tests are covered by auth tests.
# Member management tests need to be adapted for authentication.


# Keeping member management tests and adapting them for authentication
@pytest.mark.asyncio
async def test_add_member_to_group_success_auth(
    client: AsyncClient,
    normal_user_token_headers: dict[str, str],
    admin_user_token_headers: dict[str, str],
    normal_user: User,
):
    # normal_user (creator) creates group
    group_data = {"name": "Membership Test Group Auth"}
    create_group_response = await client.post(
        "/api/v1/groups/", json=group_data, headers=normal_user_token_headers
    )
    assert create_group_response.status_code == status.HTTP_200_OK
    group_id = create_group_response.json()["id"]

    # Create a user to be added as a member
    member_to_add_data = await create_test_user(
        client, "new_member_auth", "newmember_auth@example.com"
    )
    member_to_add_id = member_to_add_data["id"]

    # normal_user (creator) adds member_to_add (should be allowed if group owners can manage members or if admins do it)
    # Assuming group owners can add members (or any authenticated user can add to any group if not restricted)
    # The current implementation of add_group_member_endpoint is protected by get_current_user, but doesn't check if current_user has rights to modify the group.
    # This might be a point for future improvement in the main code. For now, any authenticated user can add.
    response = await client.post(
        f"/api/v1/groups/{group_id}/members/{member_to_add_id}",
        headers=normal_user_token_headers,  # normal_user (creator) adding
    )
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_remove_member_from_group_success_auth(
    client: AsyncClient, normal_user_token_headers: dict[str, str], normal_user: User
):
    # normal_user creates group
    group_data = {"name": "Removal Test Group Auth"}
    create_group_response = await client.post(
        "/api/v1/groups/", json=group_data, headers=normal_user_token_headers
    )
    assert create_group_response.status_code == status.HTTP_200_OK
    group_id = create_group_response.json()["id"]

    # Create a user to be added and then removed
    member_data = await create_test_user(
        client, "to_be_removed_member_auth", "toberemoved_auth@example.com"
    )
    member_id = member_data["id"]

    # Add member first (creator does this)
    add_response = await client.post(
        f"/api/v1/groups/{group_id}/members/{member_id}",
        headers=normal_user_token_headers,
    )
    assert add_response.status_code == status.HTTP_200_OK

    # Now remove (creator does this)
    # Similar to adding, the endpoint is protected but doesn't check specific rights to modify the group.
    # This means any authenticated user can update any group's name/description.
    # This is a potential security issue in the main code.
    # For this test, we'll assume normal_user (creator) is updating.
    remove_response = await client.delete(
        f"/api/v1/groups/{group_id}/members/{member_id}",
        headers=normal_user_token_headers,
    )
    assert remove_response.status_code == status.HTTP_200_OK

    # Verify member is removed
    # For this, we might need to log in as the removed member and try to access the group, or have an endpoint to list members.
    # For now, we check if trying to remove again fails as expected.
    remove_again_response = await client.delete(
        f"/api/v1/groups/{group_id}/members/{member_id}",
        headers=normal_user_token_headers,
    )
    assert (
        remove_again_response.status_code == status.HTTP_404_NOT_FOUND
    )  # User is not a member
    assert (
        remove_again_response.json()["detail"] == "User is not a member of this group."
    )


@pytest.mark.asyncio
async def test_normal_user_can_create_two_groups_consecutively(
    client: AsyncClient,
    normal_user_token_headers: dict[str, str],
):
    """Tests if a normal user can create two groups consecutively."""
    group_data1 = {"name": "Test Group One Consecutive"}
    response1 = await client.post(
        "/api/v1/groups/", json=group_data1, headers=normal_user_token_headers
    )
    assert response1.status_code == status.HTTP_200_OK, (
        f"Failed to create first group: {response1.text}"
    )

    group_data2 = {"name": "Test Group Two Consecutive"}
    response2 = await client.post(
        "/api/v1/groups/", json=group_data2, headers=normal_user_token_headers
    )
    assert response2.status_code == status.HTTP_200_OK, (
        f"Failed to create second group: {response2.text}"
    )


# Test cases for group membership
@pytest.mark.asyncio
async def test_read_multiple_groups_auth(
    client: AsyncClient, normal_user_token_headers: dict[str, str]
):
    # Assuming listing groups is allowed for any authenticated user.
    # If it's admin-only, this test would need admin_user_token_headers and expect 200,
    # or normal_user_token_headers and expect 403.
    # The current implementation of GET /groups in routers/groups.py is protected by get_current_user,
    # but does not have further role/ownership checks.
    response = await client.get("/api/v1/groups/", headers=normal_user_token_headers)
    assert response.status_code == status.HTTP_200_OK
    # Further assertions on content can be added if needed.


# Update group test with auth
@pytest.mark.asyncio
async def test_update_group_success_auth(
    client: AsyncClient, normal_user_token_headers: dict[str, str], normal_user: User
):
    # normal_user creates group
    group_data = {"name": "Initial Name Auth"}
    create_response = await client.post(
        "/api/v1/groups/", json=group_data, headers=normal_user_token_headers
    )
    assert create_response.status_code == status.HTTP_200_OK
    group_id = create_response.json()["id"]

    update_payload = {"name": "Updated Group Name Auth"}
    # The current PUT /groups/{group_id} endpoint is protected by get_current_user.
    # It does NOT check for group ownership or admin status for updates.
    # This means any authenticated user can update any group's name/description.
    # This is a potential security issue in the main code.
    # For this test, we'll assume normal_user (creator) is updating.
    response = await client.put(
        f"/api/v1/groups/{group_id}",
        json=update_payload,
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == update_payload["name"]
    assert data["id"] == group_id
    assert data["created_by_user_id"] == normal_user.id
