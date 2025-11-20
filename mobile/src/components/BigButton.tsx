import React from 'react';
import {
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
  ViewStyle,
  TouchableOpacityProps,
} from 'react-native';
import {BigText} from './BigText';
import {elderlyTheme} from '../theme/elderlyTheme';

interface BigButtonProps extends TouchableOpacityProps {
  title: string;
  variant?: 'primary' | 'success' | 'warning' | 'error';
  loading?: boolean;
  icon?: React.ReactNode;
  fullWidth?: boolean;
}

export const BigButton: React.FC<BigButtonProps> = ({
  title,
  variant = 'primary',
  loading = false,
  disabled = false,
  icon,
  fullWidth = false,
  style,
  ...props
}) => {
  const isDisabled = disabled || loading;

  const backgroundColor = isDisabled
    ? elderlyTheme.colors.disabledBackground
    : getBackgroundColor(variant);

  const textColor = isDisabled ? elderlyTheme.colors.disabled : '#FFFFFF';

  return (
    <TouchableOpacity
      style={[
        styles.button,
        {backgroundColor},
        fullWidth && styles.fullWidth,
        style,
      ]}
      disabled={isDisabled}
      activeOpacity={0.7}
      accessibilityRole="button"
      accessibilityLabel={title}
      accessibilityState={{disabled: isDisabled}}
      {...props}>
      {loading ? (
        <ActivityIndicator
          size={elderlyTheme.button.iconSize}
          color={textColor}
        />
      ) : (
        <>
          {icon && <>{icon}</>}
          <BigText
            variant="md"
            weight="semibold"
            color={textColor}
            style={icon && styles.textWithIcon}>
            {title}
          </BigText>
        </>
      )}
    </TouchableOpacity>
  );
};

function getBackgroundColor(variant: string): string {
  switch (variant) {
    case 'success':
      return elderlyTheme.colors.success;
    case 'warning':
      return elderlyTheme.colors.warning;
    case 'error':
      return elderlyTheme.colors.error;
    default:
      return elderlyTheme.colors.primary;
  }
}

const styles = StyleSheet.create({
  button: {
    minHeight: elderlyTheme.button.minHeight,
    minWidth: elderlyTheme.button.minWidth,
    paddingHorizontal: elderlyTheme.button.paddingHorizontal,
    paddingVertical: elderlyTheme.button.paddingVertical,
    borderRadius: elderlyTheme.borderRadius.medium,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    ...elderlyTheme.shadow.small,
  },
  fullWidth: {
    width: '100%',
  },
  textWithIcon: {
    marginLeft: elderlyTheme.spacing.sm,
  },
});
