/**
 * Database Schema para SQLite offline
 *
 * Este schema permite que la app funcione completamente offline
 * y sincronice datos cuando recupera conexión
 */

export const DATABASE_NAME = 'sor_hd.db';
export const DATABASE_VERSION = 1;

/**
 * Schema de tablas SQLite
 */
export const DATABASE_SCHEMA = {
  /**
   * Tabla: routes
   * Almacena las rutas asignadas al equipo clínico
   */
  routes: `
    CREATE TABLE IF NOT EXISTS routes (
      id INTEGER PRIMARY KEY,
      vehicle_id INTEGER,
      route_date TEXT NOT NULL,
      status TEXT NOT NULL,
      total_distance_km REAL,
      total_duration_minutes REAL,
      data TEXT NOT NULL,
      synced INTEGER DEFAULT 0,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      deleted_at TEXT
    )
  `,

  /**
   * Tabla: visits
   * Almacena las visitas individuales de cada ruta
   */
  visits: `
    CREATE TABLE IF NOT EXISTS visits (
      id INTEGER PRIMARY KEY,
      route_id INTEGER NOT NULL,
      case_id INTEGER NOT NULL,
      sequence_number INTEGER NOT NULL,
      status TEXT NOT NULL,
      estimated_arrival_time TEXT,
      actual_arrival_time TEXT,
      actual_departure_time TEXT,
      data TEXT NOT NULL,
      synced INTEGER DEFAULT 0,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      deleted_at TEXT,
      FOREIGN KEY (route_id) REFERENCES routes(id)
    )
  `,

  /**
   * Tabla: location_queue
   * Cola de ubicaciones GPS para sincronizar con el servidor
   */
  location_queue: `
    CREATE TABLE IF NOT EXISTS location_queue (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      route_id INTEGER,
      latitude REAL NOT NULL,
      longitude REAL NOT NULL,
      speed_kmh REAL,
      heading REAL,
      accuracy REAL,
      timestamp TEXT NOT NULL,
      synced INTEGER DEFAULT 0,
      sync_attempts INTEGER DEFAULT 0,
      last_sync_attempt TEXT,
      created_at TEXT NOT NULL
    )
  `,

  /**
   * Tabla: status_queue
   * Cola de cambios de estado de visitas para sincronizar
   */
  status_queue: `
    CREATE TABLE IF NOT EXISTS status_queue (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      visit_id INTEGER NOT NULL,
      old_status TEXT,
      new_status TEXT NOT NULL,
      notes TEXT,
      timestamp TEXT NOT NULL,
      synced INTEGER DEFAULT 0,
      sync_attempts INTEGER DEFAULT 0,
      last_sync_attempt TEXT,
      error_message TEXT,
      created_at TEXT NOT NULL
    )
  `,

  /**
   * Tabla: sync_metadata
   * Metadatos de sincronización
   */
  sync_metadata: `
    CREATE TABLE IF NOT EXISTS sync_metadata (
      key TEXT PRIMARY KEY,
      value TEXT NOT NULL,
      updated_at TEXT NOT NULL
    )
  `,

  /**
   * Tabla: user_profile
   * Perfil del usuario actual (caché)
   */
  user_profile: `
    CREATE TABLE IF NOT EXISTS user_profile (
      id INTEGER PRIMARY KEY,
      username TEXT NOT NULL,
      role TEXT NOT NULL,
      first_login INTEGER NOT NULL,
      data TEXT NOT NULL,
      updated_at TEXT NOT NULL
    )
  `,

  /**
   * Tabla: patient_info
   * Información de pacientes (para perfil paciente)
   */
  patient_info: `
    CREATE TABLE IF NOT EXISTS patient_info (
      id INTEGER PRIMARY KEY,
      name TEXT NOT NULL,
      location_lat REAL,
      location_lng REAL,
      address TEXT,
      phone TEXT,
      data TEXT NOT NULL,
      updated_at TEXT NOT NULL
    )
  `
};

/**
 * Índices para mejorar performance de queries
 */
export const DATABASE_INDEXES = {
  routes_date_status: `
    CREATE INDEX IF NOT EXISTS idx_routes_date_status
    ON routes(route_date, status)
  `,
  routes_synced: `
    CREATE INDEX IF NOT EXISTS idx_routes_synced
    ON routes(synced)
  `,
  visits_route: `
    CREATE INDEX IF NOT EXISTS idx_visits_route
    ON visits(route_id, sequence_number)
  `,
  visits_synced: `
    CREATE INDEX IF NOT EXISTS idx_visits_synced
    ON visits(synced)
  `,
  location_queue_synced: `
    CREATE INDEX IF NOT EXISTS idx_location_queue_synced
    ON location_queue(synced, created_at)
  `,
  status_queue_synced: `
    CREATE INDEX IF NOT EXISTS idx_status_queue_synced
    ON status_queue(synced, created_at)
  `
};

