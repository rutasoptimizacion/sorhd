#!/bin/bash
# Database Initialization Script

set -e

echo "🔄 Waiting for PostgreSQL to be ready..."
until pg_isready -h ${DATABASE_HOST:-postgres} -U ${DATABASE_USER:-sorhd_user}; do
  echo "Waiting for postgres..."
  sleep 2
done

echo "✅ PostgreSQL is ready!"

echo "🔄 Creating PostGIS extension..."
PGPASSWORD=${DATABASE_PASSWORD:-sorhd_password} psql -h ${DATABASE_HOST:-postgres} -U ${DATABASE_USER:-sorhd_user} -d ${DATABASE_NAME:-sorhd} <<-EOSQL
  CREATE EXTENSION IF NOT EXISTS postgis;
  CREATE EXTENSION IF NOT EXISTS postgis_topology;
EOSQL

echo "✅ PostGIS extension created!"

echo "🔄 Running Alembic migrations..."
alembic upgrade head

echo "✅ Database initialized successfully!"
