"""
Authentication Pydantic Schemas
"""
from pydantic import BaseModel, Field
from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """Schema for login request"""

    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    """Schema for token response"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenRefreshRequest(BaseModel):
    """Schema for token refresh request"""

    refresh_token: str


class AccessTokenResponse(BaseModel):
    """Schema for access token response"""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for token payload"""

    sub: int  # User ID
    role: str
    exp: int  # Expiration timestamp
    type: str  # "access" or "refresh"


class ActivateAccountRequest(BaseModel):
    """Schema for account activation request"""

    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")
