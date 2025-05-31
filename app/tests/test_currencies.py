import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from src.models.models import Currency, User, Expense, ExpenseParticipant
from src.main import app  # To get TestClient(app)

# Assuming conftest.py provides these fixtures:
# db_session, test_user_admin, test_user_non_admin, admin_auth_headers, normal_user_auth_headers

API_PREFIX = "/api/v1/currencies"


@pytest.fixture(scope="function")
def test_client(db_session: Session): # db_session fixture to ensure clean DB state
    # Override dependencies for testing if needed, e.g., get_session
    # For now, assuming TestClient(app) handles DB session scoping correctly with a test DB.
    return TestClient(app)


def test_create_currency_admin(test_client: TestClient, admin_auth_headers: dict, db_session: Session):
    currency_data = {"code": "USD", "name": "US Dollar", "symbol": "$"}
    response = test_client.post(f"{API_PREFIX}/", headers=admin_auth_headers, json=currency_data)
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "USD"
    assert data["name"] == "US Dollar"
    assert data["symbol"] == "$"
    assert "id" in data

    # Verify in DB
    currency_in_db = db_session.get(Currency, data["id"])
    assert currency_in_db is not None
    assert currency_in_db.code == "USD"


def test_create_currency_non_admin(test_client: TestClient, normal_user_auth_headers: dict):
    currency_data = {"code": "EUR", "name": "Euro", "symbol": "€"}
    response = test_client.post(f"{API_PREFIX}/", headers=normal_user_auth_headers, json=currency_data)
    assert response.status_code == 403


def test_create_currency_duplicate_code(test_client: TestClient, admin_auth_headers: dict, db_session: Session):
    currency_data = {"code": "CAD", "name": "Canadian Dollar", "symbol": "C$"}
    response1 = test_client.post(f"{API_PREFIX}/", headers=admin_auth_headers, json=currency_data)
    assert response1.status_code == 201

    currency_data_dup = {"code": "CAD", "name": "Another CAD", "symbol": "C$"}
    response2 = test_client.post(f"{API_PREFIX}/", headers=admin_auth_headers, json=currency_data_dup)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"]


def test_read_currencies_empty(test_client: TestClient):
    response = test_client.get(f"{API_PREFIX}/")
    assert response.status_code == 200
    assert response.json() == []


