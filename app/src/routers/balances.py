from typing import Dict, List # Added List
from fastapi import APIRouter, Depends, HTTPException # Added HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import or_

from app.src.db.database import get_session # Corrected import path
from app.src.models.models import ( # Corrected import path
    User,
    Expense,
    ExpenseParticipant,
    Group, # Added Group
    UserGroupLink, # Added UserGroupLink
)
from app.src.models.schemas import ( # Corrected import path
    UserOverallBalance, # Changed from UserBalanceResponse
    GroupBalanceSummary, # Added
    # CurrencyBalance, # No longer directly used here
    # CurrencyRead, # No longer directly used here
)
from app.src.core.security import ( # Corrected import path
    get_current_user,
)
from app.src.services import balance_service # Added balance_service import

router = APIRouter(prefix="/api/v1", tags=["Balances"]) # Prefix changed to /api/v1 for consistency if other routers use it


@router.get("/balances/me", response_model=UserOverallBalance) # Path changed for clarity
async def get_my_overall_balances( # Function name changed
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves the overall balance summary for the currently authenticated user.
    This includes total amounts owed, total amounts owed to the user,
    a breakdown by group, and detailed lists of debts and credits, all by currency.
    """
    if not current_user.id:
        raise HTTPException(status_code=400, detail="User ID not available")

    overall_balances = await balance_service.calculate_user_overall_balances(
        user_id=current_user.id, session=session
    )
    return overall_balances


@router.get("/groups/{group_id}/balances", response_model=GroupBalanceSummary)
async def get_group_balances_summary( # Function name changed
    group_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves the balance summary for a specific group.
    This includes a list of members and their net balances within the group,
    detailing who owes whom for what amounts, broken down by currency.
    The requesting user must be a member of the group.
    """
    # Verify group existence and user membership
    group_membership_stmt = await session.exec(
        select(Group)
        .join(UserGroupLink, Group.id == UserGroupLink.group_id)
        .where(Group.id == group_id)
        .where(UserGroupLink.user_id == current_user.id)
        .options(selectinload(Group.members)) # Preload members to check membership without another query if needed by service
    )
    group = group_membership_stmt.one_or_none()

    if not group:
        # Check if group exists at all to differentiate between "not found" and "not a member"
        group_exists_stmt = await session.exec(select(Group).where(Group.id == group_id))
        if not group_exists_stmt.one_or_none():
            raise HTTPException(status_code=404, detail=f"Group with ID {group_id} not found.")
        else:
            raise HTTPException(
                status_code=403,
                detail=f"User is not a member of group with ID {group_id} or group does not exist.",
            )

    if not current_user.id:
         raise HTTPException(status_code=400, detail="User ID not available")

    group_balance_summary = await balance_service.calculate_group_balances(
        group_id=group_id, db_user_id=current_user.id, session=session
    )
    if not group_balance_summary.members_balances and group_balance_summary.group_name == "Not Found": # Check based on service return for non-existent group
        raise HTTPException(status_code=404, detail=f"Group with ID {group_id} not found during balance calculation.")

    return group_balance_summary
