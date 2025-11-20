# FlamenGO! Implementation Checklist
## Sistema de Optimización de Rutas para Hospitalización Domiciliaria

**Version:** 1.0
**Date:** 2025-11-14
**Related Documents:** specs/requirements.md, specs/design.md

---

## Phase 0: Project Setup & Infrastructure
**Objective:** Establish development environment and project structure
**Duration:** 1-2 days
**Dependencies:** None

### Tasks

- [ ] **0.1 Development Environment Setup**
  - [ ] Install Python 3.11+
  - [ ] Install Node.js 18+ and npm
  - [ ] Install PostgreSQL 15+ with PostGIS extension
  - [ ] Install Docker and Docker Compose
  - [ ] Install React Native development tools (Xcode/Android Studio)
  - [ ] Configure IDE/editor with linting and formatting tools

- [ ] **0.2 Repository Initialization**
  - [ ] Initialize Git repository
  - [ ] Create `.gitignore` for Python, Node.js, React Native
  - [ ] Set up branch protection rules
  - [ ] Create initial README.md with project overview

- [ ] **0.3 Project Structure**
  - [ ] Create backend directory structure
    ```
    backend/
    ├── app/
    │   ├── api/
    │   ├── core/
    │   ├── models/
    │   ├── schemas/
    │   ├── services/
    │   └── main.py
    ├── tests/
    ├── requirements.txt
    └── Dockerfile
    ```
  - [ ] Create admin panel directory structure
    ```
    admin/
    ├── src/
    │   ├── components/
    │   ├── hooks/
    │   ├── services/
    │   ├── store/
    │   ├── types/
    │   └── App.tsx
    ├── package.json
    └── vite.config.ts
    ```
  - [ ] Create mobile app directory structure
    ```
    mobile/
    ├── src/
    │   ├── screens/
    │   ├── components/
    │   ├── services/
    │   ├── store/
    │   └── navigation/
    ├── ios/
    ├── android/
    └── package.json
    ```

- [ ] **0.4 Docker Configuration**
  - [ ] Create `docker-compose.yml` for development
  - [ ] Configure PostgreSQL service with PostGIS
  - [ ] Configure backend service
  - [ ] Configure Redis service (optional)
  - [ ] Test Docker setup with `docker-compose up`

- [ ] **0.5 CI/CD Pipeline**
  - [ ] Set up GitHub Actions workflow (or GitLab CI)
  - [ ] Configure automated testing on push
  - [ ] Configure linting and code quality checks
  - [ ] Set up deployment pipeline (placeholder)

### Acceptance Criteria
- ✅ All team members can run `docker-compose up` successfully
- ✅ Database is accessible at localhost:5432
- ✅ Project structure follows design specifications
- ✅ Git repository is properly configured

---

## Phase 1: Backend Foundation
**Objective:** Implement core backend infrastructure with authentication
**Duration:** 3-4 days
**Dependencies:** Phase 0

### Tasks

- [ ] **1.1 Database Schema Implementation**
  - [ ] Create database migration tool setup (Alembic)
  - [ ] Implement `users` table schema
  - [ ] Implement `skills` table schema
  - [ ] Implement `personnel` and `personnel_skills` tables
  - [ ] Implement `vehicles` and `vehicle_resources` tables
  - [ ] Implement `patients` table schema
  - [ ] Implement `care_types` and `care_type_skills` tables
  - [ ] Implement `cases` table schema
  - [ ] Implement `routes`, `route_personnel`, `visits` tables
  - [ ] Implement `location_logs` table with geospatial indexes
  - [ ] Implement `notifications` table schema
  - [ ] Implement `distance_cache` table (optional)
  - [ ] Implement `audit_logs` table schema
  - [ ] Create initial migration scripts
  - [ ] Run migrations and verify schema

- [ ] **1.2 SQLAlchemy Models**
  - [ ] Create base model class with timestamps
  - [ ] Implement User model with role enum
  - [ ] Implement Skill model
  - [ ] Implement Personnel model with PostGIS location
  - [ ] Implement Vehicle model with PostGIS location
  - [ ] Implement Patient model with PostGIS location
  - [ ] Implement CareType model
  - [ ] Implement Case model with time windows
  - [ ] Implement Route model
  - [ ] Implement Visit model
  - [ ] Implement LocationLog model
  - [ ] Implement Notification model
  - [ ] Implement relationships between models
  - [ ] Add indexes for performance optimization

- [ ] **1.3 Pydantic Schemas (DTOs)**
  - [ ] Create base schema classes
  - [ ] Create User schemas (Create, Update, Response)
  - [ ] Create Personnel schemas with validation
  - [ ] Create Vehicle schemas with validation
  - [ ] Create Patient schemas with validation
  - [ ] Create Case schemas with time window validation
  - [ ] Create Route schemas
  - [ ] Create Location schema with coordinate validation
  - [ ] Create pagination schema
  - [ ] Create error response schemas

- [ ] **1.4 FastAPI Application Setup**
  - [ ] Create FastAPI app instance in `main.py`
  - [ ] Configure CORS middleware
  - [ ] Configure database connection pooling
  - [ ] Add request/response logging middleware
  - [ ] Configure OpenAPI documentation
  - [ ] Set up API versioning (/api/v1)
  - [ ] Add health check endpoint
  - [ ] Create environment configuration management

- [ ] **1.5 Authentication System**
  - [ ] Install dependencies (python-jose, passlib)
  - [ ] Implement password hashing utilities
  - [ ] Implement JWT token generation
  - [ ] Implement JWT token validation
  - [ ] Implement refresh token mechanism
  - [ ] Create authentication service
  - [ ] Create dependency for current user extraction
  - [ ] Implement login endpoint (POST /api/v1/auth/login)
  - [ ] Implement refresh token endpoint
  - [ ] Implement logout endpoint with token blacklisting
  - [ ] Write unit tests for authentication

- [ ] **1.6 Authorization System**
  - [ ] Create role-based permission decorators
  - [ ] Implement `@requires_role` decorator
  - [ ] Create permission checking utilities
  - [ ] Add authorization to protected endpoints
  - [ ] Write tests for authorization rules

- [ ] **1.7 Error Handling**
  - [ ] Create custom exception classes
  - [ ] Implement global exception handler
  - [ ] Add validation error formatting
  - [ ] Implement error response standardization
  - [ ] Add error logging

