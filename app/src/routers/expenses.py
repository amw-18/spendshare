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
    ConversionRate,
)
from datetime import datetime
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
    await session.refresh(db_expense)  # Refresh again after adding participants

    # Re-fetch with relationships for ExpenseRead using a select statement
    stmt = (
        select(Expense)
        .where(Expense.id == db_expense.id)
        .options(
            selectinload(Expense.currency),
            selectinload(Expense.paid_by),
            selectinload(Expense.group),
            selectinload(Expense.all_participant_details)
            .selectinload(ExpenseParticipant.user)
            .selectinload(User.groups),  # For UserRead in participant
            selectinload(Expense.all_participant_details)
            .selectinload(ExpenseParticipant.transaction)
            .selectinload(Transaction.currency),  # For settlement details
        )
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


@router.get(
    "/settlement-details/expense/{expense_id}/currency/{target_currency_id}",
    response_model=schemas.ExpenseSettlementDetails,
    summary="Get Settlement Details for a Specific Expense Share",
)
async def get_expense_settlement_details(
    *,
    session: AsyncSession = Depends(get_session),
    expense_id: int,
    target_currency_id: int,
    current_user: User = Depends(get_current_user),
) -> schemas.ExpenseSettlementDetails:
    """
    Provides details for settling the current user's share of a specific expense
    in a target currency. It includes the original share, target currency, 
    conversion rate used (if applicable), and the converted amount.
    """
    # Fetch Expense with its currency
    db_expense = await session.get(
        Expense,
        expense_id,
        options=[selectinload(Expense.currency)]
    )
    if not db_expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    target_currency = await get_object_or_404(session, Currency, target_currency_id, "Target currency not found")

    # Find current user's participation in the expense
    participant_stmt = (
        select(ExpenseParticipant)
        .where(ExpenseParticipant.expense_id == expense_id)
        .where(ExpenseParticipant.user_id == current_user.id)
        .options(
            selectinload(ExpenseParticipant.transaction).selectinload(Transaction.currency),
            selectinload(ExpenseParticipant.settled_conversion_rate)
        )
    )
    result = await session.exec(participant_stmt)
    participant = result.one_or_none()

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Current user is not a participant in this expense.",
        )

    original_share_amount = participant.share_amount
    original_currency_id = db_expense.currency_id
    
    converted_share_amount: Optional[float] = None
    conversion_rate_used: Optional[float] = None
    conversion_rate_timestamp: Optional[datetime] = None

    if original_currency_id == target_currency_id:
        converted_share_amount = original_share_amount
    else:
        # Fetch the latest conversion rate from original_currency to target_currency
        rate_stmt = (
            select(ConversionRate)
            .where(ConversionRate.from_currency_id == original_currency_id)
            .where(ConversionRate.to_currency_id == target_currency_id)
            .order_by(ConversionRate.timestamp.desc())
        )
        rate_result = await session.exec(rate_stmt)
        latest_rate = rate_result.first()

        if not latest_rate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No conversion rate found from currency {original_currency_id} to {target_currency_id}"
            )
        
        conversion_rate_used = latest_rate.rate
        conversion_rate_timestamp = latest_rate.timestamp
        converted_share_amount = round(original_share_amount * conversion_rate_used, 2) # Assuming 2 decimal places for currency

    settled_details_schema: Optional[schemas.SettledParticipationDetail] = None
    is_already_settled = participant.settled_transaction_id is not None

    if is_already_settled and participant.transaction:
        settled_currency_for_schema = None
        if participant.transaction.currency:
             settled_currency_for_schema = schemas.CurrencyRead.model_validate(participant.transaction.currency)

        settled_conversion_rate_details = None
        if participant.settled_conversion_rate:
            settled_conversion_rate_details = schemas.ConversionRateRead.model_validate(participant.settled_conversion_rate)

        settled_details_schema = schemas.SettledParticipationDetail(
            settled_transaction_id=participant.settled_transaction_id,
            settled_amount_in_transaction_currency=participant.settled_amount_in_transaction_currency,
            settled_in_currency_id=participant.transaction.currency_id,
            settled_in_currency=settled_currency_for_schema,
            settled_with_conversion_rate_id=participant.settled_with_conversion_rate_id,
            settled_at_conversion_timestamp=participant.settled_at_conversion_timestamp,
            settled_conversion_rate=settled_conversion_rate_details
        )

    return schemas.ExpenseSettlementDetails(
        expense_id=expense_id,
        participant_user_id=current_user.id,
        original_share_amount=original_share_amount,
        original_currency_id=original_currency_id,
        original_currency=schemas.CurrencyRead.model_validate(db_expense.currency),
        target_currency_id=target_currency_id,
        target_currency=schemas.CurrencyRead.model_validate(target_currency),
        conversion_rate_used=conversion_rate_used,
        conversion_rate_timestamp=conversion_rate_timestamp,
        converted_share_amount=converted_share_amount,
        is_already_settled=is_already_settled,
        settled_details=settled_details_schema
    )


