/**
 * Servicio de Autenticación
 *
 * Maneja login, activación de cuenta, y refresh de tokens
 */

import apiClient from '../client';
import {User, AuthTokens} from '../../contexts/AuthContext';

// ============================================
// TIPOS
// ============================================
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface ActivateAccountRequest {
  new_password: string;
}

// ============================================
// SERVICIOS
// ============================================

/**
 * Login - Autenticación de usuario
 */
export const login = async (credentials: LoginRequest): Promise<LoginResponse> => {
  const response = await apiClient.post('/auth/login', credentials);
  return response.data;
};

/**
 * Activar cuenta - Primera vez que el usuario establece contraseña
 */
export const activateAccount = async (data: ActivateAccountRequest): Promise<LoginResponse> => {
  const response = await apiClient.post('/auth/activate', data);
  return response.data;
};

/**
 * Obtener información del usuario actual
 */
export const getCurrentUser = async (): Promise<User> => {
  const response = await apiClient.get('/auth/me');
  return response.data;
};

/**
 * Refrescar access token
 */
export const refreshToken = async (refreshToken: string): Promise<{access_token: string}> => {
  const response = await apiClient.post('/auth/refresh', {
    refresh_token: refreshToken,
  });
  return response.data;
};

/**
 * Logout (placeholder - el token se limpia localmente)
 */
export const logout = async (): Promise<void> => {
  await apiClient.post('/auth/logout');
};

export default {
  login,
  activateAccount,
  getCurrentUser,
  refreshToken,
  logout,
};
