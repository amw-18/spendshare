from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session

from app.db.database import engine # Direct engine import for session, or a get_session dependency
from app.crud import crud_user
from app.models import models # To avoid conflicts, use models.User
from app.models import schemas # For schemas.UserRead, schemas.UserCreate etc.

# Dependency to get a DB session
def get_session():
    with Session(engine) as session:
        yield session

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.post("/", response_model=schemas.UserRead)
def create_user_endpoint(
    *,
    session: Session = Depends(get_session),
    user_in: schemas.UserCreate
) -> models.User:
    db_user_by_email = crud_user.get_user_by_email(session, email=user_in.email)
    if db_user_by_email:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists.",
        )
    db_user_by_username = crud_user.get_user_by_username(session, username=user_in.username)
    if db_user_by_username:
        raise HTTPException(
            status_code=400,
            detail="User with this username already exists.",
        )
    user = crud_user.create_user(session=session, user_in=user_in)
    return user

@router.get("/", response_model=List[schemas.UserRead])
def read_users_endpoint(
    session: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100
) -> List[models.User]:
    users = crud_user.get_users(session=session, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=schemas.UserRead)
def read_user_endpoint(
    *,
    session: Session = Depends(get_session),
    user_id: int
) -> models.User:
    db_user = crud_user.get_user(session=session, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=schemas.UserRead)
def update_user_endpoint(
    *,
    session: Session = Depends(get_session),
    user_id: int,
    user_in: schemas.UserUpdate
) -> models.User:
    db_user = crud_user.get_user(session=session, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check for email/username conflicts if they are being changed
    if user_in.email:
        existing_user_email = crud_user.get_user_by_email(session, email=user_in.email)
        if existing_user_email and existing_user_email.id != user_id:
            raise HTTPException(status_code=400, detail="Email already registered by another user.")
    if user_in.username:
        existing_user_username = crud_user.get_user_by_username(session, username=user_in.username)
        if existing_user_username and existing_user_username.id != user_id:
            raise HTTPException(status_code=400, detail="Username already taken.")
            
    user = crud_user.update_user(session=session, db_user=db_user, user_in=user_in)
    return user

@router.delete("/{user_id}", response_model=schemas.UserRead) # Or return a status code/message
def delete_user_endpoint(
    *,
    session: Session = Depends(get_session),
    user_id: int
) -> models.User: # Returning the deleted user, or could be a message.
    db_user = crud_user.get_user(session=session, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    # Consider implications of deleting a user (e.g., related expenses, groups)
    # This might require more complex logic or be prevented if user is involved in transactions.
    # For now, a simple delete.
    user = crud_user.delete_user(session=session, db_user=db_user)
    return user
