import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession # No change
from typing import List, Dict, Any, Optional

from app.src.models.models import ( # Corrected paths
    User,
    Group,
    Expense,
    Currency,
    ExpenseParticipant,
    UserGroupLink, # Added
)
from app.src.models.schemas import UserRead, CurrencyRead, UserOverallBalance, GroupBalanceSummary # Added new schemas
from app.src.main import app
from app.tests.conftest import TestingSessionLocal, test_engine as engine # Corrected import for TestingSessionLocal
from app.src.core.security import get_password_hash


# Helper function to create a user (can be moved to a conftest.py later)
async def create_test_user(
    username: str = "testuser",
    email: str = "test@example.com",
    password: str = "Testpassword123",
    async_db_session: AsyncSession, # Added session parameter
    username: str = "testuser",
    email: str = "test@example.com",
    password: str = "Testpassword123",
    id: Optional[int] = None, # Added id for easier reference
) -> User:
    user = User(
        id=id,
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        email_verified=True # Assume verified for these tests
    )
    async_db_session.add(user)
    await async_db_session.commit()
    await async_db_session.refresh(user)
    return user


# Helper function to create a currency
async def create_test_currency(
    async_db_session: AsyncSession, # Added session parameter
    code: str = "USD",
    name: str = "US Dollar",
    symbol: str = "$",
    id: Optional[int] = None, # Added id
) -> Currency:
    currency = Currency(id=id, code=code, name=name, symbol=symbol)
    async_db_session.add(currency)
    await async_db_session.commit()
    await async_db_session.refresh(currency)
    return currency

# Helper function to create a group
async def create_test_group(
    async_db_session: AsyncSession, # Added session parameter
    name: str,
    created_by_user_id: int,
    members_ids: List[int],
    id: Optional[int] = None, # Added id
) -> Group:
    group = Group(id=id, name=name, created_by_user_id=created_by_user_id)
    async_db_session.add(group)
    await async_db_session.commit()
    await async_db_session.refresh(group)
    for member_id in members_ids:
        link = UserGroupLink(user_id=member_id, group_id=group.id)
        async_db_session.add(link)
    await async_db_session.commit()
    await async_db_session.refresh(group, attribute_names=['members'])
    return group


# Helper function to create an expense
async def create_test_expense(
    async_db_session: AsyncSession, # Added session parameter
    description: str,
    amount: float,
    currency_id: int,
    paid_by_user_id: int,
    group_id: Optional[int] = None,
    participants_data: Optional[
        List[Dict[str, Any]]
    ] = None,  # e.g., [{"user_id": 1, "share_amount": 10.0, "settled_amount": 0.0}]
    id: Optional[int] = None, # Added id
) -> Expense:
    expense = Expense(
        id=id,
        description=description,
        amount=amount,
        currency_id=currency_id,
        paid_by_user_id=paid_by_user_id,
        group_id=group_id,
    )
    async_db_session.add(expense)
    await async_db_session.commit()
    await async_db_session.refresh(expense)

    if participants_data:
        for p_data in participants_data:
            participant = ExpenseParticipant(
                expense_id=expense.id,
                user_id=p_data["user_id"],
                share_amount=p_data["share_amount"],
                settled_amount_in_transaction_currency=p_data.get("settled_amount", 0.0)
            )
            async_db_session.add(participant)
        await async_db_session.commit()
        # Refresh to load all_participant_details relationship
        await async_db_session.refresh(expense, attribute_names=['all_participant_details'])
    return expense


@pytest.mark.asyncio
async def test_get_my_overall_balances_no_expenses( # Renamed test, new response schema
    client: AsyncClient,
    # db_session: AsyncSession, # Removed, db_setup_session is autouse, helpers manage own sessions
    normal_user_token_headers: dict,
    normal_user: User,
):
    response = await client.get("/api/v1/balances/me", headers=normal_user_token_headers)
    assert response.status_code == 200
    data = UserOverallBalance.model_validate(response.json())

    assert data.user_id == normal_user.id
    assert not data.total_you_owe_by_currency
    assert not data.total_owed_to_you_by_currency
    assert not data.net_overall_balance_by_currency
    assert not data.breakdown_by_group
    assert not data.detailed_debts_by_currency
    assert not data.detailed_credits_by_currency

