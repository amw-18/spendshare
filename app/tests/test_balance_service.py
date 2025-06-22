import pytest
from typing import List, Optional, Any, Dict
from collections import defaultdict
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel, Field, create_engine


from app.src.models.models import User, Group, Expense, Currency, ExpenseParticipant, UserGroupLink, Transaction
from app.src.models.schemas import (
    GroupBalanceSummary,
    UserOverallBalance,
    UserGroupBalance,
    DebtDetail,
    CreditDetail
)
from app.src.services import balance_service
from app.src.db.database import get_session # For potential direct session usage if needed

# Using engine and session fixtures from conftest.py

# Helper functions to create test data
# These will use the session provided by the 'async_db_session' fixture from conftest.py
async def create_user(async_db_session: AsyncSession, username: str, email: str, id: Optional[int] = None) -> User:
    user = User(id=id, username=username, email=email, hashed_password="hashedpassword", email_verified=True)
    db_session.add(user)
    await db_session.commit()
    await async_db_session.refresh(user)
    return user

async def create_currency(async_db_session: AsyncSession, code: str, name: str, id: Optional[int] = None) -> Currency:
    currency = Currency(id=id, code=code, name=name)
    async_db_session.add(currency)
    await async_db_session.commit()
    await async_db_session.refresh(currency)
    return currency

async def create_group(async_db_session: AsyncSession, name: str, created_by_user_id: int, id: Optional[int] = None) -> Group:
    group = Group(id=id, name=name, created_by_user_id=created_by_user_id)
    async_db_session.add(group)
    await async_db_session.commit()
    await async_db_session.refresh(group)
    return group

async def add_user_to_group(async_db_session: AsyncSession, user_id: int, group_id: int):
    link = UserGroupLink(user_id=user_id, group_id=group_id)
    async_db_session.add(link)
    await async_db_session.commit()

async def create_expense(
    async_db_session: AsyncSession,
    description: str,
    amount: float,
    currency_id: int,
    paid_by_user_id: int,
    group_id: Optional[int] = None,
    id: Optional[int] = None,
    participants_data: Optional[List[Dict[str, Any]]] = None # [{"user_id": int, "share_amount": float, "settled_amount": float (optional)}]
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
                settled_amount_in_transaction_currency=p_data.get("settled_amount")
            )
            # If settled_amount is provided, we might need a dummy transaction
            # For simplicity in these unit tests, we'll assume settled_transaction_id can be null
            # or that the balance service correctly handles it even if the transaction object isn't fully loaded/created here.
            async_db_session.add(participant)
        await async_db_session.commit()
        await async_db_session.refresh(expense, attribute_names=['all_participant_details'])
    return expense

@pytest.mark.asyncio
async def test_calculate_group_balances_no_expenses(async_db_session: AsyncSession):
    user1 = await create_user(async_db_session, "user1", "user1@test.com", id=1)
    group1 = await create_group(async_db_session, "Group1", user1.id, id=1)
    await add_user_to_group(async_db_session, user1.id, group1.id)

    summary = await balance_service.calculate_group_balances(group1.id, user1.id, async_db_session)

    assert summary.group_id == group1.id
    assert summary.group_name == group1.name
    assert len(summary.members_balances) == 1
    member_balance = summary.members_balances[0]
    assert member_balance.user_id == user1.id
    assert member_balance.owes_others_total == 0.0
    assert member_balance.others_owe_user_total == 0.0
    assert member_balance.net_balance_in_group == 0.0
    assert not member_balance.debts_to_specific_users_by_currency
    assert not member_balance.credits_from_specific_users_by_currency

