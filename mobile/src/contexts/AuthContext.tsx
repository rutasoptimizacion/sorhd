import React, {createContext, useContext, useState, useEffect, ReactNode} from 'react';
import * as Keychain from 'react-native-keychain';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {User, AuthTokens, LoginRequest, ActivateAccountRequest} from '../types';
import {authService} from '../api/services';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  needsActivation: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  activate: (request: ActivateAccountRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({children}) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Recuperar sesión al inicio
  useEffect(() => {
    restoreSession();
  }, []);

  const restoreSession = async () => {
    // Timeout de seguridad: si después de 5 segundos no se resolvió, forzar isLoading = false
    const timeoutId = setTimeout(() => {
      console.warn('restoreSession timeout - forzando isLoading = false');
      setIsLoading(false);
    }, 5000);

    try {
      setIsLoading(true);

      // Verificar si existen tokens
      const credentials = await Keychain.getGenericPassword({
        service: 'auth_tokens',
      });

      if (!credentials || !credentials.password) {
        clearTimeout(timeoutId);
        setIsLoading(false);
        return;
      }

      // Verificar si existe user en AsyncStorage
      const userJson = await AsyncStorage.getItem('user');
      if (!userJson) {
        clearTimeout(timeoutId);
        setIsLoading(false);
        return;
      }

      const storedUser: User = JSON.parse(userJson);
      setUser(storedUser);
      clearTimeout(timeoutId);
    } catch (error) {
      console.error('Error al restaurar sesión:', error);
      clearTimeout(timeoutId);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (credentials: LoginRequest) => {
    try {
      console.log('AuthContext: Intentando login con', credentials.username);
      const response = await authService.login(credentials);
      console.log('AuthContext: Login exitoso, usuario:', response.user.username, 'rol:', response.user.role);

      // Guardar tokens en Keychain (seguro)
      await Keychain.setGenericPassword('auth', JSON.stringify(response.tokens), {
        service: 'auth_tokens',
      });
      console.log('AuthContext: Tokens guardados en Keychain');

      // Guardar usuario en AsyncStorage
      await AsyncStorage.setItem('user', JSON.stringify(response.user));
      console.log('AuthContext: Usuario guardado en AsyncStorage');

      setUser(response.user);
      console.log('AuthContext: Estado de user actualizado');
    } catch (error) {
      console.error('Error en login:', error);
      throw error;
    }
  };

  const activate = async (request: ActivateAccountRequest) => {
    try {
      const response = await authService.activateAccount(request);

      // Actualizar tokens
      await Keychain.setGenericPassword('auth', JSON.stringify(response.tokens), {
        service: 'auth_tokens',
      });

      // Actualizar usuario (first_login = 0)
      await AsyncStorage.setItem('user', JSON.stringify(response.user));

      setUser(response.user);
    } catch (error) {
      console.error('Error en activación:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      // Llamar endpoint de logout (si falla, continuamos igual)
      await authService.logout();
    } catch (error) {
      console.error('Error en logout:', error);
    } finally {
      // Limpiar tokens y usuario
      await Keychain.resetGenericPassword({service: 'auth_tokens'});
      await AsyncStorage.removeItem('user');
      setUser(null);
    }
  };

  const refreshUser = async () => {
    try {
      const updatedUser = await authService.getCurrentUser();
      await AsyncStorage.setItem('user', JSON.stringify(updatedUser));
      setUser(updatedUser);
    } catch (error) {
      console.error('Error al refrescar usuario:', error);
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    needsActivation: user?.first_login === 1,
    isLoading,
    login,
    activate,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe ser usado dentro de un AuthProvider');
  }
  return context;
};
