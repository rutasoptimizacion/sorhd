import apiClient from '../client';
import {Route, GetMyRoutesParams} from '../../types';

export const routeService = {
  /**
   * Obtener rutas asignadas al personnel actual
   * Para uso del Clinical Team
   */
  async getMyRoutes(params?: GetMyRoutesParams): Promise<Route[]> {
    const response = await apiClient.get<Route[]>('/routes/my-routes', {
      params,
    });
    return response.data;
  },

  /**
   * Obtener detalle de una ruta por ID
   */
  async getRouteById(routeId: number): Promise<Route> {
    const response = await apiClient.get<Route>(`/routes/${routeId}`);
    return response.data;
  },

  /**
   * Obtener rutas activas
   */
  async getActiveRoutes(): Promise<Route[]> {
    const response = await apiClient.get<Route[]>('/routes/active');
    return response.data;
  },
};
