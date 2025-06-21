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
    UserOverallBalance, # Changed from UserBalanceResponse
    GroupBalanceSummary,
    # CurrencyBalance, # No longer directly used here
    # CurrencyRead, # No longer directly used here
)
from src.core.security import (
    get_current_user,
)
# Import the new service
from src.services.balance_service import BalanceService, get_balance_service
from src.models import schemas # Ensure schemas is available for response_model

router = APIRouter(prefix="/api/v1/balances", tags=["Balances"])


@router.get("/me", response_model=schemas.UserOverallBalance) # Updated response_model
async def get_my_overall_balances( # Renamed for clarity
    current_user: User = Depends(get_current_user),
    balance_service: BalanceService = Depends(get_balance_service),
):
    """
    Retrieves the overall balance for the currently authenticated user.
    This includes a breakdown by group and detailed lists of debts and credits
    aggregated across all groups.
    """
    if current_user.id is None:
        # This should ideally not happen if get_current_user works correctly
        # and user always has an ID after being fetched/authenticated.
        raise HTTPException(status_code=400, detail="User ID not available.")

    overall_balance = await balance_service.calculate_user_overall_balances(user_id=current_user.id)
    return overall_balance


@router.get("/groups/{group_id}", response_model=schemas.GroupBalanceSummary)
async def get_group_balances(
    group_id: int,
    current_user: User = Depends(get_current_user),
    balance_service: BalanceService = Depends(get_balance_service),
    # session: AsyncSession = Depends(get_session) # Can be removed if balance_service handles session
):
    """
    Retrieves the balance summary for a specific group.
    Shows who owes whom within the group.
    Requires the current user to be a member of the group.
    """
    if current_user.id is None:
        raise HTTPException(status_code=400, detail="User ID not available.")

    try:
        group_balance_summary = await balance_service.calculate_group_balances(
            group_id=group_id, requesting_user_id=current_user.id
        )
        return group_balance_summary
    except ValueError as e: # Catch specific errors from service for proper HTTP responses
        raise HTTPException(status_code=404, detail=str(e)) # e.g., Group not found
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) # e.g., User not member of group
    except Exception as e:
        # Generic error handler for unexpected issues
        # Log this error server-side
        raise HTTPException(status_code=500, detail="An unexpected error occurred while calculating group balances.")

# Need to import HTTPException
from fastapi import HTTPException

# The old /me endpoint logic is now encapsulated within balance_service.calculate_user_overall_balances
# and the response model has changed from UserBalanceResponse to schemas.UserOverallBalance.
# The previous implementation of get_user_balances is removed.