@pytest.mark.asyncio
async def test_calculate_group_balances_single_expense_two_users(async_db_session: AsyncSession):
    user1 = await create_user(async_db_session, "user1", "user1@test.com", id=1)
    user2 = await create_user(async_db_session, "user2", "user2@test.com", id=2)
    currency_usd = await create_currency(async_db_session, "USD", "US Dollar", id=1)
    group1 = await create_group(async_db_session, "Group1", user1.id, id=1)
    await add_user_to_group(async_db_session, user1.id, group1.id)
    await add_user_to_group(async_db_session, user2.id, group1.id)

    await create_expense(
        async_db_session,
        description="Lunch",
        amount=100.0,
        currency_id=currency_usd.id,
        paid_by_user_id=user1.id,
        group_id=group1.id,
        participants_data=[
            {"user_id": user1.id, "share_amount": 50.0},
            {"user_id": user2.id, "share_amount": 50.0},
        ],
    )

    summary = await balance_service.calculate_group_balances(group1.id, user1.id, async_db_session)
    assert len(summary.members_balances) == 2

    user1_balance = next(mb for mb in summary.members_balances if mb.user_id == user1.id)
    user2_balance = next(mb for mb in summary.members_balances if mb.user_id == user2.id)

    # User1 paid 100, their share is 50. So, User2 owes User1 50.
    assert user1_balance.others_owe_user_total == 50.0
    assert user1_balance.owes_others_total == 0.0
    assert user1_balance.net_balance_in_group == 50.0
    assert len(user1_balance.credits_from_specific_users_by_currency["USD"]) == 1
    credit_detail_u1 = user1_balance.credits_from_specific_users_by_currency["USD"][0]
    assert credit_detail_u1.owed_by_user_id == user2.id
    assert credit_detail_u1.amount == 50.0

    assert user2_balance.owes_others_total == 50.0
    assert user2_balance.others_owe_user_total == 0.0
    assert user2_balance.net_balance_in_group == -50.0
    assert len(user2_balance.debts_to_specific_users_by_currency["USD"]) == 1
    debt_detail_u2 = user2_balance.debts_to_specific_users_by_currency["USD"][0]
    assert debt_detail_u2.owes_user_id == user1.id
    assert debt_detail_u2.amount == 50.0

