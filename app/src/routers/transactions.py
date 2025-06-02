from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession  # Changed import
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone

from src.models.models import User, Transaction, Currency, ExpenseParticipant, ConversionRate, Expense
from src.models.schemas import (
    TransactionCreate,
    TransactionRead,
    CreateSettlementTransactionRequest,
    CreateSettlementTransactionResponse,
    UpdatedExpenseStatus
)
from src.core.security import get_current_user  # Corrected path to core.security
from src.db.database import get_session
from src.utils import get_object_or_404 # For fetching objects or raising 404

router = APIRouter(
    prefix="/transactions",  # Corrected prefix
    tags=["Transactions"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
async def create_transaction(  # Added async
    *,
    session: AsyncSession = Depends(get_session),  # Changed to AsyncSession
    current_user: User = Depends(get_current_user),
    transaction_in: TransactionCreate,
):
    """
    Create a new transaction.
    """
    currency = await session.get(Currency, transaction_in.currency_id)  # Added await
    if not currency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Currency with id {transaction_in.currency_id} not found",
        )

    db_transaction = Transaction.model_validate(
        transaction_in,
        update={
            "created_by_user_id": current_user.id,
            "timestamp": datetime.now(timezone.utc),
            # 'currency': currency  # Not needed to set here, relationship will be formed by currency_id
        },
    )

    session.add(db_transaction)
    await session.commit()  # Added await
    await session.refresh(db_transaction)  # Added await
    await session.refresh(
        db_transaction, attribute_names=["currency"]
    )  # To load relationship

    return db_transaction


@router.get("/{transaction_id}", response_model=TransactionRead)
async def read_transaction(  # Added async
    *,
    session: AsyncSession = Depends(get_session),  # Changed to AsyncSession
    current_user: User = Depends(get_current_user),
    transaction_id: int,
):
    """
    Get a specific transaction by its ID.
    """
    # Query for the transaction and eagerly load the currency
    statement = (
        select(Transaction)
        .options(selectinload(Transaction.currency))  # Eagerly load currency
        .where(Transaction.id == transaction_id)
    )
    result = await session.exec(statement)  # Added await
    transaction = result.first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )

    # Authorization check
    # If the current user is not the creator, they must be a participant in an expense settled by this transaction.
    if transaction.created_by_user_id != current_user.id:
        # Check if user is a participant in an expense settled by this transaction
        participant_link_stmt = (
            select(ExpenseParticipant)
            .where(ExpenseParticipant.settled_transaction_id == transaction.id)
            .where(ExpenseParticipant.user_id == current_user.id)
        )
        result = await session.exec(participant_link_stmt)  # Added await
        is_participant = result.first()

        if not is_participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this transaction",
            )

    return transaction


