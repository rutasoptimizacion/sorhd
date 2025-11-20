"""
Base Model with Timestamps
"""
from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declared_attr

from app.core.database import Base


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps"""

    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False
        )


class BaseModel(Base, TimestampMixin):
    """Base model class with timestamps"""
    __abstract__ = True
