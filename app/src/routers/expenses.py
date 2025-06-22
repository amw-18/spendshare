import json
import shutil
import os
import uuid
from fastapi import UploadFile, File # Added for file upload
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
    Transaction,  # Ensure Transaction is imported
)
from src.models import schemas
from src.core.security import get_current_user
from src.utils import get_object_or_404
from src.services.expense_service import update_expense_settlement_status # Added import

router = APIRouter(
    prefix="/expenses",
    tags=["expenses"],
)


@router.post(
    "/service/", response_model=schemas.ExpenseRead, status_code=status.HTTP_201_CREATED
)
async def create_expense_with_participants_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    expense_in: schemas.ExpenseCreate,
    current_user: User = Depends(get_current_user),
) -> schemas.ExpenseRead:
    # Determine the actual payer
    payer_id = current_user.id
    if expense_in.paid_by_user_id is not None:
        # Validate the provided paid_by_user_id
        payer_user = await get_object_or_404(session, User, expense_in.paid_by_user_id, "Payer user not found.")
        payer_id = payer_user.id

    # Validate currency_id
    await get_object_or_404(session, Currency, expense_in.currency_id, "Currency not found.")

    # Validate group_id if provided and permissions
    if expense_in.group_id:
        group = await get_object_or_404(session, Group, expense_in.group_id, "Group not found.")
        # Check if current_user (creator) is a member of the group
        current_user_is_member = any(member.id == current_user.id for member in group.members)
        if not current_user_is_member:
            # This check might need adjustment based on product requirements (e.g., group admins)
            # For now, creator must be a member.
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Creator must be a member of the group to add expenses.",
            )

        # If a specific payer is designated, check if that payer is also a member of the group
        if expense_in.paid_by_user_id is not None and expense_in.paid_by_user_id != current_user.id:
            payer_is_member = any(member.id == expense_in.paid_by_user_id for member in group.members)
            if not payer_is_member:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Designated payer is not a member of the group.",
                )
    participants_for_db = []
    group_members_if_group_expense = None
    if expense_in.group_id and group: # group object fetched earlier
        group_members_if_group_expense = {member.id for member in group.members}

    try:
        # --- SPLIT METHOD LOGIC ---
        if expense_in.split_method == schemas.SplitMethodEnum.EQUAL:
            if not expense_in.selected_participant_user_ids:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="selected_participant_user_ids is required for 'equal' split.")
            if not expense_in.selected_participant_user_ids: # Should be caught by above, but defensive
                 raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No participants selected for equal split.")

            num_participants = len(expense_in.selected_participant_user_ids)
            if num_participants == 0: # Explicitly check for empty list if it bypasses the None check
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Participant list cannot be empty for equal split.")

            individual_share = round(expense_in.amount / num_participants, 2) # Using 2 decimal places for currency

            # Distribute remainder for precision
            remainder = round(expense_in.amount - (individual_share * num_participants), 2)

            seen_user_ids = set()
            for i, user_id in enumerate(expense_in.selected_participant_user_ids):
                await get_object_or_404(session, User, user_id, f"Participant user ID {user_id} not found.")
                if group_members_if_group_expense and user_id not in group_members_if_group_expense:
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Participant user ID {user_id} is not a member of the group.")
                if user_id in seen_user_ids:
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Duplicate user ID {user_id} in selected_participant_user_ids.")
                seen_user_ids.add(user_id)

                current_share = individual_share
                if i == 0 and remainder != 0: # Add remainder to the first participant
                    current_share = round(individual_share + remainder, 2)

                participants_for_db.append({"user_id": user_id, "share_amount": current_share})

        elif expense_in.split_method == schemas.SplitMethodEnum.PERCENTAGE:
            if not expense_in.participant_shares:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="participant_shares is required for 'percentage' split.")

            total_percentage = 0.0
            calculated_shares = []
            seen_user_ids = set()

            for share_detail in expense_in.participant_shares:
                await get_object_or_404(session, User, share_detail.user_id, f"Participant user ID {share_detail.user_id} not found.")
                if group_members_if_group_expense and share_detail.user_id not in group_members_if_group_expense:
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Participant user ID {share_detail.user_id} is not a member of the group.")
                if share_detail.user_id in seen_user_ids:
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Duplicate user ID {share_detail.user_id} in participant shares.")
                seen_user_ids.add(share_detail.user_id)

                if not (0 < share_detail.share_amount <= 100): # Percentage must be > 0 and <= 100
                     raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid percentage {share_detail.share_amount} for user {share_detail.user_id}. Must be between 0 (exclusive) and 100 (inclusive).")
                total_percentage += share_detail.share_amount
                calculated_shares.append({"user_id": share_detail.user_id, "percentage": share_detail.share_amount})

            if abs(total_percentage - 100.0) > 1e-2: # Using tolerance for 100% check
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Percentages must sum up to 100. Current sum: {total_percentage:.2f}%.")

            actual_sum_of_calculated_shares = 0.0
            for i, cs in enumerate(calculated_shares):
                share_value = round((cs["percentage"] / 100.0) * expense_in.amount, 2)
                participants_for_db.append({"user_id": cs["user_id"], "share_amount": share_value})
                actual_sum_of_calculated_shares += share_value

            # Adjust for rounding differences against total expense amount
            remainder = round(expense_in.amount - actual_sum_of_calculated_shares, 2)
            if abs(remainder) > 1e-9 and participants_for_db: # If there's a non-negligible remainder
                participants_for_db[0]["share_amount"] = round(participants_for_db[0]["share_amount"] + remainder, 2)


        elif expense_in.split_method == schemas.SplitMethodEnum.UNEQUAL:
            if not expense_in.participant_shares:
                 # For 'unequal', if no shares provided, it implies payer takes all. This is handled later.
                 # If shares are explicitly empty list [], that's an error for non-zero amount.
                if expense_in.participant_shares == []: # Explicit empty list
                    if abs(expense_in.amount) > 1e-9: # If amount is not zero
                        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Participant shares cannot be an empty list for 'unequal' split with non-zero amount.")
                    # If amount is zero, empty list is fine, no participants.
                # If None, then payer covers all. This is handled by the 'else' block after all split methods.

            # This block processes if participant_shares is provided and not empty for 'unequal'
            if expense_in.participant_shares: # Not None and not empty (empty list handled above)
                seen_user_ids = set()
                sum_of_shares = 0.0
                for share_detail in expense_in.participant_shares:
                    await get_object_or_404(session, User, share_detail.user_id, f"Participant user ID {share_detail.user_id} not found.")
                    if group_members_if_group_expense and share_detail.user_id not in group_members_if_group_expense:
                        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Participant user ID {share_detail.user_id} is not a member of the group.")
                    if share_detail.user_id in seen_user_ids:
                        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Duplicate user ID {share_detail.user_id} in participant shares.")
                    seen_user_ids.add(share_detail.user_id)
                    if share_detail.share_amount <= 1e-9: # Share must be positive
                        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Share amount for user {share_detail.user_id} must be positive for 'unequal' split.")

                    sum_of_shares += share_detail.share_amount
                    participants_for_db.append({"user_id": share_detail.user_id, "share_amount": share_detail.share_amount})

                if abs(sum_of_shares - expense_in.amount) > 1e-2:
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Sum of participant shares ({sum_of_shares:.2f}) does not match total expense amount ({expense_in.amount:.2f}) for 'unequal' split.")

        # Default case: If no specific split method processed shares, or if 'unequal' had no participant_shares (payer takes all)
        if not participants_for_db:
            if abs(expense_in.amount) > 1e-9: # If amount is not zero, payer is the sole participant
                await get_object_or_404(session, User, payer_id, "Payer (for default participation) not found.")
                participants_for_db.append({"user_id": payer_id, "share_amount": expense_in.amount})
            # If amount is zero and no participants, it's fine. participants_for_db remains empty.

        # Create the Expense object
        expense_data_for_model = expense_in.model_dump(exclude={"split_method", "selected_participant_user_ids", "participant_shares"})
        expense_data_for_model["paid_by_user_id"] = payer_id

        # Store split_method and selected_participant_user_ids_json
        expense_data_for_model["split_method"] = expense_in.split_method.value if expense_in.split_method else schemas.SplitMethodEnum.UNEQUAL.value
        if expense_in.split_method == schemas.SplitMethodEnum.EQUAL and expense_in.selected_participant_user_ids:
            expense_data_for_model["selected_participant_user_ids_json"] = json.dumps(expense_in.selected_participant_user_ids)
        else:
            expense_data_for_model["selected_participant_user_ids_json"] = None

        db_expense = Expense(**expense_data_for_model)
        session.add(db_expense)
        await session.flush()  # Assigns an ID to db_expense

        # Create ExpenseParticipant objects
        for participant_data in participants_for_db:
            expense_participant = ExpenseParticipant(
                expense_id=db_expense.id,  # Use the flushed expense ID
                user_id=participant_data["user_id"],
                share_amount=participant_data["share_amount"],
            )
            session.add(expense_participant)

        await session.commit()
        await session.refresh(db_expense) # Refresh to get any DB-side updates on db_expense itself

        # Re-fetch the expense with all necessary relationships for the response
        # This ensures all related data, especially from ExpenseParticipant, is loaded
        stmt = (
            select(Expense)
            .where(Expense.id == db_expense.id)
            .options(
                selectinload(Expense.currency),
                selectinload(Expense.paid_by),
                selectinload(Expense.group),
                # Participant details are loaded by _get_expense_read_details
                # We don't need to explicitly load Expense.all_participant_details here
                # as _get_expense_read_details will query them based on db_expense.id
            )
        )
        result = await session.exec(stmt)
        refreshed_db_expense_for_response = result.one_or_none()

        if not refreshed_db_expense_for_response:
            # This case should ideally not happen if commit was successful
            # but it's a safeguard.
            # No rollback here as data is already committed. Error indicates a fetch issue.
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to re-fetch expense after creation for response.",
            )

        return await _get_expense_read_details(
            session=session, db_expense=refreshed_db_expense_for_response
        )

    except HTTPException:
        # If it's an HTTPException we raised (e.g. 422, 404), rollback was likely called.
        # Re-raise it to be handled by FastAPI.
        await session.rollback() # Ensure rollback on any HTTPException during the try block
        raise
    except Exception as e:
        # For any other unexpected exceptions, rollback and raise a generic 500.
        await session.rollback()
        # Log the exception e for debugging if logging is set up
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.post(
    "/", response_model=schemas.ExpenseRead, status_code=status.HTTP_201_CREATED
)
async def create_expense_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    expense_in: schemas.ExpenseCreate,
    current_user: User = Depends(get_current_user),
) -> schemas.ExpenseRead:
    # Validate currency_id
    await get_object_or_404(session, Currency, expense_in.currency_id)

    # Determine the actual payer
    payer_id = current_user.id
    if expense_in.paid_by_user_id is not None:
        payer_user = await get_object_or_404(session, User, expense_in.paid_by_user_id, "Payer user not found.")
        payer_id = payer_user.id

    # Validate currency_id
    await get_object_or_404(session, Currency, expense_in.currency_id)

    # Validate group_id if provided and permissions
    if expense_in.group_id:
        group = await get_object_or_404(session, Group, expense_in.group_id, "Group not found.")
        # Check if current_user (creator) is a member of the group
        current_user_is_member = any(member.id == current_user.id for member in group.members)
        if not current_user_is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Creator must be a member of the group to add expenses.",
            )

        # If a specific payer is designated, check if that payer is also a member of the group
        if expense_in.paid_by_user_id is not None and expense_in.paid_by_user_id != current_user.id:
            payer_is_member = any(member.id == expense_in.paid_by_user_id for member in group.members)
            if not payer_is_member:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Designated payer is not a member of the group.",
                )

    # Create the Expense object, ensuring paid_by_user_id is set to the determined payer_id
    # For this simple endpoint, participant_shares are not processed.
    # The payer (payer_id) is implicitly the sole participant.
    expense_data_for_model = expense_in.model_dump(exclude={"split_method", "selected_participant_user_ids", "participant_shares"})
    expense_data_for_model["paid_by_user_id"] = payer_id

    # For this simple endpoint, split_method is implicitly "unequal" and no specific selected_participant_user_ids.
    expense_data_for_model["split_method"] = schemas.SplitMethodEnum.UNEQUAL.value
    expense_data_for_model["selected_participant_user_ids_json"] = None

    db_expense = Expense(**expense_data_for_model)
    session.add(db_expense)

    # Add the payer as the sole participant
    # This was missing previously if this endpoint is to truly represent a single-payer expense
    # where the payer covers the whole amount.
    # If participant_shares were allowed here, this would be more complex.
    # Assuming this endpoint creates an expense where the payer_id is the only participant.
    sole_participant = ExpenseParticipant(
        expense_id=db_expense.id, # This will be set after flush
        user_id=payer_id,
        share_amount=db_expense.amount
    )
    # Need to flush to get db_expense.id before creating ExpenseParticipant
    # Or, handle it similarly to create_expense_with_participants_endpoint

    await session.flush() # Get expense ID
    sole_participant.expense_id = db_expense.id # Set it now
    session.add(sole_participant)

    await session.commit()
    await session.refresh(db_expense)

    # Re-fetch with relationships for ExpenseRead using a select statement
    stmt = (
        select(Expense)
        .where(Expense.id == db_expense.id)
        .options(selectinload(Expense.currency), selectinload(Expense.paid_by))
        # Participants will be loaded by _get_expense_read_details
    )
    result = await session.exec(stmt)
    refreshed_db_expense = result.one_or_none()

    if not refreshed_db_expense:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to re-fetch expense after creation with full details",
        )

    return await _get_expense_read_details(
        session=session, db_expense=refreshed_db_expense
    )


