from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel.ext.asyncio.session import AsyncSession # Import AsyncSession

from app.db.database import get_session # Async get_session
from app.crud import crud_group, crud_user # Async crud_group and crud_user
from app.models import models
from app.models import schemas

router = APIRouter(
    prefix="/groups",
    tags=["groups"],
)

@router.post("/", response_model=schemas.GroupRead)
async def create_group_endpoint( # async def
    *,
    session: AsyncSession = Depends(get_session), # AsyncSession
    group_in: schemas.GroupCreate
    # current_user: models.User = Depends(get_current_active_user) # Placeholder
) -> models.Group:
    creator = await crud_user.get_user(session, group_in.created_by_user_id) # await
    if not creator:
        raise HTTPException(status_code=404, detail="Creator user not found.")
    
    group = await crud_group.create_group(session=session, group_in=group_in, creator_id=group_in.created_by_user_id) # await
    return group

@router.get("/", response_model=List[schemas.GroupRead])
async def read_groups_endpoint( # async def
    *,
    session: AsyncSession = Depends(get_session),
    skip: int = 0,
    limit: int = 100
) -> List[models.Group]:
    groups = await crud_group.get_groups(session=session, skip=skip, limit=limit) # await
    return groups

@router.get("/{group_id}", response_model=schemas.GroupRead) # Consider GroupReadWithMembers later
async def read_group_endpoint( # async def
    *,
    session: AsyncSession = Depends(get_session),
    group_id: int
) -> models.Group:
    db_group = await crud_group.get_group(session=session, group_id=group_id) # await
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    return db_group

@router.put("/{group_id}", response_model=schemas.GroupRead)
async def update_group_endpoint( # async def
    *,
    session: AsyncSession = Depends(get_session),
    group_id: int,
    group_in: schemas.GroupUpdate
    # current_user: models.User = Depends(get_current_active_user) # Placeholder
) -> models.Group:
    db_group = await crud_group.get_group(session=session, group_id=group_id) # await
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    # Add authorization checks here if needed
    group = await crud_group.update_group(session=session, db_group=db_group, group_in=group_in) # await
    return group

@router.delete("/{group_id}", response_model=schemas.GroupRead)
async def delete_group_endpoint( # async def
    *,
    session: AsyncSession = Depends(get_session),
    group_id: int
    # current_user: models.User = Depends(get_current_active_user) # Placeholder
) -> models.Group:
    db_group = await crud_group.get_group(session=session, group_id=group_id) # await
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    # Add authorization checks here
    group = await crud_group.delete_group(session=session, db_group=db_group) # await
    return group

# Group Member Management
@router.post("/{group_id}/members/{user_id}", response_model=schemas.GroupRead) # Consider GroupReadWithMembers
async def add_group_member_endpoint( # async def
    *,
    session: AsyncSession = Depends(get_session),
    group_id: int,
    user_id: int
    # current_user: models.User = Depends(get_current_active_user) # Placeholder
) -> models.Group:
    # crud_group.add_member_to_group already fetches group and user
    # No need to fetch them again here unless for specific checks before calling the crud function.
    # db_group_check = await crud_group.get_group(session=session, group_id=group_id)
    # if not db_group_check:
    #     raise HTTPException(status_code=404, detail="Group not found")
    # user_to_add_check = await crud_user.get_user(session=session, user_id=user_id)
    # if not user_to_add_check:
    #     raise HTTPException(status_code=404, detail="User to add not found")

    updated_group = await crud_group.add_member_to_group(session=session, group_id=group_id, user_id=user_id) # await
    if updated_group is None:
        # This condition implies either the group or user was not found by the CRUD function.
        # Or the user was already a member and the CRUD func decided to return None (though current returns group).
        # Better to rely on CRUD to find group/user and raise from there or return consistently.
        # For now, assume crud_group.add_member_to_group returns the group or None if group/user not found.
        raise HTTPException(status_code=404, detail="Group or User not found, or member could not be added.")
    return updated_group

@router.delete("/{group_id}/members/{user_id}", response_model=schemas.GroupRead) # Consider GroupReadWithMembers
async def remove_group_member_endpoint( # async def
    *,
    session: AsyncSession = Depends(get_session),
    group_id: int,
    user_id: int
    # current_user: models.User = Depends(get_current_active_user) # Placeholder
) -> models.Group:
    # Similar to add_member, crud_group.remove_member_from_group handles fetching.
    # db_group_check = await crud_group.get_group(session=session, group_id=group_id)
    # if not db_group_check:
    #     raise HTTPException(status_code=404, detail="Group not found")
    # user_to_remove_check = await crud_user.get_user(session=session, user_id=user_id)
    # if not user_to_remove_check:
    #     raise HTTPException(status_code=404, detail="User to remove not found")

    updated_group = await crud_group.remove_member_from_group(session=session, group_id=group_id, user_id=user_id) # await
    if updated_group is None:
        # This implies group or user not found by the CRUD function.
        raise HTTPException(status_code=404, detail="Group or User not found, or member could not be removed.")
    return updated_group