/**
 * Queries pre-compiladas para operaciones comunes
 */
export const QUERIES = {
  // Routes
  getRouteById: 'SELECT * FROM routes WHERE id = ? AND deleted_at IS NULL',
  getRoutesByDate: 'SELECT * FROM routes WHERE route_date = ? AND deleted_at IS NULL ORDER BY created_at DESC',
  getUnsyncedRoutes: 'SELECT * FROM routes WHERE synced = 0 AND deleted_at IS NULL',
  insertRoute: `
    INSERT INTO routes (id, vehicle_id, route_date, status, total_distance_km, total_duration_minutes, data, synced, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `,
  updateRoute: `
    UPDATE routes
    SET status = ?, data = ?, updated_at = ?, synced = 0
    WHERE id = ?
  `,
  markRouteSynced: 'UPDATE routes SET synced = 1, updated_at = ? WHERE id = ?',

  // Visits
  getVisitById: 'SELECT * FROM visits WHERE id = ? AND deleted_at IS NULL',
  getVisitsByRoute: 'SELECT * FROM visits WHERE route_id = ? AND deleted_at IS NULL ORDER BY sequence_number ASC',
  getUnsyncedVisits: 'SELECT * FROM visits WHERE synced = 0 AND deleted_at IS NULL',
  insertVisit: `
    INSERT INTO visits (id, route_id, case_id, sequence_number, status, estimated_arrival_time, data, synced, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `,
  updateVisitStatus: `
    UPDATE visits
    SET status = ?, actual_arrival_time = ?, actual_departure_time = ?, data = ?, updated_at = ?, synced = 0
    WHERE id = ?
  `,
  markVisitSynced: 'UPDATE visits SET synced = 1, updated_at = ? WHERE id = ?',

  // Location Queue
  insertLocation: `
    INSERT INTO location_queue (route_id, latitude, longitude, speed_kmh, heading, accuracy, timestamp, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `,
  getUnsyncedLocations: `
    SELECT * FROM location_queue
    WHERE synced = 0 AND sync_attempts < 5
    ORDER BY created_at ASC
    LIMIT ?
  `,
  markLocationSynced: 'UPDATE location_queue SET synced = 1 WHERE id = ?',
  markLocationSyncAttempt: `
    UPDATE location_queue
    SET sync_attempts = sync_attempts + 1, last_sync_attempt = ?
    WHERE id = ?
  `,
  deleteOldSyncedLocations: `
    DELETE FROM location_queue
    WHERE synced = 1 AND created_at < ?
  `,

  // Status Queue
  insertStatusChange: `
    INSERT INTO status_queue (visit_id, old_status, new_status, notes, timestamp, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
  `,
  getUnsyncedStatusChanges: `
    SELECT * FROM status_queue
    WHERE synced = 0 AND sync_attempts < 5
    ORDER BY created_at ASC
    LIMIT ?
  `,
  markStatusSynced: 'UPDATE status_queue SET synced = 1 WHERE id = ?',
  markStatusSyncAttempt: `
    UPDATE status_queue
    SET sync_attempts = sync_attempts + 1, last_sync_attempt = ?, error_message = ?
    WHERE id = ?
  `,
  deleteOldSyncedStatuses: `
    DELETE FROM status_queue
    WHERE synced = 1 AND created_at < ?
  `,

  // Sync Metadata
  getSyncMetadata: 'SELECT value FROM sync_metadata WHERE key = ?',
  setSyncMetadata: `
    INSERT OR REPLACE INTO sync_metadata (key, value, updated_at)
    VALUES (?, ?, ?)
  `,

  // User Profile
  getUserProfile: 'SELECT * FROM user_profile LIMIT 1',
  upsertUserProfile: `
    INSERT OR REPLACE INTO user_profile (id, username, role, first_login, data, updated_at)
    VALUES (?, ?, ?, ?, ?, ?)
  `,
  clearUserProfile: 'DELETE FROM user_profile',

  // Patient Info
  getPatientInfo: 'SELECT * FROM patient_info WHERE id = ?',
  upsertPatientInfo: `
    INSERT OR REPLACE INTO patient_info (id, name, location_lat, location_lng, address, phone, data, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `
};

/**
 * Claves de metadatos de sincronización
 */
export const SYNC_KEYS = {
  LAST_ROUTE_SYNC: 'last_route_sync',
  LAST_VISIT_SYNC: 'last_visit_sync',
  LAST_LOCATION_SYNC: 'last_location_sync',
  LAST_STATUS_SYNC: 'last_status_sync',
  LAST_FULL_SYNC: 'last_full_sync',
  SYNC_IN_PROGRESS: 'sync_in_progress',
  NETWORK_STATUS: 'network_status'
};
