/**
 * Tipos de navegación
 */

export type AuthStackParamList = {
  Login: undefined;
  Activation: undefined;
};

export type ClinicalStackParamList = {
  RouteList: undefined;
  // Fase 3: VisitDetail, MapNavigation, etc.
};

export type PatientStackParamList = {
  VisitStatus: undefined;
  // Fase 3: TrackingMap, TeamInfo, etc.
};

export type RootStackParamList = {
  Auth: undefined;
  Main: undefined;
};
