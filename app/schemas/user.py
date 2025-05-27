from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr
    roll_number: str = Field(..., description="Unique roll number for the user")
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    role: str = "student"


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    email: Optional[EmailStr] = None
    roll_number: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None  # Optional: to change password
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class User(UserBase):
    id: int

    class Config:
        from_attributes = True


class UserInDB(User):
    hashed_password: str
