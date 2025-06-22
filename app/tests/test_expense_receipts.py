import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi import status, UploadFile
from typing import Dict, Any, AsyncGenerator, IO
import io
import os # For UPLOAD_DIR_RECEIPTS access if needed for cleanup or path construction

from src.models.models import User, Group, Currency, Expense
from src.main import app # For UPLOAD_DIR_RECEIPTS if defined there, or define locally for test

# Assuming UPLOAD_DIR_RECEIPTS is defined in expenses router or main app
# For testing, we might need to know this path to check file existence or clean up.
# Let's define it here based on what was used in expenses.py for consistency.
# CWD for tests is /app
TEST_UPLOAD_DIR = "uploads/receipts"


@pytest.mark.asyncio
async def test_upload_receipt_success_payer(
    client: AsyncClient,
    normal_user_token_headers: dict[str, str], # Payer's headers
    test_user: User, # Payer
    test_currency: Currency,
):
    # 1. Create an expense
    expense_payload = {
        "description": "Expense for receipt",
        "amount": 50.0,
        "currency_id": test_currency.id,
        "paid_by_user_id": test_user.id,
        "split_method": "unequal",
    }
    response_create = await client.post("/api/v1/expenses/service/", json=expense_payload, headers=normal_user_token_headers)
    assert response_create.status_code == status.HTTP_201_CREATED
    expense_id = response_create.json()["id"]

    # 2. Upload a receipt
    # Create a dummy file for upload
    dummy_file_content = b"fake image data"
    files = {"file": ("receipt.jpg", io.BytesIO(dummy_file_content), "image/jpeg")}

    response_upload = await client.post(f"/api/v1/expenses/{expense_id}/upload-receipt", files=files, headers=normal_user_token_headers)
    assert response_upload.status_code == status.HTTP_200_OK, f"Upload failed: {response_upload.text}"

    data = response_upload.json()
    assert data["id"] == expense_id
    assert data["receipt_image_url"] is not None
    assert data["receipt_image_url"].startswith("receipts/")
    assert data["receipt_image_url"].endswith(".jpg")

    # Optional: Verify file exists on server (requires knowing the exact path and access)
    # file_path_on_server = os.path.join(os.getcwd(), TEST_UPLOAD_DIR, data["receipt_image_url"].split('/')[-1])
    # assert os.path.exists(file_path_on_server)
    # Cleanup: os.remove(file_path_on_server) # Requires careful handling

@pytest.mark.asyncio
async def test_upload_receipt_success_group_member(
    client: AsyncClient,
    normal_user_token_headers: dict[str, str], # Payer (test_user)
    test_user: User,
    test_user_2_with_token: dict, # Group member who is not payer
    test_group_shared_with_user2: Group, # Group with test_user and test_user_2
    test_currency: Currency,
):
    # 1. Create a group expense paid by test_user
    expense_payload = {
        "description": "Group expense for receipt",
        "amount": 60.0,
        "currency_id": test_currency.id,
        "group_id": test_group_shared_with_user2.id,
        "paid_by_user_id": test_user.id, # test_user is payer
        "split_method": "equal",
        "selected_participant_user_ids": [test_user.id, test_user_2_with_token["user"].id]
    }
    response_create = await client.post("/api/v1/expenses/service/", json=expense_payload, headers=normal_user_token_headers)
    assert response_create.status_code == status.HTTP_201_CREATED
    expense_id = response_create.json()["id"]

    # 2. test_user_2 (group member, not payer) uploads receipt
    group_member_headers = test_user_2_with_token["headers"]
    dummy_file_content = b"group member image data"
    files = {"file": ("receipt_group.png", io.BytesIO(dummy_file_content), "image/png")}

    response_upload = await client.post(f"/api/v1/expenses/{expense_id}/upload-receipt", files=files, headers=group_member_headers)
    assert response_upload.status_code == status.HTTP_200_OK, f"Upload failed: {response_upload.text}"
    data = response_upload.json()
    assert data["receipt_image_url"] is not None
    assert data["receipt_image_url"].startswith("receipts/")
    assert data["receipt_image_url"].endswith(".png")

