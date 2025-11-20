/**
 * BigText - Componente de texto con tamaños grandes para adultos mayores
 *
 * Usa los tamaños definidos en elderlyTheme para garantizar legibilidad
 */

import React from 'react';
import {Text, TextStyle, StyleSheet} from 'react-native';
import {elderlyTheme} from '../theme/elderlyTheme';

interface BigTextProps {
  variant?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'xxl';
  children: React.ReactNode;
  color?: string;
  weight?: 'regular' | 'medium' | 'semibold' | 'bold';
  style?: TextStyle;
  accessibilityLabel?: string;
  numberOfLines?: number;
  textAlign?: 'left' | 'center' | 'right';
}

export const BigText: React.FC<BigTextProps> = ({
  variant = 'md',
  children,
  color = elderlyTheme.colors.text,
  weight = 'regular',
  style,
  accessibilityLabel,
  numberOfLines,
  textAlign = 'left',
}) => {
  const fontSize = elderlyTheme.fontSize[variant];
  const fontWeight = getFontWeight(weight);

  return (
    <Text
      style={[
        styles.text,
        {
          fontSize,
          fontWeight,
          color,
          textAlign,
        },
        style,
      ]}
      accessibilityLabel={accessibilityLabel || (typeof children === 'string' ? children : undefined)}
      accessible={true}
      numberOfLines={numberOfLines}>
      {children}
    </Text>
  );
};

const getFontWeight = (weight: BigTextProps['weight']): TextStyle['fontWeight'] => {
  const weights = {
    regular: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
  };
  return weights[weight || 'regular'] as TextStyle['fontWeight'];
};

const styles = StyleSheet.create({
  text: {
    includeFontPadding: false, // Mejor control de altura en Android
  },
});
