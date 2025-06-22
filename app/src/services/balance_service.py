from typing import Dict, List, Tuple
from collections import defaultdict
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, col
from sqlalchemy.orm import selectinload

from app.src.models.models import User, Group, Expense, ExpenseParticipant, Currency, Transaction # Added Transaction
from app.src.models.schemas import (
    DebtDetail,
    CreditDetail,
    UserGroupBalance,
    GroupBalanceSummary,
    GroupBalanceUserPerspective,
    UserOverallBalance,
    UserRead,
)


async def calculate_group_balances(
    group_id: int, db_user_id: int, session: AsyncSession
) -> GroupBalanceSummary:
    """
    Calculates who owes whom within a specific group.
    Considers settled amounts and different currencies.
    """
    group_stmt = await session.exec(
        select(Group)
        .where(Group.id == group_id)
        .options(
            selectinload(Group.members),
            selectinload(Group.expenses)
            .selectinload(Expense.currency),  # Load currency for each expense
            selectinload(Group.expenses)
            .selectinload(Expense.paid_by), # Load payer for each expense
            selectinload(Group.expenses)
            .selectinload(Expense.all_participant_details)
            .selectinload(ExpenseParticipant.user), # Load user for each participant
            selectinload(Group.expenses)
            .selectinload(Expense.all_participant_details)
            .selectinload(ExpenseParticipant.transaction) # For settled amounts
            .selectinload(Transaction.currency), # Currency of settlement transaction (if needed)
        )
    )
    group = group_stmt.one_or_none()

    if not group:
        # Or raise HTTPException(status_code=404, detail="Group not found")
        return GroupBalanceSummary(group_id=group_id, group_name="Not Found", members_balances=[])

    # Check if the requesting user is a member of the group (optional, could be handled at router level)
    # if not any(member.id == db_user_id for member in group.members):
    #     # Or raise HTTPException(status_code=403, detail="User not member of group")
    #     return GroupBalanceSummary(group_id=group_id, group_name=group.name, members_balances=[])


    # Initialize balances for all members
    # Balances: Dict[Tuple[user_id_debtor, user_id_creditor, currency_code], amount_owed]
    # Positive amount means debtor owes creditor.
    member_net_balances: Dict[Tuple[int, int, str], float] = defaultdict(float)

    for expense in group.expenses:
        if not expense.currency: # Should not happen if data is consistent
            continue

        expense_currency_code = expense.currency.code
        payer_id = expense.paid_by_user_id

        for participant_detail in expense.all_participant_details:
            debtor_id = participant_detail.user_id

            if debtor_id == payer_id:
                continue # Payer does not owe themselves for their own payment

            share_amount = participant_detail.share_amount

            # Adjust for settled amounts
            # This assumes settlement currency is the same as expense currency.
            # If settlement can be in a different currency, conversion would be needed here.
            # For now, we assume settled_amount_in_transaction_currency is comparable to share_amount.
            if participant_detail.settled_amount_in_transaction_currency:
                share_amount -= participant_detail.settled_amount_in_transaction_currency

            if share_amount <= 0: # Fully settled or over-settled
                continue

            # Debtor owes Payer
            member_net_balances[(debtor_id, payer_id, expense_currency_code)] += share_amount

    # Simplify debts: If A owes B $10 and B owes A $5 (in same currency), then A owes B $5.
    simplified_balances: Dict[Tuple[int, int, str], float] = defaultdict(float)
    processed_pairs_currencies = set()

    for (user_a_id, user_b_id, currency_code), amount_a_owes_b in member_net_balances.items():
        if (user_a_id, user_b_id, currency_code) in processed_pairs_currencies or \
           (user_b_id, user_a_id, currency_code) in processed_pairs_currencies:
            continue

        amount_b_owes_a = member_net_balances.get((user_b_id, user_a_id, currency_code), 0.0)

        net_a_owes_b = amount_a_owes_b - amount_b_owes_a

        if net_a_owes_b > 0:
            simplified_balances[(user_a_id, user_b_id, currency_code)] = net_a_owes_b
        elif net_a_owes_b < 0:
            simplified_balances[(user_b_id, user_a_id, currency_code)] = -net_a_owes_b

        processed_pairs_currencies.add((user_a_id, user_b_id, currency_code))
        processed_pairs_currencies.add((user_b_id, user_a_id, currency_code))


    # Construct the GroupBalanceSummary response
    member_user_map = {member.id: member for member in group.members}
    user_group_balances: List[UserGroupBalance] = []

    for member_id, member_user_obj in member_user_map.items():
        user_balance = UserGroupBalance(
            user_id=member_id,
            username=member_user_obj.username,
            # owes_others_total, others_owe_user_total, net_balance_in_group will be calculated per currency later
            # For now, initialize with empty dicts for by_currency fields
            debts_to_specific_users_by_currency=defaultdict(list),
            credits_from_specific_users_by_currency=defaultdict(list),
        )

        total_owes_for_member_by_currency = defaultdict(float)
        total_owed_to_member_by_currency = defaultdict(float)

        for (debtor_id, creditor_id, currency_code), amount in simplified_balances.items():
            if debtor_id == member_id: # This member (member_id) owes creditor_id
                creditor_user_obj = member_user_map.get(creditor_id)
                if creditor_user_obj:
                    debt_detail = DebtDetail(
                        owes_user_id=creditor_id,
                        owes_username=creditor_user_obj.username,
                        amount=amount,
                        currency_code=currency_code,
                    )
                    user_balance.debts_to_specific_users_by_currency[currency_code].append(debt_detail)
                    total_owes_for_member_by_currency[currency_code] += amount

            elif creditor_id == member_id: # This member (member_id) is owed by debtor_id
                debtor_user_obj = member_user_map.get(debtor_id)
                if debtor_user_obj:
                    credit_detail = CreditDetail(
                        owed_by_user_id=debtor_id,
                        owed_by_username=debtor_user_obj.username,
                        amount=amount,
                        currency_code=currency_code,
                    )
                    user_balance.credits_from_specific_users_by_currency[currency_code].append(credit_detail)
                    total_owed_to_member_by_currency[currency_code] += amount

        # Calculate overall totals for this member (can be complex if multiple currencies)
        # For simplicity, we'll leave the single float fields as 0 or sum them if only one currency.
        # The by_currency fields provide the precise breakdown.
        # If we need a single value for owes_others_total, it implies conversion to a common currency.
        # For now, we'll sum them up if there's only one currency involved for this user, otherwise 0.

        if len(total_owes_for_member_by_currency) == 1:
            user_balance.owes_others_total = list(total_owes_for_member_by_currency.values())[0]
        # else: sum across currencies if a primary currency is defined, or keep 0.

        if len(total_owed_to_member_by_currency) == 1:
            user_balance.others_owe_user_total = list(total_owed_to_member_by_currency.values())[0]
        # else: sum across currencies or keep 0.

        user_balance.net_balance_in_group = user_balance.others_owe_user_total - user_balance.owes_others_total

        user_group_balances.append(user_balance)

    return GroupBalanceSummary(
        group_id=group.id,
        group_name=group.name,
        members_balances=user_group_balances,
    )


