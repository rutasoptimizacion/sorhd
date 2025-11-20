/**
 * OfflineQueueService
 *
 * Servicio para manejar operaciones cuando no hay conexión a internet
 * Encola operaciones y las procesa cuando se recupera la conexión
 */

import NetInfo from '@react-native-community/netinfo';
import databaseService from './DatabaseService';
import syncService from './SyncService';

export enum OperationType {
  STATUS_CHANGE = 'status_change',
  LOCATION_UPDATE = 'location_update',
  ROUTE_UPDATE = 'route_update',
}

export interface QueuedOperation {
  id: string;
  type: OperationType;
  data: any;
  timestamp: string;
  retryCount: number;
  maxRetries: number;
}

class OfflineQueueService {
  private queue: Map<string, QueuedOperation> = new Map();
  private isProcessing: boolean = false;
  private networkUnsubscribe: (() => void) | null = null;

  /**
   * Inicializa el servicio de cola offline
   */
  initialize(): void {
    console.log('[OfflineQueueService] Inicializando servicio de cola offline...');

    // Escuchar cambios de conectividad
    this.networkUnsubscribe = NetInfo.addEventListener(state => {
      if (state.isConnected && this.queue.size > 0 && !this.isProcessing) {
        console.log('[OfflineQueueService] Conexión recuperada, procesando cola...');
        this.processQueue().catch(error => {
          console.error('[OfflineQueueService] Error al procesar cola:', error);
        });
      }
    });

    console.log('[OfflineQueueService] Servicio inicializado');
  }

  /**
   * Detiene el servicio
   */
  stop(): void {
    if (this.networkUnsubscribe) {
      this.networkUnsubscribe();
      this.networkUnsubscribe = null;
    }
    this.queue.clear();
    console.log('[OfflineQueueService] Servicio detenido');
  }

  /**
   * Encola un cambio de estado de visita
   */
  async enqueueStatusChange(
    visitId: number,
    oldStatus: string | undefined,
    newStatus: string,
    notes?: string
  ): Promise<void> {
    const operationId = `status_${visitId}_${Date.now()}`;
    const timestamp = new Date().toISOString();

    // Guardar en base de datos
    await databaseService.insertStatusChange({
      visit_id: visitId,
      old_status: oldStatus,
      new_status: newStatus,
      notes: notes,
      timestamp: timestamp,
    });

    // Agregar a cola en memoria
    this.queue.set(operationId, {
      id: operationId,
      type: OperationType.STATUS_CHANGE,
      data: {
        visit_id: visitId,
        old_status: oldStatus,
        new_status: newStatus,
        notes: notes,
      },
      timestamp: timestamp,
      retryCount: 0,
      maxRetries: 5,
    });

    console.log(`[OfflineQueueService] Cambio de estado encolado: ${operationId}`);

    // Intentar procesar si hay conexión
    const netInfo = await NetInfo.fetch();
    if (netInfo.isConnected && !this.isProcessing) {
      await this.processQueue();
    }
  }

  /**
   * Encola una actualización de ubicación GPS
   */
  async enqueueLocationUpdate(
    routeId: number | undefined,
    latitude: number,
    longitude: number,
    speed?: number,
    heading?: number,
    accuracy?: number
  ): Promise<void> {
    const timestamp = new Date().toISOString();

    // Guardar en base de datos
    await databaseService.insertLocation({
      route_id: routeId,
      latitude: latitude,
      longitude: longitude,
      speed_kmh: speed,
      heading: heading,
      accuracy: accuracy,
      timestamp: timestamp,
    });

    console.log('[OfflineQueueService] Ubicación encolada');

    // Las ubicaciones se sincronizan en lote por SyncService
    // No necesitamos procesarlas inmediatamente
  }

  /**
   * Procesa la cola de operaciones pendientes
   */
  private async processQueue(): Promise<void> {
    if (this.isProcessing) {
      console.log('[OfflineQueueService] Ya hay un proceso en ejecución');
      return;
    }

    // Verificar conexión
    const netInfo = await NetInfo.fetch();
    if (!netInfo.isConnected) {
      console.log('[OfflineQueueService] Sin conexión, no se puede procesar cola');
      return;
    }

    this.isProcessing = true;

    try {
      console.log(`[OfflineQueueService] Procesando ${this.queue.size} operaciones en cola...`);

      // Delegar la sincronización al SyncService
      await syncService.syncAll();

      // Limpiar cola de operaciones completadas
      this.queue.clear();

      console.log('[OfflineQueueService] Cola procesada exitosamente');
    } catch (error) {
      console.error('[OfflineQueueService] Error al procesar cola:', error);
      // La cola permanecerá y se reintentará en la próxima oportunidad
    } finally {
      this.isProcessing = false;
    }
  }

  /**
   * Obtiene el estado de la cola
   */
  getQueueStatus(): {
    queueSize: number;
    isProcessing: boolean;
    operations: QueuedOperation[];
  } {
    return {
      queueSize: this.queue.size,
      isProcessing: this.isProcessing,
      operations: Array.from(this.queue.values()),
    };
  }

  /**
   * Limpia la cola (usar solo en casos excepcionales como logout)
   */
  clearQueue(): void {
    this.queue.clear();
    console.log('[OfflineQueueService] Cola limpiada');
  }

  /**
   * Fuerza el procesamiento de la cola inmediatamente
   */
  async forceProcessQueue(): Promise<void> {
    console.log('[OfflineQueueService] Procesamiento forzado de cola...');
    await this.processQueue();
  }

  /**
   * Obtiene estadísticas de la cola
   */
  async getQueueStats(): Promise<{
    totalInQueue: number;
    statusChanges: number;
    locations: number;
    oldestItem?: string;
  }> {
    const dbStats = await databaseService.getStats();

    const operations = Array.from(this.queue.values());
    const oldestOperation = operations.reduce<QueuedOperation | null>((oldest, current) => {
      if (!oldest) return current;
      return new Date(current.timestamp) < new Date(oldest.timestamp) ? current : oldest;
    }, null);

    return {
      totalInQueue: this.queue.size,
      statusChanges: dbStats.unsyncedStatusChanges,
      locations: dbStats.unsyncedLocations,
      oldestItem: oldestOperation?.timestamp,
    };
  }
}

// Singleton instance
const offlineQueueService = new OfflineQueueService();

export default offlineQueueService;
