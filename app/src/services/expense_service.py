from typing import List
from sqlmodel import select, Session
from sqlmodel.ext.asyncio.session import AsyncSession # Use AsyncSession if your main app uses it

from src.models.models import Expense, ExpenseParticipant


async def update_expense_settlement_status(expense_id: int, session: AsyncSession) -> bool:
    """
    Checks if all participants of an expense have settled their shares.
    If so, marks the expense as settled.

    Args:
        expense_id: The ID of the expense to check.
        session: The database session.

    Returns:
        True if the expense is now settled, False otherwise.
    """
    # Get the expense
    expense = await session.get(Expense, expense_id)
    if not expense:
        # Or raise an exception, depending on desired error handling
        return False

    # Get all participant records for this expense
    participant_stmt = select(ExpenseParticipant).where(
        ExpenseParticipant.expense_id == expense_id
    )
    participant_results = await session.exec(participant_stmt)
    participants: List[ExpenseParticipant] = participant_results.all()

    if not participants:
        # If an expense has no participants, it could be considered settled by default,
        # especially if amount is 0. Or, if amount > 0, this implies the payer covers it all.
        # For now, if amount > 0 and no participants, it's not "settled" in terms of reimbursement.
        # However, the create_expense logic ensures the payer is a participant if amount > 0.
        # If amount is 0, it's trivially settled.
        if expense.amount == 0:
            if not expense.is_settled:
                expense.is_settled = True
                session.add(expense)
                # await session.commit() # Commit should be handled by the calling router function
                await session.flush()
            return True
        return False # Or handle as an anomaly if an expense with amount > 0 has no participants

    all_participants_settled = True
    for p in participants:
        # A participant is settled if their settled_transaction_id is not None
        # and the settled_amount_in_transaction_currency covers their share_amount.
        # For simplicity, we assume direct comparison is fine if currencies are consistent.
        # The problem statement mentions currency consistency is enforced for now.
        is_settled = False
        if p.settled_transaction_id is not None:
            if p.settled_amount_in_transaction_currency is not None and \
               p.settled_amount_in_transaction_currency >= p.share_amount:
                is_settled = True
            elif p.share_amount == 0: # If share is zero, it's considered settled.
                 is_settled = True


        if not is_settled:
            all_participants_settled = False
            break

    if all_participants_settled:
        if not expense.is_settled: # Only update if state changes
            expense.is_settled = True
            session.add(expense)
            # await session.commit() # Commit handled by caller
            await session.flush()
        return True
    else:
        # If any participant is not settled, ensure the expense is marked as not settled
        if expense.is_settled: # Only update if state changes
            expense.is_settled = False
            session.add(expense)
            # await session.commit() # Commit handled by caller
            await session.flush()
        return False
