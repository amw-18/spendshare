from typing import List, Optional
from sqlmodel.ext.asyncio.session import AsyncSession # Use AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload # Added
from fastapi import HTTPException # Added for add_member_to_group

from app.models import models # For models.Group, models.UserGroupLink etc.
from app.models.schemas import GroupCreate, GroupUpdate # Schemas remain the same

async def create_group(session: AsyncSession, group_in: GroupCreate) -> models.Group: # Signature updated
    # For Pydantic v2/SQLModel 0.0.14+
    db_group = models.Group.model_validate(group_in)

    session.add(db_group)
    await session.commit()
    await session.refresh(db_group)

    # Add creator as the first member
    if db_group.created_by_user_id:
        creator_as_member_link = models.UserGroupLink(user_id=db_group.created_by_user_id, group_id=db_group.id)
        session.add(creator_as_member_link)
        await session.commit()
        await session.refresh(db_group) # Refresh to load the new member relationship

    return db_group

async def get_group(session: AsyncSession, group_id: int) -> Optional[models.Group]:
    return await session.get(models.Group, group_id)

async def get_group_with_members(session: AsyncSession, group_id: int) -> Optional[models.Group]:
    statement = select(models.Group).where(models.Group.id == group_id).options(selectinload(models.Group.members))
    result = await session.exec(statement)
    return result.first()

async def get_groups(session: AsyncSession, skip: int = 0, limit: int = 100) -> List[models.Group]:
    statement = select(models.Group).offset(skip).limit(limit)
    results = await session.exec(statement)
    return results.all()

async def get_groups_created_by_user(session: AsyncSession, user_id: int) -> List[models.Group]:
    statement = select(models.Group).where(models.Group.created_by_user_id == user_id)
    result = await session.exec(statement)
    return result.all()

async def get_groups_for_member(session: AsyncSession, user_id: int) -> List[models.Group]:
    statement = select(models.Group).join(models.UserGroupLink).where(models.UserGroupLink.user_id == user_id)
    result = await session.exec(statement)
    return result.unique().all() # .unique() if joins produce duplicates

# get_groups_for_user is renamed to get_groups_for_member, or it's a different function.
# The prompt asks for get_groups_for_member, which is similar to the existing get_groups_for_user.
# I will keep get_groups_for_member as defined above and assume get_groups_for_user is no longer needed or is different.
# For safety, I will keep the old get_groups_for_user if it's substantially different.
# On review, get_groups_for_member is identical to the old get_groups_for_user, so I'll let the replacement handle it.

async def update_group(session: AsyncSession, *, db_group: models.Group, group_in: GroupUpdate) -> models.Group:
    group_data = group_in.model_dump(exclude_unset=True)
    for key, value in group_data.items():
        setattr(db_group, key, value)
    session.add(db_group)
    await session.commit()
    await session.refresh(db_group)
    return db_group

async def delete_group(session: AsyncSession, *, db_group: models.Group) -> models.Group:
    # Manual deletion of links example (if cascade is not set up):
    # statement_links = select(models.UserGroupLink).where(models.UserGroupLink.group_id == db_group.id)
    # links_to_delete_results = await session.exec(statement_links)
    # links_to_delete = links_to_delete_results.all()
    # for link in links_to_delete:
    #     await session.delete(link)
    # await session.commit() # Commit link deletions

    await session.delete(db_group)
    await session.commit()
    return db_group # Object is expired

async def add_member_to_group(session: AsyncSession, group_id: int, user_id: int) -> Optional[models.Group]:
    group = await session.get(models.Group, group_id)
    if not group:
        # As per instructions, router will handle None or CRUD can raise HTTPException
        # For now, let's stick to the prompt's version of add_member_to_group which raises HTTPException
        raise HTTPException(status_code=404, detail="Group not found")
    user = await session.get(models.User, user_id) # Assuming models.User is correct
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if user is already a member
    existing_link_result = await session.exec(
        select(models.UserGroupLink).where(
            models.UserGroupLink.user_id == user_id,
            models.UserGroupLink.group_id == group_id
        )
    )
    if existing_link_result.first():
        raise HTTPException(status_code=400, detail="User is already a member of this group.")

    user_group_link = models.UserGroupLink(user_id=user_id, group_id=group_id)
    session.add(user_group_link)
    await session.commit()
    await session.refresh(group) # Refresh to update group.members if accessed later
    return group

async def remove_member_from_group(session: AsyncSession, *, group_id: int, user_id: int) -> Optional[models.Group]:
    db_group = await session.get(models.Group, group_id)
    user_to_remove = await session.get(models.User, user_id) # Assuming models.User is correct

    if not db_group or not user_to_remove:
        return None

    statement = select(models.UserGroupLink).where(
        models.UserGroupLink.group_id == group_id, models.UserGroupLink.user_id == user_id
    )
    link_to_delete_result = await session.exec(statement)
    link_to_delete = link_to_delete_result.first()

    if link_to_delete:
        await session.delete(link_to_delete)
        await session.commit()
        await session.refresh(db_group) 
        
    return db_group