@router.get("/", response_model=List[schemas.ExpenseRead])
async def read_expenses_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    group_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
) -> List[schemas.ExpenseRead]:
    # Base query with eager loading for fields directly on Expense model
    # _get_expense_read_details will handle loading participant details separately
    base_options = [
        selectinload(Expense.currency),
        selectinload(Expense.paid_by),
        selectinload(Expense.group),  # Ensure Group is loaded if group_id is present
    ]
    statement = select(Expense).options(*base_options)

    if user_id:
        # Users can only fetch their own expenses when user_id is provided
        if user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to fetch expenses for another user. You can only fetch your own.",
            )
        # Filter for expenses where the specified user_id (which is current_user.id) is payer or participant.
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
        # All users see their own expenses if no specific user_id or group_id is given
        statement = (
            statement.outerjoin(
                ExpenseParticipant,
                Expense.id == ExpenseParticipant.expense_id,
            )
            .where(
                or_(
                    Expense.paid_by_user_id == current_user.id,  # User is payer
                    ExpenseParticipant.user_id
                    == current_user.id,  # User is participant
                )
            )
            .offset(skip)
            .limit(limit)
        )

    result = await session.exec(statement)
    # Use .unique().all() to avoid duplicate Expense rows if outerjoin produces them
    expenses_db = list(result.unique().all())

    # Convert each Expense model to ExpenseRead schema using the helper
    expenses_read_list: List[schemas.ExpenseRead] = []
    for db_expense in expenses_db:
        expenses_read_list.append(
            await _get_expense_read_details(session=session, db_expense=db_expense)
        )
    return expenses_read_list


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
            selectinload(Expense.currency),
            selectinload(Expense.paid_by),
            selectinload(Expense.group),
            selectinload(
                Expense.participants
            ),  # Eagerly load participants for auth check
            # Participant details for response are handled by _get_expense_read_details
        )
    )
    result = await session.exec(statement)
    db_expense = result.first()

    if not db_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found"
        )

    # Authorization check: current_user must be the payer or one of the participants.
    is_payer = db_expense.paid_by_user_id == current_user.id
    is_participant = any(p.id == current_user.id for p in db_expense.participants)

    if not (is_payer or is_participant):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this expense",
        )

    return await _get_expense_read_details(session=session, db_expense=db_expense)


