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
    Transaction, # Ensure Transaction is imported
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
            selectinload(Expense.paid_by),
            selectinload(Expense.group),
            selectinload(Expense.all_participant_details).selectinload(ExpenseParticipant.user).selectinload(User.groups), # For UserRead in participant
            selectinload(Expense.all_participant_details).selectinload(ExpenseParticipant.transaction).selectinload(Transaction.currency) # For settlement details
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
    # Base query with eager loading for fields directly on Expense model
    # _get_expense_read_details will handle loading participant details separately
    base_options = [
        selectinload(Expense.currency),
        selectinload(Expense.paid_by),
        selectinload(Expense.group), # Ensure Group is loaded if group_id is present
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
        # All users (admins or not) see their own expenses if no specific user_id or group_id is given
        statement = (
            statement.outerjoin(
                ExpenseParticipant,
                Expense.id == ExpenseParticipant.expense_id,
            )
            .where(
                or_(
                    Expense.paid_by_user_id == current_user.id,  # User is payer
                    ExpenseParticipant.user_id == current_user.id,  # User is participant
                )
            )
            .offset(skip)
            .limit(limit)
        )
        # Admin-specific view for all expenses removed.

    result = await session.exec(statement)
    # Use .unique().all() to avoid duplicate Expense rows if outerjoin produces them
    expenses_db = list(result.unique().all())

    # Convert each Expense model to ExpenseRead schema using the helper
    expenses_read_list: List[schemas.ExpenseRead] = []
    for db_expense in expenses_db:
        expenses_read_list.append(await _get_expense_read_details(session=session, db_expense=db_expense))
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
            selectinload(Expense.participants)  # Eagerly load participants for auth check
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
            selectinload(Expense.paid_by),
            selectinload(Expense.group),
            selectinload(Expense.all_participant_details).options(
                selectinload(ExpenseParticipant.user),
                selectinload(ExpenseParticipant.transaction).selectinload(Transaction.currency)
            )
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
            selectinload(Expense.paid_by),
            selectinload(Expense.group),
            selectinload(Expense.all_participant_details).options(selectinload(ExpenseParticipant.user).selectinload(User.groups)),
            selectinload(Expense.all_participant_details).options(selectinload(ExpenseParticipant.transaction).selectinload(Transaction.currency))
        )
    )
    result = await session.exec(stmt)
    refreshed_db_expense = result.one_or_none()

    if not refreshed_db_expense:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to re-fetch expense after update with full details")

    # Manually construct and return ExpenseRead with participant_details
    return await _get_expense_read_details(session=session, db_expense=refreshed_db_expense)


