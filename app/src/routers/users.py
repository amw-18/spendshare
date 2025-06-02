from typing import List, Optional  # Consolidated and removed Any
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)  # Removed Body, Added status
from fastapi.security import (
    OAuth2PasswordRequestForm,
)  # Added OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, or_  # Added or_

from src.db.database import get_session
from src.models import schemas
from src.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
)  # Added verify_password, create_access_token, get_current_user
from src.models.models import User  # Used for User object, e.g. User(...)
from src.utils import get_object_or_404, get_optional_object_by_attribute

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.post("/", response_model=schemas.UserRead)
async def create_user_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    user_in: schemas.UserCreate,
) -> User:
    db_user_by_email = await get_optional_object_by_attribute(
        session, User, "email", user_in.email
    )
    if db_user_by_email:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists.",
        )

    db_user_by_username = await get_optional_object_by_attribute(
        session, User, "username", user_in.username
    )
    if db_user_by_username:
        raise HTTPException(
            status_code=400,
            detail="User with this username already exists.",
        )

    # Logic from crud_user.create_user
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password,
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


@router.get("/search", response_model=List[schemas.UserRead])
async def search_users_endpoint(
    *,
    query: str,  # Search query for username or email
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),  # Ensure user is authenticated
) -> List[User]:
    """
    Search for users by username or email.
    Returns a list of users matching the query.
    Accessible to any authenticated user.
    """
    if not query or len(query) < 2:  # Add minimum query length
        return []  # Return empty list if query is empty or too short

    statement = (
        select(User)
        .where(or_(User.username.ilike(f"%{query}%"), User.email.ilike(f"%{query}%")))
        .limit(20)  # Limit results
    )

    result = await session.exec(statement)
    users = list(result)
    return users


@router.get("/me", response_model=schemas.UserRead)
async def read_current_user_me_endpoint(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current logged-in user.
    """
    return current_user


@router.get("/{user_id}", response_model=schemas.UserRead)
async def read_user_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    user_id: int,
    current_user: User = Depends(get_current_user),
) -> User:
    db_user = await get_object_or_404(session, User, user_id)
    return db_user


@router.put("/{user_id}", response_model=schemas.UserRead)
async def update_user_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    user_id: int,
    user_in: schemas.UserUpdate,
    current_user: User = Depends(get_current_user),
) -> User:
    db_user = await get_object_or_404(
        session, User, user_id
    )  # This is the user to be updated

    # Authorization check: User can only update their own account
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user account",
        )

    user_data = user_in.model_dump(exclude_unset=True)

    # Check for email conflict
    if "email" in user_data and user_data["email"] != db_user.email:
        existing_user_email = await get_optional_object_by_attribute(
            session, User, "email", user_data["email"]
        )
        if existing_user_email and existing_user_email.id != user_id:
            raise HTTPException(
                status_code=400, detail="Email already registered by another user."
            )

    # Check for username conflict
    if "username" in user_data and user_data["username"] != db_user.username:
        existing_user_username = await get_optional_object_by_attribute(
            session, User, "username", user_data["username"]
        )
        if existing_user_username and existing_user_username.id != user_id:
            raise HTTPException(status_code=400, detail="Username already taken.")

    # Handle password update separately
    if "password" in user_data:
        if user_data["password"]:
            db_user.hashed_password = get_password_hash(user_data["password"])
        del user_data["password"]  # Remove password from dict to prevent direct setattr

    # Update other fields
    for key, value in user_data.items():
        setattr(db_user, key, value)

    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


@router.delete("/{user_id}", response_model=int)
async def delete_user_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    user_id: int,
    current_user: User = Depends(get_current_user),
) -> int:
    db_user = await get_object_or_404(
        session, User, user_id
    )  # This is the user to be deleted

    # User can only delete their own account
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user account",
        )

    await session.delete(db_user)
    await session.commit()
    return user_id


@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    # Authenticate user (fetch user by username and verify password)
    statement = select(User).where(User.username == form_data.username)
    result = await session.exec(statement)
    user = result.first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id}  # Add user_id to token payload
    )
    return {"access_token": access_token, "token_type": "bearer"}