@router.post("/settle", response_model=CreateSettlementTransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_settlement_transaction(
    *,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    settlement_request: CreateSettlementTransactionRequest,
) -> CreateSettlementTransactionResponse:
    """
    Creates a new transaction to settle one or more expense participations.
    Handles currency conversion and updates expense settlement status.
    """
    transaction_input = settlement_request.transaction
    await get_object_or_404(session, Currency, transaction_input.currency_id, "Transaction currency not found")

    conversion_rate_model: Optional[ConversionRate] = None
    if settlement_request.conversion_rate_id:
        conversion_rate_model = await get_object_or_404(
            session, ConversionRate, settlement_request.conversion_rate_id, "Conversion rate not found"
        )

    # Create the main transaction record
    db_transaction = Transaction(
        description=transaction_input.description or "Settlement Transaction",
        amount=transaction_input.amount, # This should be the sum of all item.amount_to_settle_in_transaction_currency
        currency_id=transaction_input.currency_id,
        transaction_type=transaction_input.transaction_type or "settlement", # Ensure this type is meaningful
        timestamp=datetime.now(timezone.utc),
        created_by_user_id=current_user.id,
        # paid_to_user_id could be added if settling a specific debt to one user
    )
    session.add(db_transaction)
    # We need the transaction ID for ExpenseParticipant updates, so flush or commit before loop if FK is immediate.
    # SQLModel usually handles this fine with a final commit.

    settled_participations_details: List[schemas.SettledParticipationDetail] = []
    updated_expenses_details: List[schemas.UpdatedExpenseStatus] = []
    affected_expense_ids = set()

    total_settled_amount_in_tx_currency = 0.0

    for item in settlement_request.settlement_items:
        participant = await session.get(
            ExpenseParticipant, 
            item.expense_participant_id, 
            options=[selectinload(ExpenseParticipant.expense).selectinload(Expense.currency)]
        )

        if not participant:
            await session.rollback()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ExpenseParticipant with id {item.expense_participant_id} not found.")
        
        if participant.settled_transaction_id:
            await session.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"ExpenseParticipant id {participant.id} is already settled.")

        # Authorization: Current user must be the payer of the transaction.
        # The items being settled can belong to anyone involved in the expense.
        # More complex auth (e.g. current_user must be part of the expense) could be added.

        original_expense_currency_id = participant.expense.currency_id
        
        # Validate currency and conversion rate consistency
        if conversion_rate_model:
            if not (conversion_rate_model.from_currency_id == original_expense_currency_id and 
                    conversion_rate_model.to_currency_id == db_transaction.currency_id):
                await session.rollback()
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Conversion rate does not match currencies for participant {participant.id}.")
            
            # Optional: Verify item.amount_to_settle_in_transaction_currency against calculated conversion
            # calculated_amount = round(participant.share_amount * conversion_rate_model.rate, 2)
            # if abs(calculated_amount - item.amount_to_settle_in_transaction_currency) > 0.005: # tolerance for float precision
            #     await session.rollback()
            #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Provided settlement amount for P_ID {participant.id} does not match calculated conversion.")

            participant.settled_with_conversion_rate_id = conversion_rate_model.id
            participant.settled_at_conversion_timestamp = conversion_rate_model.timestamp
        else: # No conversion rate provided, settlement must be in original expense currency
            if db_transaction.currency_id != original_expense_currency_id:
                await session.rollback()
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Transaction currency must match expense currency for P_ID {participant.id} if no conversion rate is used.")
            # Optional: Verify item.amount_to_settle_in_transaction_currency against original share
            # if abs(participant.share_amount - item.amount_to_settle_in_transaction_currency) > 0.005:
            #     await session.rollback()
            #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Provided settlement amount for P_ID {participant.id} does not match original share amount.")

        participant.settled_transaction = db_transaction # Link via relationship
        participant.settled_amount_in_transaction_currency = item.amount_to_settle_in_transaction_currency
        session.add(participant)
        total_settled_amount_in_tx_currency += item.amount_to_settle_in_transaction_currency
        affected_expense_ids.add(participant.expense_id)

        # Prepare details for response
        settled_participations_details.append(schemas.SettledParticipationDetail(
            expense_participant_id=participant.id,
            settled_transaction_id=db_transaction.id, # Will be None until commit and refresh, but schema expects int
            settled_amount_in_transaction_currency=participant.settled_amount_in_transaction_currency,
            settled_in_currency_id=db_transaction.currency_id,
            settled_with_conversion_rate_id=participant.settled_with_conversion_rate_id,
            settled_at_conversion_timestamp=participant.settled_at_conversion_timestamp
        ))

    # Validate that the sum of amounts in settlement_items matches the transaction.amount
    if abs(db_transaction.amount - total_settled_amount_in_tx_currency) > 0.005: # tolerance
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sum of settlement item amounts does not match transaction amount.")

    try:
        await session.commit() # This will commit the transaction and all participant updates
        await session.refresh(db_transaction)
        # Refresh participants to get updated fields and FKs for response
        for detail in settled_participations_details:
            detail.settled_transaction_id = db_transaction.id # Now it has an ID
            # participant_model = await session.get(ExpenseParticipant, detail.expense_participant_id, options=[selectinload(ExpenseParticipant.settled_conversion_rate)])
            # if participant_model and participant_model.settled_conversion_rate:
            #     detail.settled_conversion_rate = schemas.ConversionRateRead.model_validate(participant_model.settled_conversion_rate)
            # if participant_model and db_transaction.currency:
            #     detail.settled_in_currency = schemas.CurrencyRead.model_validate(db_transaction.currency)

        for expense_id in affected_expense_ids:
            updated_status = await _update_expense_settlement_status(expense_id, session)
            if updated_status:
                updated_expenses_details.append(updated_status)
        await session.commit() # Commit expense status updates

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred during settlement: {str(e)}")
    
    # Refresh transaction again to load relationships for the response, e.g., currency
    await session.refresh(db_transaction, attribute_names=["currency"])

    return schemas.CreateSettlementTransactionResponse(
        transaction=schemas.TransactionRead.model_validate(db_transaction),
        settled_participations=settled_participations_details,
        updated_expenses=updated_expenses_details
    )


async def _update_expense_settlement_status(expense_id: int, session: AsyncSession) -> Optional[UpdatedExpenseStatus]:
    """Checks if all participants of an expense are settled and updates Expense.is_settled."""
    stmt_participants = (
        select(ExpenseParticipant)
        .where(ExpenseParticipant.expense_id == expense_id)
    )
    result_participants = await session.exec(stmt_participants)
    all_participants = result_participants.all()

    if not all_participants:
        return None # Or raise error, as an expense should have participants

    all_are_settled = all(p.settled_transaction_id is not None for p in all_participants)

    expense_to_update = await session.get(Expense, expense_id)
    if not expense_to_update:
        # This should ideally not happen if participant.expense_id was valid
        return None 

    if all_are_settled and not expense_to_update.is_settled:
        expense_to_update.is_settled = True
        session.add(expense_to_update)
        # The commit will be handled by the calling function (create_settlement_transaction)
        return schemas.UpdatedExpenseStatus(expense_id=expense_id, is_now_settled=True)
    elif not all_are_settled and expense_to_update.is_settled: # Edge case: mark as unsettled if a settlement was reverted?
        expense_to_update.is_settled = False
        session.add(expense_to_update)
        return schemas.UpdatedExpenseStatus(expense_id=expense_id, is_now_settled=False)
    
    return None # No change in settlement status or already correctly set

