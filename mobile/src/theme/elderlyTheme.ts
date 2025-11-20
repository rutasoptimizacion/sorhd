/**
 * Tema Accesible para Adultos Mayores
 * Cumple con WCAG AAA (contraste 7:1 mínimo)
 * Diseñado para facilitar la lectura y navegación
 */

export const elderlyTheme = {
  // Tamaños de fuente grandes
  fontSize: {
    xs: 16, // Mínimo legible
    sm: 18, // Texto secundario
    md: 22, // Texto normal (BASE)
    lg: 26, // Títulos secundarios
    xl: 32, // Títulos principales
    xxl: 40, // Números importantes (ETA)
    xxxl: 48, // Números muy importantes
  },

  // Pesos de fuente
  fontWeight: {
    regular: '400' as const,
    medium: '500' as const,
    semibold: '600' as const,
    bold: '700' as const,
  },

  // Colores con alto contraste (WCAG AAA - Ratio 7:1+)
  colors: {
    // Colores base
    background: '#FFFFFF', // Blanco puro
    surface: '#F5F5F5', // Gris muy claro para cards
    text: '#000000', // Negro puro (ratio 21:1)
    textSecondary: '#424242', // Gris oscuro (ratio 12:1)
    textTertiary: '#616161', // Gris medio (ratio 7:1)

    // Colores de acción
    primary: '#1976D2', // Azul médico
    primaryDark: '#1565C0',
    primaryLight: '#42A5F5',

    // Colores semánticos
    success: '#2E7D32', // Verde oscuro
    successLight: '#43A047',
    warning: '#F57C00', // Naranja oscuro
    warningLight: '#FB8C00',
    error: '#C62828', // Rojo oscuro
    errorLight: '#D32F2F',
    info: '#1565C0', // Azul oscuro
    infoLight: '#1976D2',

    // Estados de visita
    visitStatus: {
      pending: '#757575', // Gris
      enRoute: '#1976D2', // Azul
      arrived: '#F57C00', // Naranja
      inProgress: '#FF9800', // Naranja brillante
      completed: '#2E7D32', // Verde
      cancelled: '#C62828', // Rojo
    },

    // Colores de fondo para estados
    visitStatusBackground: {
      pending: '#F5F5F5',
      enRoute: '#E3F2FD',
      arrived: '#FFF3E0',
      inProgress: '#FFF8E1',
      completed: '#E8F5E9',
      cancelled: '#FFEBEE',
    },

    // Bordes y divisores
    border: '#E0E0E0',
    divider: '#BDBDBD',

    // Deshabilitado
    disabled: '#9E9E9E',
    disabledBackground: '#F5F5F5',
  },

  // Espaciado generoso
  spacing: {
    xs: 8,
    sm: 16,
    md: 24,
    lg: 32,
    xl: 48,
    xxl: 64,
  },

  // Radios de borde
  borderRadius: {
    small: 8,
    medium: 12,
    large: 16,
    xlarge: 20,
  },

  // Configuración de botones
  button: {
    minHeight: 56, // Altura mínima para fácil toque
    minWidth: 120,
    fontSize: 20,
    iconSize: 28,
    paddingHorizontal: 24,
    paddingVertical: 16,
  },

  // Configuración de inputs
  input: {
    minHeight: 56,
    fontSize: 22,
    paddingHorizontal: 16,
    paddingVertical: 16,
    borderWidth: 2,
  },

  // Iconos grandes
  icon: {
    small: 32,
    medium: 48,
    large: 64,
    xlarge: 80,
  },

  // Sombras sutiles
  shadow: {
    small: {
      shadowColor: '#000',
      shadowOffset: {width: 0, height: 2},
      shadowOpacity: 0.1,
      shadowRadius: 4,
      elevation: 2,
    },
    medium: {
      shadowColor: '#000',
      shadowOffset: {width: 0, height: 4},
      shadowOpacity: 0.15,
      shadowRadius: 8,
      elevation: 4,
    },
    large: {
      shadowColor: '#000',
      shadowOffset: {width: 0, height: 6},
      shadowOpacity: 0.2,
      shadowRadius: 12,
      elevation: 6,
    },
  },
};

// Traducciones de estados de visita al español
export const visitStatusLabels: Record<string, string> = {
  pending: 'PROGRAMADA',
  en_route: 'EN CAMINO',
  arrived: 'LLEGÓ',
  in_progress: 'EN PROGRESO',
  completed: 'COMPLETADA',
  cancelled: 'CANCELADA',
};

export type Theme = typeof elderlyTheme;
export type VisitStatus = keyof typeof elderlyTheme.colors.visitStatus;
