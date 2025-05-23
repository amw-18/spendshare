from typing import List, Optional # Consolidated and removed Any
from fastapi import APIRouter, Depends, HTTPException # Removed Body
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.db.database import get_session
from app.models import models # Used as models.User in type hints
from app.models import schemas
from app.core.security import get_password_hash
from app.models.models import User # Used for User object, e.g. User(...)
from app.utils import get_object_or_404, get_optional_object_by_attribute

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
    db_user_by_email = await get_optional_object_by_attribute(session, User, "email", user_in.email)
    if db_user_by_email:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists.",
        )

    db_user_by_username = await get_optional_object_by_attribute(session, User, "username", user_in.username)
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
) -> List[models.User]:
    # Logic from crud_user.get_users
    statement = select(User).offset(skip).limit(limit)
    result = await session.exec(statement)
    users = list(result)
    return users


@router.get("/{user_id}", response_model=schemas.UserRead)
async def read_user_endpoint(
    *, session: AsyncSession = Depends(get_session), user_id: int
) -> models.User:
    db_user = await get_object_or_404(session, User, user_id)
    return db_user


@router.put("/{user_id}", response_model=schemas.UserRead)
async def update_user_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    user_id: int,
    user_in: schemas.UserUpdate,
) -> models.User:
    db_user = await get_object_or_404(session, User, user_id)

    if user_in.email:
        existing_user_email = await get_optional_object_by_attribute(session, User, "email", user_in.email)
        if existing_user_email and existing_user_email.id != user_id:
            raise HTTPException(
                status_code=400, detail="Email already registered by another user."
            )
    if user_in.username:
        existing_user_username = await get_optional_object_by_attribute(session, User, "username", user_in.username)
        if existing_user_username and existing_user_username.id != user_id:
            raise HTTPException(status_code=400, detail="Username already taken.")

    # Logic from crud_user.update_user
    user_data = user_in.model_dump(exclude_unset=True)
    if user_data.get("password"):
        hashed_password = get_password_hash(user_data["password"])
        user_data["password"] = hashed_password # Corrected: use user_data["password"] instead of user_data["hashed_password"]

    for key, value in user_data.items():
        setattr(db_user, key, value)

    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


@router.delete("/{user_id}", response_model=int)
async def delete_user_endpoint(
    *, session: AsyncSession = Depends(get_session), user_id: int
) -> int:
    db_user = await get_object_or_404(session, User, user_id)
    await session.delete(db_user)
    await session.commit()
    return user_id
