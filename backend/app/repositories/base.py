"""
Base Repository Pattern Implementation
Provides common CRUD operations for all entities
"""

from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, func

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository class that provides common CRUD operations

    This class uses generics to work with any SQLAlchemy model.
    Repositories for specific entities should inherit from this class.
    """

    def __init__(self, model: Type[ModelType], db: Session):
        """
        Initialize repository with model class and database session

        Args:
            model: The SQLAlchemy model class
            db: Database session
        """
        self.model = model
        self.db = db

    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """
        Create a new record

        Args:
            obj_in: Dictionary with object attributes

        Returns:
            Created model instance
        """
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        Get a record by ID

        Args:
            id: Record ID

        Returns:
            Model instance or None if not found
        """
        stmt = select(self.model).where(self.model.id == id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """
        Get multiple records with pagination and optional filtering

        Args:
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            filters: Optional dictionary of field: value filters

        Returns:
            List of model instances
        """
        stmt = select(self.model)

        # Apply filters if provided
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    stmt = stmt.where(getattr(self.model, field) == value)

        stmt = stmt.offset(skip).limit(limit)
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records with optional filtering

        Args:
            filters: Optional dictionary of field: value filters

        Returns:
            Number of records
        """
        stmt = select(func.count(self.model.id))

        # Apply filters if provided
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    stmt = stmt.where(getattr(self.model, field) == value)

        result = self.db.execute(stmt)
        return result.scalar_one()

    def update(self, id: int, obj_in: Dict[str, Any]) -> Optional[ModelType]:
        """
        Update a record

        Args:
            id: Record ID
            obj_in: Dictionary with fields to update

        Returns:
            Updated model instance or None if not found
        """
        # Remove None values from update dict
        obj_in = {k: v for k, v in obj_in.items() if v is not None}

        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**obj_in)
            .returning(self.model)
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.scalar_one_or_none()

    def delete(self, id: int) -> bool:
        """
        Delete a record

        Args:
            id: Record ID

        Returns:
            True if deleted, False if not found
        """
        stmt = delete(self.model).where(self.model.id == id)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0

    def exists(self, id: int) -> bool:
        """
        Check if a record exists

        Args:
            id: Record ID

        Returns:
            True if exists, False otherwise
        """
        stmt = select(func.count(self.model.id)).where(self.model.id == id)
        result = self.db.execute(stmt)
        return result.scalar_one() > 0
