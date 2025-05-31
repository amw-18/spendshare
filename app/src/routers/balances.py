from typing import Dict
from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload
from sqlalchemy import or_

from src.db.database import get_session
from src.models.models import (
    User,
    Expense,
    ExpenseParticipant,
)
from src.models.schemas import (
    UserBalanceResponse,
    CurrencyBalance,
    CurrencyRead,
)
from src.core.security import (
    get_current_user,
)

router = APIRouter(prefix="/api/v1/balances", tags=["Balances"])


@router.get("/me", response_model=UserBalanceResponse)
async def get_user_balances(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    balances_by_currency: Dict[int, CurrencyBalance] = {}
    query = (
        select(Expense)
        .outerjoin(ExpenseParticipant, Expense.id == ExpenseParticipant.expense_id)
        .where(
            or_(
                Expense.paid_by_user_id == current_user.id,
                ExpenseParticipant.user_id == current_user.id,
            )
        )
        .options(
            selectinload(Expense.currency),
            selectinload(Expense.participants),
            selectinload(Expense.paid_by),
        )
        .distinct()
    )
    expenses = await session.exec(query)
    for expense in expenses:
        currency_id = expense.currency_id
        if currency_id not in balances_by_currency:
            balances_by_currency[currency_id] = CurrencyBalance(
                currency=CurrencyRead.model_validate(expense.currency),
                total_paid=0.0,
                net_owed_to_user=0.0,
                net_user_owes=0.0,
            )

        current_currency_balance = balances_by_currency[currency_id]
        result_participant_links = list(
            await session.exec(
                select(
                    ExpenseParticipant.user_id, ExpenseParticipant.share_amount
                ).where(ExpenseParticipant.expense_id == expense.id)
            )
        )

        if expense.paid_by_user_id == current_user.id:
            current_currency_balance.total_paid += expense.amount
            for participant_id, share_amount in result_participant_links:
                if participant_id != current_user.id:  # User who is not the payer
                    current_currency_balance.net_owed_to_user += share_amount or 0.0
        else:
            for participant_id, share_amount in result_participant_links:
                if participant_id == current_user.id:  # User who is the payer
                    current_currency_balance.net_user_owes += share_amount or 0.0

    return UserBalanceResponse(balances=list(balances_by_currency.values()))
