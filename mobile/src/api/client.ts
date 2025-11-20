import axios, {AxiosInstance, AxiosError, InternalAxiosRequestConfig} from 'axios';
import * as Keychain from 'react-native-keychain';
import {AuthTokens} from '../types';

// Base URL para Android emulator apunta a localhost del host
const BASE_URL = __DEV__
  ? 'http://10.0.2.2:8000/api/v1'
  : 'https://api.sorhd.example.com/api/v1';

class ApiClient {
  private client: AxiosInstance;
  private isRefreshing = false;
  private failedQueue: Array<{
    resolve: (value?: unknown) => void;
    reject: (reason?: unknown) => void;
  }> = [];

  constructor() {
    this.client = axios.create({
      baseURL: BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor: agregar JWT token
    this.client.interceptors.request.use(
      async (config: InternalAxiosRequestConfig) => {
        try {
          const credentials = await Keychain.getGenericPassword({
            service: 'auth_tokens',
          });

          if (credentials && credentials.password) {
            const tokens: AuthTokens = JSON.parse(credentials.password);
            config.headers.Authorization = `Bearer ${tokens.access_token}`;
          }
        } catch (error) {
          console.error('Error getting auth token:', error);
        }

        return config;
      },
      error => Promise.reject(error),
    );

    // Response interceptor: manejar 401 y refresh token
    this.client.interceptors.response.use(
      response => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & {
          _retry?: boolean;
        };

        // Si es 401 y no es el endpoint de login/refresh
        if (
          error.response?.status === 401 &&
          !originalRequest._retry &&
          !originalRequest.url?.includes('/auth/login') &&
          !originalRequest.url?.includes('/auth/refresh')
        ) {
          if (this.isRefreshing) {
            // Ya hay un refresh en progreso, encolar este request
            return new Promise((resolve, reject) => {
              this.failedQueue.push({resolve, reject});
            })
              .then(() => {
                return this.client(originalRequest);
              })
              .catch(err => {
                return Promise.reject(err);
              });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            const credentials = await Keychain.getGenericPassword({
              service: 'auth_tokens',
            });

            if (!credentials || !credentials.password) {
              throw new Error('No refresh token available');
            }

            const tokens: AuthTokens = JSON.parse(credentials.password);

            // Intentar refresh token
            const response = await this.client.post('/auth/refresh', {
              refresh_token: tokens.refresh_token,
            });

            const newTokens: AuthTokens = response.data.tokens;

            // Guardar nuevos tokens
            await Keychain.setGenericPassword('auth', JSON.stringify(newTokens), {
              service: 'auth_tokens',
            });

            // Procesar cola de requests fallidos
            this.failedQueue.forEach(promise => promise.resolve());
            this.failedQueue = [];

            // Reintentar request original
            return this.client(originalRequest);
          } catch (refreshError) {
            // Refresh falló, limpiar tokens y rechazar todos los requests encolados
            this.failedQueue.forEach(promise => promise.reject(refreshError));
            this.failedQueue = [];

            await Keychain.resetGenericPassword({service: 'auth_tokens'});

            return Promise.reject(refreshError);
          } finally {
            this.isRefreshing = false;
          }
        }

        return Promise.reject(error);
      },
    );
  }

  public getInstance(): AxiosInstance {
    return this.client;
  }

  public getBaseURL(): string {
    return BASE_URL;
  }
}

export const apiClient = new ApiClient();
export default apiClient.getInstance();
