from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from sqlalchemy import or_
from sqlalchemy.orm import selectinload

from src.db.database import get_session
from src.models.models import (
    Expense,
    User,
    Group,
    ExpenseParticipant,
    Currency,
)
from src.models import schemas
from src.core.security import get_current_user
from src.utils import get_object_or_404

router = APIRouter(
    prefix="/expenses",
    tags=["expenses"],
)


@router.post("/service/", response_model=schemas.ExpenseRead, status_code=status.HTTP_201_CREATED)
async def create_expense_with_participants_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    expense_in: schemas.ExpenseCreate,
    participant_user_ids: List[int] = Body(...),
    current_user: User = Depends(get_current_user),
) -> schemas.ExpenseRead:
    # Validate currency_id
    await get_object_or_404(session, Currency, expense_in.currency_id)

    if expense_in.group_id:
        group = await get_object_or_404(session, Group, expense_in.group_id)
        # Not assigning to 'group' as it's not used later, just checked for existence.

    all_participants_in_expense_users = []
    users_sharing_expense_ids = set(participant_user_ids)
    if not participant_user_ids:  # If list is empty, payer is the only participant
        users_sharing_expense_ids.add(current_user.id)

    for participant_id in users_sharing_expense_ids:
        participant = await get_object_or_404(session, User, participant_id)
        all_participants_in_expense_users.append(participant)

    db_expense = Expense.model_validate(
        expense_in, update={"paid_by_user_id": current_user.id}
    )
    session.add(db_expense)
    await session.commit()
    await session.refresh(db_expense)  # Refresh to get db_expense.id

    num_participants = len(all_participants_in_expense_users)
    share_amount = None
    if num_participants > 0:
        share_amount = round(db_expense.amount / num_participants, 2)

    for user_obj in all_participants_in_expense_users:
        expense_participant = ExpenseParticipant(
            user_id=user_obj.id,
            expense_id=db_expense.id,
            share_amount=share_amount,
        )
        session.add(expense_participant)

    await session.commit()
    await session.refresh(db_expense) # Refresh again after adding participants

    # Re-fetch with relationships for ExpenseRead using a select statement
    stmt = (
        select(Expense)
        .where(Expense.id == db_expense.id)
        .options(
            selectinload(Expense.currency),
            selectinload(Expense.paid_by)
        )
    )
    result = await session.exec(stmt)
    refreshed_db_expense = result.one_or_none()

    if not refreshed_db_expense:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to re-fetch expense after creation with full details")

    return await _get_expense_read_details(session=session, db_expense=refreshed_db_expense)


@router.post("/", response_model=schemas.ExpenseRead, status_code=status.HTTP_201_CREATED)
async def create_expense_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    expense_in: schemas.ExpenseCreate,
    current_user: User = Depends(get_current_user),
) -> schemas.ExpenseRead:
    # Validate currency_id
    await get_object_or_404(session, Currency, expense_in.currency_id)

    if expense_in.group_id:
        await get_object_or_404(session, Group, expense_in.group_id)  # Check existence

    db_expense = Expense.model_validate(
        expense_in, update={"paid_by_user_id": current_user.id}
    )
    session.add(db_expense)
    await session.commit()
    await session.refresh(db_expense)

    # Re-fetch with relationships for ExpenseRead using a select statement
    stmt = (
        select(Expense)
        .where(Expense.id == db_expense.id)
        .options(
            selectinload(Expense.currency),
            selectinload(Expense.paid_by)
        )
    )
    result = await session.exec(stmt)
    refreshed_db_expense = result.one_or_none()

    if not refreshed_db_expense:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to re-fetch expense after creation with full details")

    # Manually construct and return ExpenseRead with participant_details
    # For simple creation, participants are not added here, so participant_details will be empty.
    return await _get_expense_read_details(session=session, db_expense=refreshed_db_expense)


@router.get("/", response_model=List[schemas.ExpenseRead])
async def read_expenses_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    group_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
) -> List[Expense]:
    # Base query with eager loading
    statement = select(Expense).options(
        selectinload(Expense.currency),
        selectinload(Expense.paid_by)
    )
    if user_id:
        if not current_user.is_admin:
            # Non-admin users can only fetch their own expenses
            if user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions to fetch expenses for another user",
                )
        # At this point, either user is admin, or user_id matches current_user.id
        # Filter for expenses where the specified user_id is payer or participant.
        statement = (
            statement.outerjoin(
                ExpenseParticipant,
                Expense.id == ExpenseParticipant.expense_id,
            )
            .where(
                or_(
                    Expense.paid_by_user_id == user_id,
                    ExpenseParticipant.user_id == user_id,
                )
            )
            .offset(skip)
            .limit(limit)
        )
    elif group_id:
        statement = (
            statement.where(Expense.group_id == group_id).offset(skip).limit(limit)
        )
    else:  # No user_id or group_id provided
        if not current_user.is_admin:
            # Non-admin users see their own expenses
            statement = (
                statement.outerjoin(
                    ExpenseParticipant,
                    Expense.id == ExpenseParticipant.expense_id,
                )
                .where(
                    or_(
                        Expense.paid_by_user_id == current_user.id,
                        ExpenseParticipant.user_id == current_user.id,
                    )
                )
                .offset(skip)
                .limit(limit)
            )
        else:
            # Admin users see all expenses
            statement = statement.offset(skip).limit(limit)

    result = await session.exec(statement)
    expenses = list(result)
    return expenses


