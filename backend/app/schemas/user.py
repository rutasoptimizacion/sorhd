"""
User Pydantic Schemas
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime

from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema"""

    username: str = Field(..., min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)
    role: UserRole = UserRole.CLINICAL_TEAM


class UserCreate(UserBase):
    """Schema for creating a user"""

    password: str = Field(..., min_length=6, max_length=100)
    is_active: bool = True


class UserUpdate(BaseModel):
    """Schema for updating a user"""

    username: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, min_length=6, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response"""

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserResponse):
    """User schema with password hash (for internal use)"""

    password_hash: str

    model_config = ConfigDict(from_attributes=True)
