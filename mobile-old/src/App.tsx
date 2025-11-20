/**
 * App.tsx - Punto de entrada de la aplicación
 *
 * Configura:
 * - React Query para manejo de estado del servidor
 * - AuthProvider para autenticación
 * - Navegación principal
 */

import React from 'react';
import {StatusBar, SafeAreaView, StyleSheet} from 'react-native';
import {QueryClient, QueryClientProvider} from '@tanstack/react-query';
import {AuthProvider} from './contexts/AuthContext';
import {AppNavigator} from './navigation';
import {elderlyTheme} from './theme/elderlyTheme';

// Configurar React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Cache por 5 minutos por defecto
      staleTime: 5 * 60 * 1000,
      // Reintenta 2 veces en caso de error
      retry: 2,
      // Refetch al reconectar
      refetchOnReconnect: true,
      // NO refetch al volver a la pantalla (para adultos mayores, evitar cambios inesperados)
      refetchOnWindowFocus: false,
    },
    mutations: {
      // Reintenta 1 vez en caso de error
      retry: 1,
    },
  },
});

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <SafeAreaView style={styles.container}>
          <StatusBar
            barStyle="dark-content"
            backgroundColor={elderlyTheme.colors.background}
          />
          <AppNavigator />
        </SafeAreaView>
      </AuthProvider>
    </QueryClientProvider>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: elderlyTheme.colors.background,
  },
});

export default App;
