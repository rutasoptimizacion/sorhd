import React from 'react';
import {View, TouchableOpacity, StyleSheet, ViewProps} from 'react-native';
import {elderlyTheme} from '../theme/elderlyTheme';

interface BigCardProps extends ViewProps {
  children: React.ReactNode;
  onPress?: () => void;
  elevation?: 'small' | 'medium' | 'large';
}

export const BigCard: React.FC<BigCardProps> = ({
  children,
  onPress,
  elevation = 'medium',
  style,
  ...props
}) => {
  const shadowStyle = elderlyTheme.shadow[elevation];

  if (onPress) {
    return (
      <TouchableOpacity
        style={[styles.card, shadowStyle, style]}
        onPress={onPress}
        activeOpacity={0.8}
        accessibilityRole="button"
        {...props}>
        {children}
      </TouchableOpacity>
    );
  }

  return (
    <View style={[styles.card, shadowStyle, style]} {...props}>
      {children}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: elderlyTheme.colors.surface,
    borderRadius: elderlyTheme.borderRadius.medium,
    padding: elderlyTheme.spacing.md,
    borderWidth: 1,
    borderColor: elderlyTheme.colors.border,
  },
});
