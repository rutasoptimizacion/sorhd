#!/usr/bin/env python3
"""
Simple script to create an admin user directly with SQL

Usage:
    python scripts/create_admin_simple.py

Default credentials:
    Username: admin
    Password: admin123
    Role: admin
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import psycopg2
from app.core.security import hash_password
from datetime import datetime

# Get database URL from environment or use default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://sorhd_user:sorhd_password@localhost:5432/sorhd"
)

def parse_postgres_url(url):
    """Parse PostgreSQL URL"""
    # Format: postgresql://user:password@host:port/database
    url = url.replace("postgresql://", "")
    user_pass, host_port_db = url.split("@")
    user, password = user_pass.split(":")
    host_port, database = host_port_db.split("/")
    host, port = host_port.split(":")

    return {
        "host": host,
        "port": int(port),
        "user": user,
        "password": password,
        "database": database
    }

def create_admin_user():
    """Create an admin user if it doesn't exist"""

    db_params = parse_postgres_url(DATABASE_URL)
    conn = None

    try:
        # Connect to database
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        # Check if admin user exists
        cur.execute("SELECT id, username, full_name, role FROM users WHERE username = %s", ("admin",))
        existing_user = cur.fetchone()

        if existing_user:
            print("⚠️  Usuario 'admin' ya existe en la base de datos.")
            print(f"   ID: {existing_user[0]}")
            print(f"   Usuario: {existing_user[1]}")
            print(f"   Nombre: {existing_user[2]}")
            print(f"   Rol: {existing_user[3]}")
            return

        # Hash password
        password_hash = hash_password("admin123")

        # Get current timestamp
        now = datetime.utcnow()

        # Insert admin user (only basic fields that exist in Phase 1)
        cur.execute("""
            INSERT INTO users (username, email, password_hash, role, full_name, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, ("admin", "admin@example.com", password_hash, "admin", "Administrador", 1, now, now))

        conn.commit()

        print("✅ Usuario administrador creado exitosamente!")
        print()
        print("📝 Credenciales de acceso:")
        print("   Usuario: admin")
        print("   Contraseña: admin123")
        print()
        print("⚠️  IMPORTANTE: Cambia la contraseña después del primer login")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error al crear usuario: {e}")
        sys.exit(1)
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    print("🔐 Creando usuario administrador...")
    print()
    create_admin_user()