### Testing
- [ ] Write unit tests for authentication flow
- [ ] Write unit tests for authorization rules
- [ ] Write integration tests for database models
- [ ] Test JWT token generation and validation
- [ ] Test password hashing security

### Acceptance Criteria
- ✅ Database schema matches design document
- ✅ User can register and login via API
- ✅ JWT tokens are generated correctly
- ✅ Role-based access control works
- ✅ All tests pass (>80% coverage for auth)
- ✅ API documentation is auto-generated

---

## Phase 2: Resource Management
**Objective:** Implement CRUD operations for all entities
**Duration:** 5-6 days
**Dependencies:** Phase 1

### Tasks

- [ ] **2.1 Repository Pattern Implementation**
  - [ ] Create base repository class
  - [ ] Implement PersonnelRepository
  - [ ] Implement VehicleRepository
  - [ ] Implement PatientRepository
  - [ ] Implement CaseRepository
  - [ ] Implement CareTypeRepository
  - [ ] Add query filtering utilities
  - [ ] Add pagination support

- [ ] **2.2 Service Layer**
  - [ ] Create base service class
  - [ ] Implement PersonnelService
    - [ ] CRUD operations
    - [ ] Skill validation
    - [ ] Coordinate validation
    - [ ] Active route checking before delete
  - [ ] Implement VehicleService
    - [ ] CRUD operations
    - [ ] Resource management
    - [ ] Base location validation
    - [ ] Active route checking before delete
  - [ ] Implement PatientService
    - [ ] CRUD operations
    - [ ] Location validation
  - [ ] Implement CaseService
    - [ ] CRUD operations
    - [ ] Time window validation
    - [ ] Care type compatibility checking
    - [ ] Priority handling
  - [ ] Implement CareTypeService
    - [ ] CRUD operations
    - [ ] Skill requirements management

- [ ] **2.3 Personnel API Endpoints**
  - [ ] GET /api/v1/personnel (list with pagination)
  - [ ] POST /api/v1/personnel (create)
  - [ ] GET /api/v1/personnel/{id} (get by ID)
  - [ ] PUT /api/v1/personnel/{id} (update)
  - [ ] DELETE /api/v1/personnel/{id} (delete)
  - [ ] Add query filters (skill, is_active)
  - [ ] Add role-based authorization
  - [ ] Add input validation

- [ ] **2.4 Vehicle API Endpoints**
  - [ ] GET /api/v1/vehicles (list with pagination)
  - [ ] POST /api/v1/vehicles (create)
  - [ ] GET /api/v1/vehicles/{id} (get by ID)
  - [ ] PUT /api/v1/vehicles/{id} (update)
  - [ ] DELETE /api/v1/vehicles/{id} (delete)
  - [ ] Add query filters (status, is_active)
  - [ ] Add authorization

- [ ] **2.5 Patient API Endpoints**
  - [ ] GET /api/v1/patients (list with pagination)
  - [ ] POST /api/v1/patients (create)
  - [ ] GET /api/v1/patients/{id} (get by ID)
  - [ ] PUT /api/v1/patients/{id} (update)
  - [ ] DELETE /api/v1/patients/{id} (delete)
  - [ ] Add authorization

- [ ] **2.6 Case API Endpoints**
  - [ ] GET /api/v1/cases (list with pagination)
  - [ ] POST /api/v1/cases (create)
  - [ ] GET /api/v1/cases/{id} (get by ID)
  - [ ] PUT /api/v1/cases/{id} (update)
  - [ ] DELETE /api/v1/cases/{id} (delete)
  - [ ] Add query filters (status, date, priority)
  - [ ] Add authorization

- [ ] **2.7 Care Type & Skill Management**
  - [ ] GET /api/v1/skills (list all skills)
  - [ ] POST /api/v1/skills (create skill)
  - [ ] GET /api/v1/care-types (list care types)
  - [ ] POST /api/v1/care-types (create care type)
  - [ ] PUT /api/v1/care-types/{id} (update)
  - [ ] DELETE /api/v1/care-types/{id} (delete)

- [ ] **2.8 Audit Logging**
  - [ ] Implement audit log service
  - [ ] Add audit logging to all CRUD operations
  - [ ] Store changes in JSONB format
  - [ ] Capture user ID and IP address

### Testing
- [ ] Unit tests for all repositories
- [ ] Unit tests for all services
- [ ] Integration tests for all API endpoints
- [ ] Test referential integrity constraints
- [ ] Test cascade delete behavior
- [ ] Test pagination and filtering
- [ ] Test authorization for each endpoint

### Acceptance Criteria
- ✅ All CRUD endpoints functional
- ✅ Data validation working correctly
- ✅ Cannot delete resources in active routes
- ✅ Audit logs capture all changes
- ✅ All tests pass (>80% coverage)
- ✅ API documentation complete

---

## Phase 3: Distance & Geospatial Services
**Objective:** Implement distance calculation and caching
**Duration:** 2-3 days
**Dependencies:** Phase 2

### Tasks

- [ ] **3.1 Distance Provider Abstraction**
  - [ ] Create DistanceProvider abstract base class
  - [ ] Define DistanceMatrix data structure
  - [ ] Create Location data class
  - [ ] Create TravelTime data class

- [ ] **3.2 Google Maps Provider**
  - [ ] Install Google Maps API client
  - [ ] Implement GoogleMapsProvider class
  - [ ] Implement distance matrix calculation
  - [ ] Add API key configuration
  - [ ] Add rate limiting handling
  - [ ] Add error handling for API failures

- [ ] **3.3 OSRM Provider**
  - [ ] Install OSRM client library
  - [ ] Implement OSRMProvider class
  - [ ] Configure OSRM endpoint
  - [ ] Implement distance matrix calculation
  - [ ] Add error handling

- [ ] **3.4 Haversine Fallback Provider**
  - [ ] Implement HaversineProvider class
  - [ ] Calculate great-circle distance
  - [ ] Estimate travel time based on average speed
  - [ ] Add configuration for average speeds

- [ ] **3.5 Distance Service**
  - [ ] Implement DistanceService class
  - [ ] Add provider selection logic
  - [ ] Implement distance matrix caching
  - [ ] Add cache key generation
  - [ ] Implement cache invalidation
  - [ ] Add fallback mechanism (Google Maps → OSRM → Haversine)

