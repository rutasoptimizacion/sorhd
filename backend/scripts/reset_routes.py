#!/usr/bin/env python3
"""
Reset Routes Script

Este script elimina todas las rutas existentes y resetea el estado de los casos
asociados de 'assigned' a 'pending' para que puedan ser reasignados.

Las relaciones en cascada eliminarán automáticamente:
- route_personnel (asociaciones ruta-personal)
- visits (visitas de cada ruta)

Uso:
    python scripts/reset_routes.py [--date YYYY-MM-DD] [--status STATUS] [--all]

Ejemplos:
    # Eliminar todas las rutas
    python scripts/reset_routes.py --all

    # Eliminar rutas de una fecha específica
    python scripts/reset_routes.py --date 2025-11-17

    # Eliminar rutas con un status específico
    python scripts/reset_routes.py --status draft

    # Eliminar rutas de una fecha con un status específico
    python scripts/reset_routes.py --date 2025-11-17 --status draft
"""

import sys
import os
from pathlib import Path
import argparse
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.route import Route, RouteStatus, Visit as VisitModel, RoutePersonnel
from app.models.case import Case


def reset_routes(
    db: Session,
    date: str = None,
    status: str = None,
    delete_all: bool = False,
    auto_confirm: bool = False
) -> dict:
    """
    Elimina rutas según los criterios especificados y resetea los casos asociados.

    Args:
        db: Database session
        date: Fecha de las rutas (YYYY-MM-DD) o None para todas
        status: Estado de las rutas o None para todos
        delete_all: Si es True, elimina todas las rutas sin preguntar
        auto_confirm: Si es True, no pide confirmación

    Returns:
        dict con estadísticas de la operación
    """
    # Build query
    query = db.query(Route)

    # Apply filters
    if date:
        try:
            route_date = datetime.strptime(date, "%Y-%m-%d").date()
            query = query.filter(Route.route_date == route_date)
        except ValueError:
            print(f"❌ Error: Formato de fecha inválido '{date}'. Use YYYY-MM-DD")
            return {"error": "Invalid date format"}

    if status:
        try:
            route_status = RouteStatus(status)
            query = query.filter(Route.status == route_status)
        except ValueError:
            valid_statuses = [s.value for s in RouteStatus]
            print(f"❌ Error: Status inválido '{status}'. Valores válidos: {', '.join(valid_statuses)}")
            return {"error": "Invalid status"}

    # Get routes to delete
    routes = query.all()

    if not routes:
        print("ℹ️  No se encontraron rutas que coincidan con los criterios.")
        return {
            "deleted_routes": 0,
            "deleted_visits": 0,
            "reset_cases": 0
        }

    # Show summary
    print(f"\n{'='*60}")
    print(f"RESUMEN DE RUTAS A ELIMINAR")
    print(f"{'='*60}")
    print(f"Total de rutas: {len(routes)}")

    # Group by status
    status_count = {}
    for route in routes:
        status_count[route.status] = status_count.get(route.status, 0) + 1

    print("\nPor estado:")
    for status, count in status_count.items():
        print(f"  - {status.value}: {count}")

    # Count visits and cases
    total_visits = 0
    case_ids = set()
    for route in routes:
        total_visits += len(route.visits)
        for visit in route.visits:
            case_ids.add(visit.case_id)

    print(f"\nTotal de visitas a eliminar: {total_visits}")
    print(f"Total de casos a resetear: {len(case_ids)}")
    print(f"{'='*60}\n")

    # Confirm deletion
    if not delete_all and not auto_confirm:
        confirm = input("¿Desea continuar con la eliminación? (s/n): ")
        if confirm.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
            print("❌ Operación cancelada.")
            return {
                "deleted_routes": 0,
                "deleted_visits": 0,
                "reset_cases": 0,
                "cancelled": True
            }

    # Collect case IDs from all visits before deletion
    print("\n📋 Recolectando casos asociados...")
    cases_to_reset = set()
    for route in routes:
        for visit in route.visits:
            cases_to_reset.add(visit.case_id)

    # Delete routes and their relationships manually
    print(f"🗑️  Eliminando {len(routes)} rutas y sus relaciones...")
    deleted_count = 0

    try:
        for route in routes:
            # Delete visits first
            db.query(VisitModel).filter(VisitModel.route_id == route.id).delete()

            # Delete route_personnel associations
            db.query(RoutePersonnel).filter(RoutePersonnel.route_id == route.id).delete()

            # Now delete the route itself
            db.delete(route)
            deleted_count += 1

        # Commit all deletions
        db.commit()
        print(f"✅ {deleted_count} rutas eliminadas correctamente")

    except Exception as e:
        print(f"❌ Error al eliminar rutas: {e}")
        db.rollback()
        return {"error": f"Failed to delete routes: {str(e)}"}

    # Reset case statuses from 'assigned' to 'pending'
    print(f"\n🔄 Reseteando {len(cases_to_reset)} casos a estado 'pending'...")
    reset_count = 0
    for case_id in cases_to_reset:
        case = db.query(Case).filter(Case.id == case_id).first()
        if case and case.status == "assigned":
            case.status = "pending"
            reset_count += 1

    try:
        db.commit()
        print(f"✅ {reset_count} casos reseteados a 'pending'")
    except Exception as e:
        print(f"❌ Error al resetear casos: {e}")
        db.rollback()
        return {"error": "Failed to reset cases"}

    print(f"\n{'='*60}")
    print("✅ OPERACIÓN COMPLETADA EXITOSAMENTE")
    print(f"{'='*60}")

    return {
        "deleted_routes": deleted_count,
        "deleted_visits": total_visits,
        "reset_cases": reset_count
    }


def main():
    parser = argparse.ArgumentParser(
        description="Eliminar rutas y resetear casos asociados",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Eliminar todas las rutas
  python scripts/reset_routes.py --all

  # Eliminar rutas de una fecha específica (con confirmación automática)
  python scripts/reset_routes.py --date 2025-11-17 --yes

  # Eliminar rutas con estado 'draft' (con confirmación automática)
  python scripts/reset_routes.py --status draft -y

  # Eliminar rutas de fecha y estado específicos
  python scripts/reset_routes.py --date 2025-11-17 --status draft --yes

Estados válidos: draft, active, in_progress, completed, cancelled
        """
    )

    parser.add_argument(
        "--date",
        help="Fecha de las rutas a eliminar (YYYY-MM-DD)"
    )

    parser.add_argument(
        "--status",
        choices=["draft", "active", "in_progress", "completed", "cancelled"],
        help="Estado de las rutas a eliminar"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Eliminar todas las rutas sin preguntar"
    )

    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Confirmar automáticamente sin pedir confirmación (útil para Docker)"
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.all and not args.date and not args.status:
        parser.print_help()
        print("\n❌ Error: Debe especificar --all, --date, o --status")
        sys.exit(1)

    # Create database session
    db = SessionLocal()

    try:
        result = reset_routes(
            db=db,
            date=args.date,
            status=args.status,
            delete_all=args.all,
            auto_confirm=args.yes
        )

        if "error" in result:
            sys.exit(1)
        elif result.get("cancelled"):
            sys.exit(0)
        else:
            print(f"\nResumen:")
            print(f"  - Rutas eliminadas: {result['deleted_routes']}")
            print(f"  - Visitas eliminadas: {result['deleted_visits']}")
            print(f"  - Casos reseteados: {result['reset_cases']}")

    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
