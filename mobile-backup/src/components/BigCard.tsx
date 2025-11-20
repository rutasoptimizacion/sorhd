/**
 * BigCard - Tarjeta con espaciado generoso para adultos mayores
 *
 * Características:
 * - Padding 24dp
 * - Bordes redondeados
 * - Sombra sutil
 * - Área táctil completa si tiene onPress
 */

import React from 'react';
import {View, TouchableOpacity, StyleSheet, ViewStyle, Platform} from 'react-native';
import {elderlyTheme} from '../theme/elderlyTheme';

interface BigCardProps {
  children: React.ReactNode;
  onPress?: () => void;
  elevation?: 'small' | 'medium' | 'large';
  style?: ViewStyle;
  accessibilityLabel?: string;
  accessibilityHint?: string;
}

export const BigCard: React.FC<BigCardProps> = ({
  children,
  onPress,
  elevation = 'medium',
  style,
  accessibilityLabel,
  accessibilityHint,
}) => {
  const elevationStyle = getElevationStyle(elevation);

  const cardContent = (
    <View style={[styles.card, elevationStyle, style]}>
      {children}
    </View>
  );

  if (onPress) {
    return (
      <TouchableOpacity
        onPress={onPress}
        activeOpacity={0.8}
        accessibilityRole="button"
        accessibilityLabel={accessibilityLabel}
        accessibilityHint={accessibilityHint}>
        {cardContent}
      </TouchableOpacity>
    );
  }

  return cardContent;
};

const getElevationStyle = (elevation: BigCardProps['elevation']): ViewStyle => {
  const elevations = {
    small: Platform.select({
      android: {elevation: 2},
      ios: {
        shadowColor: '#000',
        shadowOffset: {width: 0, height: 1},
        shadowOpacity: 0.15,
        shadowRadius: 2,
      },
    }),
    medium: Platform.select({
      android: {elevation: 4},
      ios: {
        shadowColor: '#000',
        shadowOffset: {width: 0, height: 2},
        shadowOpacity: 0.2,
        shadowRadius: 4,
      },
    }),
    large: Platform.select({
      android: {elevation: 8},
      ios: {
        shadowColor: '#000',
        shadowOffset: {width: 0, height: 4},
        shadowOpacity: 0.25,
        shadowRadius: 8,
      },
    }),
  };

  return elevations[elevation || 'medium'] || {};
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: elderlyTheme.colors.background,
    borderRadius: 12,
    padding: elderlyTheme.spacing.md,
    width: '100%',
  },
});