- [ ] **3.6 Cache Service**
  - [ ] Implement Redis cache adapter (if using Redis)
  - [ ] Implement database cache fallback
  - [ ] Add TTL management (24 hours)
  - [ ] Implement cache statistics

- [ ] **3.7 Geospatial Utilities**
  - [ ] Create coordinate validation utilities
  - [ ] Implement PostGIS query helpers
  - [ ] Add distance calculation helpers
  - [ ] Create bounding box utilities

### Testing
- [ ] Unit tests for each provider
- [ ] Test distance matrix calculation accuracy
- [ ] Test caching mechanism
- [ ] Test fallback behavior
- [ ] Test with various coordinate inputs
- [ ] Mock external API calls in tests

### Acceptance Criteria
- ✅ Distance calculation works with all providers
- ✅ Cache reduces external API calls
- ✅ Fallback mechanism works correctly
- ✅ Coordinate validation prevents invalid data
- ✅ All tests pass
- ✅ Performance meets requirements (<100ms for cached)

---

## Phase 4: Optimization Engine
**Objective:** Implement route optimization algorithms
**Duration:** 7-10 days
**Dependencies:** Phase 2, Phase 3

### Tasks

- [ ] **4.1 Optimization Domain Models**
  - [ ] Create OptimizationRequest dataclass
  - [ ] Create OptimizationResult dataclass
  - [ ] Create Route dataclass
  - [ ] Create Visit dataclass
  - [ ] Create Constraint violation classes

- [ ] **4.2 OR-Tools VRP Implementation**
  - [ ] Install OR-Tools library
  - [ ] Create ORToolsVRPStrategy class
  - [ ] Implement data model builder
  - [ ] Implement distance callback
  - [ ] Implement time callback
  - [ ] Add time window constraints
  - [ ] Add capacity constraints
  - [ ] Add skill matching constraints
  - [ ] Configure search parameters
  - [ ] Implement solution extraction
  - [ ] Add infeasibility detection

- [ ] **4.3 Heuristic Fallback Algorithm**
  - [ ] Create NearestNeighborStrategy class
  - [ ] Implement nearest neighbor construction
  - [ ] Implement feasibility checking
  - [ ] Implement 2-opt local search
  - [ ] Add time window validation
  - [ ] Add skill validation

- [ ] **4.4 Optimization Service**
  - [ ] Create OptimizationService class
  - [ ] Implement strategy selection (OR-Tools vs Heuristic)
  - [ ] Add request validation
  - [ ] Implement distance matrix retrieval
  - [ ] Add optimization timeout handling
  - [ ] Implement result persistence to database
  - [ ] Add optimization performance logging

- [ ] **4.5 Route API Endpoints**
  - [ ] POST /api/v1/routes/optimize (trigger optimization)
  - [ ] GET /api/v1/routes (list routes)
  - [ ] GET /api/v1/routes/{id} (get route details)
  - [ ] PATCH /api/v1/routes/{id}/status (update status)
  - [ ] DELETE /api/v1/routes/{id} (cancel route)
  - [ ] Add query filters (date, status, vehicle_id)
  - [ ] Add admin-only authorization

- [ ] **4.6 Async Optimization (Optional)**
  - [ ] Install Celery and Redis
  - [ ] Create Celery app configuration
  - [ ] Implement optimization as Celery task
  - [ ] Add job status tracking
  - [ ] Implement job result retrieval endpoint
  - [ ] Add WebSocket notification on completion

- [ ] **4.7 Constraint Validation**
  - [ ] Validate personnel skill requirements
  - [ ] Validate vehicle capacity
  - [ ] Validate time windows
  - [ ] Validate working hours
  - [ ] Generate detailed constraint violation reports

### Testing
- [ ] Unit tests for OR-Tools optimizer
- [ ] Unit tests for heuristic optimizer
- [ ] Test with small datasets (5 cases, 1 vehicle)
- [ ] Test with medium datasets (20 cases, 3 vehicles)
- [ ] Test with large datasets (50 cases, 5 vehicles)
- [ ] Test infeasible scenarios
- [ ] Test time window constraints
- [ ] Test skill matching
- [ ] Performance tests (<60 seconds for 50 cases)
- [ ] Integration tests for optimization API

### Acceptance Criteria
- ✅ Optimization generates valid routes
- ✅ Time windows are respected
- ✅ Skill requirements are met
- ✅ Performance meets requirements (REQ-PERF-001)
- ✅ Infeasible problems return clear error messages
- ✅ Heuristic fallback works when OR-Tools fails
- ✅ All tests pass (>80% coverage)

---

## Phase 5: Route Tracking & Management
**Objective:** Implement GPS tracking and real-time updates
**Duration:** 4-5 days
**Dependencies:** Phase 4

### Tasks

- [ ] **5.1 Location Tracking Service**
  - [ ] Create LocationTracker class
  - [ ] Implement location storage in database
  - [ ] Add geospatial indexing
  - [ ] Implement location history retrieval
  - [ ] Add data retention policy (90 days)

- [ ] **5.2 Route Tracker Service**
  - [ ] Create RouteTrackerService class
  - [ ] Implement active route retrieval
  - [ ] Implement visit status updates
  - [ ] Add status transition validation
  - [ ] Implement route completion detection

- [ ] **5.3 ETA Calculator**
  - [ ] Create ETACalculator class
  - [ ] Implement current position to destination calculation
  - [ ] Add traffic buffer based on time of day
  - [ ] Implement ETA caching
  - [ ] Add significant change detection (for notifications)

- [ ] **5.4 Delay Detection**
  - [ ] Implement delay detection algorithm
  - [ ] Compare actual vs estimated times
  - [ ] Add configurable delay threshold
  - [ ] Create delay alert generation

- [ ] **5.5 WebSocket Implementation**
  - [ ] Install WebSocket dependencies (socket.io or similar)
  - [ ] Configure WebSocket server
  - [ ] Implement connection authentication
  - [ ] Implement subscription mechanism (vehicle_ids)
  - [ ] Add location broadcast on update
  - [ ] Add connection management (reconnection)

- [ ] **5.6 Tracking API Endpoints**
  - [ ] POST /api/v1/tracking/location (upload location)
  - [ ] GET /api/v1/tracking/vehicle/{id} (get current location)
  - [ ] WS /api/v1/tracking/live (WebSocket endpoint)
  - [ ] GET /api/v1/routes/active (get active routes)
  - [ ] Add rate limiting for location uploads