@pytest.mark.asyncio
async def test_calculate_group_balances_multiple_expenses_settlement(async_db_session: AsyncSession):
    user1 = await create_user(async_db_session, "user1", "u1@test.com", id=1)
    user2 = await create_user(async_db_session, "user2", "u2@test.com", id=2)
    user3 = await create_user(async_db_session, "user3", "u3@test.com", id=3)
    usd = await create_currency(async_db_session, "USD", "US Dollar", id=1)
    group1 = await create_group(async_db_session, "G1", user1.id, id=1)
    await add_user_to_group(async_db_session, user1.id, group1.id)
    await add_user_to_group(async_db_session, user2.id, group1.id)
    await add_user_to_group(async_db_session, user3.id, group1.id)

    # Exp1: User1 paid 90 for U1,U2,U3 (30 each). U2 owes U1 30, U3 owes U1 30.
    await create_expense(async_db_session, "Dinner", 90.0, usd.id, user1.id, group1.id, participants_data=[
        {"user_id": user1.id, "share_amount": 30.0},
        {"user_id": user2.id, "share_amount": 30.0},
        {"user_id": user3.id, "share_amount": 30.0},
    ])
    # Exp2: User2 paid 60 for U1,U2 (30 each). U1 owes U2 30.
    await create_expense(async_db_session, "Movies", 60.0, usd.id, user2.id, group1.id, participants_data=[
        {"user_id": user1.id, "share_amount": 30.0},
        {"user_id": user2.id, "share_amount": 30.0},
    ])
    # Exp3: User3 paid 30 for U1, U3 (15 each). U1 owes U3 15. U3's share of Exp1 (30) is partially settled by 10.
    await create_expense(async_db_session, "Coffee", 30.0, usd.id, user3.id, group1.id, participants_data=[
        {"user_id": user1.id, "share_amount": 15.0},
        {"user_id": user3.id, "share_amount": 15.0, "settled_amount": 10.0}, # U3's share was 15, but let's assume this is a settlement for Exp1
    ])
    # To make the settlement test clearer, let's say user3's participation in Exp1 was settled by 10
    # We need to update that specific ExpenseParticipant record. This is a bit tricky with current helpers.
    # For now, the `settled_amount` in `create_expense` will apply to *that* expense's participant record.
    # Let's adjust Exp1's participant data for U3 for settlement.
    # This requires fetching and updating, or more complex setup.
    # Simpler: assume Exp1 U3 share was 30, and U3 paid 10 towards it separately.
    # The current model has settled_amount on ExpenseParticipant.
    # Let's simulate U3's share in Exp1 being partially settled.
    # This test will rely on the simplification logic.

    # Initial state from expenses:
    # U1: paid 90 (share 30), owed 30 by U2 (Exp1), owed 30 by U3 (Exp1). Net +60 for Exp1.
    #     owes 30 to U2 (Exp2), owes 15 to U3 (Exp3). Net -45 for Exp2 & Exp3.
    #     Overall U1: +60 - 45 = +15.
    # U2: paid 60 (share 30), owed 30 by U1 (Exp2). Net +30 for Exp2.
    #     owes 30 to U1 (Exp1). Net -30 for Exp1.
    #     Overall U2: 0.
    # U3: paid 30 (share 15), owed 15 by U1 (Exp3). Net +15 for Exp3.
    #     owes 30 to U1 (Exp1). Net -30 for Exp1. (Assume the 10 settlement on Exp3 participant doesn't affect this for now)
    #     Overall U3: +15 - 30 = -15.

    # Simplified:
    # U1 vs U2: U1 owes U2 (30(Exp2) - 30(Exp1)) = 0. No net between U1 and U2.
    # U1 vs U3: U1 owes U3 (15(Exp3) - 30(Exp1)) = -15. So U3 owes U1 15.
    # U2 vs U3: No direct transactions.

    # So, U3 owes U1 15.
    # U1: +15 (from U3)
    # U2: 0
    # U3: -15 (to U1)

    summary = await balance_service.calculate_group_balances(group1.id, user1.id, async_db_session)

    u1_b = next(mb for mb in summary.members_balances if mb.user_id == user1.id)
    u2_b = next(mb for mb in summary.members_balances if mb.user_id == user2.id)
    u3_b = next(mb for mb in summary.members_balances if mb.user_id == user3.id)

    # Check U1
    assert u1_b.net_balance_in_group == 15.0
    assert u1_b.others_owe_user_total == 15.0 # From U3
    assert u1_b.owes_others_total == 0.0
    assert len(u1_b.credits_from_specific_users_by_currency.get("USD", [])) == 1
    if u1_b.credits_from_specific_users_by_currency.get("USD"):
      assert u1_b.credits_from_specific_users_by_currency["USD"][0].owed_by_user_id == user3.id
      assert u1_b.credits_from_specific_users_by_currency["USD"][0].amount == 15.0

    # Check U2
    assert u2_b.net_balance_in_group == 0.0
    assert not u2_b.credits_from_specific_users_by_currency.get("USD")
    assert not u2_b.debts_to_specific_users_by_currency.get("USD")

    # Check U3
    assert u3_b.net_balance_in_group == -15.0
    assert u3_b.owes_others_total == 15.0 # To U1
    assert u3_b.others_owe_user_total == 0.0
    assert len(u3_b.debts_to_specific_users_by_currency.get("USD", [])) == 1
    if u3_b.debts_to_specific_users_by_currency.get("USD"):
      assert u3_b.debts_to_specific_users_by_currency["USD"][0].owes_user_id == user1.id
      assert u3_b.debts_to_specific_users_by_currency["USD"][0].amount == 15.0

