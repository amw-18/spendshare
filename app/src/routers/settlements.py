from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from src.db.database import get_session
from src.models import schemas # Import schemas
from src.models.models import (
    User,
    Transaction,
    Expense,
    ExpenseParticipant,
    Currency,
)
from src.core.security import get_current_user
from src.utils import get_object_or_404
from src.services.expense_service import update_expense_settlement_status

router = APIRouter(
    prefix="/settlements",
    tags=["settlements"],
)

# Placeholder for the new endpoint, will be implemented next
@router.post(
    "/record-direct-payment",
    response_model=schemas.SettlementResponse,
    status_code=status.HTTP_200_OK,
)
async def record_direct_payment_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    payment_request: schemas.RecordDirectPaymentRequest,
):
    # --- Input Validation and Authorization ---
    # 1. Validate existence of debtor, creditor, and currency
    debtor_user = await get_object_or_404(session, User, payment_request.debtor_user_id, "Debtor user not found.")
    creditor_user = await get_object_or_404(session, User, payment_request.creditor_user_id, "Creditor user not found.")
    await get_object_or_404(session, Currency, payment_request.currency_paid_id, "Currency not found.")

    # 2. Authorization: Current user must be either the debtor or the creditor.
    if current_user.id != debtor_user.id and current_user.id != creditor_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to record this payment. Must be the debtor or creditor.",
        )

    # --- Transaction Creation ---
    # Create a new Transaction record for this direct payment
    new_transaction = Transaction(
        amount=payment_request.amount_paid,
        currency_id=payment_request.currency_paid_id,
        created_by_user_id=current_user.id, # User recording the payment
        description=f"Direct payment from {debtor_user.username} (ID: {debtor_user.id}) to {creditor_user.username} (ID: {creditor_user.id}), recorded by {current_user.username}.",
    )
    session.add(new_transaction)
    await session.flush() # To get new_transaction.id
    await session.refresh(new_transaction)


    # --- Settlement of Expense Participants ---
    results: List[schemas.SettlementResultItem] = []
    updated_participants_to_commit = []
    affected_expense_ids = set()
    total_share_amount_to_be_settled = 0.0

    # Check for duplicate expense_participant_ids in the request
    seen_ep_ids_in_request = set()
    for ep_id_check in payment_request.expense_participant_ids_to_settle:
        if ep_id_check in seen_ep_ids_in_request:
            await session.rollback() # Rollback transaction creation
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate expense_participant_id {ep_id_check} in settlement request.",
            )
        seen_ep_ids_in_request.add(ep_id_check)

    for ep_id in payment_request.expense_participant_ids_to_settle:
        stmt_ep = (
            select(ExpenseParticipant)
            .options(selectinload(ExpenseParticipant.expense)) # Eagerly load parent expense
            .where(ExpenseParticipant.id == ep_id)
        )
        result_ep = await session.exec(stmt_ep)
        expense_participant = result_ep.first()

        if not expense_participant:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ExpenseParticipant record with ID {ep_id} not found.",
            )

        if not expense_participant.expense: # Should be loaded
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not load parent expense for participant ID {ep_id}.",
            )

        # Validate that the participant's user_id matches the debtor_user_id from the request
        if expense_participant.user_id != payment_request.debtor_user_id:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"ExpenseParticipant ID {ep_id} does not belong to debtor user ID {payment_request.debtor_user_id}.",
            )

        # Validate that the original payer of the expense matches the creditor_user_id from the request
        if expense_participant.expense.paid_by_user_id != payment_request.creditor_user_id:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Expense for participant ID {ep_id} was not paid by creditor user ID {payment_request.creditor_user_id}.",
            )

        # Check if already settled by another transaction
        if expense_participant.settled_transaction_id and \
           expense_participant.settled_transaction_id != new_transaction.id: # Check if it's settled by a *different* transaction
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Expense participation ID {ep_id} is already settled by transaction {expense_participant.settled_transaction_id}.",
            )

        # Update ExpenseParticipant
        # For this endpoint, we assume the share_amount of the participant is what's being settled.
        # The `amount_paid` in the request should ideally sum up to the total of share_amounts of all participants being settled.
        expense_participant.settled_transaction_id = new_transaction.id
        expense_participant.settled_amount_in_transaction_currency = expense_participant.share_amount
        # Note: currency of settlement is implicitly the transaction's currency (payment_request.currency_paid_id)

        total_share_amount_to_be_settled += expense_participant.share_amount

        session.add(expense_participant)
        updated_participants_to_commit.append(expense_participant)
        affected_expense_ids.add(expense_participant.expense_id)

        results.append(
            schemas.SettlementResultItem(
                expense_participant_id=ep_id,
                settled_transaction_id=new_transaction.id,
                settled_amount_in_transaction_currency=expense_participant.share_amount,
                settled_currency_id=new_transaction.currency_id,
                message="Settled successfully via direct payment recording.",
            )
        )

    # Validate that the total amount_paid in the request matches the sum of share_amounts settled
    # Using a small tolerance for float comparison
    if abs(total_share_amount_to_be_settled - payment_request.amount_paid) > 1e-2: # 0.01 tolerance
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Amount paid ({payment_request.amount_paid}) does not match the total sum of shares to be settled ({total_share_amount_to_be_settled:.2f}).",
        )

    # Commit all changes: Transaction, ExpenseParticipant updates
    try:
        await session.commit()
        for ep in updated_participants_to_commit:
            await session.refresh(ep)
        await session.refresh(new_transaction) # Refresh the transaction as well

        # After successful settlement of participants, update parent expense statuses
        for expense_id in affected_expense_ids:
            await update_expense_settlement_status(expense_id, session)

        await session.commit() # Commit changes to Expense statuses

    except Exception as e:
        await session.rollback()
        # Log the exception e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during the settlement process: {str(e)}",
        )

    return schemas.SettlementResponse(
        status="Completed",
        message="Direct payment recorded and relevant expense participations settled.",
        updated_expense_participations=results,
    )
