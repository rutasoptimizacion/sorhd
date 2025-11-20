-- FlamenGO! Database Schema
-- Manual creation script as fallback

-- Drop existing tables if any
DROP TABLE IF EXISTS visits CASCADE;
DROP TABLE IF EXISTS route_personnel CASCADE;
DROP TABLE IF EXISTS personnel_skills CASCADE;
DROP TABLE IF EXISTS cases CASCADE;
DROP TABLE IF EXISTS routes CASCADE;
DROP TABLE IF EXISTS personnel CASCADE;
DROP TABLE IF EXISTS location_logs CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS care_type_skills CASCADE;
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS patients CASCADE;
DROP TABLE IF EXISTS vehicles CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS skills CASCADE;
DROP TABLE IF EXISTS care_types CASCADE;

-- Drop enums if they exist
DROP TYPE IF EXISTS userrol CASCADE;
DROP TYPE IF EXISTS vehiclestatus CASCADE;
DROP TYPE IF EXISTS casestatus CASCADE;
DROP TYPE IF EXISTS casepriority CASCADE;
DROP TYPE IF EXISTS timewindowtype CASCADE;
DROP TYPE IF EXISTS routestatus CASCADE;
DROP TYPE IF EXISTS visitstatus CASCADE;
DROP TYPE IF EXISTS notificationtype CASCADE;
DROP TYPE IF EXISTS notificationchannel CASCADE;
DROP TYPE IF EXISTS notificationstatus CASCADE;
DROP TYPE IF EXISTS auditaction CASCADE;

-- Create enums
CREATE TYPE userrole AS ENUM ('admin', 'clinical_team', 'patient');
CREATE TYPE vehiclestatus AS ENUM ('available', 'in_use', 'maintenance', 'unavailable');
CREATE TYPE casestatus AS ENUM ('pending', 'assigned', 'in_progress', 'completed', 'cancelled');
CREATE TYPE casepriority AS ENUM ('low', 'medium', 'high', 'urgent');
CREATE TYPE timewindowtype AS ENUM ('am', 'pm', 'specific', 'anytime');
CREATE TYPE routestatus AS ENUM ('draft', 'active', 'in_progress', 'completed', 'cancelled');
CREATE TYPE visitstatus AS ENUM ('pending', 'en_route', 'arrived', 'in_progress', 'completed', 'cancelled', 'failed');
CREATE TYPE notificationtype AS ENUM ('route_assigned', 'eta_update', 'visit_completed', 'delay_alert', 'general');
CREATE TYPE notificationchannel AS ENUM ('push', 'sms', 'email');
CREATE TYPE notificationstatus AS ENUM ('pending', 'sent', 'delivered', 'failed');
CREATE TYPE auditaction AS ENUM ('create', 'update', 'delete', 'login', 'logout', 'optimize', 'status_change');

-- Core tables
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role userrole NOT NULL DEFAULT 'clinical_team',
    full_name VARCHAR(255),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_users_username ON users(username);
CREATE INDEX ix_users_email ON users(email);

CREATE TABLE skills (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE care_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description VARCHAR(500),
    estimated_duration_minutes INTEGER NOT NULL DEFAULT 60,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE vehicles (
    id SERIAL PRIMARY KEY,
    identifier VARCHAR(50) UNIQUE NOT NULL,
    license_plate VARCHAR(20),
    capacity_personnel INTEGER NOT NULL DEFAULT 2,
    base_location GEOGRAPHY(POINT, 4326) NOT NULL,
    status vehiclestatus NOT NULL DEFAULT 'available',
    resources JSON,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_vehicles_base_location ON vehicles USING GIST(base_location);

CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    address VARCHAR(500),
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_patients_location ON patients USING GIST(location);

CREATE TABLE personnel (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    start_location GEOGRAPHY(POINT, 4326) NOT NULL,
    work_start_time TIME NOT NULL DEFAULT '08:00:00',
    work_end_time TIME NOT NULL DEFAULT '17:00:00',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_personnel_start_location ON personnel USING GIST(start_location);

CREATE TABLE cases (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    care_type_id INTEGER NOT NULL REFERENCES care_types(id),
    scheduled_date TIMESTAMP NOT NULL,
    time_window_type timewindowtype NOT NULL DEFAULT 'anytime',
    time_window_start TIMESTAMP,
    time_window_end TIMESTAMP,
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    priority casepriority NOT NULL DEFAULT 'medium',
    status casestatus NOT NULL DEFAULT 'pending',
    notes TEXT,
    estimated_duration_minutes INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cases_location ON cases USING GIST(location);

CREATE TABLE routes (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER NOT NULL REFERENCES vehicles(id),
    route_date DATE NOT NULL,
    status routestatus NOT NULL DEFAULT 'draft',
    total_distance_km FLOAT,
    total_duration_minutes FLOAT,
    optimization_metadata TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Join tables
CREATE TABLE personnel_skills (
    id SERIAL PRIMARY KEY,
    personnel_id INTEGER NOT NULL REFERENCES personnel(id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE care_type_skills (
    id SERIAL PRIMARY KEY,
    care_type_id INTEGER NOT NULL REFERENCES care_types(id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE route_personnel (
    id SERIAL PRIMARY KEY,
    route_id INTEGER NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
    personnel_id INTEGER NOT NULL REFERENCES personnel(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE visits (
    id SERIAL PRIMARY KEY,
    route_id INTEGER NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
    case_id INTEGER NOT NULL REFERENCES cases(id),
    sequence_number INTEGER NOT NULL,
    estimated_arrival_time TIMESTAMP,
    estimated_departure_time TIMESTAMP,
    actual_arrival_time TIMESTAMP,
    actual_departure_time TIMESTAMP,
    status visitstatus NOT NULL DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Tracking and notifications
CREATE TABLE location_logs (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER NOT NULL REFERENCES vehicles(id),
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    speed_kmh FLOAT,
    heading_degrees FLOAT,
    accuracy_meters FLOAT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_location_logs_location ON location_logs USING GIST(location);
CREATE INDEX idx_location_logs_vehicle_timestamp ON location_logs(vehicle_id, timestamp);
CREATE INDEX ix_location_logs_timestamp ON location_logs(timestamp);

CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    notification_type notificationtype NOT NULL,
    channel notificationchannel NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    data TEXT,
    status notificationstatus NOT NULL DEFAULT 'pending',
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action auditaction NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id INTEGER,
    changes TEXT,
    ip_address VARCHAR(45),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_audit_logs_timestamp ON audit_logs(timestamp);
