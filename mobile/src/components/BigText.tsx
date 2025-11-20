import React from 'react';
import {Text, StyleSheet, TextProps} from 'react-native';
import {elderlyTheme} from '../theme/elderlyTheme';

interface BigTextProps extends TextProps {
  variant?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'xxl' | 'xxxl';
  weight?: 'regular' | 'medium' | 'semibold' | 'bold';
  color?: string;
  children: React.ReactNode;
}

export const BigText: React.FC<BigTextProps> = ({
  variant = 'md',
  weight = 'regular',
  color = elderlyTheme.colors.text,
  children,
  style,
  accessibilityLabel,
  ...props
}) => {
  const fontSize = elderlyTheme.fontSize[variant];
  const fontWeight = elderlyTheme.fontWeight[weight];

  return (
    <Text
      style={[
        styles.text,
        {
          fontSize,
          fontWeight,
          color,
        },
        style,
      ]}
      accessibilityLabel={accessibilityLabel || (typeof children === 'string' ? children : undefined)}
      accessibilityRole="text"
      {...props}>
      {children}
    </Text>
  );
};

const styles = StyleSheet.create({
  text: {
    includeFontPadding: false, // Android: reduce padding extra
  },
});
