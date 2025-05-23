from typing import List, Optional, Dict
from sqlmodel.ext.asyncio.session import AsyncSession  # Use AsyncSession

from app.models.models import Expense, User, Group
from app.models.schemas import ExpenseCreate
from app.crud import crud_expense, crud_user, crud_group  # These are now async modules


async def create_expense_with_participants(  # async def
    session: AsyncSession,  # AsyncSession
    *,
    expense_in: ExpenseCreate,
    participant_user_ids: List[int],
) -> Optional[Expense]:
    # Verify paid_by_user exists
    payer = await crud_user.get_user(session, expense_in.paid_by_user_id)
    if not payer:
        return None

    if expense_in.group_id:
        group = await crud_group.get_group(session, expense_in.group_id)
        if not group:
            return None

    all_participants_in_expense_users = []
    users_sharing_expense_ids = set(participant_user_ids)
    if not participant_user_ids:
        users_sharing_expense_ids.add(expense_in.paid_by_user_id)

    for user_id in users_sharing_expense_ids:
        user = await crud_user.get_user(session, user_id)
        if not user:
            return None
        all_participants_in_expense_users.append(user)

    if not all_participants_in_expense_users:
        return None

    db_expense = await crud_expense.create_expense(
        session=session, expense_in=expense_in
    )
    if not db_expense:
        return None

    num_participants = len(all_participants_in_expense_users)
    share_amount = None
    if num_participants > 0:
        share_amount = round(db_expense.amount / num_participants, 2)

    for user_obj in all_participants_in_expense_users:
        await crud_expense.add_participant_to_expense(
            session=session,
            expense_id=db_expense.id,
            user_id=user_obj.id,
            share_amount=share_amount,
        )

    await session.refresh(
        db_expense
    )  # Ensure expense object is up-to-date after adding participants
    return db_expense


async def get_user_balances(
    session: AsyncSession, user_id: int
) -> Dict[str, float]:  # async def
    # This function will involve async calls to CRUD operations to fetch expenses
    # For now, it remains a placeholder but is marked async.
    # Example:
    # user_paid_expenses = await crud_expense.get_expenses_for_user(session, user_id)
    # user_participated_expenses = await crud_expense.get_expenses_where_user_participated(session, user_id) # Needs new CRUD
    return {"owed_to_user": 0.0, "user_owes": 0.0}
