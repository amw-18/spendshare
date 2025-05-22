from typing import List, Optional, Any # Ensure Any is imported
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session

from app.db.database import engine # Or your get_session dependency function path
from app.crud import crud_expense, crud_user, crud_group
from app.models import models # For models.Expense
from app.models import schemas # For schemas.ExpenseRead, schemas.ExpenseCreate etc.
from app.services import expense_service # For service layer functions

# Dependency to get a DB session
def get_session():
    with Session(engine) as session:
        yield session

router = APIRouter(
    prefix="/expenses",
    tags=["expenses"],
)

# Endpoint using the service layer to create an expense with participants
@router.post("/service/", response_model=schemas.ExpenseRead)
def create_expense_with_participants_endpoint(
    *,
    session: Session = Depends(get_session),
    expense_in: schemas.ExpenseCreate, # This will contain description, amount
    paid_by_user_id: int = Body(...),
    participant_user_ids: List[int] = Body(...), # List of user IDs who are sharing the expense
    group_id: Optional[int] = Body(None) # Optional group context
    # current_user: models.User = Depends(get_current_active_user) # For auth, ensure paid_by_user_id is current_user.id
) -> models.Expense:
    # Basic validation: ensure paid_by_user_id is in participant_user_ids or handle logic in service
    # if paid_by_user_id not in participant_user_ids:
    #     participant_user_ids.append(paid_by_user_id) # Or service handles this

    # The ExpenseCreate schema might need to be adjusted if it has paid_by_user_id and group_id,
    # as they are also passed as separate Body parameters here.
    # Let's assume ExpenseCreate only has description and amount for this endpoint,
    # and other details are passed separately.
    # Or, the service function `create_expense_with_participants` expects an ExpenseCreate object
    # that already has paid_by_user_id and group_id.
    # The current service `create_expense_with_participants` expects `expense_in` (ExpenseCreate),
    # `paid_by_user_id`, `participant_user_ids`, `group_id`.
    # It internally calls `crud_expense.create_expense` which needs `expense_in` to have the relevant fields.
    # So, we should populate `expense_in.paid_by_user_id` and `expense_in.group_id` here if not already.

    # Let's ensure the expense_in (which is of type schemas.ExpenseCreate) is correctly populated.
    # The schema ExpenseCreate has: description, amount, paid_by_user_id, group_id (optional)
    # The service function will use these.
    
    populated_expense_in = schemas.ExpenseCreate(
        description=expense_in.description,
        amount=expense_in.amount,
        paid_by_user_id=paid_by_user_id,
        group_id=group_id
    )

    db_expense = expense_service.create_expense_with_participants(
        session=session,
        expense_in=populated_expense_in, # Pass the schema object
        paid_by_user_id=paid_by_user_id, # Also passed separately to service
        participant_user_ids=participant_user_ids,
        group_id=group_id # Also passed separately to service
    )
    if not db_expense:
        # Errors should be more specific based on service layer's feedback if possible
        raise HTTPException(status_code=400, detail="Failed to create expense with participants. Check user IDs or group ID.")
    return db_expense

@router.post("/", response_model=schemas.ExpenseRead)
def create_expense_endpoint(
    *,
    session: Session = Depends(get_session),
    expense_in: schemas.ExpenseCreate
    # current_user: models.User = Depends(get_current_active_user) # For auth
) -> models.Expense:
    # Ensure paid_by_user_id is valid
    payer = crud_user.get_user(session, expense_in.paid_by_user_id)
    if not payer:
        raise HTTPException(status_code=404, detail=f"Payer user with id {expense_in.paid_by_user_id} not found.")
    
    # Ensure group_id is valid if provided
    if expense_in.group_id:
        group = crud_group.get_group(session, expense_in.group_id)
        if not group:
            raise HTTPException(status_code=404, detail=f"Group with id {expense_in.group_id} not found.")
            
    # This is a simpler creation, does not handle participants directly.
    # Participants would be added via another endpoint or by the more complex service endpoint.
    expense = crud_expense.create_expense(session=session, expense_in=expense_in, paid_by_user_id=expense_in.paid_by_user_id)
    return expense

@router.get("/", response_model=List[schemas.ExpenseRead])
def read_expenses_endpoint(
    session: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None, # Filter by user who paid or participated
    group_id: Optional[int] = None  # Filter by group
) -> List[models.Expense]:
    if user_id:
        # TODO: Enhance crud_expense.get_expenses_for_user to include participation
        expenses = crud_expense.get_expenses_for_user(session=session, user_id=user_id, skip=skip, limit=limit)
    elif group_id:
        expenses = crud_expense.get_expenses_for_group(session=session, group_id=group_id, skip=skip, limit=limit)
    else:
        expenses = crud_expense.get_expenses(session=session, skip=skip, limit=limit)
    return expenses

