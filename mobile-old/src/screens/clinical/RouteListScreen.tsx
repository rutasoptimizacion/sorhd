/**
 * RouteListScreen - Pantalla de lista de rutas (Equipo Clínico)
 * PLACEHOLDER - Se implementará completamente en Fase 3
 */

import React from 'react';
import {View, StyleSheet} from 'react-native';
import {elderlyTheme} from '../../theme/elderlyTheme';
import {BigText, BigButton} from '../../components';
import {useAuth} from '../../contexts/AuthContext';

export const RouteListScreen: React.FC = () => {
  const {user, logout} = useAuth();

  return (
    <View style={styles.container}>
      <BigText variant="xl" weight="bold" textAlign="center">
        Mis Rutas
      </BigText>
      <BigText variant="md" color={elderlyTheme.colors.textSecondary} textAlign="center" style={styles.welcome}>
        Bienvenido, {user?.full_name || user?.username}
      </BigText>
      <BigText variant="md" textAlign="center" style={styles.subtitle}>
        (Pantalla en desarrollo - Fase 3)
      </BigText>

      <BigButton
        title="Cerrar Sesión"
        onPress={logout}
        variant="secondary"
        style={styles.logoutButton}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: elderlyTheme.colors.background,
    padding: elderlyTheme.spacing.lg,
    justifyContent: 'center',
    alignItems: 'center',
  },
  welcome: {
    marginTop: elderlyTheme.spacing.md,
  },
  subtitle: {
    marginTop: elderlyTheme.spacing.sm,
    marginBottom: elderlyTheme.spacing.xl,
  },
  logoutButton: {
    marginTop: elderlyTheme.spacing.xl,
    minWidth: 200,
  },
});
