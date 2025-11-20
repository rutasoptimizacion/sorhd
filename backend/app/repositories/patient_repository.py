"""
Patient Repository
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.repositories.base import BaseRepository
from app.models.patient import Patient


class PatientRepository(BaseRepository[Patient]):
    """Repository for Patient entity"""

    def __init__(self, db: Session):
        super().__init__(Patient, db)

    def search(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Patient]:
        """
        Search patients by name, phone, or email

        Args:
            query: Search query
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of patients matching the query
        """
        search_term = f"%{query}%"
        stmt = select(Patient).where(
            or_(
                Patient.name.ilike(search_term),
                Patient.phone.ilike(search_term),
                Patient.email.ilike(search_term)
            )
        ).offset(skip).limit(limit)

        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def get_by_phone(self, phone: str) -> Optional[Patient]:
        """
        Get patient by phone number

        Args:
            phone: Phone number

        Returns:
            Patient instance or None
        """
        stmt = select(Patient).where(Patient.phone == phone)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_email(self, email: str) -> Optional[Patient]:
        """
        Get patient by email

        Args:
            email: Email address

        Returns:
            Patient instance or None
        """
        stmt = select(Patient).where(Patient.email == email)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
