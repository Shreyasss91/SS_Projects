# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\frontend\src\api



---

# FILE: frontend\src\api\admin.ts

```ts
import type {
  AddFreezeQtyRequest,
  AddHolidayRequest,
  AdminStats,
  DiagnosticsResponse,
  ErrorGroupsResponse,
  ErrorsListResponse,
  ErrorsStats,
  FreezeQty,
  Holiday,
  HolidaysResponse,
  MCPAuditResponse,
  MCPSettingsResponse,
  MCPSettingsUpdateRequest,
  MCPSettingsUpdateResponse,
  OAuthClientsResponse,
  SystemInfo,
  TimingsResponse,
  TodayTiming,
  UpdateFreezeQtyRequest,
  UpdateTimingRequest,
} from '@/types/admin'
import { webClient } from './client'

interface ApiResponse<T = void> {
  status: string
  message?: string
  data?: T
}

export const adminApi = {
  // ============================================================================
  // Admin Stats
  // ============================================================================

  /**
   * Get admin dashboard stats
   */
  getStats: async (): Promise<AdminStats> => {
    const response = await webClient.get<ApiResponse<void> & AdminStats>('/admin/api/stats')
    return {
      freeze_count: response.data.freeze_count,
      holiday_count: response.data.holiday_count,
    }
  },

  // ============================================================================
  // Freeze Quantity APIs
  // ============================================================================

  /**
   * Get all freeze quantities
   */
  getFreezeList: async (): Promise<FreezeQty[]> => {
    const response = await webClient.get<ApiResponse<FreezeQty[]>>('/admin/api/freeze')
    return response.data.data || []
  },

  /**
   * Add a new freeze quantity entry
   */
  addFreeze: async (data: AddFreezeQtyRequest): Promise<ApiResponse<FreezeQty>> => {
    const response = await webClient.post<ApiResponse<FreezeQty>>('/admin/api/freeze', data)
    return response.data
  },

  /**
   * Edit a freeze quantity entry
   */
  editFreeze: async (id: number, data: UpdateFreezeQtyRequest): Promise<ApiResponse<FreezeQty>> => {
    const response = await webClient.put<ApiResponse<FreezeQty>>(`/admin/api/freeze/${id}`, data)
    return response.data
  },

  /**
   * Delete a freeze quantity entry
   */
  deleteFreeze: async (id: number): Promise<ApiResponse> => {
    const response = await webClient.delete<ApiResponse>(`/admin/api/freeze/${id}`)
    return response.data
  },

  /**
   * Upload CSV file to update freeze quantities
   */
  uploadFreezeCSV: async (
    file: File,
    exchange: string
  ): Promise<ApiResponse<{ count: number }>> => {
    const formData = new FormData()
    formData.append('csv_file', file)
    formData.append('exchange', exchange)

    const response = await webClient.post<ApiResponse<{ count: number }>>(
      '/admin/api/freeze/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return response.data
  },

  // ============================================================================
  // Holiday APIs
  // ============================================================================

  /**
   * Get holidays for a specific year
   */
  getHolidays: async (year?: number): Promise<HolidaysResponse> => {
    const params = year ? `?year=${year}` : ''
    const response = await webClient.get<HolidaysResponse>(`/admin/api/holidays${params}`)
    return response.data
  },

  /**
   * Add a new holiday
   */
  addHoliday: async (data: AddHolidayRequest): Promise<ApiResponse<Holiday>> => {
    const response = await webClient.post<ApiResponse<Holiday>>('/admin/api/holidays', data)
    return response.data
  },

  /**
   * Delete a holiday
   */
  deleteHoliday: async (id: number): Promise<ApiResponse> => {
    const response = await webClient.delete<ApiResponse>(`/admin/api/holidays/${id}`)
    return response.data
  },

  // ============================================================================
  // Market Timings APIs
  // ============================================================================

  /**
   * Get all market timings
   */
  getTimings: async (): Promise<TimingsResponse> => {
    const response = await webClient.get<TimingsResponse>('/admin/api/timings')
    return response.data
  },

  /**
   * Edit market timing for an exchange
   */
  editTiming: async (exchange: string, data: UpdateTimingRequest): Promise<ApiResponse> => {
    const response = await webClient.put<ApiResponse>(`/admin/api/timings/${exchange}`, data)
    return response.data
  },

  /**
   * Check market timings for a specific date
   */
  checkTimings: async (date: string): Promise<{ date: string; timings: TodayTiming[] }> => {
    const response = await webClient.post<ApiResponse & { date: string; timings: TodayTiming[] }>(
      '/admin/api/timings/check',
      { date }
    )
    return { date: response.data.date, timings: response.data.timings }
  },

  // ============================================================================
  // Diagnostics APIs
  // ============================================================================

  getErrors: async (params?: {
    limit?: number
    level?: string
    q?: string
  }): Promise<ErrorsListResponse> => {
    const search = new URLSearchParams()
    if (params?.limit) search.set('limit', String(params.limit))
    if (params?.level) search.set('level', params.level)
    if (params?.q) search.set('q', params.q)
    const qs = search.toString() ? `?${search.toString()}` : ''
    const response = await webClient.get<ErrorsListResponse>(`/admin/api/errors${qs}`)
    return response.data
  },

  getErrorStats: async (): Promise<ErrorsStats> => {
    const response = await webClient.get<ErrorsStats>('/admin/api/errors/stats')
    return response.data
  },

  getErrorGroups: async (limit = 50): Promise<ErrorGroupsResponse> => {
    const response = await webClient.get<ErrorGroupsResponse>(
      `/admin/api/errors/groups?limit=${limit}`
    )
    return response.data
  },

  getSystemInfo: async (): Promise<SystemInfo> => {
    const response = await webClient.get<ApiResponse<SystemInfo>>('/admin/api/system')
    if (!response.data.data) {
      throw new Error(response.data.message || 'Failed to load system info')
    }
    return response.data.data
  },

  runDiagnostics: async (): Promise<DiagnosticsResponse> => {
    const response = await webClient.post<DiagnosticsResponse>('/admin/api/system/diagnostics')
    return response.data
  },

  /**
   * Trigger a browser download of the system report.
   * The server enforces filename and content-disposition; we just navigate to the URL.
   */
  downloadReport: (format: 'md' | 'txt' = 'md'): void => {
    const fmt = format === 'txt' ? 'txt' : 'md'
    window.location.href = `/admin/api/system/report?format=${fmt}`
  },

  // ============================================================================
  // Remote MCP admin APIs
  // ============================================================================

  getOAuthClients: async (): Promise<OAuthClientsResponse> => {
    const response = await webClient.get<OAuthClientsResponse>('/admin/api/oauth/clients')
    return response.data
  },

  approveOAuthClient: async (clientId: string): Promise<{ status: string }> => {
    const response = await webClient.post<{ status: string }>(
      `/admin/api/oauth/clients/${clientId}/approve`
    )
    return response.data
  },

  revokeOAuthClient: async (
    clientId: string
  ): Promise<{ status: string; tokens_revoked: number }> => {
    const response = await webClient.post<{ status: string; tokens_revoked: number }>(
      `/admin/api/oauth/clients/${clientId}/revoke`,
      { confirm: true }
    )
    return response.data
  },

  getMCPAudit: async (params?: {
    limit?: number
    tool?: string
    scope?: string
    outcome?: string
  }): Promise<MCPAuditResponse> => {
    const search = new URLSearchParams()
    if (params?.limit) search.set('limit', String(params.limit))
    if (params?.tool) search.set('tool', params.tool)
    if (params?.scope) search.set('scope', params.scope)
    if (params?.outcome) search.set('outcome', params.outcome)
    const qs = search.toString() ? `?${search.toString()}` : ''
    const response = await webClient.get<MCPAuditResponse>(`/admin/api/mcp/audit${qs}`)
    return response.data
  },

  triggerMCPKillSwitch: async (): Promise<{ status: string; tokens_revoked: number }> => {
    const response = await webClient.post<{ status: string; tokens_revoked: number }>(
      '/admin/api/mcp/kill-switch',
      { confirm: 'REVOKE_ALL_MCP_TOKENS' }
    )
    return response.data
  },

  getMCPSettings: async (): Promise<MCPSettingsResponse> => {
    const response = await webClient.get<MCPSettingsResponse>('/admin/api/mcp/settings')
    return response.data
  },

  updateMCPSettings: async (
    payload: MCPSettingsUpdateRequest
  ): Promise<MCPSettingsUpdateResponse> => {
    const response = await webClient.put<MCPSettingsUpdateResponse>(
      '/admin/api/mcp/settings',
      payload
    )
    return response.data
  },
}

```


---

# FILE: frontend\src\api\auth.ts

