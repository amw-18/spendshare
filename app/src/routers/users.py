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
from src.models import models  # Used as models.User in type hints
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
) -> models.User:
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


@router.get("/", response_model=List[schemas.UserRead])
async def read_users_endpoint(
    *,  # Added for consistency, if skip/limit are to be query params, they should be after session
    session: AsyncSession = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
) -> List[models.User]:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to list users",
        )
    # Logic from crud_user.get_users
    statement = select(User).offset(skip).limit(limit)
    result = await session.exec(statement)
    users = list(result)
    return users


@router.get("/search", response_model=List[schemas.UserRead])
async def search_users_endpoint(
    *,
    query: str,  # Search query for username or email
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),  # Ensure user is authenticated
) -> List[models.User]:
    """
    Search for users by username or email.
    Returns a list of users matching the query.
    Accessible to any authenticated user.
    """
    if not query or len(query) < 2: # Add minimum query length
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
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """
    Get current logged-in user.
    """
    return current_user


@router.get("/{user_id}", response_model=schemas.UserRead)
async def read_user_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    user_id: int,
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    db_user = await get_object_or_404(session, User, user_id)
    return db_user


@router.put("/{user_id}", response_model=schemas.UserRead)
async def update_user_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    user_id: int,
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    db_user = await get_object_or_404(
        session, User, user_id
    )  # This is the user to be updated

    # Authorization check: Only admin or the user themselves can update
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user account",
        )

    # Authorization check: Prevent non-admins from granting admin privileges
    if (
        user_in.is_admin is not None
        and user_in.is_admin == True
        and not current_user.is_admin
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to grant admin privileges",
        )

    # Prevent users from revoking their own admin status if they are the sole admin
    # This logic is more complex and might require a global check or be handled as a separate feature.
    # For now, we assume there's a mechanism or policy outside this direct endpoint to prevent this.

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
        # Special handling for is_admin: only allow if current_user is admin, or if user is de-adminning themselves (which is fine)
        if key == "is_admin":
            if current_user.is_admin:  # Admin can set it to True or False
                setattr(db_user, key, value)
            # else: non-admin cannot change is_admin (already covered by earlier check if they try to set to True)
            # If a non-admin tries to set is_admin to False, it's a no-op if they are not admin.
            # If they are admin and set to False, it's allowed.
            # The initial check `if user_in.is_admin is not None and user_in.is_admin == True and not current_user.is_admin:`
            # already prevents non-admins from setting is_admin to True.
            # So, if we reach here, and key is "is_admin", and current_user is not admin, value must be False.
            # Setting their own (already False) is_admin to False is a no-op and fine.
            # This means we only need to ensure that if `is_admin` is in `user_data`, it's applied correctly based on permissions.
            # The current logic with `exclude_unset` and the top-level check for `is_admin == True` is mostly sufficient.
            # However, to be explicit:
            elif (
                current_user.id == user_id and value == False
            ):  # User de-adminning themselves (if they were admin)
                setattr(db_user, key, value)
            # Other cases for 'is_admin' by non-admins are effectively blocked or no-ops.
        else:
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
    current_user: models.User = Depends(get_current_user),
) -> int:
    db_user = await get_object_or_404(
        session, User, user_id
    )  # This is the user to be deleted

    if not current_user.is_admin and current_user.id != user_id:
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


@router.post("/admin/login_as/{target_user_id}", response_model=schemas.Token)
async def admin_login_as_user(
    target_user_id: int,
    current_user: models.User = Depends(
        get_current_user
    ),  # Ensures this endpoint is protected
    session: AsyncSession = Depends(get_session),
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized for this action",
        )

    target_user = await get_object_or_404(session, User, target_user_id)

    # Create access token for the target user
    # Ensure the payload matches what get_current_user expects, e.g., 'sub' for username
    # and potentially 'user_id'.
    access_token = create_access_token(
        data={"sub": target_user.username, "user_id": target_user.id}
    )
    return {"access_token": access_token, "token_type": "bearer"}
