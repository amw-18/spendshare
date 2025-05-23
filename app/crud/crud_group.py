from typing import List, Optional
from sqlmodel.ext.asyncio.session import AsyncSession  # Use AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload  # Added
from fastapi import HTTPException  # Added for add_member_to_group

from app.models import models  # For models.Group, models.UserGroupLink etc.
from app.models.schemas import GroupCreate, GroupUpdate  # Schemas remain the same


async def create_group(
    session: AsyncSession, group_in: GroupCreate
) -> models.Group:  # Signature updated
    # For Pydantic v2/SQLModel 0.0.14+
    db_group = models.Group.model_validate(group_in)

    session.add(db_group)
    await session.commit()
    await session.refresh(db_group)

    # Add creator as the first member
    if db_group.created_by_user_id:
        creator_as_member_link = models.UserGroupLink(
            user_id=db_group.created_by_user_id, group_id=db_group.id
        )
        session.add(creator_as_member_link)
        await session.commit()
        await session.refresh(db_group)  # Refresh to load the new member relationship

    return db_group


async def get_group(session: AsyncSession, group_id: int) -> Optional[models.Group]:
    return await session.get(models.Group, group_id)


async def get_group_with_members(
    session: AsyncSession, group_id: int
) -> Optional[models.Group]:
    statement = (
        select(models.Group)
        .where(models.Group.id == group_id)
        .options(selectinload(models.Group.members))
    )
    result = await session.exec(statement)
    return result.first()


async def get_groups(
    session: AsyncSession, skip: int = 0, limit: int = 100
) -> List[models.Group]:
    statement = select(models.Group).offset(skip).limit(limit)
    results = await session.exec(statement)
    return list(results)


async def get_groups_created_by_user(
    session: AsyncSession, user_id: int
) -> List[models.Group]:
    statement = select(models.Group).where(models.Group.created_by_user_id == user_id)
    result = await session.exec(statement)
    return list(result)


async def get_groups_for_member(
    session: AsyncSession, user_id: int
) -> List[models.Group]:
    statement = (
        select(models.Group)
        .join(models.UserGroupLink)
        .where(models.UserGroupLink.user_id == user_id)
    )
    result = await session.exec(statement)
    return list(result)


async def update_group(
    session: AsyncSession, *, db_group: models.Group, group_in: GroupUpdate
) -> models.Group:
    group_data = group_in.model_dump(exclude_unset=True)
    for key, value in group_data.items():
        setattr(db_group, key, value)
    session.add(db_group)
    await session.commit()
    await session.refresh(db_group)
    return db_group


async def delete_group(session: AsyncSession, *, db_group: models.Group) -> None:
    await session.delete(db_group)
    await session.commit()


async def add_member_to_group(
    session: AsyncSession, group_id: int, user_id: int
) -> models.Group:
    group = await session.get(models.Group, group_id)
    if not group:
        # As per instructions, router will handle None or CRUD can raise HTTPException
        # For now, let's stick to the prompt's version of add_member_to_group which raises HTTPException
        raise HTTPException(status_code=404, detail="Group not found")
    user = await session.get(models.User, user_id)  # Assuming models.User is correct
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if user is already a member
    existing_link_result = await session.exec(
        select(models.UserGroupLink).where(
            models.UserGroupLink.user_id == user_id,
            models.UserGroupLink.group_id == group_id,
        )
    )
    if existing_link_result.first():
        raise HTTPException(
            status_code=400, detail="User is already a member of this group."
        )

    user_group_link = models.UserGroupLink(user_id=user_id, group_id=group_id)
    session.add(user_group_link)
    await session.commit()
    await session.refresh(group)  # Refresh to update group.members if accessed later
    return group


async def remove_member_from_group(
    session: AsyncSession, *, group_id: int, user_id: int
) -> models.Group:
    db_group = await session.get(models.Group, group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")

    statement = select(models.UserGroupLink).where(
        models.UserGroupLink.group_id == group_id,
        models.UserGroupLink.user_id == user_id,
    )
    link_to_delete_result = await session.exec(statement)
    link_to_delete = link_to_delete_result.first()

    if link_to_delete:
        await session.delete(link_to_delete)
        await session.commit()
        await session.refresh(db_group)

    return db_group
