import apiClient from '../client';
import {
  LoginRequest,
  LoginResponse,
  ActivateAccountRequest,
  ActivateAccountResponse,
  User,
  AuthTokens,
} from '../../types';

export const authService = {
  /**
   * Login con username y password
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post('/auth/login', {
      username: credentials.username,
      password: credentials.password,
    });

    // El backend devuelve: {access_token, refresh_token, token_type, user}
    // Necesitamos transformarlo a: {user, tokens}
    const data = response.data;
    return {
      user: data.user,
      tokens: {
        access_token: data.access_token,
        refresh_token: data.refresh_token,
        token_type: data.token_type,
      },
    };
  },

  /**
   * Activar cuenta (primera vez - establecer contraseña permanente)
   */
  async activateAccount(
    request: ActivateAccountRequest,
  ): Promise<ActivateAccountResponse> {
    const response = await apiClient.post<ActivateAccountResponse>(
      '/auth/activate',
      request,
    );
    return response.data;
  },

  /**
   * Obtener usuario actual
   */
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },

  /**
   * Refresh token (manejado automáticamente por el interceptor)
   */
  async refreshToken(refreshToken: string): Promise<{tokens: AuthTokens}> {
    const response = await apiClient.post<{tokens: AuthTokens}>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  /**
   * Logout
   */
  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout');
    } catch (error) {
      // Ignorar errores de logout (el token puede ya estar inválido)
      console.error('Error durante logout:', error);
    }
  },
};
