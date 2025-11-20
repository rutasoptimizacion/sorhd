import React from 'react';
import {View, ActivityIndicator, StyleSheet} from 'react-native';
import {BigText} from './BigText';
import {elderlyTheme} from '../theme/elderlyTheme';

interface LoadingSpinnerProps {
  size?: 'medium' | 'large';
  message?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'large',
  message,
}) => {
  const spinnerSize = size === 'large' ? elderlyTheme.icon.large : elderlyTheme.icon.medium;

  return (
    <View style={styles.container} accessibilityRole="progressbar" accessibilityLabel={message || 'Cargando'}>
      <ActivityIndicator
        size={spinnerSize}
        color={elderlyTheme.colors.primary}
      />
      {message && (
        <BigText
          variant="md"
          color={elderlyTheme.colors.textSecondary}
          style={styles.message}>
          {message}
        </BigText>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: elderlyTheme.spacing.lg,
    backgroundColor: elderlyTheme.colors.background,
  },
  message: {
    marginTop: elderlyTheme.spacing.md,
    textAlign: 'center',
  },
});