@router.get("/{expense_id}", response_model=schemas.ExpenseRead)
async def read_expense_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    expense_id: int,
    current_user: User = Depends(get_current_user),
) -> schemas.ExpenseRead:
    statement = (
        select(Expense)
        .where(Expense.id == expense_id)
        .options(
            selectinload(Expense.paid_by),
            selectinload(Expense.participants),
            selectinload(Expense.currency),
        )
    )
    result = await session.exec(statement)
    db_expense = result.first()

    if not db_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found"
        )

    if not current_user.is_admin and db_expense.paid_by_user_id != current_user.id:
        found = False
        for (
            participant
        ) in db_expense.participants:  # already loaded in sql using selectinload
            found = found or (current_user.id == participant.id)
        if not found:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this expense",
            )

    return await _get_expense_read_details(session=session, db_expense=db_expense)


# TODO:  audit/test this properly
@router.put("/{expense_id}", response_model=schemas.ExpenseRead)
async def update_expense_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    expense_id: int,
    expense_in: schemas.ExpenseUpdate,
    current_user: User = Depends(get_current_user),
) -> schemas.ExpenseRead:
    # TODO:
    # if the expense is in group, any group member should be allowed
    # otherwise, only the participants    # Fetch the expense with eager loading for currency and paid_by
    db_expense = await session.get(
        Expense, 
        expense_id, 
        options=[
            selectinload(Expense.currency),
            selectinload(Expense.paid_by)
        ]
    )
    if not db_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found"
        )
    # Update basic expense fields first
    expense_data = expense_in.model_dump(exclude_unset=True)

    # Keep track if amount changed for share recalculation
    amount_changed = (
        "amount" in expense_data and expense_data["amount"] != db_expense.amount
    )

    # Temporarily remove 'participants' from expense_data if it exists, handle it separately
    updated_participant_user_ids_input: Optional[List[int]] = None
    if "participants" in expense_data:
        participants_input_list = expense_data.pop("participants")
        if participants_input_list is not None:
            # The input `p` here is a dict from the JSON payload, not a ParticipantUpdate model instance directly from Pydantic parsing at this stage.
            updated_participant_user_ids_input = [
                p["user_id"] for p in participants_input_list
            ]

    for key, value in expense_data.items():
        setattr(db_expense, key, value)

    # Fetch existing participants from DB
    existing_participants_statement = select(ExpenseParticipant).where(
        ExpenseParticipant.expense_id == db_expense.id
    )
    result = await session.exec(existing_participants_statement)
    existing_participant_links = result.all()
    existing_participant_user_ids = {
        link.user_id for link in existing_participant_links
    }

    final_participant_user_ids = set(
        existing_participant_user_ids
    )  # Start with current participants

    if (
        updated_participant_user_ids_input is not None
    ):  # If 'participants' was in the input payload
        # Validate all incoming participant user_ids
        for user_id in updated_participant_user_ids_input:
            await get_object_or_404(session, User, user_id)  # Ensures user exists

        incoming_participant_user_ids_set = set(updated_participant_user_ids_input)

        # Determine users to remove
        user_ids_to_remove = (
            existing_participant_user_ids - incoming_participant_user_ids_set
        )
        for link_to_delete in [
            link
            for link in existing_participant_links
            if link.user_id in user_ids_to_remove
        ]:
            await session.delete(link_to_delete)

        final_participant_user_ids = incoming_participant_user_ids_set
        # Links for new users will be created/updated during share recalculation
        amount_changed = (
            True  # Force share recalculation if participants list is explicitly set
        )

    # Recalculate shares if amount changed or if participant list was explicitly provided
    if amount_changed and final_participant_user_ids:
        new_share_amount = round(db_expense.amount / len(final_participant_user_ids), 2)

        # Update existing or create new participant links
        current_links_map = {link.user_id: link for link in existing_participant_links}

        for user_id in final_participant_user_ids:
            if user_id in current_links_map:
                # User was already a participant, update their share
                link = current_links_map[user_id]
                if (
                    link.user_id not in user_ids_to_remove
                    if updated_participant_user_ids_input is not None
                    else True
                ):  # Check if not marked for removal
                    link.share_amount = new_share_amount
                    session.add(link)
            else:
                # New participant, create a new link
                new_link = ExpenseParticipant(
                    expense_id=db_expense.id,
                    user_id=user_id,
                    share_amount=new_share_amount,
                )
                session.add(new_link)
    elif (
        amount_changed and not final_participant_user_ids and existing_participant_links
    ):
        # Amount changed, but no participants specified in input, and no final participants (e.g. all removed)
        # This means all existing links should be removed if any existed before an explicit empty list.
        # This case is mostly covered if updated_participant_user_ids_input was an empty list.
        # If updated_participant_user_ids_input was None, and amount changed, and there are existing participants,
        # their shares should ideally be updated. This specific edge case might need refinement.
        # For now, if final_participant_user_ids is empty, all links are already removed or will be.
        pass

    # Handle paid_by_user_id and group_id checks after basic attributes are set on db_expense
    if (
        db_expense.paid_by_user_id is not None
    ):  # Check if it was set by the update or existed before
        await get_object_or_404(session, User, db_expense.paid_by_user_id)

    if (
        db_expense.group_id is not None
    ):  # Check if it was set by the update or existed before
        # Example TODOs from original code, kept for context if relevant to other logic
        # if db_expense.group_id == 0:
        #     pass
        # else:
        await get_object_or_404(session, Group, db_expense.group_id)

    if "currency_id" in expense_data and expense_data["currency_id"] is not None:
        await get_object_or_404(session, Currency, expense_data["currency_id"])
        # setattr will handle the update of db_expense.currency_id

    session.add(db_expense)
    await session.commit()
    await session.refresh(db_expense)

    # Re-fetch with relationships for ExpenseRead using a select statement
    stmt = (
        select(Expense)
        .where(Expense.id == db_expense.id)
        .options(
            selectinload(Expense.currency),
            selectinload(Expense.paid_by)
        )
    )
    result = await session.exec(stmt)
    refreshed_db_expense = result.one_or_none()

    if not refreshed_db_expense:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to re-fetch expense after update with full details")

    # Manually construct and return ExpenseRead with participant_details
    return await _get_expense_read_details(session=session, db_expense=refreshed_db_expense)


