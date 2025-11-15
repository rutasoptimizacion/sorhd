# Sistema de Optimización de Rutas para Hospitalización Domiciliaria (SOR-HD)
## Requirements Specification (EARS Format)

**Version:** 1.0
**Date:** 2025-11-14
**Document Type:** Functional and Non-Functional Requirements

---

## 1. Introduction

### 1.1 Purpose
This document defines high-level requirements for the Route Optimization System for Home Hospitalization (SOR-HD). The system optimizes visit route planning and execution for clinical teams in home hospitalization settings.

### 1.2 Scope
The SOR-HD platform comprises three main components:
- **Backend Central**: Core optimization service with business logic and database management
- **Admin Panel**: Web application for resource management and route planning
- **Mobile Application**: Hybrid app with Clinical Team and Patient profiles

### 1.3 Stakeholders
- Clinical Teams (Medical professionals, kinesiologists, TENS)
- Administrative Staff (Coordinators)
- Patients receiving home hospitalization
- System Administrators

---

## 2. System-Wide Requirements

### 2.1 Architecture

**REQ-ARCH-001**: The system shall be built using a modular architecture allowing independent development and deployment of modules (Authentication, Optimization, Notifications, Geocoding).

**REQ-ARCH-002**: The system shall expose all backend functionality through a RESTful API.

**REQ-ARCH-003**: The system shall implement API-first design with decoupled frontend clients.

### 2.2 Technology Stack

**REQ-TECH-001**: The backend shall be developed using Python with FastAPI or Flask framework.

**REQ-TECH-002**: The admin panel shall be developed using React.js.

**REQ-TECH-003**: The system shall use PostgreSQL or similar relational database with geospatial capabilities.

**REQ-TECH-004**: The mobile application shall be developed using React Native for iOS and Android compatibility.

### 2.3 Security

**REQ-SEC-001**: The system shall implement secure authentication for all user types.

**REQ-SEC-002**: The system shall enforce role-based access control (RBAC) for different user profiles.

**REQ-SEC-003**: The system shall encrypt all data transmissions using HTTPS/TLS.

---

## 3. Data Entity Requirements

### 3.1 Personnel Management

**REQ-DATA-001**: The system shall store personnel records including identifier, role/skill (physician, kinesiologist, TENS, etc.), work schedule, and starting location.

**REQ-DATA-002**: The system shall support multiple skill types per personnel record.

**REQ-DATA-003**: WHEN a personnel record is created or updated, the system shall validate that all required fields are present.

### 3.2 Vehicle (Móviles) Management

**REQ-DATA-004**: The system shall store vehicle records including identifier, capacity, special equipment, and base location (latitude/longitude).

**REQ-DATA-005**: The system shall support special resource attributes for vehicles (e.g., "advanced wound care equipment").

**REQ-DATA-006**: WHEN a vehicle record is created or updated, the system shall validate geospatial coordinates.

### 3.3 Case (Visit) Management

**REQ-DATA-007**: The system shall store case records including patient identifier, geocoded location (latitude/longitude), required care type, and time windows.

**REQ-DATA-008**: The system shall support flexible time window definitions (e.g., "AM only", "10:00-12:00").

**REQ-DATA-009**: The system shall map care types to required personnel roles/skills.

**REQ-DATA-010**: WHEN a case is created, the system shall validate that the care type is supported.

### 3.4 Distance and Time Matrix

**REQ-DATA-011**: The system shall calculate distance and travel time between locations using external mapping services (Google Maps, OSRM).

**REQ-DATA-012**: WHERE external mapping services are unavailable, the system shall use cached distance data or fallback calculations.

---

## 4. Backend and Optimization Core Requirements

### 4.1 Data Management API

**REQ-BE-001**: The system shall provide RESTful CRUD endpoints for all entities (Personnel, Vehicles, Cases).

**REQ-BE-002**: WHEN an API request is received, the system shall validate input data before processing.

**REQ-BE-003**: The system shall return appropriate HTTP status codes and error messages for all API responses.

### 4.2 Optimization Engine

**REQ-OPT-001**: WHEN a route planning request is received, the system shall process Cases, available Personnel, and available Vehicles to generate optimal routes.

**REQ-OPT-002**: The system shall assign cases to vehicles respecting personnel skill requirements.

**REQ-OPT-003**: The system shall respect time window constraints when generating routes.

**REQ-OPT-004**: The system shall minimize total travel distance and time across all routes.

**REQ-OPT-005**: The system shall maximize clinical attention time by reducing logistical costs.

