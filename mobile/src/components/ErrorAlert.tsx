import React from 'react';
import {View, StyleSheet} from 'react-native';
import {BigText} from './BigText';
import {BigButton} from './BigButton';
import {elderlyTheme} from '../theme/elderlyTheme';

interface ErrorAlertProps {
  message: string;
  onDismiss?: () => void;
  onRetry?: () => void;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({
  message,
  onDismiss,
  onRetry,
}) => {
  return (
    <View style={styles.container} accessibilityRole="alert">
      <BigText variant="xl" style={styles.icon}>
        ⚠️
      </BigText>
      <BigText
        variant="md"
        weight="medium"
        color={elderlyTheme.colors.error}
        style={styles.message}>
        {message}
      </BigText>
      <View style={styles.buttons}>
        {onRetry && (
          <BigButton
            title="Reintentar"
            variant="primary"
            onPress={onRetry}
            style={styles.button}
          />
        )}
        {onDismiss && (
          <BigButton
            title="Cerrar"
            variant="error"
            onPress={onDismiss}
            style={styles.button}
          />
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: elderlyTheme.colors.visitStatusBackground.cancelled,
    borderRadius: elderlyTheme.borderRadius.medium,
    borderWidth: 2,
    borderColor: elderlyTheme.colors.error,
    padding: elderlyTheme.spacing.lg,
    alignItems: 'center',
    ...elderlyTheme.shadow.medium,
  },
  icon: {
    marginBottom: elderlyTheme.spacing.sm,
  },
  message: {
    textAlign: 'center',
    marginBottom: elderlyTheme.spacing.md,
  },
  buttons: {
    flexDirection: 'row',
    gap: elderlyTheme.spacing.sm,
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  button: {
    minWidth: 120,
  },
});
