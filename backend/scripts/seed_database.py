#!/usr/bin/env python3
"""
Script to populate the database with test data for Phase 9 testing (Route Planning)

Creates:
- 10 Skills
- 10 Care Types
- 15 Personnel
- 5 Vehicles
- 70 Patients
- 50+ Daily Cases

Usage:
    python scripts/seed_database.py
"""

import sys
import os
import random
import argparse
from datetime import datetime, timedelta, time
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.patient import Patient
from app.models.personnel import Personnel, Skill, PersonnelSkill
from app.models.vehicle import Vehicle, VehicleStatus
from app.models.case import Case, CareType, CareTypeSkill, CaseStatus, CasePriority, TimeWindowType
from app.core.database import Base
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

# Get database URL from environment or use default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://sorhd_user:sorhd_password@localhost:5432/sorhd"
)

# Santiago, Chile coordinates (approximate center)
SANTIAGO_LAT = -33.4489
SANTIAGO_LON = -70.6693
# Approximate radius in degrees (~0.1 degree ≈ 11km)
RADIUS = 0.1

# Spanish names for realistic data
FIRST_NAMES = [
    "María", "José", "Juan", "Ana", "Carlos", "Isabel", "Francisco", "Carmen", "Luis", "Rosa",
    "Antonio", "Teresa", "Pedro", "Laura", "Miguel", "Patricia", "Jorge", "Elena", "Ricardo", "Sofía",
    "Alejandro", "Gabriela", "Fernando", "Claudia", "Roberto", "Natalia", "Diego", "Valentina",
    "Andrés", "Camila", "Sebastián", "Daniela", "Mateo", "Martina", "Santiago", "Florencia"
]

LAST_NAMES = [
    "González", "Rodríguez", "Pérez", "Fernández", "López", "Martínez", "García", "Sánchez",
    "Ramírez", "Torres", "Flores", "Rivera", "Silva", "Morales", "Muñoz", "Rojas", "Díaz",
    "Herrera", "Jiménez", "Alvarez", "Castillo", "Vargas", "Castro", "Reyes", "Ortiz"
]

STREETS = [
    "Av. Libertador Bernardo O'Higgins", "Av. Providencia", "Av. Vicuña Mackenna",
    "Av. Apoquindo", "Av. Grecia", "Av. La Florida", "Av. Irarrázaval", "Av. Ñuñoa",
    "Av. Las Condes", "Av. Pedro de Valdivia", "Av. Manuel Montt", "Av. Salvador",
    "Av. Macul", "Av. Matta", "Calle Catedral", "Calle San Diego", "Calle Santa Rosa",
    "Calle Gran Avenida", "Av. Pajaritos", "Av. Américo Vespucio"
]

# Skills for healthcare (10 skills)
SKILLS_DATA = [
    {"name": "Enfermería", "description": "Cuidados de enfermería general"},
    {"name": "Medicina General", "description": "Atención médica general"},
    {"name": "Kinesiología", "description": "Terapia física y rehabilitación"},
    {"name": "Terapia Ocupacional", "description": "Rehabilitación ocupacional"},
    {"name": "Fonoaudiología", "description": "Terapia del habla y lenguaje"},
    {"name": "Nutrición", "description": "Asesoría nutricional"},
    {"name": "Psicología", "description": "Apoyo psicológico"},
    {"name": "Trabajo Social", "description": "Apoyo social y familiar"},
    {"name": "Cuidados Paliativos", "description": "Cuidados al final de la vida"},
    {"name": "Manejo de Heridas", "description": "Curaciones y manejo de heridas complejas"}
]

# Care Types (10 types)
CARE_TYPES_DATA = [
    {
        "name": "Control de Signos Vitales",
        "description": "Monitoreo de presión arterial, temperatura, pulso",
        "duration": 30,
        "skills": ["Enfermería"]
    },
    {
        "name": "Curación de Heridas",
        "description": "Curación y limpieza de heridas",
        "duration": 45,
        "skills": ["Enfermería", "Manejo de Heridas"]
    },
    {
        "name": "Terapia Respiratoria",
        "description": "Ejercicios y terapia respiratoria",
        "duration": 60,
        "skills": ["Kinesiología"]
    },
    {
        "name": "Control Médico",
        "description": "Evaluación médica general",
        "duration": 45,
        "skills": ["Medicina General", "Enfermería"]
    },
    {
        "name": "Terapia Ocupacional",
        "description": "Rehabilitación de actividades diarias",
        "duration": 60,
        "skills": ["Terapia Ocupacional"]
    },
    {
        "name": "Evaluación Nutricional",
        "description": "Valoración y plan nutricional",
        "duration": 45,
        "skills": ["Nutrición"]
    },
    {
        "name": "Apoyo Psicológico",
        "description": "Sesión de apoyo psicológico",
        "duration": 60,
        "skills": ["Psicología"]
    },
    {
        "name": "Cuidados Paliativos",
        "description": "Atención integral paliativa",
        "duration": 90,
        "skills": ["Medicina General", "Enfermería", "Cuidados Paliativos"]
    },
    {
        "name": "Terapia del Habla",
        "description": "Rehabilitación del habla y deglución",
        "duration": 60,
        "skills": ["Fonoaudiología"]
    },
    {
        "name": "Visita Social",
        "description": "Evaluación social y familiar",
        "duration": 45,
        "skills": ["Trabajo Social"]
    }
]


