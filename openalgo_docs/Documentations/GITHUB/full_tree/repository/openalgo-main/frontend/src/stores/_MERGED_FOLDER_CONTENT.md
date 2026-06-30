# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\frontend\src\stores



---

# FILE: frontend\src\stores\alertStore.ts

```ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type ToastPosition =
  | 'top-right'
  | 'top-center'
  | 'top-left'
  | 'bottom-right'
  | 'bottom-center'
  | 'bottom-left'

export interface AlertCategories {
  // Real-time Socket.IO events (High-frequency)
  orders: boolean // Order placement notifications (BUY/SELL) - Socket: order_event, order_notification
  analyzer: boolean // Analyzer/sandbox mode operations - Socket: analyzer_update
  system: boolean // Password change, master contract download - Socket: password_change, master_contract_download
  actionCenter: boolean // Pending order notifications - Socket: pending_order_created

  // User-initiated operations (Tier 1 - High Impact)
  historify: boolean // Historify job operations, file uploads, schedules (67 toasts)
  strategy: boolean // Strategy management, symbol configuration (39 toasts)
  positions: boolean // Position close/update operations

  // User-initiated operations (Tier 2 - Medium Impact)
  chartink: boolean // Chartink strategy operations (26 toasts)
  pythonStrategy: boolean // Python strategy operations (34 toasts)
  telegram: boolean // Telegram bot operations (19 toasts)
  whatsapp: boolean // WhatsApp bot operations
  flow: boolean // Workflow management (15 toasts)

  // User-initiated operations (Tier 3 - Low Impact)
  admin: boolean // Admin panel operations (27 toasts)
  monitoring: boolean // Health, latency, security dashboards (10 toasts)
  clipboard: boolean // Copy to clipboard feedback (11 toasts)
}

interface AlertStore {
  // Master controls
  toastsEnabled: boolean
  soundEnabled: boolean

  // Toast display settings
  position: ToastPosition
  maxVisibleToasts: number
  duration: number // in milliseconds

  // Category toggles
  categories: AlertCategories

  // Actions
  setToastsEnabled: (enabled: boolean) => void
  setSoundEnabled: (enabled: boolean) => void
  setPosition: (position: ToastPosition) => void
  setMaxVisibleToasts: (max: number) => void
  setDuration: (duration: number) => void
  setCategoryEnabled: (category: keyof AlertCategories, enabled: boolean) => void
  resetToDefaults: () => void

  // Helper to check if a category toast should be shown
  shouldShowToast: (category?: keyof AlertCategories) => boolean
  shouldPlaySound: () => boolean
}

const DEFAULT_STATE = {
  toastsEnabled: true,
  soundEnabled: true,
  position: 'top-right' as ToastPosition,
  maxVisibleToasts: 3,
  duration: 3000, // 3 seconds
  categories: {
    // Real-time (Socket.IO)
    orders: true,
    analyzer: true,
    system: true,
    actionCenter: true,
    // Tier 1
    historify: true,
    strategy: true,
    positions: true,
    // Tier 2
    chartink: true,
    pythonStrategy: true,
    telegram: true,
    whatsapp: true,
    flow: true,
    // Tier 3
    admin: true,
    monitoring: true,
    clipboard: true,
  },
}

export const useAlertStore = create<AlertStore>()(
  persist(
    (set, get) => ({
      ...DEFAULT_STATE,

      setToastsEnabled: (enabled) => set({ toastsEnabled: enabled }),

      setSoundEnabled: (enabled) => set({ soundEnabled: enabled }),

      setPosition: (position) => set({ position }),

      setMaxVisibleToasts: (max) => set({ maxVisibleToasts: Math.min(Math.max(max, 1), 10) }),

      setDuration: (duration) => set({ duration: Math.min(Math.max(duration, 1000), 15000) }),

      setCategoryEnabled: (category, enabled) =>
        set((state) => ({
          categories: {
            ...state.categories,
            [category]: enabled,
          },
        })),

      resetToDefaults: () => set(DEFAULT_STATE),

      shouldShowToast: (category) => {
        const state = get()
        if (!state.toastsEnabled) return false
        if (category && !state.categories[category]) return false
        return true
      },

      shouldPlaySound: () => {
        const state = get()
        return state.toastsEnabled && state.soundEnabled
      },
    }),
    {
      name: 'openalgo-alerts',
      partialize: (state) => ({
        toastsEnabled: state.toastsEnabled,
        soundEnabled: state.soundEnabled,
        position: state.position,
        maxVisibleToasts: state.maxVisibleToasts,
        duration: state.duration,
        categories: state.categories,
      }),
    }
  )
)

```


---

# FILE: frontend\src\stores\authStore.ts

```ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { useBrokerStore } from './brokerStore'

interface User {
  username: string
  broker: string | null
  isLoggedIn: boolean
  loginTime: string | null
}

interface AuthStore {
  user: User | null
  apiKey: string | null
  isAuthenticated: boolean

  setUser: (user: User) => void
  setApiKey: (apiKey: string | null) => void
  login: (username: string, broker: string) => void
  logout: () => void
  checkSession: () => boolean
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: null,
      apiKey: null,
      isAuthenticated: false,

      setUser: (user) => set({ user, isAuthenticated: user.isLoggedIn }),

      setApiKey: (apiKey) => set({ apiKey }),

      login: (username, broker) => {
        const user: User = {
          username,
          broker,
          isLoggedIn: true,
          loginTime: new Date().toISOString(),
        }
        set({ user, isAuthenticated: true })
      },

      logout: () => {
        set({ user: null, isAuthenticated: false, apiKey: null })
      },

      checkSession: () => {
        const { user } = get()
        if (!user || !user.loginTime) return false

        // Skip session expiry for crypto brokers (24/7 markets)
        const capabilities = useBrokerStore.getState().capabilities
        if (capabilities?.broker_type === 'crypto') {
          return true
        }

        // Session expiry check (3 AM IST daily)
        const now = new Date()
        const loginTime = new Date(user.loginTime)

        // Convert to IST properly: UTC + 5.5 hours
        // First get UTC time, then add IST offset
        const istOffsetMs = 5.5 * 60 * 60 * 1000
        const localOffsetMs = now.getTimezoneOffset() * 60 * 1000

        // Convert current time to IST
        const nowUTC = now.getTime() + localOffsetMs
        const nowIST = new Date(nowUTC + istOffsetMs)

        // Convert login time to IST
        const loginUTC = loginTime.getTime() + localOffsetMs
        const loginIST = new Date(loginUTC + istOffsetMs)

        // Create today's 3 AM IST expiry time
        const todayExpiry = new Date(nowIST)
        todayExpiry.setHours(3, 0, 0, 0)

        // If current time is after 3 AM IST today and login was before 3 AM IST today
        if (nowIST > todayExpiry && loginIST < todayExpiry) {
          get().logout()
          return false
        }

        return true
      },
    }),
    {
      name: 'openalgo-auth',
    }
  )
)

```


---

# FILE: frontend\src\stores\brokerStore.ts

```ts
import { create } from 'zustand'

interface BrokerCapabilities {
  broker_name: string
  broker_type: 'IN_stock' | 'crypto'
  supported_exchanges: string[]
  leverage_config: boolean
}

interface BrokerStore {
  capabilities: BrokerCapabilities | null
  isLoaded: boolean

  fetchCapabilities: () => Promise<void>
  clearCapabilities: () => void
}

export const useBrokerStore = create<BrokerStore>()((set) => ({
  capabilities: null,
  isLoaded: false,

  fetchCapabilities: async () => {
    try {
      const response = await fetch('/api/broker/capabilities', {
        credentials: 'include',
      })

      if (response.ok) {
        const data = await response.json()
        if (data.status === 'success' && data.data) {
          set({ capabilities: data.data, isLoaded: true })
        }
      }
    } catch {
      // Silently fail — capabilities will be null, pages fall back to showing all exchanges
    }
  },

  clearCapabilities: () => set({ capabilities: null, isLoaded: false }),
}))

```


---

# FILE: frontend\src\stores\flowWorkflowStore.ts

