// User roles
export enum UserRole {
  ADMIN = 'admin',
  CLINICAL_TEAM = 'clinical_team',
  PATIENT = 'patient',
}

// User types
export interface User {
  id: number
  username: string
  full_name: string
  role: UserRole
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface UserCreate {
  username: string
  password: string
  full_name: string
  role: UserRole
  is_active: boolean
}

export interface UserUpdate {
  username?: string
  password?: string
  full_name?: string
  role?: UserRole
  is_active?: boolean
}

// Authentication types
export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

// API Error Response
export interface ApiError {
  detail: string
  status_code?: number
}

// Pagination
export interface PaginationParams {
  skip?: number
  limit?: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}

// Location
export interface Location {
  latitude: number
  longitude: number
}

// Skill
export interface Skill {
  id: number
  name: string
  description?: string
  created_at: string
  updated_at: string
}

export interface SkillCreate {
  name: string
  description?: string
}

export interface SkillUpdate {
  name?: string
  description?: string
}

// Care Type
export interface CareType {
  id: number
  name: string
  description?: string
  estimated_duration: number
  required_skill_ids: number[]
  created_at: string
  updated_at: string
}

export interface CareTypeCreate {
  name: string
  description?: string
  estimated_duration: number
  required_skill_ids: number[]
}

export interface CareTypeUpdate {
  name?: string
  description?: string
  estimated_duration?: number
  required_skill_ids?: number[]
}

// Personnel
export interface Personnel {
  id: number
  user_id?: number  // Optional link to User account for mobile app access
  name: string
  phone?: string
  email?: string
  is_active: boolean
  start_location?: Location
  work_hours_start: string  // HH:MM format
  work_hours_end: string    // HH:MM format
  skill_ids: number[]
  created_at: string
  updated_at: string
}

export interface PersonnelCreate {
  user_id?: number  // Optional link to User account
  name: string
  phone?: string
  email?: string
  is_active: boolean
  start_location?: Location
  work_hours_start: string
  work_hours_end: string
  skill_ids: number[]
}

export interface PersonnelUpdate {
  user_id?: number  // Optional link to User account
  name?: string
  phone?: string
  email?: string
  is_active?: boolean
  start_location?: Location
  work_hours_start?: string
  work_hours_end?: string
  skill_ids?: number[]
}

// Vehicle
export enum VehicleStatus {
  AVAILABLE = 'available',
  IN_USE = 'in_use',
  MAINTENANCE = 'maintenance',
  UNAVAILABLE = 'unavailable',
}

export interface Vehicle {
  id: number
  identifier: string
  capacity: number
  is_active: boolean
  base_location: Location
  status: VehicleStatus
  resources: string[]
  created_at: string
  updated_at: string
}

export interface VehicleCreate {
  identifier: string
  capacity: number
  is_active: boolean
  base_location: Location
  status: VehicleStatus
  resources?: string[]
}

export interface VehicleUpdate {
  identifier?: string
  capacity?: number
  is_active?: boolean
  base_location?: Location
  status?: VehicleStatus
  resources?: string[]
}

// Patient
export interface Patient {
  id: number
  user_id?: number  // Optional link to User account for mobile app access
  name: string
  rut?: string  // Chilean RUT (Rol Único Tributario)
  phone?: string
  email?: string
  date_of_birth?: string  // ISO date string
  medical_notes?: string
  address?: string  // Full address string
  location: Location
  created_at: string
  updated_at: string
}

export interface PatientCreate {
  user_id?: number  // Optional link to User account
  name: string
  rut?: string  // Chilean RUT (optional but validated if provided)
  phone?: string
  email?: string
  date_of_birth?: string
  medical_notes?: string
  address?: string  // Address for geocoding (alternative to location)
  location?: Location  // Optional - can use address instead
}

export interface PatientUpdate {
  user_id?: number  // Optional link to User account
  name?: string
  rut?: string  // Chilean RUT (optional but validated if provided)
  phone?: string
  email?: string
  date_of_birth?: string
  medical_notes?: string
  address?: string  // Address for geocoding (alternative to location)
  location?: Location
}

// Case
export enum CaseStatus {
  PENDING = 'pending',
  ASSIGNED = 'assigned',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
}

export enum CasePriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  URGENT = 'urgent',
}

export interface Case {
  id: number
  patient_id: number
  care_type_id: number
  scheduled_date: string  // ISO date string
  priority: CasePriority
  notes?: string
  location: Location
  time_window_start?: string  // HH:MM format
  time_window_end?: string    // HH:MM format
  status: CaseStatus
  created_at: string
  updated_at: string
}

