import { TenantContext } from '@/types/common';

// Authentication types
export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  tenantId: string;
  tenantName: string;
  permissions: Permission[];
  settings: UserSettings;
  lastLoginAt?: string;
  createdAt: string;
  updatedAt: string;
  isActive: boolean;
  emailVerified: boolean;
}

export type UserRole = 'admin' | 'manager' | 'user' | 'viewer';

export interface Permission {
  resource: PermissionResource;
  actions: PermissionAction[];
  conditions?: PermissionCondition[];
}

export type PermissionResource =
  | 'documents'
  | 'classifications'
  | 'gl_accounts'
  | 'billing_routes'
  | 'reports'
  | 'settings'
  | 'users'
  | 'tenant_config';

export type PermissionAction =
  | 'create'
  | 'read'
  | 'update'
  | 'delete'
  | 'classify'
  | 'approve'
  | 'export'
  | 'manage';

export interface PermissionCondition {
  field: string;
  operator: 'equals' | 'in' | 'not_equals';
  value: any;
}

export interface UserSettings {
  language: string;
  timezone: string;
  dateFormat: string;
  notifications: NotificationSettings;
  dashboard: DashboardSettings;
  ui: UISettings;
}

export interface NotificationSettings {
  email: boolean;
  inApp: boolean;
  desktop: boolean;
  documentProcessed: boolean;
  classificationFailed: boolean;
  manualReviewRequired: boolean;
  systemMaintenance: boolean;
}

export interface DashboardSettings {
  defaultView: 'summary' | 'detailed';
  refreshInterval: number;
  metricsToShow: string[];
  chartPreferences: Record<string, any>;
}

export interface UISettings {
  theme: 'light' | 'dark' | 'auto';
  density: 'comfortable' | 'compact' | 'spacious';
  sidebar: 'expanded' | 'collapsed';
  showTutorials: boolean;
}

// Authentication state and context
export interface AuthState {
  user: User | null;
  tenant: TenantContext | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  lastActivity: Date | null;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresAt: Date;
  tokenType: 'Bearer';
  scope: string[];
}

export interface LoginCredentials {
  email: string;
  password: string;
  tenantId?: string;
  rememberMe?: boolean;
}

export interface LoginResponse {
  user: User;
  tenant: TenantContext;
  tokens: AuthTokens;
  sessionId: string;
}

export interface RefreshTokenResponse {
  tokens: AuthTokens;
  user?: User; // Updated user data if changed
}

// Registration and setup
export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
  tenantName: string;
  companyName?: string;
  inviteCode?: string;
}

export interface RegisterResponse {
  userId: string;
  tenantId: string;
  emailVerificationRequired: boolean;
  setupRequired: boolean;
  message: string;
}

export interface EmailVerificationRequest {
  email: string;
  token: string;
}

export interface PasswordResetRequest {
  email: string;
  tenantId?: string;
}

export interface PasswordResetResponse {
  message: string;
  resetRequired: boolean;
}

export interface PasswordUpdateRequest {
  token: string;
  newPassword: string;
  email: string;
}

// Multi-tenant authentication
export interface TenantAuthConfig {
  tenantId: string;
  domain?: string;
  ssoEnabled: boolean;
  ssoProvider?: 'google' | 'microsoft' | 'okta' | 'auth0';
  ssoConfig?: Record<string, any>;
  passwordPolicy: PasswordPolicy;
  sessionTimeout: number;
  maxSessions: number;
  ipWhitelist?: string[];
}

export interface PasswordPolicy {
  minLength: number;
  requireUppercase: boolean;
  requireLowercase: boolean;
  requireNumbers: boolean;
  requireSymbols: boolean;
  maxAge: number; // days
  historyCount: number; // previous passwords to remember
  lockoutAttempts: number;
  lockoutDuration: number; // minutes
}

// SSO and OAuth types
export interface SSOConfig {
  provider: 'google' | 'microsoft' | 'okta' | 'auth0';
  clientId: string;
  redirectUri: string;
  scopes: string[];
  domain?: string;
}

export interface SSOLoginRequest {
  provider: string;
  code: string;
  state: string;
  redirectUri: string;
}

// Session management
export interface SessionInfo {
  sessionId: string;
  userId: string;
  tenantId: string;
  userAgent: string;
  ipAddress: string;
  createdAt: string;
  lastActivity: string;
  expiresAt: string;
  isActive: boolean;
}

export interface SessionActivity {
  sessionId: string;
  activity: string;
  timestamp: string;
  ipAddress: string;
  userAgent: string;
  details?: Record<string, any>;
}

// Security and audit
export interface SecurityEvent {
  id: string;
  type: 'login' | 'logout' | 'failed_login' | 'password_change' | 'permission_change' | 'suspicious_activity';
  userId?: string;
  tenantId: string;
  timestamp: string;
  ipAddress: string;
  userAgent: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  details: Record<string, any>;
  resolved: boolean;
}

export interface AuditLog {
  id: string;
  userId: string;
  tenantId: string;
  action: string;
  resource: string;
  resourceId?: string;
  timestamp: string;
  ipAddress: string;
  userAgent: string;
  oldValues?: Record<string, any>;
  newValues?: Record<string, any>;
  success: boolean;
  error?: string;
}

// API Key management (for programmatic access)
export interface ApiKey {
  id: string;
  name: string;
  description?: string;
  userId: string;
  tenantId: string;
  key: string; // Only returned on creation
  permissions: Permission[];
  expiresAt?: string;
  lastUsed?: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CreateApiKeyRequest {
  name: string;
  description?: string;
  permissions: Permission[];
  expiresAt?: string;
}

export interface CreateApiKeyResponse {
  apiKey: ApiKey;
  message: string;
}