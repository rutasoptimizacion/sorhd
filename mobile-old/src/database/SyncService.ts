/**
 * SyncService
 *
 * Servicio de sincronización bidireccional entre SQLite local y el backend
 * Maneja sincronización inteligente con manejo de conflictos
 */

import NetInfo from '@react-native-community/netinfo';
import databaseService from './DatabaseService';
import apiClient from '../api/client';
import {SYNC_KEYS} from './schema';

export interface SyncStatus {
  isOnline: boolean;
  isSyncing: boolean;
  lastSyncTime?: string;
  unsyncedItems: {
    routes: number;
    visits: number;
    locations: number;
    statusChanges: number;
  };
  errors: string[];
}

class SyncService {
  private isSyncing: boolean = false;
  private syncInterval: NodeJS.Timeout | null = null;
  private networkUnsubscribe: (() => void) | null = null;

  /**
   * Inicializa el servicio de sincronización
   * Configura listeners de red y sincronización periódica
   */
  async initialize(): Promise<void> {
    console.log('[SyncService] Inicializando servicio de sincronización...');

    // Escuchar cambios de conectividad
    this.networkUnsubscribe = NetInfo.addEventListener(state => {
      console.log('[SyncService] Estado de red:', state.isConnected);

      // Si recuperamos conexión, intentar sincronizar
      if (state.isConnected && !this.isSyncing) {
        console.log('[SyncService] Conexión recuperada, iniciando sincronización...');
        this.syncAll().catch(error => {
          console.error('[SyncService] Error en auto-sync:', error);
        });
      }
    });

    // Sincronización periódica cada 5 minutos si hay conexión
    this.syncInterval = setInterval(async () => {
      const netInfo = await NetInfo.fetch();
      if (netInfo.isConnected && !this.isSyncing) {
        console.log('[SyncService] Sincronización periódica...');
        await this.syncAll().catch(error => {
          console.error('[SyncService] Error en sync periódico:', error);
        });
      }
    }, 5 * 60 * 1000); // 5 minutos

    console.log('[SyncService] Servicio inicializado');
  }

