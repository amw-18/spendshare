from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query # Added Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload # For selectinload in GET /

# Database and Security
from app.src.db.database import get_session
from app.src.core.security import get_current_user

# Models
from app.src.models.models import User, Currency, ConversionRate

# Schemas
from app.src.models.schemas import (
    ConversionRateCreate,
    ConversionRateRead,
    CurrencyRead, # Used for populating nested currency details in ConversionRateRead
)

# Utils
from app.src.utils import get_object_or_404


router = APIRouter(
    prefix="/api/v1/conversion-rates", 
    tags=["Conversion Rates"]
)


@router.post("/", response_model=ConversionRateRead, status_code=status.HTTP_201_CREATED)
async def create_conversion_rate(
    rate_in: ConversionRateCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create conversion rates",
        )

    if rate_in.from_currency_id == rate_in.to_currency_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create a conversion rate for the same currency",
        )

    # Validate that both currencies exist
    from_currency_obj = await get_object_or_404(
        session, Currency, rate_in.from_currency_id, "From currency not found"
    )
    to_currency_obj = await get_object_or_404(
        session, Currency, rate_in.to_currency_id, "To currency not found"
    )
    
    # Create the ConversionRate instance
    # timestamp will be set by default_factory in the model
    db_conversion_rate = ConversionRate.model_validate(rate_in)
    
    session.add(db_conversion_rate)
    await session.commit()
    await session.refresh(db_conversion_rate) # Refresh to get ID and default timestamp

    # For the response, we want to include the full currency objects.
    # We already fetched them (from_currency_obj, to_currency_obj).
    # The db_conversion_rate itself doesn't have these loaded yet from relationships.
    
    # Construct the response model by validating the db_conversion_rate and then
    # updating it with the already fetched currency objects.
    response_data = ConversionRateRead.model_validate(
        db_conversion_rate,
        update={
            "from_currency": CurrencyRead.model_validate(from_currency_obj),
            "to_currency": CurrencyRead.model_validate(to_currency_obj),
        }
    )
    return response_data


@router.get("/", response_model=List[ConversionRateRead])
async def read_conversion_rates(
    session: AsyncSession = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
):
    statement = (
        select(ConversionRate)
        .options(
            selectinload(ConversionRate.from_currency), 
            selectinload(ConversionRate.to_currency)
        )
        .offset(skip)
        .limit(limit)
        .order_by(ConversionRate.timestamp.desc())
    )
    # Using session.exec() as it's the preferred way in SQLModel for type-hinted results
    # and directly returns model instances.
    result = await session.exec(statement)
    db_rates = result.all()
    
    # SQLModel will automatically map these db_rates (ConversionRate instances with loaded relationships)
    # to ConversionRateRead Pydantic models.
    return db_rates


@router.get("/latest", response_model=ConversionRateRead)
async def read_latest_conversion_rate(
    session: AsyncSession = Depends(get_session),
    from_code: str = Query(..., description="Currency code to convert from (e.g., USD)"),
    to_code: str = Query(..., description="Currency code to convert to (e.g., EUR)"),
):
    if from_code.upper() == to_code.upper():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot get a conversion rate for the same currency",
        )

    # Fetch 'from' currency
    stmt_from = select(Currency).where(Currency.code == from_code.upper())
    db_from_currency = (await session.exec(stmt_from)).first()
    if not db_from_currency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"From currency code '{from_code.upper()}' not found",
        )

    # Fetch 'to' currency
    stmt_to = select(Currency).where(Currency.code == to_code.upper())
    db_to_currency = (await session.exec(stmt_to)).first()
    if not db_to_currency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"To currency code '{to_code.upper()}' not found",
        )

    # Fetch the latest conversion rate
    statement = (
        select(ConversionRate)
        .where(
            ConversionRate.from_currency_id == db_from_currency.id,
            ConversionRate.to_currency_id == db_to_currency.id,
        )
        .options(
            selectinload(ConversionRate.from_currency), # Eager load for response model
            selectinload(ConversionRate.to_currency)   # Eager load for response model
        )
        .order_by(ConversionRate.timestamp.desc())
        .limit(1)
    )
    db_rate = (await session.exec(statement)).first()

    if not db_rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversion rate from {from_code.upper()} to {to_code.upper()} not found",
        )
    
    return db_rate
