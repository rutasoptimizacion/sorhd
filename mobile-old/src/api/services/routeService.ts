/**
 * Servicio de Rutas
 *
 * Maneja la obtención de rutas asignadas al equipo clínico
 */

import apiClient from '../client';

// ============================================
// TIPOS
// ============================================
export interface RouteWithDetails {
  id: number;
  vehicle_id: number;
  route_date: string;
  status: 'draft' | 'active' | 'in_progress' | 'completed' | 'cancelled';
  total_distance_km: number | null;
  total_duration_minutes: number | null;
  created_at: string;
  updated_at: string;
  vehicle: {
    id: number;
    identifier: string;
    vehicle_type: string;
    capacity: number;
  };
  assigned_personnel: Array<{
    id: number;
    name: string;
    phone: string | null;
    skills: Array<{id: number; name: string}>;
  }>;
  visits: Array<{
    id: number;
    route_id: number;
    case_id: number;
    sequence_number: number;
    estimated_arrival_time: string | null;
    estimated_departure_time: string | null;
    actual_arrival_time: string | null;
    actual_departure_time: string | null;
    status: string;
    notes: string | null;
    case: {
      id: number;
      patient_id: number;
      care_type_id: number;
      scheduled_date: string;
      priority: string;
      status: string;
      location: {
        latitude: number;
        longitude: number;
      };
      patient: {
        id: number;
        name: string;
        phone: string | null;
        address: string | null;
      };
      care_type: {
        id: number;
        name: string;
        duration_minutes: number;
      };
    };
  }>;
}

// ============================================
// SERVICIOS
// ============================================

/**
 * Obtener rutas asignadas al personnel actual
 */
export const getMyRoutes = async (params?: {
  date?: string;
  status?: string;
}): Promise<RouteWithDetails[]> => {
  const response = await apiClient.get('/routes/my-routes', {params});
  return response.data;
};

/**
 * Obtener detalle de una ruta específica
 */
export const getRouteById = async (routeId: number): Promise<RouteWithDetails> => {
  const response = await apiClient.get(`/routes/${routeId}`);
  return response.data;
};

/**
 * Obtener rutas activas (en progreso)
 */
export const getActiveRoutes = async (): Promise<RouteWithDetails[]> => {
  const response = await apiClient.get('/routes/active');
  return response.data;
};

export default {
  getMyRoutes,
  getRouteById,
  getActiveRoutes,
};
