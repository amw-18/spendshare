from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import or_, select

from src.db.database import get_session
from src.models.models import (
    Group,
    User,
    UserGroupLink,
    Expense,
    ExpenseParticipant,
)
from src.models import schemas
from src.core.security import get_current_user
from src.utils import get_object_or_404

router = APIRouter(
    prefix="/groups",
    tags=["groups"],
)


@router.post("/", response_model=schemas.GroupRead)
async def create_group_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    group_in: schemas.GroupCreate,
    current_user: User = Depends(get_current_user),
) -> Group:
    db_group = Group(
        name=group_in.name,
        description=group_in.description,
        created_by_user_id=current_user.id,  # Use current_user.id
    )
    session.add(db_group)
    await session.commit()
    await session.refresh(db_group)

    # Automatically add the creator as a member
    if db_group.id is not None:  # current_user.id will always be not None
        creator_as_member_link = UserGroupLink(
            user_id=current_user.id,
            group_id=db_group.id,
        )
        session.add(creator_as_member_link)
        await session.commit()
        await session.refresh(db_group)

    return db_group


@router.get("/", response_model=List[schemas.GroupRead])
async def read_groups_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> List[Group]:
    statement = (
        select(Group)
        .where(Group.created_by_user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    result = await session.exec(statement)
    groups = list(result)
    return groups


@router.get("/{group_id}", response_model=schemas.GroupRead)
async def read_group_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    group_id: int,
    current_user: User = Depends(get_current_user),
) -> Group:
    db_group = await get_object_or_404(session, Group, group_id)

    if db_group.created_by_user_id != current_user.id:
        # Check if current_user is a member of the group
        link_exists_statement = select(UserGroupLink).where(
            UserGroupLink.group_id == group_id, UserGroupLink.user_id == current_user.id
        )
        result = await session.exec(link_exists_statement)
        if not result.first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this group",
            )
    return db_group


@router.put("/{group_id}", response_model=schemas.GroupRead)
async def update_group_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    group_id: int,
    group_in: schemas.GroupUpdate,
    current_user: User = Depends(get_current_user),
) -> Group:
    db_group = await get_object_or_404(session, Group, group_id)

    if db_group.created_by_user_id != current_user.id:
        # Check if current_user is a member of the group
        link_exists_statement = select(UserGroupLink).where(
            UserGroupLink.group_id == group_id, UserGroupLink.user_id == current_user.id
        )
        result = await session.exec(link_exists_statement)
        if not result.first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this group",
            )

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
    current_user: User = Depends(get_current_user),
) -> int:
    db_group = await get_object_or_404(session, Group, group_id)
    if db_group.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this group",
        )

    await session.delete(db_group)
    await session.commit()

    return group_id


@router.post("/{group_id}/members/{user_id}", response_model=schemas.GroupRead)
async def add_group_member_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
) -> Group:
    db_group = await get_object_or_404(session, Group, group_id)

    # check existence of user
    await get_object_or_404(session, User, user_id)

    # Authorization: Only group creator or admin can add members
    if db_group.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add members to this group",
        )

    # Check if user is already a member
    link_exists_statement = select(UserGroupLink).where(
        UserGroupLink.group_id == group_id, UserGroupLink.user_id == user_id
    )
    result = await session.exec(link_exists_statement)
    if result.first():
        raise HTTPException(
            status_code=400, detail="User is already a member of this group."
        )

    new_link = UserGroupLink(user_id=user_id, group_id=group_id)
    session.add(new_link)
    await session.commit()
    await session.refresh(
        db_group
    )  # Refresh to get updated members list if GroupRead schema expects it

    return db_group


@router.delete("/{group_id}/members/{user_id}", response_model=schemas.GroupRead)
async def remove_group_member_endpoint(
    *,
    session: AsyncSession = Depends(get_session),
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
) -> Group:
    db_group = await get_object_or_404(session, Group, group_id)
    user_to_remove = await get_object_or_404(session, User, user_id)

    # Authorization: Only group creator (or user themselves)
    if db_group.created_by_user_id != current_user.id and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to remove this member from the group",
        )

    # Find the UserGroupLink entry to delete
    link_statement = select(UserGroupLink).where(
        UserGroupLink.group_id == group_id, UserGroupLink.user_id == user_id
    )
    result = await session.exec(link_statement)
    link_to_delete = result.first()

    if not link_to_delete:
        raise HTTPException(
            status_code=404, detail="User is not a member of this group."
        )

    # Cascade removal from expenses in this group
    # 1. Find all expenses associated with this group
    expenses_in_group_statement = select(Expense).where(Expense.group_id == group_id)
    expenses_result = await session.exec(expenses_in_group_statement)
    expenses_in_group = expenses_result.all()

    for expense_obj in expenses_in_group:
        if expense_obj.paid_by_user_id == user_id or not expense_obj.is_settled:
            raise HTTPException(status_code=400, detail="Expense is not settled")

        participant_statement = select(ExpenseParticipant).where(
            ExpenseParticipant.expense_id == expense_obj.id,
            ExpenseParticipant.user_id == user_to_remove.id,
        )
        participant_result = await session.exec(participant_statement)
        participant_to_delete = participant_result.first()
        if participant_to_delete:
            raise HTTPException(
                status_code=400, detail="Cannot delete if part of an expense"
            )

    await session.delete(link_to_delete)

    await session.commit()
    await session.refresh(db_group)

    return db_group
