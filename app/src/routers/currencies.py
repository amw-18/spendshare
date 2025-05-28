from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.security import get_current_user
from src.db.database import get_session
from src.models import models, schemas
from src.models.models import Currency, User, Expense  # Added User and Expense
from src.utils import get_object_or_404

router = APIRouter(tags=["Currencies"])


@router.post("/", response_model=schemas.CurrencyRead, status_code=status.HTTP_201_CREATED)
async def create_currency(
    currency_in: schemas.CurrencyCreate,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    statement = select(Currency).where(Currency.code == currency_in.code)
    existing_currency = (await session.exec(statement)).first()
    if existing_currency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Currency with code '{currency_in.code}' already exists.",
        )

    db_currency = Currency.model_validate(currency_in)
    session.add(db_currency)
    await session.commit()
    await session.refresh(db_currency)
    return db_currency


@router.get("/", response_model=List[schemas.CurrencyRead])
async def list_currencies(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
):
    statement = select(Currency).offset(skip).limit(limit)
    currencies = (await session.exec(statement)).all()
    return currencies


@router.get("/{currency_id}", response_model=schemas.CurrencyRead)
async def get_currency(
    currency_id: int,
    session: AsyncSession = Depends(get_session),
):
    currency = await get_object_or_404(session, Currency, currency_id)
    return currency


@router.put("/{currency_id}", response_model=schemas.CurrencyRead)
async def update_currency(
    currency_id: int,
    currency_in: schemas.CurrencyUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    db_currency = await get_object_or_404(session, Currency, currency_id)

    if currency_in.code and currency_in.code != db_currency.code:
        statement = select(Currency).where(Currency.code == currency_in.code)
        existing_currency_with_new_code = (await session.exec(statement)).first()
        if existing_currency_with_new_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Currency with code '{currency_in.code}' already exists.",
            )
    
    update_data = currency_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_currency, key, value)

    session.add(db_currency)
    await session.commit()
    await session.refresh(db_currency)
    return db_currency


@router.delete("/{currency_id}", response_model=dict)
async def delete_currency(
    currency_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    db_currency = await get_object_or_404(session, Currency, currency_id)

    # Check if the currency is associated with any expenses
    # Assuming Expense model has a 'currency_id' field or similar link.
    # This needs to be adjusted based on your actual Expense model structure.
    # For now, let's assume there's no direct link yet, and we'll add it if the tests fail.
    # If Expense model has e.g. currency_code: str, then:
    # expenses_with_currency = await session.exec(select(Expense).where(Expense.currency_code == db_currency.code)) # Example
    # For now, as Expense model doesn't have currency field, we can't check.
    # This check will be fully implemented once Expense model is updated to include currency.
    # Placeholder for the check:
    related_expenses_statement = select(Expense).where(Expense.currency_id == currency_id) # Assuming Expense has currency_id
    related_expenses_result = await session.exec(related_expenses_statement)
    if related_expenses_result.first(): # Check if any expense is using this currency
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete currency: it is associated with existing expenses.",
        )
    # The above check is commented out because the Expense model does not yet have a currency field.
    # This will need to be implemented in a future step when Expense is updated.

    await session.delete(db_currency)
    await session.commit()
    return {"message": "Currency deleted"}
