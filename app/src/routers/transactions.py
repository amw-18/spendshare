from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession # Changed import
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone

from src.models.models import User, Transaction, Currency, ExpenseParticipant
from src.models.schemas import (
    TransactionCreate,
    TransactionRead,
    # CurrencyRead, # CurrencyRead is resolved via Transaction.currency relationship
)
from src.core.security import get_current_user # Corrected path to core.security
from src.db.database import get_session

router = APIRouter(
    prefix="/transactions", # Corrected prefix
    tags=["Transactions"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
async def create_transaction( # Added async
    *,
    session: AsyncSession = Depends(get_session), # Changed to AsyncSession
    current_user: User = Depends(get_current_user),
    transaction_in: TransactionCreate,
):
    """
    Create a new transaction.
    """
    currency = await session.get(Currency, transaction_in.currency_id) # Added await
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
    await session.commit() # Added await
    await session.refresh(db_transaction) # Added await
    # await session.refresh(db_transaction, attribute_names=['currency']) # To load relationship

    # Re-fetch with options to ensure relationships are loaded for the response model.
    # This is often the most reliable way with async sessions too.
    # After commit & refresh, the db_transaction object should have its ID.
    # Accessing db_transaction.currency might trigger a load if lazy loading is configured and allowed in async,
    # but explicit loading is safer for response models.

    # Forcing load of currency for the response.
    # The refresh above might not be enough for related objects in async,
    # an explicit query with options is better.
    loaded_transaction_stmt = (
        select(Transaction)
        .options(selectinload(Transaction.currency)) # Eagerly load currency
        .where(Transaction.id == db_transaction.id)
    )
    result = await session.exec(loaded_transaction_stmt) # Added await
    loaded_transaction = result.first()

    if not loaded_transaction:
         # This should ideally not happen if commit was successful
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create or retrieve transaction after commit")

    return loaded_transaction


@router.get("/{transaction_id}", response_model=TransactionRead)
async def read_transaction( # Added async
    *,
    session: AsyncSession = Depends(get_session), # Changed to AsyncSession
    current_user: User = Depends(get_current_user),
    transaction_id: int,
):
    """
    Get a specific transaction by its ID.
    """
    # Query for the transaction and eagerly load the currency
    statement = (
        select(Transaction)
        .options(selectinload(Transaction.currency)) # Eagerly load currency
        .where(Transaction.id == transaction_id)
    )
    result = await session.exec(statement) # Added await
    transaction = result.first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )

    # Authorization check
    if transaction.created_by_user_id != current_user.id and not current_user.is_admin:
        # Check if user is a participant in an expense settled by this transaction
        participant_link_stmt = (
            select(ExpenseParticipant)
            .where(ExpenseParticipant.settled_transaction_id == transaction.id)
            .where(ExpenseParticipant.user_id == current_user.id)
        )
        result = await session.exec(participant_link_stmt) # Added await
        is_participant = result.first()

        if not is_participant:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this transaction",
            )

    return transaction