@pytest.mark.asyncio
async def test_calculate_group_balances_multi_currency(async_db_session: AsyncSession):
    user1 = await create_user(async_db_session, "user1", "u1@test.com", id=1)
    user2 = await create_user(async_db_session, "user2", "u2@test.com", id=2)
    usd = await create_currency(async_db_session, "USD", "US Dollar", id=1)
    eur = await create_currency(async_db_session, "EUR", "Euro", id=2)
    group1 = await create_group(async_db_session, "G1", user1.id, id=1)
    await add_user_to_group(async_db_session, user1.id, group1.id)
    await add_user_to_group(async_db_session, user2.id, group1.id)

    # Exp1 (USD): U1 paid 100 for U1,U2 (50 each). U2 owes U1 50 USD.
    await create_expense(async_db_session, "Lunch USD", 100.0, usd.id, user1.id, group1.id, participants_data=[
        {"user_id": user1.id, "share_amount": 50.0}, {"user_id": user2.id, "share_amount": 50.0}
    ])
    # Exp2 (EUR): U2 paid 80 for U1,U2 (40 each). U1 owes U2 40 EUR.
    await create_expense(async_db_session, "Taxi EUR", 80.0, eur.id, user2.id, group1.id, participants_data=[
        {"user_id": user1.id, "share_amount": 40.0}, {"user_id": user2.id, "share_amount": 40.0}
    ])

    summary = await balance_service.calculate_group_balances(group1.id, user1.id, async_db_session)
    u1_b = next(mb for mb in summary.members_balances if mb.user_id == user1.id)
    u2_b = next(mb for mb in summary.members_balances if mb.user_id == user2.id)

    # User1: owes 40 EUR to U2, is owed 50 USD by U2.
    # Net balance field is tricky here. The by_currency fields are key.
    # For owes_others_total and others_owe_user_total, if only one currency, it's that sum.
    # Here, U1 owes in EUR, is owed in USD.
    assert u1_b.owes_others_total == 40.0 # Assuming it picks one if mixed, or based on how feature doc wants summary fields.
                                        # The detailed list is what matters more.
    assert u1_b.others_owe_user_total == 50.0
    # u1_b.net_balance_in_group will be 50 - 40 = 10 if we sum scalar fields.
    # However, this is not currency-aware. Let's check detailed breakdowns.

    assert len(u1_b.debts_to_specific_users_by_currency["EUR"]) == 1
    assert u1_b.debts_to_specific_users_by_currency["EUR"][0].owes_user_id == user2.id
    assert u1_b.debts_to_specific_users_by_currency["EUR"][0].amount == 40.0
    assert u1_b.debts_to_specific_users_by_currency["EUR"][0].currency_code == "EUR"

    assert len(u1_b.credits_from_specific_users_by_currency["USD"]) == 1
    assert u1_b.credits_from_specific_users_by_currency["USD"][0].owed_by_user_id == user2.id
    assert u1_b.credits_from_specific_users_by_currency["USD"][0].amount == 50.0
    assert u1_b.credits_from_specific_users_by_currency["USD"][0].currency_code == "USD"


    # User2: owes 50 USD to U1, is owed 40 EUR by U1.
    assert u2_b.owes_others_total == 50.0
    assert u2_b.others_owe_user_total == 40.0

    assert len(u2_b.debts_to_specific_users_by_currency["USD"]) == 1
    assert u2_b.debts_to_specific_users_by_currency["USD"][0].owes_user_id == user1.id
    assert u2_b.debts_to_specific_users_by_currency["USD"][0].amount == 50.0
    assert u2_b.debts_to_specific_users_by_currency["USD"][0].currency_code == "USD"

    assert len(u2_b.credits_from_specific_users_by_currency["EUR"]) == 1
    assert u2_b.credits_from_specific_users_by_currency["EUR"][0].owed_by_user_id == user1.id
    assert u2_b.credits_from_specific_users_by_currency["EUR"][0].amount == 40.0
    assert u2_b.credits_from_specific_users_by_currency["EUR"][0].currency_code == "EUR"