export interface CaseCreate {
  patient_id: number
  care_type_id: number
  scheduled_date: string
  priority: CasePriority
  notes?: string
  location?: Location
  time_window_start?: string
  time_window_end?: string
}

export interface CaseUpdate {
  patient_id?: number
  care_type_id?: number
  scheduled_date?: string
  priority?: CasePriority
  notes?: string
  location?: Location
  time_window_start?: string
  time_window_end?: string
  status?: CaseStatus
}

// Route
export enum RouteStatus {
  DRAFT = 'draft',
  ACTIVE = 'active',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
}

export interface Route {
  id: number
  vehicle_id: number
  route_date: string  // ISO date string
  status: RouteStatus
  total_distance_km?: number
  total_duration_minutes?: number
  optimization_metadata?: string  // JSON string
  visit_count: number
  created_at: string
  updated_at: string
}

export interface RouteCreate {
  vehicle_id: number
  route_date: string
  status?: RouteStatus
  personnel_ids?: number[]
}

export interface RouteUpdate {
  status?: RouteStatus
}

export interface RouteListParams {
  date?: string
  status?: RouteStatus
  vehicle_id?: number
  page?: number
  page_size?: number
}

export interface RouteListResponse {
  items: Route[]
  total: number
  page: number
  page_size: number
  pages: number
}

// Visit
export enum VisitStatus {
  PENDING = 'pending',
  EN_ROUTE = 'en_route',
  ARRIVED = 'arrived',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
  FAILED = 'failed',
}

export interface Visit {
  id: number
  route_id: number
  case_id: number
  sequence_number: number
  estimated_arrival_time?: string  // ISO datetime
  estimated_departure_time?: string  // ISO datetime
  actual_arrival_time?: string  // ISO datetime
  actual_departure_time?: string  // ISO datetime
  status: VisitStatus
  notes?: string
  created_at: string
  updated_at: string
}

export interface VisitCreate {
  route_id: number
  case_id: number
  sequence_number: number
  estimated_arrival_time?: string
  estimated_departure_time?: string
  status?: VisitStatus
}

export interface VisitUpdate {
  status?: VisitStatus
  actual_arrival_time?: string
  actual_departure_time?: string
  notes?: string
}

// Optimization
export enum ConstraintType {
  SKILL_MISMATCH = 'skill_mismatch',
  CAPACITY_EXCEEDED = 'capacity_exceeded',
  TIME_WINDOW_VIOLATION = 'time_window_violation',
  WORKING_HOURS_VIOLATION = 'working_hours_violation',
  INFEASIBLE = 'infeasible',
}

export interface ConstraintViolation {
  type: ConstraintType
  description: string
  entity_id?: number
  entity_type?: string  // "case", "vehicle", "personnel", "route"
  severity: string  // "error" or "warning"
  details: Record<string, any>
}

export interface OptimizationRequest {
  case_ids: number[]
  vehicle_ids: number[]
  date: string  // ISO date format (YYYY-MM-DD)
  use_heuristic?: boolean
  max_optimization_time?: number  // seconds (10-300, default: 60)
}

export interface UnassignedCaseDetail {
  case_id: number
  case_name: string
  required_skills: string[]
  missing_skills: string[]
  priority: number
}

export interface SkillGapAnalysis {
  unassigned_cases_by_skill: Record<string, number[]>
  unassigned_case_details: UnassignedCaseDetail[]
  most_demanded_skills: Array<{ skill: string; demand_count: number }>
  skill_coverage_percentage: Record<string, number>
  hiring_impact_simulation: Record<string, number>
  summary: {
    total_cases_requested: number
    total_cases_assigned: number
    total_cases_unassigned: number
    assignment_rate_percentage: number
  }
}

export interface OptimizationResponse {
  success: boolean
  message: string
  route_ids: number[]
  unassigned_case_ids: number[]
  constraint_violations: ConstraintViolation[]
  optimization_time_seconds: number
  strategy_used: string  // "ortools" or "heuristic"
  total_distance_km: number
  total_time_minutes: number
  skill_gap_analysis?: SkillGapAnalysis
}

// Extended types for route planning UI
export interface RouteWithDetails extends Route {
  vehicle?: Vehicle
  visits?: VisitWithDetails[]
  personnel?: Personnel[]
}

export interface VisitWithDetails extends Visit {
  case?: Case
  patient?: Patient
  care_type?: CareType
}

export interface CaseWithDetails extends Case {
  patient?: Patient
  care_type?: CareType
}
