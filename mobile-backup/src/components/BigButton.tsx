/**
 * BigButton - Botón grande y accesible para adultos mayores
 *
 * Características:
 * - Altura mínima 56dp
 * - Fuente 20pt
 * - Icono opcional 28dp
 * - Feedback táctil
 * - Alta visibilidad
 */

import React from 'react';
import {
  TouchableOpacity,
  View,
  ActivityIndicator,
  StyleSheet,
  ViewStyle,
  Platform,
} from 'react-native';
import {elderlyTheme} from '../theme/elderlyTheme';
import {BigText} from './BigText';

interface BigButtonProps {
  title: string;
  onPress: () => void;
  icon?: React.ReactNode;
  variant?: 'primary' | 'success' | 'warning' | 'error' | 'secondary';
  disabled?: boolean;
  loading?: boolean;
  style?: ViewStyle;
  fullWidth?: boolean;
  accessibilityLabel?: string;
  accessibilityHint?: string;
}

export const BigButton: React.FC<BigButtonProps> = ({
  title,
  onPress,
  icon,
  variant = 'primary',
  disabled = false,
  loading = false,
  style,
  fullWidth = true,
  accessibilityLabel,
  accessibilityHint,
}) => {
  const isDisabled = disabled || loading;
  const backgroundColor = getBackgroundColor(variant, isDisabled);
  const textColor = getTextColor(variant);

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={isDisabled}
      activeOpacity={0.7}
      style={[
        styles.button,
        {backgroundColor},
        fullWidth && styles.fullWidth,
        isDisabled && styles.disabled,
        style,
      ]}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel || title}
      accessibilityHint={accessibilityHint}
      accessibilityState={{disabled: isDisabled}}>
      <View style={styles.content}>
        {loading ? (
          <ActivityIndicator size="large" color={textColor} />
        ) : (
          <>
            {icon && <View style={styles.iconContainer}>{icon}</View>}
            <BigText variant="lg" color={textColor} weight="semibold">
              {title}
            </BigText>
          </>
        )}
      </View>
    </TouchableOpacity>
  );
};

const getBackgroundColor = (
  variant: BigButtonProps['variant'],
  disabled: boolean
): string => {
  if (disabled) {
    return elderlyTheme.colors.disabled;
  }

  const colors = {
    primary: elderlyTheme.colors.primary,
    success: elderlyTheme.colors.success,
    warning: elderlyTheme.colors.warning,
    error: elderlyTheme.colors.error,
    secondary: elderlyTheme.colors.textSecondary,
  };

  return colors[variant || 'primary'];
};

const getTextColor = (variant: BigButtonProps['variant']): string => {
  // Todos los botones usan texto blanco para máximo contraste
  return '#FFFFFF';
};

const styles = StyleSheet.create({
  button: {
    minHeight: elderlyTheme.button.minHeight,
    minWidth: elderlyTheme.button.minWidth,
    borderRadius: 12,
    paddingHorizontal: elderlyTheme.spacing.lg,
    paddingVertical: elderlyTheme.spacing.sm,
    justifyContent: 'center',
    alignItems: 'center',
    ...Platform.select({
      android: {
        elevation: 4,
      },
      ios: {
        shadowColor: '#000',
        shadowOffset: {width: 0, height: 2},
        shadowOpacity: 0.25,
        shadowRadius: 4,
      },
    }),
  },
  fullWidth: {
    width: '100%',
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconContainer: {
    marginRight: elderlyTheme.spacing.sm,
  },
  disabled: {
    opacity: 0.5,
  },
});
