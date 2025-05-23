from typing import List, Optional # Consolidated and removed Any
from fastapi import APIRouter, Depends, HTTPException # Removed Body
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.db.database import get_session
from app.models import models # Used as models.Group in type hints
from app.models.models import Group, User, UserGroupLink
from app.models import schemas
from app.utils import get_object_or_404 # Removed get_optional_object_by_attribute

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
    creator = await get_object_or_404(session, User, group_in.created_by_user_id)
    # The detail message in get_object_or_404 is generic, e.g. "User with id X not found"
    # If "Creator user not found." is specifically required, custom logic would be needed here.
    # For this refactoring, we'll accept the generic message from the utility.

    # Logic from crud_group.create_group
    db_group = Group(
        name=group_in.name,
        description=group_in.description,
        created_by_user_id=group_in.created_by_user_id,
    )
    session.add(db_group)
    await session.commit()
    await session.refresh(db_group)

    # Automatically add the creator as a member
    # Ensure db_group.id is populated after refresh
    if db_group.id is not None and db_group.created_by_user_id is not None:
        creator_as_member_link = UserGroupLink(
            user_id=db_group.created_by_user_id, group_id=db_group.id
        )
        session.add(creator_as_member_link)
        await session.commit()
        # Refresh the group again to ensure the members list (if included in response) is updated
        await session.refresh(db_group) 
    
    return db_group


@router.get("/", response_model=List[schemas.GroupRead])
async def read_groups_endpoint(
    *, session: AsyncSession = Depends(get_session), skip: int = 0, limit: int = 100
) -> List[models.Group]:
    # Logic from crud_group.get_groups
    statement = select(Group).offset(skip).limit(limit)
    result = await session.exec(statement)
    groups = list(result)
    return groups


@router.get("/{group_id}", response_model=schemas.GroupRead)
async def read_group_endpoint(
    *, session: AsyncSession = Depends(get_session), group_id: int
) -> models.Group:
    db_group = await get_object_or_404(session, Group, group_id)
    return db_group


@router.put("/{group_id}", response_model=schemas.GroupRead)
async def update_group_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    group_id: int,
    group_in: schemas.GroupUpdate,
) -> models.Group:
    db_group = await get_object_or_404(session, Group, group_id)

    # Logic from crud_group.update_group
    group_data = group_in.model_dump(exclude_unset=True)
    for key, value in group_data.items():
        setattr(db_group, key, value)
    
    session.add(db_group)
    await session.commit()
    await session.refresh(db_group)
    return db_group


@router.delete("/{group_id}", response_model=int)
async def delete_group_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    group_id: int,
) -> int:
    db_group = await get_object_or_404(session, Group, group_id)

    # Logic from crud_group.delete_group
    # Need to ensure related UserGroupLink entries are handled if necessary,
    # or rely on DB cascade if configured. For now, direct delete.
    # Also, consider expenses related to the group. The current models don't show cascade delete for group on expenses.
    # This might be an issue to flag, but for now, just delete the group.
    await session.delete(db_group)
    await session.commit()
    return group_id


# Group Member Management
@router.post("/{group_id}/members/{user_id}", response_model=schemas.GroupRead)
async def add_group_member_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    group_id: int,
    user_id: int,
) -> models.Group:
    db_group = await get_object_or_404(session, Group, group_id)
    user_to_add = await get_object_or_404(session, User, user_id)
    # Custom message for user_to_add can be handled by catching HTTPException from get_object_or_404
    # and re-raising if needed, or by accepting generic message.

    # Check if user is already a member using get_optional_object_by_attribute for UserGroupLink
    # This requires a composite key, so direct usage of get_optional_object_by_attribute is not straightforward.
    # The existing select statement is more appropriate for composite keys.
    link_exists_statement = select(UserGroupLink).where(
        UserGroupLink.group_id == group_id, UserGroupLink.user_id == user_id
    )
    result = await session.exec(link_exists_statement)
    if result.first():
        raise HTTPException(status_code=400, detail="User is already a member of this group.")

    # Add member
    # The Relationship on Group.members uses UserGroupLink.
    # Appending to db_group.members should ideally trigger SQLModel to create UserGroupLink.
    # Alternatively, create UserGroupLink directly. Let's try with direct UserGroupLink for clarity.
    
    # Check current members to avoid duplicate add if relying on db_group.members.append()
    # This is inefficient if group has many members. The link_exists_statement above is better.
    # for member in db_group.members: # This would trigger a load of all members
    #    if member.id == user_id:
    #        raise HTTPException(status_code=400, detail="User is already a member of this group.")
            
    new_link = UserGroupLink(user_id=user_id, group_id=group_id)
    session.add(new_link)
    # db_group.members.append(user_to_add) # This should also work if relationships are set up correctly
    # session.add(db_group) # Mark group as changed if append is used
    
    await session.commit()
    await session.refresh(db_group) # Refresh to get updated members list if GroupRead schema expects it
    
    # To return the group with members, we might need options for selectinload
    # For now, refresh and return. The GroupRead schema will determine what's serialized.
    # If GroupRead includes members, SQLModel will lazy/auto load them after refresh.
    return db_group


@router.delete("/{group_id}/members/{user_id}", response_model=schemas.GroupRead)
async def remove_group_member_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    group_id: int,
    user_id: int,
) -> models.Group:
    db_group = await get_object_or_404(session, Group, group_id)
    user_to_remove = await get_object_or_404(session, User, user_id)

    # Find the UserGroupLink entry to delete
    link_statement = select(UserGroupLink).where(
        UserGroupLink.group_id == group_id, UserGroupLink.user_id == user_id
    )
    result = await session.exec(link_statement)
    link_to_delete = result.first()

    if not link_to_delete:
        raise HTTPException(status_code=404, detail="User is not a member of this group.")

    await session.delete(link_to_delete)
    # Alternatively, if using db_group.members.remove(user_to_remove), ensure it works with backrefs
    # session.add(db_group) # Mark group as changed if remove is used
    
    await session.commit()
    await session.refresh(db_group) # Refresh to get updated members list

    return db_group