  /**
   * Detiene el servicio de sincronización
   */
  stop(): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }

    if (this.networkUnsubscribe) {
      this.networkUnsubscribe();
      this.networkUnsubscribe = null;
    }

    console.log('[SyncService] Servicio detenido');
  }

  /**
   * Sincroniza todos los datos pendientes
   */
  async syncAll(): Promise<void> {
    if (this.isSyncing) {
      console.log('[SyncService] Sincronización ya en progreso, saltando...');
      return;
    }

    // Verificar conexión
    const netInfo = await NetInfo.fetch();
    if (!netInfo.isConnected) {
      console.log('[SyncService] Sin conexión, saltando sincronización');
      return;
    }

    this.isSyncing = true;
    await databaseService.setSyncMetadata(SYNC_KEYS.SYNC_IN_PROGRESS, '1');

    try {
      console.log('[SyncService] Iniciando sincronización completa...');

      // 1. Sincronizar cambios de estado (prioridad alta)
      await this.syncStatusChanges();

      // 2. Sincronizar ubicaciones GPS
      await this.syncLocations();

      // 3. Descargar actualizaciones del servidor (rutas y visitas)
      await this.pullUpdates();

      // 4. Limpiar datos antiguos
      await this.cleanupOldData();

      // Actualizar timestamp de última sincronización
      const now = new Date().toISOString();
      await databaseService.setSyncMetadata(SYNC_KEYS.LAST_FULL_SYNC, now);

      console.log('[SyncService] Sincronización completa exitosa');
    } catch (error) {
      console.error('[SyncService] Error en sincronización:', error);
      throw error;
    } finally {
      this.isSyncing = false;
      await databaseService.setSyncMetadata(SYNC_KEYS.SYNC_IN_PROGRESS, '0');
    }
  }

  /**
   * Sincroniza cambios de estado de visitas con el servidor
   */
  private async syncStatusChanges(): Promise<void> {
    try {
      const changes = await databaseService.getUnsyncedStatusChanges(50);

      if (changes.length === 0) {
        console.log('[SyncService] No hay cambios de estado por sincronizar');
        return;
      }

      console.log(`[SyncService] Sincronizando ${changes.length} cambios de estado...`);

      for (const change of changes) {
        try {
          // Enviar cambio al servidor
          await apiClient.patch(`/visits/${change.visit_id}/status`, {
            status: change.new_status,
            notes: change.notes,
            timestamp: change.timestamp,
          });

          // Marcar como sincronizado
          await databaseService.markStatusSynced(change.id!);

          // Actualizar la visita local
          const visit = await databaseService.getVisitById(change.visit_id);
          if (visit) {
            const visitData = JSON.parse(visit.data);
            visitData.status = change.new_status;
            await databaseService.updateVisitStatus(
              change.visit_id,
              change.new_status,
              undefined,
              undefined,
              JSON.stringify(visitData)
            );
            await databaseService.markVisitSynced(change.visit_id);
          }

          console.log(`[SyncService] Cambio de estado ${change.id} sincronizado`);
        } catch (error: any) {
          console.error(`[SyncService] Error al sincronizar cambio ${change.id}:`, error);

          // Marcar intento fallido
          const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
          await databaseService.markStatusSyncAttempt(change.id!, errorMessage);

          // Si es error 404, marcar como sincronizado (la visita no existe en servidor)
          if (error.response?.status === 404) {
            await databaseService.markStatusSynced(change.id!);
          }
        }
      }

      const now = new Date().toISOString();
      await databaseService.setSyncMetadata(SYNC_KEYS.LAST_STATUS_SYNC, now);
    } catch (error) {
      console.error('[SyncService] Error en syncStatusChanges:', error);
      throw error;
    }
  }

  /**
   * Sincroniza ubicaciones GPS con el servidor
   */
  private async syncLocations(): Promise<void> {
    try {
      const locations = await databaseService.getUnsyncedLocations(100);

      if (locations.length === 0) {
        console.log('[SyncService] No hay ubicaciones por sincronizar');
        return;
      }

      console.log(`[SyncService] Sincronizando ${locations.length} ubicaciones GPS...`);

      // Agrupar ubicaciones por lote (batch)
      const batchSize = 20;
      for (let i = 0; i < locations.length; i += batchSize) {
        const batch = locations.slice(i, i + batchSize);

        try {
          // Enviar lote al servidor
          await apiClient.post('/tracking/locations/batch', {
            locations: batch.map(loc => ({
              route_id: loc.route_id,
              latitude: loc.latitude,
              longitude: loc.longitude,
              speed_kmh: loc.speed_kmh,
              heading: loc.heading,
              accuracy: loc.accuracy,
              timestamp: loc.timestamp,
            })),
          });

          // Marcar todas como sincronizadas
          for (const location of batch) {
            await databaseService.markLocationSynced(location.id!);
          }

          console.log(`[SyncService] Lote de ${batch.length} ubicaciones sincronizado`);
        } catch (error) {
          console.error('[SyncService] Error al sincronizar lote de ubicaciones:', error);

          // Marcar intentos fallidos
          for (const location of batch) {
            await databaseService.markLocationSyncAttempt(location.id!);
          }
        }
      }

      const now = new Date().toISOString();
      await databaseService.setSyncMetadata(SYNC_KEYS.LAST_LOCATION_SYNC, now);
    } catch (error) {
      console.error('[SyncService] Error en syncLocations:', error);
      throw error;
    }
  }

  /**
   * Descarga actualizaciones de rutas y visitas desde el servidor
   */
  private async pullUpdates(): Promise<void> {
    try {
      console.log('[SyncService] Descargando actualizaciones del servidor...');

      // Obtener última fecha de sincronización
      const lastSync = await databaseService.getSyncMetadata(SYNC_KEYS.LAST_ROUTE_SYNC);
      const today = new Date().toISOString().split('T')[0];

      // Descargar rutas del día actual
      const response = await apiClient.get('/routes/my-routes', {
        params: {
          date: today,
        },
      });

      const routes = response.data;

      for (const route of routes) {
        // Verificar si la ruta ya existe localmente
        const existingRoute = await databaseService.getRouteById(route.id);

        if (existingRoute) {
          // Comparar timestamps para detectar cambios
          const serverUpdated = new Date(route.updated_at).getTime();
          const localUpdated = new Date(existingRoute.updated_at).getTime();

          if (serverUpdated > localUpdated) {
            // El servidor tiene una versión más nueva, actualizar
            await databaseService.updateRoute(
              route.id,
              route.status,
              JSON.stringify(route)
            );
            await databaseService.markRouteSynced(route.id);
            console.log(`[SyncService] Ruta ${route.id} actualizada desde servidor`);
          }
        } else {
          // Insertar nueva ruta
          await databaseService.insertRoute({
            id: route.id,
            vehicle_id: route.vehicle_id,
            route_date: route.route_date,
            status: route.status,
            total_distance_km: route.total_distance_km,
            total_duration_minutes: route.total_duration_minutes,
            data: JSON.stringify(route),
            synced: 1,
          });
          console.log(`[SyncService] Nueva ruta ${route.id} insertada desde servidor`);
        }

        // Sincronizar visitas de la ruta
        if (route.visits && route.visits.length > 0) {
          for (const visit of route.visits) {
            const existingVisit = await databaseService.getVisitById(visit.id);

            if (existingVisit) {
              // Actualizar si el servidor tiene versión más nueva
              const serverUpdated = new Date(visit.updated_at).getTime();
              const localUpdated = new Date(existingVisit.updated_at).getTime();

              if (serverUpdated > localUpdated) {
                await databaseService.updateVisitStatus(
                  visit.id,
                  visit.status,
                  visit.actual_arrival_time,
                  visit.actual_departure_time,
                  JSON.stringify(visit)
                );
                await databaseService.markVisitSynced(visit.id);
                console.log(`[SyncService] Visita ${visit.id} actualizada desde servidor`);
              }
            } else {
              // Insertar nueva visita
              await databaseService.insertVisit({
                id: visit.id,
                route_id: visit.route_id,
                case_id: visit.case_id,
                sequence_number: visit.sequence_number,
                status: visit.status,
                estimated_arrival_time: visit.estimated_arrival_time,
                actual_arrival_time: visit.actual_arrival_time,
                actual_departure_time: visit.actual_departure_time,
                data: JSON.stringify(visit),
                synced: 1,
              });
              console.log(`[SyncService] Nueva visita ${visit.id} insertada desde servidor`);
            }
          }
        }
      }

      const now = new Date().toISOString();
      await databaseService.setSyncMetadata(SYNC_KEYS.LAST_ROUTE_SYNC, now);
      await databaseService.setSyncMetadata(SYNC_KEYS.LAST_VISIT_SYNC, now);

      console.log('[SyncService] Actualizaciones descargadas exitosamente');
    } catch (error) {
      console.error('[SyncService] Error en pullUpdates:', error);
      throw error;
    }
  }

  /**
   * Limpia datos antiguos ya sincronizados
   */
  private async cleanupOldData(): Promise<void> {
    try {
      console.log('[SyncService] Limpiando datos antiguos...');

      // Eliminar ubicaciones sincronizadas de hace más de 7 días
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
      await databaseService.deleteOldSyncedLocations(sevenDaysAgo.toISOString());

      // Eliminar cambios de estado sincronizados de hace más de 7 días
      await databaseService.deleteOldSyncedStatuses(sevenDaysAgo.toISOString());

      console.log('[SyncService] Limpieza completada');
    } catch (error) {
      console.error('[SyncService] Error en cleanup:', error);
      // No lanzar error, el cleanup es opcional
    }
  }

  /**
   * Obtiene el estado actual de sincronización
   */
  async getSyncStatus(): Promise<SyncStatus> {
    const netInfo = await NetInfo.fetch();
    const stats = await databaseService.getStats();
    const lastSyncTime = await databaseService.getSyncMetadata(SYNC_KEYS.LAST_FULL_SYNC);

    return {
      isOnline: netInfo.isConnected ?? false,
      isSyncing: this.isSyncing,
      lastSyncTime: lastSyncTime ?? undefined,
      unsyncedItems: {
        routes: 0, // Las rutas no se modifican localmente
        visits: stats.unsyncedStatusChanges, // Visitas con cambios de estado
        locations: stats.unsyncedLocations,
        statusChanges: stats.unsyncedStatusChanges,
      },
      errors: [],
    };
  }

  /**
   * Fuerza una sincronización inmediata
   */
  async forceSyncNow(): Promise<void> {
    console.log('[SyncService] Sincronización forzada por usuario...');
    await this.syncAll();
  }
}

// Singleton instance
const syncService = new SyncService();

export default syncService;
