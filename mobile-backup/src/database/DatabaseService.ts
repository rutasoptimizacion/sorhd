/**
 * DatabaseService
 *
 * Servicio principal para manejo de la base de datos SQLite offline
 * Maneja inicialización, queries, y operaciones CRUD
 */

import SQLite, {SQLiteDatabase, ResultSet} from 'react-native-sqlite-storage';
import {
  DATABASE_NAME,
  DATABASE_VERSION,
  DATABASE_SCHEMA,
  DATABASE_INDEXES,
  QUERIES,
  SYNC_KEYS,
} from './schema';

// Enable promise API
SQLite.enablePromise(true);

// Enable debug mode in development
if (__DEV__) {
  SQLite.DEBUG(true);
}

export interface Route {
  id: number;
  vehicle_id: number;
  route_date: string;
  status: string;
  total_distance_km?: number;
  total_duration_minutes?: number;
  data: string; // JSON string
  synced: number;
  created_at: string;
  updated_at: string;
  deleted_at?: string;
}

export interface Visit {
  id: number;
  route_id: number;
  case_id: number;
  sequence_number: number;
  status: string;
  estimated_arrival_time?: string;
  actual_arrival_time?: string;
  actual_departure_time?: string;
  data: string; // JSON string
  synced: number;
  created_at: string;
  updated_at: string;
  deleted_at?: string;
}

export interface LocationQueueItem {
  id?: number;
  route_id?: number;
  latitude: number;
  longitude: number;
  speed_kmh?: number;
  heading?: number;
  accuracy?: number;
  timestamp: string;
  synced: number;
  sync_attempts: number;
  last_sync_attempt?: string;
  created_at: string;
}

export interface StatusQueueItem {
  id?: number;
  visit_id: number;
  old_status?: string;
  new_status: string;
  notes?: string;
  timestamp: string;
  synced: number;
  sync_attempts: number;
  last_sync_attempt?: string;
  error_message?: string;
  created_at: string;
}

class DatabaseService {
  private db: SQLiteDatabase | null = null;
  private initialized: boolean = false;

  /**
   * Inicializa la base de datos
   * Crea las tablas e índices si no existen
   */
  async initialize(): Promise<void> {
    if (this.initialized && this.db) {
      return;
    }

    try {
      console.log('[DatabaseService] Inicializando base de datos...');

      // Abrir o crear la base de datos
      this.db = await SQLite.openDatabase({
        name: DATABASE_NAME,
        location: 'default',
      });

      // Crear tablas
      await this.createTables();

      // Crear índices
      await this.createIndexes();

      this.initialized = true;
      console.log('[DatabaseService] Base de datos inicializada correctamente');
    } catch (error) {
      console.error('[DatabaseService] Error al inicializar:', error);
      throw error;
    }
  }

  /**
   * Crea todas las tablas del schema
   */
  private async createTables(): Promise<void> {
    if (!this.db) throw new Error('Database not opened');

    for (const [tableName, createSQL] of Object.entries(DATABASE_SCHEMA)) {
      try {
        await this.db.executeSql(createSQL);
        console.log(`[DatabaseService] Tabla ${tableName} creada/verificada`);
      } catch (error) {
        console.error(`[DatabaseService] Error al crear tabla ${tableName}:`, error);
        throw error;
      }
    }
  }

  /**
   * Crea todos los índices
   */
  private async createIndexes(): Promise<void> {
    if (!this.db) throw new Error('Database not opened');

    for (const [indexName, createSQL] of Object.entries(DATABASE_INDEXES)) {
      try {
        await this.db.executeSql(createSQL);
        console.log(`[DatabaseService] Índice ${indexName} creado/verificado`);
      } catch (error) {
        console.error(`[DatabaseService] Error al crear índice ${indexName}:`, error);
        // Los índices son opcionales, no lanzar error
      }
    }
  }

  /**
   * Cierra la base de datos
   */
  async close(): Promise<void> {
    if (this.db) {
      await this.db.close();
      this.db = null;
      this.initialized = false;
      console.log('[DatabaseService] Base de datos cerrada');
    }
  }

  /**
   * Elimina completamente la base de datos
   * SOLO USAR EN LOGOUT O RESET
   */
  async deleteDatabase(): Promise<void> {
    try {
      if (this.db) {
        await this.close();
      }
      await SQLite.deleteDatabase({name: DATABASE_NAME, location: 'default'});
      console.log('[DatabaseService] Base de datos eliminada');
    } catch (error) {
      console.error('[DatabaseService] Error al eliminar base de datos:', error);
      throw error;
    }
  }

  /**
   * Ejecuta una query SQL
   */
  private async executeSql(sql: string, params: any[] = []): Promise<ResultSet> {
    if (!this.db) {
      throw new Error('Database not initialized');
    }

    try {
      const [results] = await this.db.executeSql(sql, params);
      return results;
    } catch (error) {
      console.error('[DatabaseService] Error en SQL:', sql, params, error);
      throw error;
    }
  }

