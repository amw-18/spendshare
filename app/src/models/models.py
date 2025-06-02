from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    UniqueConstraint,
)


class UserGroupLink(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    user_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True
        ),
    )
    group_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("group.id", ondelete="CASCADE"), primary_key=True
        ),
    )


class ExpenseParticipant(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("user_id", "expense_id", name="uq_user_expense_participation"),
        {"extend_existing": True},
    )
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(
        sa_column=Column(Integer, ForeignKey("user.id", ondelete="CASCADE")),
    )
    expense_id: int = Field(
        sa_column=Column(Integer, ForeignKey("expense.id", ondelete="CASCADE")),
    )
    share_amount: float
    settled_transaction_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("transaction.id", ondelete="SET NULL")),
    )
    settled_amount_in_transaction_currency: Optional[float] = Field(default=None)

    # Relationship to Transaction (optional, as not all participations are settled via a direct transaction record)
    transaction: Optional["Transaction"] = Relationship(
        back_populates="settled_expense_participations"
    )

    # Relationship to User
    user: "User" = Relationship(back_populates="participant_records")
    # Relationship to Expense
    expense: "Expense" = Relationship(back_populates="all_participant_details")


class User(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str

    groups: List["Group"] = Relationship(
        back_populates="members",
        link_model=UserGroupLink,
        sa_relationship_kwargs={"cascade": "save-update, merge"},
    )
    expenses_paid: List["Expense"] = Relationship(
        back_populates="paid_by",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    expenses_participated_in: List["Expense"] = Relationship(
        back_populates="participants",
        link_model=ExpenseParticipant,
        sa_relationship_kwargs={"cascade": "all, delete", "overlaps": "user,expense"},
    )
    groups_created: List["Group"] = Relationship(
        back_populates="created_by",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    transactions_created: List["Transaction"] = Relationship(
        back_populates="created_by",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}, # if user is deleted, their transactions are deleted
    )

    # Link to the actual ExpenseParticipant entries for this user
    participant_records: List["ExpenseParticipant"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "overlaps": "expenses_participated_in"}
    )


class Group(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    created_by_user_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False
        )
    )
    description: Optional[str]

    created_by: "User" = Relationship(back_populates="groups_created")
    members: List["User"] = Relationship(
        back_populates="groups",
        link_model=UserGroupLink,
        sa_relationship_kwargs={"cascade": "save-update, merge"},
    )
    expenses: List["Expense"] = Relationship(
        back_populates="group", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class Expense(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    description: str
    amount: float
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_settled: bool = Field(default=False)

    paid_by_user_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False
        )
    )
    paid_by: "User" = Relationship(back_populates="expenses_paid")

    group_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            Integer, ForeignKey("group.id", ondelete="CASCADE"), nullable=True
        ),
    )
    group: Optional["Group"] = Relationship(back_populates="expenses")

    currency_id: int = Field(foreign_key="currency.id")
    currency: Optional["Currency"] = Relationship(back_populates="expenses")

    participants: List["User"] = Relationship(
        back_populates="expenses_participated_in",
        link_model=ExpenseParticipant,
        sa_relationship_kwargs={"cascade": "all, delete", "overlaps": "expense,participant_records,user"},
    )

    # Relationship to the ExpenseParticipant link table records for this expense
    all_participant_details: List["ExpenseParticipant"] = Relationship(
        back_populates="expense",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "overlaps": "expenses_participated_in,participants"}
    )


class Currency(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True)
    name: str = Field(index=True)
    symbol: Optional[str] = Field(default=None)
    expenses: List["Expense"] = Relationship(back_populates="currency")
    conversion_rates_from: List["ConversionRate"] = Relationship(
        back_populates="from_currency",
        sa_relationship_kwargs={"foreign_keys": "[ConversionRate.from_currency_id]"},
    )
    conversion_rates_to: List["ConversionRate"] = Relationship(
        back_populates="to_currency",
        sa_relationship_kwargs={"foreign_keys": "[ConversionRate.to_currency_id]"},
    )
    transactions: List["Transaction"] = Relationship(back_populates="currency")


class ConversionRate(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "from_currency_id",
            "to_currency_id",
            "timestamp",
            name="uq_conversion_rate_from_to_timestamp",
        ),
        {"extend_existing": True},
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    from_currency_id: int = Field(
        sa_column=Column(Integer, ForeignKey("currency.id", ondelete="CASCADE"))
    )
    to_currency_id: int = Field(
        sa_column=Column(Integer, ForeignKey("currency.id", ondelete="CASCADE"))
    )
    rate: float = Field(gt=0)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )

    from_currency: Optional["Currency"] = Relationship(
        back_populates="conversion_rates_from",
        sa_relationship_kwargs={"foreign_keys": "[ConversionRate.from_currency_id]"},
    )
    to_currency: Optional["Currency"] = Relationship(
        back_populates="conversion_rates_to",
        sa_relationship_kwargs={"foreign_keys": "[ConversionRate.to_currency_id]"},
    )


class Transaction(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    amount: float
    currency_id: int = Field(
        sa_column=Column(Integer, ForeignKey("currency.id", ondelete="CASCADE"))
    ) # If currency is deleted, cascade delete transactions
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
    description: Optional[str] = Field(default=None)
    created_by_user_id: int = Field(
        sa_column=Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    ) # If user is deleted, cascade delete transactions

    currency: "Currency" = Relationship(back_populates="transactions")
    created_by: "User" = Relationship(back_populates="transactions_created")

    settled_expense_participations: List["ExpenseParticipant"] = Relationship(
        back_populates="transaction",
        sa_relationship_kwargs={
            "cascade": "save-update, merge", # Keep participations if transaction is deleted, just nullify the link
        },
    )
