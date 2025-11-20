import React from 'react';
import {View, StyleSheet, ScrollView, RefreshControl, Alert} from 'react-native';
import {useQuery} from '@tanstack/react-query';
import {format} from 'date-fns';
import {es} from 'date-fns/locale';
import {useNavigation} from '@react-navigation/native';
import {StackNavigationProp} from '@react-navigation/stack';
import {useAuth} from '../../contexts/AuthContext';
import {patientService} from '../../api/services';
import {
  BigText,
  BigButton,
  BigCard,
  StatusBadge,
  LoadingSpinner,
  ErrorAlert,
} from '../../components';
import {elderlyTheme} from '../../theme/elderlyTheme';
import {RootStackParamList, VisitStatus} from '../../types';

type VisitStatusNavigationProp = StackNavigationProp<RootStackParamList, 'VisitStatus'>;

const VisitStatusScreen: React.FC = () => {
  const navigation = useNavigation<VisitStatusNavigationProp>();
  const {logout, user} = useAuth();

  const {
    data,
    isLoading,
    error,
    refetch,
    isRefetching,
  } = useQuery({
    queryKey: ['my-visit'],
    queryFn: () => patientService.getMyVisit(),
    refetchInterval: 30000, // Refetch cada 30 segundos
    staleTime: 10000,
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
    return <LoadingSpinner size="large" message="Cargando..." />;
  }

  if (error) {
    return (
      <View style={styles.container}>
        <ErrorAlert
          message="Error al cargar información de la visita"
          onRetry={refetch}
        />
      </View>
    );
  }

  // Manejar nuevo formato de respuesta del backend
  const visit = data?.visit || null;
  const route = data?.route || null;
  const eta_minutes = data?.eta_minutes;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} />}>
      <View style={styles.header}>
        <BigText variant="xl" weight="bold">
          MI PRÓXIMA VISITA
        </BigText>
        <BigText variant="sm" color={elderlyTheme.colors.textSecondary} style={styles.username}>
          👤 {user?.username}
        </BigText>
      </View>

      {!visit ? (
        <BigCard>
          <BigText variant="lg" weight="medium" style={styles.centered}>
            📅 No tiene visitas programadas
          </BigText>
        </BigCard>
      ) : (
        <>
          <View style={styles.statusCard}>
            {renderStatusContent(visit.status, eta_minutes)}
          </View>

          <BigText variant="lg" weight="bold" style={styles.sectionTitle}>
            🏥 TIPO DE ATENCIÓN
          </BigText>
          <BigCard>
            <BigText variant="md" weight="semibold">
              {visit.case.care_type.name}
            </BigText>
            <BigText variant="sm" color={elderlyTheme.colors.textSecondary}>
              {visit.case.care_type.duration_minutes} minutos
            </BigText>
          </BigCard>

          {visit.case.scheduled_date && (
            <>
              <BigText variant="lg" weight="bold" style={styles.sectionTitle}>
                📅 FECHA Y HORA
              </BigText>
              <BigCard>
                <BigText variant="md" weight="medium">
                  {format(new Date(visit.case.scheduled_date), "EEEE d 'de' MMMM", {
                    locale: es,
                  })}
                </BigText>
                {visit.case.time_window_start && (
                  <BigText variant="sm" color={elderlyTheme.colors.textSecondary}>
                    {visit.case.time_window_start} - {visit.case.time_window_end}
                  </BigText>
                )}
              </BigCard>
            </>
          )}

          {route && (
            <>
              <BigText variant="lg" weight="bold" style={styles.sectionTitle}>
                👥 EQUIPO ASIGNADO
              </BigText>
              <BigCard>
                <BigText variant="md" weight="medium">
                  {route.personnel.map(p => p.name).join(', ')}
                </BigText>
                <BigText variant="sm" color={elderlyTheme.colors.textSecondary}>
                  🚗 {route.vehicle.identifier}
                </BigText>
              </BigCard>

              {(visit.status === 'en_route' || visit.status === 'arrived') && (
                <BigButton
                  title="VER EQUIPO"
                  variant="primary"
                  onPress={() =>
                    navigation.navigate('TeamInfo', {visitId: visit.id})
                  }
                  fullWidth
                  style={styles.button}
                />
              )}
            </>
          )}
        </>
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

function renderStatusContent(status: VisitStatus, eta_minutes?: number) {
  const statusConfig = {
    pending: {
      icon: '⏰',
      title: 'PROGRAMADA',
      message: 'Su visita está programada',
      color: elderlyTheme.colors.visitStatus.pending,
    },
    en_route: {
      icon: '🚗',
      title: 'EL EQUIPO VA EN CAMINO',
      message: eta_minutes ? `${eta_minutes} MINUTOS` : 'Próximamente',
      color: elderlyTheme.colors.visitStatus.enRoute,
    },
    arrived: {
      icon: '🏠',
      title: 'EL EQUIPO HA LLEGADO',
      message: 'Por favor prepárese para recibir al equipo médico',
      color: elderlyTheme.colors.visitStatus.arrived,
    },
    in_progress: {
      icon: '🏥',
      title: 'ATENCIÓN EN PROGRESO',
      message: 'El equipo está con usted',
      color: elderlyTheme.colors.visitStatus.inProgress,
    },
    completed: {
      icon: '✅',
      title: 'VISITA COMPLETADA',
      message: 'Gracias por su tiempo',
      color: elderlyTheme.colors.visitStatus.completed,
    },
    cancelled: {
      icon: '❌',
      title: 'VISITA CANCELADA',
      message: 'La visita ha sido cancelada',
      color: elderlyTheme.colors.visitStatus.cancelled,
    },
  };

  const config = statusConfig[status];

  return (
    <>
      <BigText variant="xxxl" style={styles.statusIcon}>
        {config.icon}
      </BigText>
      <BigText
        variant="xl"
        weight="bold"
        color={config.color}
        style={styles.statusTitle}>
        {config.title}
      </BigText>
      {status === 'en_route' && eta_minutes ? (
        <BigText variant="xxxl" weight="bold" style={styles.eta}>
          ⏱️ {eta_minutes}′
        </BigText>
      ) : (
        <BigText
          variant="md"
          color={elderlyTheme.colors.textSecondary}
          style={styles.statusMessage}>
          {config.message}
        </BigText>
      )}
    </>
  );
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
  centered: {
    textAlign: 'center',
  },
  statusCard: {
    backgroundColor: elderlyTheme.colors.surface,
    borderRadius: elderlyTheme.borderRadius.large,
    padding: elderlyTheme.spacing.xl,
    alignItems: 'center',
    marginBottom: elderlyTheme.spacing.lg,
    ...elderlyTheme.shadow.large,
  },
  statusIcon: {
    marginBottom: elderlyTheme.spacing.sm,
  },
  statusTitle: {
    textAlign: 'center',
    marginBottom: elderlyTheme.spacing.sm,
  },
  statusMessage: {
    textAlign: 'center',
  },
  eta: {
    marginTop: elderlyTheme.spacing.md,
    color: elderlyTheme.colors.primary,
  },
  sectionTitle: {
    marginTop: elderlyTheme.spacing.lg,
    marginBottom: elderlyTheme.spacing.sm,
  },
  button: {
    marginTop: elderlyTheme.spacing.md,
  },
  logoutButton: {
    marginTop: elderlyTheme.spacing.xl,
  },
});

export default VisitStatusScreen;