async def calculate_user_overall_balances(
    user_id: int, session: AsyncSession
) -> UserOverallBalance:
    """
    Calculates a user's net balance (total owed vs. total owing) across all their involvements.
    """
    user_stmt = await session.exec(
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.groups).selectinload(Group.members) # For group names and member details if needed later
        )
    )
    user = user_stmt.one_or_none()

    if not user:
        # Or raise HTTPException(status_code=404, detail="User not found")
        # Return an empty/default UserOverallBalance
        return UserOverallBalance(user_id=user_id)

    overall_balance = UserOverallBalance(
        user_id=user_id,
        # Initialize with defaultdicts for by_currency fields
        total_you_owe_by_currency=defaultdict(float),
        total_owed_to_you_by_currency=defaultdict(float),
        net_overall_balance_by_currency=defaultdict(float),
        breakdown_by_group=[],
        detailed_debts_by_currency=defaultdict(list),
        detailed_credits_by_currency=defaultdict(list),
    )

    for group_membership_link in user.groups: # user.groups here are actual Group objects due to relationship loading
        group_summary = await calculate_group_balances(group_membership_link.id, user_id, session)

        user_perspective_in_group = None

        for member_balance in group_summary.members_balances:
            if member_balance.user_id == user_id:
                # Calculate net balance for this user in this group, per currency
                net_in_group_by_currency = defaultdict(float)

                for currency_code, credits in member_balance.credits_from_specific_users_by_currency.items():
                    for credit in credits:
                        net_in_group_by_currency[currency_code] += credit.amount
                        # Aggregate to overall credits
                        overall_balance.total_owed_to_you_by_currency[currency_code] += credit.amount
                        # Add to detailed_credits_by_currency, ensuring no duplicates if user in multiple groups owes same person
                        # This requires careful aggregation based on (owed_by_user_id, currency_code)

                for currency_code, debts in member_balance.debts_to_specific_users_by_currency.items():
                    for debt in debts:
                        net_in_group_by_currency[currency_code] -= debt.amount
                        # Aggregate to overall debts
                        overall_balance.total_you_owe_by_currency[currency_code] += debt.amount
                        # Add to detailed_debts_by_currency

                # For GroupBalanceUserPerspective, we need one entry per currency for this group
                for currency_code, net_amount in net_in_group_by_currency.items():
                    overall_balance.breakdown_by_group.append(
                        GroupBalanceUserPerspective(
                            group_id=group_summary.group_id,
                            group_name=group_summary.group_name,
                            your_net_balance_in_group=net_amount,
                            currency_code=currency_code,
                        )
                    )
                break # Found the user's balance in this group

    # Aggregate detailed debts and credits across all groups
    # This is tricky because calculate_group_balances already gives simplified debts/credits within a group.
    # We need to sum these up globally.
    # For example, if User A owes User B $10 in Group 1 (USD) and $5 in Group 2 (USD),
    # UserOverallBalance should show User A owes User B $15 (USD).

    # Re-fetch all expenses involving the user to correctly aggregate global debts/credits
    # This is a more direct way to get overall debts/credits rather than summing up group-level simplifications.

    all_expenses_stmt = await session.exec(
        select(Expense)
        .join(ExpenseParticipant, Expense.id == ExpenseParticipant.expense_id)
        .where((Expense.paid_by_user_id == user_id) | (ExpenseParticipant.user_id == user_id))
        .options(
            selectinload(Expense.currency),
            selectinload(Expense.paid_by),
            selectinload(Expense.all_participant_details).selectinload(ExpenseParticipant.user),
            selectinload(Expense.all_participant_details).selectinload(ExpenseParticipant.transaction),
        )
        .distinct()
    )
    all_user_expenses = all_expenses_stmt.unique().all()

    # Similar to group calculation, but global: Dict[Tuple[debtor, creditor, currency], amount]
    global_net_balances: Dict[Tuple[int, int, str], float] = defaultdict(float)

    for expense in all_user_expenses:
        if not expense.currency:
            continue
        expense_currency_code = expense.currency.code
        payer_id = expense.paid_by_user_id

        for p_detail in expense.all_participant_details:
            debtor_id = p_detail.user_id
            if debtor_id == payer_id:
                continue

            share = p_detail.share_amount
            if p_detail.settled_amount_in_transaction_currency:
                # Assuming settlement currency matches expense currency for now
                share -= p_detail.settled_amount_in_transaction_currency

            if share <= 0:
                continue

            global_net_balances[(debtor_id, payer_id, expense_currency_code)] += share

    # Simplify global balances
    simplified_global_balances: Dict[Tuple[int, int, str], float] = defaultdict(float)
    processed_global_pairs = set()

    for (debtor_id, creditor_id, currency_code), amount_debtor_owes_creditor in global_net_balances.items():
        pair_key = tuple(sorted((debtor_id, creditor_id))) + (currency_code,)
        if pair_key in processed_global_pairs:
            continue

        amount_creditor_owes_debtor = global_net_balances.get((creditor_id, debtor_id, currency_code), 0.0)

        net_debtor_owes_creditor = amount_debtor_owes_creditor - amount_creditor_owes_debtor

        if net_debtor_owes_creditor > 0:
            simplified_global_balances[(debtor_id, creditor_id, currency_code)] = net_debtor_owes_creditor
        elif net_debtor_owes_creditor < 0:
            simplified_global_balances[(creditor_id, debtor_id, currency_code)] = -net_debtor_owes_creditor

        processed_global_pairs.add(pair_key)

    # Populate UserOverallBalance.detailed_debts_by_currency and detailed_credits_by_currency
    # And also recalculate total_you_owe_by_currency, total_owed_to_you_by_currency

    overall_balance.total_you_owe_by_currency.clear()
    overall_balance.total_owed_to_you_by_currency.clear()
    overall_balance.detailed_debts_by_currency.clear()
    overall_balance.detailed_credits_by_currency.clear()

    # Temporary map to fetch user objects for usernames efficiently
    involved_user_ids = set()
    for debtor_id, creditor_id, _ in simplified_global_balances.keys():
        involved_user_ids.add(debtor_id)
        involved_user_ids.add(creditor_id)

    if involved_user_ids:
        users_stmt = await session.exec(select(User).where(col(User.id).in_(list(involved_user_ids))))
        involved_users_map = {u.id: u for u in users_stmt.all()}
    else:
        involved_users_map = {}


    for (debtor_id, creditor_id, currency_code), amount in simplified_global_balances.items():
        if debtor_id == user_id: # Current user (user_id) owes creditor_id
            creditor_obj = involved_users_map.get(creditor_id)
            if creditor_obj:
                debt_detail = DebtDetail(
                    owes_user_id=creditor_id,
                    owes_username=creditor_obj.username,
                    amount=amount,
                    currency_code=currency_code
                )
                overall_balance.detailed_debts_by_currency[currency_code].append(debt_detail)
                overall_balance.total_you_owe_by_currency[currency_code] += amount

        elif creditor_id == user_id: # Current user (user_id) is owed by debtor_id
            debtor_obj = involved_users_map.get(debtor_id)
            if debtor_obj:
                credit_detail = CreditDetail(
                    owed_by_user_id=debtor_id,
                    owed_by_username=debtor_obj.username,
                    amount=amount,
                    currency_code=currency_code
                )
                overall_balance.detailed_credits_by_currency[currency_code].append(credit_detail)
                overall_balance.total_owed_to_you_by_currency[currency_code] += amount

    # Calculate net_overall_balance_by_currency
    all_involved_currencies = set(overall_balance.total_you_owe_by_currency.keys()) | \
                              set(overall_balance.total_owed_to_you_by_currency.keys())

    for currency_code in all_involved_currencies:
        owed = overall_balance.total_owed_to_you_by_currency.get(currency_code, 0.0)
        owes = overall_balance.total_you_owe_by_currency.get(currency_code, 0.0)
        overall_balance.net_overall_balance_by_currency[currency_code] = owed - owes

    return overall_balance
