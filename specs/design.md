# Sistema de Optimización de Rutas para Hospitalización Domiciliaria (FlamenGO!)
## System Design Document

**Version:** 1.0
**Date:** 2025-11-14
**Status:** Draft
**Related Documents:** requirements.md

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Component Design](#3-component-design)
4. [Data Model](#4-data-model)
5. [API Specifications](#5-api-specifications)
6. [Technology Stack](#6-technology-stack)
7. [Security Design](#7-security-design)
8. [Deployment Architecture](#8-deployment-architecture)
9. [Optimization Algorithm Design](#9-optimization-algorithm-design)
10. [User Interface Design](#10-user-interface-design)
11. [Performance and Scalability](#11-performance-and-scalability)
12. [Error Handling and Recovery](#12-error-handling-and-recovery)
13. [Testing Strategy](#13-testing-strategy)
14. [Traceability to Requirements](#14-traceability-to-requirements)

---

## 1. Executive Summary

This document describes the system design for FlamenGO!, a route optimization platform for home hospitalization services. The design implements a three-tier architecture with:

- **Backend**: Python-based REST API with optimization engine
- **Web Admin Panel**: React.js administrative interface
- **Mobile Application**: React Native hybrid app for clinical teams and patients

The system optimizes daily visit routes considering personnel skills, vehicle capacity, time windows, and geographic constraints to minimize travel time and maximize clinical care delivery.

### 1.1 Design Goals

- **Modularity**: Independent, loosely-coupled components
- **Scalability**: Support for growing user base and data volume
- **Reliability**: 99% uptime with graceful degradation
- **Performance**: Sub-60-second route optimization for 50 cases
- **Extensibility**: Easy addition of new features and integrations
- **Security**: Healthcare-grade data protection

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        External Services                         │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐     │
│  │ Google Maps │  │ FCM/APNS     │  │ SMS Gateway        │     │
│  │ / OSRM      │  │ (Push Notif) │  │ (Twilio/AWS SNS)   │     │
│  └─────────────┘  └──────────────┘  └────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ HTTPS/API
                              │
┌─────────────────────────────┼───────────────────────────────────┐
│                        Backend Layer                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              API Gateway (FastAPI/Flask)                 │   │
│  │  - Authentication & Authorization                        │   │
│  │  - Rate Limiting                                         │   │
│  │  - Request Validation                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌───────────────┬───────────┴────────┬──────────────────────┐  │
│  │               │                    │                      │  │
│  ▼               ▼                    ▼                      ▼  │
│  ┌──────────┐  ┌────────────┐  ┌──────────────┐  ┌────────────┐│
│  │ Resource │  │Optimization│  │ Route        │  │Notification││
│  │ Manager  │  │ Engine     │  │ Tracker      │  │ Service    ││
│  │ Module   │  │ Module     │  │ Module       │  │ Module     ││
│  └──────────┘  └────────────┘  └──────────────┘  └────────────┘│
│  │               │                    │                      │  │
│  └───────────────┴───────────┬────────┴──────────────────────┘  │
│                              │                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │               Data Access Layer (ORM)                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │       PostgreSQL + PostGIS (Database)                    │   │
│  │  - Relational Data                                       │   │
│  │  - Geospatial Extensions                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │       Redis Cache (Optional)                             │   │
│  │  - Session Management                                    │   │
│  │  - Distance Matrix Cache                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
                              ▲
                              │ REST API (HTTPS)
            ┌─────────────────┴─────────────────┐
            │                                   │
┌───────────▼──────────────┐       ┌───────────▼────────────────┐
│   Admin Panel (Web)      │       │  Mobile App (React Native) │
│   - React.js SPA         │       │  - Clinical Team Profile   │
│   - Resource Management  │       │  - Patient Profile         │
│   - Route Planning       │       │  - GPS Tracking            │
│   - Live Monitoring      │       │  - Offline Support         │
└──────────────────────────┘       └────────────────────────────┘
```

### 2.2 Architecture Principles

**Separation of Concerns**: Each module has a single, well-defined responsibility.

**API-First Design**: All functionality exposed through RESTful API endpoints, enabling multiple client types.

**Stateless Backend**: Backend services are stateless for horizontal scalability. State is managed in database and cache.

**Asynchronous Processing**: Long-running operations (optimization) use async processing with job queues.

**Offline-First Mobile**: Mobile app caches data locally for offline operation during network interruptions.

**Event-Driven Updates**: Real-time updates use WebSocket/Server-Sent Events for live tracking.

### 2.3 Communication Patterns

- **Client-Server**: REST API for CRUD operations and commands
- **Publish-Subscribe**: Real-time GPS updates and notifications
- **Request-Response**: Synchronous API calls for immediate operations
- **Job Queue**: Asynchronous optimization processing (optional: Celery + Redis)

---

## 3. Component Design

### 3.1 Backend Components

#### 3.1.1 API Gateway

**Responsibilities**:
- Route HTTP requests to appropriate modules
- Authentication and authorization
- Input validation and sanitization
- Rate limiting and throttling
- Error handling and response formatting
- API versioning

**Technology**: FastAPI (recommended) or Flask

**Key Features**:
- JWT-based authentication
- Role-based access control (Admin, Clinical Team, Patient)
- OpenAPI/Swagger documentation auto-generation
- Request/response middleware chain

**Endpoints Structure**:
```
/api/v1/
  /auth/
    POST /login
    POST /logout
    POST /refresh-token
  /personnel/
    GET    /personnel
    POST   /personnel
    GET    /personnel/{id}
    PUT    /personnel/{id}
    DELETE /personnel/{id}
  /vehicles/
    GET    /vehicles
    POST   /vehicles
    GET    /vehicles/{id}
    PUT    /vehicles/{id}
    DELETE /vehicles/{id}
  /cases/
    GET    /cases
    POST   /cases
    GET    /cases/{id}
    PUT    /cases/{id}
    DELETE /cases/{id}
  /routes/
    POST   /routes/optimize
    GET    /routes/{id}
    GET    /routes/active
    PATCH  /routes/{id}/status
  /tracking/
    POST   /tracking/location
    GET    /tracking/vehicle/{id}
    WS     /tracking/live
  /notifications/
    POST   /notifications/send
```

#### 3.1.2 Resource Manager Module

**Responsibilities**:
- CRUD operations for Personnel, Vehicles, Cases
- Data validation and business rules enforcement
- Referential integrity checks
- Audit logging

**Design Pattern**: Repository Pattern with Service Layer

**Key Classes**:
```python
# Service Layer
class PersonnelService:
    def create_personnel(data: PersonnelCreateDTO) -> Personnel
    def update_personnel(id: int, data: PersonnelUpdateDTO) -> Personnel
    def delete_personnel(id: int) -> bool
    def get_personnel(id: int) -> Personnel
    def list_personnel(filters: dict) -> List[Personnel]
    def validate_skills(skills: List[str]) -> bool

class VehicleService:
    def create_vehicle(data: VehicleCreateDTO) -> Vehicle
    def update_vehicle(id: int, data: VehicleUpdateDTO) -> Vehicle
    def delete_vehicle(id: int) -> bool
    def get_vehicle(id: int) -> Vehicle
    def list_vehicles(filters: dict) -> List[Vehicle]
    def validate_coordinates(lat: float, lon: float) -> bool

class CaseService:
    def create_case(data: CaseCreateDTO) -> Case
    def update_case(id: int, data: CaseUpdateDTO) -> Case
    def delete_case(id: int) -> bool
    def get_case(id: int) -> Case
    def list_cases(filters: dict) -> List[Case]
    def validate_time_window(window: TimeWindow) -> bool

# Repository Layer
class PersonnelRepository:
    def save(personnel: Personnel) -> Personnel
    def find_by_id(id: int) -> Optional[Personnel]
    def find_all(filters: dict) -> List[Personnel]
    def delete(id: int) -> bool

# Similar repositories for Vehicle, Case
```

#### 3.1.3 Optimization Engine Module

**Responsibilities**:
- Route optimization algorithm execution
- Constraint satisfaction (skills, time windows, capacity)
- Objective function minimization (distance, time)
- Feasibility checking

**Design Pattern**: Strategy Pattern (multiple optimization algorithms)

**Key Components**:

```python
# Domain Models
@dataclass
class OptimizationRequest:
    date: datetime
    cases: List[Case]
    personnel: List[Personnel]
    vehicles: List[Vehicle]
    distance_matrix: DistanceMatrix

@dataclass
class OptimizationResult:
    routes: List[Route]
    total_distance: float
    total_time: float
    unassigned_cases: List[Case]
    warnings: List[str]

@dataclass
class Route:
    vehicle_id: int
    personnel_ids: List[int]
    visits: List[Visit]  # Ordered list
    total_distance: float
    estimated_duration: float

@dataclass
class Visit:
    case_id: int
    arrival_time: datetime
    departure_time: datetime
    travel_time_from_previous: float

# Optimization Strategy Interface
class OptimizationStrategy(ABC):
    @abstractmethod
    def optimize(request: OptimizationRequest) -> OptimizationResult:
        pass

# Concrete Implementations
class ORToolsVRPStrategy(OptimizationStrategy):
    """Uses Google OR-Tools Vehicle Routing Problem solver"""
    def optimize(request: OptimizationRequest) -> OptimizationResult:
        # Implementation using OR-Tools
        pass

class HeuristicStrategy(OptimizationStrategy):
    """Faster heuristic approach for quick solutions"""
    def optimize(request: OptimizationRequest) -> OptimizationResult:
        # Nearest neighbor + 2-opt improvement
        pass

# Optimization Service
class OptimizationService:
    def __init__(self, strategy: OptimizationStrategy):
        self.strategy = strategy

    def optimize_routes(request: OptimizationRequest) -> OptimizationResult:
        # Validate request
        # Build distance matrix (cache if available)
        # Execute optimization
        # Persist results
        # Return result
        pass
```

**Algorithm Selection**:
- **Primary**: Google OR-Tools VRP solver (powerful, handles complex constraints)
- **Fallback**: Custom heuristic (nearest neighbor + local search)
- **Future**: Machine learning-based prediction for visit durations

#### 3.1.4 Route Tracker Module

**Responsibilities**:
- Store and update active route status
- Track vehicle GPS positions in real-time
- Calculate ETA for next visits
- Detect delays and trigger notifications

**Design Pattern**: Observer Pattern for real-time updates

**Key Components**:

```python
class RouteTrackerService:
    def update_vehicle_location(vehicle_id: int, location: Location) -> None
    def update_visit_status(visit_id: int, status: VisitStatus) -> None
    def get_active_routes() -> List[ActiveRoute]
    def get_vehicle_location(vehicle_id: int) -> Location
    def calculate_eta(vehicle_id: int, destination: Location) -> datetime
    def detect_delays(route_id: int) -> List[Delay]

class LocationTracker:
    """Real-time location tracking with WebSocket support"""
    def subscribe_to_vehicle(vehicle_id: int, callback: Callable)
    def unsubscribe(vehicle_id: int, callback: Callable)
    def broadcast_location_update(vehicle_id: int, location: Location)

class ETACalculator:
    def __init__(self, distance_service: DistanceService):
        self.distance_service = distance_service

    def calculate(current_location: Location,
                 destination: Location,
                 current_time: datetime) -> datetime:
        # Get travel time from distance service
        # Add buffer based on time of day
        # Return estimated arrival time
        pass
```

#### 3.1.5 Notification Service Module

**Responsibilities**:
- Send push notifications to mobile apps
- Send SMS fallback notifications
- Manage notification templates
- Track notification delivery status

**Design Pattern**: Template Method Pattern for notification types

**Key Components**:

```python
class NotificationService:
    def __init__(self,
                push_provider: PushNotificationProvider,
                sms_provider: SMSProvider):
        self.push_provider = push_provider
        self.sms_provider = sms_provider

    def send_notification(
        user_id: int,
        notification_type: NotificationType,
        data: dict
    ) -> NotificationResult:
        # Try push notification first
        # Fallback to SMS if push fails
        # Log delivery status
        pass

class PushNotificationProvider(ABC):
    @abstractmethod
    def send(device_token: str, title: str, body: str, data: dict) -> bool
        pass

class FCMProvider(PushNotificationProvider):
    """Firebase Cloud Messaging for Android"""
    def send(device_token: str, title: str, body: str, data: dict) -> bool:
        # FCM implementation
        pass

class APNSProvider(PushNotificationProvider):
    """Apple Push Notification Service for iOS"""
    def send(device_token: str, title: str, body: str, data: dict) -> bool:
        # APNS implementation
        pass

class SMSProvider(ABC):
    @abstractmethod
    def send(phone_number: str, message: str) -> bool:
        pass

class TwilioSMSProvider(SMSProvider):
    def send(phone_number: str, message: str) -> bool:
        # Twilio implementation
        pass
```

#### 3.1.6 Distance Service Module

**Responsibilities**:
- Calculate distances and travel times between locations
- Cache distance matrix for performance
- Handle multiple geocoding providers
- Fallback to haversine distance if API unavailable

**Design Pattern**: Adapter Pattern for multiple providers

**Key Components**:

```python
class DistanceService:
    def __init__(self,
                provider: DistanceProvider,
                cache: CacheService):
        self.provider = provider
        self.cache = cache

    def get_distance_matrix(
        origins: List[Location],
        destinations: List[Location]
    ) -> DistanceMatrix:
        # Check cache first
        # If not cached, call provider
        # Cache result
        # Return matrix
        pass

class DistanceProvider(ABC):
    @abstractmethod
    def calculate_matrix(
        origins: List[Location],
        destinations: List[Location]
    ) -> DistanceMatrix:
        pass

class GoogleMapsProvider(DistanceProvider):
    def calculate_matrix(...) -> DistanceMatrix:
        # Google Maps Distance Matrix API
        pass

class OSRMProvider(DistanceProvider):
    def calculate_matrix(...) -> DistanceMatrix:
        # Open Source Routing Machine API
        pass

class HaversineProvider(DistanceProvider):
    """Fallback provider using great-circle distance"""
    def calculate_matrix(...) -> DistanceMatrix:
        # Calculate haversine distance
        # Estimate time based on average speed
        pass
```

### 3.2 Admin Panel (Web)

#### 3.2.1 Architecture

**Framework**: React.js 18+ with functional components and hooks

**State Management**:
- **Global State**: Redux Toolkit or Zustand for application state
- **Server State**: React Query for API data caching and synchronization
- **Form State**: React Hook Form for form management

**Routing**: React Router v6

**UI Framework**: Material-UI (MUI) or Ant Design

**Map Library**: Leaflet or Google Maps JavaScript API

#### 3.2.2 Component Structure

```
src/
├── components/
│   ├── common/
│   │   ├── Layout.tsx
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   ├── DataTable.tsx
│   │   └── Map.tsx
│   ├── personnel/
│   │   ├── PersonnelList.tsx
│   │   ├── PersonnelForm.tsx
│   │   └── PersonnelDetail.tsx
│   ├── vehicles/
│   │   ├── VehicleList.tsx
│   │   ├── VehicleForm.tsx
│   │   └── VehicleDetail.tsx
│   ├── cases/
│   │   ├── CaseList.tsx
│   │   ├── CaseForm.tsx
│   │   └── CaseDetail.tsx
│   ├── routes/
│   │   ├── RoutePlanner.tsx
│   │   ├── RouteOptimizer.tsx
│   │   ├── RouteVisualization.tsx
│   │   └── RouteList.tsx
│   └── monitoring/
│       ├── LiveMap.tsx
│       ├── VehicleTracker.tsx
│       └── StatusDashboard.tsx
├── hooks/
│   ├── useAuth.ts
│   ├── useWebSocket.ts
│   └── useGeolocation.ts
├── services/
│   ├── api.ts
│   ├── auth.ts
│   └── websocket.ts
├── store/
│   ├── authSlice.ts
│   ├── routeSlice.ts
│   └── store.ts
├── types/
│   └── index.ts
└── App.tsx
```

#### 3.2.3 Key Features

**Resource Management**:
- CRUD operations with data tables
- Form validation
- Confirmation dialogs for deletions
- Inline editing where appropriate

**Route Planning Interface**:
- Date picker for planning date
- Multi-select for cases, personnel, vehicles
- "Optimize" button triggering backend calculation
- Loading state during optimization
- Results display with sortable/filterable table
- Map visualization of routes

**Live Monitoring**:
- Real-time map with vehicle markers
- WebSocket connection for live updates
- Vehicle status indicators
- Visit completion timeline
- Alert panel for delays/issues

### 3.3 Mobile Application

#### 3.3.1 Architecture

**Framework**: React Native (supports iOS and Android)

**Navigation**: React Navigation

**State Management**:
- Redux Toolkit for global state
- React Query for server state
- AsyncStorage for persistence

**Offline Support**:
- Redux Persist for state persistence
- Custom sync mechanism for offline changes

**Location Tracking**:
- react-native-geolocation-service
- Background location updates

**Push Notifications**:
- react-native-firebase for FCM (Android)
- Native APNS integration (iOS)

#### 3.3.2 Component Structure

```
src/
├── screens/
│   ├── auth/
│   │   ├── LoginScreen.tsx
│   │   └── ProfileScreen.tsx
│   ├── team/
│   │   ├── RouteListScreen.tsx
│   │   ├── RouteDetailScreen.tsx
│   │   ├── VisitDetailScreen.tsx
│   │   └── NavigationScreen.tsx
│   └── patient/
│       ├── VisitStatusScreen.tsx
│       ├── TrackingScreen.tsx
│       └── NotificationsScreen.tsx
├── components/
│   ├── common/
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   └── StatusBadge.tsx
│   ├── MapView.tsx
│   ├── VisitCard.tsx
│   └── StatusTimeline.tsx
├── services/
│   ├── api.ts
│   ├── location.ts
│   ├── notifications.ts
│   └── sync.ts
├── hooks/
│   ├── useLocation.ts
│   ├── useOfflineSync.ts
│   └── useNotifications.ts
├── store/
│   ├── authSlice.ts
│   ├── routeSlice.ts
│   ├── locationSlice.ts
│   └── store.ts
└── navigation/
    └── AppNavigator.tsx
```

#### 3.3.3 Key Features

**Clinical Team Profile**:
- Route list with visit cards
- Status update buttons (En Route, Started, Completed, Cancelled)
- Navigation integration (deep link to Google/Apple Maps)
- Background GPS tracking with minimal battery impact
- Offline mode with sync queue

**Patient Profile**:
- Visit status card
- Live tracking map (when vehicle en route)
- ETA display with automatic updates
- Push notification handling
- Simple, accessible UI

**Offline Handling**:
- Cache route data locally
- Queue status updates when offline
- Sync automatically when connection restored
- Visual indicator of offline state

---

## 4. Data Model

### 4.1 Entity-Relationship Diagram

```
┌─────────────────┐         ┌──────────────────┐
│   Personnel     │         │    Skill         │
├─────────────────┤         ├──────────────────┤
│ id (PK)         │────┐    │ id (PK)          │
│ name            │    │    │ name             │
│ email           │    │    │ description      │
│ phone           │    │    └──────────────────┘
│ start_location  │    │            ▲
│ work_hours      │    │            │
│ created_at      │    │    ┌───────┴──────────┐
│ updated_at      │    │    │ PersonnelSkill   │
└─────────────────┘    │    ├──────────────────┤
                       └───▶│ personnel_id (FK)│
                            │ skill_id (FK)    │
┌─────────────────┐         └──────────────────┘
│    Vehicle      │
├─────────────────┤         ┌──────────────────┐
│ id (PK)         │         │ VehicleResource  │
│ identifier      │         ├──────────────────┤
│ capacity        │         │ id (PK)          │
│ base_location   │◀───────▶│ vehicle_id (FK)  │
│ status          │         │ resource_name    │
│ created_at      │         │ description      │
│ updated_at      │         └──────────────────┘
└─────────────────┘
        │
        │
        ▼
┌─────────────────┐
│     Route       │
├─────────────────┤         ┌──────────────────┐
│ id (PK)         │         │ RoutePersonnel   │
│ vehicle_id (FK) │         ├──────────────────┤
│ date            │◀───────▶│ route_id (FK)    │
│ status          │         │ personnel_id(FK) │
│ total_distance  │         └──────────────────┘
│ total_time      │
│ created_at      │         ┌──────────────────┐
│ updated_at      │         │    Patient       │
└─────────────────┘         ├──────────────────┤
        │                   │ id (PK)          │
        │                   │ name             │
        ▼                   │ phone            │
┌─────────────────┐         │ email            │
│     Visit       │         │ address          │
├─────────────────┤         │ location         │
│ id (PK)         │         │ created_at       │
│ route_id (FK)   │         │ updated_at       │
│ case_id (FK)    │         └──────────────────┘
│ sequence        │                 │
│ arrival_time    │                 │
│ departure_time  │                 ▼
│ status          │         ┌──────────────────┐
│ created_at      │         │      Case        │
│ updated_at      │         ├──────────────────┤
└─────────────────┘         │ id (PK)          │
                            │ patient_id (FK)  │
┌─────────────────┐         │ care_type_id(FK) │
│   CareType      │         │ location         │
├─────────────────┤         │ time_window_start│
│ id (PK)         │◀────────│ time_window_end  │
│ name            │         │ duration_minutes │
│ description     │         │ priority         │
│ duration_est    │         │ status           │
└─────────────────┘         │ created_at       │
        │                   │ updated_at       │
        │                   └──────────────────┘
        ▼
┌─────────────────┐
│CareTypeSkill    │
├─────────────────┤         ┌──────────────────┐
│care_type_id(FK) │         │   LocationLog    │
│ skill_id (FK)   │         ├──────────────────┤
└─────────────────┘         │ id (PK)          │
                            │ vehicle_id (FK)  │
┌─────────────────┐         │ location         │
│      User       │         │ timestamp        │
├─────────────────┤         │ accuracy         │
│ id (PK)         │         └──────────────────┘
│ username        │
│ password_hash   │         ┌──────────────────┐
│ email           │         │  Notification    │
│ role            │         ├──────────────────┤
│ personnel_id(FK)│         │ id (PK)          │
│ patient_id (FK) │         │ user_id (FK)     │
│ created_at      │         │ type             │
│ updated_at      │         │ title            │
│ last_login      │         │ message          │
└─────────────────┘         │ data             │
                            │ sent_at          │
                            │ read_at          │
                            │ delivery_status  │
                            └──────────────────┘
```

### 4.2 Database Schema (PostgreSQL)

```sql
-- Enable PostGIS extension for geospatial data
CREATE EXTENSION IF NOT EXISTS postgis;

-- Users and Authentication
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'clinical_team', 'patient')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Skills
CREATE TABLE skills (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Personnel
CREATE TABLE personnel (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    start_location GEOGRAPHY(POINT, 4326) NOT NULL,
    work_hours_start TIME NOT NULL DEFAULT '08:00:00',
    work_hours_end TIME NOT NULL DEFAULT '17:00:00',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE personnel_skills (
    personnel_id INTEGER REFERENCES personnel(id) ON DELETE CASCADE,
    skill_id INTEGER REFERENCES skills(id) ON DELETE CASCADE,
    PRIMARY KEY (personnel_id, skill_id)
);

-- Vehicles
CREATE TABLE vehicles (
    id SERIAL PRIMARY KEY,
    identifier VARCHAR(100) UNIQUE NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    base_location GEOGRAPHY(POINT, 4326) NOT NULL,
    status VARCHAR(50) DEFAULT 'available' CHECK (status IN ('available', 'in_use', 'maintenance', 'unavailable')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE vehicle_resources (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES vehicles(id) ON DELETE CASCADE,
    resource_name VARCHAR(100) NOT NULL,
    description TEXT
);

-- Patients
CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Care Types
CREATE TABLE care_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    estimated_duration_minutes INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE care_type_skills (
    care_type_id INTEGER REFERENCES care_types(id) ON DELETE CASCADE,
    skill_id INTEGER REFERENCES skills(id) ON DELETE CASCADE,
    PRIMARY KEY (care_type_id, skill_id)
);

-- Cases
CREATE TABLE cases (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    care_type_id INTEGER REFERENCES care_types(id) ON DELETE RESTRICT,
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    time_window_start TIME,
    time_window_end TIME,
    duration_minutes INTEGER,
    priority INTEGER DEFAULT 1 CHECK (priority BETWEEN 1 AND 5),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'scheduled', 'in_progress', 'completed', 'cancelled')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Routes
CREATE TABLE routes (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES vehicles(id) ON DELETE RESTRICT,
    date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'planned' CHECK (status IN ('planned', 'in_progress', 'completed', 'cancelled')),
    total_distance_km DECIMAL(10, 2),
    total_time_minutes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vehicle_id, date)
);

CREATE TABLE route_personnel (
    route_id INTEGER REFERENCES routes(id) ON DELETE CASCADE,
    personnel_id INTEGER REFERENCES personnel(id) ON DELETE CASCADE,
    PRIMARY KEY (route_id, personnel_id)
);

-- Visits
CREATE TABLE visits (
    id SERIAL PRIMARY KEY,
    route_id INTEGER REFERENCES routes(id) ON DELETE CASCADE,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,
    sequence INTEGER NOT NULL,
    estimated_arrival_time TIMESTAMP,
    estimated_departure_time TIMESTAMP,
    actual_arrival_time TIMESTAMP,
    actual_departure_time TIMESTAMP,
    status VARCHAR(50) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'en_route', 'started', 'completed', 'cancelled')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(route_id, sequence)
);

-- Location Tracking
CREATE TABLE location_logs (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES vehicles(id) ON DELETE CASCADE,
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    accuracy_meters DECIMAL(10, 2),
    speed_kmh DECIMAL(10, 2),
    heading_degrees INTEGER
);

CREATE INDEX idx_location_logs_vehicle_time ON location_logs(vehicle_id, timestamp DESC);
CREATE INDEX idx_location_logs_geo ON location_logs USING GIST(location);

-- Notifications
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL CHECK (type IN ('route_assigned', 'eta_update', 'visit_completed', 'delay_alert', 'general')),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    data JSONB,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP,
    delivery_status VARCHAR(50) DEFAULT 'pending' CHECK (delivery_status IN ('pending', 'sent', 'delivered', 'failed'))
);

CREATE INDEX idx_notifications_user ON notifications(user_id, sent_at DESC);

-- Distance Matrix Cache (Optional)
CREATE TABLE distance_cache (
    id SERIAL PRIMARY KEY,
    origin GEOGRAPHY(POINT, 4326) NOT NULL,
    destination GEOGRAPHY(POINT, 4326) NOT NULL,
    distance_km DECIMAL(10, 2) NOT NULL,
    duration_minutes INTEGER NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX idx_distance_cache_locations ON distance_cache USING GIST(origin, destination);

-- Audit Log
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id INTEGER,
    changes JSONB,
    ip_address INET,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_user_time ON audit_logs(user_id, timestamp DESC);
```

### 4.3 Data Types and Validation

**Location Data**:
- Stored as PostGIS GEOGRAPHY type (POINT, 4326 = WGS 84)
- Latitude: -90 to +90
- Longitude: -180 to +180
- Validation at application layer and database constraint

**Time Windows**:
- Stored as TIME type (hour:minute:second)
- Business logic validates start < end
- Supports both specific windows ("10:00-12:00") and general ("AM" = 08:00-12:00)

**Status Enums**:
- Defined as CHECK constraints in database
- Also defined as application-level enums for type safety

**JSONB Fields**:
- Used for flexible data (notification data, audit changes)
- Indexed where needed for query performance

---

## 5. API Specifications

### 5.1 API Design Principles

- RESTful conventions
- JSON request/response bodies
- HTTP status codes for semantics
- Versioned API path (/api/v1)
- Pagination for list endpoints
- Filtering and sorting query parameters
- JWT authentication with Bearer tokens
- Consistent error response format

### 5.2 Authentication Endpoints

#### POST /api/v1/auth/login

**Request**:
```json
{
  "username": "string",
  "password": "string"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "username": "coordinator1",
    "email": "coord@hospital.cl",
    "role": "admin"
  }
}
```

**Errors**:
- 401 Unauthorized: Invalid credentials
- 400 Bad Request: Missing fields

#### POST /api/v1/auth/refresh-token

**Request**:
```json
{
  "refresh_token": "string"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### 5.3 Personnel Endpoints

#### GET /api/v1/personnel

**Query Parameters**:
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)
- `skill`: Filter by skill name
- `is_active`: Filter by active status (true/false)

**Response** (200 OK):
```json
{
  "data": [
    {
      "id": 1,
      "name": "Dr. María González",
      "email": "maria.gonzalez@hospital.cl",
      "phone": "+56912345678",
      "start_location": {
        "lat": -33.4489,
        "lon": -70.6693
      },
      "work_hours": {
        "start": "08:00:00",
        "end": "17:00:00"
      },
      "skills": ["physician", "geriatrics"],
      "is_active": true,
      "created_at": "2025-01-15T10:00:00Z",
      "updated_at": "2025-01-15T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 45,
    "pages": 3
  }
}
```

#### POST /api/v1/personnel

**Request**:
```json
{
  "name": "Dr. Juan Pérez",
  "email": "juan.perez@hospital.cl",
  "phone": "+56987654321",
  "start_location": {
    "lat": -33.4489,
    "lon": -70.6693
  },
  "work_hours": {
    "start": "09:00:00",
    "end": "18:00:00"
  },
  "skills": ["kinesiologist"]
}
```

**Response** (201 Created):
```json
{
  "id": 2,
  "name": "Dr. Juan Pérez",
  ...
}
```

**Errors**:
- 400 Bad Request: Invalid data
- 401 Unauthorized: Not authenticated
- 403 Forbidden: Insufficient permissions

#### GET /api/v1/personnel/{id}

**Response** (200 OK): Single personnel object

#### PUT /api/v1/personnel/{id}

**Request**: Same as POST (partial updates allowed)

**Response** (200 OK): Updated personnel object

#### DELETE /api/v1/personnel/{id}

**Response** (204 No Content)

**Errors**:
- 409 Conflict: Personnel assigned to active routes

### 5.4 Vehicle Endpoints

Similar CRUD pattern as Personnel with endpoints:
- GET /api/v1/vehicles
- POST /api/v1/vehicles
- GET /api/v1/vehicles/{id}
- PUT /api/v1/vehicles/{id}
- DELETE /api/v1/vehicles/{id}

### 5.5 Case Endpoints

Similar CRUD pattern with endpoints:
- GET /api/v1/cases
- POST /api/v1/cases
- GET /api/v1/cases/{id}
- PUT /api/v1/cases/{id}
- DELETE /api/v1/cases/{id}

### 5.6 Route Optimization Endpoints

#### POST /api/v1/routes/optimize

**Request**:
```json
{
  "date": "2025-11-15",
  "case_ids": [1, 2, 3, 4, 5],
  "vehicle_ids": [1, 2],
  "personnel_assignments": [
    {
      "vehicle_id": 1,
      "personnel_ids": [1, 3]
    },
    {
      "vehicle_id": 2,
      "personnel_ids": [2]
    }
  ],
  "options": {
    "algorithm": "ortools",
    "max_duration_minutes": 480,
    "balance_routes": true
  }
}
```

**Response** (200 OK):
```json
{
  "routes": [
    {
      "id": 101,
      "vehicle_id": 1,
      "personnel_ids": [1, 3],
      "visits": [
        {
          "case_id": 1,
          "sequence": 1,
          "estimated_arrival": "2025-11-15T08:30:00Z",
          "estimated_departure": "2025-11-15T09:00:00Z",
          "travel_time_from_previous": 15
        },
        {
          "case_id": 3,
          "sequence": 2,
          "estimated_arrival": "2025-11-15T09:20:00Z",
          "estimated_departure": "2025-11-15T09:50:00Z",
          "travel_time_from_previous": 20
        }
      ],
      "total_distance_km": 45.2,
      "total_time_minutes": 240,
      "status": "planned"
    }
  ],
  "unassigned_cases": [],
  "warnings": [],
  "optimization_time_seconds": 12.5
}
```

**Errors**:
- 400 Bad Request: Invalid input
- 422 Unprocessable Entity: No feasible solution

#### GET /api/v1/routes

**Query Parameters**:
- `date`: Filter by date
- `status`: Filter by status
- `vehicle_id`: Filter by vehicle

**Response**: List of routes

#### GET /api/v1/routes/{id}

**Response**: Single route with full details

#### PATCH /api/v1/routes/{id}/status

**Request**:
```json
{
  "status": "in_progress"
}
```

**Response** (200 OK): Updated route

### 5.7 Tracking Endpoints

#### POST /api/v1/tracking/location

**Request**:
```json
{
  "vehicle_id": 1,
  "location": {
    "lat": -33.4500,
    "lon": -70.6650
  },
  "timestamp": "2025-11-15T10:30:00Z",
  "accuracy_meters": 10.5,
  "speed_kmh": 45.0,
  "heading_degrees": 180
}
```

**Response** (201 Created):
```json
{
  "id": 12345,
  "recorded_at": "2025-11-15T10:30:01Z"
}
```

#### GET /api/v1/tracking/vehicle/{id}

**Query Parameters**:
- `since`: ISO timestamp (default: last 5 minutes)

**Response** (200 OK):
```json
{
  "vehicle_id": 1,
  "current_location": {
    "lat": -33.4500,
    "lon": -70.6650
  },
  "last_updated": "2025-11-15T10:30:00Z",
  "speed_kmh": 45.0,
  "heading_degrees": 180,
  "recent_path": [
    {"lat": -33.4489, "lon": -70.6693, "timestamp": "2025-11-15T10:25:00Z"},
    {"lat": -33.4495, "lon": -70.6670, "timestamp": "2025-11-15T10:28:00Z"},
    {"lat": -33.4500, "lon": -70.6650, "timestamp": "2025-11-15T10:30:00Z"}
  ]
}
```

#### WebSocket: /api/v1/tracking/live

**Connection**: `wss://api.example.com/api/v1/tracking/live?token=<jwt>`

**Subscribe Message**:
```json
{
  "action": "subscribe",
  "vehicle_ids": [1, 2, 3]
}
```

**Location Update Message (from server)**:
```json
{
  "type": "location_update",
  "vehicle_id": 1,
  "location": {
    "lat": -33.4500,
    "lon": -70.6650
  },
  "timestamp": "2025-11-15T10:30:00Z",
  "speed_kmh": 45.0
}
```

### 5.8 Notification Endpoints

#### POST /api/v1/notifications/send

**Request**:
```json
{
  "user_ids": [10, 11],
  "type": "eta_update",
  "title": "ETA Update",
  "message": "El equipo médico llegará en 15 minutos",
  "data": {
    "visit_id": 123,
    "eta": "2025-11-15T11:00:00Z"
  }
}
```

**Response** (200 OK):
```json
{
  "notifications_sent": 2,
  "failed": []
}
```

### 5.9 Error Response Format

All errors follow this structure:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": [
      {
        "field": "location.lat",
        "message": "Latitude must be between -90 and 90"
      }
    ]
  }
}
```

**Common Error Codes**:
- `VALIDATION_ERROR`: Invalid input data
- `AUTHENTICATION_FAILED`: Invalid or missing credentials
- `AUTHORIZATION_FAILED`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `CONFLICT`: Resource conflict (e.g., duplicate)
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Server error

---

## 6. Technology Stack

### 6.1 Backend

| Component | Technology | Justification |
|-----------|-----------|---------------|
| **Runtime** | Python 3.11+ | Excellent ecosystem for optimization, data science, and web APIs |
| **Web Framework** | FastAPI | Modern, fast, automatic OpenAPI docs, async support, type hints |
| **ORM** | SQLAlchemy | Mature, flexible, supports PostGIS |
| **Database** | PostgreSQL 15+ | Robust, ACID compliant, excellent geospatial support |
| **Geospatial** | PostGIS | Industry standard for geospatial data |
| **Optimization** | OR-Tools | Google's powerful optimization library, handles VRP well |
| **Authentication** | PyJWT + Passlib | JWT tokens with bcrypt password hashing |
| **Validation** | Pydantic | Type-safe data validation, integrated with FastAPI |
| **Task Queue** | Celery (optional) | Async processing for long-running optimizations |
| **Message Broker** | Redis (optional) | For Celery, caching, and real-time features |
| **Testing** | pytest + httpx | Comprehensive testing framework |

**Key Python Packages**:
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
geoalchemy2==0.14.2
pydantic==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
ortools==9.8.3296
httpx==0.25.1
pytest==7.4.3
redis==5.0.1
celery==5.3.4
```

### 6.2 Admin Panel (Web)

| Component | Technology | Justification |
|-----------|-----------|---------------|
| **Framework** | React 18 | Industry standard, large ecosystem, excellent performance |
| **Build Tool** | Vite | Fast development server, optimized production builds |
| **Language** | TypeScript | Type safety, better developer experience |
| **State Management** | Redux Toolkit | Predictable state management, great DevTools |
| **Server State** | React Query | Caching, synchronization, automatic refetching |
| **Routing** | React Router v6 | Standard routing solution |
| **UI Library** | Material-UI (MUI) | Professional components, accessibility, theming |
| **Maps** | Leaflet + React-Leaflet | Open source, flexible, good performance |
| **Forms** | React Hook Form | Performant, simple API, validation support |
| **HTTP Client** | Axios | Simple, interceptors for auth, wide adoption |
| **WebSocket** | Socket.io-client | Reliable real-time communication |
| **Testing** | Vitest + React Testing Library | Fast, modern testing |

**Key npm Packages**:
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "@reduxjs/toolkit": "^2.0.1",
    "react-redux": "^9.0.4",
    "@tanstack/react-query": "^5.12.2",
    "@mui/material": "^5.15.0",
    "@mui/x-data-grid": "^6.18.5",
    "react-leaflet": "^4.2.1",
    "leaflet": "^1.9.4",
    "react-hook-form": "^7.49.2",
    "axios": "^1.6.2",
    "socket.io-client": "^4.5.4",
    "date-fns": "^3.0.0"
  },
  "devDependencies": {
    "typescript": "^5.3.3",
    "vite": "^5.0.7",
    "vitest": "^1.0.4",
    "@testing-library/react": "^14.1.2"
  }
}
```

### 6.3 Mobile Application

| Component | Technology | Justification |
|-----------|-----------|---------------|
| **Framework** | React Native 0.73+ | Cross-platform, large community, reuse React knowledge |
| **Language** | TypeScript | Type safety |
| **Navigation** | React Navigation v6 | Standard navigation library |
| **State Management** | Redux Toolkit | Consistent with web app |
| **Persistence** | AsyncStorage | Built-in key-value storage |
| **Maps** | react-native-maps | Native map components for iOS/Android |
| **Location** | react-native-geolocation | Background location tracking |
| **Push Notifications** | @react-native-firebase/messaging | FCM for Android, APNS for iOS |
| **HTTP Client** | Axios | Consistent with web app |
| **Testing** | Jest + React Native Testing Library | Standard testing tools |

**Key npm Packages**:
```json
{
  "dependencies": {
    "react-native": "0.73.0",
    "@react-navigation/native": "^6.1.9",
    "@react-navigation/stack": "^6.3.20",
    "@reduxjs/toolkit": "^2.0.1",
    "react-redux": "^9.0.4",
    "@react-native-async-storage/async-storage": "^1.21.0",
    "react-native-maps": "^1.10.0",
    "@react-native-community/geolocation": "^3.2.1",
    "@react-native-firebase/app": "^19.0.0",
    "@react-native-firebase/messaging": "^19.0.0",
    "axios": "^1.6.2"
  }
}
```

### 6.4 Infrastructure

| Component | Technology | Options |
|-----------|-----------|---------|
| **Hosting** | Cloud Platform | AWS, Google Cloud, Azure, or local datacenter |
| **Application Server** | Uvicorn + Gunicorn | ASGI server with multiple workers |
| **Web Server** | Nginx | Reverse proxy, static file serving, SSL termination |
| **Container** | Docker | Consistent environments, easy deployment |
| **Orchestration** | Docker Compose (initial) | Simple multi-container deployment |
| **CI/CD** | GitHub Actions or GitLab CI | Automated testing and deployment |
| **Monitoring** | Prometheus + Grafana | Metrics and visualization |
| **Logging** | ELK Stack or Loki | Centralized logging |
| **SSL/TLS** | Let's Encrypt | Free, automated certificates |

---

## 7. Security Design

### 7.1 Authentication

**Mechanism**: JWT (JSON Web Tokens)

**Flow**:
1. User submits credentials to `/auth/login`
2. Backend validates credentials against database
3. Backend generates access token (short-lived, 1 hour) and refresh token (long-lived, 7 days)
4. Client stores tokens securely (HttpOnly cookies for web, secure storage for mobile)
5. Client includes access token in Authorization header for subsequent requests
6. When access token expires, client uses refresh token to get new access token

**Token Structure**:
```json
{
  "sub": "user_id",
  "username": "coordinator1",
  "role": "admin",
  "exp": 1699876543,
  "iat": 1699872943
}
```

**Security Measures**:
- Passwords hashed with bcrypt (cost factor: 12)
- Refresh token rotation (new refresh token on each refresh)
- Token blacklisting for logout
- Short expiration for access tokens
- HTTPS required for all authentication endpoints

### 7.2 Authorization

**Model**: Role-Based Access Control (RBAC)

**Roles**:
- **Admin**: Full access to all resources and operations
- **Clinical Team**: Read routes, update visit status, upload location
- **Patient**: Read own visit status, view tracking

**Permission Matrix**:

| Resource | Admin | Clinical Team | Patient |
|----------|-------|---------------|---------|
| Personnel (CRUD) | ✓ | ✗ | ✗ |
| Vehicles (CRUD) | ✓ | ✗ | ✗ |
| Cases (CRUD) | ✓ | ✗ | ✗ |
| Routes (Create/Optimize) | ✓ | ✗ | ✗ |
| Routes (Read) | ✓ | ✓ (own only) | ✗ |
| Visit Status (Update) | ✓ | ✓ (own only) | ✗ |
| Location (Upload) | ✓ | ✓ (own vehicle) | ✗ |
| Visit Tracking (Read) | ✓ | ✓ (own routes) | ✓ (own only) |

**Implementation**:
```python
# Decorator for route protection
@requires_role("admin")
def create_personnel(data: PersonnelCreateDTO):
    ...

@requires_role(["admin", "clinical_team"])
def get_route(route_id: int, current_user: User):
    route = route_service.get(route_id)
    # Clinical team can only see own routes
    if current_user.role == "clinical_team":
        if not route.has_personnel(current_user.personnel_id):
            raise PermissionDenied()
    return route
```

### 7.3 Data Protection

**At Rest**:
- Database encryption (PostgreSQL TDE or encrypted volumes)
- Patient data pseudonymization where possible
- Audit logs for all data access

**In Transit**:
- TLS 1.3 for all API communication
- Certificate pinning in mobile app
- WebSocket over TLS (WSS)

**Personal Data**:
- Minimal data collection (GDPR/privacy principles)
- Data retention policies (e.g., location logs older than 90 days deleted)
- Patient consent management
- Right to erasure support

### 7.4 API Security

**Rate Limiting**:
- Per-user rate limits (e.g., 100 requests/minute for authenticated users)
- Stricter limits for sensitive endpoints (e.g., 5 login attempts/minute)
- IP-based rate limiting for unauthenticated endpoints

**Input Validation**:
- Pydantic models for request validation
- SQL injection prevention (parameterized queries via ORM)
- XSS prevention (sanitize inputs, CSP headers)
- CORS configuration (whitelist trusted origins)

**Additional Measures**:
- API versioning to allow security updates without breaking clients
- Request signing for critical operations (optional)
- Audit logging for all mutations

### 7.5 Mobile Security

**App Security**:
- Certificate pinning to prevent MITM attacks
- Secure storage for tokens (Keychain on iOS, Keystore on Android)
- No sensitive data in logs
- Code obfuscation for release builds
- Jailbreak/root detection (warning only, not blocking)

**Communication Security**:
- All API calls over HTTPS
- Token refresh before expiration
- Automatic logout on token invalidation

---

## 8. Deployment Architecture

### 8.1 Development Environment

```
┌──────────────────────────────────────────┐
│ Developer Machine                         │
│ ┌──────────────┐    ┌─────────────────┐  │
│ │ Docker       │    │ Local           │  │
│ │ Compose      │    │ PostgreSQL      │  │
│ │ - Backend    │◀──▶│ + PostGIS       │  │
│ │ - Admin UI   │    └─────────────────┘  │
│ │   (Vite dev) │                          │
│ └──────────────┘                          │
│                                           │
│ React Native Metro Bundler                │
│ (connects to backend on localhost)        │
└──────────────────────────────────────────┘
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  db:
    image: postgis/postgis:15-3.4
    environment:
      POSTGRES_DB: sorhd_dev
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: devpass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: ./backend
    command: uvicorn main:app --reload --host 0.0.0.0 --port 8000
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql://dev:devpass@db:5432/sorhd_dev
      JWT_SECRET: dev-secret-key
      ENVIRONMENT: development

  admin:
    build: ./admin
    command: npm run dev
    volumes:
      - ./admin:/app
      - /app/node_modules
    ports:
      - "5173:5173"
    environment:
      VITE_API_URL: http://localhost:8000

volumes:
  postgres_data:
```

### 8.2 Production Environment

```
┌─────────────────────────────────────────────────────────────┐
│                         Load Balancer                        │
│                     (Nginx / Cloud LB)                       │
└────────────┬────────────────────────────┬───────────────────┘
             │                            │
             │ HTTPS                      │ HTTPS
             │                            │
┌────────────▼────────────┐  ┌───────────▼────────────────────┐
│   Backend Instances     │  │   Static File Server (CDN)     │
│   (Uvicorn + Gunicorn)  │  │   - Admin Panel (React SPA)    │
│   - Multiple workers    │  │   - Mobile API docs            │
│   - Horizontal scaling  │  └────────────────────────────────┘
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL Cluster                        │
│  ┌──────────────┐         ┌──────────────────────────────┐  │
│  │   Primary    │────────▶│   Replica (Read-only)        │  │
│  │   (Write)    │         │   - Analytics queries        │  │
│  └──────────────┘         │   - Reporting                │  │
│                           └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│   Redis Cluster (Optional)                                   │
│   - Session management                                       │
│   - Distance matrix cache                                    │
│   - Celery broker                                           │
└─────────────────────────────────────────────────────────────┘
```

### 8.3 Deployment Process

**Backend Deployment**:
1. Code pushed to Git repository
2. CI/CD pipeline triggered (GitHub Actions)
3. Run tests (unit, integration)
4. Build Docker image
5. Push image to container registry
6. Deploy to production (blue-green or rolling update)
7. Run database migrations
8. Health check verification

**Admin Panel Deployment**:
1. Build static production bundle (`npm run build`)
2. Upload to static file server or CDN
3. Invalidate cache
4. Verify deployment

**Mobile App Deployment**:
1. Build release APK/IPA
2. Upload to app stores (Google Play, App Store)
3. Staged rollout (e.g., 10% → 50% → 100%)

### 8.4 Infrastructure as Code

**Terraform Example** (AWS):
```hcl
# VPC, Subnets, Security Groups
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

# RDS PostgreSQL with PostGIS
resource "aws_db_instance" "postgres" {
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.medium"
  allocated_storage = 100
  db_name        = "sorhd_prod"
  username       = var.db_username
  password       = var.db_password
}

# ECS Cluster for backend
resource "aws_ecs_cluster" "backend" {
  name = "sorhd-backend"
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "sorhd-alb"
  internal           = false
  load_balancer_type = "application"
  subnets            = aws_subnet.public.*.id
}

# CloudFront for admin panel
resource "aws_cloudfront_distribution" "admin" {
  origin {
    domain_name = aws_s3_bucket.admin.bucket_regional_domain_name
    origin_id   = "admin-panel"
  }
  enabled = true
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "admin-panel"
    viewer_protocol_policy = "redirect-to-https"
  }
}
```

---

## 9. Optimization Algorithm Design

### 9.1 Problem Formulation

**Vehicle Routing Problem with Time Windows and Skills (VRP-TWS)**

**Given**:
- Set of cases C = {c₁, c₂, ..., cₙ}
- Set of vehicles V = {v₁, v₂, ..., vₘ}
- Set of personnel P = {p₁, p₂, ..., pₖ}
- Distance matrix D[i][j] = distance from location i to location j
- Time matrix T[i][j] = travel time from location i to location j

**Constraints**:
- Each case must be visited exactly once
- Each vehicle starts and ends at its base location
- Time windows must be respected: cᵢ.time_window_start ≤ arrival_time ≤ cᵢ.time_window_end
- Personnel skills must match case requirements
- Vehicle capacity must not be exceeded
- Working hours must be respected

**Objectives** (multi-objective):
1. Minimize total travel distance
2. Minimize total travel time
3. Balance workload across vehicles
4. Maximize on-time arrivals within time windows

### 9.2 Algorithm Selection: OR-Tools

**Why OR-Tools**:
- Proven performance on VRP problems
- Handles complex constraints natively
- Good documentation and Python support
- Free and open source

**Implementation Approach**:

```python
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

class ORToolsOptimizer:
    def optimize(self, request: OptimizationRequest) -> OptimizationResult:
        # 1. Build data model
        data = self._build_data_model(request)

        # 2. Create routing index manager
        manager = pywrapcp.RoutingIndexManager(
            len(data['distance_matrix']),
            len(data['vehicles']),
            data['depot']
        )

        # 3. Create routing model
        routing = pywrapcp.RoutingModel(manager)

        # 4. Define cost function (distance)
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return data['distance_matrix'][from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # 5. Add time window constraints
        time_callback_index = routing.RegisterTransitCallback(self._time_callback)
        routing.AddDimension(
            time_callback_index,
            30,  # allow waiting time
            480,  # maximum time per vehicle (8 hours)
            False,  # Don't force start cumul to zero
            'Time'
        )
        time_dimension = routing.GetDimensionOrDie('Time')

        # Add time window constraints for each location
        for location_idx, time_window in enumerate(data['time_windows']):
            if time_window[0] == time_window[1]:
                continue
            index = manager.NodeToIndex(location_idx)
            time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])

        # 6. Add skill constraints (custom constraint)
        # This is a simplification; real implementation would be more complex
        routing.solver().Add(self._build_skill_constraints(routing, manager, data))

        # 7. Add capacity constraints
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return data['demands'][from_node]

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            data['vehicle_capacities'],
            True,  # start cumul to zero
            'Capacity'
        )

        # 8. Set search parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = 30

        # 9. Solve
        solution = routing.SolveWithParameters(search_parameters)

        # 10. Extract solution
        if solution:
            return self._extract_routes(routing, manager, solution, data)
        else:
            return self._handle_infeasible(data)
```

### 9.3 Heuristic Fallback Algorithm

For faster, approximate solutions:

**Nearest Neighbor with Time Windows**:
1. For each vehicle:
   a. Start at depot
   b. Select nearest unvisited case that:
      - Has required skills in vehicle's personnel
      - Fits in time window
      - Doesn't violate capacity
   c. Add to route
   d. Repeat until no more cases can be added
2. Apply 2-opt local search for improvement

**Implementation**:
```python
class NearestNeighborOptimizer:
    def optimize(self, request: OptimizationRequest) -> OptimizationResult:
        routes = []
        unassigned = set(request.cases)

        for vehicle in request.vehicles:
            route = self._build_route_for_vehicle(vehicle, unassigned, request)
            routes.append(route)

        # Improve routes with 2-opt
        routes = [self._two_opt(route) for route in routes]

        return OptimizationResult(
            routes=routes,
            unassigned_cases=list(unassigned),
            ...
        )

    def _build_route_for_vehicle(self, vehicle, unassigned, request):
        route = Route(vehicle_id=vehicle.id)
        current_location = vehicle.base_location
        current_time = datetime.combine(request.date, time(8, 0))

        while unassigned:
            # Find nearest feasible case
            best_case = None
            best_distance = float('inf')

            for case in unassigned:
                if not self._is_feasible(case, vehicle, current_time):
                    continue

                distance = self._calculate_distance(current_location, case.location)
                if distance < best_distance:
                    best_case = case
                    best_distance = distance

            if best_case is None:
                break  # No more feasible cases for this vehicle

            # Add to route
            travel_time = self._calculate_travel_time(current_location, best_case.location)
            arrival_time = current_time + timedelta(minutes=travel_time)
            departure_time = arrival_time + timedelta(minutes=best_case.duration_minutes)

            route.visits.append(Visit(
                case_id=best_case.id,
                arrival_time=arrival_time,
                departure_time=departure_time,
                ...
            ))

            unassigned.remove(best_case)
            current_location = best_case.location
            current_time = departure_time

        return route

    def _two_opt(self, route):
        # 2-opt improvement: try swapping pairs of edges
        improved = True
        while improved:
            improved = False
            for i in range(1, len(route.visits) - 1):
                for j in range(i + 1, len(route.visits)):
                    if self._would_improve(route, i, j):
                        route = self._swap(route, i, j)
                        improved = True
        return route
```

### 9.4 Performance Considerations

**Distance Matrix Caching**:
- Calculate matrix once per day for all locations
- Store in Redis with 24-hour TTL
- Use haversine distance as fallback

**Parallel Processing**:
- For large problems, split into regions
- Solve each region independently
- Merge solutions

**Incremental Updates**:
- When single case added/removed, don't re-optimize from scratch
- Use local adjustments (insert/remove heuristics)

---

## 10. User Interface Design

### 10.1 Admin Panel UI

#### 10.1.1 Main Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Header: FlamenGO! | Search | Notifications | User Menu         │
├──────────┬──────────────────────────────────────────────────┤
│          │                                                   │
│ Sidebar  │            Main Content Area                     │
│          │                                                   │
│ - Panel  │                                                   │
│ - Recur. │                                                   │
│ - Vehícu.│                                                   │
│ - Casos  │                                                   │
│ - Rutas  │                                                   │
│ - Monitor│                                                   │
│          │                                                   │
│          │                                                   │
└──────────┴──────────────────────────────────────────────────┘
```

#### 10.1.2 Route Planner Interface

**Workflow**:
1. Select date
2. Select cases to visit (multi-select table with search/filter)
3. Select available vehicles and personnel
4. Click "Optimize Routes"
5. View results (table + map)
6. Approve and activate routes

**UI Components**:
- Date picker (top)
- Two-column layout:
  - Left: Case selection table (checkboxes)
  - Right: Vehicle/personnel selection
- "Optimize" button (prominent, disabled until selections made)
- Results section (appears below):
  - Summary cards (total distance, time, cost)
  - Route table (expandable rows showing visits)
  - Map with color-coded routes

#### 10.1.3 Live Monitoring Dashboard

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Date: [Today] | Status: [All] | Vehicle: [All]              │
├───────────────────────────┬─────────────────────────────────┤
│                           │                                 │
│         Map               │   Active Routes Panel           │
│  (vehicle markers)        │   ┌──────────────────────────┐  │
│                           │   │ Vehicle 001              │  │
│  [Legend]                 │   │ Status: En Route         │  │
│  🔵 En Route              │   │ Current: Visit 2/5       │  │
│  🟢 At Visit              │   │ ETA Next: 10:30          │  │
│  🔴 Delayed               │   └──────────────────────────┘  │
│  ⚪ Completed             │   ┌──────────────────────────┐  │
│                           │   │ Vehicle 002              │  │
│                           │   │ ...                      │  │
│                           │   └──────────────────────────┘  │
└───────────────────────────┴─────────────────────────────────┘
```

**Real-time Updates**:
- Vehicle markers move on map
- Status badges update automatically
- Alert notifications for delays

### 10.2 Mobile App UI

#### 10.2.1 Clinical Team - Route Screen

```
┌─────────────────────────────────────┐
│ ← Ruta del Día    📅 Nov 15, 2025  │
├─────────────────────────────────────┤
│                                     │
│ ✅ 08:30 - Paciente: María S.      │
│    Dirección: Av. Libertador 123    │
│    Estado: Completada               │
│                                     │
│ ▶ 10:00 - Paciente: Juan P.        │
│    Dirección: Calle San Martín 456  │
│    Estado: En Camino                │
│    [📍 Navegar] [✓ Marcar Llegada] │
│                                     │
│ ⏳ 11:30 - Paciente: Ana G.        │
│    Dirección: Av. Principal 789     │
│    Estado: Pendiente                │
│                                     │
│ ⏳ 14:00 - Paciente: Carlos R.     │
│    ...                              │
│                                     │
└─────────────────────────────────────┘
```

**Interactions**:
- Tap card to expand details
- "Navegar" opens Google/Apple Maps
- Status buttons update backend
- Pull to refresh

#### 10.2.2 Patient - Tracking Screen

```
┌─────────────────────────────────────┐
│ ← Mi Visita                         │
├─────────────────────────────────────┤
│                                     │
│   Su equipo médico está en camino  │
│                                     │
│   🚑                                │
│   Tiempo estimado: 12 minutos       │
│   Llegada aprox: 10:45              │
│                                     │
│   ┌──────────────────────────────┐ │
│   │                              │ │
│   │         Map View             │ │
│   │    (vehicle marker + route)  │ │
│   │                              │ │
│   └──────────────────────────────┘ │
│                                     │
│   Equipo:                           │
│   👨‍⚕️ Dr. Juan Pérez (Médico)    │
│   👩‍⚕️ Ana Torres (TENS)         │
│                                     │
└─────────────────────────────────────┘
```

**Features**:
- Real-time map updates (every 30 seconds)
- ETA countdown
- Team member info
- Simple, reassuring design

---

## 11. Performance and Scalability

### 11.1 Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Route optimization (50 cases) | < 60 seconds | Backend processing time |
| API response time (95th %ile) | < 500ms | All CRUD endpoints |
| Map load time | < 2 seconds | Admin panel, 50 vehicles |
| Mobile app startup | < 3 seconds | Cold start to first screen |
| WebSocket latency | < 1 second | Location update to map display |
| Database queries | < 100ms | 95th percentile |

### 11.2 Scalability Design

**Horizontal Scaling**:
- Stateless backend allows multiple instances behind load balancer
- Database read replicas for reporting and analytics
- CDN for static assets

**Caching Strategy**:
- Distance matrix cache (Redis, 24-hour TTL)
- API response caching for static data (personnel, vehicles)
- Browser caching for admin panel assets

**Database Optimization**:
- Proper indexes on frequently queried fields
- Geospatial indexes on location columns
- Partitioning for large tables (location_logs by month)
- Connection pooling

**Async Processing**:
- Long-running optimizations use Celery task queue
- Notification sending is asynchronous
- Background jobs for cleanup and maintenance

### 11.3 Load Testing

**Scenarios**:
1. 100 concurrent admin users browsing and updating data
2. 50 mobile devices uploading GPS locations every 30 seconds
3. 10 simultaneous route optimization requests
4. WebSocket connections for 100 concurrent live monitoring users

**Tools**:
- Locust for HTTP load testing
- Artillery for WebSocket testing
- pgbench for database performance testing

---

## 12. Error Handling and Recovery

### 12.1 Error Categories

**User Errors** (4xx):
- Invalid input data
- Authentication failures
- Permission denied
- Resource not found

**System Errors** (5xx):
- Database connection failures
- External API failures (maps, notifications)
- Optimization timeouts
- Unexpected exceptions

### 12.2 Error Handling Strategies

**Backend**:
```python
# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, ValidationError):
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request data",
                    "details": exc.errors()
                }
            }
        )

    # Log unexpected errors
    logger.error(f"Unexpected error: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        }
    )

# Service layer error handling
class OptimizationService:
    def optimize_routes(self, request: OptimizationRequest) -> OptimizationResult:
        try:
            result = self.optimizer.optimize(request)
            return result
        except OptimizationTimeout:
            # Fallback to heuristic
            logger.warning("Optimization timeout, using heuristic fallback")
            result = self.heuristic_optimizer.optimize(request)
            result.warnings.append("Used faster algorithm due to timeout")
            return result
        except InfeasibleProblem as e:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "INFEASIBLE_SOLUTION",
                    "message": "Cannot find feasible solution",
                    "constraints": e.violated_constraints
                }
            )
