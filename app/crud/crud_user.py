from typing import List, Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.core.security import get_password_hash
from app.models.models import User
from app.models.schemas import UserCreate, UserUpdate


async def create_user(session: AsyncSession, *, user_in: UserCreate) -> User:
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


async def get_user(session: AsyncSession, user_id: int) -> Optional[User]:
    return await session.get(User, user_id)


async def get_user_by_email(session: AsyncSession, *, email: str) -> Optional[User]:
    statement = select(User).where(User.email == email)
    result = await session.exec(statement)
    return result.first()


async def get_user_by_username(
    session: AsyncSession, *, username: str
) -> Optional[User]:
    statement = select(User).where(User.username == username)
    result = await session.exec(statement)
    return result.first()


async def get_users(
    session: AsyncSession, skip: int = 0, limit: int = 100
) -> List[User]:
    statement = select(User).offset(skip).limit(limit)
    result = await session.exec(statement)
    return list(result)


async def update_user(
    session: AsyncSession, *, db_user: User, user_in: UserUpdate
) -> User:
    user_data = user_in.model_dump(exclude_unset=True)
    if user_data.get("password"):
        hashed_password = get_password_hash(user_data["password"])
        user_data["password"] = hashed_password

    for key, value in user_data.items():
        setattr(db_user, key, value)

    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def delete_user(session: AsyncSession, *, db_user: User) -> None:
    await session.delete(db_user)
    await session.commit()
