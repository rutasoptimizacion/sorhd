# Phase 1 - Testing Guide

## Database Setup - COMPLETE ✅

The database has been successfully initialized with all tables:
- users, skills, care_types, vehicles, patients, personnel
- cases, routes, visits, personnel_skills, care_type_skills, route_personnel
- location_logs, notifications, audit_logs

## Testing the API

### 1. Wait for Backend to Finish Building

The backend container is currently building and installing all dependencies. Wait for it to complete:

```bash
# Check if backend is healthy
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy", "service": "FlamenGO!-backend"}
```

### 2. View API Documentation

Once the backend is running:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

### 3. Register a Test Admin User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@sorhd.com",
    "password": "admin123456",
    "role": "admin",
    "full_name": "Sistema Administrador"
  }'
```

Expected response:
```json
{
  "username": "admin",
  "email": "admin@sorhd.com",
  "role": "admin",
  "full_name": "Sistema Administrador",
  "id": 1,
  "is_active": true,
  "created_at": "2025-11-15T...",
  "updated_at": "2025-11-15T..."
}
```

### 4. Login and Get Tokens

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123456"
  }'
```

Expected response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 5. Get Current User Info (Protected Route)

```bash
# Replace YOUR_ACCESS_TOKEN with the token from step 4
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Expected response:
```json
{
  "username": "admin",
  "email": "admin@sorhd.com",
  "role": "admin",
  "full_name": "Sistema Administrador",
  "id": 1,
  "is_active": true,
  "created_at": "2025-11-15T...",
  "updated_at": "2025-11-15T..."
}
```

### 6. Refresh Access Token

```bash
# Replace YOUR_REFRESH_TOKEN with the refresh_token from step 4
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

Expected response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

## Verify Database Tables

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U sorhd_user -d sorhd

# List all tables
\dt

# View users table structure
\d users

# View some PostGIS info
SELECT PostGIS_Version();

# Exit psql
\q
```

## Check Logs

```bash
# Backend logs
docker-compose logs backend --tail=50

# Follow logs in real-time
docker-compose logs -f backend

# Database logs
docker-compose logs postgres --tail=50
```

## Troubleshooting

### Backend Not Responding

```bash
# Check container status
docker-compose ps

# Restart backend
docker-compose restart backend

# Rebuild if needed
docker-compose up -d --build backend
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
docker-compose exec postgres psql -U sorhd_user -d sorhd -c "SELECT 1;"

# Check PostGIS extension
docker-compose exec postgres psql -U sorhd_user -d sorhd -c "SELECT PostGIS_Version();"
```

### View All Services Status

```bash
docker-compose ps
```

## Next Steps

After successful Phase 1 testing:

1. ✅ All authentication endpoints working
2. ✅ Database schema created
3. ✅ JWT tokens generated correctly
4. ✅ Role-based access control functional

**Ready to proceed to Phase 2: Resource Management**
- CRUD operations for Personnel
- CRUD operations for Vehicles
- CRUD operations for Patients
- CRUD operations for Cases
- Care Type and Skill management

## Quick Commands Reference

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f backend

# Rebuild backend
docker-compose up -d --build backend

# Connect to database
docker-compose exec postgres psql -U sorhd_user -d sorhd

# Run Alembic migration
docker-compose exec backend alembic upgrade head
```