```

**Admin Panel**:
```typescript
// Axios interceptor for error handling
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Token expired, redirect to login
      store.dispatch(logout());
      navigate('/login');
    } else if (error.response?.status === 500) {
      // Show generic error message
      showNotification({
        type: 'error',
        message: 'Ha ocurrido un error. Por favor, intente nuevamente.'
      });
    }
    return Promise.reject(error);
  }
);

// Component error boundary
class ErrorBoundary extends React.Component {
  componentDidCatch(error, errorInfo) {
    // Log to error tracking service
    errorTracker.captureException(error, { extra: errorInfo });

    // Show error UI
    this.setState({ hasError: true });
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback />;
    }
    return this.props.children;
  }
}
```

**Mobile App**:
```typescript
// Offline handling
const syncQueue = [];

const makeAPICall = async (endpoint, data) => {
  if (!isOnline()) {
    // Queue for later
    syncQueue.push({ endpoint, data, timestamp: Date.now() });
    await AsyncStorage.setItem('syncQueue', JSON.stringify(syncQueue));

    // Update local state optimistically
    dispatch(updateLocalState(data));

    return { success: true, queued: true };
  }

  try {
    const response = await axios.post(endpoint, data);
    return response.data;
  } catch (error) {
    if (error.code === 'NETWORK_ERROR') {
      // Queue and retry later
      syncQueue.push({ endpoint, data, timestamp: Date.now() });
      await AsyncStorage.setItem('syncQueue', JSON.stringify(syncQueue));
    }
    throw error;
  }
};