@router.get("/{expense_id}", response_model=schemas.ExpenseRead) # Later ExpenseReadWithDetails
def read_expense_endpoint(
    *,
    session: Session = Depends(get_session),
    expense_id: int
) -> models.Expense:
    db_expense = crud_expense.get_expense(session=session, expense_id=expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return db_expense

@router.put("/{expense_id}", response_model=schemas.ExpenseRead)
def update_expense_endpoint(
    *,
    session: Session = Depends(get_session),
    expense_id: int,
    expense_in: schemas.ExpenseUpdate
    # current_user: models.User = Depends(get_current_active_user) # For auth
) -> models.Expense:
    db_expense = crud_expense.get_expense(session=session, expense_id=expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    # Add authorization: e.g., only payer or group admin can update
    # if db_expense.paid_by_user_id != current_user.id:
    #     raise HTTPException(status_code=403, detail="Not authorized to update this expense")
    
    # Validate paid_by_user_id if it's being changed
    if expense_in.paid_by_user_id is not None:
        payer = crud_user.get_user(session, expense_in.paid_by_user_id)
        if not payer:
            raise HTTPException(status_code=404, detail=f"New payer user with id {expense_in.paid_by_user_id} not found.")
    
    # Validate group_id if it's being changed
    if expense_in.group_id is not None:
        group = crud_group.get_group(session, expense_in.group_id)
        if not group:
             raise HTTPException(status_code=404, detail=f"New group with id {expense_in.group_id} not found.")

    expense = crud_expense.update_expense(session=session, db_expense=db_expense, expense_in=expense_in)
    return expense

@router.delete("/{expense_id}", response_model=schemas.ExpenseRead) # Or a success message
def delete_expense_endpoint(
    *,
    session: Session = Depends(get_session),
    expense_id: int
    # current_user: models.User = Depends(get_current_active_user) # For auth
) -> models.Expense:
    db_expense = crud_expense.get_expense(session=session, expense_id=expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    # Add authorization check
    # if db_expense.paid_by_user_id != current_user.id: # Simplistic check
    #     raise HTTPException(status_code=403, detail="Not authorized to delete this expense")
    
    # Consider implications: deleting an expense should also delete related ExpenseParticipant entries.
    # This should ideally be handled by cascade deletes in the DB model relationship.
    expense = crud_expense.delete_expense(session=session, db_expense=db_expense)
    return expense

# Endpoints for managing expense participants (could be part of main expense or separate)
# These are just examples; the service layer endpoint is more comprehensive for creation.
@router.post("/{expense_id}/participants/{user_id}", response_model=schemas.ExpenseRead) # Consider specific response
def add_expense_participant_endpoint(
    *,
    session: Session = Depends(get_session),
    expense_id: int,
    user_id: int,
    share_amount: Optional[float] = Body(None) # Optional custom share
    # current_user: models.User = Depends(get_current_active_user) # For auth
):
    db_expense = crud_expense.get_expense(session=session, expense_id=expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    user_to_add = crud_user.get_user(session=session, user_id=user_id)
    if not user_to_add:
        raise HTTPException(status_code=404, detail="User to add not found")
    # Auth check: e.g., payer or group admin can add participants
    
    updated_expense = crud_expense.add_participant_to_expense(
        session=session, expense_id=expense_id, user_id=user_id, share_amount=share_amount
    )
    if not updated_expense: # Should not happen if expense and user exist
        raise HTTPException(status_code=500, detail="Failed to add participant")
    return updated_expense

@router.delete("/{expense_id}/participants/{user_id}", response_model=schemas.ExpenseRead)
def remove_expense_participant_endpoint(
    *,
    session: Session = Depends(get_session),
    expense_id: int,
    user_id: int
    # current_user: models.User = Depends(get_current_active_user) # For auth
):
    db_expense = crud_expense.get_expense(session=session, expense_id=expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    user_to_remove = crud_user.get_user(session=session, user_id=user_id)
    if not user_to_remove:
        raise HTTPException(status_code=404, detail="User to remove not found")
    # Auth check

    updated_expense = crud_expense.remove_participant_from_expense(
        session=session, expense_id=expense_id, user_id=user_id
    )
    if not updated_expense: # Should not happen if expense and user exist and user is a participant
        # This implies an issue if operation failed unexpectedly.
        # crud_expense.remove_participant_from_expense returns the expense.
        # If participant was not found, it still returns the expense (refreshed).
        pass # Or raise specific error
    return db_expense # Return the refreshed expense
