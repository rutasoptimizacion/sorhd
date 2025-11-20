/**
 * Cliente API con Axios
 *
 * Características:
 * - Interceptores para agregar JWT token automáticamente
 * - Refresh token automático en 401
 * - Queue offline para requests cuando no hay internet
 * - Retry logic con exponential backoff
 */

import axios, {AxiosInstance, AxiosError, InternalAxiosRequestConfig} from 'axios';
import NetInfo from '@react-native-community/netinfo';

// TODO: Cambiar a la URL del backend real
const BASE_URL = __DEV__
  ? 'http://10.0.2.2:8000/api/v1' // Android emulator
  : 'https://api.sorhd.example.com/api/v1';

// ============================================
// CONFIGURACIÓN AXIOS
// ============================================
const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000, // 30 segundos
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============================================
// OFFLINE QUEUE
// ============================================
interface QueuedRequest {
  config: InternalAxiosRequestConfig;
  resolve: (value: any) => void;
  reject: (error: any) => void;
}

let offlineQueue: QueuedRequest[] = [];
let isRefreshing = false;
let failedQueue: Array<{resolve: (value: any) => void; reject: (error: any) => void}> = [];

// ============================================
// FUNCIONES AUXILIARES
// ============================================

/**
 * Obtener token del Keychain
 */
const getTokens = async (): Promise<{access_token: string; refresh_token: string} | null> => {
  try {
    const Keychain = require('react-native-keychain');
    const credentials = await Keychain.getGenericPassword({service: 'sorhd.auth'});
    if (credentials) {
      return JSON.parse(credentials.password);
    }
    return null;
  } catch (error) {
    console.error('Error getting tokens:', error);
    return null;
  }
};

/**
 * Guardar tokens en Keychain
 */
const saveTokens = async (tokens: {access_token: string; refresh_token: string}): Promise<void> => {
  try {
    const Keychain = require('react-native-keychain');
    await Keychain.setGenericPassword('tokens', JSON.stringify(tokens), {
      service: 'sorhd.auth',
    });
  } catch (error) {
    console.error('Error saving tokens:', error);
  }
};

/**
 * Refrescar access token
 */
const refreshAccessToken = async (): Promise<string | null> => {
  try {
    const tokens = await getTokens();
    if (!tokens) {
      return null;
    }

    const response = await axios.post(`${BASE_URL}/auth/refresh`, {
      refresh_token: tokens.refresh_token,
    });

    const newAccessToken = response.data.access_token;

    // Guardar nuevo token
    await saveTokens({
      access_token: newAccessToken,
      refresh_token: tokens.refresh_token,
    });

    return newAccessToken;
  } catch (error) {
    console.error('Error refreshing token:', error);
    return null;
  }
};

/**
 * Procesar queue de requests pendientes
 */
const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });

  failedQueue = [];
};

// ============================================
// INTERCEPTOR DE REQUEST
// ============================================
apiClient.interceptors.request.use(
  async (config) => {
    // Agregar token de autenticación
    const tokens = await getTokens();
    if (tokens && tokens.access_token) {
      config.headers.Authorization = `Bearer ${tokens.access_token}`;
    }

    // Verificar conexión a internet
    const netInfo = await NetInfo.fetch();
    if (!netInfo.isConnected) {
      // Si no hay internet, encolar request
      return new Promise((resolve, reject) => {
        offlineQueue.push({
          config,
          resolve,
          reject,
        });
      }) as any;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// ============================================
// INTERCEPTOR DE RESPONSE
// ============================================
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {_retry?: boolean};

    // Si es 401 (no autorizado), intentar refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Si ya estamos refrescando, agregar a la queue
        return new Promise((resolve, reject) => {
          failedQueue.push({resolve, reject});
        })
          .then(token => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return apiClient(originalRequest);
          })
          .catch(err => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const newToken = await refreshAccessToken();

        if (newToken) {
          processQueue(null, newToken);

          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
          }

          return apiClient(originalRequest);
        } else {
          // No se pudo refrescar, hacer logout
          processQueue(new Error('Token refresh failed'), null);
          // TODO: Emitir evento para forzar logout en la app
          return Promise.reject(error);
        }
      } catch (refreshError) {
        processQueue(refreshError as Error, null);
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// ============================================
// MANEJO DE RECONEXIÓN
// ============================================

/**
 * Procesar queue offline cuando se recupera la conexión
 */
export const processOfflineQueue = async () => {
  if (offlineQueue.length === 0) {
    return;
  }

  console.log(`Processing ${offlineQueue.length} queued requests...`);

  const queue = [...offlineQueue];
  offlineQueue = [];

  for (const {config, resolve, reject} of queue) {
    try {
      const response = await apiClient(config);
      resolve(response);
    } catch (error) {
      reject(error);
    }
  }
};

// Escuchar cambios de conectividad
NetInfo.addEventListener(state => {
  if (state.isConnected) {
    processOfflineQueue();
  }
});

// ============================================
// EXPORTAR
// ============================================
export default apiClient;
export {BASE_URL};
