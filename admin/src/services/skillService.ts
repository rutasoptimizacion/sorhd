import apiClient from './api'
import type { Skill, SkillCreate, SkillUpdate, PaginatedResponse } from '@/types'

export const skillService = {
  // Get all skills
  getAll: async (): Promise<Skill[]> => {
    const response = await apiClient.get<PaginatedResponse<Skill>>('/skills')
    return response.data.items
  },

  // Get skill by ID
  getById: async (id: number): Promise<Skill> => {
    const response = await apiClient.get<Skill>(`/skills/${id}`)
    return response.data
  },

  // Create skill
  create: async (data: SkillCreate): Promise<Skill> => {
    const response = await apiClient.post<Skill>('/skills', data)
    return response.data
  },

  // Update skill
  update: async (id: number, data: SkillUpdate): Promise<Skill> => {
    const response = await apiClient.put<Skill>(`/skills/${id}`, data)
    return response.data
  },

  // Delete skill
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/skills/${id}`)
  },
}
