from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel.ext.asyncio.session import AsyncSession # Import AsyncSession

from app.db.database import get_session # Async get_session
from app.crud import crud_expense, crud_user, crud_group # Async CRUD modules
from app.models import models
from app.models import schemas
from app.services import expense_service # Async service module

router = APIRouter(
    prefix="/expenses",
    tags=["expenses"],
)

@router.post("/service/", response_model=schemas.ExpenseRead)
async def create_expense_with_participants_endpoint( # async def
    *,
    session: AsyncSession = Depends(get_session), # AsyncSession
    expense_in: schemas.ExpenseCreate, # Contains description, amount
    paid_by_user_id: int = Body(...),
    participant_user_ids: List[int] = Body(...),
    group_id: Optional[int] = Body(None)
) -> models.Expense:
    populated_expense_in = schemas.ExpenseCreate(
        description=expense_in.description,
        amount=expense_in.amount,
        paid_by_user_id=paid_by_user_id, # Ensure schema is populated correctly
        group_id=group_id
    )

    db_expense = await expense_service.create_expense_with_participants( # await service call
        session=session,
        expense_in=populated_expense_in,
        paid_by_user_id=paid_by_user_id,
        participant_user_ids=participant_user_ids,
        group_id=group_id
    )
    if not db_expense:
        raise HTTPException(status_code=400, detail="Failed to create expense with participants. Check user IDs or group ID.")
    return db_expense

@router.post("/", response_model=schemas.ExpenseRead)
async def create_expense_endpoint( # async def
    *,
    session: AsyncSession = Depends(get_session),
    expense_in: schemas.ExpenseCreate
) -> models.Expense:
    payer = await crud_user.get_user(session, expense_in.paid_by_user_id) # await
    if not payer:
        raise HTTPException(status_code=404, detail=f"Payer user with id {expense_in.paid_by_user_id} not found.")
    
    if expense_in.group_id:
        group = await crud_group.get_group(session, expense_in.group_id) # await
        if not group:
            raise HTTPException(status_code=404, detail=f"Group with id {expense_in.group_id} not found.")
            
    expense = await crud_expense.create_expense( # await
        session=session, 
        expense_in=expense_in, 
        paid_by_user_id=expense_in.paid_by_user_id
    )
    return expense

@router.get("/", response_model=List[schemas.ExpenseRead])
async def read_expenses_endpoint( # async def
    *,
    session: AsyncSession = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    group_id: Optional[int] = None
) -> List[models.Expense]:
    if user_id:
        expenses = await crud_expense.get_expenses_for_user( # await
            session=session, user_id=user_id, skip=skip, limit=limit
        )
    elif group_id:
        expenses = await crud_expense.get_expenses_for_group( # await
            session=session, group_id=group_id, skip=skip, limit=limit
        )
    else:
        expenses = await crud_expense.get_expenses(session=session, skip=skip, limit=limit) # await
    return expenses

@router.get("/{expense_id}", response_model=schemas.ExpenseRead)
async def read_expense_endpoint( # async def
    *,
    session: AsyncSession = Depends(get_session),
    expense_id: int
) -> models.Expense:
    db_expense = await crud_expense.get_expense(session=session, expense_id=expense_id) # await
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return db_expense

@router.put("/{expense_id}", response_model=schemas.ExpenseRead)
async def update_expense_endpoint( # async def
    *,
    session: AsyncSession = Depends(get_session),
    expense_id: int,
    expense_in: schemas.ExpenseUpdate
) -> models.Expense:
    db_expense = await crud_expense.get_expense(session=session, expense_id=expense_id) # await
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    if expense_in.paid_by_user_id is not None:
        payer = await crud_user.get_user(session, expense_in.paid_by_user_id) # await
        if not payer:
            raise HTTPException(status_code=404, detail=f"New payer user with id {expense_in.paid_by_user_id} not found.")
    
    if expense_in.group_id is not None: # Check if group_id is being updated
        if expense_in.group_id == 0: # Or some other indicator for "no group" if that's how client sends it
             pass # Allow setting group_id to null or a specific value meaning "no group"
        else:
            group = await crud_group.get_group(session, expense_in.group_id) # await
            if not group:
                 raise HTTPException(status_code=404, detail=f"New group with id {expense_in.group_id} not found.")

    expense = await crud_expense.update_expense(session=session, db_expense=db_expense, expense_in=expense_in) # await
    return expense

@router.delete("/{expense_id}", response_model=schemas.ExpenseRead)
async def delete_expense_endpoint( # async def
    *,
    session: AsyncSession = Depends(get_session),
    expense_id: int
) -> models.Expense:
    db_expense = await crud_expense.get_expense(session=session, expense_id=expense_id) # await
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    expense = await crud_expense.delete_expense(session=session, db_expense=db_expense) # await
    return expense

@router.post("/{expense_id}/participants/{user_id}", response_model=schemas.ExpenseRead)
async def add_expense_participant_endpoint( # async def
    *,
    session: AsyncSession = Depends(get_session),
    expense_id: int,
    user_id: int,
    share_amount: Optional[float] = Body(None)
):
    # crud_expense.add_participant_to_expense will fetch expense and user
    updated_expense = await crud_expense.add_participant_to_expense( # await
        session=session, expense_id=expense_id, user_id=user_id, share_amount=share_amount
    )
    if not updated_expense:
         # This implies expense or user was not found by the CRUD function
        raise HTTPException(status_code=404, detail="Expense or User not found, or participant could not be added.")
    return updated_expense

@router.delete("/{expense_id}/participants/{user_id}", response_model=schemas.ExpenseRead)
async def remove_expense_participant_endpoint( # async def
    *,
    session: AsyncSession = Depends(get_session),
    expense_id: int,
    user_id: int
):
    # crud_expense.remove_participant_from_expense will fetch expense and user
    updated_expense = await crud_expense.remove_participant_from_expense( # await
        session=session, expense_id=expense_id, user_id=user_id
    )
    if not updated_expense:
        # This implies expense or user was not found by the CRUD function
        raise HTTPException(status_code=404, detail="Expense or User not found, or participant could not be removed.")
    return updated_expense
