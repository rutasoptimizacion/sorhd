"""
Patient Service
Business logic for patient management
"""

from typing import List, Optional
from sqlalchemy.orm import Session
import logging

from app.repositories.patient_repository import PatientRepository
from app.schemas.patient import PatientCreate, PatientUpdate
from app.schemas.common import LocationSchema
from app.models.patient import Patient
from app.core.exceptions import NotFoundException
from app.services.audit_service import AuditService
from app.services.geocoding.geocoding_service import GeocodingService

logger = logging.getLogger(__name__)


class PatientService:
    """Service for Patient business logic"""

    def __init__(self, db: Session):
        self.db = db
        self.patient_repo = PatientRepository(db)
        self.audit_service = AuditService(db)
        self.geocoding_service = GeocodingService()

    def _location_to_wkt(self, location: LocationSchema) -> str:
        """Convert LocationSchema to WKT Point"""
        return f"POINT({location.longitude} {location.latitude})"

    def _wkt_to_location(self, wkt: str) -> LocationSchema:
        """Convert WKT Point to LocationSchema"""
        coords = wkt.replace("POINT(", "").replace(")", "").split()
        return LocationSchema(longitude=float(coords[0]), latitude=float(coords[1]))

    async def create_patient(
        self,
        patient_in: PatientCreate,
        user_id: Optional[int] = None
    ) -> Patient:
        """
        Create new patient

        Supports two modes:
        1. Explicit coordinates via 'location' field
        2. Chilean address via 'address' field (will be geocoded)

        Args:
            patient_in: Patient creation data
            user_id: ID of user creating patient

        Returns:
            Created patient

        Raises:
            Exception: If geocoding fails or coordinates are invalid
        """
        # Determine location from either explicit coordinates or geocoded address
        location_schema = None
        geocoded_address = None

        if patient_in.location:
            # Use explicit coordinates (existing behavior)
            location_schema = patient_in.location
            logger.info(f"Creating patient with explicit coordinates: ({location_schema.latitude}, {location_schema.longitude})")
        elif patient_in.address:
            # Geocode address to get coordinates
            logger.info(f"Geocoding address for new patient: {patient_in.address}")
            geocoding_result = await self.geocoding_service.geocode_address(patient_in.address, country="CL")

            if not geocoding_result:
                raise Exception(f"No se pudo geocodificar la dirección: {patient_in.address}")

            location_schema = LocationSchema(
                latitude=geocoding_result.latitude,
                longitude=geocoding_result.longitude
            )
            geocoded_address = geocoding_result.formatted_address

            logger.info(
                f"Successfully geocoded address '{patient_in.address}' to "
                f"({location_schema.latitude}, {location_schema.longitude})"
            )
        else:
            # This should never happen due to model_validator in PatientCreate
            raise ValueError("Debe proporcionar 'location' o 'address'")

        # Convert location to WKT
        location_wkt = self._location_to_wkt(location_schema)

        # Create patient (exclude location and date_of_birth)
        patient_dict = patient_in.model_dump(exclude={"location", "date_of_birth"})
        patient_dict["location"] = location_wkt

        # If address was geocoded, store the formatted address
        if geocoded_address and not patient_dict.get("address"):
            patient_dict["address"] = geocoded_address

        # Map field names from schema to model
        if "medical_notes" in patient_dict:
            patient_dict["notes"] = patient_dict.pop("medical_notes")

        patient = self.patient_repo.create(patient_dict)

        # Log audit
        self.audit_service.log_create("patient", patient.id, user_id)

        logger.info(f"Created patient {patient.id} with RUT: {patient.rut}")

        return patient

    def get_patient(self, patient_id: int) -> Patient:
        """
        Get patient by ID

        Args:
            patient_id: Patient ID

        Returns:
            Patient instance

        Raises:
            NotFoundException: If patient not found
        """
        patient = self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise NotFoundException(f"Patient with ID {patient_id} not found")
        return patient

    def get_patients(self, skip: int = 0, limit: int = 100) -> List[Patient]:
        """
        Get patients with pagination

        Args:
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of patients
        """
        return self.patient_repo.get_multi(skip=skip, limit=limit)

    def search_patients(self, query: str, skip: int = 0, limit: int = 100) -> List[Patient]:
        """
        Search patients by name, phone, or email

        Args:
            query: Search query
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of matching patients
        """
        return self.patient_repo.search(query=query, skip=skip, limit=limit)

    async def update_patient(
        self,
        patient_id: int,
        patient_in: PatientUpdate,
        user_id: Optional[int] = None
    ) -> Patient:
        """
        Update patient

        Supports updating location via:
        1. Explicit coordinates via 'location' field
        2. Chilean address via 'address' field (will be geocoded)

        Args:
            patient_id: Patient ID
            patient_in: Update data
            user_id: ID of user updating patient

        Returns:
            Updated patient

        Raises:
            NotFoundException: If patient not found
            Exception: If geocoding fails
        """
        # Check if patient exists
        patient = self.get_patient(patient_id)

        # Update patient (exclude location and date_of_birth)
        update_dict = patient_in.model_dump(exclude_unset=True, exclude={"location", "date_of_birth"})

        # Handle location update
        if patient_in.location:
            # Use explicit coordinates
            update_dict["location"] = self._location_to_wkt(patient_in.location)
            logger.info(f"Updating patient {patient_id} with explicit coordinates")
        elif patient_in.address:
            # Geocode address to get coordinates
            logger.info(f"Geocoding address for patient {patient_id}: {patient_in.address}")
            geocoding_result = await self.geocoding_service.geocode_address(patient_in.address, country="CL")

            if not geocoding_result:
                raise Exception(f"No se pudo geocodificar la dirección: {patient_in.address}")

            location_schema = LocationSchema(
                latitude=geocoding_result.latitude,
                longitude=geocoding_result.longitude
            )
            update_dict["location"] = self._location_to_wkt(location_schema)

            # Store formatted address
            update_dict["address"] = geocoding_result.formatted_address

            logger.info(
                f"Successfully geocoded address for patient {patient_id}: "
                f"({location_schema.latitude}, {location_schema.longitude})"
            )

        # Map field names from schema to model
        if "medical_notes" in update_dict:
            update_dict["notes"] = update_dict.pop("medical_notes")

        updated_patient = self.patient_repo.update(patient_id, update_dict)

        # Log audit
        self.audit_service.log_update("patient", patient_id, user_id, patient_in.model_dump(exclude_unset=True))

        logger.info(f"Updated patient {patient_id}")

        return updated_patient

    def delete_patient(
        self,
        patient_id: int,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Delete patient

        Args:
            patient_id: Patient ID
            user_id: ID of user deleting patient

        Returns:
            True if deleted

        Raises:
            NotFoundException: If patient not found
        """
        # Check if patient exists
        patient = self.get_patient(patient_id)

        # Delete patient
        result = self.patient_repo.delete(patient_id)

        # Log audit
        if result:
            self.audit_service.log_delete("patient", patient_id, user_id)

        return result

    def count_patients(self) -> int:
        """
        Count patients

        Returns:
            Number of patients
        """
        return self.patient_repo.count()
