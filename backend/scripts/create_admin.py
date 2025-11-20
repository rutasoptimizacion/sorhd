#!/usr/bin/env python3
"""
Script to create an initial admin user for FlamenGO!

Usage:
    python scripts/create_admin.py

Default credentials:
    Username: admin
    Password: admin123
    Role: admin
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import os

from app.core.database import Base
from app.core.security import hash_password
from app.models.user import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Get database URL from environment or use default
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://sorhd_user:sorhd_password@localhost:5432/sorhd"
)


def create_admin_user():
    """Create an admin user if it doesn't exist"""

    # Create engine and session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Check if admin user exists
        existing_user = db.query(User).filter(User.username == "admin").first()

        if existing_user:
            print("⚠️  Usuario 'admin' ya existe en la base de datos.")
            print(f"   ID: {existing_user.id}")
            print(f"   Nombre: {existing_user.full_name}")
            print(f"   Rol: {existing_user.role}")
            return

        # Create admin user
        admin_user = User(
            username="admin",
            full_name="Administrador",
            password_hash=hash_password("admin123"),
            role="admin",
            is_active=True,
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print("✅ Usuario administrador creado exitosamente!")
        print()
        print("📝 Credenciales de acceso:")
        print("   Usuario: admin")
        print("   Contraseña: admin123")
        print()
        print("⚠️  IMPORTANTE: Cambia la contraseña después del primer login")

    except Exception as e:
        db.rollback()
        print(f"❌ Error al crear usuario: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    print("🔐 Creando usuario administrador...")
    print()
    create_admin_user()