@router.put("/{expense_id}", response_model=schemas.ExpenseRead)
async def update_expense_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    expense_id: int,
    expense_in: schemas.ExpenseUpdate,
    current_user: User = Depends(get_current_user),
) -> schemas.ExpenseRead:
    # I. Authorization and Initial Setup
    db_expense = await session.get(
        Expense,
        expense_id,
        options=[
            selectinload(Expense.paid_by),
            selectinload(Expense.group).selectinload(Group.members), # For group membership check
            selectinload(Expense.all_participant_details).selectinload(ExpenseParticipant.user), # For participant check
        ],
    )

    if not db_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found",
        )

    # Authorization Logic
    can_edit = False
    if db_expense.paid_by_user_id == current_user.id:
        can_edit = True
    elif db_expense.group and any(member.id == current_user.id for member in db_expense.group.members):
        can_edit = True
    elif not db_expense.group and any(ep.user_id == current_user.id for ep in db_expense.all_participant_details):
        can_edit = True

    if not can_edit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this expense.",
        )

    try:
        # II. Processing Input and Basic Field Updates
        update_data = expense_in.model_dump(exclude_unset=True)
        new_participants_input_list = update_data.pop("participants", None)

        amount_changed = False
        current_expense_amount = round(db_expense.amount, 2)

        if "amount" in update_data:
            new_proposed_amount = round(update_data["amount"], 2)
            # Use a small tolerance for float comparison
            if abs(new_proposed_amount - round(db_expense.amount, 2)) > 1e-9: # Compare with original rounded amount
                amount_changed = True
            current_expense_amount = new_proposed_amount # This will be the amount to validate shares against
            db_expense.amount = new_proposed_amount # Actual field update
            # Remove amount from update_data as it's handled
            update_data.pop("amount")


        # Update other mutable fields
        if "currency_id" in update_data:
            new_currency_id = update_data.pop("currency_id")
            if new_currency_id is not None: # Schema allows Optional for update
                 await get_object_or_404(session, Currency, new_currency_id, "Currency not found.")
                 db_expense.currency_id = new_currency_id

        if "group_id" in update_data:
            new_group_id = update_data.pop("group_id")
            # group_id can be None to remove expense from a group
            if new_group_id is not None:
                await get_object_or_404(session, Group, new_group_id, "Group not found.")
            db_expense.group_id = new_group_id

        # Update remaining fields like description
        for key, value in update_data.items():
            setattr(db_expense, key, value)

        session.add(db_expense) # Add changes so far, including amount, currency, group, description

        # III. Handling Participant Updates (if new_participants_input_list is provided)
        if new_participants_input_list is not None:
            # Delete Existing Participants
            for link in db_expense.all_participant_details:
                await session.delete(link)
            db_expense.all_participant_details = [] # Clear local collection
            await session.flush() # Process deletions in DB

            new_shares_to_create = []
            calculated_sum_of_new_shares = 0.0
            user_ids_in_new_list = set()

            if not new_participants_input_list: # Empty list [] was provided
                # If expense amount is not zero, this is an error.
                # Using 1e-2 as tolerance for "non-zero" amount check
                if abs(current_expense_amount - 0.0) > 1e-2:
                    await session.rollback()
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Empty participant list provided for a non-zero expense amount."
                    )
                # If amount is zero and participants list is empty, it's fine. No participants to add.
            else: # List has items
                for p_dict in new_participants_input_list:
                    user_id = p_dict.get("user_id")
                    share_amount_input = p_dict.get("share_amount")

                    if user_id is None or share_amount_input is None:
                        await session.rollback()
                        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Each participant must have user_id and share_amount.")

                    share_amount = round(float(share_amount_input), 2) # Ensure float and round

                    if share_amount <= 1e-9: # Effectively checks for positive amount
                        await session.rollback()
                        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Share amount must be positive.")

                    if user_id in user_ids_in_new_list:
                        await session.rollback()
                        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Duplicate user_id {user_id} in input.")

                    await get_object_or_404(session, User, user_id, f"Participant user ID {user_id} not found.")
                    user_ids_in_new_list.add(user_id)
                    new_shares_to_create.append({"user_id": user_id, "share_amount": share_amount})
                    calculated_sum_of_new_shares += share_amount

                calculated_sum_of_new_shares = round(calculated_sum_of_new_shares, 2)
                # Using 1e-2 tolerance for currency sum validation
                if abs(calculated_sum_of_new_shares - current_expense_amount) > 1e-2:
                    await session.rollback()
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Sum of new shares ({calculated_sum_of_new_shares:.2f}) does not equal expense amount ({current_expense_amount:.2f})."
                    )

            # Create New ExpenseParticipant Records
            for s_info in new_shares_to_create:
                ep = ExpenseParticipant(user_id=s_info['user_id'], expense_id=db_expense.id, share_amount=s_info['share_amount'])
                session.add(ep)
                db_expense.all_participant_details.append(ep) # Keep local model in sync
            amount_changed = True # Shares were explicitly set, treat as amount/share change for recalculation logic avoidance

        # IV. Handling Amount Change WITHOUT Explicit Participant Update
        elif new_participants_input_list is None and amount_changed:
            current_participants = db_expense.all_participant_details # Already loaded
            if current_participants: # Only if there are existing participants
                num_participants = len(current_participants)
                new_equal_share = round(current_expense_amount / num_participants, 2)

                recalculated_sum = 0.0
                for idx, link in enumerate(current_participants):
                    link.share_amount = new_equal_share
                    session.add(link)
                    recalculated_sum += new_equal_share

                recalculated_sum = round(recalculated_sum, 2)
                # Adjust for rounding differences on the first participant
                if abs(recalculated_sum - current_expense_amount) > 1e-9: # Use small tolerance for this adjustment
                    remainder = round(current_expense_amount - recalculated_sum, 2)
                    current_participants[0].share_amount = round(current_participants[0].share_amount + remainder, 2)
                    session.add(current_participants[0])
            # If no current participants and amount changes, it implies the payer (current_user) now bears the full new amount.
            # This case needs to be handled: if no participants, and amount changed, who pays?
            # For now, if no participants and amount changed, and no new list, it's an implicit single-payer expense (the original payer).
            # The current logic correctly updates db_expense.amount. If there are no participant links, no shares need updating.
            # If the intention is to automatically add the payer as a participant if none exist, that needs explicit logic.
            # Given the problem, we assume existing participants (if any) split the new total, or new participants are provided.
            # If no participants exist AND no new ones are provided, it's ok, implies payer covers all.

        # V. Commit and Respond
        await session.commit()
        await session.refresh(db_expense) # Refresh db_expense itself

        # For the response, reload the expense with relations needed by _get_expense_read_details
        stmt = (
            select(Expense)
            .where(Expense.id == expense_id)
            .options(
                selectinload(Expense.currency),
                selectinload(Expense.paid_by),
                selectinload(Expense.group)
                # _get_expense_read_details will load its own participant details
            )
        )
        result = await session.exec(stmt)
        refreshed_expense_for_response = result.one_or_none()

        if not refreshed_expense_for_response:
            # This indicates a serious issue if commit succeeded but fetch failed
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to re-fetch updated expense for response."
            )

        return await _get_expense_read_details(session=session, db_expense=refreshed_expense_for_response)

    except HTTPException:
        await session.rollback() # Ensure rollback if an HTTPException was raised by us or get_object_or_404
        raise
    except Exception as e:
        await session.rollback()
        # Consider logging the error e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.post(
    "/settle", response_model=schemas.SettlementResponse, status_code=status.HTTP_200_OK
)  # this should probably happen in the backend only (background task maybe). TransactionCreate should have a list of expense_id's to use for this transaction
async def settle_expenses_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    settle_request: schemas.SettleExpensesRequest,
):
    """
    Settle one or more expense participations using a transaction.
    All or none.
    """
    # Retrieve the transaction
    transaction = await session.get(
        Transaction,  # Corrected to Transaction
        settle_request.transaction_id,
        options=[
            selectinload(Transaction.currency)
        ],  # Ensure currency is loaded if needed later, though not strictly for this logic
    )
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )

    # Verify current_user created the transaction
    if transaction.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to use this transaction for settlement",
        )

    # Calculate total settlement amount from the request
    total_settled_amount_from_request = sum(
        item.settled_amount for item in settle_request.settlements
    )

    # Check if total settlement amount exceeds transaction amount
    if total_settled_amount_from_request > transaction.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Total settlement amount exceeds transaction amount.",
        )

    results: List[schemas.SettlementResultItem] = []
    updated_participants_to_commit = []
    affected_expense_ids = set() # To store IDs of expenses whose participants were updated

    # Check for duplicate expense_participant_ids in the request upfront
    seen_ep_ids_in_request = set()
    for item_check in settle_request.settlements:
        if item_check.expense_participant_id in seen_ep_ids_in_request:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate expense_participant_id {item_check.expense_participant_id} in settlement request.",
            )
        seen_ep_ids_in_request.add(item_check.expense_participant_id)

    for item in settle_request.settlements:
        # Explicit validation for settled_amount (Pydantic's gt=0 should also catch this)
        if item.settled_amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Settled amount for expense participant ID {item.expense_participant_id} must be positive.",
            )

        # Retrieve ExpenseParticipant by its own ID and eagerly load its parent Expense
        stmt_ep = (
            select(ExpenseParticipant)
            .options(
                selectinload(ExpenseParticipant.expense)
            )  # Eagerly load the parent expense
            .where(ExpenseParticipant.id == item.expense_participant_id)
        )
        result_ep = await session.exec(stmt_ep)
        expense_participant = result_ep.first()

        if not expense_participant:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="ExpenseParticipant record not found.",
            )

        if not expense_participant.expense:  # Should be loaded due to selectinload
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not load parent expense for participation record.",
            )

        # Authorization check for settling this specific ExpenseParticipant:
        # The current_user (who created the transaction) can settle an ExpenseParticipant if:
        # 1. They are the payer of the original expense (expense_participant.expense.paid_by_user_id == current_user.id), OR
        # 2. The ExpenseParticipant record belongs to them (expense_participant.user_id == current_user.id).
        is_original_payer = (
            expense_participant.expense.paid_by_user_id == current_user.id
        )
        is_own_participation = expense_participant.user_id == current_user.id

        if not (is_original_payer or is_own_participation):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Not authorized to settle this expense participation.",
            )

        # Verify settled_currency_id matches transaction.currency_id
        # TODO: This needs to be relaxed later on
        if item.settled_currency_id != transaction.currency_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Settlement currency ID ({item.settled_currency_id}) does not match transaction currency ID ({transaction.currency_id}).",
            )

        # Check if already settled by another transaction
        if (
            expense_participant.settled_transaction_id
            and expense_participant.settled_transaction_id != transaction.id
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Expense participation is already settled by transaction {expense_participant.settled_transaction_id}.",
            )

        # Update ExpenseParticipant
        expense_participant.settled_transaction_id = transaction.id
        expense_participant.settled_amount_in_transaction_currency = item.settled_amount

        session.add(expense_participant)
        updated_participants_to_commit.append(
            expense_participant
        )  # Keep track for commit
        affected_expense_ids.add(expense_participant.expense_id) # Track affected expense

        results.append(
            schemas.SettlementResultItem(
                expense_participant_id=item.expense_participant_id,
                settled_transaction_id=transaction.id,
                settled_amount_in_transaction_currency=item.settled_amount,
                settled_currency_id=transaction.currency_id,  # Use transaction's currency ID
                message="Settled successfully.",
            )
        )

    if updated_participants_to_commit:  # Only commit if there are successful updates
        await session.commit() # Commit changes to ExpenseParticipant first
        for ep in updated_participants_to_commit:
            await session.refresh(ep)  # Refresh to get any DB-side updates if necessary

        # After successful settlement of participants, update parent expense statuses
        for expense_id in affected_expense_ids:
            await update_expense_settlement_status(expense_id, session)

        await session.commit() # Commit changes to Expense statuses

    return schemas.SettlementResponse(
        status="Completed",
        message="Settlement process finished. Check individual item statuses.",
        updated_expense_participations=results,
    )