@pytest.mark.asyncio
async def test_get_my_overall_balances_user_paid_others_owe( # Renamed, adapted
    client: AsyncClient,
    # db_session: AsyncSession, # Removed
    normal_user_token_headers: dict,
    normal_user: User,
):
    user2 = await create_test_user(username="user2bal", email="user2bal@example.com", id=102)
    currency_eur = await create_test_currency(code="EUR", name="Euro", id=101)

    group1 = await create_test_group("Group Bal Test", normal_user.id, members_ids=[normal_user.id, user2.id], id=101)

    await create_test_expense(
        description="Dinner EUR",
        amount=100.0,
        currency_id=currency_eur.id,
        paid_by_user_id=normal_user.id,
        group_id=group1.id,
        participants_data=[
            {"user_id": normal_user.id, "share_amount": 60.0}, # Payer's share
            {"user_id": user2.id, "share_amount": 40.0},     # User2 owes 40
        ],
    )

    response = await client.get("/api/v1/balances/me", headers=normal_user_token_headers)
    assert response.status_code == 200
    data = UserOverallBalance.model_validate(response.json())

    assert data.user_id == normal_user.id
    assert data.total_owed_to_you_by_currency.get("EUR") == 40.0
    assert not data.total_you_owe_by_currency.get("EUR")
    assert data.net_overall_balance_by_currency.get("EUR") == 40.0

    assert len(data.detailed_credits_by_currency.get("EUR", [])) == 1
    credit_detail = data.detailed_credits_by_currency["EUR"][0]
    assert credit_detail.owed_by_user_id == user2.id
    assert credit_detail.amount == 40.0
    assert credit_detail.currency_code == "EUR"

    assert len(data.breakdown_by_group) == 1
    group_breakdown = data.breakdown_by_group[0]
    assert group_breakdown.group_id == group1.id
    assert group_breakdown.your_net_balance_in_group == 40.0 # 40 owed to user1 by user2
    assert group_breakdown.currency_code == "EUR"


@pytest.mark.asyncio
async def test_get_my_overall_balances_user_owes_others( # Renamed, adapted
    client: AsyncClient,
    # db_session: AsyncSession, # Removed
    normal_user_token_headers: dict,
    normal_user: User,
):
    payer_user = await create_test_user(username="payeruserbal", email="payerbal@example.com", id=103)
    currency_gbp = await create_test_currency(code="GBP", name="British Pound", id=102)
    group1 = await create_test_group("Group Bal Test 2", normal_user.id, members_ids=[normal_user.id, payer_user.id], id=102)

    await create_test_expense(
        description="Concert Tickets GBP",
        amount=120.0,
        currency_id=currency_gbp.id,
        paid_by_user_id=payer_user.id, # Payer is other user
        group_id=group1.id,
        participants_data=[
            {"user_id": normal_user.id, "share_amount": 60.0}, # Current user's share
            {"user_id": payer_user.id, "share_amount": 60.0},  # Payer's share
        ],
    )

    response = await client.get("/api/v1/balances/me", headers=normal_user_token_headers)
    assert response.status_code == 200
    data = UserOverallBalance.model_validate(response.json())

    assert data.user_id == normal_user.id
    assert data.total_you_owe_by_currency.get("GBP") == 60.0
    assert not data.total_owed_to_you_by_currency.get("GBP")
    assert data.net_overall_balance_by_currency.get("GBP") == -60.0

    assert len(data.detailed_debts_by_currency.get("GBP", [])) == 1
    debt_detail = data.detailed_debts_by_currency["GBP"][0]
    assert debt_detail.owes_user_id == payer_user.id
    assert debt_detail.amount == 60.0
    assert debt_detail.currency_code == "GBP"

