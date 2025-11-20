#!/usr/bin/env python3
"""
Script para crear 75 pacientes y casos de prueba en la región de Valparaíso
para el 20 de noviembre de 2025.

Áreas cubiertas: Comunas del Servicio de Salud Viña del Mar Quillota
Hospitales base: Gustavo Fricke (Viña), Quilpué, Biprovincial

Usage:
    python scripts/seed_valparaiso.py
"""

import sys
import os
import random
from datetime import datetime, timedelta, time
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from app.models.patient import Patient
from app.models.personnel import Personnel
from app.models.vehicle import Vehicle
from app.models.case import Case, CareType, CaseStatus, CasePriority, TimeWindowType
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

# Get database URL from environment or use default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://sorhd_user:sorhd_password@localhost:5432/sorhd"
)

# Coordenadas de hospitales base (lon, lat)
HOSPITALS = {
    "Gustavo Fricke": {"lat": -33.0205, "lon": -71.5514, "name": "Hospital Dr. Gustavo Fricke, Viña del Mar"},
    "Quilpue": {"lat": -33.0475, "lon": -71.4428, "name": "Hospital de Quilpué"},
    "Biprovincial": {"lat": -32.7896, "lon": -71.2145, "name": "Hospital Biprovincial Quillota-Petorca"}
}

# Comunas del Servicio de Salud Viña del Mar Quillota con coordenadas aproximadas
# Cada comuna tiene un centro y radio aproximado en grados (~0.01 grados ≈ 1.1km)
COMUNAS = {
    "Viña del Mar": {
        "center": {"lat": -33.0247, "lon": -71.5514},
        "radius": 0.03,  # ~3.3km
        "calles": [
            "Av. Libertad", "Av. Valparaíso", "Av. España", "Av. Álvarez",
            "Av. Marina", "Calle Von Schroeders", "Av. San Martín", "Av. Los Castaños",
            "Av. Agua Santa", "Calle Quillota", "Av. Benidorm", "Calle Arlegui"
        ]
    },
    "Quilpué": {
        "center": {"lat": -33.0475, "lon": -71.4428},
        "radius": 0.025,
        "calles": [
            "Av. Presidente Jorge Alessandri", "Av. Los Carrera", "Calle Maipú",
            "Calle Freire", "Av. El Retiro", "Calle Rancagua", "Av. Francia",
            "Calle Carmen Covarrubias", "Av. Concepción", "Calle Membrillar"
        ]
    },
    "Villa Alemana": {
        "center": {"lat": -33.0436, "lon": -71.3732},
        "radius": 0.02,
        "calles": [
            "Av. Valparaíso", "Av. José Francisco Vergara", "Calle Victoria",
            "Av. Portales", "Av. Alessandri", "Calle Esmeralda", "Av. Padre Hurtado",
            "Calle Las Acacias", "Av. Sargento Aldea", "Calle Los Copihues"
        ]
    },
    "Concón": {
        "center": {"lat": -32.9253, "lon": -71.5193},
        "radius": 0.025,
        "calles": [
            "Av. Concón Reñaca", "Av. Borgoño", "Av. Los Pescadores",
            "Calle Santa Laura", "Av. Vecinal", "Calle Los Jazmines",
            "Av. Edmundo Eluchans", "Calle Arrayán", "Av. Costanera"
        ]
    },
    "Quintero": {
        "center": {"lat": -32.7832, "lon": -71.5320},
        "radius": 0.02,
        "calles": [
            "Av. 21 de Mayo", "Calle Latorre", "Av. Libertad",
            "Calle Bulnes", "Av. Costanera", "Calle Errázuriz",
            "Av. Arturo Prat", "Calle Los Aromos", "Av. Portales"
        ]
    },
    "Puchuncaví": {
        "center": {"lat": -32.7393, "lon": -71.4065},
        "radius": 0.015,
        "calles": [
            "Av. Puchuncaví", "Calle Carrera", "Av. La Iglesia",
            "Calle Portales", "Av. Prat", "Calle Las Palmas",
            "Av. El Llano", "Calle Los Boldos", "Av. Central"
        ]
    },
    "Quillota": {
        "center": {"lat": -32.8836, "lon": -71.2492},
        "radius": 0.025,
        "calles": [
            "Av. Balmaceda", "Calle Freire", "Av. O'Higgins",
            "Calle Maipú", "Av. Los Carrera", "Calle Condell",
            "Av. San Martín", "Calle Chacabuco", "Av. Eastman"
        ]
    },
    "La Calera": {
        "center": {"lat": -32.7867, "lon": -71.2019},
        "radius": 0.02,
        "calles": [
            "Av. Eastman", "Calle Independencia", "Av. Portales",
            "Calle Freire", "Av. Alessandri", "Calle Esmeralda",
            "Av. Pedro Montt", "Calle Barros Arana", "Av. Central"
        ]
    },
    "La Cruz": {
        "center": {"lat": -32.8267, "lon": -71.2289},
        "radius": 0.015,
        "calles": [
            "Av. Principal", "Calle O'Higgins", "Av. La Cruz",
            "Calle Portales", "Av. Los Aromos", "Calle Balmaceda",
            "Av. Central", "Calle Las Rosas", "Av. Santa Rosa"
        ]
    },
    "Nogales": {
        "center": {"lat": -32.7289, "lon": -71.1756},
        "radius": 0.015,
        "calles": [
            "Av. Nogales", "Calle Portales", "Av. La Unión",
            "Calle Freire", "Av. Central", "Calle Las Palmas",
            "Av. Los Aromos", "Calle Independencia", "Av. Prat"
        ]
    },
    "Hijuelas": {
        "center": {"lat": -32.8111, "lon": -71.1578},
        "radius": 0.012,
        "calles": [
            "Av. Hijuelas", "Calle Portales", "Av. Central",
            "Calle O'Higgins", "Av. La Paz", "Calle Las Rosas",
            "Av. Los Copihues", "Calle Freire", "Av. Principal"
        ]
    }
}

