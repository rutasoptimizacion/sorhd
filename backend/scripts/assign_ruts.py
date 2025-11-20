#!/usr/bin/env python3
"""
Assign RUTs Script

Este script asigna RUTs válidos chilenos a pacientes que no tienen RUT asignado.
Genera RUTs aleatorios válidos con dígito verificador correcto y verifica unicidad.

Uso:
    python scripts/assign_ruts.py [--dry-run] [--count N]

Ejemplos:
    # Asignar RUTs a todos los pacientes sin RUT
    python scripts/assign_ruts.py

    # Simular sin guardar cambios
    python scripts/assign_ruts.py --dry-run

    # Asignar RUTs solo a los primeros 10 pacientes
    python scripts/assign_ruts.py --count 10

    # Combinar dry-run con límite
    python scripts/assign_ruts.py --dry-run --count 5
"""

import sys
import os
from pathlib import Path
import argparse
import random

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import SessionLocal
from app.models.patient import Patient


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


def format_rut(rut_number: int, verifier: str) -> str:
    """
    Formatea un RUT en el formato estándar 12.345.678-9

    Args:
        rut_number: Número del RUT
        verifier: Dígito verificador

    Returns:
        RUT formateado con puntos y guión
    """
    rut_str = str(rut_number)
    # Add dots for thousands separator
    formatted = ''
    for i, digit in enumerate(reversed(rut_str)):
        if i > 0 and i % 3 == 0:
            formatted = '.' + formatted
        formatted = digit + formatted

    return f"{formatted}-{verifier}"


def generate_unique_rut(db: Session, existing_ruts: set) -> tuple[int, str, str]:
    """
    Genera un RUT válido único que no existe en la base de datos.

    Args:
        db: Sesión de base de datos
        existing_ruts: Set de RUTs ya existentes para verificación rápida

    Returns:
        Tupla de (rut_number, verifier, formatted_rut)
    """
    max_attempts = 100

    for _ in range(max_attempts):
        # Generate random RUT between 5,000,000 and 25,000,000
        rut_number = random.randint(5_000_000, 25_000_000)
        verifier = calculate_rut_verifier(rut_number)
        formatted_rut = format_rut(rut_number, verifier)
        clean_rut = f"{rut_number}{verifier}"

        # Check if RUT already exists in our set
        if clean_rut not in existing_ruts:
            # Double-check in database
            existing = db.query(Patient).filter(
                or_(
                    Patient.rut == clean_rut,
                    Patient.rut == formatted_rut
                )
            ).first()

            if not existing:
                return rut_number, verifier, clean_rut

    raise RuntimeError("No se pudo generar un RUT único después de 100 intentos")


def assign_ruts(
    db: Session,
    dry_run: bool = False,
    count: int = None
) -> dict:
    """
    Asigna RUTs válidos a pacientes sin RUT.

    Args:
        db: Sesión de base de datos
        dry_run: Si es True, simula sin guardar cambios
        count: Límite de pacientes a procesar (None = todos)

    Returns:
        Diccionario con estadísticas de la operación
    """
    print("=" * 60)
    print("ASIGNACIÓN DE RUTs CHILENOS A PACIENTES")
    print("=" * 60)
    print()

    # Get patients without RUT
    query = db.query(Patient).filter(
        or_(
            Patient.rut.is_(None),
            Patient.rut == ''
        )
    )

    if count:
        query = query.limit(count)

    patients = query.all()

    if not patients:
        print("✓ No hay pacientes sin RUT.")
        return {
            "total_patients": 0,
            "assigned": 0,
            "errors": 0
        }

    print(f"Pacientes sin RUT encontrados: {len(patients)}")

    if dry_run:
        print("\n⚠️  MODO DRY-RUN: No se guardarán cambios en la base de datos\n")

    # Get all existing RUTs for quick lookup
    existing_ruts = set()
    all_patients = db.query(Patient.rut).filter(Patient.rut.isnot(None)).all()
    for (rut,) in all_patients:
        if rut:
            # Store cleaned RUT (remove dots and hyphens)
            clean = rut.replace('.', '').replace('-', '')
            existing_ruts.add(clean)

    # Assign RUTs
    assigned = 0
    errors = 0

    print(f"\nAsignando RUTs...\n")

    for i, patient in enumerate(patients, 1):
        try:
            # Generate unique RUT
            rut_number, verifier, clean_rut = generate_unique_rut(db, existing_ruts)
            formatted_rut = format_rut(rut_number, verifier)

            print(f"[{i}/{len(patients)}] {patient.name:30s} → {formatted_rut}")

            if not dry_run:
                # Assign RUT (store cleaned version)
                patient.rut = clean_rut
                existing_ruts.add(clean_rut)

            assigned += 1

        except Exception as e:
            print(f"[{i}/{len(patients)}] ERROR para {patient.name}: {e}")
            errors += 1

    # Commit changes if not dry-run
    if not dry_run and assigned > 0:
        try:
            db.commit()
            print(f"\n✓ Cambios guardados en la base de datos")
        except Exception as e:
            db.rollback()
            print(f"\n✗ Error al guardar cambios: {e}")
            return {
                "total_patients": len(patients),
                "assigned": 0,
                "errors": len(patients)
            }

    # Summary
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Pacientes procesados:  {len(patients)}")
    print(f"RUTs asignados:        {assigned}")
    print(f"Errores:               {errors}")

    if dry_run:
        print("\n⚠️  Modo dry-run: Los cambios NO fueron guardados")

    print()

    return {
        "total_patients": len(patients),
        "assigned": assigned,
        "errors": errors
    }


def main():
    """Main function to run the script"""
    parser = argparse.ArgumentParser(
        description="Asigna RUTs válidos chilenos a pacientes sin RUT"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simular sin guardar cambios en la base de datos'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=None,
        help='Número máximo de pacientes a procesar (por defecto: todos)'
    )

    args = parser.parse_args()

    # Create database session
    db = SessionLocal()

    try:
        result = assign_ruts(
            db=db,
            dry_run=args.dry_run,
            count=args.count
        )

        # Exit with error code if there were errors
        if result['errors'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"\n✗ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