**REQ-OPT-006**: WHEN optimization completes, the system shall return an ordered set of cases for each vehicle.

**REQ-OPT-007**: IF optimization cannot find a feasible solution, THEN the system shall report which constraints cannot be satisfied.

### 4.3 Live Route Management

**REQ-ROUTE-001**: The system shall store route state (in progress, completed, cancelled).

**REQ-ROUTE-002**: WHEN a mobile device reports GPS location, the system shall update the vehicle's real-time position.

**REQ-ROUTE-003**: The system shall track visit status transitions (Scheduled, En Route, Started, Completed, Cancelled).

**REQ-ROUTE-004**: WHILE a route is active, the system shall accept status updates from mobile devices.

### 4.4 Notification Service

**REQ-NOTIF-001**: The system shall send push notifications to mobile applications.

**REQ-NOTIF-002**: WHERE push notifications fail, the system shall send SMS notifications as fallback.

**REQ-NOTIF-003**: WHEN a vehicle is en route to a patient, the system shall notify the patient.

**REQ-NOTIF-004**: WHEN ETA changes significantly, the system shall send updated notifications.

---

## 5. Admin Panel Requirements

### 5.1 Resource Management

**REQ-ADMIN-001**: The system shall provide web forms to create, edit, and delete Personnel records.

**REQ-ADMIN-002**: The system shall provide web forms to create, edit, and delete Vehicle records.

**REQ-ADMIN-003**: The system shall provide web forms to create, edit, and delete Patient/Case records.

**REQ-ADMIN-004**: WHEN a record is deleted, the system shall prevent deletion if the record is referenced in active routes.

### 5.2 Route Planning Interface

**REQ-ADMIN-005**: The system shall provide an interface to select cases to visit on a specific date.

**REQ-ADMIN-006**: The system shall provide an interface to select available personnel and vehicles for a specific date.

**REQ-ADMIN-007**: WHEN the administrator initiates route calculation, the system shall call the backend optimization API.

**REQ-ADMIN-008**: The system shall display optimization results as a list of routes.

**REQ-ADMIN-009**: WHERE map visualization is available, the system shall display routes on an interactive map.

### 5.3 Real-Time Monitoring

**REQ-ADMIN-010**: The system shall display real-time vehicle locations on a map.

**REQ-ADMIN-011**: WHILE routes are active, the system shall update vehicle positions automatically.

**REQ-ADMIN-012**: The system shall display current status of all active visits.

**REQ-ADMIN-013**: WHEN a vehicle reports a status change, the system shall update the monitoring dashboard.

---

## 6. Mobile Application Requirements

### 6.1 Authentication

**REQ-MOB-001**: The system shall provide secure login for clinical team members.

**REQ-MOB-002**: The system shall provide secure login for patients.

**REQ-MOB-003**: WHEN authentication fails, the system shall display appropriate error messages.

### 6.2 Clinical Team Profile

**REQ-MOB-TEAM-001**: WHEN a clinical team member logs in, the system shall display their assigned route.

**REQ-MOB-TEAM-002**: The system shall display the list of patients and visit order.

**REQ-MOB-TEAM-003**: WHEN a team member selects a visit, the system shall provide navigation integration with Google/Apple Maps.

**REQ-MOB-TEAM-004**: The system shall allow team members to update visit status (En Route, Started, Completed, Cancelled).

**REQ-MOB-TEAM-005**: WHILE a route is active, the system shall transmit GPS location to the backend continuously.

**REQ-MOB-TEAM-006**: The system shall allow manual refresh of route information.

**REQ-MOB-TEAM-007**: WHERE network connectivity is lost, the system shall cache route data locally.

### 6.3 Patient Profile

**REQ-MOB-PAT-001**: WHEN a patient logs in, the system shall display their scheduled visit status.

**REQ-MOB-PAT-002**: The system shall show visit states: Scheduled, En Route, In Progress, Completed.

**REQ-MOB-PAT-003**: WHEN the assigned vehicle is en route, the system shall display vehicle location on a map (Uber-style tracking).

**REQ-MOB-PAT-004**: The system shall display estimated time of arrival (ETA) for the assigned vehicle.

**REQ-MOB-PAT-005**: WHEN the patient receives a notification, the system shall display it in the app.

**REQ-MOB-PAT-006**: The system shall allow patients to receive notifications about delays or schedule changes.

---

## 7. Performance Requirements

**REQ-PERF-001**: The optimization engine shall generate routes for up to 50 cases within 60 seconds.

**REQ-PERF-002**: The admin panel shall load within 3 seconds on standard broadband connections.