# Nombres chilenos realistas
FIRST_NAMES = [
    "María", "José", "Juan", "Ana", "Carlos", "Isabel", "Francisco", "Carmen", "Luis", "Rosa",
    "Antonio", "Teresa", "Pedro", "Laura", "Miguel", "Patricia", "Jorge", "Elena", "Ricardo", "Sofía",
    "Alejandro", "Gabriela", "Fernando", "Claudia", "Roberto", "Natalia", "Diego", "Valentina",
    "Andrés", "Camila", "Sebastián", "Daniela", "Mateo", "Martina", "Santiago", "Florencia",
    "Pablo", "Javiera", "Tomás", "Constanza", "Nicolás", "Catalina", "Ignacio", "Fernanda",
    "Felipe", "Macarena", "Cristóbal", "Isidora", "Vicente", "Antonia", "Joaquín", "Amanda",
    "Benjamín", "Carolina", "Agustín", "Verónica", "Maximiliano", "Paz", "Lucas", "Francisca",
    "Raúl", "Pilar", "Emilio", "Beatriz", "Hernán", "Gloria", "Manuel", "Cecilia", "Rodrigo", "Soledad"
]

LAST_NAMES = [
    "González", "Rodríguez", "Pérez", "Fernández", "López", "Martínez", "García", "Sánchez",
    "Ramírez", "Torres", "Flores", "Rivera", "Silva", "Morales", "Muñoz", "Rojas", "Díaz",
    "Herrera", "Jiménez", "Alvarez", "Castillo", "Vargas", "Castro", "Reyes", "Ortiz",
    "Núñez", "Mendoza", "Guzmán", "Bravo", "Medina", "Vega", "Peña", "Espinoza", "Campos",
    "Contreras", "Fuentes", "Navarrete", "Sepúlveda", "Pizarro", "Riquelme"
]


def calculate_rut_verifier(rut_number: int) -> str:
    """
    Calcula el dígito verificador de un RUT chileno usando módulo 11.

    Args:
        rut_number: Número del RUT sin dígito verificador

    Returns:
        Dígito verificador como string ('0'-'9' o 'K')
    """
    multipliers = [2, 3, 4, 5, 6, 7]
    sum_result = 0
    rut_str = str(rut_number)

    # Recorrer de derecha a izquierda
    for i, digit in enumerate(reversed(rut_str)):
        multiplier = multipliers[i % len(multipliers)]
        sum_result += int(digit) * multiplier

    remainder = sum_result % 11
    verifier = 11 - remainder

    if verifier == 11:
        return '0'
    elif verifier == 10:
        return 'K'
    else:
        return str(verifier)