  // ========== ROUTES ==========

  async getRouteById(id: number): Promise<Route | null> {
    const results = await this.executeSql(QUERIES.getRouteById, [id]);
    return results.rows.length > 0 ? results.rows.item(0) : null;
  }

  async getRoutesByDate(date: string): Promise<Route[]> {
    const results = await this.executeSql(QUERIES.getRoutesByDate, [date]);
    const routes: Route[] = [];
    for (let i = 0; i < results.rows.length; i++) {
      routes.push(results.rows.item(i));
    }
    return routes;
  }

  async getUnsyncedRoutes(): Promise<Route[]> {
    const results = await this.executeSql(QUERIES.getUnsyncedRoutes);
    const routes: Route[] = [];
    for (let i = 0; i < results.rows.length; i++) {
      routes.push(results.rows.item(i));
    }
    return routes;
  }

  async insertRoute(route: Omit<Route, 'created_at' | 'updated_at'>): Promise<void> {
    const now = new Date().toISOString();
    await this.executeSql(QUERIES.insertRoute, [
      route.id,
      route.vehicle_id,
      route.route_date,
      route.status,
      route.total_distance_km ?? null,
      route.total_duration_minutes ?? null,
      route.data,
      route.synced,
      now,
      now,
    ]);
  }

  async updateRoute(id: number, status: string, data: string): Promise<void> {
    const now = new Date().toISOString();
    await this.executeSql(QUERIES.updateRoute, [status, data, now, id]);
  }

  async markRouteSynced(id: number): Promise<void> {
    const now = new Date().toISOString();
    await this.executeSql(QUERIES.markRouteSynced, [now, id]);
  }

  // ========== VISITS ==========

  async getVisitById(id: number): Promise<Visit | null> {
    const results = await this.executeSql(QUERIES.getVisitById, [id]);
    return results.rows.length > 0 ? results.rows.item(0) : null;
  }

  async getVisitsByRoute(routeId: number): Promise<Visit[]> {
    const results = await this.executeSql(QUERIES.getVisitsByRoute, [routeId]);
    const visits: Visit[] = [];
    for (let i = 0; i < results.rows.length; i++) {
      visits.push(results.rows.item(i));
    }
    return visits;
  }

  async getUnsyncedVisits(): Promise<Visit[]> {
    const results = await this.executeSql(QUERIES.getUnsyncedVisits);
    const visits: Visit[] = [];
    for (let i = 0; i < results.rows.length; i++) {
      visits.push(results.rows.item(i));
    }
    return visits;
  }

  async insertVisit(visit: Omit<Visit, 'created_at' | 'updated_at'>): Promise<void> {
    const now = new Date().toISOString();
    await this.executeSql(QUERIES.insertVisit, [
      visit.id,
      visit.route_id,
      visit.case_id,
      visit.sequence_number,
      visit.status,
      visit.estimated_arrival_time ?? null,
      visit.data,
      visit.synced,
      now,
      now,
    ]);
  }

  async updateVisitStatus(
    id: number,
    status: string,
    arrivalTime?: string,
    departureTime?: string,
    data?: string,
  ): Promise<void> {
    const now = new Date().toISOString();
    const visit = await this.getVisitById(id);
    if (!visit) throw new Error(`Visit ${id} not found`);

    const updatedData = data ?? visit.data;
    await this.executeSql(QUERIES.updateVisitStatus, [
      status,
      arrivalTime ?? visit.actual_arrival_time ?? null,
      departureTime ?? visit.actual_departure_time ?? null,
      updatedData,
      now,
      id,
    ]);
  }

  async markVisitSynced(id: number): Promise<void> {
    const now = new Date().toISOString();
    await this.executeSql(QUERIES.markVisitSynced, [now, id]);
  }

  // ========== LOCATION QUEUE ==========

  async insertLocation(location: Omit<LocationQueueItem, 'id' | 'synced' | 'sync_attempts' | 'created_at'>): Promise<void> {
    const now = new Date().toISOString();
    await this.executeSql(QUERIES.insertLocation, [
      location.route_id ?? null,
      location.latitude,
      location.longitude,
      location.speed_kmh ?? null,
      location.heading ?? null,
      location.accuracy ?? null,
      location.timestamp,
      now,
    ]);
  }

  async getUnsyncedLocations(limit: number = 100): Promise<LocationQueueItem[]> {
    const results = await this.executeSql(QUERIES.getUnsyncedLocations, [limit]);
    const locations: LocationQueueItem[] = [];
    for (let i = 0; i < results.rows.length; i++) {
      locations.push(results.rows.item(i));
    }
    return locations;
  }

  async markLocationSynced(id: number): Promise<void> {
    await this.executeSql(QUERIES.markLocationSynced, [id]);
  }

  async markLocationSyncAttempt(id: number): Promise<void> {
    const now = new Date().toISOString();
    await this.executeSql(QUERIES.markLocationSyncAttempt, [now, id]);
  }

