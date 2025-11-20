/**
 * Contexto de Autenticación
 *
 * Maneja el estado de autenticación del usuario usando Context API.
 * NO usa Redux para mantener simplicidad (ideal para adultos mayores).
 */

import React, {createContext, useContext, useState, useEffect, ReactNode} from 'react';
import * as Keychain from 'react-native-keychain';

// ============================================
// TIPOS
// ============================================
export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  role: 'admin' | 'clinical_team' | 'patient';
  is_active: number;
  first_login: number; // 1 = needs activation, 0 = activated
  created_at: string;
  updated_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

interface AuthContextType {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  needsActivation: boolean;
  login: (tokens: AuthTokens, user: User) => Promise<void>;
  logout: () => Promise<void>;
  activate: (tokens: AuthTokens, user: User) => Promise<void>;
  updateTokens: (tokens: AuthTokens) => Promise<void>;
}

// ============================================
// CONTEXTO
// ============================================
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// ============================================
// PROVIDER
// ============================================
interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({children}) => {
  const [user, setUser] = useState<User | null>(null);
  const [tokens, setTokens] = useState<AuthTokens | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Cargar datos almacenados al iniciar
  useEffect(() => {
    loadStoredAuth();
  }, []);

  const loadStoredAuth = async () => {
    try {
      // Cargar tokens del Keychain (seguro)
      const credentials = await Keychain.getGenericPassword({
        service: 'sorhd.auth',
      });

      if (credentials) {
        const storedTokens: AuthTokens = JSON.parse(credentials.password);
        setTokens(storedTokens);

        // Cargar usuario de AsyncStorage
        const AsyncStorage = require('@react-native-async-storage/async-storage').default;
        const storedUser = await AsyncStorage.getItem('@user');
        if (storedUser) {
          setUser(JSON.parse(storedUser));
        }
      }
    } catch (error) {
      console.error('Error loading stored auth:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (newTokens: AuthTokens, newUser: User) => {
    try {
      // Guardar tokens en Keychain (seguro)
      await Keychain.setGenericPassword('tokens', JSON.stringify(newTokens), {
        service: 'sorhd.auth',
      });

      // Guardar usuario en AsyncStorage
      const AsyncStorage = require('@react-native-async-storage/async-storage').default;
      await AsyncStorage.setItem('@user', JSON.stringify(newUser));

      setTokens(newTokens);
      setUser(newUser);
    } catch (error) {
      console.error('Error storing auth:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      // Limpiar Keychain
      await Keychain.resetGenericPassword({service: 'sorhd.auth'});

      // Limpiar AsyncStorage
      const AsyncStorage = require('@react-native-async-storage/async-storage').default;
      await AsyncStorage.removeItem('@user');

      setTokens(null);
      setUser(null);
    } catch (error) {
      console.error('Error during logout:', error);
    }
  };

  const activate = async (newTokens: AuthTokens, updatedUser: User) => {
    // Igual que login, actualiza el usuario activado
    await login(newTokens, updatedUser);
  };

  const updateTokens = async (newTokens: AuthTokens) => {
    try {
      await Keychain.setGenericPassword('tokens', JSON.stringify(newTokens), {
        service: 'sorhd.auth',
      });
      setTokens(newTokens);
    } catch (error) {
      console.error('Error updating tokens:', error);
      throw error;
    }
  };

  const isAuthenticated = !!user && !!tokens;
  const needsActivation = user?.first_login === 1;

  return (
    <AuthContext.Provider
      value={{
        user,
        tokens,
        isAuthenticated,
        isLoading,
        needsActivation,
        login,
        logout,
        activate,
        updateTokens,
      }}>
      {children}
    </AuthContext.Provider>
  );
};

// ============================================
// HOOK PERSONALIZADO
// ============================================
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