def generate_unique_rut(db, existing_ruts: set) -> str:
    """
    Genera un RUT válido único que no existe en la base de datos.

    Args:
        db: Sesión de base de datos
        existing_ruts: Set de RUTs ya existentes para verificación rápida

    Returns:
        RUT limpio (sin puntos ni guión) como string
    """
    max_attempts = 100

    for _ in range(max_attempts):
        # Generar RUT entre 5.000.000 y 25.000.000
        rut_number = random.randint(5_000_000, 25_000_000)
        verifier = calculate_rut_verifier(rut_number)
        clean_rut = f"{rut_number}{verifier}"

        # Verificar si el RUT ya existe
        if clean_rut not in existing_ruts:
            # Doble verificación en base de datos
            existing = db.query(Patient).filter(
                or_(
                    Patient.rut == clean_rut,
                    Patient.rut.like(f"%{rut_number}%{verifier}")
                )
            ).first()

            if not existing:
                return clean_rut

    raise RuntimeError("No se pudo generar un RUT único después de 100 intentos")


def random_phone():
    """Generar número de teléfono chileno"""
    return f"+569{random.randint(10000000, 99999999)}"


def random_email(first_name, last_name):
    """Generar email aleatorio"""
    domains = ["gmail.com", "hotmail.com", "yahoo.com", "outlook.com", "icloud.com"]
    return f"{first_name.lower()}.{last_name.lower()}@{random.choice(domains)}"


def random_location_in_comuna(comuna_name):
    """Generar ubicación aleatoria dentro de una comuna"""
    comuna = COMUNAS[comuna_name]
    center_lat = comuna["center"]["lat"]
    center_lon = comuna["center"]["lon"]
    radius = comuna["radius"]

    # Distribución aleatoria dentro del radio
    lat = center_lat + random.uniform(-radius, radius)
    lon = center_lon + random.uniform(-radius, radius)

    return Point(lon, lat)  # PostGIS usa (lon, lat)


def random_address_in_comuna(comuna_name):
    """Generar dirección aleatoria en la comuna"""
    calle = random.choice(COMUNAS[comuna_name]["calles"])
    numero = random.randint(100, 9999)
    return f"{calle} {numero}, {comuna_name}"


def update_vehicles_and_personnel(db):
    """Actualizar vehículos y personal para usar hospitales como punto de partida"""
    print("\n🚗 Actualizando vehículos con ubicaciones de hospitales...")

    vehicles = db.query(Vehicle).all()
    hospital_list = list(HOSPITALS.values())

    for vehicle in vehicles:
        hospital = random.choice(hospital_list)
        vehicle.base_location = from_shape(
            Point(hospital["lon"], hospital["lat"]),
            srid=4326
        )
        print(f"   {vehicle.identifier} → {hospital['name']}")

    db.commit()
    print(f"✅ {len(vehicles)} vehículos actualizados")

    print("\n👥 Actualizando personal con ubicaciones de hospitales...")
    personnel = db.query(Personnel).all()

    for person in personnel:
        hospital = random.choice(hospital_list)
        person.start_location = from_shape(
            Point(hospital["lon"], hospital["lat"]),
            srid=4326
        )
        print(f"   {person.name} → {hospital['name']}")

    db.commit()
    print(f"✅ {len(personnel)} personal actualizado")


