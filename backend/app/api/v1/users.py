"""
Users API Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.common import MessageResponse, PaginatedResponse
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Create new user

    Requires: Admin role
    """
    repo = UserRepository(User, db)

    # Check if username already exists
    existing_user = repo.get_by_username(user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Check if email already exists (only if email is provided)
    if user_in.email:
        existing_email = repo.get_by_email(user_in.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )

    # Create user with hashed password
    user_data = user_in.model_dump(exclude={"password"})
    user_data["password_hash"] = hash_password(user_in.password)
    user_data["is_active"] = 1 if user_in.is_active else 0  # Convert bool to int
    user_data["first_login"] = 1  # New users need to activate

    user = repo.create(user_data)

    return UserResponse.model_validate(user)


@router.get("", response_model=PaginatedResponse[UserResponse])
def get_users_list(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    role: Optional[str] = Query(None, description="Filter by role"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get users list with pagination and filters

    Requires: Admin role
    """
    repo = UserRepository(User, db)

    # Build filters
    filters = {}
    if is_active is not None:
        filters["is_active"] = 1 if is_active else 0
    if role:
        filters["role"] = role

    # Get users with filters
    users = repo.get_multi(skip=skip, limit=limit, filters=filters)
    total = repo.count(filters=filters)

    # Convert to response models
    user_responses = [UserResponse.model_validate(u) for u in users]

    return PaginatedResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=user_responses
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get user by ID

    Requires: Admin role
    """
    repo = UserRepository(User, db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update user

    Requires: Admin role
    """
    repo = UserRepository(User, db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if email is being changed and if it's already taken
    if user_in.email and user_in.email != user.email:
        existing_email = repo.get_by_email(user_in.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )

    # Prepare update data
    update_data = user_in.model_dump(exclude_unset=True)

    # Hash password if provided
    if "password" in update_data and update_data["password"]:
        update_data["password_hash"] = hash_password(update_data["password"])
        del update_data["password"]

    # Convert is_active bool to int
    if "is_active" in update_data:
        update_data["is_active"] = 1 if update_data["is_active"] else 0

    # Update user
    updated_user = repo.update(user_id, update_data)

    return UserResponse.model_validate(updated_user)


@router.delete("/{user_id}", response_model=MessageResponse)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Delete user

    Requires: Admin role

    Note: Cannot delete yourself
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )

    repo = UserRepository(User, db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    repo.delete(user_id)

    return MessageResponse(message="User deleted successfully")
