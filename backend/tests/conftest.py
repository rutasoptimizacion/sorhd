"""
Pytest configuration and shared fixtures for tests
"""
import pytest
from datetime import datetime, time, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from geoalchemy2 import WKTElement

from app.core.database import Base
from app.models.vehicle import Vehicle as VehicleModel
from app.models.route import Route as RouteModel, RouteStatus, Visit, VisitStatus
from app.models.case import Case as CaseModel, CaseStatus
from app.models.patient import Patient as PatientModel
from app.models.personnel import Personnel as PersonnelModel
from app.models.user import User as UserModel
from app.services.optimization.models import (
    Location,
    TimeWindow,
    Personnel,
    Vehicle,
    Case,
    OptimizationRequest
)


# Database fixtures
@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine using PostgreSQL from docker-compose"""
    from app.core.config import settings
    # Use test database URL or default to docker-compose postgres
    database_url = settings.DATABASE_URL
    engine = create_engine(database_url)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a test database session"""
    from sqlalchemy import text

    # Create a new session
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    # Start a transaction
    connection = session.connection()

    yield session

    # Rollback the transaction to clean up test data
    session.rollback()

    # Clean up all test data
    try:
        session.execute(text("TRUNCATE location_logs, visits, routes, cases, patients, vehicles, personnel, users, care_types, skills CASCADE"))
        session.commit()
    except:
        session.rollback()

    session.close()


@pytest.fixture(scope="function")
def db(db_session):
    """Alias for db_session for compatibility"""
    return db_session