@pytest.mark.asyncio
async def test_calculate_user_overall_balances_no_groups_no_expenses(async_db_session: AsyncSession):
    user1 = await create_user(async_db_session, "user1", "u1@test.com", id=1)

    overall_summary = await balance_service.calculate_user_overall_balances(user1.id, async_db_session)

    assert overall_summary.user_id == user1.id
    assert not overall_summary.total_you_owe_by_currency
    assert not overall_summary.total_owed_to_you_by_currency
    assert not overall_summary.net_overall_balance_by_currency
    assert not overall_summary.breakdown_by_group
    assert not overall_summary.detailed_debts_by_currency
    assert not overall_summary.detailed_credits_by_currency

@pytest.mark.asyncio
async def test_calculate_user_overall_balances_one_group(async_db_session: AsyncSession):
    user1 = await create_user(async_db_session, "user1", "u1@test.com", id=1)
    user2 = await create_user(async_db_session, "user2", "u2@test.com", id=2)
    usd = await create_currency(async_db_session, "USD", "US Dollar", id=1)
    group1 = await create_group(async_db_session, "G1", user1.id, id=1)
    await add_user_to_group(async_db_session, user1.id, group1.id)
    await add_user_to_group(async_db_session, user2.id, group1.id)

    # U1 paid 100 for U1,U2 (50 each). U2 owes U1 50 USD.
    await create_expense(async_db_session, "Lunch", 100.0, usd.id, user1.id, group1.id, participants_data=[
        {"user_id": user1.id, "share_amount": 50.0}, {"user_id": user2.id, "share_amount": 50.0}
    ])

    overall_summary_u1 = await balance_service.calculate_user_overall_balances(user1.id, async_db_session)

    assert overall_summary_u1.total_owed_to_you_by_currency["USD"] == 50.0
    assert not overall_summary_u1.total_you_owe_by_currency.get("USD", 0.0) # Check it's 0 or not present
    assert overall_summary_u1.net_overall_balance_by_currency["USD"] == 50.0

    assert len(overall_summary_u1.breakdown_by_group) == 1
    group_perspective = overall_summary_u1.breakdown_by_group[0]
    assert group_perspective.group_id == group1.id
    assert group_perspective.your_net_balance_in_group == 50.0
    assert group_perspective.currency_code == "USD"

    assert len(overall_summary_u1.detailed_credits_by_currency["USD"]) == 1
    credit = overall_summary_u1.detailed_credits_by_currency["USD"][0]
    assert credit.owed_by_user_id == user2.id
    assert credit.amount == 50.0
    assert not overall_summary_u1.detailed_debts_by_currency.get("USD")

    overall_summary_u2 = await balance_service.calculate_user_overall_balances(user2.id, async_db_session)
    assert overall_summary_u2.total_you_owe_by_currency["USD"] == 50.0
    assert not overall_summary_u2.total_owed_to_you_by_currency.get("USD", 0.0)
    assert overall_summary_u2.net_overall_balance_by_currency["USD"] == -50.0
    assert len(overall_summary_u2.detailed_debts_by_currency["USD"]) == 1
    debt = overall_summary_u2.detailed_debts_by_currency["USD"][0]
    assert debt.owes_user_id == user1.id
    assert debt.amount == 50.0