@pytest.mark.asyncio
async def test_get_my_overall_balances_multi_currency_complex( # New test for overall balance
    client: AsyncClient,
    # db_session: AsyncSession, # Removed
    normal_user_token_headers: dict,
    normal_user: User,
):
    user2 = await create_test_user(username="user2compl", email="user2compl@example.com", id=201)
    user3 = await create_test_user(username="user3compl", email="user3compl@example.com", id=202)
    usd = await create_test_currency(code="USD", name="US Dollar", id=201)
    eur = await create_test_currency(code="EUR", name="Euro", id=202)

    group1 = await create_test_group("G1 Bal", normal_user.id, members_ids=[normal_user.id, user2.id], id=201)
    group2 = await create_test_group("G2 Bal", normal_user.id, members_ids=[normal_user.id, user3.id], id=202)

    # G1: normal_user paid 100 USD for self,user2 (50 each). user2 owes normal_user 50 USD.
    await create_test_expense("Lunch G1 USD", 100.0, usd.id, normal_user.id, group1.id,
                              participants_data=[{"user_id": normal_user.id, "share_amount": 50.0},
                                                 {"user_id": user2.id, "share_amount": 50.0}])
    # G1: user2 paid 80 EUR for self,normal_user (40 each). normal_user owes user2 40 EUR.
    await create_test_expense("Taxi G1 EUR", 80.0, eur.id, user2.id, group1.id,
                              participants_data=[{"user_id": normal_user.id, "share_amount": 40.0},
                                                 {"user_id": user2.id, "share_amount": 40.0}])
    # G2: normal_user paid 60 USD for self,user3 (30 each). user3 owes normal_user 30 USD.
    await create_test_expense("Coffee G2 USD", 60.0, usd.id, normal_user.id, group2.id,
                              participants_data=[{"user_id": normal_user.id, "share_amount": 30.0},
                                                 {"user_id": user3.id, "share_amount": 30.0}])
    # G2: user3 paid 20 EUR for self,normal_user (10 each). normal_user owes user3 10 EUR.
    await create_test_expense("Snacks G2 EUR", 20.0, eur.id, user3.id, group2.id,
                              participants_data=[{"user_id": normal_user.id, "share_amount": 10.0},
                                                 {"user_id": user3.id, "share_amount": 10.0}])

    response = await client.get("/api/v1/balances/me", headers=normal_user_token_headers)
    assert response.status_code == 200
    data = UserOverallBalance.model_validate(response.json())

    assert data.total_owed_to_you_by_currency.get("USD") == 80.0 # 50 from user2, 30 from user3
    assert data.total_you_owe_by_currency.get("EUR") == 50.0    # 40 to user2, 10 to user3
    assert data.net_overall_balance_by_currency.get("USD") == 80.0
    assert data.net_overall_balance_by_currency.get("EUR") == -50.0

    assert len(data.detailed_credits_by_currency.get("USD", [])) == 2
    assert len(data.detailed_debts_by_currency.get("EUR", [])) == 2

    assert len(data.breakdown_by_group) == 4 # G1-USD, G1-EUR, G2-USD, G2-EUR


# --- Tests for GET /groups/{group_id}/balances ---

@pytest.mark.asyncio
async def test_get_group_balances_not_a_member(
    client: AsyncClient,
    # db_session: AsyncSession, # Removed
    normal_user_token_headers: dict, # Belongs to normal_user
    normal_user: User,
):
    other_user = await create_test_user(username="othergroupuser", email="othergu@example.com", id=301)
    group_other = await create_test_group("Other's Group", other_user.id, members_ids=[other_user.id], id=301)

    response = await client.get(f"/api/v1/groups/{group_other.id}/balances", headers=normal_user_token_headers)
    assert response.status_code == 403 # Or 404 if combined, router logic specific

