from typing import List, Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, or_

from src.db.database import get_session # Assuming this provides AsyncSession
from src.models import schemas # Updated schemas
from src.models.models import User
from src.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user, # Assuming this is get_current_active_user which checks for active (verified) status
)
from src.core.email import send_verification_email, send_email_change_verification_email
from src.utils import get_object_or_404 # get_optional_object_by_attribute might need review

from datetime import datetime, timedelta, timezone
import secrets

router = APIRouter(
    prefix="/api/v1/users",  # Changed prefix
    tags=["users"],
)


@router.post("/register", response_model=schemas.MessageResponse, status_code=status.HTTP_202_ACCEPTED)
async def register_user(user_in: schemas.UserRegister, session: AsyncSession = Depends(get_session)):
    # Check for existing email or username
    statement = select(User).where(
        or_(User.email == user_in.email, User.username == user_in.username)
    )
    result = await session.exec(statement)
    existing_user = result.first()

    if existing_user:
        if existing_user.email_verified:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or username already registered and verified.")

        token_expires_at = existing_user.email_verification_token_expires_at
        if isinstance(token_expires_at, datetime): # Ensure it's a datetime object
            if not existing_user.email_verified and token_expires_at and token_expires_at < datetime.now(timezone.utc):
                # Overwrite existing unverified user's token and details
                existing_user.email = user_in.email
                existing_user.username = user_in.username
                existing_user.full_name = user_in.full_name
                existing_user.hashed_password = get_password_hash(user_in.password)
                existing_user.email_verification_token = secrets.token_urlsafe(32)
                existing_user.email_verification_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
                existing_user.email_verified = False # Ensure it's false
                session.add(existing_user)
                await session.commit()
                await session.refresh(existing_user)
                await send_verification_email(existing_user.email, existing_user.email_verification_token)
                return schemas.MessageResponse(message="Registration initiated. Please check your email to verify your account.")
        # If not expired or other conditions, raise error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or username already registered or pending verification with a valid token.")

    hashed_password = get_password_hash(user_in.password)
    verification_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    db_user = User(
        email=user_in.email,
        username=user_in.username,
        full_name=user_in.full_name,
        hashed_password=hashed_password,
        email_verified=False,
        email_verification_token=verification_token,
        email_verification_token_expires_at=expires_at
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    await send_verification_email(db_user.email, verification_token)
    return schemas.MessageResponse(message="Registration initiated. Please check your email to verify your account.")


@router.get("/verify-email", response_model=schemas.MessageResponse)
async def verify_email(token: str, session: AsyncSession = Depends(get_session)):
    statement = select(User).where(User.email_verification_token == token)
    result = await session.exec(statement)
    user = result.first()

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token.")
    if user.email_verified:
        # Allow re-verification if token is somehow valid but already verified? Or just inform?
        # For now, let's say it's an invalid state for this token.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified.")

    token_expires_at = user.email_verification_token_expires_at
    if not isinstance(token_expires_at, datetime) or token_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification token expired.")

    user.email_verified = True
    user.email_verification_token = None
    user.email_verification_token_expires_at = None
    session.add(user)
    await session.commit()
    return schemas.MessageResponse(message="Email verified successfully. You can now log in.")


@router.post("/resend-verification-email", response_model=schemas.MessageResponse, status_code=status.HTTP_202_ACCEPTED)
async def resend_verification_email_endpoint(request: schemas.ResendVerificationEmailRequest, session: AsyncSession = Depends(get_session)):
    statement = select(User).where(User.email == request.email)
    result = await session.exec(statement)
    user = result.first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with this email not found.")
    if user.email_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already verified.")

    user.email_verification_token = secrets.token_urlsafe(32)
    user.email_verification_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    session.add(user)
    await session.commit()
    await send_verification_email(user.email, user.email_verification_token)
    return schemas.MessageResponse(message="Verification email resent. Please check your inbox.")


@router.get("/search", response_model=List[schemas.UserRead])
async def search_users_endpoint(
    *,
    query: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[User]:
    if not query or len(query) < 2:
        return []

    statement = (
        select(User)
        .where(User.email_verified == True) # Only search verified users
        .where(or_(User.username.ilike(f"%{query}%"), User.email.ilike(f"%{query}%")))
        .limit(20)
    )
    result = await session.exec(statement)
    users = list(result)
    return users


@router.get("/me", response_model=schemas.UserRead)
async def read_current_user_me_endpoint(
    current_user: User = Depends(get_current_user), # get_current_user should ensure user is active/verified
) -> User:
    return current_user


@router.put("/me/email", response_model=schemas.MessageResponse, status_code=status.HTTP_202_ACCEPTED)
async def change_user_email_request(
    request: schemas.UserEmailChangeRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if not current_user.email_verified: # Should be redundant if get_current_user checks this
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified.")

    if not verify_password(request.password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password.")
    if request.new_email == current_user.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New email cannot be the same as the current email.")

    # Check if the new email is already in use by another VERIFIED user
    statement = select(User).where(User.email == request.new_email, User.id != current_user.id, User.email_verified == True)
    result = await session.exec(statement)
    existing_email_user = result.first()
    if existing_email_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This email address is already in use by another verified account.")

    current_user.new_email_pending_verification = request.new_email
    current_user.email_change_token = secrets.token_urlsafe(32)
    current_user.email_change_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    session.add(current_user)
    await session.commit()

    await send_email_change_verification_email(request.new_email, current_user.email_change_token)
    return schemas.MessageResponse(message="Email change initiated. Please check your new email address to verify.")


@router.get("/verify-email-change", response_model=schemas.MessageResponse)
async def verify_email_change(token: str, session: AsyncSession = Depends(get_session)):
    statement = select(User).where(User.email_change_token == token)
    result = await session.exec(statement)
    user = result.first()

    if not user or not user.new_email_pending_verification:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or no pending email change for this token.")

    token_expires_at = user.email_change_token_expires_at
    if not isinstance(token_expires_at, datetime) or token_expires_at < datetime.now(timezone.utc):
        user.new_email_pending_verification = None
        user.email_change_token = None
        user.email_change_token_expires_at = None
        session.add(user)
        await session.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email change token expired. Please try changing your email again.")

    # Check again if the new email has been taken by someone else in the meantime
    statement_conflict = select(User).where(
        User.email == user.new_email_pending_verification,
        User.id != user.id,
        User.email_verified == True
    )
    result_conflict = await session.exec(statement_conflict)
    conflicting_user = result_conflict.first()
    if conflicting_user:
        user.new_email_pending_verification = None
        user.email_change_token = None
        user.email_change_token_expires_at = None
        session.add(user)
        await session.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This email address has been taken by another user. Please try a different email.")

    user.email = user.new_email_pending_verification
    user.new_email_pending_verification = None
    user.email_change_token = None
    user.email_change_token_expires_at = None
    session.add(user)
    await session.commit()
    return schemas.MessageResponse(message="Email address updated successfully.")


@router.get("/{user_id}", response_model=schemas.UserRead)
async def read_user_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    user_id: int,
    current_user: User = Depends(get_current_user), # Ensures requester is authenticated
) -> User:
    db_user = await get_object_or_404(session, User, user_id)
    if not db_user.email_verified:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or not verified.")
    return db_user


@router.put("/{user_id}", response_model=schemas.UserRead)
async def update_user_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    user_id: int,
    user_in: schemas.UserUpdate, # UserUpdate schema prevents email changes
    current_user: User = Depends(get_current_user),
) -> User:
    target_user = await get_object_or_404(session, User, user_id)

    if not target_user.email_verified:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify an unverified user account.")

    if current_user.id != target_user.id: # Add admin check here in future if needed
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user account",
        )

    user_data = user_in.model_dump(exclude_unset=True)

    if "username" in user_data and user_data["username"] != target_user.username:
        statement = select(User).where(User.username == user_data["username"], User.id != target_user.id)
        result = await session.exec(statement)
        existing_user_username = result.first()
        if existing_user_username:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken.")
        target_user.username = user_data["username"]

    if "password" in user_data and user_data["password"] is not None:
        target_user.hashed_password = get_password_hash(user_data["password"])

    if "full_name" in user_data:
         target_user.full_name = user_data["full_name"]

    session.add(target_user)
    await session.commit()
    await session.refresh(target_user)
    return target_user


@router.delete("/{user_id}", response_model=schemas.MessageResponse) # Return MessageResponse
async def delete_user_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    user_id: int,
    current_user: User = Depends(get_current_user),
) -> schemas.MessageResponse:
    target_user = await get_object_or_404(session, User, user_id)

    # User can only delete their own account (add admin check here in future)
    if current_user.id != target_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user account",
        )

    # Consider what happens to related data (e.g. expenses). Cascade deletes in model should handle it.
    # If not verified, maybe allow deletion without being "active"?
    # For now, consistent that target_user must exist and be accessible.

    await session.delete(target_user)
    await session.commit()
    return schemas.MessageResponse(message=f"User {user_id} deleted successfully.")


@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    statement = select(User).where(User.username == form_data.username)
    result = await session.exec(statement)
    user = result.first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not verified. Please check your email for a verification link.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.username, "user_id": str(user.id)} # Ensure user_id is string for jwt
    )
    return schemas.Token(access_token=access_token, token_type="bearer")