@pytest.mark.asyncio
async def test_calculate_user_overall_balances_multiple_groups_currencies_complex(async_db_session: AsyncSession):
    u1 = await create_user(async_db_session, "u1", "u1@t.com", id=1)
    u2 = await create_user(async_db_session, "u2", "u2@t.com", id=2)
    u3 = await create_user(async_db_session, "u3", "u3@t.com", id=3)
    usd = await create_currency(async_db_session, "USD", "USD", id=1)
    eur = await create_currency(async_db_session, "EUR", "EUR", id=2)

    g1 = await create_group(async_db_session, "G1", u1.id, id=1) # u1, u2
    await add_user_to_group(async_db_session, u1.id, g1.id)
    await add_user_to_group(async_db_session, u2.id, g1.id)

    g2 = await create_group(async_db_session, "G2", u1.id, id=2) # u1, u3
    await add_user_to_group(async_db_session, u1.id, g2.id)
    await add_user_to_group(async_db_session, u3.id, g2.id)

    # G1: u1 paid 100 USD for u1,u2 (50 each). u2 owes u1 50 USD.
    await create_expense(async_db_session, "Lunch G1", 100.0, usd.id, u1.id, g1.id, participants_data=[
        {"user_id": u1.id, "share_amount": 50.0}, {"user_id": u2.id, "share_amount": 50.0}])
    # G1: u2 paid 80 EUR for u1,u2 (40 each). u1 owes u2 40 EUR.
    await create_expense(async_db_session, "Taxi G1", 80.0, eur.id, u2.id, g1.id, participants_data=[
        {"user_id": u1.id, "share_amount": 40.0}, {"user_id": u2.id, "share_amount": 40.0}])

    # G2: u1 paid 60 USD for u1,u3 (30 each). u3 owes u1 30 USD.
    await create_expense(async_db_session, "Coffee G2", 60.0, usd.id, u1.id, g2.id, participants_data=[
        {"user_id": u1.id, "share_amount": 30.0}, {"user_id": u3.id, "share_amount": 30.0}])
    # G2: u3 paid 20 EUR for u1,u3 (10 each). u1 owes u3 10 EUR.
    await create_expense(async_db_session, "Snacks G2", 20.0, eur.id, u3.id, g2.id, participants_data=[
        {"user_id": u1.id, "share_amount": 10.0}, {"user_id": u3.id, "share_amount": 10.0}])

    # User1 Overall:
    # Owed: 50 USD (by u2 from G1), 30 USD (by u3 from G2) => Total 80 USD owed to u1
    # Owes: 40 EUR (to u2 from G1), 10 EUR (to u3 from G2) => Total 50 EUR u1 owes

    summary_u1 = await balance_service.calculate_user_overall_balances(u1.id, async_db_session)

    assert summary_u1.total_owed_to_you_by_currency["USD"] == 80.0
    assert summary_u1.total_you_owe_by_currency["EUR"] == 50.0
    assert not summary_u1.total_you_owe_by_currency.get("USD", 0.0)
    assert not summary_u1.total_owed_to_you_by_currency.get("EUR", 0.0)

    assert summary_u1.net_overall_balance_by_currency["USD"] == 80.0
    assert summary_u1.net_overall_balance_by_currency["EUR"] == -50.0

    # Detailed debts for U1 (owes u2 40 EUR, owes u3 10 EUR)
    assert len(summary_u1.detailed_debts_by_currency["EUR"]) == 2
    u1_debt_to_u2 = next(d for d in summary_u1.detailed_debts_by_currency["EUR"] if d.owes_user_id == u2.id)
    u1_debt_to_u3 = next(d for d in summary_u1.detailed_debts_by_currency["EUR"] if d.owes_user_id == u3.id)
    assert u1_debt_to_u2.amount == 40.0
    assert u1_debt_to_u3.amount == 10.0

    # Detailed credits for U1 (owed by u2 50 USD, owed by u3 30 USD)
    assert len(summary_u1.detailed_credits_by_currency["USD"]) == 2
    u1_credit_from_u2 = next(c for c in summary_u1.detailed_credits_by_currency["USD"] if c.owed_by_user_id == u2.id)
    u1_credit_from_u3 = next(c for c in summary_u1.detailed_credits_by_currency["USD"] if c.owed_by_user_id == u3.id)
    assert u1_credit_from_u2.amount == 50.0
    assert u1_credit_from_u3.amount == 30.0

    # Breakdown by group for U1
    assert len(summary_u1.breakdown_by_group) == 4 # G1-USD, G1-EUR, G2-USD, G2-EUR

    g1_usd_perspective = next(b for b in summary_u1.breakdown_by_group if b.group_id == g1.id and b.currency_code == "USD")
    assert g1_usd_perspective.your_net_balance_in_group == 50.0 # Owed 50 USD by U2

    g1_eur_perspective = next(b for b in summary_u1.breakdown_by_group if b.group_id == g1.id and b.currency_code == "EUR")
    assert g1_eur_perspective.your_net_balance_in_group == -40.0 # Owes 40 EUR to U2

    g2_usd_perspective = next(b for b in summary_u1.breakdown_by_group if b.group_id == g2.id and b.currency_code == "USD")
    assert g2_usd_perspective.your_net_balance_in_group == 30.0 # Owed 30 USD by U3

    g2_eur_perspective = next(b for b in summary_u1.breakdown_by_group if b.group_id == g2.id and b.currency_code == "EUR")
    assert g2_eur_perspective.your_net_balance_in_group == -10.0 # Owes 10 EUR to U3


