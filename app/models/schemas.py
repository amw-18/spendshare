from typing import List, Optional
from sqlmodel import SQLModel
from datetime import datetime


# User Schemas
class UserBase(SQLModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int


class UserUpdate(SQLModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


# Group Schemas
class GroupBase(SQLModel):
    name: str
    description: Optional[str] = None


class GroupCreate(GroupBase):
    created_by_user_id: int  # Keep this simple for creation


class GroupRead(GroupBase):
    id: int
    created_by_user_id: int


class GroupUpdate(SQLModel):
    name: Optional[str] = None


# Expense Schemas
class ExpenseBase(SQLModel):
    description: str
    amount: float
    paid_by_user_id: int
    group_id: Optional[int] = None


class ExpenseCreate(ExpenseBase):
    # For creating an expense, we might want to specify participants and their shares
    # This can get complex, so for now, let's assume a simple model.
    # Advanced: participants: Optional[List[Tuple[int, Optional[float]]]] = None # List of (user_id, share_amount)
    pass


class ExpenseRead(ExpenseBase):
    id: int
    date: datetime
    participant_details: List["ExpenseParticipantReadWithUser"] = [] # Added for reading shares and user


class ExpenseUpdate(SQLModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    paid_by_user_id: Optional[int] = None
    group_id: Optional[int] = None
    participants: Optional[List["ParticipantUpdate"]] = None # Added participants field


# Schema for Participant Update
class ParticipantUpdate(SQLModel):
    user_id: int
    # share_amount: Optional[float] = None # For now, shares will be recalculated equally


# Schemas for reading participant details with shares
class ExpenseParticipantBase(SQLModel): # Base for ExpenseParticipant data
    user_id: int
    expense_id: int
    share_amount: Optional[float]

class ExpenseParticipantRead(ExpenseParticipantBase): # Reading an ExpenseParticipant link
    # No extra fields needed if ExpenseParticipantBase is sufficient
    pass

class ExpenseParticipantReadWithUser(ExpenseParticipantRead): # Reading an ExpenseParticipant link with User details
    user: UserRead


# Schemas with Relationships (for responses)


class UserReadWithDetails(UserRead):
    # groups: List["GroupRead"] = [] # Causes Pydantic ForwardRef error if GroupRead not defined or imported
    # expenses_paid: List["ExpenseRead"] = []
    # expenses_participated_in: List["ExpenseRead"] = []
    pass  # Postponing detailed relationships in schemas until CRUD and routers are built to see what's needed


class GroupReadWithMembers(GroupRead):
    # members: List["UserRead"] = []
    # expenses: List["ExpenseRead"] = []
    pass  # Postponing detailed relationships


class ExpenseReadWithDetails(ExpenseRead):
    # paid_by: "UserRead"
    # group: Optional["GroupRead"] = None
    # participants: List["UserRead"] = []
    pass  # Postponing detailed relationships


# Link Schemas (if needed for direct manipulation, often handled via parent object operations)
class UserGroupLinkCreate(SQLModel):
    user_id: int
    group_id: int


class ExpenseParticipantCreate(SQLModel):
    user_id: int
    expense_id: int
    share_amount: Optional[float] = None
