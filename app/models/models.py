from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime

class UserGroupLink(SQLModel, table=True):
    user_id: int = Field(default=None, primary_key=True, foreign_key="user.id")
    group_id: int = Field(default=None, primary_key=True, foreign_key="group.id")

class ExpenseParticipant(SQLModel, table=True):
    user_id: int = Field(default=None, primary_key=True, foreign_key="user.id")
    expense_id: int = Field(default=None, primary_key=True, foreign_key="expense.id")
    share_amount: Optional[float] = Field(default=None) # Optional: if not equal split

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str

    groups: List["Group"] = Relationship(back_populates="members", link_model=UserGroupLink)
    expenses_paid: List["Expense"] = Relationship(back_populates="paid_by")
    expenses_participated_in: List["Expense"] = Relationship(back_populates="participants", link_model=ExpenseParticipant)

class Group(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    created_by_user_id: int = Field(foreign_key="user.id")

    created_by: User = Relationship() # Will be User, but need to define User first or use string
    members: List[User] = Relationship(back_populates="groups", link_model=UserGroupLink)
    expenses: List["Expense"] = Relationship(back_populates="group")

class Expense(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    description: str
    amount: float
    date: datetime = Field(default_factory=datetime.utcnow)

    paid_by_user_id: int = Field(foreign_key="user.id")
    paid_by: User = Relationship(back_populates="expenses_paid")

    group_id: Optional[int] = Field(default=None, foreign_key="group.id")
    group: Optional[Group] = Relationship(back_populates="expenses")

    participants: List[User] = Relationship(back_populates="expenses_participated_in", link_model=ExpenseParticipant)

# Update forward references now that all models are defined
# This might not be strictly necessary with SQLModel if types are strings,
# but it's good practice for linters and type checkers.
# However, SQLModel handles string forward references automatically.
