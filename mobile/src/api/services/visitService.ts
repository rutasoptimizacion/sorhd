import apiClient from '../client';
import {Visit, UpdateVisitStatusRequest} from '../../types';

export const visitService = {
  /**
   * Obtener detalle de una visita por ID
   */
  async getVisitById(visitId: number): Promise<Visit> {
    const response = await apiClient.get<Visit>(`/visits/${visitId}`);
    return response.data;
  },

  /**
   * Actualizar estado de una visita
   * Para uso del Clinical Team
   */
  async updateVisitStatus(
    visitId: number,
    request: UpdateVisitStatusRequest,
  ): Promise<Visit> {
    const response = await apiClient.patch<Visit>(
      `/visits/${visitId}/status`,
      request,
    );
    return response.data;
  },
};
