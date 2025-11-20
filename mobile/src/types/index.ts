/**
 * TypeScript Types para SOR-HD Mobile App
 */

// ========== USER & AUTH ==========

export type UserRole = 'admin' | 'clinical_team' | 'patient';

export interface User {
  id: number;
  username: string;
  email?: string;
  full_name?: string;
  role: UserRole;
  is_active: boolean;
  first_login?: number; // 1 = needs activation, 0 = activated (opcional para compatibilidad)
  phone_number?: string;
  device_token?: string;
  created_at: string;
  updated_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  user: User;
  tokens: AuthTokens;
}

export interface ActivateAccountRequest {
  new_password: string;
}

export interface ActivateAccountResponse {
  user: User;
  tokens: AuthTokens;
}

// ========== PERSONNEL ==========

export interface Skill {
  id: number;
  name: string;
  description?: string;
}

export interface Personnel {
  id: number;
  user_id: number;
  name: string;
  skills: Skill[];
  start_location_lat: number;
  start_location_lng: number;
  start_location_address?: string;
  start_time?: string; // HH:MM
  end_time?: string; // HH:MM
  is_available: boolean;
  created_at: string;
  updated_at: string;
}

// ========== VEHICLE ==========

export interface Vehicle {
  id: number;
  identifier: string; // e.g., "Ambulancia 3"
  capacity: number;
  base_location_lat: number;
  base_location_lng: number;
  base_location_address?: string;
  is_available: boolean;
  resources?: string; // JSON string
  created_at: string;
  updated_at: string;
}

// ========== PATIENT ==========

export interface Patient {
  id: number;
  user_id?: number;
  name: string;
  address: string;
  location_lat: number;
  location_lng: number;
  phone_number?: string;
  emergency_contact?: string;
  emergency_phone?: string;
  medical_notes?: string;
  created_at: string;
  updated_at: string;
}

// ========== CARE TYPE ==========

export interface CareType {
  id: number;
  name: string; // e.g., "Fisioterapia"
  description?: string;
  duration_minutes: number;
  required_skills: Skill[];
}

// ========== CASE ==========

export type CasePriority = 'low' | 'normal' | 'high' | 'urgent';
export type CaseStatus = 'pending' | 'assigned' | 'in_progress' | 'completed' | 'cancelled';

export interface Case {
  id: number;
  patient_id: number;
  patient: Patient;
  care_type_id: number;
  care_type: CareType;
  priority: CasePriority;
  status: CaseStatus;
  scheduled_date?: string; // YYYY-MM-DD
  time_window_start?: string; // HH:MM
  time_window_end?: string; // HH:MM
  special_notes?: string;
  created_at: string;
  updated_at: string;
}

// ========== VISIT ==========

export type VisitStatus = 'pending' | 'en_route' | 'arrived' | 'in_progress' | 'completed' | 'cancelled';

export interface Visit {
  id: number;
  route_id: number;
  case_id: number;
  case: Case;
  sequence_number: number;
  status: VisitStatus;
  estimated_arrival_time?: string; // ISO datetime
  actual_arrival_time?: string;
  actual_start_time?: string;
  actual_end_time?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

// ========== ROUTE ==========

export type RouteStatus = 'planned' | 'active' | 'completed' | 'cancelled';

export interface Route {
  id: number;
  vehicle_id: number;
  vehicle: Vehicle;
  route_date: string; // YYYY-MM-DD
  status: RouteStatus;
  total_distance_km?: number;
  total_duration_minutes?: number;
  start_time?: string; // HH:MM
  end_time?: string; // HH:MM
  visits: Visit[];
  personnel: Personnel[];
  created_at: string;
  updated_at: string;
}

// ========== API RESPONSES ==========

export interface ApiError {
  detail: string;
  status_code?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

// Personnel endpoints
export interface GetMyRoutesParams {
  date?: string; // YYYY-MM-DD
  status?: RouteStatus;
}

export interface UpdateVisitStatusRequest {
  status: VisitStatus;
  notes?: string;
}

// Patient endpoints
export interface MyVisitResponse {
  visit: Visit | null;
  route: {
    id: number;
    vehicle: Vehicle;
    personnel: Personnel[];
  } | null;
  eta_minutes?: number; // Estimated Time of Arrival in minutes
}

export interface VisitTeamResponse {
  vehicle: Vehicle;
  personnel: Personnel[];
}

// ========== NAVIGATION TYPES ==========

export type RootStackParamList = {
  // Auth Stack
  Login: undefined;
  Activation: undefined;

  // Clinical Stack
  RouteList: undefined;
  VisitDetail: {visitId: number; routeId: number};

  // Patient Stack
  VisitStatus: undefined;
  TeamInfo: {visitId: number};
};
