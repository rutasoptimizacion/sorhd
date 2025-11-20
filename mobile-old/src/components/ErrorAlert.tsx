/**
 * ErrorAlert - Alerta de error clara y grande para adultos mayores
 *
 * Características:
 * - Icono de error grande 48dp
 * - Mensaje claro fuente 22pt
 * - Botón "Reintentar" si onRetry existe
 * - Botón "Cerrar" si onDismiss existe
 */

import React from 'react';
import {View, StyleSheet} from 'react-native';
import {elderlyTheme} from '../theme/elderlyTheme';
import {BigText} from './BigText';
import {BigButton} from './BigButton';
import {BigCard} from './BigCard';

interface ErrorAlertProps {
  message: string;
  onDismiss?: () => void;
  onRetry?: () => void;
  title?: string;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({
  message,
  onDismiss,
  onRetry,
  title = 'Error',
}) => {
  return (
    <View style={styles.container}>
      <BigCard elevation="medium">
        <View style={styles.content}>
          {/* Icono de error */}
          <BigText variant="xxl" style={styles.icon}>
            ⚠️
          </BigText>

          {/* Título */}
          <BigText
            variant="xl"
            color={elderlyTheme.colors.error}
            weight="bold"
            textAlign="center"
            style={styles.title}>
            {title}
          </BigText>

          {/* Mensaje */}
          <BigText
            variant="md"
            color={elderlyTheme.colors.text}
            textAlign="center"
            style={styles.message}>
            {message}
          </BigText>

          {/* Botones */}
          <View style={styles.buttons}>
            {onRetry && (
              <BigButton
                title="Reintentar"
                onPress={onRetry}
                variant="primary"
                style={styles.button}
                accessibilityHint="Toca para reintentar la acción"
              />
            )}
            {onDismiss && (
              <BigButton
                title="Cerrar"
                onPress={onDismiss}
                variant="secondary"
                style={styles.button}
                accessibilityHint="Toca para cerrar este mensaje"
              />
            )}
          </View>
        </View>
      </BigCard>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: elderlyTheme.spacing.lg,
  },
  content: {
    alignItems: 'center',
  },
  icon: {
    fontSize: elderlyTheme.icon.large,
    marginBottom: elderlyTheme.spacing.md,
  },
  title: {
    marginBottom: elderlyTheme.spacing.sm,
  },
  message: {
    marginBottom: elderlyTheme.spacing.lg,
  },
  buttons: {
    width: '100%',
    gap: elderlyTheme.spacing.sm,
  },
  button: {
    marginBottom: elderlyTheme.spacing.sm,
  },
});