```ts
// stores/flowWorkflowStore.ts
// Zustand store for Flow workflow editor state

import type { Edge, Node, OnConnect, OnEdgesChange, OnNodesChange } from '@xyflow/react'
import { addEdge, applyEdgeChanges, applyNodeChanges } from '@xyflow/react'
import { create } from 'zustand'

interface WorkflowState {
  // Workflow data
  id: number | null
  name: string
  description: string
  nodes: Node[]
  edges: Edge[]

  // Selection state
  selectedNodeId: string | null
  selectedEdgeId: string | null

  // Edit tracking
  isModified: boolean

  // Actions - Workflow
  setWorkflow: (workflow: {
    id: number | null
    name: string
    description: string
    nodes: Node[]
    edges: Edge[]
  }) => void
  setName: (name: string) => void
  setDescription: (description: string) => void
  resetWorkflow: () => void
  markSaved: () => void

  // Actions - Nodes
  setNodes: (nodes: Node[]) => void
  onNodesChange: OnNodesChange
  addNode: (node: Node) => void
  updateNodeData: (nodeId: string, data: Record<string, unknown>) => void
  deleteNode: (nodeId: string) => void

  // Actions - Edges
  setEdges: (edges: Edge[]) => void
  onEdgesChange: OnEdgesChange
  onConnect: OnConnect
  deleteEdge: (edgeId: string) => void

  // Actions - Selection
  selectNode: (nodeId: string | null) => void
  selectEdge: (edgeId: string | null) => void
  deleteSelected: () => void
}

const initialState = {
  id: null,
  name: 'Untitled Workflow',
  description: '',
  nodes: [],
  edges: [],
  selectedNodeId: null,
  selectedEdgeId: null,
  isModified: false,
}

export const useFlowWorkflowStore = create<WorkflowState>((set, get) => ({
  ...initialState,

  // =============================================================================
  // Workflow Actions
  // =============================================================================

  setWorkflow: (workflow) =>
    set({
      id: workflow.id,
      name: workflow.name,
      description: workflow.description,
      nodes: workflow.nodes,
      edges: workflow.edges,
      isModified: false,
      selectedNodeId: null,
      selectedEdgeId: null,
    }),

  setName: (name) => set({ name, isModified: true }),

  setDescription: (description) => set({ description, isModified: true }),

  resetWorkflow: () => set(initialState),

  markSaved: () => set({ isModified: false }),

  // =============================================================================
  // Node Actions
  // =============================================================================

  setNodes: (nodes) => set({ nodes, isModified: true }),

  onNodesChange: (changes) => {
    set({
      nodes: applyNodeChanges(changes, get().nodes),
      isModified: true,
    })
  },

  addNode: (node) =>
    set((state) => ({
      nodes: [...state.nodes, node],
      isModified: true,
    })),

  updateNodeData: (nodeId, data) =>
    set((state) => ({
      nodes: state.nodes.map((node) =>
        node.id === nodeId ? { ...node, data: { ...node.data, ...data } } : node
      ),
      isModified: true,
    })),

  deleteNode: (nodeId) =>
    set((state) => ({
      nodes: state.nodes.filter((node) => node.id !== nodeId),
      edges: state.edges.filter((edge) => edge.source !== nodeId && edge.target !== nodeId),
      selectedNodeId: state.selectedNodeId === nodeId ? null : state.selectedNodeId,
      isModified: true,
    })),

  // =============================================================================
  // Edge Actions
  // =============================================================================

  setEdges: (edges) => set({ edges, isModified: true }),

  onEdgesChange: (changes) => {
    set({
      edges: applyEdgeChanges(changes, get().edges),
      isModified: true,
    })
  },

  onConnect: (connection) => {
    set({
      edges: addEdge(
        {
          ...connection,
          id: `edge-${Date.now()}`,
          type: 'insertable',
          animated: true,
        },
        get().edges
      ),
      isModified: true,
    })
  },

  deleteEdge: (edgeId) =>
    set((state) => ({
      edges: state.edges.filter((edge) => edge.id !== edgeId),
      selectedEdgeId: state.selectedEdgeId === edgeId ? null : state.selectedEdgeId,
      isModified: true,
    })),

  // =============================================================================
  // Selection Actions
  // =============================================================================

  selectNode: (nodeId) => set({ selectedNodeId: nodeId, selectedEdgeId: null }),

  selectEdge: (edgeId) => set({ selectedEdgeId: edgeId, selectedNodeId: null }),

  deleteSelected: () =>
    set((state) => {
      const { selectedNodeId, selectedEdgeId, nodes, edges } = state

      if (selectedNodeId) {
        return {
          nodes: nodes.filter((node) => node.id !== selectedNodeId),
          edges: edges.filter(
            (edge) => edge.source !== selectedNodeId && edge.target !== selectedNodeId
          ),
          selectedNodeId: null,
          isModified: true,
        }
      }

      if (selectedEdgeId) {
        return {
          edges: edges.filter((edge) => edge.id !== selectedEdgeId),
          selectedEdgeId: null,
          isModified: true,
        }
      }

      return state
    }),
}))

```


---

# FILE: frontend\src\stores\sessionStore.ts

```ts
import { create } from 'zustand'

interface SessionStore {
  activeSessionCount: number
  setActiveSessionCount: (count: number) => void
}

export const useSessionStore = create<SessionStore>((set) => ({
  activeSessionCount: 0,
  setActiveSessionCount: (count) => set({ activeSessionCount: count }),
}))

```


---

# FILE: frontend\src\stores\themeStore.ts

```ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type ThemeMode = 'light' | 'dark'
export type AppMode = 'live' | 'analyzer'
export type ThemeColor =
  | 'zinc'
  | 'slate'
  | 'stone'
  | 'gray'
  | 'neutral'
  | 'red'
  | 'rose'
  | 'orange'
  | 'green'
  | 'blue'
  | 'yellow'
  | 'violet'

// Event emitter for mode changes
type ModeChangeCallback = (newMode: AppMode) => void
const modeChangeListeners: Set<ModeChangeCallback> = new Set()

export const onModeChange = (callback: ModeChangeCallback): (() => void) => {
  modeChangeListeners.add(callback)
  return () => {
    modeChangeListeners.delete(callback)
  }
}

const notifyModeChange = (newMode: AppMode) => {
  modeChangeListeners.forEach((cb) => cb(newMode))
}

interface ThemeStore {
  mode: ThemeMode
  color: ThemeColor
  appMode: AppMode
  isTogglingMode: boolean

  setMode: (mode: ThemeMode) => void
  setColor: (color: ThemeColor) => void
  setAppMode: (appMode: AppMode) => void
  toggleMode: () => void
  toggleAppMode: () => Promise<{ success: boolean; message?: string }>
  syncAppMode: () => Promise<void>
}

export const useThemeStore = create<ThemeStore>()(
  persist(
    (set, get) => ({
      mode: 'light',
      color: 'zinc',
      appMode: 'live',
      isTogglingMode: false,

      setMode: (mode) => {
        // Only allow theme change in live mode
        if (get().appMode !== 'live') return

        set({ mode })
        if (typeof document !== 'undefined') {
          document.documentElement.classList.toggle('dark', mode === 'dark')
        }
      },

      setColor: (color) => {
        // Only allow color change in live mode
        if (get().appMode !== 'live') return

        set({ color })
        if (typeof document !== 'undefined') {
          document.documentElement.setAttribute('data-theme', color)
        }
      },

      setAppMode: (appMode) => {
        const previousMode = get().appMode
        set({ appMode })
        if (typeof document !== 'undefined') {
          // Remove all mode classes first
          document.documentElement.classList.remove('analyzer', 'sandbox', 'dark')

          if (appMode === 'live') {
            // Restore the saved light/dark mode when returning to live
            const savedMode = get().mode
            document.documentElement.classList.toggle('dark', savedMode === 'dark')
          } else {
            // Analyzer mode uses its own dark purple theme (like dracula)
            document.documentElement.classList.add('analyzer')
          }
        }
        // Notify listeners if mode changed
        if (previousMode !== appMode) {
          notifyModeChange(appMode)
        }
      },

      toggleMode: () => {
        // Only allow toggle in live mode
        if (get().appMode !== 'live') return

        const newMode = get().mode === 'light' ? 'dark' : 'light'
        set({ mode: newMode })
        if (typeof document !== 'undefined') {
          document.documentElement.classList.toggle('dark', newMode === 'dark')
        }
      },

      // Toggle app mode via backend API
      toggleAppMode: async (): Promise<{ success: boolean; message?: string }> => {
        if (get().isTogglingMode) return { success: false, message: 'Already toggling' }

        set({ isTogglingMode: true })
        try {
          // First fetch CSRF token
          const csrfResponse = await fetch('/auth/csrf-token', {
            credentials: 'include',
          })
          const csrfData = await csrfResponse.json()

          const response = await fetch('/auth/analyzer-toggle', {
            method: 'POST',
            credentials: 'include',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': csrfData.csrf_token,
            },
          })

          const data = await response.json()

          if (response.ok && data.status === 'success') {
            const newMode: AppMode = data.data.analyze_mode ? 'analyzer' : 'live'
            get().setAppMode(newMode)
            return { success: true, message: data.data.message }
          } else {
            return { success: false, message: data.message || 'Failed to toggle mode' }
          }
        } catch (error) {
          return { success: false, message: 'Network error' }
        } finally {
          set({ isTogglingMode: false })
        }
      },

      // Sync app mode from backend
      syncAppMode: async () => {
        try {
          const response = await fetch('/auth/analyzer-mode', {
            credentials: 'include',
          })

          if (response.ok) {
            const data = await response.json()
            if (data.status === 'success') {
              const backendMode: AppMode = data.data.analyze_mode ? 'analyzer' : 'live'
              const currentMode = get().appMode
              if (currentMode !== backendMode) {
                get().setAppMode(backendMode)
              }
            }
            // If backend returns error status but response.ok, keep current appMode
          }
          // If request fails (401, etc.) - user is logged out, keep current appMode
          // This preserves the theme across logout for visual continuity
        } catch (error) {
          // On error, keep current appMode - preserves theme across logout
        }
      },
    }),
    {
      name: 'openalgo-theme',
      partialize: (state) => ({
        mode: state.mode,
        color: state.color,
        appMode: state.appMode, // Persist appMode for visual continuity across logout
      }),
      onRehydrateStorage: () => (state) => {
        // Apply theme on rehydration
        if (state && typeof document !== 'undefined') {
          document.documentElement.classList.remove('analyzer', 'sandbox', 'dark')

          // Apply persisted appMode for visual continuity
          if (state.appMode === 'analyzer') {
            document.documentElement.classList.add('analyzer')
          } else {
            // Live mode - apply light/dark preference
            document.documentElement.classList.toggle('dark', state.mode === 'dark')
          }
          document.documentElement.setAttribute('data-theme', state.color)
        }
      },
    }
  )
)

```
