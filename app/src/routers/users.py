from typing import List
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, or_

from src.db.database import get_session
from src.models import schemas
from src.models.models import User
from src.core.security import get_current_user
from src.utils import get_object_or_404

router = APIRouter(
    prefix="",
    tags=["users"],
)


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
        .where(User.email_verified == True)
        .where(or_(User.username.ilike(f"%{query}%"), User.email.ilike(f"%{query}%")))
        .limit(20)
    )
    result = await session.exec(statement)
    users = list(result)
    return users


@router.get("/me", response_model=schemas.UserRead)
async def read_current_user_me_endpoint(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


@router.get("/{user_id}", response_model=schemas.UserRead)
async def read_user_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    user_id: int,
    current_user: User = Depends(get_current_user),
) -> User:
    db_user = await get_object_or_404(session, User, user_id)
    if not db_user.email_verified:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or not verified.")
    return db_user


@router.put("/me", response_model=schemas.UserRead)
async def update_user_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    user_in: schemas.UserUpdate,
    current_user: User = Depends(get_current_user),
) -> User:
    user_data = user_in.model_dump(exclude_unset=True)

    if "username" in user_data and user_data["username"] != current_user.username:
        statement = select(User).where(User.username == user_data["username"], User.id != current_user.id)
        result = await session.exec(statement)
        existing_user_username = result.first()
        if existing_user_username:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken.")
        current_user.username = user_data["username"]

    if "full_name" in user_data:
         current_user.full_name = user_data["full_name"]

    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user