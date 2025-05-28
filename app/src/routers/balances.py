from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, aliased # Added aliased
from sqlalchemy import or_

from src.db.database import get_session # Corrected import: Removed 'app.'
from src.models.models import User, Expense, ExpenseParticipant, Currency # Corrected import: Removed 'app.'
from src.models.schemas import UserBalanceResponse, CurrencyBalance, CurrencyRead, UserRead # Corrected import: Removed 'app.'
from src.core.security import get_current_user # Corrected import: Changed path and removed 'app.'

router = APIRouter(prefix="/api/v1/balances", tags=["Balances"])

# Endpoint will be implemented in the next step
@router.get("/me", response_model=UserBalanceResponse)
async def get_user_balances(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    balances_by_currency: Dict[int, CurrencyBalance] = {}

    # Fetch all expenses involving the current user
    # This query fetches expenses where the user is either the payer or a participant.
    
    ep_alias = aliased(ExpenseParticipant) # Alias for explicit join for WHERE clause
    
    query = (
        select(Expense)
        .outerjoin(ep_alias, Expense.id == ep_alias.expense_id) # Explicit outer join
        .where(
            or_(
                Expense.paid_by_user_id == current_user.id,
                ep_alias.user_id == current_user.id # Condition on aliased table
            )
        )
        .options(
            selectinload(Expense.currency),
            selectinload(Expense.participants), 
            selectinload(Expense.paid_by) 
        )
        .distinct()
    )
    result = await session.execute(query) # Use session.execute for SQLModel < 0.0.16 or if session.exec is not preferred
    expenses = result.scalars().all()

    for expense in expenses:
        if expense.currency_id is None or expense.currency is None:
            # This case should ideally not happen if data integrity is maintained.
            # Consider logging a warning or raising an error.
            continue

        currency_id = expense.currency_id
        if currency_id not in balances_by_currency:
            balances_by_currency[currency_id] = CurrencyBalance(
                currency=CurrencyRead.model_validate(expense.currency),
                total_paid=0.0,
                net_owed_to_user=0.0,
                net_user_owes=0.0
            )
        
        current_currency_balance = balances_by_currency[currency_id]

        # current_currency_balance has been initialized or found.
        # Now, calculate paid amounts and shares.

        # Fetch all ExpenseParticipant entries for the current expense
        # This needs to be inside the loop over expenses.
        # Explicitly select columns to ensure they are available on the resulting Row objects.
        result_participant_links = (await session.exec(
            select(ExpenseParticipant.user_id, ExpenseParticipant.share_amount)
            .where(ExpenseParticipant.expense_id == expense.id)
        )).all() # result_participant_links will be a list of Row objects

        if expense.paid_by_user_id == current_user.id:
            current_currency_balance.total_paid += expense.amount
            for link_data in result_participant_links: # link_data is a Row
                if link_data.user_id != current_user.id: # User who is not the payer
                    current_currency_balance.net_owed_to_user += link_data.share_amount or 0.0
        else:
            # User is a participant, not the payer.
            # Find their share in this specific expense.
            for link_data in result_participant_links: # link_data is a Row
                if link_data.user_id == current_user.id:
                    current_currency_balance.net_user_owes += link_data.share_amount or 0.0
    
    return UserBalanceResponse(balances=list(balances_by_currency.values()))
