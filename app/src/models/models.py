from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime, timezone
from sqlalchemy import Column, ForeignKey, Integer


class UserGroupLink(SQLModel, table=True):
    user_id: int = Field(default=None, sa_column=Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True))
    group_id: int = Field(default=None, sa_column=Column(Integer, ForeignKey("group.id", ondelete="CASCADE"), primary_key=True))


class ExpenseParticipant(SQLModel, table=True):
    user_id: int = Field(default=None, sa_column=Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True))
    expense_id: int = Field(default=None, sa_column=Column(Integer, ForeignKey("expense.id", ondelete="CASCADE"), primary_key=True))
    share_amount: Optional[float] = Field(default=None)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_admin: bool = Field(default=False, nullable=False)

    groups: List["Group"] = Relationship(
        back_populates="members",
        link_model=UserGroupLink,
        sa_relationship_kwargs={"cascade": "save-update, merge"}
    )
    expenses_paid: List["Expense"] = Relationship(
        back_populates="paid_by",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    expenses_participated_in: List["Expense"] = Relationship(
        back_populates="participants",
        link_model=ExpenseParticipant,
        sa_relationship_kwargs={"cascade": "all, delete"}
    )
    groups_created: List["Group"] = Relationship(
        back_populates="created_by",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class Group(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    created_by_user_id: int = Field(sa_column=Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False))
    description: Optional[str]

    created_by: "User" = Relationship(back_populates="groups_created")
    members: List["User"] = Relationship(
        back_populates="groups",
        link_model=UserGroupLink,
        sa_relationship_kwargs={"cascade": "save-update, merge"}
    )
    expenses: List["Expense"] = Relationship(
        back_populates="group",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class Expense(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    description: str
    amount: float
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    paid_by_user_id: int = Field(sa_column=Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False))
    paid_by: "User" = Relationship(back_populates="expenses_paid")

    group_id: Optional[int] = Field(default=None, sa_column=Column(Integer, ForeignKey("group.id", ondelete="CASCADE"), nullable=True))
    group: Optional["Group"] = Relationship(back_populates="expenses")

    participants: List["User"] = Relationship(
        back_populates="expenses_participated_in",
        link_model=ExpenseParticipant,
        sa_relationship_kwargs={"cascade": "all, delete"}
    )


# Update forward references now that all models are defined
# This might not be strictly necessary with SQLModel if types are strings,
# but it's good practice for linters and type checkers.
# However, SQLModel handles string forward references automatically.