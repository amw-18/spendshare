from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession # Use AsyncSession
from sqlalchemy.exc import SQLAlchemyError


from src.models import schemas
from src.models.models import BetaInterest # Import the model
from src.db.database import get_session # Use get_session for async
from src.core.email import send_beta_interest_email
from src.config import Settings # Import Settings
from src.dependencies import get_settings # Import dependency for settings

router = APIRouter(
    prefix="/beta",
    tags=["Beta"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/interest",
    response_model=schemas.BetaInterestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Interest for Beta Program",
    description="Allows users to register their interest in the beta program by providing their email.",
)
async def register_beta_interest(
    payload: schemas.BetaInterestCreate,
    db: AsyncSession = Depends(get_session), # Use AsyncSession and get_session
    settings: Settings = Depends(get_settings),
):
    """
    Register interest for the beta program.

    - **email**: Email address of the user.
    - **description**: Optional description or reason for interest.
    """
    db_beta_interest = BetaInterest(
        email=payload.email,
        description=payload.description
    )

    try:
        db.add(db_beta_interest)
        await db.commit()
        await db.refresh(db_beta_interest)
    except SQLAlchemyError as e:
        await db.rollback()
        # Log the error e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while registering interest. Please try again later.",
        )

    # Send email notification (logging for now)
    send_beta_interest_email(
        email_to=settings.SUPPORT_EMAIL,
        interested_email=payload.email,
        description=payload.description,
    )

    return schemas.BetaInterestResponse(
        message="Successfully registered interest." # Generic success message
    )
