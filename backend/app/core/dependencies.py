"""
FastAPI Dependencies for Authentication and Authorization
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import verify_access_token
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.models.user import User, UserRole
from app.services.auth_service import AuthService

# HTTP Bearer security scheme
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token

    Args:
        credentials: HTTP authorization credentials (Bearer token)
        db: Database session

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    payload = verify_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(payload.get("sub"))
    user = AuthService.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current active user

    Args:
        current_user: Current user from token

    Returns:
        User: Current active user
    """
    return current_user


def require_role(allowed_roles: List[UserRole]):
    """
    Create a dependency that requires specific roles

    Args:
        allowed_roles: List of allowed user roles

    Returns:
        Dependency function
    """

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted for role: {current_user.role}",
            )
        return current_user

    return role_checker


# Pre-defined role dependencies
require_admin = require_role([UserRole.ADMIN])
require_admin_or_clinical = require_role([UserRole.ADMIN, UserRole.CLINICAL_TEAM])