def random_location(center_lat=SANTIAGO_LAT, center_lon=SANTIAGO_LON, radius=RADIUS):
    """Generate a random location within radius of center"""
    # Simple random distribution in a square
    lat = center_lat + random.uniform(-radius, radius)
    lon = center_lon + random.uniform(-radius, radius)
    return Point(lon, lat)  # PostGIS uses (lon, lat)


def random_phone():
    """Generate a random Chilean phone number"""
    return f"+569{random.randint(10000000, 99999999)}"


def random_email(first_name, last_name):
    """Generate a random email"""
    domains = ["gmail.com", "hotmail.com", "yahoo.com", "outlook.com"]
    return f"{first_name.lower()}.{last_name.lower()}@{random.choice(domains)}"


def random_address():
    """Generate a random Chilean address"""
    street = random.choice(STREETS)
    number = random.randint(100, 9999)
    return f"{street} {number}, Santiago"


def seed_skills(db):
    """Create skills"""
    print("📚 Creando habilidades...")
    skills = []

    for skill_data in SKILLS_DATA:
        skill = Skill(
            name=skill_data["name"],
            description=skill_data["description"]
        )
        db.add(skill)
        skills.append(skill)

    db.commit()
    print(f"✅ {len(skills)} habilidades creadas")
    return skills


def seed_care_types(db, skills_dict):
    """Create care types with required skills"""
    print("\n🏥 Creando tipos de atención...")
    care_types = []

    for care_data in CARE_TYPES_DATA:
        care_type = CareType(
            name=care_data["name"],
            description=care_data["description"],
            estimated_duration_minutes=care_data["duration"]
        )
        db.add(care_type)
        db.flush()  # Get the ID

        # Add required skills
        for skill_name in care_data["skills"]:
            if skill_name in skills_dict:
                care_type_skill = CareTypeSkill(
                    care_type_id=care_type.id,
                    skill_id=skills_dict[skill_name].id
                )
                db.add(care_type_skill)

        care_types.append(care_type)

    db.commit()
    print(f"✅ {len(care_types)} tipos de atención creados")
    return care_types


def seed_personnel(db, skills_list):
    """Create 15 personnel with various skills"""
    print("\n👥 Creando personal de salud...")
    personnel_list = []

    # Define personnel profiles with skills
    personnel_profiles = [
        {"role": "Enfermero/a Jefe", "skills": ["Enfermería", "Manejo de Heridas"]},
        {"role": "Enfermero/a", "skills": ["Enfermería"]},
        {"role": "Enfermero/a", "skills": ["Enfermería", "Cuidados Paliativos"]},
        {"role": "Médico/a", "skills": ["Medicina General", "Enfermería"]},
        {"role": "Médico/a", "skills": ["Medicina General", "Cuidados Paliativos"]},
        {"role": "Kinesiólogo/a", "skills": ["Kinesiología"]},
        {"role": "Kinesiólogo/a", "skills": ["Kinesiología"]},
        {"role": "Terapeuta Ocupacional", "skills": ["Terapia Ocupacional"]},
        {"role": "Nutricionista", "skills": ["Nutrición"]},
        {"role": "Psicólogo/a", "skills": ["Psicología"]},
        {"role": "Fonoaudiólogo/a", "skills": ["Fonoaudiología"]},
        {"role": "Trabajador/a Social", "skills": ["Trabajo Social"]},
        {"role": "Enfermero/a", "skills": ["Enfermería", "Manejo de Heridas"]},
        {"role": "Técnico/a Enfermería", "skills": ["Enfermería"]},
        {"role": "Auxiliar de Enfermería", "skills": ["Enfermería"]}
    ]

    skills_dict = {skill.name: skill for skill in skills_list}

    for i, profile in enumerate(personnel_profiles):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)

        personnel = Personnel(
            name=f"{first_name} {last_name}",
            phone=random_phone(),
            start_location=from_shape(random_location(), srid=4326),
            work_start_time=time(8, 0),
            work_end_time=time(17, 0),
            is_active=True
        )
        db.add(personnel)
        db.flush()

        # Add skills
        for skill_name in profile["skills"]:
            if skill_name in skills_dict:
                personnel_skill = PersonnelSkill(
                    personnel_id=personnel.id,
                    skill_id=skills_dict[skill_name].id
                )
                db.add(personnel_skill)

        personnel_list.append(personnel)

    db.commit()
    print(f"✅ {len(personnel_list)} personal de salud creado")
    return personnel_list


