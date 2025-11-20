/**
 * StatusBadge - Badge de estado con iconos y colores semánticos
 *
 * Estados de visita:
 * - pending: Pendiente (gris)
 * - en_route: En camino (azul)
 * - arrived: Llegó (naranja)
 * - in_progress: En progreso (naranja)
 * - completed: Completada (verde)
 * - cancelled: Cancelada (rojo)
 */

import React from 'react';
import {View, StyleSheet} from 'react-native';
import {elderlyTheme} from '../theme/elderlyTheme';
import {BigText} from './BigText';

export type VisitStatus =
  | 'pending'
  | 'en_route'
  | 'arrived'
  | 'in_progress'
  | 'completed'
  | 'cancelled';

interface StatusBadgeProps {
  status: VisitStatus;
  size?: 'medium' | 'large';
}

interface StatusConfig {
  label: string;
  icon: string;
  color: string;
  backgroundColor: string;
}

const STATUS_CONFIG: Record<VisitStatus, StatusConfig> = {
  pending: {
    label: 'PROGRAMADA',
    icon: '⏰',
    color: elderlyTheme.colors.textSecondary,
    backgroundColor: '#F5F5F5',
  },
  en_route: {
    label: 'EN CAMINO',
    icon: '🚗',
    color: elderlyTheme.colors.info,
    backgroundColor: '#E3F2FD',
  },
  arrived: {
    label: 'EQUIPO LLEGÓ',
    icon: '🏠',
    color: elderlyTheme.colors.warning,
    backgroundColor: '#FFF3E0',
  },
  in_progress: {
    label: 'EN PROGRESO',
    icon: '🏥',
    color: elderlyTheme.colors.warning,
    backgroundColor: '#FFF3E0',
  },
  completed: {
    label: 'COMPLETADA',
    icon: '✅',
    color: elderlyTheme.colors.success,
    backgroundColor: '#E8F5E9',
  },
  cancelled: {
    label: 'CANCELADA',
    icon: '❌',
    color: elderlyTheme.colors.error,
    backgroundColor: '#FFEBEE',
  },
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'medium',
}) => {
  const config = STATUS_CONFIG[status];
  const iconSize = size === 'large' ? elderlyTheme.icon.large : elderlyTheme.icon.medium;
  const textVariant = size === 'large' ? 'lg' : 'md';

  return (
    <View
      style={[
        styles.container,
        {backgroundColor: config.backgroundColor},
        size === 'large' && styles.containerLarge,
      ]}
      accessible={true}
      accessibilityLabel={`Estado: ${config.label}`}
      accessibilityRole="text">
      <BigText variant="xl" style={{fontSize: iconSize}}>
        {config.icon}
      </BigText>
      <BigText variant={textVariant} color={config.color} weight="semibold" style={styles.label}>
        {config.label}
      </BigText>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: elderlyTheme.spacing.sm,
    paddingHorizontal: elderlyTheme.spacing.md,
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  containerLarge: {
    paddingVertical: elderlyTheme.spacing.md,
    paddingHorizontal: elderlyTheme.spacing.lg,
    borderRadius: 12,
  },
  label: {
    marginLeft: elderlyTheme.spacing.sm,
  },
});
