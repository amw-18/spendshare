from typing import List, Optional
from sqlmodel import Session, select
from passlib.context import CryptContext # For password hashing

from app.models.models import User
from app.models.schemas import UserCreate, UserUpdate

# Initialize a password context (using bcrypt as the scheme)
# This should ideally be in a core.security module, but for now, place it here.
# We will move it in step 9: "Add Utility for Password Hashing (`app/core/security.py`)"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_user(session: Session, *, user_in: UserCreate) -> User:
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password,
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

def get_user(session: Session, user_id: int) -> Optional[User]:
    return session.get(User, user_id)

def get_user_by_email(session: Session, *, email: str) -> Optional[User]:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()

def get_user_by_username(session: Session, *, username: str) -> Optional[User]:
    statement = select(User).where(User.username == username)
    return session.exec(statement).first()

def get_users(session: Session, skip: int = 0, limit: int = 100) -> List[User]:
    statement = select(User).offset(skip).limit(limit)
    return session.exec(statement).all()

def update_user(session: Session, *, db_user: User, user_in: UserUpdate) -> User:
    user_data = user_in.model_dump(exclude_unset=True) # Pydantic v2
    # user_data = user_in.dict(exclude_unset=True) # Pydantic v1
    if "password" in user_data and user_data["password"]:
        hashed_password = get_password_hash(user_data["password"])
        user_data["password"] = hashed_password
    
    for key, value in user_data.items():
        setattr(db_user, key, value)
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

def delete_user(session: Session, *, db_user: User) -> User:
    session.delete(db_user)
    session.commit()
    # After deletion, the db_user object might become unusable or its state unpredictable
    # depending on the ORM's behavior, especially if it had relationships.
    # It's often safer to return a confirmation or the ID, rather than the instance.
    # However, for now, we return the object as it was before flushing the delete.
    return db_user
