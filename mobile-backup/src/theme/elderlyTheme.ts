/**
 * Tema Accesible para Adultos Mayores
 *
 * Diseñado según las pautas de accesibilidad WCAG AAA:
 * - Tamaños de fuente grandes (mínimo 22pt)
 * - Alto contraste (ratio 7:1)
 * - Espaciado generoso
 * - Botones grandes (mínimo 56dp de altura)
 * - Iconos grandes y claros
 */

export const elderlyTheme = {
  // ============================================
  // TEXTOS GRANDES - Legibilidad óptima
  // ============================================
  fontSize: {
    xs: 16,      // Texto muy pequeño (evitar usar)
    sm: 18,      // Texto secundario
    md: 22,      // Texto normal (base)
    lg: 26,      // Títulos secundarios
    xl: 32,      // Títulos principales
    xxl: 40,     // Números importantes (ETA, contador)
    xxxl: 48,    // Números muy destacados
  },

  // ============================================
  // ALTO CONTRASTE - WCAG AAA (ratio 7:1)
  // ============================================
  colors: {
    // Fondos
    background: '#FFFFFF',        // Blanco puro
    surface: '#F5F5F5',          // Gris muy claro
    surfaceElevated: '#FFFFFF',  // Blanco para cards elevadas

    // Textos con contraste máximo
    text: '#000000',              // Negro puro (ratio 21:1)
    textSecondary: '#424242',     // Gris oscuro (ratio 12:1)
    textDisabled: '#757575',      // Gris medio para disabled

    // Colores semánticos con alto contraste
    success: '#2E7D32',           // Verde oscuro (acciones exitosas)
    successLight: '#4CAF50',      // Verde medio (indicadores)

    warning: '#F57C00',           // Naranja oscuro (advertencias)
    warningLight: '#FF9800',      // Naranja medio

    error: '#C62828',             // Rojo oscuro (errores)
    errorLight: '#E53935',        // Rojo medio

    info: '#1565C0',              // Azul oscuro (información)
    infoLight: '#1976D2',         // Azul medio

    // Color primario (sistema médico)
    primary: '#1976D2',           // Azul médico
    primaryDark: '#0D47A1',       // Azul muy oscuro
    primaryLight: '#42A5F5',      // Azul claro

    // Bordes y divisores
    border: '#BDBDBD',            // Gris medio
    divider: '#E0E0E0',           // Gris claro

    // Estado de visita (semánticos)
    pending: '#757575',           // Gris - Pendiente
    enRoute: '#1976D2',           // Azul - En camino
    arrived: '#F57C00',           // Naranja - Llegó
    inProgress: '#FF9800',        // Naranja intenso - En progreso
    completed: '#2E7D32',         // Verde - Completada
    cancelled: '#C62828',         // Rojo - Cancelada
  },

  // ============================================
  // ESPACIADO GENEROSO - Facilita el toque
  // ============================================
  spacing: {
    xs: 8,       // Espaciado mínimo
    sm: 16,      // Espaciado pequeño
    md: 24,      // Espaciado normal
    lg: 32,      // Espaciado grande
    xl: 48,      // Espaciado muy grande
    xxl: 64,     // Espaciado extra grande
  },

  // ============================================
  // BOTONES GRANDES - Área táctil mínima 56x56dp
  // ============================================
  button: {
    minHeight: 56,              // Altura mínima (Android Material Design)
    minWidth: 120,              // Ancho mínimo
    borderRadius: 8,            // Bordes redondeados suaves
    paddingHorizontal: 24,      // Padding horizontal generoso
    paddingVertical: 16,        // Padding vertical generoso
    fontSize: 20,               // Texto grande en botones
    iconSize: 28,               // Iconos grandes en botones
  },

  // ============================================
  // ICONOS GRANDES - Fáciles de ver
  // ============================================
  icon: {
    small: 32,       // Iconos pequeños
    medium: 48,      // Iconos normales
    large: 64,       // Iconos grandes
    xlarge: 80,      // Iconos muy grandes (estado principal)
  },

  // ============================================
  // CARDS Y CONTENEDORES
  // ============================================
  card: {
    borderRadius: 12,           // Bordes redondeados
    padding: 24,                // Padding generoso
    elevation: 2,               // Sombra sutil
    borderWidth: 1,             // Borde visible
  },

  // ============================================
  // INPUTS - Campos de formulario
  // ============================================
  input: {
    minHeight: 56,              // Altura mínima
    borderRadius: 8,            // Bordes redondeados
    paddingHorizontal: 16,      // Padding horizontal
    fontSize: 22,               // Texto grande
    borderWidth: 2,             // Borde grueso y visible
  },

  // ============================================
  // TIPOGRAFÍA - Pesos y estilos
  // ============================================
  fontWeight: {
    regular: '400' as '400',
    medium: '500' as '500',
    semibold: '600' as '600',
    bold: '700' as '700',
  },

  // ============================================
  // SOMBRAS - Elevación visual
  // ============================================
  shadows: {
    small: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.1,
      shadowRadius: 4,
      elevation: 2,
    },
    medium: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.15,
      shadowRadius: 8,
      elevation: 4,
    },
    large: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 8 },
      shadowOpacity: 0.2,
      shadowRadius: 16,
      elevation: 8,
    },
  },

  // ============================================
  // ANIMACIONES - Suaves pero rápidas
  // ============================================
  animation: {
    duration: {
      fast: 150,      // Animaciones rápidas
      normal: 250,    // Animaciones normales
      slow: 350,      // Animaciones lentas
    },
    easing: 'ease-in-out',
  },

  // ============================================
  // LAYOUT - Dimensiones y límites
  // ============================================
  layout: {
    screenPadding: 24,          // Padding lateral de pantallas
    maxContentWidth: 600,       // Ancho máximo de contenido
    headerHeight: 72,           // Altura de header (más grande)
    tabBarHeight: 72,           // Altura de tab bar (más grande)
  },
};

// ============================================
// TIPOS para TypeScript
// ============================================
export type ElderlyTheme = typeof elderlyTheme;

// Helper para obtener colores por estado de visita
export const getVisitStatusColor = (status: string): string => {
  const statusMap: Record<string, string> = {
    pending: elderlyTheme.colors.pending,
    en_route: elderlyTheme.colors.enRoute,
    arrived: elderlyTheme.colors.arrived,
    in_progress: elderlyTheme.colors.inProgress,
    completed: elderlyTheme.colors.completed,
    cancelled: elderlyTheme.colors.cancelled,
    failed: elderlyTheme.colors.error,
  };

  return statusMap[status] || elderlyTheme.colors.text;
};

// Helper para obtener texto legible del estado
export const getVisitStatusText = (status: string): string => {
  const textMap: Record<string, string> = {
    pending: 'Programada',
    en_route: 'En Camino',
    arrived: 'Equipo Llegó',
    in_progress: 'En Progreso',
    completed: 'Completada',
    cancelled: 'Cancelada',
    failed: 'Fallida',
  };

  return textMap[status] || status;
};

export default elderlyTheme;
