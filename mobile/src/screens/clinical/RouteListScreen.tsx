import React from 'react';
import {View, StyleSheet, ScrollView, RefreshControl, Alert} from 'react-native';
import {useQuery} from '@tanstack/react-query';
import {format} from 'date-fns';
import {es} from 'date-fns/locale';
import {useNavigation} from '@react-navigation/native';
import {StackNavigationProp} from '@react-navigation/stack';
import {useAuth} from '../../contexts/AuthContext';
import {routeService} from '../../api/services';
import {
  BigText,
  BigButton,
  BigCard,
  StatusBadge,
  LoadingSpinner,
  ErrorAlert,
} from '../../components';
import {elderlyTheme} from '../../theme/elderlyTheme';
import {RootStackParamList, Route} from '../../types';

type RouteListNavigationProp = StackNavigationProp<RootStackParamList, 'RouteList'>;

const RouteListScreen: React.FC = () => {
  const navigation = useNavigation<RouteListNavigationProp>();
  const {logout, user} = useAuth();

  const today = format(new Date(), 'yyyy-MM-dd');

  const {
    data: routes,
    isLoading,
    error,
    refetch,
    isRefetching,
  } = useQuery({
    queryKey: ['my-routes', today],
    queryFn: () => routeService.getMyRoutes({date: today}),
    staleTime: 30000, // 30 segundos
  });

  const handleLogout = () => {
    Alert.alert('Cerrar Sesión', '¿Está seguro que desea cerrar sesión?', [
      {text: 'Cancelar', style: 'cancel'},
      {
        text: 'Sí, cerrar',
        style: 'destructive',
        onPress: async () => {
          await logout();
        },
      },
    ]);
  };

  if (isLoading) {
    return <LoadingSpinner size="large" message="Cargando rutas..." />;
  }

  if (error) {
    return (
      <View style={styles.container}>
        <ErrorAlert
          message="Error al cargar las rutas. Intente nuevamente."
          onRetry={refetch}
        />
      </View>
    );
  }

  const todayRoute = routes?.[0];

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} />}>
      <View style={styles.header}>
        <BigText variant="xl" weight="bold">
          MIS RUTAS
        </BigText>
        <BigText variant="md" color={elderlyTheme.colors.textSecondary}>
          {format(new Date(), "EEEE d 'de' MMMM", {locale: es})}
        </BigText>
        <BigText variant="sm" color={elderlyTheme.colors.textSecondary} style={styles.username}>
          👤 {user?.username}
        </BigText>
      </View>

      {!todayRoute ? (
        <BigCard>
          <BigText variant="lg" weight="medium" style={styles.noRouteText}>
            📋 No tiene rutas asignadas para hoy
          </BigText>
        </BigCard>
      ) : (
        <BigCard elevation="large">
          <BigText variant="lg" weight="bold" style={styles.routeTitle}>
            🚗 Ruta #{todayRoute.id}
          </BigText>

          <View style={styles.infoRow}>
            <BigText variant="md" color={elderlyTheme.colors.textSecondary}>
              Vehículo:
            </BigText>
            <BigText variant="md" weight="medium">
              {todayRoute.vehicle.identifier}
            </BigText>
          </View>

          <View style={styles.infoRow}>
            <BigText variant="md" color={elderlyTheme.colors.textSecondary}>
              📍 Visitas:
            </BigText>
            <BigText variant="md" weight="medium">
              {todayRoute.visits.length}
            </BigText>
          </View>

          <View style={styles.infoRow}>
            <BigText variant="md" color={elderlyTheme.colors.textSecondary}>
              ⏱️ Horario:
            </BigText>
            <BigText variant="md" weight="medium">
              {todayRoute.start_time || '08:00'} - {todayRoute.end_time || '17:00'}
            </BigText>
          </View>

          <View style={styles.statusContainer}>
            <StatusBadge status={getRouteStatusAsVisitStatus(todayRoute.status)} size="large" />
          </View>

          <BigButton
            title="VER DETALLES"
            variant="primary"
            onPress={() => {
              if (todayRoute.visits.length > 0) {
                navigation.navigate('VisitDetail', {
                  visitId: todayRoute.visits[0].id,
                  routeId: todayRoute.id,
                });
              }
            }}
            fullWidth
            style={styles.button}
          />
        </BigCard>
      )}

      <BigButton
        title="CERRAR SESIÓN"
        variant="error"
        onPress={handleLogout}
        fullWidth
        style={styles.logoutButton}
      />
    </ScrollView>
  );
};

// Helper para convertir RouteStatus a VisitStatus para el badge
function getRouteStatusAsVisitStatus(
  status: string,
): 'pending' | 'en_route' | 'arrived' | 'in_progress' | 'completed' | 'cancelled' {
  const mapping: Record<string, any> = {
    planned: 'pending',
    active: 'in_progress',
    completed: 'completed',
    cancelled: 'cancelled',
  };
  return mapping[status] || 'pending';
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: elderlyTheme.colors.background,
  },
  content: {
    padding: elderlyTheme.spacing.lg,
  },
  header: {
    alignItems: 'center',
    marginBottom: elderlyTheme.spacing.lg,
  },
  username: {
    marginTop: elderlyTheme.spacing.sm,
  },
  noRouteText: {
    textAlign: 'center',
  },
  routeTitle: {
    marginBottom: elderlyTheme.spacing.md,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginVertical: elderlyTheme.spacing.xs,
  },
  statusContainer: {
    marginVertical: elderlyTheme.spacing.md,
    alignItems: 'center',
  },
  button: {
    marginTop: elderlyTheme.spacing.sm,
  },
  logoutButton: {
    marginTop: elderlyTheme.spacing.xl,
  },
});

export default RouteListScreen;