```ts
import type { BrokerInfo, LoginCredentials, LoginResponse, SessionInfo } from '@/types/auth'
import { authClient } from './client'

export const authApi = {
  /**
   * Login with username and password
   */
  login: async (credentials: LoginCredentials, csrfToken?: string): Promise<LoginResponse> => {
    const formData = new FormData()
    formData.append('username', credentials.username)
    formData.append('password', credentials.password)
    if (csrfToken) {
      formData.append('csrf_token', csrfToken)
    }

    const response = await authClient.post<LoginResponse>('/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  /**
   * Logout current user
   */
  logout: async (): Promise<void> => {
    await authClient.post('/auth/logout')
  },

  /**
   * Get current session info
   */
  getSession: async (): Promise<SessionInfo> => {
    const response = await authClient.get<SessionInfo>('/auth/session')
    return response.data
  },

  /**
   * Get list of available brokers
   */
  getBrokers: async (): Promise<BrokerInfo[]> => {
    const response = await authClient.get<{ brokers: BrokerInfo[] }>('/auth/brokers')
    return response.data.brokers
  },

  /**
   * Initiate broker OAuth flow
   */
  initiateBrokerAuth: async (
    broker: string
  ): Promise<{ redirect_url?: string; requires_totp?: boolean }> => {
    const response = await authClient.post(`/auth/broker/${broker}`)
    return response.data
  },

  /**
   * Submit TOTP for broker authentication
   */
  submitTOTP: async (
    broker: string,
    totp: string,
    additionalFields?: Record<string, string>
  ): Promise<LoginResponse> => {
    const formData = new FormData()
    formData.append('totp', totp)
    if (additionalFields) {
      Object.entries(additionalFields).forEach(([key, value]) => {
        formData.append(key, value)
      })
    }
    const response = await authClient.post<LoginResponse>(`/${broker}/auth`, formData)
    return response.data
  },

  /**
   * Get CSRF token for forms
   */
  getCSRFToken: async (): Promise<string> => {
    const response = await authClient.get<{ csrf_token: string }>('/auth/csrf-token')
    return response.data.csrf_token
  },

  /**
   * Reset password request
   */
  resetPassword: async (email: string): Promise<LoginResponse> => {
    const formData = new FormData()
    formData.append('email', email)
    const response = await authClient.post<LoginResponse>('/auth/reset-password', formData)
    return response.data
  },

  /**
   * Change password
   */
  changePassword: async (currentPassword: string, newPassword: string): Promise<LoginResponse> => {
    const formData = new FormData()
    formData.append('current_password', currentPassword)
    formData.append('new_password', newPassword)
    const response = await authClient.post<LoginResponse>('/auth/change-password', formData)
    return response.data
  },
}

```


---

# FILE: frontend\src\api\chartink.ts

```ts
import type {
  AddChartinkSymbolRequest,
  ChartinkStrategy,
  ChartinkSymbolMapping,
  CreateChartinkStrategyRequest,
} from '@/types/chartink'
import type { SymbolSearchResult } from '@/types/strategy'
import type { ApiResponse } from '@/types/trading'
import { webClient } from './client'

export const chartinkApi = {
  /**
   * Get all Chartink strategies
   */
  getStrategies: async (): Promise<ChartinkStrategy[]> => {
    const response = await webClient.get<{ strategies: ChartinkStrategy[] }>(
      '/chartink/api/strategies'
    )
    return response.data.strategies || []
  },

  /**
   * Get a single Chartink strategy by ID
   */
  getStrategy: async (
    strategyId: number
  ): Promise<{ strategy: ChartinkStrategy; mappings: ChartinkSymbolMapping[] }> => {
    const response = await webClient.get<{
      strategy: ChartinkStrategy
      mappings: ChartinkSymbolMapping[]
    }>(`/chartink/api/strategy/${strategyId}`)
    return response.data
  },

  /**
   * Create a new Chartink strategy
   */
  createStrategy: async (
    data: CreateChartinkStrategyRequest
  ): Promise<ApiResponse<{ strategy_id: number }>> => {
    const response = await webClient.post<ApiResponse<{ strategy_id: number }>>(
      '/chartink/api/strategy',
      data
    )
    return response.data
  },

  /**
   * Toggle strategy active/inactive
   */
  toggleStrategy: async (strategyId: number): Promise<ApiResponse<{ is_active: boolean }>> => {
    const response = await webClient.post<ApiResponse<{ is_active: boolean }>>(
      `/chartink/api/strategy/${strategyId}/toggle`
    )
    return response.data
  },

  /**
   * Delete a strategy
   */
  deleteStrategy: async (strategyId: number): Promise<ApiResponse<void>> => {
    const response = await webClient.post<ApiResponse<void>>(`/chartink/${strategyId}/delete`)
    return response.data
  },

  /**
   * Add a symbol mapping to a strategy
   */
  addSymbolMapping: async (
    strategyId: number,
    data: AddChartinkSymbolRequest
  ): Promise<ApiResponse<void>> => {
    const response = await webClient.post<ApiResponse<void>>(
      `/chartink/${strategyId}/configure`,
      data
    )
    return response.data
  },

  /**
   * Add bulk symbol mappings
   */
  addBulkSymbols: async (
    strategyId: number,
    csvData: string
  ): Promise<ApiResponse<{ added: number; failed: number }>> => {
    const response = await webClient.post<ApiResponse<{ added: number; failed: number }>>(
      `/chartink/${strategyId}/configure`,
      { symbols: csvData } // Backend expects 'symbols' field with CSV data
    )
    return response.data
  },

  /**
   * Delete a symbol mapping
   */
  deleteSymbolMapping: async (
    strategyId: number,
    mappingId: number
  ): Promise<ApiResponse<void>> => {
    const response = await webClient.post<ApiResponse<void>>(
      `/chartink/${strategyId}/symbol/${mappingId}/delete`
    )
    return response.data
  },

  /**
   * Search symbols (limited to NSE/BSE)
   */
  searchSymbols: async (query: string, exchange?: 'NSE' | 'BSE'): Promise<SymbolSearchResult[]> => {
    const params = new URLSearchParams({ q: query })
    if (exchange) {
      params.append('exchange', exchange)
    }
    const response = await webClient.get<{ results: SymbolSearchResult[] }>(
      `/chartink/search?${params.toString()}`
    )
    return response.data.results || []
  },

  /**
   * Get webhook URL for a strategy
   */
  getWebhookUrl: (webhookId: string): string => {
    const baseUrl = window.location.origin
    return `${baseUrl}/chartink/webhook/${webhookId}`
  },
}

```


---

# FILE: frontend\src\api\client.ts

```ts
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

// Helper to fetch CSRF token
export async function fetchCSRFToken(): Promise<string> {
  const response = await fetch('/auth/csrf-token', {
    credentials: 'include',
  })
  const data = await response.json()
  return data.csrf_token
}

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // API key can be added here if needed for specific endpoints
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized - redirect to login
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth client for login/logout operations
export const authClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  withCredentials: true,
})

// Endpoints that don't require CSRF token (no session yet)
const CSRF_EXEMPT_ENDPOINTS = ['/auth/login', '/auth/setup']

// Add CSRF token to auth client requests (except for initial login/setup)
authClient.interceptors.request.use(
  async (config) => {
    // Check if endpoint is exempt from CSRF (exact match or starts with path + query/fragment)
    const url = config.url || ''
    const isExempt = CSRF_EXEMPT_ENDPOINTS.some((exempt) => {
      // Exact match or match with query string/fragment
      return url === exempt || url.startsWith(`${exempt}?`) || url.startsWith(`${exempt}#`)
    })

    if (
      !isExempt &&
      (config.method === 'post' || config.method === 'put' || config.method === 'delete')
    ) {
      try {
        const csrfToken = await fetchCSRFToken()
        if (csrfToken) {
          config.headers['X-CSRFToken'] = csrfToken
        }
      } catch {
        // Continue without CSRF for auth operations - backend may handle differently
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Web client for session-based routes (non-API endpoints) with CSRF support
// Note: Don't set default Content-Type here - let axios set it automatically based on data type
// (multipart/form-data for FormData, application/json for objects, etc.)
export const webClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
})