- [ ] **5.7 Visit Status Management**
  - [ ] PATCH /api/v1/visits/{id}/status (update visit status)
  - [ ] Add status transition validation
  - [ ] Update case status when visit completes
  - [ ] Trigger notifications on status changes
  - [ ] Update route status when all visits complete

### Testing
- [ ] Unit tests for location tracking
- [ ] Unit tests for ETA calculation
- [ ] Test WebSocket connections
- [ ] Test location broadcasts
- [ ] Test visit status transitions
- [ ] Test delay detection
- [ ] Integration tests for tracking endpoints
- [ ] Load test WebSocket (50 concurrent connections)

### Acceptance Criteria
- ✅ GPS locations are stored correctly
- ✅ WebSocket updates work in real-time
- ✅ ETA calculations are accurate
- ✅ Delay detection works correctly
- ✅ Visit status updates propagate correctly
- ✅ Performance meets requirements (REQ-PERF-003)
- ✅ All tests pass

---

## Phase 6: Notification System
**Objective:** Implement push notifications and SMS
**Duration:** 3-4 days
**Dependencies:** Phase 5

### Tasks

- [ ] **6.1 Notification Service Architecture**
  - [ ] Create NotificationService class
  - [ ] Create PushNotificationProvider interface
  - [ ] Create SMSProvider interface
  - [ ] Implement notification templates

- [ ] **6.2 Firebase Cloud Messaging (FCM)**
  - [ ] Set up Firebase project
  - [ ] Install FCM Python SDK
  - [ ] Implement FCMProvider class
  - [ ] Add device token management
  - [ ] Implement push notification sending
  - [ ] Add notification data payload support

- [ ] **6.3 Apple Push Notification Service (APNS)**
  - [ ] Configure APNS certificates
  - [ ] Implement APNSProvider class
  - [ ] Add iOS-specific notification formatting
  - [ ] Test with iOS devices

- [ ] **6.4 SMS Integration (Twilio)**
  - [ ] Create Twilio account
  - [ ] Install Twilio Python SDK
  - [ ] Implement TwilioSMSProvider class
  - [ ] Add phone number validation
  - [ ] Implement SMS sending
  - [ ] Add message templating

- [ ] **6.5 Notification Types**
  - [ ] Implement route_assigned notification
  - [ ] Implement eta_update notification
  - [ ] Implement visit_completed notification
  - [ ] Implement delay_alert notification
  - [ ] Add Spanish language templates

