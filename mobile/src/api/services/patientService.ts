import apiClient from '../client';
import {MyVisitResponse, VisitTeamResponse} from '../../types';

export const patientService = {
  /**
   * Obtener próxima visita del paciente actual
   * Incluye info de la ruta, vehículo, personnel y ETA
   */
  async getMyVisit(): Promise<MyVisitResponse> {
    const response = await apiClient.get<MyVisitResponse>('/visits/my-visit');
    return response.data;
  },

  /**
   * Obtener información del equipo clínico asignado a una visita
   * Incluye vehículo y lista de personnel con skills
   */
  async getVisitTeam(visitId: number): Promise<VisitTeamResponse> {
    const response = await apiClient.get<VisitTeamResponse>(
      `/visits/${visitId}/team`,
    );
    return response.data;
  },
};
