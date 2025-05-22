from typing import List, Optional
from sqlmodel import Session, select

from app.models.models import Group, User, UserGroupLink
from app.models.schemas import GroupCreate, GroupUpdate

def create_group(session: Session, *, group_in: GroupCreate, creator_id: int) -> Group:
    # Ensure the creator_id is part of the group_in or passed correctly
    # The GroupCreate schema already has created_by_user_id
    db_group = Group.model_validate(group_in) # Pydantic v2
    # db_group = Group.from_orm(group_in) # Pydantic v1
    # db_group.created_by_user_id = creator_id # This is already in GroupCreate
    
    session.add(db_group)
    session.commit()
    session.refresh(db_group)
    
    # Automatically add the creator as a member of the group
    add_member_to_group(session=session, group_id=db_group.id, user_id=creator_id)
    session.refresh(db_group) # Refresh to load the new member if relationships are configured to do so
    
    return db_group

def get_group(session: Session, group_id: int) -> Optional[Group]:
    return session.get(Group, group_id)

def get_groups(session: Session, skip: int = 0, limit: int = 100) -> List[Group]:
    statement = select(Group).offset(skip).limit(limit)
    return session.exec(statement).all()

def get_groups_for_user(session: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Group]:
    statement = (
        select(Group)
        .join(UserGroupLink, UserGroupLink.group_id == Group.id)
        .where(UserGroupLink.user_id == user_id)
        .offset(skip)
        .limit(limit)
    )
    return session.exec(statement).all()

def update_group(session: Session, *, db_group: Group, group_in: GroupUpdate) -> Group:
    group_data = group_in.model_dump(exclude_unset=True)
    for key, value in group_data.items():
        setattr(db_group, key, value)
    session.add(db_group)
    session.commit()
    session.refresh(db_group)
    return db_group

def delete_group(session: Session, *, db_group: Group) -> Group:
    # Handle related UserGroupLink entries before deleting the group
    # This can be done by configuring cascade deletes in SQLAlchemy/SQLModel relationships,
    # or by manually deleting them here. For now, we assume cascade or manual deletion elsewhere.
    # If not handled, this might raise a foreign key constraint error.
    
    # Example of manual deletion of links (if cascade is not set up):
    # statement = select(UserGroupLink).where(UserGroupLink.group_id == db_group.id)
    # links_to_delete = session.exec(statement).all()
    # for link in links_to_delete:
    #     session.delete(link)
    # session.commit() # Commit link deletions before deleting group

    session.delete(db_group)
    session.commit()
    return db_group

def add_member_to_group(session: Session, *, group_id: int, user_id: int) -> Optional[Group]:
    db_group = session.get(Group, group_id)
    user_to_add = session.get(User, user_id)

    if not db_group or not user_to_add:
        return None # Or raise an error

    # Check if user is already a member
    link_exists = session.exec(
        select(UserGroupLink).where(UserGroupLink.group_id == group_id, UserGroupLink.user_id == user_id)
    ).first()

    if not link_exists:
        # Create the link
        user_group_link = UserGroupLink(user_id=user_id, group_id=group_id)
        session.add(user_group_link)
        session.commit()
        session.refresh(db_group) # Refresh group to see updated members list
    
    return db_group
    

def remove_member_from_group(session: Session, *, group_id: int, user_id: int) -> Optional[Group]:
    db_group = session.get(Group, group_id)
    user_to_remove = session.get(User, user_id)

    if not db_group or not user_to_remove:
        return None # Or raise an error

    statement = select(UserGroupLink).where(
        UserGroupLink.group_id == group_id, UserGroupLink.user_id == user_id
    )
    link_to_delete = session.exec(statement).first()

    if link_to_delete:
        session.delete(link_to_delete)
        session.commit()
        session.refresh(db_group) # Refresh group
        
    return db_group
