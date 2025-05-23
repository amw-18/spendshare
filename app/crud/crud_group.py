from typing import List, Optional
from sqlmodel.ext.asyncio.session import AsyncSession # Use AsyncSession
from sqlmodel import select

from app.models.models import Group, User, UserGroupLink # Ensure User is imported
from app.models.schemas import GroupCreate, GroupUpdate # Schemas remain the same

async def create_group(session: AsyncSession, *, group_in: GroupCreate, creator_id: int) -> Group:
    db_group = Group.model_validate(group_in) # Pydantic v2
    # db_group.created_by_user_id = creator_id # Already in GroupCreate schema

    session.add(db_group)
    await session.commit()
    await session.refresh(db_group)
    
    # Automatically add the creator as a member of the group
    # Make sure add_member_to_group is also async and awaited
    await add_member_to_group(session=session, group_id=db_group.id, user_id=creator_id)
    # The previous add_member_to_group call would commit its own session if it were separate.
    # If it uses the same session, ensure commits are handled logically.
    # The add_member_to_group below also commits, which is fine.
    await session.refresh(db_group) # Refresh to load the new member
    
    return db_group

async def get_group(session: AsyncSession, group_id: int) -> Optional[Group]:
    return await session.get(Group, group_id)

async def get_groups(session: AsyncSession, skip: int = 0, limit: int = 100) -> List[Group]:
    statement = select(Group).offset(skip).limit(limit)
    results = await session.exec(statement)
    return results.all()

async def get_groups_for_user(session: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> List[Group]:
    statement = (
        select(Group)
        .join(UserGroupLink, UserGroupLink.group_id == Group.id)
        .where(UserGroupLink.user_id == user_id)
        .offset(skip)
        .limit(limit)
    )
    results = await session.exec(statement)
    return results.all()

async def update_group(session: AsyncSession, *, db_group: Group, group_in: GroupUpdate) -> Group:
    group_data = group_in.model_dump(exclude_unset=True)
    for key, value in group_data.items():
        setattr(db_group, key, value)
    session.add(db_group)
    await session.commit()
    await session.refresh(db_group)
    return db_group

async def delete_group(session: AsyncSession, *, db_group: Group) -> Group:
    # Manual deletion of links example (if cascade is not set up):
    # statement_links = select(UserGroupLink).where(UserGroupLink.group_id == db_group.id)
    # links_to_delete_results = await session.exec(statement_links)
    # links_to_delete = links_to_delete_results.all()
    # for link in links_to_delete:
    #     await session.delete(link)
    # await session.commit() # Commit link deletions

    await session.delete(db_group)
    await session.commit()
    return db_group # Object is expired

async def add_member_to_group(session: AsyncSession, *, group_id: int, user_id: int) -> Optional[Group]:
    # Note: This function fetches the group and user. In a high-concurrency scenario,
    # consider if these fetches are always necessary or if IDs suffice for link table.
    db_group = await session.get(Group, group_id)
    user_to_add = await session.get(User, user_id) # Assuming User model is imported

    if not db_group or not user_to_add:
        return None 

    # Check if user is already a member
    link_exists_statement = select(UserGroupLink).where(
        UserGroupLink.group_id == group_id, UserGroupLink.user_id == user_id
    )
    link_exists_result = await session.exec(link_exists_statement)
    
    if not link_exists_result.first():
        user_group_link = UserGroupLink(user_id=user_id, group_id=group_id)
        session.add(user_group_link)
        await session.commit()
        await session.refresh(db_group) # Refresh group to see updated members list
    
    return db_group
    
async def remove_member_from_group(session: AsyncSession, *, group_id: int, user_id: int) -> Optional[Group]:
    db_group = await session.get(Group, group_id)
    user_to_remove = await session.get(User, user_id) # Assuming User model is imported

    if not db_group or not user_to_remove:
        return None

    statement = select(UserGroupLink).where(
        UserGroupLink.group_id == group_id, UserGroupLink.user_id == user_id
    )
    link_to_delete_result = await session.exec(statement)
    link_to_delete = link_to_delete_result.first()

    if link_to_delete:
        await session.delete(link_to_delete)
        await session.commit()
        await session.refresh(db_group) 
        
    return db_group
