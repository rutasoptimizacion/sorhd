"""
Case Service
Business logic for case management
"""

from typing import List, Optional
from datetime import date, datetime, time
from sqlalchemy.orm import Session

from app.repositories.case_repository import CaseRepository
from app.schemas.case import CaseCreate, CaseUpdate, CaseStatus, CasePriority
from app.schemas.common import LocationSchema
from app.models.case import Case
from app.core.exceptions import NotFoundException, ValidationException
from app.services.audit_service import AuditService
from app.services.patient_service import PatientService
from app.services.care_type_service import CareTypeService


class CaseService:
    """Service for Case business logic"""

    def __init__(self, db: Session):
        self.db = db
        self.case_repo = CaseRepository(db)
        self.patient_service = PatientService(db)
        self.care_type_service = CareTypeService(db)
        self.audit_service = AuditService(db)

    def _location_to_wkt(self, location: LocationSchema) -> str:
        """Convert LocationSchema to WKT Point"""
        return f"POINT({location.longitude} {location.latitude})"

    def _wkt_to_location(self, wkt: str) -> LocationSchema:
        """Convert WKT Point to LocationSchema"""
        coords = wkt.replace("POINT(", "").replace(")", "").split()
        return LocationSchema(longitude=float(coords[0]), latitude=float(coords[1]))

    def create_case(
        self,
        case_in: CaseCreate,
        user_id: Optional[int] = None
    ) -> Case:
        """
        Create new case

        Args:
            case_in: Case creation data
            user_id: ID of user creating case

        Returns:
            Created case

        Raises:
            NotFoundException: If patient or care type not found
            ValidationException: If time window is invalid
        """
        # Validate patient exists
        patient = self.patient_service.get_patient(case_in.patient_id)

        # Validate care type exists
        care_type = self.care_type_service.get_care_type(case_in.care_type_id)

        # Validate time window
        if case_in.time_window_start and case_in.time_window_end:
            if case_in.time_window_end <= case_in.time_window_start:
                raise ValidationException("time_window_end must be after time_window_start")

        # Use patient location if location not provided
        location = case_in.location if case_in.location else patient.location

        # Convert location to WKT
        if isinstance(location, LocationSchema):
            location_wkt = self._location_to_wkt(location)
        else:
            # location is already WKT from patient
            location_wkt = location

        # Create case
        case_dict = case_in.model_dump(exclude={"location"})
        case_dict["location"] = location_wkt
        case_dict["status"] = CaseStatus.PENDING  # New cases are always pending

        # Convert scheduled_date (date) to datetime
        if isinstance(case_dict.get("scheduled_date"), date):
            case_dict["scheduled_date"] = datetime.combine(case_dict["scheduled_date"], time(0, 0))

        # Convert time windows (time) to datetime by combining with scheduled_date
        if case_dict.get("time_window_start"):
            case_dict["time_window_start"] = datetime.combine(case_in.scheduled_date, case_in.time_window_start)
        if case_dict.get("time_window_end"):
            case_dict["time_window_end"] = datetime.combine(case_in.scheduled_date, case_in.time_window_end)

        case = self.case_repo.create(case_dict)

        # Log audit
        self.audit_service.log_create("case", case.id, user_id)

        # Reload with relations
        return self.case_repo.get_by_id_with_relations(case.id)

    def get_case(self, case_id: int) -> Case:
        """
        Get case by ID with relations

        Args:
            case_id: Case ID

        Returns:
            Case instance with patient and care_type

        Raises:
            NotFoundException: If case not found
        """
        case = self.case_repo.get_by_id_with_relations(case_id)
        if not case:
            raise NotFoundException(f"Case with ID {case_id} not found")
        return case

    def get_cases(
        self,
        skip: int = 0,
        limit: int = 100,
        scheduled_date: Optional[date] = None,
        status: Optional[CaseStatus] = None,
        patient_id: Optional[int] = None,
        priority: Optional[CasePriority] = None
    ) -> List[Case]:
        """
        Get cases with filters

        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            scheduled_date: Filter by scheduled date
            status: Filter by status
            patient_id: Filter by patient ID
            priority: Filter by priority

        Returns:
            List of cases with relations
        """
        return self.case_repo.get_multi_filtered(
            scheduled_date=scheduled_date,
            status=status,
            patient_id=patient_id,
            priority=priority,
            skip=skip,
            limit=limit
        )

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
        return self.case_repo.get_pending_cases_by_date(
            scheduled_date=scheduled_date,
            skip=skip,
            limit=limit
        )

    def update_case(
        self,
        case_id: int,
        case_in: CaseUpdate,
        user_id: Optional[int] = None
    ) -> Case:
        """
        Update case

        Args:
            case_id: Case ID
            case_in: Update data
            user_id: ID of user updating case

        Returns:
            Updated case

        Raises:
            NotFoundException: If case, patient, or care type not found
            ValidationException: If time window is invalid or case is already assigned
        """
        # Check if case exists
        case = self.get_case(case_id)

        # Validate patient if being updated
        if case_in.patient_id:
            self.patient_service.get_patient(case_in.patient_id)

        # Validate care type if being updated
        if case_in.care_type_id:
            self.care_type_service.get_care_type(case_in.care_type_id)

        # Validate time window
        time_start = case_in.time_window_start or case.time_window_start
        time_end = case_in.time_window_end or case.time_window_end
        if time_start and time_end and time_end <= time_start:
            raise ValidationException("time_window_end must be after time_window_start")

        # TODO: Prevent updates if case is in an active route (Phase 4)

        # Update case
        update_dict = case_in.model_dump(exclude_unset=True, exclude={"location"})

        # Convert location if provided
        if case_in.location:
            update_dict["location"] = self._location_to_wkt(case_in.location)

        # Convert scheduled_date (date) to datetime
        if "scheduled_date" in update_dict and isinstance(update_dict["scheduled_date"], date):
            update_dict["scheduled_date"] = datetime.combine(update_dict["scheduled_date"], time(0, 0))

        # Convert time windows (time) to datetime by combining with scheduled_date
        scheduled_date_for_times = case_in.scheduled_date if case_in.scheduled_date else case.scheduled_date.date()
        if "time_window_start" in update_dict and update_dict["time_window_start"]:
            update_dict["time_window_start"] = datetime.combine(scheduled_date_for_times, case_in.time_window_start)
        if "time_window_end" in update_dict and update_dict["time_window_end"]:
            update_dict["time_window_end"] = datetime.combine(scheduled_date_for_times, case_in.time_window_end)

        updated_case = self.case_repo.update(case_id, update_dict)

        # Log audit
        self.audit_service.log_update("case", case_id, user_id, case_in.model_dump(exclude_unset=True))

        # Reload with relations
        return self.case_repo.get_by_id_with_relations(case_id)

    def update_case_status(
        self,
        case_id: int,
        status: CaseStatus,
        user_id: Optional[int] = None
    ) -> Case:
        """
        Update case status

        Args:
            case_id: Case ID
            status: New status
            user_id: ID of user updating status

        Returns:
            Updated case
        """
        case = self.case_repo.update_status(case_id, status)
        if not case:
            raise NotFoundException(f"Case with ID {case_id} not found")

        # Log audit
        self.audit_service.log_update("case", case_id, user_id, {"status": status})

        # Reload with relations
        return self.case_repo.get_by_id_with_relations(case_id)

    def delete_case(
        self,
        case_id: int,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Delete case

        Args:
            case_id: Case ID
            user_id: ID of user deleting case

        Returns:
            True if deleted

        Raises:
            NotFoundException: If case not found
            ValidationException: If case is in active route
        """
        # Check if case exists
        case = self.get_case(case_id)

        # Prevent deletion if case is assigned or completed
        if case.status in [CaseStatus.ASSIGNED, CaseStatus.COMPLETED]:
            raise ValidationException(f"Cannot delete case with status '{case.status}'")

        # Delete case
        result = self.case_repo.delete(case_id)

        # Log audit
        if result:
            self.audit_service.log_delete("case", case_id, user_id)

        return result

    def count_cases(
        self,
        scheduled_date: Optional[date] = None,
        status: Optional[CaseStatus] = None
    ) -> int:
        """
        Count cases

        Args:
            scheduled_date: Filter by scheduled date
            status: Filter by status

        Returns:
            Number of cases
        """
        filters = {}
        if scheduled_date is not None:
            filters["scheduled_date"] = scheduled_date
        if status is not None:
            filters["status"] = status

        return self.case_repo.count(filters=filters if filters else None)