// Sync when back online
NetInfo.addEventListener(state => {
  if (state.isConnected && syncQueue.length > 0) {
    syncQueue.forEach(async item => {
      try {
        await axios.post(item.endpoint, item.data);
        // Remove from queue
        syncQueue.shift();
        await AsyncStorage.setItem('syncQueue', JSON.stringify(syncQueue));
      } catch (error) {
        // Keep in queue, will retry later
        logger.warn('Sync failed for queued item', error);
      }
    });
  }
});
```

### 12.3 Monitoring and Alerting

**Metrics to Monitor**:
- API response times (p50, p95, p99)
- Error rates by endpoint
- Database connection pool utilization
- Optimization success rate
- GPS update frequency
- Notification delivery rate

**Alerting Rules**:
- Error rate > 5% for 5 minutes → Page on-call
- API response time p95 > 2 seconds → Warning
- Database connections > 80% → Warning
- Optimization failures > 20% → Alert
- No GPS updates from vehicle for > 10 minutes → Alert

**Tools**:
- Prometheus for metrics collection
- Grafana for visualization
- PagerDuty or similar for alerting
- Sentry for error tracking

---

## 13. Testing Strategy

### 13.1 Backend Testing

**Unit Tests**:
```python
# Test optimization service
def test_optimization_respects_time_windows():
    cases = [
        Case(id=1, location=Location(-33.45, -70.66),
             time_window=(time(8, 0), time(10, 0))),
        Case(id=2, location=Location(-33.46, -70.67),
             time_window=(time(10, 0), time(12, 0)))
    ]
    vehicle = Vehicle(id=1, base_location=Location(-33.44, -70.65))

    result = optimizer.optimize(OptimizationRequest(
        cases=cases, vehicles=[vehicle], ...
    ))

    assert result.routes[0].visits[0].arrival_time.time() >= time(8, 0)
    assert result.routes[0].visits[0].arrival_time.time() <= time(10, 0)