@pytest.mark.asyncio
async def test_get_group_balances_group_not_found(
    client: AsyncClient,
    # db_session: AsyncSession, # Removed
    normal_user_token_headers: dict,
):
    non_existent_group_id = 99999
    response = await client.get(f"/api/v1/groups/{non_existent_group_id}/balances", headers=normal_user_token_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_group_balances_simple_case(
    client: AsyncClient,
    # db_session: AsyncSession, # Removed
    normal_user_token_headers: dict,
    normal_user: User,
):
    user2 = await create_test_user(username="user2grp", email="user2grp@example.com", id=401)
    currency_usd = await create_test_currency(code="USD", name="US Dollar", id=401)
    group1 = await create_test_group("Group Test Simple", normal_user.id, members_ids=[normal_user.id, user2.id], id=401)

    # normal_user paid 100 USD for self,user2 (50 each). user2 owes normal_user 50 USD.
    await create_test_expense(
        "Dinner USD Group", 100.0, currency_usd.id, normal_user.id, group1.id,
        participants_data=[{"user_id": normal_user.id, "share_amount": 50.0},
                           {"user_id": user2.id, "share_amount": 50.0}]
    )

    response = await client.get(f"/api/v1/groups/{group1.id}/balances", headers=normal_user_token_headers)
    assert response.status_code == 200
    data = GroupBalanceSummary.model_validate(response.json())

    assert data.group_id == group1.id
    assert data.group_name == group1.name
    assert len(data.members_balances) == 2

    nu_balance = next(mb for mb in data.members_balances if mb.user_id == normal_user.id)
    u2_balance = next(mb for mb in data.members_balances if mb.user_id == user2.id)

    assert nu_balance.others_owe_user_total == 50.0
    assert nu_balance.owes_others_total == 0.0
    assert nu_balance.net_balance_in_group == 50.0
    assert len(nu_balance.credits_from_specific_users_by_currency.get("USD",[])) == 1
    assert nu_balance.credits_from_specific_users_by_currency["USD"][0].owed_by_user_id == user2.id
    assert nu_balance.credits_from_specific_users_by_currency["USD"][0].amount == 50.0

    assert u2_balance.owes_others_total == 50.0
    assert u2_balance.others_owe_user_total == 0.0
    assert u2_balance.net_balance_in_group == -50.0
    assert len(u2_balance.debts_to_specific_users_by_currency.get("USD",[])) == 1
    assert u2_balance.debts_to_specific_users_by_currency["USD"][0].owes_user_id == normal_user.id
    assert u2_balance.debts_to_specific_users_by_currency["USD"][0].amount == 50.0


@pytest.mark.asyncio
async def test_get_group_balances_with_settlement(
    client: AsyncClient,
    # db_session: AsyncSession, # Removed
    normal_user_token_headers: dict,
    normal_user: User,
):
    user2 = await create_test_user(username="user2settle", email="user2settle@example.com", id=501)
    currency_cad = await create_test_currency(code="CAD", name="Canadian Dollar", id=501)
    group1 = await create_test_group("Group Settle Test", normal_user.id, members_ids=[normal_user.id, user2.id], id=501)

    # normal_user paid 100 CAD for self,user2 (50 each). user2's share 50 CAD.
    # user2's participation is partially settled by 20 CAD.
    await create_test_expense(
        "Event CAD Group", 100.0, currency_cad.id, normal_user.id, group1.id,
        participants_data=[
            {"user_id": normal_user.id, "share_amount": 50.0},
            {"user_id": user2.id, "share_amount": 50.0, "settled_amount": 20.0} # user2 owes 30 CAD
        ]
    )

    response = await client.get(f"/api/v1/groups/{group1.id}/balances", headers=normal_user_token_headers)
    assert response.status_code == 200
    data = GroupBalanceSummary.model_validate(response.json())

    nu_balance = next(mb for mb in data.members_balances if mb.user_id == normal_user.id)
    u2_balance = next(mb for mb in data.members_balances if mb.user_id == user2.id)

    # normal_user is owed 30 CAD by user2
    assert nu_balance.others_owe_user_total == 30.0
    assert nu_balance.credits_from_specific_users_by_currency["CAD"][0].amount == 30.0

    # user2 owes 30 CAD to normal_user
    assert u2_balance.owes_others_total == 30.0
    assert u2_balance.debts_to_specific_users_by_currency["CAD"][0].amount == 30.0

# Note: The original test_get_balances_user_payer_and_participant is effectively covered by how shares are defined.
# The new balance calculation logic correctly handles payer participation if their share is listed.
# The important part is that the service correctly calculates who owes whom based on (share_amount - paid_amount_for_that_share_by_participant).
# Payer's own share doesn't make them owe themselves.
# The new overall and group balance endpoints rely on the service layer tests for these core calculation details.
# The integration tests here focus more on the API request/response structure and basic correctness.
# More complex calculation scenarios are better tested at the service layer (test_balance_service.py).
