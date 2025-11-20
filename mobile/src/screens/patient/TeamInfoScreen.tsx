import React from 'react';
import {View, StyleSheet, ScrollView} from 'react-native';
import {useQuery} from '@tanstack/react-query';
import {RouteProp, useRoute} from '@react-navigation/native';
import {patientService} from '../../api/services';
import {BigText, BigCard, LoadingSpinner, ErrorAlert} from '../../components';
import {elderlyTheme} from '../../theme/elderlyTheme';
import {RootStackParamList} from '../../types';

type TeamInfoRouteProp = RouteProp<RootStackParamList, 'TeamInfo'>;

const TeamInfoScreen: React.FC = () => {
  const route = useRoute<TeamInfoRouteProp>();
  const {visitId} = route.params;

  const {data, isLoading, error} = useQuery({
    queryKey: ['visit-team', visitId],
    queryFn: () => patientService.getVisitTeam(visitId),
    staleTime: 60000, // 1 minuto
  });

  if (isLoading) {
    return <LoadingSpinner size="large" message="Cargando información..." />;
  }

  if (error || !data) {
    return (
      <View style={styles.container}>
        <ErrorAlert message="Error al cargar información del equipo" />
      </View>
    );
  }

  const {vehicle, personnel} = data;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <BigText variant="xl" weight="bold" style={styles.title}>
        👥 EQUIPO MÉDICO
      </BigText>

      <BigText variant="lg" weight="bold" style={styles.sectionTitle}>
        🚗 VEHÍCULO
      </BigText>
      <BigCard>
        <BigText variant="md" weight="semibold">
          {vehicle.identifier}
        </BigText>
        {vehicle.base_location_address && (
          <BigText variant="sm" color={elderlyTheme.colors.textSecondary}>
            Base: {vehicle.base_location_address}
          </BigText>
        )}
      </BigCard>

      <BigText variant="lg" weight="bold" style={styles.sectionTitle}>
        👨‍⚕️ PERSONAL
      </BigText>
      {personnel.map((person, index) => (
        <BigCard key={person.id} style={styles.personnelCard}>
          <BigText variant="md" weight="semibold">
            {person.name}
          </BigText>
          {person.skills && person.skills.length > 0 && (
            <View style={styles.skillsContainer}>
              {person.skills.map(skill => (
                <View key={skill.id} style={styles.skillBadge}>
                  <BigText
                    variant="xs"
                    color={elderlyTheme.colors.primary}
                    weight="medium">
                    {skill.name}
                  </BigText>
                </View>
              ))}
            </View>
          )}
        </BigCard>
      ))}

      <BigCard style={styles.infoCard}>
        <BigText variant="md" style={styles.infoText}>
          ℹ️ El equipo médico llegará según lo programado. Por favor esté atento
          a las actualizaciones de estado.
        </BigText>
      </BigCard>
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
  title: {
    textAlign: 'center',
    marginBottom: elderlyTheme.spacing.lg,
  },
  sectionTitle: {
    marginTop: elderlyTheme.spacing.lg,
    marginBottom: elderlyTheme.spacing.sm,
  },
  personnelCard: {
    marginBottom: elderlyTheme.spacing.md,
  },
  skillsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: elderlyTheme.spacing.sm,
  },
  skillBadge: {
    backgroundColor: elderlyTheme.colors.primaryLight,
    paddingHorizontal: elderlyTheme.spacing.sm,
    paddingVertical: elderlyTheme.spacing.xs,
    borderRadius: elderlyTheme.borderRadius.small,
    marginRight: elderlyTheme.spacing.xs,
    marginBottom: elderlyTheme.spacing.xs,
  },
  infoCard: {
    marginTop: elderlyTheme.spacing.xl,
    backgroundColor: elderlyTheme.colors.infoLight,
  },
  infoText: {
    textAlign: 'center',
    color: elderlyTheme.colors.background,
  },
});

export default TeamInfoScreen;