@router.post("/settle", response_model=schemas.SettlementResponse, status_code=status.HTTP_200_OK)
async def settle_expenses_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    settle_request: schemas.SettleExpensesRequest,
):
    """
    Settle one or more expense participations using a transaction.
    """
    # Retrieve the transaction
    transaction = await session.get(
        Transaction, # Corrected to Transaction
        settle_request.transaction_id,
        options=[selectinload(Transaction.currency)] # Ensure currency is loaded if needed later, though not strictly for this logic
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
                detail=f"Duplicate expense_participant_id {item_check.expense_participant_id} in settlement request."
            )
        seen_ep_ids_in_request.add(item_check.expense_participant_id)

    for item in settle_request.settlements:
        # Explicit validation for settled_amount (Pydantic's gt=0 should also catch this)
        if item.settled_amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                detail=f"Settled amount for expense participant ID {item.expense_participant_id} must be positive."
            )

        # Retrieve ExpenseParticipant by its own ID and eagerly load its parent Expense
        stmt_ep = (
            select(ExpenseParticipant)
            .options(selectinload(ExpenseParticipant.expense))  # Eagerly load the parent expense
            .where(ExpenseParticipant.id == item.expense_participant_id)
        )
        result_ep = await session.exec(stmt_ep)
        expense_participant = result_ep.first()

        if not expense_participant:
            results.append(
                schemas.SettlementResultItem(
                    expense_participant_id=item.expense_participant_id,
                    settled_transaction_id=transaction.id,
                    settled_amount_in_transaction_currency=item.settled_amount,
                    settled_currency_id=item.settled_currency_id,
                    status="Failed",
                    message="ExpenseParticipant record not found.",
                )
            )
            continue

        if not expense_participant.expense: # Should be loaded due to selectinload
            results.append(
                schemas.SettlementResultItem(
                    expense_participant_id=item.expense_participant_id,
                    settled_transaction_id=transaction.id,
                    settled_amount_in_transaction_currency=item.settled_amount,
                    settled_currency_id=item.settled_currency_id,
                    status="Failed",
                    message="Could not load parent expense for participation record.",
                )
            )
            continue

        # Authorization check for settling this specific ExpenseParticipant:
        # The current_user (who created the transaction) can settle an ExpenseParticipant if:
        # 1. They are the payer of the original expense (expense_participant.expense.paid_by_user_id == current_user.id), OR
        # 2. The ExpenseParticipant record belongs to them (expense_participant.user_id == current_user.id).
        is_original_payer = expense_participant.expense.paid_by_user_id == current_user.id
        is_own_participation = expense_participant.user_id == current_user.id

        if not (is_original_payer or is_own_participation):
            results.append(
                schemas.SettlementResultItem(
                    expense_participant_id=item.expense_participant_id,
                    settled_transaction_id=transaction.id,
                    settled_amount_in_transaction_currency=item.settled_amount,
                    settled_currency_id=item.settled_currency_id,
                    status="Failed",
                    message="Not authorized to settle this expense participation.",
                )
            )
            continue

        # Verify settled_currency_id matches transaction.currency_id
        if item.settled_currency_id != transaction.currency_id:
            results.append(
                schemas.SettlementResultItem(
                    expense_participant_id=item.expense_participant_id,
                    settled_transaction_id=transaction.id,
                    settled_amount_in_transaction_currency=item.settled_amount,
                    settled_currency_id=item.settled_currency_id,
                    status="Failed",
                    message=f"Settlement currency ID ({item.settled_currency_id}) does not match transaction currency ID ({transaction.currency_id}).",
                )
            )
            continue

        # Check if already settled by another transaction
        if expense_participant.settled_transaction_id and expense_participant.settled_transaction_id != transaction.id:
            results.append(
                schemas.SettlementResultItem(
                    expense_participant_id=item.expense_participant_id,
                    settled_transaction_id=transaction.id, # or original settled_transaction_id?
                    settled_amount_in_transaction_currency=item.settled_amount,
                    settled_currency_id=item.settled_currency_id,
                    status="Failed",
                    message=f"Expense participation is already settled by transaction {expense_participant.settled_transaction_id}.",
                )
            )
            continue

        # Update ExpenseParticipant
        expense_participant.settled_transaction_id = transaction.id
        expense_participant.settled_amount_in_transaction_currency = item.settled_amount
        # Potentially mark the original Expense as fully settled if all its participations are settled.
        # This logic is more complex and would require fetching all participants for the expense.
        # For now, just update the ExpenseParticipant.

        session.add(expense_participant)
        updated_participants_to_commit.append(expense_participant) # Keep track for commit

        results.append(
            schemas.SettlementResultItem(
                expense_participant_id=item.expense_participant_id,
                settled_transaction_id=transaction.id,
                settled_amount_in_transaction_currency=item.settled_amount,
                settled_currency_id=transaction.currency_id, # Use transaction's currency ID
                status="Success",
                message="Settled successfully.",
            )
        )

    if updated_participants_to_commit: # Only commit if there are successful updates
        await session.commit()
        for ep in updated_participants_to_commit:
            await session.refresh(ep) # Refresh to get any DB-side updates if necessary

    return schemas.SettlementResponse(
        status="Completed", # Or "PartiallyCompleted" if some failed
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
            selectinload(ExpenseParticipant.user).selectinload(User.groups), # User and their groups
            selectinload(ExpenseParticipant.transaction).selectinload(Transaction.currency), # Transaction and its currency
        )
    )
    result = await session.exec(stmt)
    participant_link_models = result.all() # These are ExpenseParticipant model instances

    participant_details_list = []
    for participant_model in participant_link_models: # participant_model is an ExpenseParticipant
        user_for_schema = schemas.UserRead.model_validate(participant_model.user) if participant_model.user else None
        
        settled_currency_for_schema = None
        settled_currency_id_for_schema = None
        if participant_model.transaction and participant_model.transaction.currency:
            settled_currency_for_schema = schemas.CurrencyRead.model_validate(participant_model.transaction.currency)
            settled_currency_id_for_schema = participant_model.transaction.currency_id
        elif participant_model.transaction: # Transaction exists but currency might not be loaded or set
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
    paid_by_user_for_schema = schemas.UserRead.model_validate(db_expense.paid_by) if db_expense.paid_by else None
    currency_for_schema = schemas.CurrencyRead.model_validate(db_expense.currency) if db_expense.currency else None
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
