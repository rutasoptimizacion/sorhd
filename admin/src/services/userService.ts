import { apiClient } from './api'
import type { User, UserCreate, UserUpdate, PaginatedResponse } from '@/types'

export const userService = {
  // Get all users
  async getAll(): Promise<PaginatedResponse<User>> {
    const response = await apiClient.get<PaginatedResponse<User>>('/users')
    return response.data
  },

  // Get single user by ID
  async getById(id: number): Promise<User> {
    const response = await apiClient.get<User>(`/users/${id}`)
    return response.data
  },

  // Create new user
  async create(data: UserCreate): Promise<User> {
    const response = await apiClient.post<User>('/users', data)
    return response.data
  },

  // Update user
  async update(id: number, data: UserUpdate): Promise<User> {
    const response = await apiClient.put<User>(`/users/${id}`, data)
    return response.data
  },

  // Delete user
  async delete(id: number): Promise<void> {
    await apiClient.delete(`/users/${id}`)
  },
}