- [ ] **6.6 Notification API Endpoints**
  - [ ] POST /api/v1/notifications/send (admin-only)
  - [ ] GET /api/v1/notifications (user's notifications)
  - [ ] PATCH /api/v1/notifications/{id}/read (mark as read)
  - [ ] POST /api/v1/users/device-token (register device)

- [ ] **6.7 Automatic Notifications**
  - [ ] Trigger notification when route assigned
  - [ ] Trigger notification when vehicle en route
  - [ ] Trigger notification on significant ETA change
  - [ ] Trigger notification on delay detection
  - [ ] Add fallback to SMS if push fails

### Testing
- [ ] Unit tests for notification service
- [ ] Test FCM integration (with test devices)
- [ ] Test APNS integration (with test devices)
- [ ] Test SMS sending
- [ ] Test notification fallback mechanism
- [ ] Test notification templating
- [ ] Integration tests for notification endpoints

### Acceptance Criteria
- ✅ Push notifications work on Android
- ✅ Push notifications work on iOS
- ✅ SMS fallback works when push fails
- ✅ Notifications are in Spanish
- ✅ All notification types implemented
- ✅ Device token registration works
- ✅ All tests pass

---

## Phase 7: Admin Panel - Foundation
**Objective:** Set up React admin panel infrastructure
**Duration:** 2-3 days
**Dependencies:** Phase 1 (Backend Auth)

### Tasks

- [ ] **7.1 Project Initialization**
  - [ ] Create React + TypeScript + Vite project
  - [ ] Install core dependencies (React Router, Redux Toolkit)
  - [ ] Install UI library (Material-UI)
  - [ ] Configure TypeScript (tsconfig.json)
  - [ ] Configure ESLint and Prettier
  - [ ] Set up environment variables

- [ ] **7.2 State Management**
  - [ ] Set up Redux Toolkit store
  - [ ] Create authSlice for authentication state
  - [ ] Configure Redux DevTools
  - [ ] Install React Query for server state
  - [ ] Configure query client

- [ ] **7.3 API Client**
  - [ ] Create Axios instance with base URL
  - [ ] Add request interceptor for auth token
  - [ ] Add response interceptor for errors
  - [ ] Create API service functions structure
  - [ ] Implement API error handling

- [ ] **7.4 Authentication UI**
  - [ ] Create Login page component
  - [ ] Create login form with validation
  - [ ] Implement authentication API calls
  - [ ] Add token storage (localStorage)
  - [ ] Create private route wrapper
  - [ ] Add automatic token refresh
  - [ ] Create logout functionality

- [ ] **7.5 Layout Components**
  - [ ] Create main Layout component
  - [ ] Create Header component
  - [ ] Create Sidebar navigation
  - [ ] Create responsive menu
  - [ ] Add user profile menu
  - [ ] Style with Material-UI theme

- [ ] **7.6 Routing**
  - [ ] Configure React Router
  - [ ] Create route configuration
  - [ ] Add protected routes
  - [ ] Create 404 Not Found page
  - [ ] Add navigation guards

- [ ] **7.7 Common Components**
  - [ ] Create DataTable component (with sorting/filtering)
  - [ ] Create FormField component
  - [ ] Create ConfirmDialog component
  - [ ] Create LoadingSpinner component
  - [ ] Create ErrorMessage component
  - [ ] Create SuccessMessage component

### Testing
- [ ] Test login flow
- [ ] Test protected route access
- [ ] Test logout functionality
- [ ] Test token refresh
- [ ] Component unit tests

### Acceptance Criteria
- ✅ Login page functional
- ✅ Authentication state managed correctly
- ✅ Protected routes work
- ✅ Layout is responsive
- ✅ Navigation works
- ✅ Token refresh automatic
- ✅ Error handling in place

---

## Phase 8: Admin Panel - Resource Management
**Objective:** Implement CRUD interfaces for all resources
**Duration:** 5-6 days
**Dependencies:** Phase 7, Phase 2 (Backend CRUD)

### Tasks

- [ ] **8.1 Personnel Management**
  - [ ] Create PersonnelList component with DataGrid
  - [ ] Create PersonnelForm component
  - [ ] Add form validation (React Hook Form)
  - [ ] Implement create personnel
  - [ ] Implement edit personnel
  - [ ] Implement delete personnel (with confirmation)
  - [ ] Add skill multi-select
  - [ ] Add location picker (map)
  - [ ] Add work hours picker
  - [ ] Add filters (skill, active status)
  - [ ] Add pagination

- [ ] **8.2 Vehicle Management**
  - [ ] Create VehicleList component
  - [ ] Create VehicleForm component
  - [ ] Implement CRUD operations
  - [ ] Add capacity input
  - [ ] Add base location picker (map)
  - [ ] Add resource management
  - [ ] Add status dropdown
  - [ ] Add filters and pagination

- [ ] **8.3 Patient Management**
  - [ ] Create PatientList component
  - [ ] Create PatientForm component
  - [ ] Implement CRUD operations
  - [ ] Add location picker
  - [ ] Add search functionality
  - [ ] Add filters and pagination

- [ ] **8.4 Case Management**
  - [ ] Create CaseList component
  - [ ] Create CaseForm component
  - [ ] Implement CRUD operations
  - [ ] Add patient selector
  - [ ] Add care type selector
  - [ ] Add time window picker
  - [ ] Add priority selector
  - [ ] Add location picker
  - [ ] Add filters (status, date, priority)
  - [ ] Add bulk operations (optional)

- [ ] **8.5 Care Type & Skill Management**
  - [ ] Create SkillList component
  - [ ] Create SkillForm component
  - [ ] Create CareTypeList component
  - [ ] Create CareTypeForm component
  - [ ] Add skill requirements selector
  - [ ] Implement CRUD operations

- [ ] **8.6 Data Validation**
  - [ ] Add client-side validation for all forms
  - [ ] Display server-side validation errors
  - [ ] Add coordinate validation
  - [ ] Add time window validation

- [ ] **8.7 User Experience**
  - [ ] Add loading states during API calls
  - [ ] Add success notifications
  - [ ] Add error notifications
  - [ ] Add confirmation dialogs for destructive actions
  - [ ] Add inline editing (optional)

### Testing
- [ ] Component tests for all lists
- [ ] Component tests for all forms
- [ ] Test CRUD operations
- [ ] Test form validation
- [ ] Test error handling
- [ ] E2E tests for critical flows

### Acceptance Criteria
- ✅ All CRUD interfaces functional
- ✅ Forms have proper validation
- ✅ Location pickers work
- ✅ Filters and pagination work
- ✅ Delete confirmations prevent accidents
- ✅ Error messages are clear
- ✅ UI is responsive
- ✅ All tests pass

---

## Phase 9: Admin Panel - Route Planning
**Objective:** Implement route planning and optimization interface
**Duration:** 4-5 days
**Dependencies:** Phase 8, Phase 4 (Optimization Engine)

### Tasks

- [ ] **9.1 Route Planner Interface**
  - [ ] Create RoutePlanner page
  - [ ] Add date picker for planning date
  - [ ] Create two-column layout (cases | vehicles/personnel)
  - [ ] Add case selection table with checkboxes
  - [ ] Add vehicle selection with assigned personnel
  - [ ] Add "Optimize Routes" button
  - [ ] Add loading state during optimization

- [ ] **9.2 Case Selection**
  - [ ] Display pending cases for selected date
  - [ ] Add search/filter functionality
  - [ ] Show case details (patient, location, time window)
  - [ ] Add multi-select capability
  - [ ] Show selected count

- [ ] **9.3 Vehicle & Personnel Selection**
  - [ ] Display available vehicles
  - [ ] Add personnel assignment to vehicles
  - [ ] Validate skill coverage
  - [ ] Show capacity constraints
  - [ ] Add validation before optimization

- [ ] **9.4 Optimization Execution**
  - [ ] Call optimization API endpoint
  - [ ] Handle async optimization (if implemented)
  - [ ] Show progress indicator
  - [ ] Handle optimization errors
  - [ ] Display constraint violations

- [ ] **9.5 Results Display**
  - [ ] Create RouteResults component
  - [ ] Display summary cards (total distance, time, vehicles)
  - [ ] Create route table with expandable rows
  - [ ] Show visit sequence and times
  - [ ] Display unassigned cases (if any)
  - [ ] Show warnings

- [ ] **9.6 Map Visualization**
  - [ ] Integrate Leaflet or Google Maps
  - [ ] Display all route paths
  - [ ] Use different colors for each route
  - [ ] Show vehicle markers
  - [ ] Show case/visit markers
  - [ ] Add route polylines
  - [ ] Add zoom and pan controls

- [ ] **9.7 Route Actions**
  - [ ] Add "Approve & Activate" button
  - [ ] Add "Re-optimize" button
  - [ ] Add "Save as Draft" functionality
  - [ ] Add route export (PDF/CSV)

### Testing
- [ ] Test route planning workflow
- [ ] Test optimization trigger
- [ ] Test result display
- [ ] Test map visualization
- [ ] Test error scenarios
- [ ] E2E test complete planning flow

### Acceptance Criteria
- ✅ Can select cases and vehicles
- ✅ Optimization generates routes
- ✅ Results display correctly
- ✅ Map shows all routes visually
- ✅ Can activate routes
- ✅ Handles optimization errors gracefully
- ✅ Performance acceptable (loads in <3s)
- ✅ All tests pass

---

## Phase 10: Admin Panel - Live Monitoring
**Objective:** Implement real-time vehicle tracking dashboard
**Duration:** 3-4 days
**Dependencies:** Phase 9, Phase 5 (Tracking Backend)

### Tasks

- [ ] **10.1 Live Map Component**
  - [ ] Create LiveMap component
  - [ ] Initialize map with proper center/zoom
  - [ ] Add vehicle markers with status colors
  - [ ] Update marker positions in real-time
  - [ ] Add marker clustering (optional)
  - [ ] Add route polylines for active routes

- [ ] **10.2 WebSocket Integration**
  - [ ] Install socket.io-client
  - [ ] Create WebSocket service
  - [ ] Implement connection with authentication
  - [ ] Subscribe to vehicle location updates
  - [ ] Handle connection errors and reconnection
  - [ ] Add connection status indicator

- [ ] **10.3 Active Routes Panel**
  - [ ] Create ActiveRoutesPanel component
  - [ ] Display list of active routes
  - [ ] Show current visit and progress
  - [ ] Display ETA for next visit
  - [ ] Show vehicle status badge
  - [ ] Add click to focus on map

- [ ] **10.4 Filters & Controls**
  - [ ] Add date filter (default: today)
  - [ ] Add status filter (all, en route, at visit, delayed)
  - [ ] Add vehicle filter
  - [ ] Add auto-refresh toggle

- [ ] **10.5 Status Dashboard**
  - [ ] Create summary cards (total routes, completed, in progress)
  - [ ] Display visit completion timeline
  - [ ] Show delay alerts
  - [ ] Add refresh data button

- [ ] **10.6 Real-time Updates**
  - [ ] Update vehicle positions on map
  - [ ] Update status badges
  - [ ] Update ETA values
  - [ ] Show notifications for status changes
  - [ ] Play alert sound for delays (optional)

### Testing
- [ ] Test WebSocket connection
- [ ] Test real-time location updates
- [ ] Test marker movement on map
- [ ] Test filters
- [ ] Test reconnection on disconnect
- [ ] Performance test with 50 vehicles

### Acceptance Criteria
- ✅ Map displays all active vehicles
- ✅ Vehicle positions update in real-time
- ✅ WebSocket connection stable
- ✅ Filters work correctly
- ✅ Status indicators accurate
- ✅ Performance acceptable (<30s latency)
- ✅ All tests pass

---

## Phase 11: Mobile App - Foundation
**Objective:** Set up React Native app with authentication
**Duration:** 3-4 days
**Dependencies:** Phase 1 (Backend Auth)

### Tasks

- [ ] **11.1 React Native Project Setup**
  - [ ] Initialize React Native project
  - [ ] Configure TypeScript
  - [ ] Set up folder structure
  - [ ] Configure Metro bundler
  - [ ] Set up iOS project (Xcode)
  - [ ] Set up Android project (Android Studio)

- [ ] **11.2 Dependencies Installation**
  - [ ] Install React Navigation
  - [ ] Install Redux Toolkit & React Redux
  - [ ] Install AsyncStorage
  - [ ] Install Axios
  - [ ] Install react-native-maps
  - [ ] Install geolocation service
  - [ ] Install Firebase (for notifications)

- [ ] **11.3 State Management**
  - [ ] Set up Redux store
  - [ ] Create authSlice
  - [ ] Create routeSlice
  - [ ] Create locationSlice
  - [ ] Configure Redux Persist

- [ ] **11.4 API Client**
  - [ ] Create Axios instance
  - [ ] Add request interceptor for auth
  - [ ] Add response interceptor for errors
  - [ ] Create API service functions
  - [ ] Implement offline queue

- [ ] **11.5 Authentication Screens**
  - [ ] Create LoginScreen component
  - [ ] Create login form with validation
  - [ ] Implement login API call
  - [ ] Store auth token in AsyncStorage
  - [ ] Create logout functionality
  - [ ] Add loading states

- [ ] **11.6 Navigation Structure**
  - [ ] Configure stack navigator
  - [ ] Create AuthStack for login
  - [ ] Create AppStack for authenticated routes
  - [ ] Create TeamStack for clinical team
  - [ ] Create PatientStack for patient
  - [ ] Add conditional navigation based on role

- [ ] **11.7 Common Components**
  - [ ] Create Button component
  - [ ] Create Card component
  - [ ] Create StatusBadge component
  - [ ] Create LoadingSpinner component
  - [ ] Create ErrorMessage component

- [ ] **11.8 Styling & Theme**
  - [ ] Create theme configuration
  - [ ] Define color palette
  - [ ] Create typography styles
  - [ ] Add Spanish language support

### Testing
- [ ] Test on iOS simulator
- [ ] Test on Android emulator
- [ ] Test on physical devices
- [ ] Test login flow
- [ ] Test token persistence
- [ ] Test navigation

### Acceptance Criteria
- ✅ App runs on iOS
- ✅ App runs on Android
- ✅ Login works correctly
- ✅ Token persists on app restart
- ✅ Navigation works
- ✅ Styling is consistent
- ✅ Spanish language throughout

---

## Phase 12: Mobile App - Clinical Team
**Objective:** Implement clinical team features
**Duration:** 5-6 days
**Dependencies:** Phase 11, Phase 5 (Tracking Backend)

### Tasks

- [ ] **12.1 Route List Screen**
  - [ ] Create RouteListScreen component
  - [ ] Fetch assigned route for current user
  - [ ] Display route date and summary
  - [ ] Show list of visits as cards
  - [ ] Display visit sequence and times
  - [ ] Show visit status badges
  - [ ] Add pull-to-refresh

- [ ] **12.2 Visit Cards**
  - [ ] Create VisitCard component
  - [ ] Display patient name (pseudonymized if needed)
  - [ ] Display address
  - [ ] Display time window
  - [ ] Display status
  - [ ] Add expand/collapse functionality

- [ ] **12.3 Visit Detail View**
  - [ ] Show full case details
  - [ ] Display care type and requirements
  - [ ] Show special instructions/notes
  - [ ] Display patient contact (if permitted)

- [ ] **12.4 Navigation Integration**
  - [ ] Add "Navigate" button
  - [ ] Deep link to Google Maps (Android)
  - [ ] Deep link to Apple Maps (iOS)
  - [ ] Pass destination coordinates
  - [ ] Handle no maps app installed

- [ ] **12.5 Status Updates**
  - [ ] Create status update buttons
  - [ ] Implement "Mark En Route" action
  - [ ] Implement "Mark Started" action
  - [ ] Implement "Mark Completed" action
  - [ ] Implement "Cancel Visit" action
  - [ ] Update backend via API
  - [ ] Update local state optimistically
  - [ ] Handle API errors

- [ ] **12.6 GPS Tracking**
  - [ ] Request location permissions
  - [ ] Implement foreground location tracking
  - [ ] Implement background location tracking
  - [ ] Upload location to backend every 30 seconds
  - [ ] Add battery optimization settings
  - [ ] Handle permissions denial

- [ ] **12.7 Offline Support**
  - [ ] Cache route data locally
  - [ ] Queue status updates when offline
  - [ ] Sync queue when online
  - [ ] Show offline indicator
  - [ ] Handle sync conflicts

- [ ] **12.8 Push Notifications**
  - [ ] Configure Firebase for Android
  - [ ] Configure APNS for iOS
  - [ ] Request notification permissions
  - [ ] Register device token with backend
  - [ ] Handle incoming notifications
  - [ ] Display notification badges

### Testing
- [ ] Test route fetching
- [ ] Test visit status updates
- [ ] Test GPS tracking
- [ ] Test navigation integration
- [ ] Test offline mode
- [ ] Test push notifications
- [ ] Test on physical devices
- [ ] Test battery consumption

### Acceptance Criteria
- ✅ Route displays correctly
- ✅ Can navigate to each visit
- ✅ Status updates work
- ✅ GPS tracking functional
- ✅ Offline mode works
- ✅ Push notifications received
- ✅ Battery usage acceptable
- ✅ All tests pass

---

## Phase 13: Mobile App - Patient Profile
**Objective:** Implement patient tracking features
**Duration:** 3-4 days
**Dependencies:** Phase 12

### Tasks

- [ ] **13.1 Visit Status Screen**
  - [ ] Create VisitStatusScreen component
  - [ ] Fetch patient's scheduled visit
  - [ ] Display visit date and time window
  - [ ] Show visit status
  - [ ] Display ETA when vehicle en route
  - [ ] Add refresh functionality

- [ ] **13.2 Status Display**
  - [ ] Create status cards for each state
  - [ ] "Scheduled" status view
  - [ ] "En Route" status view
  - [ ] "In Progress" status view
  - [ ] "Completed" status view
  - [ ] Add appropriate icons and colors

- [ ] **13.3 Live Tracking Map**
  - [ ] Create TrackingMap component
  - [ ] Display patient location (home)
  - [ ] Display vehicle location (when en route)
  - [ ] Show route polyline
  - [ ] Center map on vehicle
  - [ ] Update vehicle position in real-time

- [ ] **13.4 WebSocket Integration**
  - [ ] Connect to tracking WebSocket
  - [ ] Subscribe to assigned vehicle
  - [ ] Receive location updates
  - [ ] Update map markers
  - [ ] Handle connection errors

- [ ] **13.5 ETA Display**
  - [ ] Fetch ETA from backend
  - [ ] Display countdown timer
  - [ ] Update ETA automatically
  - [ ] Show arrival time estimate
  - [ ] Highlight significant delays

- [ ] **13.6 Team Information**
  - [ ] Display clinical team member names
  - [ ] Show team member roles
  - [ ] Add team member photos (optional)
  - [ ] Display vehicle identifier

- [ ] **13.7 Notifications**
  - [ ] Handle "Team Assigned" notification
  - [ ] Handle "Team En Route" notification
  - [ ] Handle "ETA Update" notification
  - [ ] Handle "Team Arrived" notification
  - [ ] Handle "Visit Completed" notification
  - [ ] Display notifications in app

### Testing
- [ ] Test visit status display
- [ ] Test live tracking map
- [ ] Test ETA updates
- [ ] Test WebSocket connection
- [ ] Test notification handling
- [ ] Test on physical devices

### Acceptance Criteria
- ✅ Visit status displays correctly
- ✅ Map shows vehicle location in real-time
- ✅ ETA updates automatically
- ✅ Notifications work
- ✅ UI is simple and clear
- ✅ Works on iOS and Android
- ✅ All tests pass

---

## Phase 14: Integration & Testing
**Objective:** End-to-end testing and bug fixes
**Duration:** 5-7 days
**Dependencies:** All previous phases

### Tasks

- [ ] **14.1 End-to-End Testing**
  - [ ] Write E2E test: Complete route planning workflow
  - [ ] Write E2E test: Route execution workflow
  - [ ] Write E2E test: Patient tracking workflow
  - [ ] Test cross-component integration
  - [ ] Test API contract compliance

- [ ] **14.2 Performance Testing**
  - [ ] Load test backend (100 concurrent users)
  - [ ] Test optimization with 50 cases
  - [ ] Test WebSocket with 50 connections
  - [ ] Test mobile GPS tracking
  - [ ] Measure API response times
  - [ ] Profile database queries

- [ ] **14.3 Security Testing**
  - [ ] Test authentication bypass attempts
  - [ ] Test authorization boundaries
  - [ ] Test SQL injection protection
  - [ ] Test XSS protection
  - [ ] Test CORS configuration
  - [ ] Review secrets management
  - [ ] Test token expiration

- [ ] **14.4 Mobile Testing**
  - [ ] Test on various Android devices/versions
  - [ ] Test on various iOS devices/versions
  - [ ] Test different screen sizes
  - [ ] Test different network conditions
  - [ ] Test battery consumption
  - [ ] Test offline scenarios

- [ ] **14.5 User Acceptance Testing (UAT)**
  - [ ] Prepare UAT environment
  - [ ] Create test data sets
  - [ ] Conduct UAT with stakeholders
  - [ ] Document feedback
  - [ ] Prioritize bug fixes

- [ ] **14.6 Bug Fixes**
  - [ ] Fix critical bugs
  - [ ] Fix high-priority bugs
  - [ ] Fix medium-priority bugs
  - [ ] Regression testing after fixes

- [ ] **14.7 Code Quality**
  - [ ] Run code coverage analysis
  - [ ] Refactor code smells
  - [ ] Add missing tests
  - [ ] Update inline documentation
  - [ ] Run security linters

### Testing Checklist
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All E2E tests pass
- [ ] Performance requirements met
- [ ] Security vulnerabilities addressed
- [ ] Mobile apps tested on devices
- [ ] UAT feedback incorporated

### Acceptance Criteria
- ✅ All critical bugs fixed
- ✅ Performance meets requirements
- ✅ Security audit passes
- ✅ UAT approved by stakeholders
- ✅ Code coverage >80% backend, >70% frontend
- ✅ No P0 or P1 bugs remaining

---

## Phase 15: Deployment & Documentation
**Objective:** Deploy to production and complete documentation
**Duration:** 4-5 days
**Dependencies:** Phase 14

### Tasks

- [ ] **15.1 Production Environment Setup**
  - [ ] Set up production database (PostgreSQL + PostGIS)
  - [ ] Configure production server/cloud
  - [ ] Set up SSL certificates
  - [ ] Configure domain and DNS
  - [ ] Set up reverse proxy (Nginx)
  - [ ] Configure firewall rules

- [ ] **15.2 Backend Deployment**
  - [ ] Build production Docker image
  - [ ] Push image to container registry
  - [ ] Deploy to production server
  - [ ] Run database migrations
  - [ ] Configure environment variables
  - [ ] Set up process manager (systemd/pm2)
  - [ ] Verify health check endpoint

- [ ] **15.3 Admin Panel Deployment**
  - [ ] Build production bundle (`npm run build`)
  - [ ] Upload to static hosting (S3, CloudFront, or server)
  - [ ] Configure CDN
  - [ ] Set up cache headers
  - [ ] Verify deployment

- [ ] **15.4 Mobile App Deployment**
  - [ ] Build Android APK/AAB
  - [ ] Upload to Google Play Console
  - [ ] Configure store listing
  - [ ] Build iOS IPA
  - [ ] Upload to App Store Connect
  - [ ] Configure App Store listing
  - [ ] Submit for review

- [ ] **15.5 Monitoring & Logging**
  - [ ] Set up Prometheus for metrics
  - [ ] Set up Grafana dashboards
  - [ ] Configure log aggregation (ELK or Loki)
  - [ ] Set up error tracking (Sentry)
  - [ ] Configure alerting rules
  - [ ] Set up uptime monitoring

- [ ] **15.6 Backup & Recovery**
  - [ ] Configure automated database backups
  - [ ] Test backup restoration
  - [ ] Document recovery procedures
  - [ ] Set up backup monitoring

- [ ] **15.7 API Documentation**
  - [ ] Review OpenAPI/Swagger docs
  - [ ] Add authentication examples
  - [ ] Add endpoint descriptions
  - [ ] Add example requests/responses
  - [ ] Publish API documentation

- [ ] **15.8 User Documentation**
  - [ ] Write admin panel user guide
  - [ ] Write mobile app user guide (clinical team)
  - [ ] Write mobile app user guide (patient)
  - [ ] Create video tutorials (optional)
  - [ ] Document common workflows
  - [ ] Document troubleshooting

- [ ] **15.9 Developer Documentation**
  - [ ] Update README with setup instructions
  - [ ] Document architecture decisions
  - [ ] Document deployment process
  - [ ] Document database schema
  - [ ] Document API versioning strategy
  - [ ] Add contributing guidelines

- [ ] **15.10 Handoff & Training**
  - [ ] Conduct admin training session
  - [ ] Conduct clinical team training
  - [ ] Conduct patient onboarding
  - [ ] Provide administrator credentials
  - [ ] Document support procedures

### Acceptance Criteria
- ✅ Backend deployed and accessible
- ✅ Admin panel accessible via HTTPS
- ✅ Mobile apps available in stores
- ✅ Monitoring dashboards operational
- ✅ Backups automated and tested
- ✅ All documentation complete
- ✅ Training conducted
- ✅ System ready for production use

---

## Post-Launch Tasks

### Immediate Post-Launch (Week 1)
- [ ] Monitor system performance closely
- [ ] Monitor error rates and logs
- [ ] Respond to user feedback
- [ ] Fix any critical bugs immediately
- [ ] Verify all notifications working
- [ ] Check GPS tracking accuracy

### Short-term Improvements (Month 1-3)
- [ ] Collect user feedback
- [ ] Analyze optimization performance
- [ ] Optimize database queries
- [ ] Improve mobile app battery usage
- [ ] Add analytics/reporting features
- [ ] Implement user-requested features

### Long-term Enhancements (Month 3+)
- [ ] Advanced geocoding from addresses
- [ ] EHR/Ficha Clínica integration
- [ ] Predictive analytics for visit duration
- [ ] Multi-day route planning
- [ ] Vehicle maintenance tracking
- [ ] Patient satisfaction surveys
- [ ] Machine learning for optimization

---

## Summary

| Phase | Duration | Dependencies | Key Deliverables |
|-------|----------|--------------|------------------|
| 0 | 1-2 days | None | Development environment, project structure |
| 1 | 3-4 days | Phase 0 | Database schema, authentication, base API |
| 2 | 5-6 days | Phase 1 | CRUD endpoints for all entities |
| 3 | 2-3 days | Phase 2 | Distance calculation and caching |
| 4 | 7-10 days | Phase 2, 3 | Route optimization engine |
| 5 | 4-5 days | Phase 4 | GPS tracking, WebSocket, real-time updates |
| 6 | 3-4 days | Phase 5 | Push notifications, SMS |
| 7 | 2-3 days | Phase 1 | Admin panel foundation |
| 8 | 5-6 days | Phase 7, 2 | Resource management UI |
| 9 | 4-5 days | Phase 8, 4 | Route planning interface |
| 10 | 3-4 days | Phase 9, 5 | Live monitoring dashboard |
| 11 | 3-4 days | Phase 1 | Mobile app foundation |
| 12 | 5-6 days | Phase 11, 5 | Clinical team features |
| 13 | 3-4 days | Phase 12 | Patient tracking features |
| 14 | 5-7 days | All | Testing and bug fixes |
| 15 | 4-5 days | Phase 14 | Production deployment, documentation |

**Total Estimated Duration:** 57-77 days (~2.5-3.5 months)

---

## Usage Instructions

### How to Use This Checklist

1. **Sequential Execution**: Complete phases in order, as later phases depend on earlier ones
2. **Daily Updates**: Check off completed tasks daily
3. **Blocker Tracking**: Document any blockers that prevent task completion
4. **Testing**: Do not mark a task complete until tests are written and passing
5. **Code Review**: All code should be reviewed before marking tasks complete
6. **Documentation**: Update relevant documentation as tasks are completed

### Task Status Indicators

- [ ] Not started
- [⏳] In progress
- [✅] Completed
- [🚫] Blocked
- [⚠️] Needs review

### Priority Levels

- **Critical**: Must be completed for MVP
- **High**: Important for full functionality
- **Medium**: Nice to have
- **Low**: Can be deferred to post-launch

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-14 | Development Team | Initial implementation checklist |

---

**End of Checklist**