@router.delete("/{expense_id}", response_model=int)
async def delete_expense_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    expense_id: int,
    current_user: User = Depends(get_current_user),
) -> int:
    db_expense = await get_object_or_404(session, Expense, expense_id)

    if not current_user.is_admin and db_expense.paid_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this expense",
        )

    await session.delete(
        db_expense
    )  # should cascade delete related ExpenseParticipant entries
    await session.commit()
    return expense_id


async def _get_expense_read_details(
    session: AsyncSession, db_expense: Expense
) -> schemas.ExpenseRead:
    """
    Helper function to construct ExpenseRead schema with populated participant_details.
    This version explicitly accesses relationships and builds a dict for validation.
    """
    participant_links_statement = select(ExpenseParticipant).where(
        ExpenseParticipant.expense_id == db_expense.id
    )
    result = await session.exec(participant_links_statement)
    participant_links = result.all()

    participant_details_list = []
    for link in participant_links:
        # Fetch user with groups eagerly loaded for UserRead schema
        user_stmt = select(User).where(User.id == link.user_id).options(selectinload(User.groups))
        user_result = await session.exec(user_stmt)
        user = user_result.one_or_none()
        if not user:
            # This case should ideally not happen if DB integrity is maintained
            # and link.user_id is valid. But good to handle.
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Participant user with id {link.user_id} not found"
            )
        
        participant_details_list.append(
            schemas.ExpenseParticipantReadWithUser(
                user_id=link.user_id,
                expense_id=link.expense_id,
                share_amount=link.share_amount,
                user=schemas.UserRead.model_validate(user), # UserRead expects groups
            )
        )

    # Explicitly access relationship attributes. This will fail if not loaded.
    # We expect these to be pre-loaded by selectinload in the calling router function.
    loaded_currency = db_expense.currency
    loaded_paid_by_user = db_expense.paid_by

    # Prepare data for ExpenseRead schema validation
    expense_read_payload = {
        "id": db_expense.id,
        "date": db_expense.date,
        "description": db_expense.description,
        "amount": db_expense.amount,
        "is_settled": db_expense.is_settled,
        "paid_by_user_id": db_expense.paid_by_user_id,
        "currency_id": db_expense.currency_id,
        "group_id": db_expense.group_id,
        "paid_by_user": schemas.UserRead.model_validate(loaded_paid_by_user) if loaded_paid_by_user else None,
        "currency": schemas.CurrencyRead.model_validate(loaded_currency) if loaded_currency else None,
        "participant_details": participant_details_list,
    }

    # Validate the constructed dictionary
    return schemas.ExpenseRead.model_validate(expense_read_payload)