  async deleteOldSyncedLocations(olderThan: string): Promise<void> {
    await this.executeSql(QUERIES.deleteOldSyncedLocations, [olderThan]);
  }

  // ========== STATUS QUEUE ==========

  async insertStatusChange(statusChange: Omit<StatusQueueItem, 'id' | 'synced' | 'sync_attempts' | 'created_at'>): Promise<void> {
    const now = new Date().toISOString();
    await this.executeSql(QUERIES.insertStatusChange, [
      statusChange.visit_id,
      statusChange.old_status ?? null,
      statusChange.new_status,
      statusChange.notes ?? null,
      statusChange.timestamp,
      now,
    ]);
  }

  async getUnsyncedStatusChanges(limit: number = 50): Promise<StatusQueueItem[]> {
    const results = await this.executeSql(QUERIES.getUnsyncedStatusChanges, [limit]);
    const changes: StatusQueueItem[] = [];
    for (let i = 0; i < results.rows.length; i++) {
      changes.push(results.rows.item(i));
    }
    return changes;
  }

  async markStatusSynced(id: number): Promise<void> {
    await this.executeSql(QUERIES.markStatusSynced, [id]);
  }

  async markStatusSyncAttempt(id: number, errorMessage?: string): Promise<void> {
    const now = new Date().toISOString();
    await this.executeSql(QUERIES.markStatusSyncAttempt, [now, errorMessage ?? null, id]);
  }

  async deleteOldSyncedStatuses(olderThan: string): Promise<void> {
    await this.executeSql(QUERIES.deleteOldSyncedStatuses, [olderThan]);
  }

  // ========== SYNC METADATA ==========

  async getSyncMetadata(key: string): Promise<string | null> {
    const results = await this.executeSql(QUERIES.getSyncMetadata, [key]);
    return results.rows.length > 0 ? results.rows.item(0).value : null;
  }

  async setSyncMetadata(key: string, value: string): Promise<void> {
    const now = new Date().toISOString();
    await this.executeSql(QUERIES.setSyncMetadata, [key, value, now]);
  }

  // ========== USER PROFILE ==========

  async getUserProfile(): Promise<any | null> {
    const results = await this.executeSql(QUERIES.getUserProfile);
    if (results.rows.length > 0) {
      const row = results.rows.item(0);
      return {
        ...row,
        data: JSON.parse(row.data),
      };
    }
    return null;
  }

  async upsertUserProfile(profile: any): Promise<void> {
    const now = new Date().toISOString();
    await this.executeSql(QUERIES.upsertUserProfile, [
      profile.id,
      profile.username,
      profile.role,
      profile.first_login,
      JSON.stringify(profile),
      now,
    ]);
  }

  async clearUserProfile(): Promise<void> {
    await this.executeSql(QUERIES.clearUserProfile);
  }

  // ========== PATIENT INFO ==========

  async getPatientInfo(id: number): Promise<any | null> {
    const results = await this.executeSql(QUERIES.getPatientInfo, [id]);
    if (results.rows.length > 0) {
      const row = results.rows.item(0);
      return {
        ...row,
        data: JSON.parse(row.data),
      };
    }
    return null;
  }

  async upsertPatientInfo(patient: any): Promise<void> {
    const now = new Date().toISOString();
    await this.executeSql(QUERIES.upsertPatientInfo, [
      patient.id,
      patient.name,
      patient.location?.latitude ?? null,
      patient.location?.longitude ?? null,
      patient.address ?? null,
      patient.phone ?? null,
      JSON.stringify(patient),
      now,
    ]);
  }

  // ========== STATISTICS ==========

  /**
   * Obtiene estadísticas de la base de datos
   */
  async getStats(): Promise<any> {
    const stats = {
      routes: 0,
      visits: 0,
      unsyncedLocations: 0,
      unsyncedStatusChanges: 0,
      databaseSize: 0,
    };

    try {
      const routesResult = await this.executeSql('SELECT COUNT(*) as count FROM routes WHERE deleted_at IS NULL');
      stats.routes = routesResult.rows.item(0).count;

      const visitsResult = await this.executeSql('SELECT COUNT(*) as count FROM visits WHERE deleted_at IS NULL');
      stats.visits = visitsResult.rows.item(0).count;

      const locationsResult = await this.executeSql('SELECT COUNT(*) as count FROM location_queue WHERE synced = 0');
      stats.unsyncedLocations = locationsResult.rows.item(0).count;

      const statusResult = await this.executeSql('SELECT COUNT(*) as count FROM status_queue WHERE synced = 0');
      stats.unsyncedStatusChanges = statusResult.rows.item(0).count;

      return stats;
    } catch (error) {
      console.error('[DatabaseService] Error al obtener estadísticas:', error);
      return stats;
    }
  }
}

// Singleton instance
const databaseService = new DatabaseService();

export default databaseService;