@pytest.mark.asyncio
async def test_calculate_group_balances_settled_expense(async_db_session: AsyncSession):
    user1 = await create_user(async_db_session, "user1", "user1@test.com", id=1)
    user2 = await create_user(async_db_session, "user2", "user2@test.com", id=2)
    currency_usd = await create_currency(async_db_session, "USD", "US Dollar", id=1)
    group1 = await create_group(async_db_session, "Group1", user1.id, id=1)
    await add_user_to_group(async_db_session, user1.id, group1.id)
    await add_user_to_group(async_db_session, user2.id, group1.id)

    # User1 paid 100 for User1 (50) and User2 (50). User2's share is 50.
    # User2's participation is partially settled by 20.
    await create_expense(
        async_db_session,
        description="Concert Tickets",
        amount=100.0,
        currency_id=currency_usd.id,
        paid_by_user_id=user1.id,
        group_id=group1.id,
        participants_data=[
            {"user_id": user1.id, "share_amount": 50.0},
            {"user_id": user2.id, "share_amount": 50.0, "settled_amount": 20.0},
        ],
    )

    summary = await balance_service.calculate_group_balances(group1.id, user1.id, async_db_session)
    user1_balance = next(mb for mb in summary.members_balances if mb.user_id == user1.id)
    user2_balance = next(mb for mb in summary.members_balances if mb.user_id == user2.id)

    # User2 originally owed 50, but 20 is settled. So, User2 owes User1 30.
    assert user1_balance.others_owe_user_total == 30.0
    assert user1_balance.credits_from_specific_users_by_currency["USD"][0].amount == 30.0

    assert user2_balance.owes_others_total == 30.0
    assert user2_balance.debts_to_specific_users_by_currency["USD"][0].amount == 30.0

@pytest.mark.asyncio
async def test_calculate_group_balances_fully_settled_expense_participant(async_db_session: AsyncSession):
    user1 = await create_user(async_db_session, "user1", "user1@test.com", id=1)
    user2 = await create_user(async_db_session, "user2", "user2@test.com", id=2)
    currency_usd = await create_currency(async_db_session, "USD", "US Dollar", id=1)
    group1 = await create_group(async_db_session, "Group1", user1.id, id=1)
    await add_user_to_group(async_db_session, user1.id, group1.id)
    await add_user_to_group(async_db_session, user2.id, group1.id)

    await create_expense(
        async_db_session,
        description="Event",
        amount=100.0,
        currency_id=currency_usd.id,
        paid_by_user_id=user1.id,
        group_id=group1.id,
        participants_data=[
            {"user_id": user1.id, "share_amount": 50.0},
            {"user_id": user2.id, "share_amount": 50.0, "settled_amount": 50.0}, # Fully settled
        ],
    )
    summary = await balance_service.calculate_group_balances(group1.id, user1.id, async_db_session)
    user1_balance = next(mb for mb in summary.members_balances if mb.user_id == user1.id)
    user2_balance = next(mb for mb in summary.members_balances if mb.user_id == user2.id)

    assert user1_balance.others_owe_user_total == 0.0
    assert not user1_balance.credits_from_specific_users_by_currency.get("USD")

    assert user2_balance.owes_others_total == 0.0
    assert not user2_balance.debts_to_specific_users_by_currency.get("USD")

