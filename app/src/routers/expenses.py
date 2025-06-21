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
    # Validate currency_id
    await get_object_or_404(session, Currency, expense_in.currency_id, "Currency not found.")

    # Validate group_id if provided
    if expense_in.group_id:
        await get_object_or_404(session, Group, expense_in.group_id, "Group not found.")

    participants_for_db = []

    try:
        if expense_in.participant_shares:
            # Case 1: Custom shares are provided
            seen_user_ids = set()
            sum_of_shares = 0.0

            for share_detail in expense_in.participant_shares:
                # Validate participant user_id
                await get_object_or_404(session, User, share_detail.user_id, f"Participant user ID {share_detail.user_id} not found.")

                # Check for duplicate user_ids in the input
                if share_detail.user_id in seen_user_ids:
                    await session.rollback()
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Duplicate user ID {share_detail.user_id} in participant shares.",
                    )
                seen_user_ids.add(share_detail.user_id)
                sum_of_shares += share_detail.share_amount
                participants_for_db.append(
                    {"user_id": share_detail.user_id, "share_amount": share_detail.share_amount}
                )

            # Validate sum of shares against total expense amount
            # Using a small tolerance for float comparison (e.g., 0.01 for currency)
            if abs(sum_of_shares - expense_in.amount) > 1e-2: # Adjusted tolerance for currency
                await session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Sum of participant shares ({sum_of_shares:.2f}) does not match total expense amount ({expense_in.amount:.2f}).",
                )
        else:
            # Case 2: No custom shares provided, payer is the only participant
            # Validate current_user.id (though typically guaranteed by Depends)
            await get_object_or_404(session, User, current_user.id, "Current user not found.")
            participants_for_db.append(
                {"user_id": current_user.id, "share_amount": expense_in.amount}
            )

        # Create the Expense object
        db_expense = Expense.model_validate(
            expense_in, update={"paid_by_user_id": current_user.id}
        )
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
        .options(selectinload(Expense.currency), selectinload(Expense.paid_by))
    )
    result = await session.exec(stmt)
    refreshed_db_expense = result.one_or_none()

    if not refreshed_db_expense:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to re-fetch expense after creation with full details",
        )

    # Manually construct and return ExpenseRead with participant_details
    # For simple creation, participants are not added here, so participant_details will be empty.
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
        if item.settled_currency_id != transaction.currency_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Settlement currency ID ({item.settled_currency_id}) does not match transaction currency ID ({transaction.currency_id}). The settled_amount should be in the transaction's currency.",
            )

        # Handle custom exchange rate
        if item.custom_exchange_rate is not None:
            if expense_participant.expense.currency_id == transaction.currency_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Custom exchange rate for EP ID {expense_participant.id} is not applicable when expense currency ({expense_participant.expense.currency_id}) and transaction currency ({transaction.currency_id}) are the same."
                )
            if item.custom_exchange_rate <= 0: # Should be caught by Pydantic gt=0 as well
                 raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Custom exchange rate must be positive."
                )
            expense_participant.custom_exchange_rate = item.custom_exchange_rate
            expense_participant.original_expense_currency_id = expense_participant.expense.currency_id
        elif expense_participant.expense.currency_id != transaction.currency_id:
            # If currencies are different but no custom rate is provided, this is a potential issue.
            # For now, we will require a custom rate if currencies differ.
            # Later, this could be a point to integrate automatic rate fetching.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Custom exchange rate is required for EP ID {expense_participant.id} when expense currency ({expense_participant.expense.currency_id}) and transaction currency ({transaction.currency_id}) differ."
            )
        else: # Currencies are the same, no custom rate provided (this is fine)
            expense_participant.custom_exchange_rate = None
            expense_participant.original_expense_currency_id = None


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

        # TODO:
        # Potentially mark the original Expense as fully settled if all its participations are settled.
        # This logic is more complex and would require fetching all participants for the expense.
        # For now, just update the ExpenseParticipant. This can also be a background task maybe?

        session.add(expense_participant)
        updated_participants_to_commit.append(
            expense_participant
        )  # Keep track for commit

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
        await session.commit()
        for ep in updated_participants_to_commit:
            await session.refresh(ep)  # Refresh to get any DB-side updates if necessary

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
    }
    return schemas.ExpenseRead.model_validate(expense_read_data)