@router.delete("/{expense_id}", response_model=int)
async def delete_expense_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    expense_id: int,
    current_user: User = Depends(get_current_user),
) -> int:
    db_expense = await get_object_or_404(session, Expense, expense_id)

    # Only the payer of the expense can delete it.
    if db_expense.paid_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this expense. Only the payer can delete.",
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
    Helper function to construct ExpenseRead schema with populated participant_details.
    It fetches ExpenseParticipant records and their related data.
    """
    # Query ExpenseParticipant records for this expense, with their related User (and User.groups)
    # and their related Transaction (and Transaction.currency)
    stmt = (
        select(ExpenseParticipant)
        .where(ExpenseParticipant.expense_id == db_expense.id)
        .options(
            selectinload(ExpenseParticipant.user).selectinload(
                User.groups
            ),  # User and their groups
            selectinload(ExpenseParticipant.transaction).selectinload(
                Transaction.currency
            ),  # Transaction and its currency
        )
    )
    result = await session.exec(stmt)
    participant_link_models = (
        result.all()
    )  # These are ExpenseParticipant model instances

    participant_details_list = []
    for (
        participant_model
    ) in participant_link_models:  # participant_model is an ExpenseParticipant
        user_for_schema = (
            schemas.UserRead.model_validate(participant_model.user)
            if participant_model.user
            else None
        )

        settled_currency_for_schema = None
        settled_currency_id_for_schema = None
        if participant_model.transaction and participant_model.transaction.currency:
            settled_currency_for_schema = schemas.CurrencyRead.model_validate(
                participant_model.transaction.currency
            )
            settled_currency_id_for_schema = participant_model.transaction.currency_id
        elif (
            participant_model.transaction
        ):  # Transaction exists but currency might not be loaded or set
            # This case might indicate an issue if transaction.currency should always be there
            pass

        participant_details_list.append(
            schemas.ExpenseParticipantReadWithUser(
                id=participant_model.id,
                user_id=participant_model.user_id,
                expense_id=participant_model.expense_id,
                share_amount=participant_model.share_amount,
                user=user_for_schema,
                settled_transaction_id=participant_model.settled_transaction_id,
                settled_amount_in_transaction_currency=participant_model.settled_amount_in_transaction_currency,
                settled_currency_id=settled_currency_id_for_schema,
                settled_currency=settled_currency_for_schema,
            )
        )

    # Ensure db_expense.currency and db_expense.paid_by are loaded by the CALLER of _get_expense_read_details
    # These should have been loaded by the options in the calling endpoint (e.g., read_expense_endpoint)
    paid_by_user_for_schema = (
        schemas.UserRead.model_validate(db_expense.paid_by)
        if db_expense.paid_by
        else None
    )
    currency_for_schema = (
        schemas.CurrencyRead.model_validate(db_expense.currency)
        if db_expense.currency
        else None
    )
    # group_for_schema = schemas.GroupRead.from_orm(db_expense.group) if db_expense.group else None # If group details are needed in ExpenseRead

    expense_read_data = {
        "id": db_expense.id,
        "description": db_expense.description,
        "amount": db_expense.amount,
        "date": db_expense.date,
        "is_settled": db_expense.is_settled,
        "paid_by_user_id": db_expense.paid_by_user_id,
        "paid_by_user": paid_by_user_for_schema,
        "group_id": db_expense.group_id,
        # "group": group_for_schema,
        "currency_id": db_expense.currency_id,
        "currency": currency_for_schema,
        "participant_details": participant_details_list,
        "receipt_image_url": db_expense.receipt_image_url, # Added
        "split_method": schemas.SplitMethodEnum(db_expense.split_method) if db_expense.split_method else None, # Added
        "selected_participant_user_ids": json.loads(db_expense.selected_participant_user_ids_json) if db_expense.selected_participant_user_ids_json else None, # Added
    }
    return schemas.ExpenseRead.model_validate(expense_read_data)


# Additional imports for receipt upload
import shutil
import os
import uuid
from fastapi import UploadFile, File

# Define upload directory relative to app root
UPLOAD_DIR_RECEIPTS = "uploads/receipts"
# Ensure UPLOAD_DIR_RECEIPTS is created if it doesn't exist when the app starts.
# This can be done in main.py or here using a startup event if complex,
# or simply by checking and creating in the endpoint for simplicity here.

@router.post("/{expense_id}/upload-receipt", response_model=schemas.ExpenseRead)
async def upload_expense_receipt_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    expense_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    db_expense = await session.get(
        Expense,
        expense_id,
        options=[
            selectinload(Expense.paid_by),
            selectinload(Expense.group).selectinload(Group.members),
        ],
    )

    if not db_expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    # Authorization: Current user must be the payer or a member of the group if it's a group expense.
    # More granular: could be creator, or involved participant. For now, payer or group member.
    is_payer = db_expense.paid_by_user_id == current_user.id
    is_group_member_of_expense_group = False
    if db_expense.group:
        is_group_member_of_expense_group = any(member.id == current_user.id for member in db_expense.group.members)

    if not (is_payer or is_group_member_of_expense_group):
        # If not a group expense, only payer can upload.
        if not db_expense.group and not is_payer:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to upload receipt for this expense.")
        # If it is a group expense, and user is neither payer nor member.
        if db_expense.group and not (is_payer or is_group_member_of_expense_group):
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to upload receipt for this group expense.")


    # Basic file validation (content type and size)
    if file.content_type not in ["image/jpeg", "image/png", "image/gif"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type. Only JPG, PNG, GIF allowed.")

    # Size limit (e.g., 5MB)
    # file.file is a SpooledTemporaryFile. We can check its size.
    # To get actual size, we need to read it or seek to end.
    # file.file.seek(0, os.SEEK_END)
    # file_size = file.file.tell()
    # file.file.seek(0) # Reset cursor
    # if file_size > 5 * 1024 * 1024: # 5MB
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds 5MB limit.")


    # Create unique filename and path
    # Ensure the root UPLOAD_DIR_RECEIPTS exists (important for first upload)
    # The path stored in DB should be relative to where static files are served from.
    # e.g. if static files served from "static/", and uploads go to "static/receipts/", then URL is "receipts/filename.ext"

    # For local dev, let's assume UPLOAD_DIR_RECEIPTS is directly under 'app' or project root,
    # and FastAPI will serve it from a path like /static/receipts.
    # So, the path stored in DB will be "receipts/unique_filename.ext"

    # Correctly create the uploads directory if it doesn't exist relative to the script's execution path (app root)
    # This assumes the script runs from the project root where 'app' is a subdir.
    # If running from 'app' dir, then UPLOAD_DIR_RECEIPTS should be relative to 'app'.
    # Given `cd app` is used, paths are relative to `/app` directory.

    # Base directory for uploads within the 'app' directory
    # This means uploads will be in 'app/uploads/receipts'
    # Static serving should be configured for 'app/uploads' or 'app/uploads/receipts' later.

    # The UPLOAD_DIR_RECEIPTS = "uploads/receipts" is relative to where the app is running from.
    # If main.py is in app/src, and we are in app/ CWD, then this path is app/uploads/receipts.

    # Let's ensure the full absolute path for os.makedirs
    # This should be relative to the project root, not the script file.
    # For the sandbox, assuming current working directory is /app

    # Path for storing files: app/uploads/receipts
    # Path for URL: /uploads/receipts/filename.ext (if /uploads is served as static)

    # Simplified: Assume UPLOAD_DIR_RECEIPTS is relative to the app's root (where main.py is, usually app/src or app/)
    # For safety, let's make it relative to the current file's directory structure if possible, or use absolute paths for clarity.
    # However, for deployment, relative paths from a known root are better.
    # Let's assume 'uploads' is at the same level as 'src' inside 'app'.
    # So, if expenses.py is in app/src/routers, then path is ../../uploads/receipts

    # Given the project structure, 'app' is the root for backend.
    # So, 'app/uploads/receipts' seems correct.

    # Create the directory path
    # The path should be formed from a known base, like the app's root directory.
    # For the tool environment, `os.getcwd()` when `cd app` has been run is `/app`.
    # So, `os.path.join(os.getcwd(), UPLOAD_DIR_RECEIPTS)` would be `/app/uploads/receipts`.

    upload_dir_full_path = os.path.join(os.getcwd(), UPLOAD_DIR_RECEIPTS) # os.getcwd() is /app here
    os.makedirs(upload_dir_full_path, exist_ok=True)

    _, extension = os.path.splitext(file.filename)
    unique_filename = f"{uuid.uuid4()}{extension}"
    file_location = os.path.join(upload_dir_full_path, unique_filename)

    # Save the file
    try:
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
    except Exception as e:
        # Log error e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not save file: {str(e)}")
    finally:
        file.file.close() # Ensure file is closed

    # Store relative path for URL (e.g., "/uploads/receipts/filename.ext" or "receipts/filename.ext")
    # This depends on how static files will be mounted.
    # If FastAPI serves a directory named "uploads_mounted_statically" which points to "app/uploads",
    # then the URL would be "/uploads_mounted_statically/receipts/unique_filename.ext"
    # For simplicity, let's store the path relative from "uploads" dir.
    # So, "receipts/unique_filename.ext". The static mount point will handle the "uploads" part.
    relative_file_path = os.path.join(UPLOAD_DIR_RECEIPTS.split('/')[-1], unique_filename) # e.g. "receipts/filename.ext"


    db_expense.receipt_image_url = relative_file_path
    session.add(db_expense)
    await session.commit()
    await session.refresh(db_expense)

    return await _get_expense_read_details(session=session, db_expense=db_expense)
