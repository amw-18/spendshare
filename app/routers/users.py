from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.database import get_session
from app.crud import crud_user
from app.models import models
from app.models import schemas

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
    db_user_by_email = await crud_user.get_user_by_email(session, email=user_in.email)
    if db_user_by_email:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists.",
        )
    db_user_by_username = await crud_user.get_user_by_username(
        session, username=user_in.username
    )
    if db_user_by_username:
        raise HTTPException(
            status_code=400,
            detail="User with this username already exists.",
        )
    user = await crud_user.create_user(session=session, user_in=user_in)
    return user


@router.get("/", response_model=List[schemas.UserRead])
async def read_users_endpoint(
    *,  # Added for consistency, if skip/limit are to be query params, they should be after session
    session: AsyncSession = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
) -> List[models.User]:
    users = await crud_user.get_users(session=session, skip=skip, limit=limit)  # await
    return users


@router.get("/{user_id}", response_model=schemas.UserRead)
async def read_user_endpoint(
    *, session: AsyncSession = Depends(get_session), user_id: int
) -> models.User:
    db_user = await crud_user.get_user(session=session, user_id=user_id)  # await
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.put("/{user_id}", response_model=schemas.UserRead)
async def update_user_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    user_id: int,
    user_in: schemas.UserUpdate,
) -> models.User:
    db_user = await crud_user.get_user(session=session, user_id=user_id)  # await
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_in.email:
        existing_user_email = await crud_user.get_user_by_email(
            session, email=user_in.email
        )  # await
        if existing_user_email and existing_user_email.id != user_id:
            raise HTTPException(
                status_code=400, detail="Email already registered by another user."
            )
    if user_in.username:
        existing_user_username = await crud_user.get_user_by_username(
            session, username=user_in.username
        )  # await
        if existing_user_username and existing_user_username.id != user_id:
            raise HTTPException(status_code=400, detail="Username already taken.")

    user = await crud_user.update_user(
        session=session, db_user=db_user, user_in=user_in
    )
    return user


@router.delete("/{user_id}", response_model=int)
async def delete_user_endpoint(
    *, session: AsyncSession = Depends(get_session), user_id: int
) -> int:
    db_user = await crud_user.get_user(session=session, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    await crud_user.delete_user(session=session, db_user=db_user)  # await
    return user_id