def seed_vehicles(db):
    """Create 5 vehicles"""
    print("\n🚗 Creando vehículos...")
    vehicles = []

    vehicle_data = [
        {"id": "VEH-001", "plate": "ABCD12", "capacity": 3, "resources": ["Oxígeno", "Camilla", "Botiquín"]},
        {"id": "VEH-002", "plate": "EFGH34", "capacity": 2, "resources": ["Oxígeno", "Botiquín"]},
        {"id": "VEH-003", "plate": "IJKL56", "capacity": 4, "resources": ["Oxígeno", "Camilla", "Botiquín", "Silla de ruedas"]},
        {"id": "VEH-004", "plate": "MNOP78", "capacity": 2, "resources": ["Botiquín"]},
        {"id": "VEH-005", "plate": "QRST90", "capacity": 3, "resources": ["Oxígeno", "Botiquín", "Silla de ruedas"]}
    ]

    for veh_data in vehicle_data:
        vehicle = Vehicle(
            identifier=veh_data["id"],
            license_plate=veh_data["plate"],
            capacity_personnel=veh_data["capacity"],
            base_location=from_shape(random_location(), srid=4326),
            status=VehicleStatus.AVAILABLE,
            resources=veh_data["resources"],
            is_active=True
        )
        db.add(vehicle)
        vehicles.append(vehicle)

    db.commit()
    print(f"✅ {len(vehicles)} vehículos creados")
    return vehicles


def seed_patients(db):
    """Create 70 patients"""
    print("\n🏠 Creando pacientes...")
    patients = []

    for i in range(70):
        first_name = random.choice(FIRST_NAMES)
        last_name1 = random.choice(LAST_NAMES)
        last_name2 = random.choice(LAST_NAMES)

        patient = Patient(
            name=f"{first_name} {last_name1} {last_name2}",
            phone=random_phone(),
            email=random_email(first_name, last_name1),
            address=random_address(),
            location=from_shape(random_location(), srid=4326),
            notes=f"Paciente {i+1} - Hospitalización domiciliaria"
        )
        db.add(patient)
        patients.append(patient)

    db.commit()
    print(f"✅ {len(patients)} pacientes creados")
    return patients


def seed_cases(db, patients, care_types):
    """Create 50+ daily cases for tomorrow"""
    print("\n📋 Creando casos para mañana...")
    cases = []

    # Use tomorrow's date for testing
    tomorrow = datetime.now().date() + timedelta(days=1)

    # Create 55 cases to have a good dataset
    num_cases = 55

    for i in range(num_cases):
        patient = random.choice(patients)
        care_type = random.choice(care_types)

        # Random priority distribution (most medium, some high, few urgent)
        priority_weights = [
            (CasePriority.LOW, 10),
            (CasePriority.MEDIUM, 60),
            (CasePriority.HIGH, 25),
            (CasePriority.URGENT, 5)
        ]
        priority = random.choices(
            [p[0] for p in priority_weights],
            weights=[p[1] for p in priority_weights]
        )[0]

        # Random time window type distribution
        time_window_weights = [
            (TimeWindowType.AM, 30),
            (TimeWindowType.PM, 30),
            (TimeWindowType.SPECIFIC, 20),
            (TimeWindowType.ANYTIME, 20)
        ]
        time_window_type = random.choices(
            [t[0] for t in time_window_weights],
            weights=[t[1] for t in time_window_weights]
        )[0]

        # Set time windows based on type
        if time_window_type == TimeWindowType.AM:
            time_window_start = datetime.combine(tomorrow, time(8, 0))
            time_window_end = datetime.combine(tomorrow, time(12, 0))
        elif time_window_type == TimeWindowType.PM:
            time_window_start = datetime.combine(tomorrow, time(12, 0))
            time_window_end = datetime.combine(tomorrow, time(17, 0))
        elif time_window_type == TimeWindowType.SPECIFIC:
            # Random 2-hour window
            start_hour = random.randint(8, 15)
            time_window_start = datetime.combine(tomorrow, time(start_hour, 0))
            time_window_end = datetime.combine(tomorrow, time(start_hour + 2, 0))
        else:  # ANYTIME
            time_window_start = datetime.combine(tomorrow, time(8, 0))
            time_window_end = datetime.combine(tomorrow, time(17, 0))

        case = Case(
            patient_id=patient.id,
            care_type_id=care_type.id,
            scheduled_date=datetime.combine(tomorrow, time(9, 0)),
            time_window_type=time_window_type,
            time_window_start=time_window_start,
            time_window_end=time_window_end,
            location=patient.location,  # Use patient's location
            priority=priority,
            status=CaseStatus.PENDING,
            notes=f"Caso de prueba {i+1}",
            estimated_duration_minutes=care_type.estimated_duration_minutes
        )
        db.add(case)
        cases.append(case)

    db.commit()
    print(f"✅ {len(cases)} casos creados para {tomorrow.strftime('%d/%m/%Y')}")
    return cases