**REQ-PERF-003**: WHILE tracking vehicles, the system shall update positions with maximum 30-second latency.

**REQ-PERF-004**: The mobile application shall consume minimal battery power during GPS tracking.

---

## 8. Scalability Requirements

**REQ-SCALE-001**: The system shall support at least 100 concurrent users on the admin panel.

**REQ-SCALE-002**: The system shall support at least 50 active mobile devices transmitting GPS data simultaneously.

**REQ-SCALE-003**: WHERE usage exceeds capacity, the system shall maintain functionality with graceful degradation.

---

## 9. Reliability Requirements

**REQ-REL-001**: The system shall have 99% uptime during business hours (6 AM - 10 PM).

**REQ-REL-002**: IF the system experiences a failure, THEN it shall recover within 15 minutes.

**REQ-REL-003**: The system shall backup data daily.

**REQ-REL-004**: WHERE external mapping services are unavailable, the system shall continue operating with cached data.

---

## 10. Usability Requirements

**REQ-USE-001**: The admin panel shall be usable by staff with basic computer literacy without extensive training.

**REQ-USE-002**: The mobile application shall be operable with one hand during vehicle operation.

**REQ-USE-003**: The system shall provide Spanish language interface for all components.

**REQ-USE-004**: WHERE users make errors, the system shall provide clear, actionable error messages.

---

## 11. Extensibility Requirements

**REQ-EXT-001**: The system shall support addition of new modules without disrupting core operations.

**REQ-EXT-002**: WHERE future integration with Electronic Health Records (EHR/Ficha Clínica) is needed, the system shall provide extensible API endpoints.

**REQ-EXT-003**: The system shall support addition of new geocoding services through modular integration.

**REQ-EXT-004**: The system shall support addition of new optimization algorithms without changing API contracts.

---

## 12. Compliance and Data Privacy

**REQ-COMP-001**: The system shall comply with applicable healthcare data privacy regulations.

**REQ-COMP-002**: The system shall anonymize patient data where full identification is not required.

**REQ-COMP-003**: WHEN storing location data, the system shall implement data retention policies.

**REQ-COMP-004**: The system shall provide audit logs for all data access and modifications.

---

## 13. Future Considerations

The following features are identified for future phases but are not required in the initial release:

- Advanced geocoding from street addresses to coordinates
- Integration with Electronic Health Record systems
- Predictive analytics for visit duration
- Multi-day route planning and optimization
- Vehicle maintenance tracking
- Patient satisfaction feedback collection

---

## 14. Traceability Matrix

| Requirement ID | Priority | Component | Verification Method |
|---------------|----------|-----------|---------------------|
| REQ-ARCH-001 to REQ-ARCH-003 | High | System-wide | Architecture Review |
| REQ-TECH-001 to REQ-TECH-004 | High | System-wide | Technical Inspection |
| REQ-SEC-001 to REQ-SEC-003 | Critical | System-wide | Security Testing |
| REQ-DATA-001 to REQ-DATA-012 | High | Backend | Unit Testing |
| REQ-BE-001 to REQ-BE-003 | High | Backend API | API Testing |
| REQ-OPT-001 to REQ-OPT-007 | Critical | Optimization Engine | Algorithm Testing |
| REQ-ROUTE-001 to REQ-ROUTE-004 | High | Backend | Integration Testing |
| REQ-NOTIF-001 to REQ-NOTIF-004 | Medium | Backend | Integration Testing |
| REQ-ADMIN-001 to REQ-ADMIN-013 | High | Admin Panel | UI Testing |
| REQ-MOB-001 to REQ-MOB-003 | High | Mobile App | User Testing |
| REQ-MOB-TEAM-001 to REQ-MOB-TEAM-007 | High | Mobile App | User Testing |
| REQ-MOB-PAT-001 to REQ-MOB-PAT-006 | High | Mobile App | User Testing |
| REQ-PERF-001 to REQ-PERF-004 | High | System-wide | Performance Testing |
| REQ-SCALE-001 to REQ-SCALE-003 | Medium | System-wide | Load Testing |
| REQ-REL-001 to REQ-REL-004 | High | System-wide | Reliability Testing |
| REQ-USE-001 to REQ-USE-004 | Medium | All UIs | Usability Testing |
| REQ-EXT-001 to REQ-EXT-004 | Low | System-wide | Architecture Review |
| REQ-COMP-001 to REQ-COMP-004 | Critical | System-wide | Compliance Audit |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-14 | System | Initial requirements document in EARS format |