// Add CSRF token to web client requests
webClient.interceptors.request.use(
  async (config) => {
    const method = config.method?.toLowerCase()
    if (method === 'post' || method === 'put' || method === 'delete') {
      try {
        const csrfToken = await fetchCSRFToken()
        if (!csrfToken) {
          // Reject request if CSRF token is empty - security requirement
          return Promise.reject(new Error('CSRF token is required for this operation'))
        }
        config.headers['X-CSRFToken'] = csrfToken
      } catch {
        // Reject request if CSRF token fetch fails - security requirement
        return Promise.reject(
          new Error('Failed to fetch CSRF token. Please refresh the page and try again.')
        )
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for web client
webClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    if (status === 401) {
      // Unauthorized - redirect to login
      window.location.href = '/login'
    } else if (status === 403) {
      // Forbidden - user doesn't have permission for this resource
      // Create a more descriptive error for the caller to handle
      error.message = 'You do not have permission to access this resource'
    }
    return Promise.reject(error)
  }
)

export default apiClient

```


---

# FILE: frontend\src\api\custom-straddle.ts

```ts
import { webClient } from './client'

export interface PnLDataPoint {
  time: number
  pnl: number
  spot: number
  atm_strike: number
  entry_strike: number
  ce_price: number
  pe_price: number
  straddle: number
  synthetic_future: number
  adjustments: number
}

export interface TradeEntry {
  time: number
  type: 'ENTRY' | 'ADJUSTMENT' | 'EXIT'
  strike: number
  old_strike?: number
  ce_price: number
  pe_price: number
  straddle: number
  exit_ce?: number
  exit_pe?: number
  exit_straddle?: number
  spot: number
  leg_pnl: number
  cumulative_pnl: number
}

export interface SimulationSummary {
  total_pnl: number
  total_adjustments: number
  max_pnl: number
  min_pnl: number
}

export interface CustomStraddleData {
  underlying: string
  underlying_ltp: number
  expiry_date: string
  interval: string
  days_to_expiry: number
  adjustment_points: number
  lot_size: number
  lots: number
  quantity: number
  pnl_series: PnLDataPoint[]
  trades: TradeEntry[]
  summary: SimulationSummary
}

export interface CustomStraddleResponse {
  status: 'success' | 'error'
  message?: string
  data?: CustomStraddleData
}

export interface IntervalsData {
  seconds: string[]
  minutes: string[]
  hours: string[]
}

export interface IntervalsResponse {
  status: 'success' | 'error'
  message?: string
  data?: IntervalsData
}

export const customStraddleApi = {
  simulate: async (params: {
    underlying: string
    exchange: string
    expiry_date: string
    interval: string
    days?: number
    adjustment_points?: number
    lot_size?: number
    lots?: number
  }): Promise<CustomStraddleResponse> => {
    const response = await webClient.post<CustomStraddleResponse>(
      '/straddlepnl/api/simulate',
      params
    )
    return response.data
  },

  getIntervals: async (): Promise<IntervalsResponse> => {
    const response = await webClient.get<IntervalsResponse>('/straddlepnl/api/intervals')
    return response.data
  },

  getLotSize: async (
    underlying: string,
    exchange: string
  ): Promise<{ status: string; lotsize: number | null }> => {
    const response = await webClient.get<{ status: string; lotsize: number | null }>(
      `/straddlepnl/api/lotsize?underlying=${underlying}&exchange=${exchange}`
    )
    return response.data
  },
}

```


---

# FILE: frontend\src\api\flow.ts

```ts
// api/flow.ts
// Flow Workflow API module

import type { Edge, Node } from '@xyflow/react'
import { webClient } from './client'

// =============================================================================
// Types
// =============================================================================

export interface Workflow {
  id: number
  name: string
  description: string | null
  nodes: Node[]
  edges: Edge[]
  is_active: boolean
  schedule_job_id: string | null
  webhook_token: string | null
  webhook_secret: string | null
  webhook_enabled: boolean
  webhook_auth_type: 'payload' | 'url'
  created_at: string
  updated_at: string
}

export interface WorkflowListItem {
  id: number
  name: string
  description: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  last_execution_status: string | null
}

export interface WorkflowExecution {
  id: number
  workflow_id: number
  status: string
  started_at: string | null
  completed_at: string | null
  logs: ExecutionLog[]
  error: string | null
}

export interface ExecutionLog {
  time: string
  message: string
  level: string
}

export interface WebhookInfo {
  webhook_token: string
  webhook_secret: string
  webhook_enabled: boolean
  webhook_auth_type: 'payload' | 'url'
  webhook_url: string
  webhook_url_with_symbol: string
  webhook_url_with_secret: string | null
}

export interface WorkflowExportData {
  version: string
  name: string
  description: string | null
  nodes: Node[]
  edges: Edge[]
  exported_at: string
}

// =============================================================================
// API Functions
// =============================================================================

const FLOW_API_BASE = '/flow/api'

/**
 * List all workflows
 */
export async function listWorkflows(): Promise<WorkflowListItem[]> {
  const response = await webClient.get(`${FLOW_API_BASE}/workflows`)
  return response.data
}

/**
 * Get a single workflow by ID
 */
export async function getWorkflow(id: number): Promise<Workflow> {
  const response = await webClient.get(`${FLOW_API_BASE}/workflows/${id}`)
  return response.data
}

/**
 * Create a new workflow
 */
export async function createWorkflow(data: {
  name: string
  description?: string
  nodes?: Node[]
  edges?: Edge[]
}): Promise<Workflow> {
  const response = await webClient.post(`${FLOW_API_BASE}/workflows`, data)
  return response.data
}

/**
 * Update an existing workflow
 */
export async function updateWorkflow(
  id: number,
  data: {
    name?: string
    description?: string
    nodes?: Node[]
    edges?: Edge[]
  }
): Promise<Workflow> {
  const response = await webClient.put(`${FLOW_API_BASE}/workflows/${id}`, data)
  return response.data
}

/**
 * Delete a workflow
 */
export async function deleteWorkflow(id: number): Promise<{ status: string; message: string }> {
  const response = await webClient.delete(`${FLOW_API_BASE}/workflows/${id}`)
  return response.data
}

/**
 * Activate a workflow
 */
export async function activateWorkflow(id: number): Promise<{
  status: string
  message: string
  job_id?: string
  next_run?: string
}> {
  const response = await webClient.post(`${FLOW_API_BASE}/workflows/${id}/activate`)
  return response.data
}

/**
 * Deactivate a workflow
 */
export async function deactivateWorkflow(id: number): Promise<{ status: string; message: string }> {
  const response = await webClient.post(`${FLOW_API_BASE}/workflows/${id}/deactivate`)
  return response.data
}

/**
 * Execute a workflow manually
 */
export async function executeWorkflow(id: number): Promise<{
  status: string
  message: string
  execution_id?: number
  logs?: ExecutionLog[]
}> {
  const response = await webClient.post(`${FLOW_API_BASE}/workflows/${id}/execute`)
  return response.data
}

/**
 * Get workflow execution history
 */
export async function getWorkflowExecutions(id: number, limit = 20): Promise<WorkflowExecution[]> {
  const response = await webClient.get(`${FLOW_API_BASE}/workflows/${id}/executions?limit=${limit}`)
  return response.data
}

/**
 * Get webhook configuration for a workflow
 */
export async function getWebhookInfo(id: number): Promise<WebhookInfo> {
  const response = await webClient.get(`${FLOW_API_BASE}/workflows/${id}/webhook`)
  return response.data
}

/**
 * Enable webhook for a workflow
 */
export async function enableWebhook(
  id: number
): Promise<WebhookInfo & { status: string; message: string }> {
  const response = await webClient.post(`${FLOW_API_BASE}/workflows/${id}/webhook/enable`)
  return response.data
}

/**
 * Disable webhook for a workflow
 */
export async function disableWebhook(id: number): Promise<{ status: string; message: string }> {
  const response = await webClient.post(`${FLOW_API_BASE}/workflows/${id}/webhook/disable`)
  return response.data
}

/**
 * Regenerate webhook token
 */
export async function regenerateWebhook(id: number): Promise<{
  status: string
  message: string
  webhook_token: string
  webhook_secret: string
  webhook_url: string
  webhook_url_with_symbol: string
}> {
  const response = await webClient.post(`${FLOW_API_BASE}/workflows/${id}/webhook/regenerate`)
  return response.data
}

/**
 * Regenerate webhook secret only
 */
export async function regenerateWebhookSecret(id: number): Promise<{
  status: string
  message: string
  webhook_secret: string
}> {
  const response = await webClient.post(
    `${FLOW_API_BASE}/workflows/${id}/webhook/regenerate-secret`
  )
  return response.data
}

/**
 * Update webhook authentication type
 */
export async function updateWebhookAuthType(
  id: number,
  authType: 'payload' | 'url'
): Promise<{
  status: string
  message: string
  webhook_auth_type: 'payload' | 'url'
  webhook_url: string
  webhook_url_with_secret: string | null
}> {
  const response = await webClient.post(`${FLOW_API_BASE}/workflows/${id}/webhook/auth-type`, {
    auth_type: authType,
  })
  return response.data
}

/**
 * Export workflow for sharing
 */
export async function exportWorkflow(id: number): Promise<WorkflowExportData> {
  const response = await webClient.get(`${FLOW_API_BASE}/workflows/${id}/export`)
  return response.data
}

/**
 * Import workflow from JSON
 * Backend returns { status, workflow_id } so we transform it to { id, name }
 */
export async function importWorkflow(
  data: WorkflowExportData
): Promise<{ id: number; name: string }> {
  const response = await webClient.post(`${FLOW_API_BASE}/workflows/import`, data)
  return {
    id: response.data.workflow_id,
    name: data.name || 'Imported Workflow',
  }
}

// =============================================================================
// Index Symbols Types & API
// =============================================================================

export interface IndexSymbolInfo {
  value: string
  label: string
  exchange: string
  lotSize: number
}

/**
 * Get lot sizes for index symbols from master contract database
 * Returns dynamic lot sizes instead of hardcoded values
 */
export async function getIndexSymbolsLotSizes(): Promise<IndexSymbolInfo[]> {
  const response = await webClient.get(`${FLOW_API_BASE}/index-symbols`)
  return response.data.data || []
}

// =============================================================================
// React Query Keys
// =============================================================================

export const flowQueryKeys = {
  all: ['flow'] as const,
  workflows: () => [...flowQueryKeys.all, 'workflows'] as const,
  workflow: (id: number) => [...flowQueryKeys.workflows(), id] as const,
  executions: (id: number) => [...flowQueryKeys.workflow(id), 'executions'] as const,
  webhook: (id: number) => [...flowQueryKeys.workflow(id), 'webhook'] as const,
  indexSymbols: () => [...flowQueryKeys.all, 'index-symbols'] as const,
}

```


---

# FILE: frontend\src\api\gex.ts

```ts
import { webClient } from './client'

export interface GEXChainItem {
  strike: number
  ce_oi: number
  pe_oi: number
  ce_gamma: number
  pe_gamma: number
  ce_gex: number
  pe_gex: number
  net_gex: number
}

export interface GEXDataResponse {
  status: 'success' | 'error'
  message?: string
  underlying?: string
  spot_price?: number
  futures_price?: number | null
  lot_size?: number
  atm_strike?: number
  expiry_date?: string
  pcr_oi?: number
  total_ce_oi?: number
  total_pe_oi?: number
  total_ce_gex?: number
  total_pe_gex?: number
  total_net_gex?: number
  chain?: GEXChainItem[]
}

export interface UnderlyingsResponse {
  status: 'success' | 'error'
  underlyings: string[]
}

export interface ExpiriesResponse {
  status: 'success' | 'error'
  expiries: string[]
}

export const gexApi = {
  getGEXData: async (params: {
    underlying: string
    exchange: string
    expiry_date: string
  }): Promise<GEXDataResponse> => {
    const response = await webClient.post<GEXDataResponse>('/gex/api/gex-data', params)
    return response.data
  },

  getUnderlyings: async (exchange: string): Promise<UnderlyingsResponse> => {
    const response = await webClient.get<UnderlyingsResponse>(
      `/search/api/underlyings?exchange=${exchange}`
    )
    return response.data
  },

  getExpiries: async (exchange: string, underlying: string): Promise<ExpiriesResponse> => {
    const response = await webClient.get<ExpiriesResponse>(
      `/search/api/expiries?exchange=${exchange}&underlying=${underlying}`
    )
    return response.data
  },
}

```


---

# FILE: frontend\src\api\health.ts

```ts
/**
 * Health Monitoring API Client
 * Industry-standard health check endpoints
 */

import { webClient } from './client'

export interface HealthStatus {
  status: 'pass' | 'warn' | 'fail'
  version?: string
  serviceId?: string
  description?: string
}

export interface HealthCheck extends HealthStatus {
  checks?: {
    'database:connectivity'?: Array<{
      componentId: string
      status: 'pass' | 'fail'
      time: string
    }>
    'system:file-descriptors'?: Array<{
      componentId: string
      status: 'pass' | 'warn' | 'fail'
      observedValue: number
      observedUnit: string
      time: string
    }>
    'system:memory'?: Array<{
      componentId: string
      status: 'pass' | 'warn' | 'fail'
      observedValue: number
      observedUnit: string
      time: string
    }>
  }
}

export interface CurrentMetrics {
  timestamp: string
  fd: {
    count: number
    limit: number
    usage_percent: number
    status: 'pass' | 'warn' | 'fail'
  }
  memory: {
    rss_mb: number
    vms_mb: number
    percent: number
    available_mb: number
    swap_mb: number
    status: 'pass' | 'warn' | 'fail'
  }
  database: {
    total: number
    connections: Record<string, number>
    status: 'pass' | 'warn' | 'fail'
  }
  websocket: {
    total: number
    connections: Record<string, { count: number; symbols: number }>
    total_symbols: number
    status: 'pass' | 'warn' | 'fail'
  }
  threads: {
    count: number
    stuck: number
    details?: Array<{ id: number | null; name: string; daemon: boolean; alive: boolean }>
    status: 'pass' | 'warn' | 'fail'
  }
  processes?: Array<{
    pid: number | null
    name: string
    rss_mb: number
    vms_mb: number
    memory_percent: number
  }>
  overall_status: 'pass' | 'warn' | 'fail'
}

export interface HistoricalMetric {
  timestamp: string
  fd_count: number
  memory_rss_mb: number
  db_connections: number
  ws_connections: number
  threads: number
  overall_status: 'pass' | 'warn' | 'fail'
}

export interface HealthStats {
  total_samples: number
  time_period_hours: number
  fd: {
    current: number
    avg: number
    min: number
    max: number
    fail_count: number
    warn_count: number
  }
  memory: {
    current_mb: number
    avg_mb: number
    min_mb: number
    max_mb: number
    fail_count: number
    warn_count: number
  }
  database: {
    current: number
    avg: number
    min: number
    max: number
  }
  websocket: {
    current: number
    avg: number
    min: number
    max: number
  }
  threads: {
    current: number
    avg: number
    min: number
    max: number
  }
  status?: {
    overall?: { pass: number; warn: number; fail: number }
    fd?: { warn: number; fail: number }
    memory?: { warn: number; fail: number }
    database?: { warn: number; fail: number }
    websocket?: { warn: number; fail: number }
    threads?: { warn: number; fail: number }
  }
}

export interface HealthAlert {
  id: number
  timestamp: string
  alert_type: string
  severity: 'warn' | 'fail'
  metric_name: string
  metric_value: number
  threshold_value: number
  message: string
  acknowledged: boolean
  resolved: boolean
}

/**
 * Simple health check (for AWS ELB, K8s)
 * No authentication required
 */
export async function getSimpleHealth(): Promise<HealthStatus> {
  const response = await webClient.get<HealthStatus>('/health')
  return response.data
}

/**
 * Detailed health check with DB connectivity
 * No authentication required
 */
export async function getDetailedHealthCheck(): Promise<HealthCheck> {
  const response = await webClient.get<HealthCheck>('/health/check')
  return response.data
}

/**
 * Get current metrics snapshot
 * Requires authentication
 */
export async function getCurrentMetrics(): Promise<CurrentMetrics> {
  const response = await webClient.get<CurrentMetrics>('/health/api/current')
  return response.data
}

/**
 * Get metrics history
 * Requires authentication
 */
export async function getMetricsHistory(hours = 24): Promise<HistoricalMetric[]> {
  const response = await webClient.get<HistoricalMetric[]>('/health/api/history', {
    params: { hours },
  })
  return response.data
}

/**
 * Get aggregated statistics
 * Requires authentication
 */
export async function getHealthStats(hours = 24): Promise<HealthStats> {
  const response = await webClient.get<HealthStats>('/health/api/stats', {
    params: { hours },
  })
  return response.data
}

/**
 * Get active alerts
 * Requires authentication
 */
export async function getActiveAlerts(): Promise<HealthAlert[]> {
  const response = await webClient.get<HealthAlert[]>('/health/api/alerts')
  return response.data
}

/**
 * Acknowledge an alert
 * Requires authentication
 */
export async function acknowledgeAlert(alertId: number): Promise<void> {
  await webClient.post(`/health/api/alerts/${alertId}/acknowledge`)
}

/**
 * Resolve an alert
 * Requires authentication
 */
export async function resolveAlert(alertId: number): Promise<void> {
  await webClient.post(`/health/api/alerts/${alertId}/resolve`)
}

/**
 * Export metrics to CSV
 * Requires authentication
 */
export function exportMetricsCSV(hours = 24): string {
  return `/health/export?hours=${hours}`
}

```


---

# FILE: frontend\src\api\iv-chart.ts

```ts
import { webClient } from './client'

export interface IVDataPoint {
  time: number
  iv: number | null
  delta: number | null
  gamma: number | null
  theta: number | null
  vega: number | null
  option_price: number
  underlying_price: number
}

export interface IVSeries {
  symbol: string
  option_type: 'CE' | 'PE'
  strike: number
  iv_data: IVDataPoint[]
}

export interface IVChartData {
  underlying: string
  underlying_ltp: number
  atm_strike: number
  ce_symbol: string
  pe_symbol: string
  interval: string
  series: IVSeries[]
}

export interface IVChartResponse {
  status: 'success' | 'error'
  message?: string
  data?: IVChartData
}

export interface DefaultSymbolsData {
  ce_symbol: string
  pe_symbol: string
  atm_strike: number
  exchange: string
  underlying_ltp: number
}

export interface DefaultSymbolsResponse {
  status: 'success' | 'error'
  message?: string
  data?: DefaultSymbolsData
}

export interface IntervalsData {
  seconds: string[]
  minutes: string[]
  hours: string[]
}

export interface IntervalsResponse {
  status: 'success' | 'error'
  message?: string
  data?: IntervalsData
}

export interface UnderlyingsResponse {
  status: 'success' | 'error'
  underlyings: string[]
}

export interface ExpiriesResponse {
  status: 'success' | 'error'
  expiries: string[]
}

export const ivChartApi = {
  getIVData: async (params: {
    underlying: string
    exchange: string
    expiry_date: string
    interval: string
    days?: number
  }): Promise<IVChartResponse> => {
    const response = await webClient.post<IVChartResponse>('/ivchart/api/iv-data', params)
    return response.data
  },

  getDefaultSymbols: async (params: {
    underlying: string
    exchange: string
    expiry_date: string
  }): Promise<DefaultSymbolsResponse> => {
    const response = await webClient.post<DefaultSymbolsResponse>(
      '/ivchart/api/default-symbols',
      params
    )
    return response.data
  },

  getIntervals: async (): Promise<IntervalsResponse> => {
    const response = await webClient.get<IntervalsResponse>('/ivchart/api/intervals')
    return response.data
  },

  getUnderlyings: async (exchange: string): Promise<UnderlyingsResponse> => {
    const response = await webClient.get<UnderlyingsResponse>(
      `/search/api/underlyings?exchange=${exchange}`
    )
    return response.data
  },

  getExpiries: async (exchange: string, underlying: string): Promise<ExpiriesResponse> => {
    const response = await webClient.get<ExpiriesResponse>(
      `/search/api/expiries?exchange=${exchange}&underlying=${underlying}`
    )
    return response.data
  },
}

```


---

# FILE: frontend\src\api\iv-smile.ts

```ts
import { webClient } from './client'

export interface IVSmileChainItem {
  strike: number
  ce_iv: number | null
  pe_iv: number | null
}

export interface IVSmileDataResponse {
  status: 'success' | 'error'
  message?: string
  underlying?: string
  spot_price?: number
  atm_strike?: number
  atm_iv?: number | null
  skew?: number | null
  expiry_date?: string
  chain?: IVSmileChainItem[]
}

export interface UnderlyingsResponse {
  status: 'success' | 'error'
  underlyings: string[]
}

export interface ExpiriesResponse {
  status: 'success' | 'error'
  expiries: string[]
}

export const ivSmileApi = {
  getIVSmileData: async (params: {
    underlying: string
    exchange: string
    expiry_date: string
  }): Promise<IVSmileDataResponse> => {
    const response = await webClient.post<IVSmileDataResponse>('/ivsmile/api/iv-smile-data', params)
    return response.data
  },

  getUnderlyings: async (exchange: string): Promise<UnderlyingsResponse> => {
    const response = await webClient.get<UnderlyingsResponse>(
      `/search/api/underlyings?exchange=${exchange}`
    )
    return response.data
  },

  getExpiries: async (exchange: string, underlying: string): Promise<ExpiriesResponse> => {
    const response = await webClient.get<ExpiriesResponse>(
      `/search/api/expiries?exchange=${exchange}&underlying=${underlying}`
    )
    return response.data
  },
}

```


---

# FILE: frontend\src\api\oi-profile.ts

```ts
import { webClient } from './client'

export interface CandleData {
  timestamp?: string | number
  time?: string | number
  open: number
  high: number
  low: number
  close: number
  volume: number
  oi?: number
}

export interface OIProfileChainItem {
  strike: number
  ce_oi: number
  pe_oi: number
  ce_oi_change: number
  pe_oi_change: number
}

export interface OIProfileDataResponse {
  status: 'success' | 'error'
  message?: string
  underlying?: string
  spot_price?: number
  atm_strike?: number
  lot_size?: number
  expiry_date?: string
  futures_symbol?: string | null
  interval?: string
  candles?: CandleData[]
  oi_chain?: OIProfileChainItem[]
}

export interface IntervalsResponse {
  status: 'success' | 'error'
  data?: { intervals: string[] }
}

export interface UnderlyingsResponse {
  status: 'success' | 'error'
  underlyings: string[]
}

export interface ExpiriesResponse {
  status: 'success' | 'error'
  expiries: string[]
}

export const oiProfileApi = {
  getProfileData: async (params: {
    underlying: string
    exchange: string
    expiry_date: string
    interval: string
    days: number
  }): Promise<OIProfileDataResponse> => {
    const response = await webClient.post<OIProfileDataResponse>(
      '/oiprofile/api/profile-data',
      params
    )
    return response.data
  },

  getIntervals: async (): Promise<IntervalsResponse> => {
    const response = await webClient.get<IntervalsResponse>('/oiprofile/api/intervals')
    return response.data
  },

  getUnderlyings: async (exchange: string): Promise<UnderlyingsResponse> => {
    const response = await webClient.get<UnderlyingsResponse>(
      `/search/api/underlyings?exchange=${exchange}`
    )
    return response.data
  },

  getExpiries: async (exchange: string, underlying: string): Promise<ExpiriesResponse> => {
    const response = await webClient.get<ExpiriesResponse>(
      `/search/api/expiries?exchange=${exchange}&underlying=${underlying}`
    )
    return response.data
  },
}

```


---

# FILE: frontend\src\api\oi-tracker.ts

```ts
import { webClient } from './client'

export interface OIChainItem {
  strike: number
  ce_oi: number
  pe_oi: number
}

export interface OIDataResponse {
  status: 'success' | 'error'
  message?: string
  underlying?: string
  spot_price?: number
  futures_price?: number | null
  lot_size?: number
  pcr_oi?: number
  pcr_volume?: number
  total_ce_oi?: number
  total_pe_oi?: number
  atm_strike?: number
  expiry_date?: string
  chain?: OIChainItem[]
}

export interface PainDataItem {
  strike: number
  ce_pain: number
  pe_pain: number
  total_pain: number
  total_pain_cr: number
}

export interface MaxPainResponse {
  status: 'success' | 'error'
  message?: string
  underlying?: string
  spot_price?: number
  futures_price?: number | null
  atm_strike?: number
  max_pain_strike?: number
  lot_size?: number
  pcr_oi?: number
  pcr_volume?: number
  expiry_date?: string
  pain_data?: PainDataItem[]
}

export interface UnderlyingsResponse {
  status: 'success' | 'error'
  underlyings: string[]
}

export interface ExpiriesResponse {
  status: 'success' | 'error'
  expiries: string[]
}

export const oiTrackerApi = {
  getOIData: async (params: {
    underlying: string
    exchange: string
    expiry_date: string
  }): Promise<OIDataResponse> => {
    const response = await webClient.post<OIDataResponse>('/oitracker/api/oi-data', params)
    return response.data
  },

  getMaxPain: async (params: {
    underlying: string
    exchange: string
    expiry_date: string
  }): Promise<MaxPainResponse> => {
    const response = await webClient.post<MaxPainResponse>('/oitracker/api/maxpain', params)
    return response.data
  },

  getUnderlyings: async (exchange: string): Promise<UnderlyingsResponse> => {
    const response = await webClient.get<UnderlyingsResponse>(
      `/search/api/underlyings?exchange=${exchange}`
    )
    return response.data
  },

  getExpiries: async (exchange: string, underlying: string): Promise<ExpiriesResponse> => {
    const response = await webClient.get<ExpiriesResponse>(
      `/search/api/expiries?exchange=${exchange}&underlying=${underlying}`
    )
    return response.data
  },
}

```


---

# FILE: frontend\src\api\option-chain.ts

```ts
import type { OptionChainResponse } from '@/types/option-chain'
import { apiClient } from './client'

export interface ExpiryResponse {
  status: 'success' | 'error'
  data: string[]
  message?: string
}

export const optionChainApi = {
  getOptionChain: async (
    apiKey: string,
    underlying: string,
    exchange: string,
    expiryDate: string,
    strikeCount?: number
  ): Promise<OptionChainResponse> => {
    const response = await apiClient.post<OptionChainResponse>('/optionchain', {
      apikey: apiKey,
      underlying,
      exchange,
      expiry_date: expiryDate,
      strike_count: strikeCount ?? 20,
    })
    return response.data
  },

  getExpiries: async (
    apiKey: string,
    symbol: string,
    exchange: string,
    instrumenttype: string = 'options'
  ): Promise<ExpiryResponse> => {
    const response = await apiClient.post<ExpiryResponse>('/expiry', {
      apikey: apiKey,
      symbol,
      exchange,
      instrumenttype,
    })
    return response.data
  },
}

```


---

# FILE: frontend\src\api\python-strategy.ts

```ts
import type {
  EnvironmentVariables,
  LogContent,
  LogFile,
  MasterContractStatus,
  PythonStrategy,
  PythonStrategyContent,
  ScheduleConfig,
} from '@/types/python-strategy'
import type { ApiResponse } from '@/types/trading'
import { webClient } from './client'

export const pythonStrategyApi = {
  /**
   * Get all Python strategies
   */
  getStrategies: async (): Promise<PythonStrategy[]> => {
    const response = await webClient.get<{ strategies: PythonStrategy[] }>('/python/api/strategies')
    return response.data.strategies || []
  },

  /**
   * Get a single strategy
   */
  getStrategy: async (strategyId: string): Promise<PythonStrategy> => {
    const response = await webClient.get<{ strategy: PythonStrategy }>(
      `/python/api/strategy/${strategyId}`
    )
    return response.data.strategy
  },

  /**
   * Get strategy content for editing
   */
  getStrategyContent: async (strategyId: string): Promise<PythonStrategyContent> => {
    const response = await webClient.get<PythonStrategyContent>(
      `/python/api/strategy/${strategyId}/content`
    )
    return response.data
  },

  /**
   * Upload a new strategy with mandatory schedule
   */
  uploadStrategy: async (
    name: string,
    file: File,
    schedule: {
      start_time: string
      stop_time: string
      days: string[]
      exchange?: string
    }
  ): Promise<ApiResponse<{ strategy_id: string }>> => {
    const formData = new FormData()
    formData.append('strategy_name', name)
    formData.append('strategy_file', file)
    formData.append('exchange', schedule.exchange || 'NSE')
    // Add schedule fields
    formData.append('schedule_start', schedule.start_time)
    formData.append('schedule_stop', schedule.stop_time)
    formData.append('schedule_days', JSON.stringify(schedule.days))

    const response = await webClient.post<ApiResponse<{ strategy_id: string }>>(
      '/python/new',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return response.data
  },

  /**
   * Save strategy content
   */
  saveStrategy: async (strategyId: string, content: string): Promise<ApiResponse<void>> => {
    const response = await webClient.post<ApiResponse<void>>(`/python/save/${strategyId}`, {
      content,
    })
    return response.data
  },

  /**
   * Export strategy file
   */
  exportStrategy: async (
    strategyId: string,
    version: 'saved' | 'current' = 'saved'
  ): Promise<Blob> => {
    const response = await webClient.get(`/python/export/${strategyId}?version=${version}`, {
      responseType: 'blob',
    })
    return response.data
  },

  /**
   * Delete a strategy
   */
  deleteStrategy: async (strategyId: string): Promise<ApiResponse<void>> => {
    const response = await webClient.post<ApiResponse<void>>(`/python/delete/${strategyId}`)
    return response.data
  },

  /**
   * Start a strategy
   */
  startStrategy: async (strategyId: string): Promise<ApiResponse<{ process_id: number }>> => {
    const response = await webClient.post<ApiResponse<{ process_id: number }>>(
      `/python/start/${strategyId}`
    )
    return response.data
  },

  /**
   * Stop a strategy
   */
  stopStrategy: async (strategyId: string): Promise<ApiResponse<void>> => {
    const response = await webClient.post<ApiResponse<void>>(`/python/stop/${strategyId}`)
    return response.data
  },

  /**
   * Clear error state
   */
  clearError: async (strategyId: string): Promise<ApiResponse<void>> => {
    const response = await webClient.post<ApiResponse<void>>(`/python/clear-error/${strategyId}`)
    return response.data
  },

  /**
   * Schedule a strategy
   */
  scheduleStrategy: async (
    strategyId: string,
    config: ScheduleConfig
  ): Promise<ApiResponse<void>> => {
    const response = await webClient.post<ApiResponse<void>>(
      `/python/schedule/${strategyId}`,
      config
    )
    return response.data
  },

  /**
   * Unschedule a strategy
   */
  unscheduleStrategy: async (strategyId: string): Promise<ApiResponse<void>> => {
    const response = await webClient.post<ApiResponse<void>>(`/python/unschedule/${strategyId}`)
    return response.data
  },

  /**
   * Get log files for a strategy
   */
  getLogFiles: async (strategyId: string): Promise<LogFile[]> => {
    const response = await webClient.get<{ logs: LogFile[] }>(`/python/api/logs/${strategyId}`)
    return response.data.logs || []
  },

  /**
   * Get log file content
   */
  getLogContent: async (strategyId: string, logName: string): Promise<LogContent> => {
    const response = await webClient.get<LogContent>(`/python/api/logs/${strategyId}/${logName}`)
    return response.data
  },

  /**
   * Clear all logs for a strategy
   */
  clearLogs: async (strategyId: string): Promise<ApiResponse<void>> => {
    const response = await webClient.post<ApiResponse<void>>(`/python/logs/${strategyId}/clear`)
    return response.data
  },

  /**
   * Get environment variables
   */
  getEnvVariables: async (strategyId: string): Promise<EnvironmentVariables> => {
    const response = await webClient.get<EnvironmentVariables>(`/python/env/${strategyId}`)
    return response.data
  },

  /**
   * Save environment variables
   */
  saveEnvVariables: async (
    strategyId: string,
    variables: EnvironmentVariables
  ): Promise<ApiResponse<void>> => {
    const response = await webClient.post<ApiResponse<void>>(`/python/env/${strategyId}`, variables)
    return response.data
  },

  /**
   * Get master contract status
   */
  getMasterContractStatus: async (): Promise<MasterContractStatus> => {
    const response = await webClient.get<MasterContractStatus>('/python/status')
    return response.data
  },

  /**
   * Check and start pending strategies (after master contract download)
   */
  checkAndStartPending: async (): Promise<ApiResponse<{ started: number }>> => {
    const response =
      await webClient.post<ApiResponse<{ started: number }>>('/python/check-contracts')
    return response.data
  },
}

```


---

# FILE: frontend\src\api\straddle-chart.ts

```ts
import { webClient } from './client'

export interface StraddleDataPoint {
  time: number
  spot: number
  atm_strike: number
  ce_price: number
  pe_price: number
  straddle: number
  synthetic_future: number
}

export interface StraddleChartData {
  underlying: string
  underlying_ltp: number
  expiry_date: string
  interval: string
  days_to_expiry: number
  series: StraddleDataPoint[]
}

export interface StraddleChartResponse {
  status: 'success' | 'error'
  message?: string
  data?: StraddleChartData
}

export interface IntervalsData {
  seconds: string[]
  minutes: string[]
  hours: string[]
}

export interface IntervalsResponse {
  status: 'success' | 'error'
  message?: string
  data?: IntervalsData
}

export const straddleChartApi = {
  getStraddleData: async (params: {
    underlying: string
    exchange: string
    expiry_date: string
    interval: string
    days?: number
  }): Promise<StraddleChartResponse> => {
    const response = await webClient.post<StraddleChartResponse>(
      '/straddle/api/straddle-data',
      params
    )
    return response.data
  },

  getIntervals: async (): Promise<IntervalsResponse> => {
    const response = await webClient.get<IntervalsResponse>('/straddle/api/intervals')
    return response.data
  },
}

```


---

# FILE: frontend\src\api\strategy-chart.ts

```ts
import { webClient } from './client'

export interface StrategyChartPoint {
  time: number
  // Missing when the broker doesn't return intraday history for the
  // underlying (e.g., Zerodha index 1m candles). The combined_premium
  // series is still valid; the chart hides the underlying curve.
  underlying?: number
  net_premium: number
  combined_premium: number
}

export interface StrategyChartData {
  underlying: string
  underlying_ltp: number
  interval: string
  tag: 'credit' | 'debit' | 'flat'
  entry_net_premium: number
  entry_abs_premium: number
  legs_used: number
  underlying_available: boolean
  series: StrategyChartPoint[]
}

export interface StrategyChartResponse {
  status: 'success' | 'error'
  message?: string
  data?: StrategyChartData
}

export interface StrategyChartLegInput {
  symbol: string
  exchange: string
  side: 'BUY' | 'SELL'
  segment: 'OPTION' | 'FUTURE'
  active: boolean
  price: number
}

export interface StrategyChartRequest {
  underlying: string
  exchange: string
  legs: StrategyChartLegInput[]
  interval: string
  days: number
}

export interface IntervalsData {
  seconds: string[]
  minutes: string[]
  hours: string[]
  days?: string[]
}

export interface IntervalsResponse {
  status: 'success' | 'error'
  message?: string
  data?: IntervalsData
}

export interface OIPoint {
  time: number
  value: number
}

export interface MultiStrikeOILeg {
  symbol: string
  exchange: string
  side: 'BUY' | 'SELL'
  strike?: number
  option_type?: 'CE' | 'PE'
  expiry?: string
  has_oi: boolean
  series: OIPoint[]
}

export interface MultiStrikeOIData {
  underlying: string
  underlying_ltp: number
  interval: string
  underlying_available: boolean
  underlying_series: OIPoint[]
  legs: MultiStrikeOILeg[]
}

export interface MultiStrikeOIResponse {
  status: 'success' | 'error'
  message?: string
  data?: MultiStrikeOIData
}

// Let 4xx responses resolve instead of throw — the backend returns structured
// `{status: "error", message: "..."}` bodies for user-fixable states (empty
// history window, missing OI, etc). Throwing swallows those and the toast
// falls back to a generic message.
const allow4xx = { validateStatus: (s: number) => s < 500 }

export const strategyChartApi = {
  getStrategyChart: async (params: StrategyChartRequest): Promise<StrategyChartResponse> => {
    const response = await webClient.post<StrategyChartResponse>(
      '/strategybuilder/api/strategy-chart',
      params,
      allow4xx
    )
    return response.data
  },

  getMultiStrikeOI: async (params: StrategyChartRequest): Promise<MultiStrikeOIResponse> => {
    const response = await webClient.post<MultiStrikeOIResponse>(
      '/strategybuilder/api/multi-strike-oi',
      params,
      allow4xx
    )
    return response.data
  },

  getIntervals: async (): Promise<IntervalsResponse> => {
    const response = await webClient.get<IntervalsResponse>(
      '/strategybuilder/api/intervals',
      allow4xx
    )
    return response.data
  },
}

```


---

# FILE: frontend\src\api\strategy-portfolio.ts

```ts
import { webClient } from './client'

export type Watchlist = 'mytrades' | 'simulation'

/** Leg payload — kept loose since backend stores it as a JSON blob. */
export interface PortfolioLeg {
  id?: string
  segment: 'OPTION' | 'FUTURE'
  side: 'BUY' | 'SELL'
  lots: number
  lotSize: number
  expiry: string
  strike?: number
  optionType?: 'CE' | 'PE'
  price: number
  iv?: number
  active?: boolean
  symbol: string
  exitPrice?: number
}

export interface PortfolioEntry {
  id: number
  watchlist: Watchlist
  name: string
  underlying: string
  exchange: string
  expiry: string | null
  legs: PortfolioLeg[]
  notes: string | null
  created_at: string | null
  updated_at: string | null
}

export interface PortfolioSavePayload {
  name: string
  watchlist: Watchlist
  underlying: string
  exchange: string
  expiry?: string | null
  legs: PortfolioLeg[]
  notes?: string | null
}

interface ListResponse {
  status: 'success' | 'error'
  items?: PortfolioEntry[]
  message?: string
}

interface ItemResponse {
  status: 'success' | 'error'
  item?: PortfolioEntry
  message?: string
}

interface StatusResponse {
  status: 'success' | 'error'
  message?: string
}

export const strategyPortfolioApi = {
  list: async (watchlist?: Watchlist): Promise<PortfolioEntry[]> => {
    const url = watchlist
      ? `/api/strategy-portfolio?watchlist=${watchlist}`
      : '/api/strategy-portfolio'
    const res = await webClient.get<ListResponse>(url)
    if (res.data.status !== 'success' || !res.data.items) {
      throw new Error(res.data.message || 'Failed to list portfolio')
    }
    return res.data.items
  },

  get: async (id: number): Promise<PortfolioEntry> => {
    const res = await webClient.get<ItemResponse>(`/api/strategy-portfolio/${id}`)
    if (res.data.status !== 'success' || !res.data.item) {
      throw new Error(res.data.message || 'Not found')
    }
    return res.data.item
  },

  create: async (payload: PortfolioSavePayload): Promise<PortfolioEntry> => {
    const res = await webClient.post<ItemResponse>('/api/strategy-portfolio', payload)
    if (res.data.status !== 'success' || !res.data.item) {
      throw new Error(res.data.message || 'Save failed')
    }
    return res.data.item
  },

  update: async (id: number, payload: PortfolioSavePayload): Promise<PortfolioEntry> => {
    const res = await webClient.put<ItemResponse>(`/api/strategy-portfolio/${id}`, payload)
    if (res.data.status !== 'success' || !res.data.item) {
      throw new Error(res.data.message || 'Update failed')
    }
    return res.data.item
  },

  remove: async (id: number): Promise<void> => {
    const res = await webClient.delete<StatusResponse>(`/api/strategy-portfolio/${id}`)
    if (res.data.status !== 'success') {
      throw new Error(res.data.message || 'Delete failed')
    }
  },
}

```


---

# FILE: frontend\src\api\strategy.ts

```ts
import type {
  AddSymbolRequest,
  CreateStrategyRequest,
  Strategy,
  StrategySymbolMapping,
  SymbolSearchResult,
} from '@/types/strategy'
import type { ApiResponse } from '@/types/trading'
import { webClient } from './client'

export const strategyApi = {
  /**
   * Get all strategies
   */
  getStrategies: async (): Promise<Strategy[]> => {
    const response = await webClient.get<{ strategies: Strategy[] }>('/strategy/api/strategies')
    return response.data.strategies || []
  },

  /**
   * Get a single strategy by ID
   */
  getStrategy: async (
    strategyId: number
  ): Promise<{ strategy: Strategy; mappings: StrategySymbolMapping[] }> => {
    const response = await webClient.get<{ strategy: Strategy; mappings: StrategySymbolMapping[] }>(
      `/strategy/api/strategy/${strategyId}`
    )
    return response.data
  },

  /**
   * Create a new strategy
   */
  createStrategy: async (
    data: CreateStrategyRequest
  ): Promise<ApiResponse<{ strategy_id: number }>> => {
    const response = await webClient.post<ApiResponse<{ strategy_id: number }>>(
      '/strategy/api/strategy',
      data
    )
    return response.data
  },

  /**
   * Toggle strategy active/inactive
   */
  toggleStrategy: async (strategyId: number): Promise<ApiResponse<{ is_active: boolean }>> => {
    const response = await webClient.post<ApiResponse<{ is_active: boolean }>>(
      `/strategy/api/strategy/${strategyId}/toggle`
    )
    return response.data
  },

  /**
   * Delete a strategy
   */
  deleteStrategy: async (strategyId: number): Promise<ApiResponse<void>> => {
    const response = await webClient.post<ApiResponse<void>>(`/strategy/${strategyId}/delete`)
    return response.data
  },

  /**
   * Add a symbol mapping to a strategy
   */
  addSymbolMapping: async (
    strategyId: number,
    data: AddSymbolRequest
  ): Promise<ApiResponse<void>> => {
    const response = await webClient.post<ApiResponse<void>>(
      `/strategy/${strategyId}/configure`,
      data
    )
    return response.data
  },

  /**
   * Add bulk symbol mappings
   */
  addBulkSymbols: async (
    strategyId: number,
    csvData: string
  ): Promise<ApiResponse<{ added: number; failed: number }>> => {
    const response = await webClient.post<ApiResponse<{ added: number; failed: number }>>(
      `/strategy/${strategyId}/configure`,
      { symbols: csvData } // Backend expects 'symbols' field
    )
    return response.data
  },

  /**
   * Delete a symbol mapping
   */
  deleteSymbolMapping: async (
    strategyId: number,
    mappingId: number
  ): Promise<ApiResponse<void>> => {
    const response = await webClient.post<ApiResponse<void>>(
      `/strategy/${strategyId}/symbol/${mappingId}/delete`
    )
    return response.data
  },

  /**
   * Search symbols
   */
  searchSymbols: async (query: string, exchange?: string): Promise<SymbolSearchResult[]> => {
    const params = new URLSearchParams({ q: query })
    if (exchange) {
      params.append('exchange', exchange)
    }
    const response = await webClient.get<{ results: SymbolSearchResult[] }>(
      `/strategy/search?${params.toString()}`
    )
    return response.data.results || []
  },

  /**
   * Get webhook URL for a strategy
   */
  getWebhookUrl: (webhookId: string): string => {
    const baseUrl = window.location.origin
    return `${baseUrl}/strategy/webhook/${webhookId}`
  },
}

```


---

# FILE: frontend\src\api\telegram.ts

```ts
import type {
  BroadcastRequest,
  BroadcastResponse,
  CommandStats,
  TelegramAnalytics,
  TelegramBotStatus,
  TelegramConfig,
  TelegramUser,
  UpdateConfigRequest,
} from '@/types/telegram'
import { webClient } from './client'

interface ApiResponse<T = void> {
  status: string
  message?: string
  data?: T
}

export const telegramApi = {
  // ============================================================================
  // Bot Status & Control
  // ============================================================================

  /**
   * Get bot status
   */
  getBotStatus: async (): Promise<TelegramBotStatus> => {
    const response = await webClient.get<ApiResponse<TelegramBotStatus>>('/telegram/bot/status')
    return response.data.data!
  },

  /**
   * Start the bot
   */
  startBot: async (): Promise<ApiResponse> => {
    const response = await webClient.post<ApiResponse>('/telegram/bot/start')
    return response.data
  },

  /**
   * Stop the bot
   */
  stopBot: async (): Promise<ApiResponse> => {
    const response = await webClient.post<ApiResponse>('/telegram/bot/stop')
    return response.data
  },

  // ============================================================================
  // Configuration
  // ============================================================================

  /**
   * Get bot configuration
   */
  getConfig: async (): Promise<TelegramConfig> => {
    const response = await webClient.get<ApiResponse<TelegramConfig>>('/telegram/api/config')
    return response.data.data!
  },

  /**
   * Update bot configuration
   */
  updateConfig: async (data: UpdateConfigRequest): Promise<ApiResponse> => {
    const response = await webClient.post<ApiResponse>('/telegram/config', data)
    return response.data
  },

  // ============================================================================
  // Users
  // ============================================================================

  /**
   * Get all telegram users
   */
  getUsers: async (): Promise<{ users: TelegramUser[]; stats: CommandStats[] }> => {
    const response =
      await webClient.get<ApiResponse<{ users: TelegramUser[]; stats: CommandStats[] }>>(
        '/telegram/api/users'
      )
    return response.data.data!
  },

  /**
   * Unlink a telegram user
   */
  unlinkUser: async (telegramId: number): Promise<ApiResponse> => {
    const response = await webClient.post<ApiResponse>(`/telegram/user/${telegramId}/unlink`)
    return response.data
  },

  // ============================================================================
  // Analytics
  // ============================================================================

  /**
   * Get analytics data
   */
  getAnalytics: async (): Promise<TelegramAnalytics> => {
    const response = await webClient.get<ApiResponse<TelegramAnalytics>>('/telegram/api/analytics')
    return response.data.data!
  },

  // ============================================================================
  // Messaging
  // ============================================================================

  /**
   * Send test message
   */
  sendTestMessage: async (): Promise<ApiResponse> => {
    const response = await webClient.post<ApiResponse>('/telegram/test-message')
    return response.data
  },

  /**
   * Send broadcast message
   */
  sendBroadcast: async (data: BroadcastRequest): Promise<ApiResponse<BroadcastResponse>> => {
    const response = await webClient.post<ApiResponse<BroadcastResponse>>(
      '/telegram/broadcast',
      data
    )
    return response.data
  },

  /**
   * Send message to specific user
   */
  sendMessage: async (telegramId: number, message: string): Promise<ApiResponse> => {
    const response = await webClient.post<ApiResponse>('/telegram/send-message', {
      telegram_id: telegramId,
      message,
    })
    return response.data
  },
}

```


---

# FILE: frontend\src\api\trading.ts

```ts
import type {
  ApiResponse,
  GttOrder,
  Holding,
  MarginData,
  Order,
  OrderStats,
  PlaceOrderRequest,
  PortfolioStats,
  Position,
  Trade,
} from '@/types/trading'
import { apiClient, webClient } from './client'

export interface QuotesData {
  ask: number
  bid: number
  high: number
  low: number
  ltp: number
  oi: number
  open: number
  prev_close: number
  volume: number
}

export interface DepthLevel {
  price: number
  quantity: number
}

export interface DepthData {
  asks: DepthLevel[]
  bids: DepthLevel[]
  high: number
  low: number
  ltp: number
  ltq: number
  oi: number
  open: number
  prev_close: number
  totalbuyqty: number
  totalsellqty: number
  volume: number
}

export interface MultiQuotesSymbol {
  symbol: string
  exchange: string
}

export interface MultiQuotesResult {
  symbol: string
  exchange: string
  data: QuotesData
}

// MultiQuotes API has a different response structure (results at root, not in data)
export interface MultiQuotesApiResponse {
  status: 'success' | 'error'
  results?: MultiQuotesResult[]
  message?: string
}

export interface BasketOrderItem {
  symbol: string
  exchange: string
  action: 'BUY' | 'SELL'
  quantity: number
  pricetype: 'MARKET' | 'LIMIT' | 'SL' | 'SL-M'
  product: 'CNC' | 'NRML' | 'MIS'
  price?: number
  trigger_price?: number
  disclosed_quantity?: number
}

export interface BasketOrderResult {
  symbol: string
  status: 'success' | 'error'
  orderid?: string
  message?: string
}

export interface BasketOrderResponse {
  status: 'success' | 'error'
  message?: string
  results?: BasketOrderResult[]
  mode?: 'live' | 'analyze'
}

export const tradingApi = {
  /**
   * Get real-time quotes for a symbol
   */
  getQuotes: async (
    apiKey: string,
    symbol: string,
    exchange: string
  ): Promise<ApiResponse<QuotesData>> => {
    const response = await apiClient.post<ApiResponse<QuotesData>>('/quotes', {
      apikey: apiKey,
      symbol,
      exchange,
    })
    return response.data
  },

  /**
   * Get real-time quotes for multiple symbols
   */
  getMultiQuotes: async (
    apiKey: string,
    symbols: MultiQuotesSymbol[]
  ): Promise<MultiQuotesApiResponse> => {
    const response = await apiClient.post<MultiQuotesApiResponse>('/multiquotes', {
      apikey: apiKey,
      symbols,
    })
    return response.data
  },

  /**
   * Get market depth for a symbol (5-level order book)
   */
  getDepth: async (
    apiKey: string,
    symbol: string,
    exchange: string
  ): Promise<ApiResponse<DepthData>> => {
    const response = await apiClient.post<ApiResponse<DepthData>>('/depth', {
      apikey: apiKey,
      symbol,
      exchange,
    })
    return response.data
  },

  /**
   * Get margin/funds data
   */
  getFunds: async (apiKey: string): Promise<ApiResponse<MarginData>> => {
    const response = await apiClient.post<ApiResponse<MarginData>>('/funds', {
      apikey: apiKey,
    })
    return response.data
  },

  /**
   * Get positions
   */
  getPositions: async (apiKey: string): Promise<ApiResponse<Position[]>> => {
    const response = await apiClient.post<ApiResponse<Position[]>>('/positionbook', {
      apikey: apiKey,
    })
    return response.data
  },

  /**
   * Get order book
   */
  getOrders: async (
    apiKey: string
  ): Promise<ApiResponse<{ orders: Order[]; statistics: OrderStats }>> => {
    const response = await apiClient.post<ApiResponse<{ orders: Order[]; statistics: OrderStats }>>(
      '/orderbook',
      {
        apikey: apiKey,
      }
    )
    return response.data
  },

  /**
   * Get trade book
   */
  getTrades: async (apiKey: string): Promise<ApiResponse<Trade[]>> => {
    const response = await apiClient.post<ApiResponse<Trade[]>>('/tradebook', {
      apikey: apiKey,
    })
    return response.data
  },

  /**
   * Get holdings
   */
  getHoldings: async (
    apiKey: string
  ): Promise<ApiResponse<{ holdings: Holding[]; statistics: PortfolioStats }>> => {
    const response = await apiClient.post<
      ApiResponse<{ holdings: Holding[]; statistics: PortfolioStats }>
    >('/holdings', {
      apikey: apiKey,
    })
    return response.data
  },

  /**
   * Place order
   */
  placeOrder: async (order: PlaceOrderRequest): Promise<ApiResponse<{ orderid: string }>> => {
    const response = await apiClient.post<ApiResponse<{ orderid: string }>>('/placeorder', order)
    return response.data
  },

  /**
   * Place a basket of orders in one call. Each item is independent — the
   * backend returns a per-order `results[]` so partial success is possible.
   */
  placeBasketOrder: async (
    apiKey: string,
    strategy: string,
    orders: BasketOrderItem[]
  ): Promise<BasketOrderResponse> => {
    const response = await apiClient.post<BasketOrderResponse>('/basketorder', {
      apikey: apiKey,
      strategy,
      orders,
    })
    return response.data
  },

  /**
   * Modify order (uses session auth with CSRF)
   */
  modifyOrder: async (
    orderid: string,
    orderData: {
      symbol: string
      exchange: string
      action: string
      product: string
      pricetype: string
      quantity: number
      price?: number
      trigger_price?: number
      disclosed_quantity?: number
    }
  ): Promise<ApiResponse<{ orderid: string }>> => {
    const response = await webClient.post<ApiResponse<{ orderid: string }>>('/modify_order', {
      orderid,
      ...orderData,
    })
    return response.data
  },

  /**
   * Cancel order (uses session auth with CSRF)
   */
  cancelOrder: async (orderid: string): Promise<ApiResponse<{ orderid: string }>> => {
    const response = await webClient.post<ApiResponse<{ orderid: string }>>('/cancel_order', {
      orderid,
    })
    return response.data
  },

  /**
   * Close a specific position (uses session auth with CSRF)
   */
  closePosition: async (
    symbol: string,
    exchange: string,
    product: string
  ): Promise<ApiResponse<void>> => {
    // Uses the web route which handles session-based auth with CSRF
    const response = await webClient.post<ApiResponse<void>>('/close_position', {
      symbol,
      exchange,
      product,
    })
    return response.data
  },

  /**
   * Close all positions (uses session auth with CSRF)
   */
  closeAllPositions: async (): Promise<ApiResponse<void>> => {
    const response = await webClient.post<ApiResponse<void>>('/close_all_positions', {})
    return response.data
  },

  /**
   * Cancel all orders (uses session auth with CSRF)
   */
  cancelAllOrders: async (): Promise<ApiResponse<void>> => {
    const response = await webClient.post<ApiResponse<void>>('/cancel_all_orders', {})
    return response.data
  },

  /**
   * Get the GTT (Good Till Triggered) order book — active triggers + recent history.
   */
  getGttOrderbook: async (apiKey: string): Promise<ApiResponse<GttOrder[]>> => {
    const response = await apiClient.post<ApiResponse<GttOrder[]>>('/gttorderbook', {
      apikey: apiKey,
    })
    return response.data
  },

  /**
   * Cancel an active GTT trigger (uses session auth with CSRF).
   */
  cancelGttOrder: async (triggerId: string): Promise<ApiResponse<{ trigger_id: string }>> => {
    const response = await webClient.post<ApiResponse<{ trigger_id: string }>>(
      '/cancel_gtt_order',
      { trigger_id: triggerId }
    )
    return response.data
  },

  /**
   * Modify an active GTT trigger (uses session auth with CSRF).
   * Flat replacement body — same shape as PlaceGTTOrder plus trigger_id.
   * last_price is fetched server-side from the broker's quotes endpoint.
   */
  modifyGttOrder: async (
    triggerId: string,
    payload: {
      symbol: string
      exchange: string
      trigger_type: 'SINGLE' | 'OCO'
      action: 'BUY' | 'SELL' | string
      product: string
      quantity: number
      pricetype: string
      price: number
      triggerprice_sl: number
      triggerprice_tg: number
      stoploss?: number | null
      target?: number | null
      strategy?: string
    }
  ): Promise<ApiResponse<{ trigger_id: string }>> => {
    const response = await webClient.post<ApiResponse<{ trigger_id: string }>>(
      '/modify_gtt_order',
      { trigger_id: triggerId, ...payload }
    )
    return response.data
  },
}

```


---

# FILE: frontend\src\api\vol-surface.ts

```ts
import { webClient } from './client'

export interface VolSurfaceExpiry {
  date: string
  dte: number
}

export interface VolSurfaceData {
  underlying: string
  underlying_ltp: number
  atm_strike: number
  strikes: number[]
  expiries: VolSurfaceExpiry[]
  surface: (number | null)[][]
}

export interface VolSurfaceResponse {
  status: 'success' | 'error'
  message?: string
  data?: VolSurfaceData
}

export const volSurfaceApi = {
  getSurfaceData: async (params: {
    underlying: string
    exchange: string
    expiry_dates: string[]
    strike_count?: number
  }): Promise<VolSurfaceResponse> => {
    const response = await webClient.post<VolSurfaceResponse>(
      '/volsurface/api/surface-data',
      params
    )
    return response.data
  },
}

```


---

# FILE: frontend\src\api\whatsapp.ts

```ts
// WhatsApp API client — talks to the session-authed blueprint at /whatsapp/...
// (Public REST namespace /api/v1/whatsapp is send-only and used by external
// scripts / SDKs, not by this frontend.)

import type {
  WhatsAppBotStatus,
  WhatsAppBroadcastRequest,
  WhatsAppCommandStats,
  WhatsAppConfigBundle,
  WhatsAppPairState,
  WhatsAppSendToPhoneRequest,
  WhatsAppUpdateConfigRequest,
  WhatsAppUser,
} from '@/types/whatsapp'
import { webClient } from './client'

interface ApiResponse<T = void> {
  status: string
  message?: string
  data?: T
}

export const whatsappApi = {
  // ----- bundled status (single call for the index page) -----

  getConfig: async (): Promise<WhatsAppConfigBundle> => {
    const r = await webClient.get<ApiResponse<WhatsAppConfigBundle>>('/whatsapp/config')
    return r.data.data!
  },

  updateConfig: async (payload: WhatsAppUpdateConfigRequest): Promise<ApiResponse> => {
    const r = await webClient.post<ApiResponse>('/whatsapp/config', payload)
    return r.data
  },

  getStatus: async (): Promise<WhatsAppBotStatus> => {
    const r = await webClient.get<ApiResponse<WhatsAppBotStatus>>('/whatsapp/bot/status')
    return r.data.data!
  },

  // ----- pairing -----

  startPair: async (phone?: string): Promise<ApiResponse<WhatsAppPairState>> => {
    const r = await webClient.post<ApiResponse<WhatsAppPairState>>('/whatsapp/pair', {
      phone: phone ?? '',
    })
    return r.data
  },

  pollPairStatus: async (): Promise<WhatsAppPairState> => {
    const r = await webClient.get<ApiResponse<WhatsAppPairState>>('/whatsapp/pair/status')
    return r.data.data!
  },

  unlinkDevice: async (): Promise<ApiResponse> => {
    const r = await webClient.post<ApiResponse>('/whatsapp/unlink')
    return r.data
  },

  // ----- bot lifecycle -----

  startBot: async (): Promise<ApiResponse> => {
    const r = await webClient.post<ApiResponse>('/whatsapp/bot/start')
    return r.data
  },

  stopBot: async (): Promise<ApiResponse> => {
    const r = await webClient.post<ApiResponse>('/whatsapp/bot/stop')
    return r.data
  },

  // ----- linked users -----

  listUsers: async (): Promise<WhatsAppUser[]> => {
    const r = await webClient.get<ApiResponse<WhatsAppUser[]>>('/whatsapp/users')
    return r.data.data ?? []
  },

  unlinkUser: async (whatsappJid: string): Promise<ApiResponse> => {
    const encoded = encodeURIComponent(whatsappJid)
    const r = await webClient.post<ApiResponse>(`/whatsapp/user/${encoded}/unlink`)
    return r.data
  },

  // ----- send -----

  broadcast: async (
    payload: WhatsAppBroadcastRequest
  ): Promise<{ queued: number; skipped: number }> => {
    const r = await webClient.post<ApiResponse<{ queued: number; skipped: number }>>(
      '/whatsapp/broadcast',
      payload
    )
    return { queued: r.data.data?.queued ?? 0, skipped: r.data.data?.skipped ?? 0 }
  },

  sendToPhone: async (payload: WhatsAppSendToPhoneRequest): Promise<ApiResponse> => {
    const r = await webClient.post<ApiResponse>('/whatsapp/send', payload)
    return r.data
  },

  testMessage: async (): Promise<ApiResponse> => {
    const r = await webClient.post<ApiResponse>('/whatsapp/test-message')
    return r.data
  },

  // ----- stats -----

  getStats: async (days = 7): Promise<WhatsAppCommandStats> => {
    const r = await webClient.get<ApiResponse<WhatsAppCommandStats>>(`/whatsapp/stats?days=${days}`)
    return r.data.data!
  },
}

```