# Test data fixtures
@pytest.fixture
def test_vehicle(db: Session):
    """Create a test vehicle in the database"""
    vehicle = VehicleModel(
        identifier="TEST-VH-001",
        capacity_personnel=10,
        base_location=WKTElement("POINT(-70.6693 -33.4489)", srid=4326),
        status="available",  # Use string value directly
        is_active=True,
        resources={"oxygen": True, "wheelchair": True}
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@pytest.fixture
def test_patient(db: Session):
    """Create a test patient in the database"""
    patient = PatientModel(
        name="Juan Pérez",
        phone="+56912345678",
        email="juan.perez@example.com",
        address="Av. Providencia 1234",
        location=WKTElement("POINT(-70.6506 -33.4372)", srid=4326)
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@pytest.fixture
def test_care_type(db: Session):
    """Create a test care type in the database"""
    from app.models.case import CareType
    care_type = CareType(
        name="Atención General",
        description="Atención general de enfermería",
        estimated_duration_minutes=30
    )
    db.add(care_type)
    db.commit()
    db.refresh(care_type)
    return care_type


@pytest.fixture
def test_case(db: Session, test_patient, test_care_type):
    """Create a test case in the database"""
    from datetime import datetime
    case = CaseModel(
        patient_id=test_patient.id,
        care_type_id=test_care_type.id,
        scheduled_date=datetime.now(),
        time_window_start=datetime.now().replace(hour=8, minute=0),
        time_window_end=datetime.now().replace(hour=12, minute=0),
        location=WKTElement("POINT(-70.6506 -33.4372)", srid=4326),
        estimated_duration_minutes=30,
        priority="medium",
        status="pending",
        notes="Test case"
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@pytest.fixture
def test_active_route(db: Session, test_vehicle, test_case):
    """Create a test active route in the database"""
    route = RouteModel(
        vehicle_id=test_vehicle.id,
        route_date=date.today(),
        status="active",
        total_distance_km=5.0,
        total_duration_minutes=60.0
    )
    db.add(route)
    db.commit()
    db.refresh(route)

    # Add a visit to the route
    visit = Visit(
        route_id=route.id,
        case_id=test_case.id,
        sequence_number=1,
        estimated_arrival_time=datetime.now(),
        estimated_departure_time=datetime.now(),
        status="pending"
    )
    db.add(visit)
    db.commit()
    db.refresh(route)

    return route


@pytest.fixture
def test_visit(db: Session, test_active_route, test_case):
    """Create a test visit in the database"""
    visit = db.query(Visit).filter_by(
        route_id=test_active_route.id,
        case_id=test_case.id
    ).first()

    if not visit:
        visit = Visit(
            route_id=test_active_route.id,
            case_id=test_case.id,
            sequence_number=1,
            estimated_arrival_time=datetime.now(),
            estimated_departure_time=datetime.now(),
            status="pending"
        )
        db.add(visit)
        db.commit()
        db.refresh(visit)

    return visit


@pytest.fixture
def santiago_location():
    """Santiago, Chile location"""
    return Location(latitude=-33.4489, longitude=-70.6693)


@pytest.fixture
def providencia_location():
    """Providencia, Santiago location"""
    return Location(latitude=-33.4372, longitude=-70.6506)


@pytest.fixture
def las_condes_location():
    """Las Condes, Santiago location"""
    return Location(latitude=-33.4177, longitude=-70.5940)


@pytest.fixture
def vitacura_location():
    """Vitacura, Santiago location"""
    return Location(latitude=-33.3882, longitude=-70.5765)


@pytest.fixture
def am_time_window():
    """Morning time window (8:00 - 12:00)"""
    return TimeWindow(start=time(8, 0), end=time(12, 0))


@pytest.fixture
def pm_time_window():
    """Afternoon time window (12:00 - 17:00)"""
    return TimeWindow(start=time(12, 0), end=time(17, 0))


@pytest.fixture
def specific_time_window():
    """Specific time window (10:00 - 11:00)"""
    return TimeWindow(start=time(10, 0), end=time(11, 0))


@pytest.fixture
def sample_personnel(santiago_location):
    """Sample personnel with nurse skills"""
    return Personnel(
        id=1,
        name="Enfermera María González",
        skills=["nurse", "wound_care"],
        start_location=santiago_location,
        work_hours_start=time(8, 0),
        work_hours_end=time(17, 0),
        is_active=True
    )


@pytest.fixture
def sample_physician(santiago_location):
    """Sample physician personnel"""
    return Personnel(
        id=2,
        name="Dr. Carlos Ramírez",
        skills=["physician", "emergency"],
        start_location=santiago_location,
        work_hours_start=time(8, 0),
        work_hours_end=time(17, 0),
        is_active=True
    )


@pytest.fixture
def sample_kinesiologist(santiago_location):
    """Sample kinesiologist personnel"""
    return Personnel(
        id=3,
        name="Kinesiólogo Ana López",
        skills=["kinesiologist", "rehabilitation"],
        start_location=santiago_location,
        work_hours_start=time(8, 0),
        work_hours_end=time(17, 0),
        is_active=True
    )


@pytest.fixture
def sample_vehicle(santiago_location):
    """Sample vehicle"""
    return Vehicle(
        id=1,
        identifier="VH-001",
        capacity=10,
        base_location=santiago_location,
        status="available",
        is_active=True,
        resources={"oxygen": True, "wheelchair": True}
    )


@pytest.fixture
def sample_vehicle_small(santiago_location):
    """Small capacity vehicle"""
    return Vehicle(
        id=2,
        identifier="VH-002",
        capacity=3,
        base_location=santiago_location,
        status="available",
        is_active=True,
        resources={}
    )


@pytest.fixture
def sample_case_nurse(providencia_location, am_time_window):
    """Sample case requiring nurse"""
    return Case(
        id=1,
        patient_id=100,
        patient_name="Juan Pérez",
        location=providencia_location,
        care_type_id=1,
        care_type_name="Curación de Heridas",
        required_skills=["nurse", "wound_care"],
        time_window=am_time_window,
        priority=2,
        estimated_duration=30,
        special_instructions="Tocar timbre dos veces"
    )


@pytest.fixture
def sample_case_physician(las_condes_location, pm_time_window):
    """Sample case requiring physician"""
    return Case(
        id=2,
        patient_id=101,
        patient_name="María Silva",
        location=las_condes_location,
        care_type_id=2,
        care_type_name="Control Médico",
        required_skills=["physician"],
        time_window=pm_time_window,
        priority=1,
        estimated_duration=45,
        special_instructions=None
    )


@pytest.fixture
def sample_case_kinesiology(vitacura_location, am_time_window):
    """Sample case requiring kinesiologist"""
    return Case(
        id=3,
        patient_id=102,
        patient_name="Pedro Torres",
        location=vitacura_location,
        care_type_id=3,
        care_type_name="Rehabilitación",
        required_skills=["kinesiologist"],
        time_window=am_time_window,
        priority=3,
        estimated_duration=60
    )


@pytest.fixture
def sample_cases(sample_case_nurse, sample_case_physician, sample_case_kinesiology):
    """List of sample cases"""
    return [sample_case_nurse, sample_case_physician, sample_case_kinesiology]


@pytest.fixture
def sample_personnel_list(sample_personnel, sample_physician, sample_kinesiologist):
    """List of sample personnel"""
    return [sample_personnel, sample_physician, sample_kinesiologist]


@pytest.fixture
def sample_optimization_request(
    sample_cases,
    sample_vehicle,
    sample_personnel_list
):
    """Sample optimization request"""
    return OptimizationRequest(
        cases=sample_cases,
        vehicles=[sample_vehicle],
        personnel=sample_personnel_list,
        date=datetime(2025, 11, 15),
        max_optimization_time=30
    )


@pytest.fixture
def simple_distance_matrix():
    """Simple distance matrix (km) for testing"""
    # Depot (0), Case 1 (1), Case 2 (2), Case 3 (3)
    return {
        (0, 0): 0.0,
        (0, 1): 2.5,
        (0, 2): 5.0,
        (0, 3): 7.0,
        (1, 0): 2.5,
        (1, 1): 0.0,
        (1, 2): 3.0,
        (1, 3): 5.5,
        (2, 0): 5.0,
        (2, 1): 3.0,
        (2, 2): 0.0,
        (2, 3): 2.5,
        (3, 0): 7.0,
        (3, 1): 5.5,
        (3, 2): 2.5,
        (3, 3): 0.0,
    }


@pytest.fixture
def simple_time_matrix():
    """Simple time matrix (minutes) for testing"""
    # Assume 40 km/h average speed
    # Depot (0), Case 1 (1), Case 2 (2), Case 3 (3)
    return {
        (0, 0): 0,
        (0, 1): 4,  # 2.5 km / 40 km/h * 60 min/h
        (0, 2): 8,
        (0, 3): 11,
        (1, 0): 4,
        (1, 1): 0,
        (1, 2): 5,
        (1, 3): 8,
        (2, 0): 8,
        (2, 1): 5,
        (2, 2): 0,
        (2, 3): 4,
        (3, 0): 11,
        (3, 1): 8,
        (3, 2): 4,
        (3, 3): 0,
    }
