"""
Authentication Service
"""
from sqlalchemy.orm import Session
from typing import Optional

from app.models.user import User
from app.schemas.user import UserCreate
from app.schemas.auth import TokenResponse
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from app.core.exceptions import AuthenticationError, ConflictError


class AuthService:
    """Authentication service"""

    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """
        Create a new user

        Args:
            db: Database session
            user_data: User creation data

        Returns:
            User: Created user

        Raises:
            ConflictError: If username or email already exists
        """
        # Check if username already exists
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise ConflictError(f"Username '{user_data.username}' already exists")

        # Check if email already exists
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise ConflictError(f"Email '{user_data.email}' already registered")

        # Create user
        hashed_pw = hash_password(user_data.password)
        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_pw,
            role=user_data.role,
            full_name=user_data.full_name,
            is_active=1,  # Active by default
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user

        Args:
            db: Database session
            username: Username
            password: Plain text password

        Returns:
            Optional[User]: User if authentication successful, None otherwise
        """
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        return user

    @staticmethod
    def login(db: Session, username: str, password: str) -> TokenResponse:
        """
        Log in a user and generate tokens

        Args:
            db: Database session
            username: Username
            password: Plain text password

        Returns:
            TokenResponse: Access and refresh tokens

        Raises:
            AuthenticationError: If authentication fails
        """
        user = AuthService.authenticate_user(db, username, password)
        if not user:
            raise AuthenticationError("Incorrect username or password")

        # Create tokens
        token_data = {"sub": str(user.id), "role": user.role.value}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        # Import here to avoid circular dependency
        from app.schemas.user import UserResponse

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )

    @staticmethod
    def refresh_access_token(refresh_token: str) -> str:
        """
        Generate a new access token from a refresh token

        Args:
            refresh_token: Refresh token

        Returns:
            str: New access token

        Raises:
            AuthenticationError: If refresh token is invalid
        """
        payload = verify_refresh_token(refresh_token)
        if not payload:
            raise AuthenticationError("Invalid or expired refresh token")

        # Create new access token
        token_data = {"sub": payload["sub"], "role": payload["role"]}
        access_token = create_access_token(token_data)
        return access_token

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """
        Get user by ID

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Optional[User]: User if found
        """
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def activate_account(db: Session, user_id: int, new_password: str) -> TokenResponse:
        """
        Activate user account by setting new password

        Used by mobile app when user logs in for the first time.
        Sets first_login flag to 0 and updates password.

        Args:
            db: Database session
            user_id: User ID
            new_password: New password (plain text)

        Returns:
            TokenResponse: Access and refresh tokens

        Raises:
            AuthenticationError: If user not found or already activated
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise AuthenticationError("User not found")

        if user.first_login == 0:
            raise AuthenticationError("Account already activated")

        # Update password and set first_login to 0
        hashed_pw = hash_password(new_password)
        user.password_hash = hashed_pw
        user.first_login = 0

        db.commit()
        db.refresh(user)

        # Create tokens
        token_data = {"sub": str(user.id), "role": user.role.value}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        # Import here to avoid circular dependency
        from app.schemas.user import UserResponse

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )
