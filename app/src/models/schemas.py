from typing import List, Optional
from sqlmodel import SQLModel
from datetime import datetime
from pydantic import BaseModel, constr, EmailStr, Field, field_validator


# Token Schema
class Token(BaseModel):
    access_token: str
    token_type: str


# User Schemas
class UserBase(SQLModel):
    username: constr(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    email: EmailStr

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if len(v) > 50:
            raise ValueError("username must be at most 50 characters")
        if len(v) < 3:
            raise ValueError("username must be at least 3 characters")
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                "username must only contain letters, numbers, hyphens, and underscores"
            )
        return v


class UserCreate(UserBase):
    password: constr(min_length=8)

    @field_validator("password")
    @classmethod
    def password_must_contain_number(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        if not any(char.isdigit() for char in v):
            raise ValueError("password must contain at least one number")
        if not any(char.isalpha() for char in v):
            raise ValueError("password must contain at least one letter")
        return v


class UserRead(UserBase):
    id: int


class UserUpdate(SQLModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[constr(min_length=8)] = None

    @field_validator("password")
    @classmethod
    def password_must_contain_number_if_provided(
        cls, v: Optional[str]
    ) -> Optional[str]:
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        if not any(char.isdigit() for char in v):
            raise ValueError("password must contain at least one number")
        if not any(char.isalpha() for char in v):
            raise ValueError("password must contain at least one letter")
        return v

    @field_validator("username")
    @classmethod
    def validate_username_if_provided(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if len(v) > 50:
            raise ValueError("username must be at most 50 characters")
        if len(v) < 3:
            raise ValueError("username must be at least 3 characters")
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                "username must only contain letters, numbers, hyphens, and underscores"
            )
        return v


# Group Schemas
class GroupBase(SQLModel):
    name: constr(min_length=1, max_length=100)
    description: Optional[str] = None


class GroupCreate(GroupBase):
    pass


class GroupRead(GroupBase):
    id: int
    created_by_user_id: int


class GroupUpdate(SQLModel):
    name: Optional[str] = None


# Expense Schemas
class ExpenseBase(SQLModel):
    description: constr(min_length=1)
    amount: float = Field(gt=0)
    currency_id: int  # Added currency_id
    group_id: Optional[int] = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseRead(ExpenseBase):
    id: int
    date: datetime
    paid_by_user_id: Optional[int] = None
    paid_by_user: Optional[UserRead] = None
    currency: Optional["CurrencyRead"] = None  # Added currency
    description: str = Field(default="")
    participant_details: List["ExpenseParticipantReadWithUser"] = []


class ExpenseUpdate(SQLModel):
    description: Optional[constr(min_length=1)] = None
    amount: Optional[float] = Field(default=None, gt=0)
    paid_by_user_id: Optional[int] = None
    group_id: Optional[int] = None
    currency_id: Optional[int] = None  # Added currency_id
    participants: Optional[List["ParticipantUpdate"]] = None


class ParticipantUpdate(SQLModel):
    user_id: int
    share_amount: Optional[float] = None


# Schemas for reading participant details with shares
class ExpenseParticipantBase(SQLModel):
    id: int  # Added id field
    user_id: int
    expense_id: int
    share_amount: Optional[float]


class ExpenseParticipantRead(ExpenseParticipantBase):
    pass


class ExpenseParticipantReadWithUser(ExpenseParticipantRead):
    user: UserRead
    settled_transaction_id: Optional[int] = None
    settled_amount_in_transaction_currency: Optional[float] = None
    settled_currency_id: Optional[int] = (
        None  # Currency ID of the transaction used for settlement
    )
    settled_currency: Optional["CurrencyRead"] = (
        None  # Currency object of the transaction, use forward reference
    )


# Schemas with Relationships (for responses)


class UserReadWithDetails(UserRead):
    pass


class GroupReadWithMembers(GroupRead):
    pass


class ExpenseReadWithDetails(ExpenseRead):
    pass


# Link Schemas (if needed for direct manipulation, often handled via parent object operations)
class UserGroupLinkCreate(SQLModel):
    user_id: int
    group_id: int


class ExpenseParticipantCreate(SQLModel):
    user_id: int
    expense_id: int
    share_amount: Optional[float] = None


# Currency Schemas
class CurrencyBase(SQLModel):
    code: constr(min_length=3, max_length=3)
    name: str
    symbol: Optional[str] = None

    @field_validator("code")
    @classmethod
    def validate_code_format(cls, v: str) -> str:
        if not v.isupper():
            raise ValueError("Currency code must be uppercase")
        if len(v) != 3:
            raise ValueError("Currency code must be 3 characters long")
        return v


class CurrencyCreate(CurrencyBase):
    pass


class CurrencyRead(CurrencyBase):
    id: int


class CurrencyUpdate(SQLModel):
    code: Optional[constr(min_length=3, max_length=3)] = None
    name: Optional[str] = None
    symbol: Optional[str] = None

    @field_validator("code")
    @classmethod
    def validate_code_format_if_provided(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v.isupper():
            raise ValueError("Currency code must be uppercase")
        if len(v) != 3:
            raise ValueError("Currency code must be 3 characters long")
        return v


# User Balance Schemas
class CurrencyBalance(SQLModel):
    currency: CurrencyRead
    total_paid: float = 0.0
    net_owed_to_user: float = 0.0
    net_user_owes: float = 0.0


class UserBalanceResponse(SQLModel):
    balances: List[CurrencyBalance]


# ConversionRate Schemas
class ConversionRateBase(SQLModel):
    from_currency_id: int
    to_currency_id: int
    rate: float = Field(gt=0)


class ConversionRateCreate(ConversionRateBase):
    pass


class ConversionRateRead(ConversionRateBase):
    id: int
    timestamp: datetime
    from_currency: Optional[CurrencyRead] = None
    to_currency: Optional[CurrencyRead] = None


# Transaction Schemas
class TransactionBase(SQLModel):
    amount: float = Field(gt=0)
    currency_id: int
    description: Optional[str] = None


class TransactionCreate(TransactionBase):
    pass


class TransactionRead(TransactionBase):
    id: int
    timestamp: datetime
    created_by_user_id: int
    currency: Optional[CurrencyRead] = None


# Settlement Schemas
class ExpenseParticipantSettlementInfo(SQLModel):
    expense_participant_id: (
        int  # This refers to the primary key of the ExpenseParticipant table link.
    )
    settled_amount: float = Field(
        gt=0
    )  # Amount settled in the currency of the transaction
    settled_currency_id: int  # Currency ID of the transaction, for validation


class SettleExpensesRequest(SQLModel):
    transaction_id: int
    settlements: List[ExpenseParticipantSettlementInfo]

    @field_validator("settlements")
    @classmethod
    def settlements_must_not_be_empty(
        cls, v: List[ExpenseParticipantSettlementInfo]
    ) -> List[ExpenseParticipantSettlementInfo]:
        if not v:
            raise ValueError("Settlements list cannot be empty.")
        return v


class SettlementResultItem(SQLModel):
    expense_participant_id: int  # The ID of the ExpenseParticipant link record
    settled_transaction_id: int
    settled_amount_in_transaction_currency: float
    settled_currency_id: int  # This is the currency_id of the transaction
    message: Optional[str] = None


class SettlementResponse(SQLModel):
    status: str
    message: Optional[str] = None
    updated_expense_participations: List[SettlementResultItem]
