/**
 * LoadingSpinner - Spinner grande y visible para adultos mayores
 *
 * Características:
 * - Spinner grande 64dp
 * - Mensaje opcional en fuente 22pt
 * - Alta visibilidad
 */

import React from 'react';
import {View, ActivityIndicator, StyleSheet} from 'react-native';
import {elderlyTheme} from '../theme/elderlyTheme';
import {BigText} from './BigText';

interface LoadingSpinnerProps {
  size?: 'medium' | 'large';
  message?: string;
  color?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'large',
  message,
  color = elderlyTheme.colors.primary,
}) => {
  const spinnerSize = size === 'large' ? 64 : 48;

  return (
    <View style={styles.container} accessible={true} accessibilityLabel={message || 'Cargando'}>
      <ActivityIndicator size={spinnerSize as any} color={color} />
      {message && (
        <BigText variant="md" color={elderlyTheme.colors.textSecondary} style={styles.message}>
          {message}
        </BigText>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: elderlyTheme.spacing.xl,
  },
  message: {
    marginTop: elderlyTheme.spacing.md,
    textAlign: 'center',
  },
});