@router.get(
    "/settlement-details/group/{group_id}/currency/{target_currency_id}",
    response_model=schemas.GroupSettlementDetails,
    summary="Get Settlement Details for User's Net Balances in a Group",
)
async def get_group_settlement_details(
    *,
    session: AsyncSession = Depends(get_session),
    group_id: int,
    target_currency_id: int,
    current_user: User = Depends(get_current_user),
) -> schemas.GroupSettlementDetails:
    """
    Calculates the net balance of the current user with every other member 
    in the specified group, presented in the target currency. 
    This involves summing up all unsettled shares.
    """
    group = await session.get(Group, group_id, options=[selectinload(Group.members), selectinload(Group.expenses).selectinload(Expense.all_participant_details).selectinload(ExpenseParticipant.user), selectinload(Group.expenses).selectinload(Expense.currency)])
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    if not any(member.id == current_user.id for member in group.members):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not a member of this group")

    target_currency_model = await get_object_or_404(session, Currency, target_currency_id, "Target currency not found")

    net_balances: List[schemas.NetBalanceItem] = []

    other_members = [member for member in group.members if member.id != current_user.id]

    for other_member in other_members:
        # For each other_member, calculate how much current_user owes them and how much they owe current_user
        # This will be aggregated across all UNSETTLED participations in SHARED expenses within this group.
        
        # We need to iterate through expenses in the group, then their participants.
        # An ExpenseParticipant links a user to an expense with a share_amount.
        # If ExpenseParticipant.settled_transaction_id is None, it's unsettled.

        # Positive amount means current_user owes other_member
        # Negative amount means other_member owes current_user
        # All amounts are first calculated in their original currency and then converted to target_currency.
        # For simplicity in this example, we'll assume direct conversion to target_currency for each share.
        # A more robust solution might sum by original currency first, then convert.

        current_user_owes_other_member_in_target_currency = 0.0
        other_member_owes_current_user_in_target_currency = 0.0

        for expense in group.expenses:
            # Check if both current_user and other_member are participants in this expense
            current_user_participation = None
            other_member_participation = None
            
            for p in expense.all_participant_details:
                if p.user_id == current_user.id and p.settled_transaction_id is None:
                    current_user_participation = p
                elif p.user_id == other_member.id and p.settled_transaction_id is None:
                    other_member_participation = p
            
            # Scenario 1: Expense paid by current_user, other_member is a participant and owes current_user
            if expense.paid_by_user_id == current_user.id and other_member_participation:
                amount_to_convert = other_member_participation.share_amount
                original_expense_currency_id = expense.currency_id
                
                converted_amount = await _convert_amount(
                    session, amount_to_convert, original_expense_currency_id, target_currency_id
                )
                other_member_owes_current_user_in_target_currency += converted_amount

            # Scenario 2: Expense paid by other_member, current_user is a participant and owes other_member
            elif expense.paid_by_user_id == other_member.id and current_user_participation:
                amount_to_convert = current_user_participation.share_amount
                original_expense_currency_id = expense.currency_id
                
                converted_amount = await _convert_amount(
                    session, amount_to_convert, original_expense_currency_id, target_currency_id
                )
                current_user_owes_other_member_in_target_currency += converted_amount
            
            # Scenario 3: Expense paid by a third party (or group itself if that's a feature)
            # Both current_user and other_member are participants and owe their shares to the payer.
            # This logic focuses on direct balances between current_user and other_member, 
            # so if they both owe a third party, it doesn't create a direct debt between them for *this* expense part.
            # However, if the system implies that all group expenses create debts between members relative to who paid,
            # this part might need adjustment. The current simplified model assumes direct payer-participant debt.

        net_amount_in_target_currency = round(current_user_owes_other_member_in_target_currency - other_member_owes_current_user_in_target_currency, 2)

        if net_amount_in_target_currency != 0:
            net_balances.append(schemas.NetBalanceItem(
                with_user_id=other_member.id,
                with_user=schemas.UserRead.model_validate(other_member),
                amount=net_amount_in_target_currency,
                currency_id=target_currency_id,
                currency=schemas.CurrencyRead.model_validate(target_currency_model)
            ))

    return schemas.GroupSettlementDetails(
        group_id=group_id,
        current_user_id=current_user.id,
        target_currency_id=target_currency_id,
        target_currency=schemas.CurrencyRead.model_validate(target_currency_model),
        net_balances=net_balances
    )


async def _convert_amount(session: AsyncSession, amount: float, from_currency_id: int, to_currency_id: int) -> float:
    if from_currency_id == to_currency_id:
        return amount
    
    rate_stmt = (
        select(ConversionRate)
        .where(ConversionRate.from_currency_id == from_currency_id)
        .where(ConversionRate.to_currency_id == to_currency_id)
        .order_by(ConversionRate.timestamp.desc())
    )
    rate_result = await session.exec(rate_stmt)
    latest_rate = rate_result.first()

    if not latest_rate:
        # Attempt reverse conversion if direct rate not found
        reverse_rate_stmt = (
            select(ConversionRate)
            .where(ConversionRate.from_currency_id == to_currency_id)
            .where(ConversionRate.to_currency_id == from_currency_id)
            .order_by(ConversionRate.timestamp.desc())
        )
        reverse_rate_result = await session.exec(reverse_rate_stmt)
        latest_reverse_rate = reverse_rate_result.first()
        if latest_reverse_rate and latest_reverse_rate.rate != 0:
            return round(amount / latest_reverse_rate.rate, 2)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No conversion rate found between currency {from_currency_id} and {to_currency_id}, or its reverse."
            )
    return round(amount * latest_rate.rate, 2)


# TODO:  audit/test this properly


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
                selectinload(ExpenseParticipant.transaction).selectinload(
                    Transaction.currency
                ),
            ),
        ],
    )
    if not db_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found",
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
            selectinload(Expense.all_participant_details).options(
                selectinload(ExpenseParticipant.user).selectinload(User.groups)
            ),
            selectinload(Expense.all_participant_details).options(
                selectinload(ExpenseParticipant.transaction).selectinload(
                    Transaction.currency
                )
            ),
        )
    )
    result = await session.exec(stmt)
    refreshed_db_expense = result.one_or_none()

    if not refreshed_db_expense:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to re-fetch expense after update with full details",
        )

    # Manually construct and return ExpenseRead with participant_details
    return await _get_expense_read_details(
        session=session, db_expense=refreshed_db_expense
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
