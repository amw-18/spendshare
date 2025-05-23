from typing import List, Optional, Tuple # Ensure Tuple is imported if used
from sqlmodel.ext.asyncio.session import AsyncSession # Use AsyncSession
from sqlmodel import select

from app.models.models import Expense, User, Group, ExpenseParticipant
from app.models.schemas import ExpenseCreate, ExpenseUpdate

async def create_expense(session: AsyncSession, *, expense_in: ExpenseCreate, paid_by_user_id: int) -> Expense:
    # The `paid_by_user_id` in args is a bit redundant if ExpenseCreate already mandates it.
    # Assuming ExpenseCreate is the source of truth for these fields.
    db_expense = Expense.model_validate(expense_in)
    # db_expense.paid_by_user_id = paid_by_user_id # This is set if expense_in has it.

    session.add(db_expense)
    await session.commit()
    await session.refresh(db_expense)
    return db_expense

async def get_expense(session: AsyncSession, expense_id: int) -> Optional[Expense]:
    return await session.get(Expense, expense_id)

async def get_expenses(session: AsyncSession, skip: int = 0, limit: int = 100) -> List[Expense]:
    statement = select(Expense).offset(skip).limit(limit)
    results = await session.exec(statement)
    return results.all()

async def get_expenses_for_user(session: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> List[Expense]:
    # Expenses where the user is the payer OR a participant.
    # For now, let's get expenses paid by the user.
    # TODO: Expand this to include participation using ExpenseParticipant table.
    # from sqlalchemy import or_ # if using SQLAlchemy style 'or'
    
    # Paid by user:
    stmt_paid_by = select(Expense).where(Expense.paid_by_user_id == user_id)
    
    # Participated by user:
    # stmt_participated_in = (
    #     select(Expense)
    #     .join(ExpenseParticipant, Expense.id == ExpenseParticipant.expense_id)
    #     .where(ExpenseParticipant.user_id == user_id)
    # )
    # combined_stmt = select(Expense).distinct().where(
    #     or_(
    #         Expense.id.in_(select(stmt_paid_by.with_only_columns(Expense.id))),
    #         Expense.id.in_(select(stmt_participated_in.with_only_columns(Expense.id)))
    #     )
    # ).offset(skip).limit(limit)
    # For simplicity now, only paid_by:
    
    results = await session.exec(stmt_paid_by.offset(skip).limit(limit))
    return results.all()


async def get_expenses_for_group(session: AsyncSession, group_id: int, skip: int = 0, limit: int = 100) -> List[Expense]:
    statement = (
        select(Expense)
        .where(Expense.group_id == group_id)
        .offset(skip)
        .limit(limit)
    )
    results = await session.exec(statement)
    return results.all()

async def update_expense(session: AsyncSession, *, db_expense: Expense, expense_in: ExpenseUpdate) -> Expense:
    expense_data = expense_in.model_dump(exclude_unset=True)
    for key, value in expense_data.items():
        setattr(db_expense, key, value)
    session.add(db_expense)
    await session.commit()
    await session.refresh(db_expense)
    return db_expense

async def delete_expense(session: AsyncSession, *, db_expense: Expense) -> Expense:
    # Consider cascade deletes for ExpenseParticipant or handle manually.
    # Example:
    # stmt_participants = select(ExpenseParticipant).where(ExpenseParticipant.expense_id == db_expense.id)
    # participant_links_results = await session.exec(stmt_participants)
    # for link in participant_links_results.all():
    #     await session.delete(link)
    # await session.commit() # commit deletion of links

    await session.delete(db_expense)
    await session.commit()
    return db_expense # Object is expired

async def add_participant_to_expense(
    session: AsyncSession, *, expense_id: int, user_id: int, share_amount: Optional[float] = None
) -> Optional[Expense]: # Returns Expense to allow refreshing it, or None if fundamental issue
    db_expense = await session.get(Expense, expense_id)
    # User existence check can be done here or assumed valid if IDs are from trusted source
    user_to_add = await session.get(User, user_id) 

    if not db_expense or not user_to_add:
        return None 

    link_exists_statement = select(ExpenseParticipant).where(
        ExpenseParticipant.expense_id == expense_id, ExpenseParticipant.user_id == user_id
    )
    link_exists_result = await session.exec(link_exists_statement)
    
    if not link_exists_result.first():
        participant_link = ExpenseParticipant(
            expense_id=expense_id, user_id=user_id, share_amount=share_amount
        )
        session.add(participant_link)
        await session.commit()
        await session.refresh(db_expense) # Refresh to load new participant
    return db_expense

async def remove_participant_from_expense(session: AsyncSession, *, expense_id: int, user_id: int) -> Optional[Expense]:
    db_expense = await session.get(Expense, expense_id)
    # User existence check
    user_to_remove = await session.get(User, user_id)

    if not db_expense or not user_to_remove:
        return None

    statement = select(ExpenseParticipant).where(
        ExpenseParticipant.expense_id == expense_id, ExpenseParticipant.user_id == user_id
    )
    link_to_delete_result = await session.exec(statement)
    link_to_delete = link_to_delete_result.first()

    if link_to_delete:
        await session.delete(link_to_delete)
        await session.commit()
        await session.refresh(db_expense) 
    return db_expense

# Placeholder for more complex expense logic (remains synchronous if not DB bound, or make async if it is)
async def calculate_expense_splits(session: AsyncSession, expense_id: int):
    # This function would:
    # 1. Get the expense and its participants (async).
    # 2. If no specific shares, divide equally.
    # 3. Update share_amount for each participant in ExpenseParticipant table (async).
    # For now, this is a placeholder.
    pass