def test_read_currencies_multiple(test_client: TestClient, admin_auth_headers: dict, db_session: Session):
    c1_data = {"code": "GBP", "name": "British Pound", "symbol": "£"}
    test_client.post(f"{API_PREFIX}/", headers=admin_auth_headers, json=c1_data)
    c2_data = {"code": "JPY", "name": "Japanese Yen", "symbol": "¥"}
    test_client.post(f"{API_PREFIX}/", headers=admin_auth_headers, json=c2_data)

    response = test_client.get(f"{API_PREFIX}/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["code"] == "GBP"
    assert data[1]["code"] == "JPY"

    # Test pagination (limit)
    response_limit = test_client.get(f"{API_PREFIX}/?limit=1")
    assert response_limit.status_code == 200
    data_limit = response_limit.json()
    assert len(data_limit) == 1


def test_read_specific_currency(test_client: TestClient, admin_auth_headers: dict, db_session: Session):
    currency_data = {"code": "AUD", "name": "Australian Dollar", "symbol": "A$"}
    response_create = test_client.post(f"{API_PREFIX}/", headers=admin_auth_headers, json=currency_data)
    currency_id = response_create.json()["id"]

    response_read = test_client.get(f"{API_PREFIX}/{currency_id}")
    assert response_read.status_code == 200
    data = response_read.json()
    assert data["id"] == currency_id
    assert data["code"] == "AUD"


def test_read_specific_currency_not_found(test_client: TestClient):
    response = test_client.get(f"{API_PREFIX}/99999")
    assert response.status_code == 404


def test_update_currency_admin(test_client: TestClient, admin_auth_headers: dict, db_session: Session):
    currency_data = {"code": "CHF", "name": "Swiss Franc", "symbol": "CHF"}
    response_create = test_client.post(f"{API_PREFIX}/", headers=admin_auth_headers, json=currency_data)
    currency_id = response_create.json()["id"]

    update_data = {"name": "Swiss Franc Updated", "symbol": "SFr"}
    response_update = test_client.put(f"{API_PREFIX}/{currency_id}", headers=admin_auth_headers, json=update_data)
    assert response_update.status_code == 200
    data = response_update.json()
    assert data["name"] == "Swiss Franc Updated"
    assert data["symbol"] == "SFr"
    assert data["code"] == "CHF" # Code should not change unless specified

    # Verify in DB
    currency_in_db = db_session.get(Currency, currency_id)
    assert currency_in_db.name == "Swiss Franc Updated"


def test_update_currency_admin_change_code(test_client: TestClient, admin_auth_headers: dict, db_session: Session):
    currency_data = {"code": "NZD", "name": "New Zealand Dollar", "symbol": "NZ$"}
    response_create = test_client.post(f"{API_PREFIX}/", headers=admin_auth_headers, json=currency_data)
    currency_id = response_create.json()["id"]

    update_data = {"code": "NZZ"} # Keeping it 3 chars, uppercase
    response_update = test_client.put(f"{API_PREFIX}/{currency_id}", headers=admin_auth_headers, json=update_data)
    assert response_update.status_code == 200
    data = response_update.json()
    assert data["code"] == "NZZ"

    # Verify in DB
    currency_in_db = db_session.get(Currency, currency_id)
    assert currency_in_db.code == "NZZ"


def test_update_currency_non_admin(test_client: TestClient, normal_user_auth_headers: dict, admin_auth_headers: dict):
    currency_data = {"code": "SGP", "name": "Singapore Dollar", "symbol": "S$"}
    response_create = test_client.post(f"{API_PREFIX}/", headers=admin_auth_headers, json=currency_data)
    currency_id = response_create.json()["id"]

    update_data = {"name": "Singapore Dollar Updated"}
    response_update = test_client.put(f"{API_PREFIX}/{currency_id}", headers=normal_user_auth_headers, json=update_data)
    assert response_update.status_code == 403


def test_update_currency_new_code_duplicate(test_client: TestClient, admin_auth_headers: dict, db_session: Session):
    c1_data = {"code": "HKD", "name": "Hong Kong Dollar", "symbol": "HK$"}
    test_client.post(f"{API_PREFIX}/", headers=admin_auth_headers, json=c1_data)

    c2_data = {"code": "MOP", "name": "Macanese Pataca", "symbol": "MOP$"}
    response_create_c2 = test_client.post(f"{API_PREFIX}/", headers=admin_auth_headers, json=c2_data)
    c2_id = response_create_c2.json()["id"]

    update_data = {"code": "HKD"} # Attempt to change MOP's code to HKD
    response_update = test_client.put(f"{API_PREFIX}/{c2_id}", headers=admin_auth_headers, json=update_data)
    assert response_update.status_code == 400
    assert "already exists" in response_update.json()["detail"]


def test_update_currency_not_found(test_client: TestClient, admin_auth_headers: dict):
    update_data = {"name": "Non Existent Currency"}
    response = test_client.put(f"{API_PREFIX}/88888", headers=admin_auth_headers, json=update_data)
    assert response.status_code == 404


def test_delete_currency_admin_unused(test_client: TestClient, admin_auth_headers: dict, db_session: Session):
    currency_data = {"code": "NOK", "name": "Norwegian Krone", "symbol": "kr"}
    response_create = test_client.post(f"{API_PREFIX}/", headers=admin_auth_headers, json=currency_data)
    currency_id = response_create.json()["id"]

    response_delete = test_client.delete(f"{API_PREFIX}/{currency_id}", headers=admin_auth_headers)
    assert response_delete.status_code == 200
    assert response_delete.json()["message"] == "Currency deleted"

    # Verify in DB
    currency_in_db = db_session.get(Currency, currency_id)
    assert currency_in_db is None


def test_delete_currency_non_admin(test_client: TestClient, normal_user_auth_headers: dict, admin_auth_headers: dict):
    currency_data = {"code": "SEK", "name": "Swedish Krona", "symbol": "kr"}
    response_create = test_client.post(f"{API_PREFIX}/", headers=admin_auth_headers, json=currency_data)
    currency_id = response_create.json()["id"]

    response_delete = test_client.delete(f"{API_PREFIX}/{currency_id}", headers=normal_user_auth_headers)
    assert response_delete.status_code == 403


def test_delete_currency_not_found(test_client: TestClient, admin_auth_headers: dict):
    response = test_client.delete(f"{API_PREFIX}/77777", headers=admin_auth_headers)
    assert response.status_code == 404


def test_delete_currency_admin_used(
    test_client: TestClient, 
    admin_auth_headers: dict, 
    db_session: Session,
    test_user_admin: User # To be the payer
):
    # 1. Create a currency
    currency_data = {"code": "TST", "name": "Test Currency", "symbol": "T"}
    response_currency = test_client.post(f"{API_PREFIX}/", headers=admin_auth_headers, json=currency_data)
    assert response_currency.status_code == 201
    currency_id = response_currency.json()["id"]

    # 2. Create an expense linked to this currency
    expense_data = {
        "description": "Test Expense for Currency",
        "amount": 100.0,
        "currency_id": currency_id,
        # paid_by_user_id is set by the endpoint based on current_user
        # group_id is optional
    }
    # We need to use the expense creation endpoint. Assuming it's under /api/v1/expenses
    # The user creating the expense needs to be authenticated. Using admin here.
    response_expense = test_client.post(
        "/api/v1/expenses/", # Assuming this is the correct path from expenses router
        headers=admin_auth_headers, 
        json=expense_data
    )
    assert response_expense.status_code == 201 # Or 200 depending on your expense endpoint for simple create

    # 3. Attempt to delete the currency
    response_delete = test_client.delete(f"{API_PREFIX}/{currency_id}", headers=admin_auth_headers)
    assert response_delete.status_code == 400
    assert "associated with existing expenses" in response_delete.json()["detail"]

    # Verify currency still exists in DB
    currency_in_db = db_session.get(Currency, currency_id)
    assert currency_in_db is not None
    assert currency_in_db.code == "TST"

    # Clean up the expense (optional, but good practice if not using transaction rollbacks per test)
    # This might require another call to the expense delete endpoint or direct DB manipulation if easier
    # For now, assuming test isolation handles cleanup.
    expense_id = response_expense.json()["id"]
    # To clean up, we might need to delete participants first if any were auto-created
    # Then delete the expense itself.
    # This part depends on how your expense deletion is set up.
    # For simplicity, if tests are wrapped in transactions that roll back, this is not strictly needed.
    # If not, a fixture to clean up created expenses would be good.
    
    # Example cleanup (highly dependent on expense deletion logic):
    # First remove participants if any (assuming ExpenseParticipant exists and links)
    db_session.exec(select(ExpenseParticipant).where(ExpenseParticipant.expense_id == expense_id))
    # Then delete expense
    expense_to_delete = db_session.get(Expense, expense_id)
    if expense_to_delete:
        db_session.delete(expense_to_delete)
        db_session.commit()