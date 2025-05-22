from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session

from app.db.database import engine # Or your get_session dependency function path
from app.crud import crud_group, crud_user
from app.models import models # For models.Group, models.User
from app.models import schemas # For schemas.GroupRead, schemas.GroupCreate etc.

# Dependency to get a DB session (can be shared or defined in a common place)
def get_session():
    with Session(engine) as session:
        yield session

router = APIRouter(
    prefix="/groups",
    tags=["groups"],
)

@router.post("/", response_model=schemas.GroupRead) # Consider a GroupReadWithMembers schema later
def create_group_endpoint(
    *,
    session: Session = Depends(get_session),
    group_in: schemas.GroupCreate
    # current_user: models.User = Depends(get_current_active_user) # Placeholder for auth
) -> models.Group:
    # In a real app, group_in.created_by_user_id would be set from the authenticated user.
    # For now, we trust the client to send it, or it's part of GroupCreate.
    # Let's assume GroupCreate requires created_by_user_id.
    creator = crud_user.get_user(session, group_in.created_by_user_id)
    if not creator:
        raise HTTPException(status_code=404, detail="Creator user not found.")
    
    group = crud_group.create_group(session=session, group_in=group_in, creator_id=group_in.created_by_user_id)
    return group

@router.get("/", response_model=List[schemas.GroupRead])
def read_groups_endpoint(
    session: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100
    # current_user: models.User = Depends(get_current_active_user) # To get groups for current user
) -> List[models.Group]:
    # If we want to get groups for a specific user (e.g., the current user):
    # groups = crud_group.get_groups_for_user(session=session, user_id=current_user.id, skip=skip, limit=limit)
    # For now, let's return all groups or implement a specific endpoint for user's groups
    groups = crud_group.get_groups(session=session, skip=skip, limit=limit)
    return groups

@router.get("/{group_id}", response_model=schemas.GroupRead) # Later GroupReadWithMembers
def read_group_endpoint(
    *,
    session: Session = Depends(get_session),
    group_id: int
) -> models.Group:
    db_group = crud_group.get_group(session=session, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    return db_group

@router.put("/{group_id}", response_model=schemas.GroupRead)
def update_group_endpoint(
    *,
    session: Session = Depends(get_session),
    group_id: int,
    group_in: schemas.GroupUpdate
    # current_user: models.User = Depends(get_current_active_user) # For auth
) -> models.Group:
    db_group = crud_group.get_group(session=session, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    # Add authorization: check if current_user is admin or creator of the group
    # if db_group.created_by_user_id != current_user.id:
    #     raise HTTPException(status_code=403, detail="Not authorized to update this group")
    group = crud_group.update_group(session=session, db_group=db_group, group_in=group_in)
    return group

@router.delete("/{group_id}", response_model=schemas.GroupRead) # Or a success message
def delete_group_endpoint(
    *,
    session: Session = Depends(get_session),
    group_id: int
    # current_user: models.User = Depends(get_current_active_user) # For auth
) -> models.Group:
    db_group = crud_group.get_group(session=session, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    # Add authorization check
    # if db_group.created_by_user_id != current_user.id:
    #     raise HTTPException(status_code=403, detail="Not authorized to delete this group")
    # Consider implications: what happens to expenses in this group?
    # This might require cascade deletes or preventing deletion if expenses exist.
    group = crud_group.delete_group(session=session, db_group=db_group)
    return group

# Group Member Management
@router.post("/{group_id}/members/{user_id}", response_model=schemas.GroupRead) # Later GroupReadWithMembers
def add_group_member_endpoint(
    *,
    session: Session = Depends(get_session),
    group_id: int,
    user_id: int
    # current_user: models.User = Depends(get_current_active_user) # For auth
) -> models.Group:
    db_group = crud_group.get_group(session=session, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    user_to_add = crud_user.get_user(session=session, user_id=user_id)
    if not user_to_add:
        raise HTTPException(status_code=404, detail="User to add not found")
    # Add authorization: e.g., only group creator or existing members can add
    # if db_group.created_by_user_id != current_user.id: # Simple check
    #     raise HTTPException(status_code=403, detail="Not authorized to add members to this group")
    
    updated_group = crud_group.add_member_to_group(session=session, group_id=group_id, user_id=user_id)
    if updated_group is None: # Should not happen if group and user exist
        raise HTTPException(status_code=500, detail="Failed to add member")
    return updated_group

@router.delete("/{group_id}/members/{user_id}", response_model=schemas.GroupRead) # Later GroupReadWithMembers
def remove_group_member_endpoint(
    *,
    session: Session = Depends(get_session),
    group_id: int,
    user_id: int
    # current_user: models.User = Depends(get_current_active_user) # For auth
) -> models.Group:
    db_group = crud_group.get_group(session=session, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    user_to_remove = crud_user.get_user(session=session, user_id=user_id)
    if not user_to_remove:
        raise HTTPException(status_code=404, detail="User to remove not found")
    # Add authorization: e.g., group creator or the user themselves can remove
    # Prevent creator from being removed if they are the sole member or special rules apply.
    
    updated_group = crud_group.remove_member_from_group(session=session, group_id=group_id, user_id=user_id)
    if updated_group is None: # Should not happen if group and user exist and user is a member
        # crud_group.remove_member_from_group might return None if user was not a member or group/user not found.
        # Check the logic in crud_group.remove_member_from_group. It returns the group.
        # This path implies an issue if group/user existed but operation failed.
        # However, if user was not a member, it might still return the group.
        pass # Or raise specific error if member was not found in group.

    # Need to reload the group to reflect changes if the response_model expects it
    # The crud_group.remove_member_from_group should handle session.refresh(db_group)
    return db_group # Return the group, which should be refreshed by CRUD op