def print_summary(skills, care_types, personnel, vehicles, patients, cases):
    """Print a summary of created data"""
    print("\n" + "="*60)
    print("📊 RESUMEN DE DATOS CREADOS")
    print("="*60)
    print(f"✅ Habilidades: {len(skills)}")
    print(f"✅ Tipos de atención: {len(care_types)}")
    print(f"✅ Personal: {len(personnel)}")
    print(f"✅ Vehículos: {len(vehicles)}")
    print(f"✅ Pacientes: {len(patients)}")
    print(f"✅ Casos: {len(cases)}")
    print("="*60)
    print("\n📅 Casos por prioridad:")

    priorities = {}
    for case in cases:
        priorities[case.priority] = priorities.get(case.priority, 0) + 1

    for priority, count in sorted(priorities.items()):
        print(f"   {priority.value.upper()}: {count}")

    print("\n⏰ Casos por ventana horaria:")
    time_windows = {}
    for case in cases:
        time_windows[case.time_window_type] = time_windows.get(case.time_window_type, 0) + 1

    for tw, count in sorted(time_windows.items()):
        print(f"   {tw.value.upper()}: {count}")

    print("\n" + "="*60)
    print("🎉 Base de datos poblada exitosamente!")
    print("="*60)
    print("\n💡 Próximos pasos:")
    print("   1. Inicia el backend: cd backend && uvicorn app.main:app --reload")
    print("   2. Inicia el admin panel: cd admin && npm run dev")
    print("   3. Ve a la sección de Planificación de Rutas")
    print("   4. Selecciona los casos y vehículos para optimizar")
    print()


def main():
    """Main function to seed database"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Poblar la base de datos con datos de prueba')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Forzar la ejecución sin confirmación')
    parser.add_argument('--clean', '-c', action='store_true',
                        help='Limpiar datos existentes antes de poblar (CUIDADO: Esto eliminará todos los datos)')
    args = parser.parse_args()

    print("🌱 POBLANDO BASE DE DATOS CON DATOS DE PRUEBA")
    print("="*60)

    # Create engine and session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Check if data already exists
        existing_skills = db.query(Skill).count()

        if args.clean and existing_skills > 0:
            print("\n🧹 Limpiando datos existentes...")
            # Delete in order of dependencies
            db.query(Case).delete()
            db.query(CareTypeSkill).delete()
            db.query(PersonnelSkill).delete()
            db.query(Patient).delete()
            db.query(Vehicle).delete()
            db.query(Personnel).delete()
            db.query(CareType).delete()
            db.query(Skill).delete()
            db.commit()
            print("✅ Datos eliminados")
            existing_skills = 0

        if existing_skills > 0 and not args.force:
            print("\n⚠️  ADVERTENCIA: Ya existen datos en la base de datos.")
            try:
                response = input("¿Deseas continuar y agregar más datos? (s/n): ")
                if response.lower() != 's':
                    print("❌ Operación cancelada")
                    return
            except (EOFError, KeyboardInterrupt):
                print("\n❌ Operación cancelada")
                return

        # Seed data in order
        skills = seed_skills(db)
        skills_dict = {skill.name: skill for skill in skills}

        care_types = seed_care_types(db, skills_dict)
        personnel = seed_personnel(db, skills)
        vehicles = seed_vehicles(db)
        patients = seed_patients(db)
        cases = seed_cases(db, patients, care_types)

        # Print summary
        print_summary(skills, care_types, personnel, vehicles, patients, cases)

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error al poblar la base de datos: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