def create_patients(db, num_patients=75):
    """Crear 75 pacientes distribuidos en las comunas"""
    print(f"\n🏠 Creando {num_patients} pacientes en región de Valparaíso...")
    patients = []

    # Obtener RUTs existentes para evitar duplicados
    print("   Cargando RUTs existentes...")
    existing_ruts = set()
    all_patients = db.query(Patient.rut).filter(Patient.rut.isnot(None)).all()
    for (rut,) in all_patients:
        if rut:
            # Almacenar RUT limpio (sin puntos ni guiones)
            clean = rut.replace('.', '').replace('-', '')
            existing_ruts.add(clean)
    print(f"   {len(existing_ruts)} RUTs existentes en la base de datos")

    # Distribuir pacientes proporcionalmente por tamaño de comuna
    # Más pacientes en comunas más grandes (Viña, Quilpué, Villa Alemana, Quillota)
    comuna_weights = {
        "Viña del Mar": 20,
        "Quilpué": 12,
        "Villa Alemana": 10,
        "Quillota": 10,
        "Concón": 6,
        "La Calera": 6,
        "Quintero": 4,
        "La Cruz": 3,
        "Puchuncaví": 2,
        "Nogales": 1,
        "Hijuelas": 1
    }

    # Calcular cuántos pacientes por comuna
    total_weight = sum(comuna_weights.values())
    pacientes_por_comuna = {}

    for comuna, weight in comuna_weights.items():
        pacientes_por_comuna[comuna] = int((weight / total_weight) * num_patients)

    # Ajustar para llegar exactamente a num_patients
    diff = num_patients - sum(pacientes_por_comuna.values())
    if diff > 0:
        # Agregar los faltantes a Viña del Mar
        pacientes_por_comuna["Viña del Mar"] += diff

    # Crear pacientes
    patient_count = 0
    for comuna, count in pacientes_por_comuna.items():
        print(f"   {comuna}: {count} pacientes")
        for _ in range(count):
            first_name = random.choice(FIRST_NAMES)
            last_name1 = random.choice(LAST_NAMES)
            last_name2 = random.choice(LAST_NAMES)

            # Generar RUT único
            rut = generate_unique_rut(db, existing_ruts)
            existing_ruts.add(rut)

            patient = Patient(
                rut=rut,
                name=f"{first_name} {last_name1} {last_name2}",
                phone=random_phone(),
                email=random_email(first_name, last_name1),
                address=random_address_in_comuna(comuna),
                location=from_shape(random_location_in_comuna(comuna), srid=4326),
                notes=f"Paciente {patient_count + 1} - {comuna} - Región de Valparaíso"
            )
            db.add(patient)
            patients.append(patient)
            patient_count += 1

    db.commit()
    print(f"✅ {len(patients)} pacientes creados en Valparaíso con RUTs únicos")
    return patients


def create_cases_for_date(db, patients, target_date):
    """Crear casos para la fecha especificada"""
    print(f"\n📋 Creando casos para {target_date.strftime('%d/%m/%Y')}...")

    # Obtener tipos de atención existentes
    care_types = db.query(CareType).all()
    if not care_types:
        print("❌ Error: No hay tipos de atención en la base de datos")
        print("   Ejecuta primero: python scripts/seed_database.py")
        return []

    cases = []

    # Crear un caso por cada paciente (75 casos)
    for i, patient in enumerate(patients):
        care_type = random.choice(care_types)

        # Distribución de prioridades (mayoría medium/high para casos reales)
        priority_weights = [
            (CasePriority.LOW, 5),
            (CasePriority.MEDIUM, 50),
            (CasePriority.HIGH, 35),
            (CasePriority.URGENT, 10)
        ]
        priority = random.choices(
            [p[0] for p in priority_weights],
            weights=[p[1] for p in priority_weights]
        )[0]

        # Distribución de ventanas horarias
        time_window_weights = [
            (TimeWindowType.AM, 35),
            (TimeWindowType.PM, 35),
            (TimeWindowType.SPECIFIC, 20),
            (TimeWindowType.ANYTIME, 10)
        ]
        time_window_type = random.choices(
            [t[0] for t in time_window_weights],
            weights=[t[1] for t in time_window_weights]
        )[0]

        # Configurar ventanas horarias
        if time_window_type == TimeWindowType.AM:
            time_window_start = datetime.combine(target_date, time(8, 0))
            time_window_end = datetime.combine(target_date, time(12, 0))
        elif time_window_type == TimeWindowType.PM:
            time_window_start = datetime.combine(target_date, time(12, 0))
            time_window_end = datetime.combine(target_date, time(17, 0))
        elif time_window_type == TimeWindowType.SPECIFIC:
            # Ventana específica de 2 horas
            start_hour = random.choice([8, 9, 10, 11, 13, 14, 15])
            time_window_start = datetime.combine(target_date, time(start_hour, 0))
            time_window_end = datetime.combine(target_date, time(start_hour + 2, 0))
        else:  # ANYTIME
            time_window_start = datetime.combine(target_date, time(8, 0))
            time_window_end = datetime.combine(target_date, time(17, 0))

        case = Case(
            patient_id=patient.id,
            care_type_id=care_type.id,
            scheduled_date=datetime.combine(target_date, time(9, 0)),
            time_window_type=time_window_type,
            time_window_start=time_window_start,
            time_window_end=time_window_end,
            location=patient.location,
            priority=priority,
            status=CaseStatus.PENDING,
            notes=f"Caso Valparaíso {i+1} - {care_type.name}",
            estimated_duration_minutes=care_type.estimated_duration_minutes
        )
        db.add(case)
        cases.append(case)

    db.commit()
    print(f"✅ {len(cases)} casos creados para {target_date.strftime('%d/%m/%Y')}")
    return cases


