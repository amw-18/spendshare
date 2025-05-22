from typing import List, Optional, Dict # Ensure Dict is imported
from sqlmodel import Session

from app.models.models import Expense, User, Group # Import base models
from app.models.schemas import ExpenseCreate # Schemas
from app.crud import crud_expense, crud_user, crud_group # CRUD modules

def create_expense_with_participants(
    session: Session,
    *,
    expense_in: ExpenseCreate,
    paid_by_user_id: int,
    participant_user_ids: List[int], # IDs of users participating in the expense
    group_id: Optional[int] = None # Optional group context
) -> Optional[Expense]:
    """
    Create an expense and automatically add all specified participants.
    Splits are assumed to be equal among all participants including the payer,
    unless specific share logic is implemented later.
    """
    # Verify paid_by_user exists
    payer = crud_user.get_user(session, paid_by_user_id)
    if not payer:
        # Handle error: payer not found
        return None 
    
    # Verify group exists if group_id is provided
    if group_id:
        group = crud_group.get_group(session, group_id)
        if not group:
            # Handle error: group not found
            return None
        # Further validation: check if payer and participants are members of the group
        # For now, we'll skip this detailed check.

    # Verify all participant_user_ids are valid users
    all_participants_in_expense_users = [] # To store User objects
    
    # Determine the complete list of users involved in sharing the expense
    # If participant_user_ids is empty, assume only the payer is involved (pays for themself)
    users_sharing_expense_ids = set(participant_user_ids)
    if not participant_user_ids: # If list is empty, payer bears full cost or shares with no one else explicitly listed
        users_sharing_expense_ids.add(paid_by_user_id)


    for user_id in users_sharing_expense_ids:
        user = crud_user.get_user(session, user_id)
        if not user:
            # Handle error: participant not found
            return None # Or raise an exception / collect errors
        all_participants_in_expense_users.append(user)

    if not all_participants_in_expense_users:
        # Handle error: no participants found for the expense
        return None

    # Create the base expense
    # The ExpenseCreate schema expects paid_by_user_id and optionally group_id.
    # We should use the expense_in data and ensure these IDs are set.
    # It's better to pass them directly to ExpenseCreate if they are part of its definition,
    # or construct the object carefully.
    # Assuming ExpenseCreate has: description, amount, paid_by_user_id, group_id (optional)
    
    # We need to make sure that the expense_in (which is ExpenseCreate type)
    # has its paid_by_user_id and group_id fields correctly populated before creating the model.
    # The schema `ExpenseCreate` itself has `paid_by_user_id` and `group_id`.
    # So, the caller of this service function should populate them in `expense_in`.
    # Let's assume `expense_in` is already correctly populated by the router/caller.
    
    # Ensure the expense_in has the correct paid_by_user_id and group_id from the function arguments
    # This is a bit redundant if the caller is expected to set it, but good for safety.
    expense_data_for_creation = expense_in.model_copy(update={
        "paid_by_user_id": paid_by_user_id,
        "group_id": group_id
    })

    db_expense = crud_expense.create_expense(session=session, expense_in=expense_data_for_creation, paid_by_user_id=paid_by_user_id) # paid_by_user_id is also inside expense_data_for_creation
    if not db_expense:
        # Handle error: expense creation failed
        return None

    # Add participants to the expense
    num_participants = len(all_participants_in_expense_users)
    share_amount = None 
    if num_participants > 0:
        share_amount = round(db_expense.amount / num_participants, 2)

    for user_obj in all_participants_in_expense_users:
        crud_expense.add_participant_to_expense(
            session=session,
            expense_id=db_expense.id,
            user_id=user_obj.id,
            share_amount=share_amount
        )
    
    session.refresh(db_expense)
    return db_expense

def get_user_balances(session: Session, user_id: int) -> Dict[str, float]:
    # Placeholder
    return {"owed_to_user": 0.0, "user_owes": 0.0}
