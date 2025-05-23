from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.database import get_session
from app.crud import crud_group, crud_user
from app.models import models
from app.models import schemas

router = APIRouter(
    prefix="/groups",
    tags=["groups"],
)


@router.post("/", response_model=schemas.GroupRead)
async def create_group_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    group_in: schemas.GroupCreate,
) -> models.Group:
    creator = await crud_user.get_user(session, group_in.created_by_user_id)
    if not creator:
        raise HTTPException(status_code=404, detail="Creator user not found.")

    group = await crud_group.create_group(session=session, group_in=group_in)
    return group


@router.get("/", response_model=List[schemas.GroupRead])
async def read_groups_endpoint(
    *, session: AsyncSession = Depends(get_session), skip: int = 0, limit: int = 100
) -> List[models.Group]:
    groups = await crud_group.get_groups(session=session, skip=skip, limit=limit)
    return groups


@router.get("/{group_id}", response_model=schemas.GroupRead)
async def read_group_endpoint(
    *, session: AsyncSession = Depends(get_session), group_id: int
) -> models.Group:
    db_group = await crud_group.get_group(session=session, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    return db_group


@router.put("/{group_id}", response_model=schemas.GroupRead)
async def update_group_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    group_id: int,
    group_in: schemas.GroupUpdate,
) -> models.Group:
    db_group = await crud_group.get_group(session=session, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    group = await crud_group.update_group(
        session=session, db_group=db_group, group_in=group_in
    )
    return group


@router.delete("/{group_id}", response_model=int)
async def delete_group_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    group_id: int,
) -> int:
    db_group = await crud_group.get_group(session=session, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    await crud_group.delete_group(session=session, db_group=db_group)
    return group_id


# Group Member Management
@router.post("/{group_id}/members/{user_id}", response_model=schemas.GroupRead)
async def add_group_member_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    group_id: int,
    user_id: int,
) -> models.Group:
    updated_group = await crud_group.add_member_to_group(
        session=session, group_id=group_id, user_id=user_id
    )
    return updated_group


@router.delete("/{group_id}/members/{user_id}", response_model=schemas.GroupRead)
async def remove_group_member_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    group_id: int,
    user_id: int,
) -> models.Group:
    updated_group = await crud_group.remove_member_from_group(
        session=session, group_id=group_id, user_id=user_id
    )
    return updated_group