# TODO: Add more tests for calculate_user_overall_balances, especially with settlements affecting overall picture.
# For instance, a debt in one group might be offset by a credit in another, and how settlements affect this.
# The current overall balance calculation re-evaluates debts globally, which should correctly handle this.
# A test ensuring settlements are factored into the global calculation would be good.

@pytest.mark.asyncio
async def test_user_overall_balances_with_settlement_affecting_global(async_db_session: AsyncSession):
    u1 = await create_user(async_db_session, "u1", "u1@t.com", id=1)
    u2 = await create_user(async_db_session, "u2", "u2@t.com", id=2)
    usd = await create_currency(async_db_session, "USD", "USD", id=1)

    g1 = await create_group(async_db_session, "G1", u1.id, id=1)
    await add_user_to_group(async_db_session, u1.id, g1.id)
    await add_user_to_group(async_db_session, u2.id, g1.id)

    # G1: u1 paid 100 USD for u1,u2 (50 each). u2 owes u1 50 USD.
    # u2's share is partially settled by 20 USD.
    await create_expense(async_db_session, "Big Dinner G1", 100.0, usd.id, u1.id, g1.id, participants_data=[
        {"user_id": u1.id, "share_amount": 50.0},
        {"user_id": u2.id, "share_amount": 50.0, "settled_amount": 20.0} # u2 owes 30 USD
    ])

    # G2: u2 paid 40 USD for u1,u2 (20 each). u1 owes u2 20 USD.
    g2 = await create_group(async_db_session, "G2", u1.id, id=2)
    await add_user_to_group(async_db_session, u1.id, g2.id)
    await add_user_to_group(async_db_session, u2.id, g2.id)
    await create_expense(async_db_session, "Small Lunch G2", 40.0, usd.id, u2.id, g2.id, participants_data=[
        {"user_id": u1.id, "share_amount": 20.0}, # u1 owes 20 USD
        {"user_id": u2.id, "share_amount": 20.0}
    ])

    # Overall:
    # u1 is owed 30 USD by u2 (from G1).
    # u1 owes 20 USD to u2 (from G2).
    # Net: u1 is owed 10 USD by u2.

    summary_u1 = await balance_service.calculate_user_overall_balances(u1.id, async_db_session)

    assert summary_u1.total_owed_to_you_by_currency.get("USD", 0.0) == 30.0 # From G1 after settlement
    assert summary_u1.total_you_owe_by_currency.get("USD", 0.0) == 20.0    # From G2
    assert summary_u1.net_overall_balance_by_currency.get("USD", 0.0) == 10.0

    assert len(summary_u1.detailed_credits_by_currency.get("USD", [])) == 1
    assert summary_u1.detailed_credits_by_currency["USD"][0].owed_by_user_id == u2.id
    assert summary_u1.detailed_credits_by_currency["USD"][0].amount == 10.0 # Net amount u2 owes u1

    assert not summary_u1.detailed_debts_by_currency.get("USD")


    summary_u2 = await balance_service.calculate_user_overall_balances(u2.id, session)
    # u2 owes 30 USD to u1 (from G1 after settlement)
    # u2 is owed 20 USD by u1 (from G2)
    # Net: u2 owes 10 USD to u1
    assert summary_u2.total_you_owe_by_currency.get("USD", 0.0) == 30.0
    assert summary_u2.total_owed_to_you_by_currency.get("USD", 0.0) == 20.0
    assert summary_u2.net_overall_balance_by_currency.get("USD", 0.0) == -10.0

    assert len(summary_u2.detailed_debts_by_currency.get("USD", [])) == 1
    assert summary_u2.detailed_debts_by_currency["USD"][0].owes_user_id == u1.id
    assert summary_u2.detailed_debts_by_currency["USD"][0].amount == 10.0 # Net amount u2 owes u1
    assert not summary_u2.detailed_credits_by_currency.get("USD")
