"""
Authentication API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.auth import LoginRequest, TokenResponse, TokenRefreshRequest, AccessTokenResponse, ActivateAccountRequest
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService
from app.core.exceptions import AuthenticationError, ConflictError
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        UserResponse: Created user

    Raises:
        HTTPException: If username or email already exists
    """
    try:
        user = AuthService.create_user(db, user_data)
        return user
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )


@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Login and get access token

    Args:
        login_data: Login credentials
        db: Database session

    Returns:
        TokenResponse: Access and refresh tokens

    Raises:
        HTTPException: If authentication fails
    """
    try:
        tokens = AuthService.login(db, login_data.username, login_data.password)
        return tokens
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh_token(refresh_data: TokenRefreshRequest):
    """
    Refresh access token using refresh token

    Args:
        refresh_data: Refresh token

    Returns:
        AccessTokenResponse: New access token

    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        access_token = AuthService.refresh_access_token(refresh_data.refresh_token)
        return AccessTokenResponse(access_token=access_token, token_type="bearer")
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/activate", response_model=TokenResponse)
def activate_account(
    activation_data: ActivateAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Activate user account by setting new password.

    Used by mobile app when user logs in for the first time with temporary password.
    After activation, user can login with the new password.

    Args:
        activation_data: New password data
        current_user: Current authenticated user (must be first login)
        db: Database session

    Returns:
        TokenResponse: New tokens with updated user info

    Raises:
        HTTPException: If account already activated or activation fails
    """
    try:
        tokens = AuthService.activate_account(
            db=db,
            user_id=current_user.id,
            new_password=activation_data.new_password
        )
        return tokens
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information

    Args:
        current_user: Current authenticated user

    Returns:
        UserResponse: Current user data
    """
    return current_user


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """
    Logout (placeholder - actual token blacklisting would be implemented with Redis)

    Args:
        current_user: Current authenticated user

    Returns:
        dict: Success message
    """
    # In a production system, you would add the token to a blacklist in Redis
    return {"message": "Successfully logged out"}
