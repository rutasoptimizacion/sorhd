# FlamenGO! Backend

Sistema de Optimización de Rutas para Hospitalización Domiciliaria - Backend API

## Quick Start

### Using Docker (Recommended)

1. **Start all services:**
   ```bash
   cd /Users/carlosroa1/projects/hackaton_min_ciencia/hdroutes
   docker-compose up --build
   ```

2. **Access the API:**
   - API Docs: http://localhost:8000/api/docs
   - Health Check: http://localhost:8000/health

3. **Initialize the database (first time only):**
   ```bash
   # Create migration
   docker-compose exec backend alembic revision --autogenerate -m "Initial schema"

   # Apply migration
   docker-compose exec backend alembic upgrade head
   ```

### Manual Setup (Alternative)

1. **Install Python 3.11+**

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Start PostgreSQL with PostGIS:**
   ```bash
   docker run -d \
     -p 5432:5432 \
     -e POSTGRES_DB=sorhd \
     -e POSTGRES_USER=sorhd_user \
     -e POSTGRES_PASSWORD=sorhd_password \
     postgis/postgis:15-3.4
   ```

6. **Initialize PostGIS extension:**
   ```bash
   psql -h localhost -U sorhd_user -d sorhd -c "CREATE EXTENSION IF NOT EXISTS postgis;"
   ```

7. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

8. **Start the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/logout` - Logout

### Example: Register Admin User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@sorhd.com",
    "password": "admin123456",
    "role": "admin",
    "full_name": "Administrator"
  }'
```

### Example: Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123456"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### Example: Authenticated Request

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Project Structure

```
backend/
├── alembic/              # Database migrations
├── app/
│   ├── api/             # API endpoints
│   │   └── v1/          # API version 1
│   ├── core/            # Core configuration
│   │   ├── config.py    # Settings
│   │   ├── database.py  # DB connection
│   │   ├── security.py  # Auth utilities
│   │   ├── dependencies.py # FastAPI dependencies
│   │   └── exceptions.py   # Custom exceptions
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   └── main.py          # FastAPI app
├── scripts/             # Utility scripts
├── tests/               # Unit & integration tests
├── .env                 # Environment variables (git-ignored)
├── .env.example         # Example environment file
├── alembic.ini          # Alembic configuration
├── requirements.txt     # Python dependencies
└── Dockerfile           # Docker configuration
```

## Database Models

- **User** - Authentication and user management
- **Personnel** - Healthcare workers with skills and locations
- **Skill** - Healthcare skills (e.g., physician, nurse)
- **Vehicle** - Vehicles with capacity and resources
- **Patient** - Patient records with locations
- **Case** - Visit requests with time windows and priorities
- **CareType** - Types of care with skill requirements
- **Route** - Optimized daily routes
- **Visit** - Individual visits in routes
- **LocationLog** - GPS tracking data
- **Notification** - Push/SMS notifications
- **AuditLog** - Audit trail

## User Roles

- **admin** - Full system access
- **clinical_team** - Access to assigned routes and visits
- **patient** - View own visit status and tracking

## Environment Variables

See `.env.example` for all configuration options.

Key variables:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT signing key (change in production!)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Access token lifetime
- `ALLOWED_ORIGINS` - CORS allowed origins

## Development

### Create a new migration

```bash
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

### Run tests

```bash
pytest tests/ --cov=app
```

### Code formatting

```bash
black app/
flake8 app/
```

## Troubleshooting

### Database connection errors

1. Ensure PostgreSQL is running
2. Check DATABASE_URL in .env
3. Verify PostGIS extension is installed:
   ```sql
   SELECT PostGIS_version();
   ```

### Import errors

Make sure you're in the virtual environment:
```bash
source venv/bin/activate
```

## Next Steps

Phase 1 (Backend Foundation) is complete. Next:

- **Phase 2:** Implement CRUD operations for all resources
- **Phase 3:** Add distance calculation and geospatial services
- **Phase 4:** Implement route optimization engine

See `CHECKLIST.md` for the complete implementation roadmap.

## License

[Your License Here]

## Support

For issues and questions, see the main project README.