# Test resource service
def test_cannot_delete_personnel_in_active_route():
    personnel = create_personnel(name="Dr. Test")
    route = create_route(status="in_progress", personnel_ids=[personnel.id])

    with pytest.raises(ConflictError):
        personnel_service.delete(personnel.id)
```

**Integration Tests**:
```python
# Test API endpoints
def test_optimize_route_api(client, auth_headers):
    response = client.post(
        "/api/v1/routes/optimize",
        json={
            "date": "2025-11-15",
            "case_ids": [1, 2, 3],
            "vehicle_ids": [1],
            ...
        },
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["routes"]) > 0
    assert data["routes"][0]["vehicle_id"] == 1
```

**Performance Tests**:
```python
def test_optimization_performance():
    # Generate 50 random cases
    cases = [generate_random_case() for _ in range(50)]
    vehicles = [Vehicle(id=i, ...) for i in range(5)]

    start = time.time()
    result = optimizer.optimize(OptimizationRequest(cases=cases, vehicles=vehicles))
    duration = time.time() - start

    assert duration < 60, f"Optimization took {duration}s, expected < 60s"
```

### 13.2 Frontend Testing

**Component Tests** (React Testing Library):
```typescript
describe('RouteList', () => {
  it('displays routes correctly', () => {
    const routes = [
      { id: 1, vehicle_id: 1, status: 'in_progress', visits: [...] }
    ];

    render(<RouteList routes={routes} />);

    expect(screen.getByText('Vehicle 001')).toBeInTheDocument();
    expect(screen.getByText('In Progress')).toBeInTheDocument();
  });

  it('allows filtering by status', async () => {
    render(<RouteList routes={mockRoutes} />);

    const filter = screen.getByLabelText('Status');
    await userEvent.selectOptions(filter, 'completed');

    expect(screen.queryByText('In Progress')).not.toBeInTheDocument();
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });
});
```

**E2E Tests** (Playwright):
```typescript
test('admin can create and optimize route', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="username"]', 'admin');
  await page.fill('[name="password"]', 'password');
  await page.click('button[type="submit"]');

  await page.goto('/routes/plan');
  await page.selectOption('[name="date"]', '2025-11-15');

  // Select cases
  await page.check('#case-1');
  await page.check('#case-2');

  // Select vehicle
  await page.check('#vehicle-1');

  // Optimize
  await page.click('button:has-text("Optimize Routes")');

  // Wait for results
  await page.waitForSelector('.route-results');

  // Verify
  expect(await page.textContent('.total-distance')).toContain('km');
});
```

### 13.3 Mobile Testing

**Unit Tests** (Jest):
```typescript
describe('locationService', () => {
  it('queues updates when offline', async () => {
    NetInfo.fetch.mockResolvedValue({ isConnected: false });

    await locationService.updateLocation(vehicleId, location);

    const queue = JSON.parse(await AsyncStorage.getItem('syncQueue'));
    expect(queue).toHaveLength(1);
    expect(queue[0].endpoint).toBe('/tracking/location');
  });
});
```

**E2E Tests** (Detox):
```typescript
describe('Clinical Team Flow', () => {
  it('can complete a visit', async () => {
    await device.launchApp();

    // Login
    await element(by.id('username-input')).typeText('team1');
    await element(by.id('password-input')).typeText('password');
    await element(by.id('login-button')).tap();

    // View route
    await element(by.text('Route for Today')).tap();

    // Mark visit as started
    await element(by.id('visit-1')).tap();
    await element(by.text('Mark Started')).tap();

    // Complete visit
    await element(by.text('Mark Completed')).tap();

    // Verify
    await expect(element(by.text('Completed'))).toBeVisible();
  });
});
```

### 13.4 Test Coverage Goals

- Backend: > 80% code coverage
- Frontend (Admin): > 70% code coverage
- Mobile: > 70% code coverage
- Critical paths: 100% coverage (auth, optimization, tracking)

---

## 14. Traceability to Requirements

| Design Element | Requirements Satisfied |
|----------------|------------------------|
| **FastAPI Backend** | REQ-TECH-001, REQ-ARCH-002 |
| **PostgreSQL + PostGIS** | REQ-TECH-003, REQ-DATA-006, REQ-DATA-011 |
| **React Admin Panel** | REQ-TECH-002, REQ-ADMIN-001-013 |
| **React Native Mobile** | REQ-TECH-004, REQ-MOB-001-PAT-006 |
| **JWT Authentication** | REQ-SEC-001, REQ-SEC-002 |
| **HTTPS/TLS** | REQ-SEC-003 |
| **OR-Tools Optimizer** | REQ-OPT-001-007, REQ-PERF-001 |
| **WebSocket Tracking** | REQ-ROUTE-002, REQ-ADMIN-010-013 |
| **Push Notifications** | REQ-NOTIF-001-004 |
| **Offline Support** | REQ-MOB-TEAM-007, REQ-REL-004 |
| **Horizontal Scaling** | REQ-SCALE-001-003 |
| **Database Replication** | REQ-REL-001-003 |
| **Audit Logging** | REQ-COMP-004 |

---

## Document Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Technical Lead | | | |
| System Architect | | | |
| Product Owner | | | |
| Security Officer | | | |

---

**End of Design Document**
