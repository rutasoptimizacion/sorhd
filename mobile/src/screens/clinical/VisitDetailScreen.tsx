import React from 'react';
import {View, StyleSheet, ScrollView, Linking, Platform, Alert} from 'react-native';
import {useQuery, useMutation, useQueryClient} from '@tanstack/react-query';
import {RouteProp, useRoute} from '@react-navigation/native';
import {visitService} from '../../api/services';
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

type VisitDetailRouteProp = RouteProp<RootStackParamList, 'VisitDetail'>;

const VisitDetailScreen: React.FC = () => {
  const route = useRoute<VisitDetailRouteProp>();
  const {visitId} = route.params;
  const queryClient = useQueryClient();

  const {
    data: visit,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['visit', visitId],
    queryFn: () => visitService.getVisitById(visitId),
    staleTime: 10000, // 10 segundos
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({status, notes}: {status: VisitStatus; notes?: string}) =>
      visitService.updateVisitStatus(visitId, {status, notes}),
    onSuccess: () => {
      queryClient.invalidateQueries({queryKey: ['visit', visitId]});
      queryClient.invalidateQueries({queryKey: ['my-routes']});
      Alert.alert('Éxito', 'Estado de visita actualizado correctamente');
    },
    onError: (error: any) => {
      Alert.alert(
        'Error',
        error.response?.data?.detail || 'No se pudo actualizar el estado',
      );
    },
  });

  const handleNavigate = () => {
    if (!visit) return;

    const lat = visit.case.patient.location_lat;
    const lng = visit.case.patient.location_lng;

    const url = Platform.select({
      android: `google.navigation:q=${lat},${lng}`,
      default: `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`,
    });

    Linking.canOpenURL(url!)
      .then(supported => {
        if (supported) {
          return Linking.openURL(url!);
        } else {
          // Fallback a Google Maps web
          return Linking.openURL(
            `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`,
          );
        }
      })
      .catch(err => {
        Alert.alert('Error', 'No se pudo abrir el navegador');
        console.error(err);
      });
  };

  if (isLoading) {
    return <LoadingSpinner size="large" message="Cargando visita..." />;
  }

  if (error || !visit) {
    return (
      <View style={styles.container}>
        <ErrorAlert message="Error al cargar la visita" />
      </View>
    );
  }

  const {case: caseData} = visit;
  const {patient, care_type} = caseData;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <BigText variant="lg" weight="bold" style={styles.sectionTitle}>
        👤 PACIENTE
      </BigText>
      <BigCard>
        <BigText variant="md" weight="semibold">
          {patient.name}
        </BigText>
        <View style={styles.infoRow}>
          <BigText variant="sm">📍</BigText>
          <BigText variant="sm" style={styles.infoText}>
            {patient.address}
          </BigText>
        </View>
        {patient.phone_number && (
          <View style={styles.infoRow}>
            <BigText variant="sm">☎️</BigText>
            <BigText variant="sm" style={styles.infoText}>
              {patient.phone_number}
            </BigText>
          </View>
        )}
      </BigCard>

      <BigText variant="lg" weight="bold" style={styles.sectionTitle}>
        🏥 ATENCIÓN REQUERIDA
      </BigText>
      <BigCard>
        <View style={styles.infoRow}>
          <BigText variant="sm" color={elderlyTheme.colors.textSecondary}>
            Tipo:
          </BigText>
          <BigText variant="sm" weight="medium">
            {care_type.name}
          </BigText>
        </View>
        <View style={styles.infoRow}>
          <BigText variant="sm" color={elderlyTheme.colors.textSecondary}>
            Duración:
          </BigText>
          <BigText variant="sm" weight="medium">
            {care_type.duration_minutes} minutos
          </BigText>
        </View>
        {caseData.time_window_start && (
          <View style={styles.infoRow}>
            <BigText variant="sm" color={elderlyTheme.colors.textSecondary}>
              Hora:
            </BigText>
            <BigText variant="sm" weight="medium">
              {caseData.time_window_start} - {caseData.time_window_end}
            </BigText>
          </View>
        )}
      </BigCard>

      {caseData.special_notes && (
        <>
          <BigText variant="lg" weight="bold" style={styles.sectionTitle}>
            📝 NOTAS
          </BigText>
          <BigCard>
            <BigText variant="sm">{caseData.special_notes}</BigText>
          </BigCard>
        </>
      )}

      <View style={styles.statusContainer}>
        <BigText variant="md" weight="medium" style={styles.statusLabel}>
          ESTADO ACTUAL:
        </BigText>
        <StatusBadge status={visit.status} size="large" />
      </View>

      <View style={styles.actions}>
        {visit.status !== 'completed' && visit.status !== 'cancelled' && (
          <BigButton
            title="🗺️ NAVEGAR A DIRECCIÓN"
            variant="primary"
            onPress={handleNavigate}
            fullWidth
            style={styles.actionButton}
          />
        )}

        {visit.status === 'pending' && (
          <BigButton
            title="▶️ MARCAR EN CAMINO"
            variant="primary"
            onPress={() => updateStatusMutation.mutate({status: 'en_route'})}
            loading={updateStatusMutation.isPending}
            fullWidth
            style={styles.actionButton}
          />
        )}

        {visit.status === 'en_route' && (
          <BigButton
            title="🏠 MARCAR LLEGADA"
            variant="warning"
            onPress={() => updateStatusMutation.mutate({status: 'arrived'})}
            loading={updateStatusMutation.isPending}
            fullWidth
            style={styles.actionButton}
          />
        )}

        {visit.status === 'arrived' && (
          <BigButton
            title="🏥 INICIAR ATENCIÓN"
            variant="warning"
            onPress={() => updateStatusMutation.mutate({status: 'in_progress'})}
            loading={updateStatusMutation.isPending}
            fullWidth
            style={styles.actionButton}
          />
        )}

        {visit.status === 'in_progress' && (
          <BigButton
            title="✅ MARCAR COMPLETADA"
            variant="success"
            onPress={() => updateStatusMutation.mutate({status: 'completed'})}
            loading={updateStatusMutation.isPending}
            fullWidth
            style={styles.actionButton}
          />
        )}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: elderlyTheme.colors.background,
  },
  content: {
    padding: elderlyTheme.spacing.lg,
  },
  sectionTitle: {
    marginTop: elderlyTheme.spacing.md,
    marginBottom: elderlyTheme.spacing.sm,
  },
  infoRow: {
    flexDirection: 'row',
    marginVertical: elderlyTheme.spacing.xs,
    alignItems: 'flex-start',
  },
  infoText: {
    marginLeft: elderlyTheme.spacing.sm,
    flex: 1,
  },
  statusContainer: {
    alignItems: 'center',
    marginVertical: elderlyTheme.spacing.lg,
    padding: elderlyTheme.spacing.md,
    backgroundColor: elderlyTheme.colors.surface,
    borderRadius: elderlyTheme.borderRadius.medium,
  },
  statusLabel: {
    marginBottom: elderlyTheme.spacing.sm,
  },
  actions: {
    marginTop: elderlyTheme.spacing.md,
  },
  actionButton: {
    marginVertical: elderlyTheme.spacing.sm,
  },
});

export default VisitDetailScreen;