@pytest.mark.asyncio
async def test_upload_receipt_fail_non_involved_user(
    client: AsyncClient,
    normal_user_token_headers: dict[str, str], # Payer (test_user)
    test_user: User,
    test_user_3_with_token: dict, # Non-involved user
    test_currency: Currency,
):
    # 1. Create an expense by test_user
    expense_payload = {
        "description": "Expense for auth test",
        "amount": 30.0,
        "currency_id": test_currency.id,
        "paid_by_user_id": test_user.id,
        "split_method": "unequal",
    }
    response_create = await client.post("/api/v1/expenses/service/", json=expense_payload, headers=normal_user_token_headers)
    assert response_create.status_code == status.HTTP_201_CREATED
    expense_id = response_create.json()["id"]

    # 2. test_user_3 (non-involved) tries to upload
    non_involved_user_headers = test_user_3_with_token["headers"]
    files = {"file": ("receipt_auth_fail.jpg", io.BytesIO(b"some data"), "image/jpeg")}
    response_upload = await client.post(f"/api/v1/expenses/{expense_id}/upload-receipt", files=files, headers=non_involved_user_headers)
    assert response_upload.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.asyncio
async def test_upload_receipt_fail_expense_not_found(
    client: AsyncClient, normal_user_token_headers: dict[str, str]
):
    non_existent_expense_id = 999999
    files = {"file": ("receipt_notfound.jpg", io.BytesIO(b"some data"), "image/jpeg")}
    response_upload = await client.post(f"/api/v1/expenses/{non_existent_expense_id}/upload-receipt", files=files, headers=normal_user_token_headers)
    assert response_upload.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_upload_receipt_fail_invalid_file_type(
    client: AsyncClient,
    normal_user_token_headers: dict[str, str],
    test_user: User,
    test_currency: Currency,
):
    # 1. Create an expense
    expense_payload = { "description": "File type test", "amount": 10.0, "currency_id": test_currency.id, "paid_by_user_id": test_user.id }
    response_create = await client.post("/api/v1/expenses/service/", json=expense_payload, headers=normal_user_token_headers)
    assert response_create.status_code == status.HTTP_201_CREATED
    expense_id = response_create.json()["id"]

    # 2. Upload an invalid file type
    files = {"file": ("receipt.txt", io.BytesIO(b"this is not an image"), "text/plain")}
    response_upload = await client.post(f"/api/v1/expenses/{expense_id}/upload-receipt", files=files, headers=normal_user_token_headers)
    assert response_upload.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid file type" in response_upload.json()["detail"]

# TODO: Add test for file size limit if implemented.
# TODO: Consider testing if the file URL is actually accessible (might require more setup or a different testing approach for static files).
# For now, checking the format of `receipt_image_url` is a good start.
# Cleanup of uploaded files: This test suite doesn't automatically clean up files from TEST_UPLOAD_DIR.
# In a real CI/CD, the test environment is usually ephemeral, or specific cleanup scripts are run.
# For local testing, manual cleanup of `app/uploads/receipts` might be needed.
# One could add a fixture to clean this directory before/after test session if it becomes an issue.
# Example cleanup fixture (session-scoped):
# @pytest_asyncio.fixture(scope="session", autouse=True)
# async def cleanup_receipts_folder():
#     # Before tests run (optional, if starting clean is desired)
#     # if os.path.exists(TEST_UPLOAD_DIR):
#     #     shutil.rmtree(TEST_UPLOAD_DIR)
#     # os.makedirs(TEST_UPLOAD_DIR, exist_ok=True)
#     yield
#     # After all tests in session run
#     if os.path.exists(TEST_UPLOAD_DIR):
#         shutil.rmtree(TEST_UPLOAD_DIR) # Careful with this in real projects
#         # print(f"Cleaned up {TEST_UPLOAD_DIR}")

# For now, I will not add the auto-cleanup fixture to avoid accidental deletion
# if paths are misconfigured or if someone runs tests outside a fully controlled environment.
# The test environment itself should be responsible for its state.
# The use of UUIDs for filenames minimizes collision risks.
