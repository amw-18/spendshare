from typing import List, Optional, Tuple # Ensure Tuple is imported
from sqlmodel import Session, select

from app.models.models import Expense, User, Group, ExpenseParticipant
from app.models.schemas import ExpenseCreate, ExpenseUpdate # Add other necessary schemas if they are directly used

def create_expense(session: Session, *, expense_in: ExpenseCreate, paid_by_user_id: int) -> Expense:
    # The ExpenseCreate schema already includes paid_by_user_id.
    # We might add more complex logic here later for participants.
    db_expense = Expense.model_validate(expense_in)
    # db_expense.paid_by_user_id = paid_by_user_id # This is already in ExpenseCreate

    session.add(db_expense)
    session.commit()
    session.refresh(db_expense)
    return db_expense

def get_expense(session: Session, expense_id: int) -> Optional[Expense]:
    return session.get(Expense, expense_id)

def get_expenses(session: Session, skip: int = 0, limit: int = 100) -> List[Expense]:
    statement = select(Expense).offset(skip).limit(limit)
    return session.exec(statement).all()

def get_expenses_for_user(session: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Expense]:
    # Expenses where the user is the payer OR a participant
    # This query can be complex. For now, let's get expenses paid by the user.
    # We can expand this later to include participation.
    statement = (
        select(Expense)
        .where(Expense.paid_by_user_id == user_id)
        # If we want to include expenses where the user is a participant:
        # .join(ExpenseParticipant, ExpenseParticipant.expense_id == Expense.id, isouter=True)
        # .where(or_(Expense.paid_by_user_id == user_id, ExpenseParticipant.user_id == user_id))
        # .distinct()
        .offset(skip)
        .limit(limit)
    )
    return session.exec(statement).all()

def get_expenses_for_group(session: Session, group_id: int, skip: int = 0, limit: int = 100) -> List[Expense]:
    statement = (
        select(Expense)
        .where(Expense.group_id == group_id)
        .offset(skip)
        .limit(limit)
    )
    return session.exec(statement).all()

def update_expense(session: Session, *, db_expense: Expense, expense_in: ExpenseUpdate) -> Expense:
    expense_data = expense_in.model_dump(exclude_unset=True)
    for key, value in expense_data.items():
        setattr(db_expense, key, value)
    session.add(db_expense)
    session.commit()
    session.refresh(db_expense)
    return db_expense

def delete_expense(session: Session, *, db_expense: Expense) -> Expense:
    # Similar to groups, consider cascade deletes for ExpenseParticipant
    # or handle manually here.
    session.delete(db_expense)
    session.commit()
    return db_expense

# Functions for managing expense participants (simplified for now)
def add_participant_to_expense(
    session: Session, *, expense_id: int, user_id: int, share_amount: Optional[float] = None
) -> Optional[Expense]:
    db_expense = session.get(Expense, expense_id)
    user_to_add = session.get(User, user_id)

    if not db_expense or not user_to_add:
        return None # Or raise error

    link_exists = session.exec(
        select(ExpenseParticipant).where(ExpenseParticipant.expense_id == expense_id, ExpenseParticipant.user_id == user_id)
    ).first()

    if not link_exists:
        participant_link = ExpenseParticipant(
            expense_id=expense_id, user_id=user_id, share_amount=share_amount
        )
        session.add(participant_link)
        session.commit()
        session.refresh(db_expense) # Refresh to load new participant
    return db_expense

def remove_participant_from_expense(session: Session, *, expense_id: int, user_id: int) -> Optional[Expense]:
    db_expense = session.get(Expense, expense_id)
    user_to_remove = session.get(User, user_id)

    if not db_expense or not user_to_remove:
        return None # Or raise error

    statement = select(ExpenseParticipant).where(
        ExpenseParticipant.expense_id == expense_id, ExpenseParticipant.user_id == user_id
    )
    link_to_delete = session.exec(statement).first()

    if link_to_delete:
        session.delete(link_to_delete)
        session.commit()
        session.refresh(db_expense) # Refresh expense
    return db_expense

# Placeholder for more complex expense logic
def calculate_expense_splits(session: Session, expense_id: int):
    # This function would:
    # 1. Get the expense and its participants.
    # 2. If no specific shares, divide equally.
    # 3. Update share_amount for each participant in ExpenseParticipant table.
    # For now, this is a placeholder.
    pass
