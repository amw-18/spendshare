from typing import List, Optional
from sqlmodel.ext.asyncio.session import AsyncSession # Use AsyncSession
from sqlmodel import select # select is still used the same way

# Import password hashing utilities from the new core.security module
from app.core.security import get_password_hash, verify_password
from app.models.models import User
from app.models.schemas import UserCreate, UserUpdate

# pwd_context and its helper functions (get_password_hash, verify_password)
# are synchronous and CPU-bound, so they don't need to be async.
# They will be moved to a core.security module later as planned.
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") # Removed

# def get_password_hash(password: str) -> str: # Removed
#     return pwd_context.hash(password)

# def verify_password(plain_password: str, hashed_password: str) -> bool: # Removed
#     return pwd_context.verify(plain_password, hashed_password)

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
    # session.get() is an async-compatible method for PK lookups
    return await session.get(User, user_id)

async def get_user_by_email(session: AsyncSession, *, email: str) -> Optional[User]:
    statement = select(User).where(User.email == email)
    result = await session.exec(statement)
    return result.first()

async def get_user_by_username(session: AsyncSession, *, username: str) -> Optional[User]:
    statement = select(User).where(User.username == username)
    result = await session.exec(statement)
    return result.first()

async def get_users(session: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    statement = select(User).offset(skip).limit(limit)
    result = await session.exec(statement)
    return result.all()

async def update_user(session: AsyncSession, *, db_user: User, user_in: UserUpdate) -> User:
    user_data = user_in.model_dump(exclude_unset=True)
    if "password" in user_data and user_data["password"]:
        hashed_password = get_password_hash(user_data["password"])
        user_data["password"] = hashed_password
    
    for key, value in user_data.items():
        setattr(db_user, key, value)
    
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user

async def delete_user(session: AsyncSession, *, db_user: User) -> User:
    await session.delete(db_user) # session.delete is async when using AsyncSession
    await session.commit()
    # The object is expired after commit, so accessing attributes might raise an error
    # or return stale data unless refreshed. For delete, returning it is less common.
    # Consider returning None or a status, or refresh if needed (but it's deleted).
    return db_user # Or simply return