def print_summary(patients, cases, target_date):
    """Imprimir resumen de datos creados"""
    print("\n" + "="*70)
    print("📊 RESUMEN DE DATOS CREADOS - REGIÓN DE VALPARAÍSO")
    print("="*70)
    print(f"✅ Pacientes nuevos: {len(patients)}")
    print(f"✅ Casos nuevos: {len(cases)}")
    print(f"📅 Fecha de casos: {target_date.strftime('%d de %B de %Y')}")
    print("="*70)

    # Distribución por comuna
    print("\n🏘️  Pacientes por comuna:")
    comunas_count = {}
    for patient in patients:
        comuna = patient.address.split(",")[1].strip() if "," in patient.address else "Unknown"
        comunas_count[comuna] = comunas_count.get(comuna, 0) + 1

    for comuna, count in sorted(comunas_count.items(), key=lambda x: x[1], reverse=True):
        print(f"   {comuna}: {count}")

    # Prioridades
    print("\n📋 Casos por prioridad:")
    priorities = {}
    for case in cases:
        priorities[case.priority] = priorities.get(case.priority, 0) + 1

    for priority, count in sorted(priorities.items()):
        print(f"   {priority.value.upper()}: {count}")

    # Ventanas horarias
    print("\n⏰ Casos por ventana horaria:")
    time_windows = {}
    for case in cases:
        time_windows[case.time_window_type] = time_windows.get(case.time_window_type, 0) + 1

    for tw, count in sorted(time_windows.items()):
        print(f"   {tw.value.upper()}: {count}")

    # Tipos de atención
    print("\n🏥 Casos por tipo de atención:")
    care_types_count = {}
    for case in cases:
        ct_name = case.care_type.name if case.care_type else "Unknown"
        care_types_count[ct_name] = care_types_count.get(ct_name, 0) + 1

    for care_type, count in sorted(care_types_count.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {care_type}: {count}")

    print("\n" + "="*70)
    print("🎉 Datos de Valparaíso creados exitosamente!")
    print("="*70)
    print("\n💡 Próximos pasos:")
    print("   1. Los vehículos y personal ahora parten desde:")
    print("      - Hospital Dr. Gustavo Fricke (Viña del Mar)")
    print("      - Hospital de Quilpué")
    print("      - Hospital Biprovincial Quillota-Petorca")
    print(f"   2. Hay {len(cases)} casos programados para el 20/11/2025")
    print("   3. Ve al panel de administración para optimizar rutas")
    print()


def main():
    """Función principal"""
    print("🌊 CREANDO DATOS DE PRUEBA - REGIÓN DE VALPARAÍSO")
    print("="*70)
    print("📍 Área: Servicio de Salud Viña del Mar Quillota")
    print("🏥 Hospitales base: Gustavo Fricke, Quilpué, Biprovincial")
    print("📅 Fecha objetivo: 20 de noviembre de 2025")
    print("="*70)

    # Crear motor y sesión
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Fecha objetivo: 20 de noviembre de 2025
        target_date = datetime(2025, 11, 20).date()

        # 1. Actualizar vehículos y personal con ubicaciones de hospitales
        update_vehicles_and_personnel(db)

        # 2. Crear 75 pacientes en la región
        patients = create_patients(db, num_patients=75)

        # 3. Crear casos para el 20 de noviembre de 2025
        cases = create_cases_for_date(db, patients, target_date)

        # 4. Imprimir resumen
        print_summary(patients, cases, target_date)

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
