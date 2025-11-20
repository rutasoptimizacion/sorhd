"""
Case Repository
"""

from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func, cast, Date

from app.repositories.base import BaseRepository
from app.models.case import Case, CaseStatus


class CaseRepository(BaseRepository[Case]):
    """Repository for Case entity"""

    def __init__(self, db: Session):
        super().__init__(Case, db)

    def get_by_id_with_relations(self, id: int) -> Optional[Case]:
        """
        Get case by ID with patient and care_type loaded

        Args:
            id: Case ID

        Returns:
            Case instance with relations or None
        """
        stmt = (
            select(Case)
            .options(joinedload(Case.patient), joinedload(Case.care_type))
            .where(Case.id == id)
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_multi_filtered(
        self,
        scheduled_date: Optional[date] = None,
        status: Optional[CaseStatus] = None,
        patient_id: Optional[int] = None,
        priority: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Case]:
        """
        Get cases with multiple filters

        Args:
            scheduled_date: Filter by scheduled date
            status: Filter by status
            patient_id: Filter by patient ID
            priority: Filter by priority
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of filtered cases
        """
        stmt = select(Case).options(
            joinedload(Case.patient),
            joinedload(Case.care_type)
        )

        if scheduled_date is not None:
            # Use cast to compare datetime column with date
            stmt = stmt.where(cast(Case.scheduled_date, Date) == scheduled_date)

        if status is not None:
            stmt = stmt.where(Case.status == status)

        if patient_id is not None:
            stmt = stmt.where(Case.patient_id == patient_id)

        if priority is not None:
            stmt = stmt.where(Case.priority == priority)

        stmt = stmt.offset(skip).limit(limit)
        result = self.db.execute(stmt)
        return list(result.scalars().unique().all())

    def get_pending_cases_by_date(
        self,
        scheduled_date: date,
        skip: int = 0,
        limit: int = 100
    ) -> List[Case]:
        """
        Get pending cases for a specific date

        Args:
            scheduled_date: Date to filter by
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of pending cases
        """
        return self.get_multi_filtered(
            scheduled_date=scheduled_date,
            status=CaseStatus.PENDING,
            skip=skip,
            limit=limit
        )

    def update_status(self, id: int, status: CaseStatus) -> Optional[Case]:
        """
        Update case status

        Args:
            id: Case ID
            status: New status

        Returns:
            Updated case or None
        """
        return self.update(id, {"status": status})

    def count(self, filters: Optional[dict] = None) -> int:
        """
        Count cases with optional filtering
        Override to handle scheduled_date filtering correctly

        Args:
            filters: Optional dictionary of field: value filters

        Returns:
            Number of cases
        """
        from sqlalchemy import func as sql_func

        stmt = select(sql_func.count(Case.id))

        # Apply filters if provided
        if filters:
            for field, value in filters.items():
                if field == "scheduled_date" and value is not None:
                    # Use cast to compare datetime column with date
                    stmt = stmt.where(cast(Case.scheduled_date, Date) == value)
                elif hasattr(Case, field):
                    stmt = stmt.where(getattr(Case, field) == value)

        result = self.db.execute(stmt)
        return result.scalar_one()
