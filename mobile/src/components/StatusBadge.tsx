import React from 'react';
import {View, StyleSheet} from 'react-native';
import {BigText} from './BigText';
import {elderlyTheme, visitStatusLabels} from '../theme/elderlyTheme';

type VisitStatus =
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

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'medium',
}) => {
  const icon = getStatusIcon(status);
  const label = visitStatusLabels[status] || status.toUpperCase();
  const color = elderlyTheme.colors.visitStatus[status] || elderlyTheme.colors.textSecondary;
  const backgroundColor = elderlyTheme.colors.visitStatusBackground[status] || elderlyTheme.colors.surface;

  return (
    <View style={[styles.badge, {backgroundColor}]} accessibilityRole="text" accessibilityLabel={`Estado: ${label}`}>
      <BigText
        variant={size === 'large' ? 'xl' : 'lg'}
        style={styles.icon}>
        {icon}
      </BigText>
      <BigText
        variant={size === 'large' ? 'lg' : 'md'}
        weight="semibold"
        color={color}>
        {label}
      </BigText>
    </View>
  );
};

function getStatusIcon(status: VisitStatus): string {
  const icons: Record<VisitStatus, string> = {
    pending: '⏰',
    en_route: '🚗',
    arrived: '🏠',
    in_progress: '🏥',
    completed: '✅',
    cancelled: '❌',
  };
  return icons[status] || '📋';
}

const styles = StyleSheet.create({
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: elderlyTheme.spacing.md,
    paddingVertical: elderlyTheme.spacing.sm,
    borderRadius: elderlyTheme.borderRadius.medium,
    alignSelf: 'flex-start',
  },
  icon: {
    marginRight: elderlyTheme.spacing.sm,
  },
});
