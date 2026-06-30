# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\frontend\src\lib



---

# FILE: frontend\src\lib\MarketDataManager.ts

```ts
/**
 * MarketDataManager - Singleton class for shared WebSocket connection management
 *
 * Implements:
 * - Single WebSocket connection across all components
 * - Ref-counted subscriptions (only unsubscribe when last consumer leaves)
 * - Callback registry for data fan-out to multiple subscribers
 * - Connection lifecycle management (connect, pause, resume, disconnect)
 * - REST API fallback when WebSocket is unavailable (e.g., after market hours)
 *
 * Fallback behavior:
 * - After 3 consecutive WebSocket connection failures, switches to REST API polling
 * - Polls /api/v1/multiquotes every 5 seconds for subscribed symbols
 * - Automatically switches back to WebSocket when connection is restored
 */

export interface DepthLevel {
  price: number
  quantity: number
  orders?: number
}

export interface MarketData {
  ltp?: number
  open?: number
  high?: number
  low?: number
  close?: number
  volume?: number
  change?: number
  change_percent?: number
  timestamp?: string
  bid_price?: number
  ask_price?: number
  bid_size?: number
  ask_size?: number
  depth?: {
    buy: DepthLevel[]
    sell: DepthLevel[]
  }
}

export interface SymbolData {
  symbol: string
  exchange: string
  data: MarketData
  lastUpdate?: number
}

export type SubscriptionMode = 'LTP' | 'Quote' | 'Depth'

export type ConnectionState =
  | 'disconnected'
  | 'connecting'
  | 'connected'
  | 'authenticating'
  | 'authenticated'
  | 'paused'

export type StateListener = (state: {
  connectionState: ConnectionState
  isConnected: boolean
  isAuthenticated: boolean
  isPaused: boolean
  isFallbackMode: boolean
  error: string | null
}) => void

export type DataCallback = (data: SymbolData) => void

interface SubscriptionEntry {
  symbol: string
  exchange: string
  mode: SubscriptionMode
  callbacks: Set<DataCallback>
  refCount: number
}

// Fetch CSRF token for authenticated requests
async function fetchCSRFToken(): Promise<string> {
  const response = await fetch('/auth/csrf-token', { credentials: 'include' })
  const data = await response.json()
  return data.csrf_token
}

// REST API response types
interface QuotesApiData {
  ltp?: number
  open?: number
  high?: number
  low?: number
  prev_close?: number
  volume?: number
  bid?: number
  ask?: number
  oi?: number
}

interface MultiQuotesResult {
  symbol: string
  exchange: string
  data: QuotesApiData
}

interface MultiQuotesApiResponse {
  status: 'success' | 'error'
  results?: MultiQuotesResult[]
  message?: string
}

export class MarketDataManager {
  private static instance: MarketDataManager | null = null

  private socket: WebSocket | null = null
  private subscriptions: Map<string, SubscriptionEntry> = new Map() // key: "EXCHANGE:SYMBOL:MODE"
  private dataCache: Map<string, SymbolData> = new Map() // key: "EXCHANGE:SYMBOL"
  private stateListeners: Set<StateListener> = new Set()

  private connectionState: ConnectionState = 'disconnected'
  private error: string | null = null
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null
  private autoReconnect: boolean = true
  private reconnectAttempts: number = 0
  private maxReconnectAttempts: number = 10
  private userDisconnected: boolean = false
  private connectAbortController: AbortController | null = null

  // REST API fallback properties
  private fallbackMode: boolean = false
  private fallbackPollingInterval: ReturnType<typeof setInterval> | null = null
  private fallbackPollingRate: number = 5000 // Poll every 5 seconds in fallback mode
  private apiKey: string | null = null
  private consecutiveFailures: number = 0
  private maxConsecutiveFailures: number = 3 // Switch to fallback after 3 consecutive connection failures

  private constructor() {
    // Private constructor for singleton pattern
  }

  static getInstance(): MarketDataManager {
    if (!MarketDataManager.instance) {
      MarketDataManager.instance = new MarketDataManager()
    }
    return MarketDataManager.instance
  }

  // For testing purposes only
  static resetInstance(): void {
    if (MarketDataManager.instance) {
      MarketDataManager.instance.disconnect()
      MarketDataManager.instance = null
    }
  }

  /**
   * Subscribe to market data for a symbol
   * Returns an unsubscribe function
   */
  subscribe(
    rawSymbol: string,
    rawExchange: string,
    mode: SubscriptionMode,
    callback: DataCallback
  ): () => void {
    // Normalize to uppercase for consistent cache keys across WebSocket and REST
    const symbol = rawSymbol.toUpperCase()
    const exchange = rawExchange.toUpperCase()
    const key = `${exchange}:${symbol}:${mode}`
    const dataKey = `${exchange}:${symbol}`

    let entry = this.subscriptions.get(key)

    if (entry) {
      // Existing subscription - add callback and increment ref count
      entry.callbacks.add(callback)
      entry.refCount++

      // Send cached data immediately if available
      const cached = this.dataCache.get(dataKey)
      if (cached) {
        callback(cached)
      }
    } else {
      // New subscription
      entry = {
        symbol,
        exchange,
        mode,
        callbacks: new Set([callback]),
        refCount: 1,
      }
      this.subscriptions.set(key, entry)

      // Initialize cache entry
      if (!this.dataCache.has(dataKey)) {
        this.dataCache.set(dataKey, { symbol, exchange, data: {} })
      }

      // Send subscribe message if connected and authenticated
      if (this.connectionState === 'authenticated') {
        this.sendSubscribe([{ symbol, exchange }], mode)
      } else if (this.fallbackMode && this.apiKey) {
        // In fallback mode - start polling if not already running
        if (!this.fallbackPollingInterval) {
          this.startFallbackPolling()
        } else {
          // Fetch immediately for new subscription
          this.fetchMarketDataViaRest()
        }
      }
    }

    // Return unsubscribe function
    return () => {
      this.unsubscribe(symbol, exchange, mode, callback)
    }
  }

  private unsubscribe(
    rawSymbol: string,
    rawExchange: string,
    mode: SubscriptionMode,
    callback: DataCallback
  ): void {
    const symbol = rawSymbol.toUpperCase()
    const exchange = rawExchange.toUpperCase()
    const key = `${exchange}:${symbol}:${mode}`
    const entry = this.subscriptions.get(key)

    if (!entry) return

    entry.callbacks.delete(callback)
    entry.refCount--

    // Only send unsubscribe when last consumer leaves
    if (entry.refCount <= 0) {
      this.subscriptions.delete(key)

      // Check if any other mode still needs this symbol
      const symbolStillNeeded = Array.from(this.subscriptions.values()).some(
        (e) => e.symbol === symbol && e.exchange === exchange
      )

      if (!symbolStillNeeded) {
        // Clean up cache
        const dataKey = `${exchange}:${symbol}`
        this.dataCache.delete(dataKey)

        // Send unsubscribe if connected
        if (this.connectionState === 'authenticated') {
          this.sendUnsubscribe([{ symbol, exchange }])
        }
      }

      // Stop fallback polling if no more subscriptions
      if (this.subscriptions.size === 0 && this.fallbackMode) {
        this.stopFallbackPolling()
      }
    }
  }

  /**
   * Add a listener for connection state changes
   */
  addStateListener(listener: StateListener): () => void {
    this.stateListeners.add(listener)

    // Immediately notify with current state
    listener(this.getState())

    return () => {
      this.stateListeners.delete(listener)
    }
  }

  getState() {
    return {
      connectionState: this.connectionState,
      isConnected:
        this.connectionState === 'connected' ||
        this.connectionState === 'authenticating' ||
        this.connectionState === 'authenticated',
      isAuthenticated: this.connectionState === 'authenticated',
      isPaused: this.connectionState === 'paused',
      isFallbackMode: this.fallbackMode,
      error: this.error,
    }
  }

  /**
   * Check if currently in REST API fallback mode
   */
  isFallback(): boolean {
    return this.fallbackMode
  }

  /**
   * Get cached data for a symbol
   */
  getCachedData(symbol: string, exchange: string): SymbolData | undefined {
    return this.dataCache.get(`${exchange.toUpperCase()}:${symbol.toUpperCase()}`)
  }

  /**
   * Get all cached data
   */
  getAllCachedData(): Map<string, SymbolData> {
    return new Map(this.dataCache)
  }

  /**
   * Set auto-reconnect behavior
   */
  setAutoReconnect(enabled: boolean): void {
    this.autoReconnect = enabled
  }

  /**
   * Get current auto-reconnect setting
   */
  getAutoReconnect(): boolean {
    return this.autoReconnect
  }

  /**
   * Connect to WebSocket server
   */
  async connect(): Promise<void> {
    // Guard against multiple connections - check all active/connecting states
    if (
      this.socket?.readyState === WebSocket.OPEN ||
      this.socket?.readyState === WebSocket.CONNECTING ||
      this.connectionState === 'connecting' ||
      this.connectionState === 'connected' ||
      this.connectionState === 'authenticating' ||
      this.connectionState === 'authenticated'
    ) {
      return
    }

    // Clear user disconnect flag when starting a new connection
    this.userDisconnected = false

    // Abort any previous connect attempt
    this.connectAbortController?.abort()
    this.connectAbortController = new AbortController()
    const abortSignal = this.connectAbortController.signal

    this.setConnectionState('connecting')
    this.error = null

    try {
      const csrfToken = await fetchCSRFToken()

      // Check if disconnect was called during async operation
      if (this.userDisconnected || abortSignal.aborted) {
        this.setConnectionState('disconnected')
        return
      }

      // Get WebSocket config
      const configResponse = await fetch('/api/websocket/config', {
        headers: { 'X-CSRFToken': csrfToken },
        credentials: 'include',
        signal: abortSignal,
      })
      const configData = await configResponse.json()

      if (configData.status !== 'success') {
        throw new Error('Failed to get WebSocket configuration')
      }

      // Check again after config fetch
      if (this.userDisconnected || abortSignal.aborted) {
        this.setConnectionState('disconnected')
        return
      }

      const wsUrl = configData.websocket_url
      const socket = new WebSocket(wsUrl)

      socket.onopen = async () => {
        // Check if disconnect was called before socket opened
        if (this.userDisconnected) {
          socket.close(1000, 'User disconnect during connection')
          return
        }

        this.setConnectionState('connected')
        this.reconnectAttempts = 0

        try {
          // Get API key for authentication
          const authCsrfToken = await fetchCSRFToken()

          // Check again after async operation
          if (this.userDisconnected) {
            socket.close(1000, 'User disconnect during authentication')
            return
          }

          const apiKeyResponse = await fetch('/api/websocket/apikey', {
            headers: { 'X-CSRFToken': authCsrfToken },
            credentials: 'include',
          })
          const apiKeyData = await apiKeyResponse.json()

          // Check again after API key fetch
          if (this.userDisconnected) {
            socket.close(1000, 'User disconnect during authentication')
            return
          }

          if (apiKeyData.status === 'success' && apiKeyData.api_key) {
            this.setConnectionState('authenticating')
            socket.send(JSON.stringify({ action: 'authenticate', api_key: apiKeyData.api_key }))
          } else {
            this.setError('No API key found - please generate one at /apikey')
          }
        } catch (err) {
          this.setError(`Authentication error: ${err}`)
        }
      }

      socket.onclose = (event) => {
        this.socket = null

        if (this.connectionState !== 'paused') {
          this.setConnectionState('disconnected')
        }

        // Track consecutive failures for fallback trigger
        if (!event.wasClean) {
          this.consecutiveFailures++
        }

        // Auto-reconnect if not clean close and not paused
        if (
          this.autoReconnect &&
          !event.wasClean &&
          this.connectionState !== 'paused' &&
          this.reconnectAttempts < this.maxReconnectAttempts
        ) {
          this.reconnectAttempts++
          const delay = Math.min(1000 * 2 ** (this.reconnectAttempts - 1), 30000) // Exponential backoff, max 30s
          this.reconnectTimeout = setTimeout(() => this.connect(), delay)
        } else if (
          this.reconnectAttempts >= this.maxReconnectAttempts ||
          this.consecutiveFailures >= this.maxConsecutiveFailures
        ) {
          // Max reconnect attempts reached - switch to REST API fallback
          this.enableFallbackMode()
        }
      }

      socket.onerror = () => {
        this.consecutiveFailures++
        this.setError('WebSocket connection error')
      }

      socket.onmessage = (event) => this.handleMessage(event)

      this.socket = socket
    } catch (err) {
      this.consecutiveFailures++
      this.setError(`Connection failed: ${err}`)
      this.setConnectionState('disconnected')

      // Check if we should switch to fallback mode
      if (this.consecutiveFailures >= this.maxConsecutiveFailures) {
        this.enableFallbackMode()
      }
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    // Mark as user-initiated disconnect to prevent zombie connections
    this.userDisconnected = true

    // Abort any in-progress connection attempt
    if (this.connectAbortController) {
      this.connectAbortController.abort()
      this.connectAbortController = null
    }

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
      this.reconnectTimeout = null
    }

    if (this.socket) {
      this.socket.close(1000, 'User disconnect')
      this.socket = null
    }

    // Stop fallback polling on disconnect
    this.stopFallbackPolling()
    this.fallbackMode = false
    this.consecutiveFailures = 0
    this.apiKey = null

    this.setConnectionState('disconnected')
  }

  /**
   * Pause connection (e.g., when tab is hidden)
   * Keeps subscriptions in memory for resume
   */
  pauseConnection(): void {
    if (this.connectionState === 'paused' || this.connectionState === 'disconnected') {
      return
    }

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
      this.reconnectTimeout = null
    }

    if (this.socket) {
      this.socket.close(1000, 'Paused')
      this.socket = null
    }

    this.setConnectionState('paused')
  }

  /**
   * Resume connection after pause
   * Resubscribes to all active subscriptions
   */
  async resumeConnection(): Promise<void> {
    if (this.connectionState !== 'paused') {
      return
    }

    await this.connect()
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const data = JSON.parse(event.data)
      const type = (data.type || data.status) as string

      switch (type) {
        case 'auth':
          if (data.status === 'success') {
            this.setConnectionState('authenticated')
            this.error = null
            this.consecutiveFailures = 0 // Reset failure count on successful auth
            // Disable fallback mode now that WebSocket is working
            this.disableFallbackMode()
            // Resubscribe to all active subscriptions
            this.resubscribeAll()
          } else {
            this.setError(`Authentication failed: ${data.message}`)
          }
          break

        case 'market_data': {
          const symbol = (data.symbol as string).toUpperCase()
          const exchange = (data.exchange as string).toUpperCase()
          const marketDataPayload = (data.data || {}) as MarketData
          const dataKey = `${exchange}:${symbol}`

          // Update cache
          const existing = this.dataCache.get(dataKey) || { symbol, exchange, data: {} }
          const newData = { ...existing.data }

          Object.assign(newData, {
            ltp: marketDataPayload.ltp ?? newData.ltp,
            open: marketDataPayload.open ?? newData.open,
            high: marketDataPayload.high ?? newData.high,
            low: marketDataPayload.low ?? newData.low,
            close: marketDataPayload.close ?? newData.close,
            volume: marketDataPayload.volume ?? newData.volume,
            change: marketDataPayload.change ?? newData.change,
            change_percent: marketDataPayload.change_percent ?? newData.change_percent,
            timestamp: marketDataPayload.timestamp ?? newData.timestamp,
            bid_price: marketDataPayload.bid_price ?? newData.bid_price,
            ask_price: marketDataPayload.ask_price ?? newData.ask_price,
            bid_size: marketDataPayload.bid_size ?? newData.bid_size,
            ask_size: marketDataPayload.ask_size ?? newData.ask_size,
            depth: marketDataPayload.depth ?? newData.depth,
          })

          const updatedSymbolData: SymbolData = {
            ...existing,
            data: newData,
            lastUpdate: Date.now(),
          }
          this.dataCache.set(dataKey, updatedSymbolData)

          // Fan out to all callbacks for this symbol (across all modes)
          this.subscriptions.forEach((entry) => {
            if (entry.symbol === symbol && entry.exchange === exchange) {
              entry.callbacks.forEach((callback) => {
                callback(updatedSymbolData)
              })
            }
          })
          break
        }

        case 'subscribe':
          // Subscription confirmed - no action needed
          break

        case 'error':
          this.setError(`WebSocket error: ${data.message}`)
          break
      }
    } catch {
      // Ignore parse errors for non-JSON messages
    }
  }

  private sendSubscribe(
    symbols: Array<{ symbol: string; exchange: string }>,
    mode: SubscriptionMode
  ): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) return

    this.socket.send(
      JSON.stringify({
        action: 'subscribe',
        symbols,
        mode,
      })
    )
  }

  private sendUnsubscribe(symbols: Array<{ symbol: string; exchange: string }>): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) return

    this.socket.send(
      JSON.stringify({
        action: 'unsubscribe',
        symbols,
      })
    )
  }

  private resubscribeAll(): void {
    // Group subscriptions by mode for efficient batching
    const byMode = new Map<SubscriptionMode, Array<{ symbol: string; exchange: string }>>()

    this.subscriptions.forEach((entry) => {
      const symbols = byMode.get(entry.mode) || []
      symbols.push({ symbol: entry.symbol, exchange: entry.exchange })
      byMode.set(entry.mode, symbols)
    })

    // Send subscribe for each mode
    byMode.forEach((symbols, mode) => {
      if (symbols.length > 0) {
        this.sendSubscribe(symbols, mode)
      }
    })
  }

  private setConnectionState(state: ConnectionState): void {
    this.connectionState = state
    this.notifyStateListeners()
  }

  private setError(error: string): void {
    this.error = error
    this.notifyStateListeners()
  }

  private notifyStateListeners(): void {
    const state = this.getState()
    this.stateListeners.forEach((listener) => listener(state))
  }

  // ============================================================
  // REST API Fallback Methods
  // ============================================================

  /**
   * Switch to REST API fallback mode
   * Called when WebSocket connection repeatedly fails
   */
  private async enableFallbackMode(): Promise<void> {
    if (this.fallbackMode) return

    this.fallbackMode = true
    this.notifyStateListeners()

    // Fetch API key for REST calls
    await this.fetchApiKeyForFallback()

    // Start polling if we have subscriptions
    if (this.subscriptions.size > 0 && this.apiKey) {
      this.startFallbackPolling()
    }
  }

  /**
   * Disable REST API fallback mode (when WebSocket reconnects)
   */
  private disableFallbackMode(): void {
    if (!this.fallbackMode) return

    this.fallbackMode = false
    this.stopFallbackPolling()
    this.consecutiveFailures = 0
    this.notifyStateListeners()
  }

  /**
   * Fetch API key for REST API calls
   */
  private async fetchApiKeyForFallback(): Promise<void> {
    try {
      const csrfToken = await fetchCSRFToken()
      const response = await fetch('/api/websocket/apikey', {
        headers: { 'X-CSRFToken': csrfToken },
        credentials: 'include',
      })
      const data = await response.json()
      if (data.status === 'success' && data.api_key) {
        this.apiKey = data.api_key
      }
    } catch (err) {}
  }

  /**
   * Start REST API polling for subscribed symbols
   */
  private startFallbackPolling(): void {
    if (this.fallbackPollingInterval) return

    // Fetch immediately
    this.fetchMarketDataViaRest()

    // Then poll at regular intervals
    this.fallbackPollingInterval = setInterval(() => {
      this.fetchMarketDataViaRest()
    }, this.fallbackPollingRate)
  }

  /**
   * Stop REST API polling
   */
  private stopFallbackPolling(): void {
    if (this.fallbackPollingInterval) {
      clearInterval(this.fallbackPollingInterval)
      this.fallbackPollingInterval = null
    }
  }

  /**
   * Fetch market data via REST API (multiquotes endpoint)
   */
  private async fetchMarketDataViaRest(): Promise<void> {
    if (!this.apiKey || this.subscriptions.size === 0) return

    try {
      // Collect unique symbols from subscriptions
      const uniqueSymbols = new Map<string, { symbol: string; exchange: string }>()
      this.subscriptions.forEach((entry) => {
        const key = `${entry.exchange}:${entry.symbol}`
        if (!uniqueSymbols.has(key)) {
          uniqueSymbols.set(key, { symbol: entry.symbol, exchange: entry.exchange })
        }
      })

      const symbolsArray = Array.from(uniqueSymbols.values())
      if (symbolsArray.length === 0) return

      // Call multiquotes API
      const response = await fetch('/api/v1/multiquotes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          apikey: this.apiKey,
          symbols: symbolsArray,
        }),
      })

      const data = (await response.json()) as MultiQuotesApiResponse

      if (data.status === 'success' && data.results) {
        // Process each result and update cache + notify subscribers
        for (const result of data.results) {
          const symbol = result.symbol.toUpperCase()
          const exchange = result.exchange.toUpperCase()
          const dataKey = `${exchange}:${symbol}`

          // Update cache
          const existing = this.dataCache.get(dataKey) || { symbol, exchange, data: {} }
          const newData = { ...existing.data }

          Object.assign(newData, {
            ltp: result.data.ltp ?? newData.ltp,
            open: result.data.open ?? newData.open,
            high: result.data.high ?? newData.high,
            low: result.data.low ?? newData.low,
            close: result.data.prev_close ?? newData.close,
            volume: result.data.volume ?? newData.volume,
            bid_price: result.data.bid ?? newData.bid_price,
            ask_price: result.data.ask ?? newData.ask_price,
          })

          const updatedSymbolData: SymbolData = {
            ...existing,
            data: newData,
            lastUpdate: Date.now(),
          }
          this.dataCache.set(dataKey, updatedSymbolData)

          // Fan out to all callbacks for this symbol (keys are already normalized to uppercase)
          this.subscriptions.forEach((entry) => {
            if (entry.symbol === symbol && entry.exchange === exchange) {
              entry.callbacks.forEach((callback) => {
                callback(updatedSymbolData)
              })
            }
          })
        }
      }
    } catch (err) {}
  }

  /**
   * Set fallback polling rate in milliseconds
   */
  setFallbackPollingRate(rate: number): void {
    this.fallbackPollingRate = rate
    // Restart polling if currently active
    if (this.fallbackPollingInterval) {
      this.stopFallbackPolling()
      this.startFallbackPolling()
    }
  }
}

export default MarketDataManager

```


---

# FILE: frontend\src\lib\Plot2D.tsx

[BINARY FILE]

Type: .tsx

Size: 546 bytes

Path: frontend\src\lib\Plot2D.tsx


---

# FILE: frontend\src\lib\Plot3D.tsx

[BINARY FILE]

Type: .tsx

Size: 303 bytes

Path: frontend\src\lib\Plot3D.tsx


---

# FILE: frontend\src\lib\plotly-2d.ts

```ts
// Custom Plotly 2D build — registers only the trace types the 2D tools
// actually use (scatter, bar, candlestick). Scatter covers line, marker,
// and area fills; `type: 'line'` in code is treated as scatter by Plotly.
// Ships a much smaller chunk than the full plotly.js-dist-min bundle.
// 3D surface plots are in a separate module (`plotly-3d.ts`) so VolSurface
// is the only page that pays the WebGL / gl3d cost.

import bar from 'plotly.js/lib/bar'
import candlestick from 'plotly.js/lib/candlestick'
import Plotly from 'plotly.js/lib/core'
import scatter from 'plotly.js/lib/scatter'

Plotly.register([scatter, bar, candlestick])

export default Plotly

```


---

# FILE: frontend\src\lib\plotly-3d.ts

```ts
// Plotly 3D build — adds only the `surface` trace, used exclusively by
// /volsurface. Kept as its own module so 2D tools don't bundle the gl3d
// WebGL engine. Vite / Rollup dedupes `plotly.js/lib/core` into a shared
// vendor chunk between this file and plotly-2d.ts.
import Plotly from 'plotly.js/lib/core'
import surface from 'plotly.js/lib/surface'

Plotly.register([surface])

export default Plotly

```


---

# FILE: frontend\src\lib\rateLimiter.ts

```ts
/**
 * Rate Limiting Utilities
 *
 * Provides client-side rate limiting to prevent excessive API calls
 * and improve user experience by preventing accidental double-clicks.
 */

/**
 * Creates a debounced version of a function that delays execution
 * until after `wait` milliseconds have elapsed since the last call.
 *
 * @param fn - The function to debounce
 * @param wait - The number of milliseconds to delay
 * @returns A debounced version of the function
 */
export function debounce<T extends (...args: Parameters<T>) => ReturnType<T>>(
  fn: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null

  return function debounced(...args: Parameters<T>): void {
    if (timeoutId !== null) {
      clearTimeout(timeoutId)
    }

    timeoutId = setTimeout(() => {
      fn(...args)
      timeoutId = null
    }, wait)
  }
}

/**
 * Creates a throttled version of a function that only executes
 * at most once per `wait` milliseconds.
 *
 * @param fn - The function to throttle
 * @param wait - The minimum time between function calls in milliseconds
 * @returns A throttled version of the function
 */
export function throttle<T extends (...args: Parameters<T>) => ReturnType<T>>(
  fn: T,
  wait: number
): (...args: Parameters<T>) => void {
  let lastCall = 0
  let timeoutId: ReturnType<typeof setTimeout> | null = null

  return function throttled(...args: Parameters<T>): void {
    const now = Date.now()
    const remaining = wait - (now - lastCall)

    if (remaining <= 0) {
      if (timeoutId !== null) {
        clearTimeout(timeoutId)
        timeoutId = null
      }
      lastCall = now
      fn(...args)
    } else if (timeoutId === null) {
      timeoutId = setTimeout(() => {
        lastCall = Date.now()
        timeoutId = null
        fn(...args)
      }, remaining)
    }
  }
}

/**
 * Creates a rate limiter that allows at most `maxCalls` calls
 * within a `windowMs` time window.
 *
 * @param maxCalls - Maximum number of calls allowed in the window
 * @param windowMs - Time window in milliseconds
 * @returns An object with `canCall()` to check limits and `call()` to execute
 */
export function createRateLimiter(maxCalls: number, windowMs: number) {
  const timestamps: number[] = []

  function cleanup() {
    const now = Date.now()
    while (timestamps.length > 0 && timestamps[0] < now - windowMs) {
      timestamps.shift()
    }
  }

  return {
    /**
     * Check if a call is allowed without consuming a slot
     */
    canCall(): boolean {
      cleanup()
      return timestamps.length < maxCalls
    },

    /**
     * Record a call and return whether it was allowed
     */
    call(): boolean {
      cleanup()
      if (timestamps.length < maxCalls) {
        timestamps.push(Date.now())
        return true
      }
      return false
    },

    /**
     * Get remaining calls available in current window
     */
    remaining(): number {
      cleanup()
      return Math.max(0, maxCalls - timestamps.length)
    },

    /**
     * Get time until next call is available (0 if available now)
     */
    timeUntilNext(): number {
      cleanup()
      if (timestamps.length < maxCalls) {
        return 0
      }
      return Math.max(0, timestamps[0] + windowMs - Date.now())
    },

    /**
     * Reset the rate limiter
     */
    reset(): void {
      timestamps.length = 0
    },
  }
}

/**
 * Creates a function wrapper that prevents duplicate calls while
 * a previous call is still pending.
 *
 * @param fn - An async function to wrap
 * @returns A wrapped function that prevents concurrent execution
 */
export function preventConcurrent<
  T extends (...args: Parameters<T>) => Promise<Awaited<ReturnType<T>>>,
>(fn: T): (...args: Parameters<T>) => Promise<Awaited<ReturnType<T>> | undefined> {
  let isPending = false

  return async (...args: Parameters<T>): Promise<Awaited<ReturnType<T>> | undefined> => {
    if (isPending) {
      return undefined
    }

    isPending = true
    try {
      return await fn(...args)
    } finally {
      isPending = false
    }
  }
}

// Pre-configured rate limiters for common use cases
export const orderRateLimiter = createRateLimiter(10, 1000) // 10 orders per second
export const apiRateLimiter = createRateLimiter(50, 1000) // 50 API calls per second
export const searchRateLimiter = createRateLimiter(5, 1000) // 5 searches per second

```


---

# FILE: frontend\src\lib\strategyMath.ts

```ts
/**
 * Options math for the Strategy Builder.
 *
 * Uses the Black-Scholes model on spot (for intra-expiry "T+0" pricing in the
 * payoff simulator) and a simple intrinsic payoff at expiry. IV / live prices
 * come from the server's Black-76 greeks service — this file only re-prices
 * the same legs under what-if shifts (spot %, IV %, days).
 */

export type OptionType = 'CE' | 'PE'
export type Side = 'BUY' | 'SELL'
export type Segment = 'OPTION' | 'FUTURE'

/**
 * Classify a strike's moneyness relative to the ATM strike.
 *
 * Returns a short label like "ATM", "ITM1", "ITM2", "OTM1", "OTM3" where the
 * number is how many strike-steps away from ATM the strike is.
 *
 * Call (CE):  strike < ATM → ITM    ·    strike > ATM → OTM
 * Put (PE):   strike > ATM → ITM    ·    strike < ATM → OTM
 *
 * Returns null when inputs are insufficient (missing ATM, non-positive step).
 */
export function strikeMoneyness(
  strike: number | undefined,
  atmStrike: number | null,
  strikeStep: number,
  optionType: OptionType | undefined
): { label: string; kind: 'ATM' | 'ITM' | 'OTM'; steps: number } | null {
  if (strike === undefined || atmStrike === null || !optionType) return null
  if (!Number.isFinite(strikeStep) || strikeStep <= 0) return null
  const rawSteps = (strike - atmStrike) / strikeStep
  const steps = Math.round(rawSteps)
  if (steps === 0) return { label: 'ATM', kind: 'ATM', steps: 0 }
  const isCallITM = optionType === 'CE' && steps < 0
  const isPutITM = optionType === 'PE' && steps > 0
  const kind: 'ITM' | 'OTM' = isCallITM || isPutITM ? 'ITM' : 'OTM'
  return { label: `${kind}${Math.abs(steps)}`, kind, steps }
}

export interface StrategyLeg {
  id: string
  segment: Segment
  side: Side
  lots: number
  lotSize: number
  expiry: string // OpenAlgo format, e.g. 28APR26
  strike?: number // required for options
  optionType?: OptionType // required for options
  /** Live / entry premium (per share, not per lot). 0 if unknown. */
  price: number
  /** Live IV (%) at the time of building. 0 if unknown. */
  iv: number
  active: boolean
  /** Symbol for display / Greeks lookup */
  symbol: string
  /**
   * Exit price (per share). When > 0 the leg is treated as "closed":
   * P&L is frozen at (exitPrice - entryPrice) * qty * sign for every
   * underlying value, and it no longer responds to spot/IV/time shifts.
   */
  exitPrice?: number
}

const SQRT2 = Math.SQRT2
const SQRT2PI = Math.sqrt(2 * Math.PI)

/** Error function approximation (Abramowitz & Stegun 7.1.26, max error ~1.5e-7). */
function erf(x: number): number {
  const sign = Math.sign(x) || 1
  const ax = Math.abs(x)
  const t = 1 / (1 + 0.3275911 * ax)
  const y =
    1 -
    ((((1.061405429 * t - 1.453152027) * t + 1.421413741) * t - 0.284496736) * t + 0.254829592) *
      t *
      Math.exp(-ax * ax)
  return sign * y
}

/** Standard normal CDF. */
export function normCdf(x: number): number {
  return 0.5 * (1 + erf(x / SQRT2))
}

/** Standard normal PDF. */
export function normPdf(x: number): number {
  return Math.exp(-0.5 * x * x) / SQRT2PI
}

export interface BsInputs {
  spot: number
  strike: number
  /** Time to expiry in years. Must be > 0 for the formula; we floor at a tiny epsilon. */
  t: number
  /** Implied volatility as decimal (0.15 = 15%). */
  iv: number
  /** Risk-free rate as decimal (0.0 default for INR index options). */
  r?: number
  /** Dividend yield as decimal. */
  q?: number
}

/** Black-Scholes price for a European option on spot. */
export function bsPrice(type: OptionType, inp: BsInputs): number {
  const { spot, strike, iv } = inp
  const r = inp.r ?? 0
  const q = inp.q ?? 0
  const t = Math.max(inp.t, 1e-8)

  // Intrinsic fallback for zero-vol or zero-time.
  if (iv <= 0 || t <= 1e-8) {
    return intrinsic(type, spot, strike)
  }

  const d1 = (Math.log(spot / strike) + (r - q + 0.5 * iv * iv) * t) / (iv * Math.sqrt(t))
  const d2 = d1 - iv * Math.sqrt(t)

  if (type === 'CE') {
    return spot * Math.exp(-q * t) * normCdf(d1) - strike * Math.exp(-r * t) * normCdf(d2)
  }
  return strike * Math.exp(-r * t) * normCdf(-d2) - spot * Math.exp(-q * t) * normCdf(-d1)
}

export function intrinsic(type: OptionType, spot: number, strike: number): number {
  return type === 'CE' ? Math.max(spot - strike, 0) : Math.max(strike - spot, 0)
}

/**
 * Payoff of a single leg at a given underlying price, advanced `daysElapsed`
 * from `now`.
 *
 * Each leg computes its OWN remaining time from its own expiry, which is
 * critical for calendar/diagonal spreads where legs have different expiries.
 * The caller only specifies how far forward in calendar time to move from now;
 * the leg-specific remaining time is derived from that.
 */
export function legPnlAt(
  leg: StrategyLeg,
  underlying: number,
  daysElapsed: number,
  ivOverride?: number,
  now: Date = new Date()
): number {
  if (!leg.active) return 0
  const sign = leg.side === 'BUY' ? 1 : -1
  const qty = leg.lots * leg.lotSize

  // Closed leg: P&L is locked at the realised exit level and no longer
  // responds to spot / IV / time changes.
  if (leg.exitPrice !== undefined && leg.exitPrice > 0) {
    return sign * (leg.exitPrice - leg.price) * qty
  }

  if (leg.segment === 'FUTURE') {
    return sign * (underlying - leg.price) * qty
  }
  if (leg.strike === undefined || !leg.optionType) return 0

  // Days of life remaining for THIS leg after advancing calendar time.
  const legDaysNow = daysToExpiry(leg.expiry, now)
  const legRemainingDays = Math.max(legDaysNow - daysElapsed, 0)
  const tLeg = daysToYears(legRemainingDays)

  // At expiry (t=0) use intrinsic value; before that use Black-Scholes.
  const iv = (ivOverride ?? leg.iv) / 100
  const valueNow =
    tLeg <= 1e-6
      ? intrinsic(leg.optionType, underlying, leg.strike)
      : bsPrice(leg.optionType, { spot: underlying, strike: leg.strike, t: tLeg, iv })

  return sign * (valueNow - leg.price) * qty
}

export function totalPnlAt(
  legs: StrategyLeg[],
  underlying: number,
  daysElapsed: number,
  ivShiftPct: number = 0,
  /**
   * Fallback IV (%) used when a leg's own IV hasn't been fetched yet. Without
   * this, legs default to 0 IV and the T+0 curve collapses onto the expiry
   * curve on first paint. Typically the ATM IV from the option chain.
   */
  fallbackIv: number = 0,
  now: Date = new Date()
): number {
  let total = 0
  for (const leg of legs) {
    const baseIv = leg.iv > 0 ? leg.iv : fallbackIv
    const legIv = baseIv * (1 + ivShiftPct / 100)
    total += legPnlAt(leg, underlying, daysElapsed, legIv, now)
  }
  return total
}

/**
 * Net credit (+) / debit (-) collected when opening the strategy.
 * Futures legs contribute 0 (no premium).
 */
export function netCredit(legs: StrategyLeg[]): number {
  let credit = 0
  for (const leg of legs) {
    if (!leg.active) continue
    if (leg.segment !== 'OPTION') continue
    const qty = leg.lots * leg.lotSize
    credit += (leg.side === 'SELL' ? 1 : -1) * leg.price * qty
  }
  return credit
}

/** Total premium outlay (absolute). */
export function totalPremium(legs: StrategyLeg[]): number {
  let total = 0
  for (const leg of legs) {
    if (!leg.active || leg.segment !== 'OPTION') continue
    const qty = leg.lots * leg.lotSize
    total += leg.price * qty
  }
  return total
}

export interface PayoffSample {
  underlying: number
  expiry: number
  tplus0: number
}

export interface PayoffResult {
  samples: PayoffSample[]
  /**
   * True mathematical maximum profit of the strategy at expiry.
   * May be ``+Infinity`` for strategies with unlimited upside
   * (e.g. Long Call, Long Synthetic, Call Ratio Back Spread).
   */
  maxProfit: number
  /**
   * True mathematical maximum loss of the strategy at expiry.
   * May be ``-Infinity`` for strategies with unlimited downside
   * (e.g. Short Call, Short Synthetic, Short Straddle).
   */
  maxLoss: number
  breakevens: number[]
  /** Indexes of samples where expiry crosses zero, used for shading. */
  zeroCrossings: number[]
}

/**
 * Asymptotic slopes of the expiry payoff:
 *   right = dP/dS as S → +∞  (sensitivity to far-upside moves)
 *   left  = dP/dS as S → 0+  (sensitivity to far-downside moves)
 *
 * Used to detect unlimited-profit / unlimited-loss strategies that a finite
 * sample window would otherwise report as capped. Closed / inactive legs
 * contribute 0 (their P&L is locked or excluded).
 *
 * Slope contributions at S → +∞:
 *   BUY  CE  → +qty    (call goes ITM, gains ₹1 per ₹1 spot rise)
 *   SELL CE  → −qty
 *   BUY  PE  →  0      (put worthless at high spot)
 *   SELL PE  →  0
 *   BUY  FUT → +qty
 *   SELL FUT → −qty
 *
 * Slope contributions at S → 0+ (slope w.r.t. S, so a put gaining value as
 * S drops gives a NEGATIVE slope):
 *   BUY  CE  →  0
 *   SELL CE  →  0
 *   BUY  PE  → −qty
 *   SELL PE  → +qty
 *   BUY  FUT → +qty
 *   SELL FUT → −qty
 */
function asymptoticSlopes(legs: StrategyLeg[]): { right: number; left: number } {
  let right = 0
  let left = 0
  for (const leg of legs) {
    if (!leg.active) continue
    if (leg.exitPrice !== undefined && leg.exitPrice > 0) continue
    const qty = leg.lots * leg.lotSize
    const sign = leg.side === 'BUY' ? 1 : -1

    if (leg.segment === 'FUTURE') {
      right += sign * qty
      left += sign * qty
      continue
    }

    if (leg.segment === 'OPTION') {
      if (leg.optionType === 'CE') {
        right += sign * qty
      } else if (leg.optionType === 'PE') {
        left -= sign * qty
      }
    }
  }
  return { right, left }
}

export function computePayoff(
  legs: StrategyLeg[],
  _spot: number,
  /**
   * Calendar days to advance for the **Expiry** curve. For same-expiry
   * strategies this is the days to that single expiry. For calendars /
   * diagonals, pass the days to the NEAREST leg expiry — the remaining
   * legs will still be priced via Black-Scholes at their own remaining time.
   */
  daysAtExpiry: number,
  /**
   * Calendar days to advance for the **T+0** curve (simulator). 0 = now.
   */
  daysAtT0: number,
  priceRange: [number, number],
  steps: number = 240,
  ivShiftPct: number = 0,
  /** Fallback IV (%) for legs that haven't received their own IV yet. */
  fallbackIv: number = 0,
  now: Date = new Date()
): PayoffResult {
  const [lo, hi] = priceRange
  const step = (hi - lo) / steps
  const samples: PayoffSample[] = []
  let maxProfit = -Infinity
  let maxLoss = Infinity
  const zeroCrossings: number[] = []

  let prevExpiry: number | null = null
  for (let i = 0; i <= steps; i++) {
    const x = lo + i * step
    const atExpiry = totalPnlAt(legs, x, daysAtExpiry, ivShiftPct, fallbackIv, now)
    const atT0 = totalPnlAt(legs, x, daysAtT0, ivShiftPct, fallbackIv, now)
    samples.push({ underlying: x, expiry: atExpiry, tplus0: atT0 })
    if (atExpiry > maxProfit) maxProfit = atExpiry
    if (atExpiry < maxLoss) maxLoss = atExpiry
    if (prevExpiry !== null && Math.sign(prevExpiry) !== Math.sign(atExpiry)) {
      zeroCrossings.push(i - 1)
    }
    prevExpiry = atExpiry
  }

  // Linearly interpolate breakevens at zero crossings.
  const breakevens: number[] = []
  for (const idx of zeroCrossings) {
    const a = samples[idx]
    const b = samples[idx + 1]
    if (!a || !b) continue
    const dy = b.expiry - a.expiry
    if (Math.abs(dy) < 1e-9) continue
    const frac = -a.expiry / dy
    breakevens.push(a.underlying + frac * (b.underlying - a.underlying))
  }

  // ── True (mathematical) max profit / max loss ──
  //
  // The ±10% sample window used for the chart can silently cap true extrema:
  // Long Synthetic keeps rising past +10%, Short Call keeps falling, etc.
  // We can't rely on the sampled min/max — so compute them structurally:
  //
  //   1. Enumerate candidate underlying prices where the piecewise-linear
  //      expiry payoff can have an extremum — every strike (kinks) plus 0
  //      (the true left boundary, since spot ≥ 0) plus a point well past
  //      the highest strike (right plateau when rightSlope == 0).
  //   2. Evaluate the expiry payoff at each candidate.
  //   3. For the right side, use the asymptotic slope: if the payoff is
  //      still growing / falling past the last strike we override with
  //      ±Infinity — the user sees "Unlimited" instead of a misleading
  //      finite plateau value.
  //
  // The left side doesn't need an Infinity override because spot is
  // floored at 0 — the payoff at S=0 is the true left extremum even when
  // leftSlope is non-zero.
  const slopes = asymptoticSlopes(legs)

  const strikeSet = new Set<number>([0])
  for (const leg of legs) {
    if (!leg.active) continue
    if (leg.exitPrice !== undefined && leg.exitPrice > 0) continue
    if (leg.segment === 'OPTION' && leg.strike !== undefined) {
      strikeSet.add(leg.strike)
    } else if (leg.segment === 'FUTURE' && leg.price > 0) {
      // Futures legs have no strike kink, but their entry price gives us
      // a useful reference point to evaluate extrema near the current spot.
      strikeSet.add(leg.price)
    }
  }
  if (strikeSet.size > 1) {
    const farRight = Math.max(...Array.from(strikeSet)) * 2
    strikeSet.add(farRight)
  }

  let mathMaxProfit = -Infinity
  let mathMaxLoss = Infinity
  for (const s of strikeSet) {
    const val = totalPnlAt(legs, s, daysAtExpiry, ivShiftPct, fallbackIv, now)
    if (val > mathMaxProfit) mathMaxProfit = val
    if (val < mathMaxLoss) mathMaxLoss = val
  }

  if (slopes.right > 0) mathMaxProfit = Infinity
  if (slopes.right < 0) mathMaxLoss = -Infinity

  maxProfit = mathMaxProfit
  maxLoss = mathMaxLoss

  // Empty leg list → leave max/min at 0 so the UI doesn't flash "-Infinity".
  if (legs.length === 0) {
    maxProfit = 0
    maxLoss = 0
  }

  return {
    samples,
    maxProfit,
    maxLoss,
    breakevens,
    zeroCrossings,
  }
}

/**
 * Probability of profit using lognormal spot distribution.
 *
 * Models spot at expiry as lognormal with drift (r - q - σ²/2)·T and volatility σ√T
 * using the ATM IV. We then sum the probability mass over underlying ranges where
 * the expiry payoff is positive.
 */
export function probabilityOfProfit(
  samples: PayoffSample[],
  spot: number,
  atmIv: number,
  tYears: number
): number {
  if (samples.length < 2 || atmIv <= 0 || tYears <= 0 || spot <= 0) return 0
  const sigmaT = (atmIv / 100) * Math.sqrt(tYears)
  if (sigmaT <= 0) return 0

  // F(x) = P(S_T <= x) = Phi((ln(x/S0) - (-sigma^2/2) T) / (sigma sqrt T))  (risk-free drift = 0)
  const cdf = (x: number) => {
    if (x <= 0) return 0
    const mu = -0.5 * (atmIv / 100) * (atmIv / 100) * tYears
    return normCdf((Math.log(x / spot) - mu) / sigmaT)
  }

  let prob = 0
  for (let i = 0; i < samples.length - 1; i++) {
    const a = samples[i]
    const b = samples[i + 1]
    const mid = 0.5 * (a.expiry + b.expiry)
    if (mid > 0) {
      prob += cdf(b.underlying) - cdf(a.underlying)
    }
  }
  // Tail beyond last sample: assume same sign as last point.
  const last = samples[samples.length - 1]
  if (last.expiry > 0) prob += 1 - cdf(last.underlying)
  const first = samples[0]
  if (first.expiry > 0) prob += cdf(first.underlying)

  return Math.max(0, Math.min(1, prob))
}

/** Days to expiry (approximate, at 15:30 IST expiry close). */
export function parseExpiryDate(expiry: string): Date | null {
  // Format: DDMMMYY e.g. 28APR26
  const m = /^(\d{1,2})([A-Z]{3})(\d{2})$/.exec(expiry)
  if (!m) return null
  const day = parseInt(m[1], 10)
  const monthName = m[2]
  const year = 2000 + parseInt(m[3], 10)
  const months: Record<string, number> = {
    JAN: 0,
    FEB: 1,
    MAR: 2,
    APR: 3,
    MAY: 4,
    JUN: 5,
    JUL: 6,
    AUG: 7,
    SEP: 8,
    OCT: 9,
    NOV: 10,
    DEC: 11,
  }
  if (!(monthName in months)) return null
  // 15:30 IST = 10:00 UTC for Indian markets.
  return new Date(Date.UTC(year, months[monthName], day, 10, 0, 0))
}

export function daysToExpiry(expiry: string, now: Date = new Date()): number {
  const d = parseExpiryDate(expiry)
  if (!d) return 0
  const ms = d.getTime() - now.getTime()
  return Math.max(0, ms / (1000 * 60 * 60 * 24))
}

/**
 * Days to the nearest leg's expiry among a set of legs. Used by the payoff
 * chart's "At Expiry" curve for calendar / diagonal strategies where
 * multiple expiries are in play.
 */
export function nearestLegDays(legs: StrategyLeg[], now: Date = new Date()): number {
  let best = Infinity
  for (const leg of legs) {
    if (!leg.active) continue
    if (leg.exitPrice !== undefined && leg.exitPrice > 0) continue
    const d = daysToExpiry(leg.expiry, now)
    if (d < best) best = d
  }
  return best === Infinity ? 0 : best
}

/** Convert days to year-fraction (365 calendar days). */
export function daysToYears(days: number): number {
  return Math.max(0, days) / 365
}

/** Format symbol per OpenAlgo standard: BASE[DDMMMYY][STRIKE][CE|PE]. */
export function buildOptionSymbol(
  base: string,
  expiry: string,
  strike: number,
  type: OptionType
): string {
  const strikeStr =
    Number.isInteger(strike) || Math.abs(strike - Math.round(strike)) < 1e-6
      ? String(Math.round(strike))
      : String(strike)
  return `${base}${expiry}${strikeStr}${type}`
}

export function buildFutureSymbol(base: string, expiry: string): string {
  return `${base}${expiry}FUT`
}

/** Greek-level utilities for the Greeks tab. */
export function bsGreeks(
  type: OptionType,
  inp: BsInputs
): { delta: number; gamma: number; theta: number; vega: number } {
  const r = inp.r ?? 0
  const q = inp.q ?? 0
  const t = Math.max(inp.t, 1e-8)
  const iv = Math.max(inp.iv, 1e-8)
  const sqrtT = Math.sqrt(t)
  const d1 = (Math.log(inp.spot / inp.strike) + (r - q + 0.5 * iv * iv) * t) / (iv * sqrtT)
  const d2 = d1 - iv * sqrtT
  const pdf = normPdf(d1)
  const delta =
    type === 'CE' ? Math.exp(-q * t) * normCdf(d1) : Math.exp(-q * t) * (normCdf(d1) - 1)
  const gamma = (Math.exp(-q * t) * pdf) / (inp.spot * iv * sqrtT)
  const vega = inp.spot * Math.exp(-q * t) * pdf * sqrtT * 0.01 // per 1%
  const thetaCommon = -(inp.spot * pdf * iv * Math.exp(-q * t)) / (2 * sqrtT)
  let theta: number
  if (type === 'CE') {
    theta =
      thetaCommon -
      r * inp.strike * Math.exp(-r * t) * normCdf(d2) +
      q * inp.spot * Math.exp(-q * t) * normCdf(d1)
  } else {
    theta =
      thetaCommon +
      r * inp.strike * Math.exp(-r * t) * normCdf(-d2) -
      q * inp.spot * Math.exp(-q * t) * normCdf(-d1)
  }
  return { delta, gamma, theta: theta / 365, vega }
}

```


---

# FILE: frontend\src\lib\strategyTemplates.ts

```ts
/**
 * Strategy templates used by the Strategy Builder's template grid.
 *
 * Each template produces a list of legs with strikes expressed relative to ATM
 * (in "strike steps" — the strike interval in the option chain, e.g. 50 for
 * NIFTY, 100 for BANKNIFTY). The Strategy Builder resolves these offsets
 * against the nearest available strikes in the live option chain when the user
 * picks a template.
 */

import type { OptionType, Side } from './strategyMath'

export type Direction = 'BULLISH' | 'BEARISH' | 'NON_DIRECTIONAL'

export interface TemplateLeg {
  side: Side
  optionType: OptionType
  /** Offset in strike-steps from ATM. 0 = ATM, -1 = one strike ITM for calls, etc. */
  strikeOffset: number
  lots: number
  /**
   * Offset in expiries from the "near" expiry selected in the header.
   * 0 (default) = near expiry. 1 = next expiry in the list (farther out).
   * Used for calendar / diagonal spreads.
   */
  expiryOffset?: number
}

export interface StrategyTemplate {
  id: string
  name: string
  direction: Direction
  description: string
  legs: TemplateLeg[]
  /** Normalised viewBox-(0,0)-(100,40) SVG path for the mini payoff icon. */
  payoffPath: string
}

/**
 * Icons are drawn so that:
 *   x = 0 .. 100 represents the underlying range,
 *   y = 0 (top, max profit) .. 40 (bottom, max loss),
 *   the zero line sits at y = 20.
 */
export const STRATEGY_TEMPLATES: StrategyTemplate[] = [
  // ──────────────────────────────────────────────────────────────────────
  // BULLISH (9)
  // ──────────────────────────────────────────────────────────────────────
  {
    id: 'long_call',
    name: 'Long Call',
    direction: 'BULLISH',
    description: 'Unlimited upside, limited downside. Best for strong bullish view.',
    legs: [{ side: 'BUY', optionType: 'CE', strikeOffset: 0, lots: 1 }],
    payoffPath: 'M0,30 L55,30 L100,2',
  },
  {
    id: 'short_put',
    name: 'Short Put',
    direction: 'BULLISH',
    description: 'Collect premium; profit if price stays above strike.',
    legs: [{ side: 'SELL', optionType: 'PE', strikeOffset: 0, lots: 1 }],
    payoffPath: 'M0,38 L50,10 L100,10',
  },
  {
    id: 'bull_call_spread',
    name: 'Bull Call Spread',
    direction: 'BULLISH',
    description: 'Buy ATM call, sell OTM call. Capped profit & loss.',
    legs: [
      { side: 'BUY', optionType: 'CE', strikeOffset: 0, lots: 1 },
      { side: 'SELL', optionType: 'CE', strikeOffset: 2, lots: 1 },
    ],
    payoffPath: 'M0,28 L50,28 L75,6 L100,6',
  },
  {
    id: 'bull_put_spread',
    name: 'Bull Put Spread',
    direction: 'BULLISH',
    description: 'Sell ATM put, buy OTM put. Net credit trade.',
    legs: [
      { side: 'SELL', optionType: 'PE', strikeOffset: 0, lots: 1 },
      { side: 'BUY', optionType: 'PE', strikeOffset: -2, lots: 1 },
    ],
    payoffPath: 'M0,34 L25,34 L50,10 L100,10',
  },
  {
    id: 'call_ratio_back_spread',
    name: 'Call Ratio Back Spread',
    direction: 'BULLISH',
    description:
      'Sell 1 ATM call, buy 2 OTM calls. Small credit; unlimited upside if market rallies hard.',
    legs: [
      { side: 'SELL', optionType: 'CE', strikeOffset: 0, lots: 1 },
      { side: 'BUY', optionType: 'CE', strikeOffset: 2, lots: 2 },
    ],
    payoffPath: 'M0,18 L40,18 L60,28 L75,22 L100,2',
  },
  {
    id: 'long_synthetic',
    name: 'Long Synthetic',
    direction: 'BULLISH',
    description:
      'Buy ATM call + sell ATM put (same strike). Synthetic long futures — unlimited upside, unlimited downside.',
    legs: [
      { side: 'BUY', optionType: 'CE', strikeOffset: 0, lots: 1 },
      { side: 'SELL', optionType: 'PE', strikeOffset: 0, lots: 1 },
    ],
    payoffPath: 'M0,38 L100,2',
  },
  {
    id: 'range_forward',
    name: 'Range Forward',
    direction: 'BULLISH',
    description:
      'Sell OTM put + buy OTM call. Bullish collar-style structure — limited downside via short put, unlimited upside via long call.',
    legs: [
      { side: 'SELL', optionType: 'PE', strikeOffset: -2, lots: 1 },
      { side: 'BUY', optionType: 'CE', strikeOffset: 2, lots: 1 },
    ],
    payoffPath: 'M0,38 L30,22 L65,22 L100,2',
  },
  {
    id: 'bullish_butterfly',
    name: 'Bullish Butterfly',
    direction: 'BULLISH',
    description:
      'Call butterfly centred above spot — buy 1 ATM CE, sell 2 OTM CE, buy 1 further OTM CE. Max profit if spot rallies to the body strike.',
    legs: [
      { side: 'BUY', optionType: 'CE', strikeOffset: 0, lots: 1 },
      { side: 'SELL', optionType: 'CE', strikeOffset: 2, lots: 2 },
      { side: 'BUY', optionType: 'CE', strikeOffset: 4, lots: 1 },
    ],
    payoffPath: 'M0,26 L55,26 L70,4 L85,26 L100,26',
  },
  {
    id: 'bullish_condor',
    name: 'Bullish Condor',
    direction: 'BULLISH',
    description:
      'Call condor above spot — profit zone sits over a range of higher strikes. Defined risk on both ends.',
    legs: [
      { side: 'BUY', optionType: 'CE', strikeOffset: 0, lots: 1 },
      { side: 'SELL', optionType: 'CE', strikeOffset: 1, lots: 1 },
      { side: 'SELL', optionType: 'CE', strikeOffset: 3, lots: 1 },
      { side: 'BUY', optionType: 'CE', strikeOffset: 4, lots: 1 },
    ],
    payoffPath: 'M0,26 L45,26 L60,6 L80,6 L92,26 L100,26',
  },

  // ──────────────────────────────────────────────────────────────────────
  // BEARISH (9)
  // ──────────────────────────────────────────────────────────────────────
  {
    id: 'short_call',
    name: 'Short Call',
    direction: 'BEARISH',
    description: 'Collect premium; profit if price stays below strike.',
    legs: [{ side: 'SELL', optionType: 'CE', strikeOffset: 0, lots: 1 }],
    payoffPath: 'M0,10 L50,10 L100,38',
  },
  {
    id: 'long_put',
    name: 'Long Put',
    direction: 'BEARISH',
    description: 'Unlimited downside profit, limited loss. Best for strong bearish view.',
    legs: [{ side: 'BUY', optionType: 'PE', strikeOffset: 0, lots: 1 }],
    payoffPath: 'M0,2 L45,30 L100,30',
  },
  {
    id: 'bear_call_spread',
    name: 'Bear Call Spread',
    direction: 'BEARISH',
    description: 'Sell ATM call, buy OTM call. Net credit trade.',
    legs: [
      { side: 'SELL', optionType: 'CE', strikeOffset: 0, lots: 1 },
      { side: 'BUY', optionType: 'CE', strikeOffset: 2, lots: 1 },
    ],
    payoffPath: 'M0,10 L50,10 L75,34 L100,34',
  },
  {
    id: 'bear_put_spread',
    name: 'Bear Put Spread',
    direction: 'BEARISH',
    description: 'Buy ATM put, sell OTM put. Capped profit & loss.',
    legs: [
      { side: 'BUY', optionType: 'PE', strikeOffset: 0, lots: 1 },
      { side: 'SELL', optionType: 'PE', strikeOffset: -2, lots: 1 },
    ],
    payoffPath: 'M0,6 L25,6 L50,28 L100,28',
  },
  {
    id: 'put_ratio_back_spread',
    name: 'Put Ratio Back Spread',
    direction: 'BEARISH',
    description:
      'Sell 1 ATM put, buy 2 OTM puts. Small credit; unlimited downside if market falls hard.',
    legs: [
      { side: 'SELL', optionType: 'PE', strikeOffset: 0, lots: 1 },
      { side: 'BUY', optionType: 'PE', strikeOffset: -2, lots: 2 },
    ],
    payoffPath: 'M0,2 L25,22 L40,28 L60,18 L100,18',
  },
  {
    id: 'short_synthetic',
    name: 'Short Synthetic',
    direction: 'BEARISH',
    description:
      'Sell ATM call + buy ATM put (same strike). Synthetic short futures — unlimited downside profit, unlimited upside loss.',
    legs: [
      { side: 'SELL', optionType: 'CE', strikeOffset: 0, lots: 1 },
      { side: 'BUY', optionType: 'PE', strikeOffset: 0, lots: 1 },
    ],
    payoffPath: 'M0,2 L100,38',
  },
  {
    id: 'risk_reversal',
    name: 'Risk Reversal',
    direction: 'BEARISH',
    description:
      'Buy OTM put + sell OTM call. Bearish collar — profits on downside, unlimited upside loss.',
    legs: [
      { side: 'BUY', optionType: 'PE', strikeOffset: -2, lots: 1 },
      { side: 'SELL', optionType: 'CE', strikeOffset: 2, lots: 1 },
    ],
    payoffPath: 'M0,2 L35,22 L70,22 L100,38',
  },
  {
    id: 'bearish_butterfly',
    name: 'Bearish Butterfly',
    direction: 'BEARISH',
    description:
      'Put butterfly centred below spot — buy 1 ATM PE, sell 2 OTM PE, buy 1 further OTM PE. Max profit if spot falls to the body strike.',
    legs: [
      { side: 'BUY', optionType: 'PE', strikeOffset: 0, lots: 1 },
      { side: 'SELL', optionType: 'PE', strikeOffset: -2, lots: 2 },
      { side: 'BUY', optionType: 'PE', strikeOffset: -4, lots: 1 },
    ],
    payoffPath: 'M0,26 L15,26 L30,4 L45,26 L100,26',
  },
  {
    id: 'bearish_condor',
    name: 'Bearish Condor',
    direction: 'BEARISH',
    description:
      'Put condor below spot — profit zone sits over a range of lower strikes. Defined risk on both ends.',
    legs: [
      { side: 'BUY', optionType: 'PE', strikeOffset: 0, lots: 1 },
      { side: 'SELL', optionType: 'PE', strikeOffset: -1, lots: 1 },
      { side: 'SELL', optionType: 'PE', strikeOffset: -3, lots: 1 },
      { side: 'BUY', optionType: 'PE', strikeOffset: -4, lots: 1 },
    ],
    payoffPath: 'M0,26 L8,26 L20,6 L40,6 L55,26 L100,26',
  },

  // ──────────────────────────────────────────────────────────────────────
  // NON-DIRECTIONAL (20)
  // ──────────────────────────────────────────────────────────────────────
  {
    id: 'long_straddle',
    name: 'Long Straddle',
    direction: 'NON_DIRECTIONAL',
    description: 'Buy ATM call + put. Profits from a large move either way.',
    legs: [
      { side: 'BUY', optionType: 'CE', strikeOffset: 0, lots: 1 },
      { side: 'BUY', optionType: 'PE', strikeOffset: 0, lots: 1 },
    ],
    payoffPath: 'M0,4 L50,30 L100,4',
  },
  {
    id: 'short_straddle',
    name: 'Short Straddle',
    direction: 'NON_DIRECTIONAL',
    description: 'Sell ATM call + put. Profits if price stays pinned near strike.',
    legs: [
      { side: 'SELL', optionType: 'CE', strikeOffset: 0, lots: 1 },
      { side: 'SELL', optionType: 'PE', strikeOffset: 0, lots: 1 },
    ],
    payoffPath: 'M0,36 L50,10 L100,36',
  },
  {
    id: 'long_strangle',
    name: 'Long Strangle',
    direction: 'NON_DIRECTIONAL',
    description: 'Buy OTM call + OTM put. Cheaper than straddle; needs bigger move.',
    legs: [
      { side: 'BUY', optionType: 'PE', strikeOffset: -2, lots: 1 },
      { side: 'BUY', optionType: 'CE', strikeOffset: 2, lots: 1 },
    ],
    payoffPath: 'M0,6 L30,26 L70,26 L100,6',
  },
  {
    id: 'short_strangle',
    name: 'Short Strangle',
    direction: 'NON_DIRECTIONAL',
    description: 'Sell OTM call + OTM put. Wider profit zone than short straddle.',
    legs: [
      { side: 'SELL', optionType: 'PE', strikeOffset: -2, lots: 1 },
      { side: 'SELL', optionType: 'CE', strikeOffset: 2, lots: 1 },
    ],
    payoffPath: 'M0,34 L30,14 L70,14 L100,34',
  },
  {
    id: 'jade_lizard',
    name: 'Jade Lizard',
    direction: 'NON_DIRECTIONAL',
    description:
      'Sell OTM put + short OTM call spread. No risk on upside if credit exceeds call-spread width.',
    legs: [
      { side: 'SELL', optionType: 'PE', strikeOffset: -2, lots: 1 },
      { side: 'SELL', optionType: 'CE', strikeOffset: 2, lots: 1 },
      { side: 'BUY', optionType: 'CE', strikeOffset: 4, lots: 1 },
    ],
    payoffPath: 'M0,34 L20,34 L35,14 L75,14 L90,20 L100,20',
  },
  {
    id: 'reverse_jade_lizard',
    name: 'Reverse Jade Lizard',
    direction: 'NON_DIRECTIONAL',
    description:
      'Sell OTM call + short OTM put spread. No risk on downside if credit exceeds put-spread width.',
    legs: [
      { side: 'SELL', optionType: 'CE', strikeOffset: 2, lots: 1 },
      { side: 'SELL', optionType: 'PE', strikeOffset: -2, lots: 1 },
      { side: 'BUY', optionType: 'PE', strikeOffset: -4, lots: 1 },
    ],
    payoffPath: 'M0,20 L10,20 L25,14 L65,14 L80,34 L100,34',
  },
  {
    id: 'call_ratio_spread',
    name: 'Call Ratio Spread',
    direction: 'NON_DIRECTIONAL',
    description:
      'Buy 1 ATM call, sell 2 OTM calls. Peak profit at short strike; unlimited upside loss above.',
    legs: [
      { side: 'BUY', optionType: 'CE', strikeOffset: 0, lots: 1 },
      { side: 'SELL', optionType: 'CE', strikeOffset: 2, lots: 2 },
    ],
    payoffPath: 'M0,28 L50,28 L75,4 L100,38',
  },
  {
    id: 'put_ratio_spread',
    name: 'Put Ratio Spread',
    direction: 'NON_DIRECTIONAL',
    description:
      'Buy 1 ATM put, sell 2 OTM puts. Peak profit at short strike; unlimited downside loss below.',
    legs: [
      { side: 'BUY', optionType: 'PE', strikeOffset: 0, lots: 1 },
      { side: 'SELL', optionType: 'PE', strikeOffset: -2, lots: 2 },
    ],
    payoffPath: 'M0,38 L25,4 L50,28 L100,28',
  },
  {
    id: 'batman_strategy',
    name: 'Batman Strategy',
    direction: 'NON_DIRECTIONAL',
    description:
      'Call ratio spread (1×2) above + Put ratio spread (1×2) below. Two-eared "Batman" profile — small profit peaks at the short strikes, with unlimited loss on both wings due to the extra short legs.',
    legs: [
      // ── CE side: call ratio spread — long 1, short 2 ──
      { side: 'BUY', optionType: 'CE', strikeOffset: 10, lots: 1 },
      { side: 'SELL', optionType: 'CE', strikeOffset: 15, lots: 2 },
      // ── PE side: put ratio spread — long 1, short 2 ──
      { side: 'BUY', optionType: 'PE', strikeOffset: -10, lots: 1 },
      { side: 'SELL', optionType: 'PE', strikeOffset: -15, lots: 2 },
    ],
    payoffPath: 'M0,38 L15,30 L30,12 L45,22 L55,22 L70,12 L85,30 L100,38',
  },
  {
    id: 'long_iron_fly',
    name: 'Long Iron Fly',
    direction: 'NON_DIRECTIONAL',
    description: 'Short ATM straddle + long OTM wings. Max profit pinned at ATM.',
    legs: [
      { side: 'BUY', optionType: 'PE', strikeOffset: -2, lots: 1 },
      { side: 'SELL', optionType: 'PE', strikeOffset: 0, lots: 1 },
      { side: 'SELL', optionType: 'CE', strikeOffset: 0, lots: 1 },
      { side: 'BUY', optionType: 'CE', strikeOffset: 2, lots: 1 },
    ],
    payoffPath: 'M0,30 L25,30 L50,6 L75,30 L100,30',
  },
  {
    id: 'short_iron_fly',
    name: 'Short Iron Fly',
    direction: 'NON_DIRECTIONAL',
    description:
      'Long ATM straddle + short OTM wings. Max profit on a big move either way; max loss pinned at ATM.',
    legs: [
      { side: 'SELL', optionType: 'PE', strikeOffset: -2, lots: 1 },
      { side: 'BUY', optionType: 'PE', strikeOffset: 0, lots: 1 },
      { side: 'BUY', optionType: 'CE', strikeOffset: 0, lots: 1 },
      { side: 'SELL', optionType: 'CE', strikeOffset: 2, lots: 1 },
    ],
    payoffPath: 'M0,10 L25,10 L50,34 L75,10 L100,10',
  },
  {
    id: 'double_fly',
    name: 'Double Fly',
    direction: 'NON_DIRECTIONAL',
    description:
      'Two iron butterflies — one centred below spot, one above. Eight legs total: short straddle at each body strike, long CE wing above and long PE wing below. Two profit peaks at the body strikes, defined risk on both ends.',
    legs: [
      // ── CE legs (grouped first) ──
      // Lower iron fly body @ ATM − 8, CE wing @ ATM − 4 (4 strikes above body)
      { side: 'SELL', optionType: 'CE', strikeOffset: -8, lots: 1 },
      { side: 'BUY', optionType: 'CE', strikeOffset: -4, lots: 1 },
      // Upper iron fly body @ ATM + 8, CE wing @ ATM + 12 (4 strikes above body)
      { side: 'SELL', optionType: 'CE', strikeOffset: 8, lots: 1 },
      { side: 'BUY', optionType: 'CE', strikeOffset: 12, lots: 1 },
      // ── PE legs ──
      // Lower iron fly PE wing @ ATM − 12 (4 strikes below body), body @ ATM − 8
      { side: 'BUY', optionType: 'PE', strikeOffset: -12, lots: 1 },
      { side: 'SELL', optionType: 'PE', strikeOffset: -8, lots: 1 },
      // Upper iron fly PE wing @ ATM + 4 (4 strikes below body), body @ ATM + 8
      { side: 'BUY', optionType: 'PE', strikeOffset: 4, lots: 1 },
      { side: 'SELL', optionType: 'PE', strikeOffset: 8, lots: 1 },
    ],
    payoffPath: 'M0,30 L10,30 L20,8 L35,30 L65,30 L80,8 L90,30 L100,30',
  },
  {
    id: 'long_iron_condor',
    name: 'Long Iron Condor',
    direction: 'NON_DIRECTIONAL',
    description: 'Bull put spread + bear call spread. Defined-risk range play.',
    legs: [
      { side: 'BUY', optionType: 'PE', strikeOffset: -4, lots: 1 },
      { side: 'SELL', optionType: 'PE', strikeOffset: -2, lots: 1 },
      { side: 'SELL', optionType: 'CE', strikeOffset: 2, lots: 1 },
      { side: 'BUY', optionType: 'CE', strikeOffset: 4, lots: 1 },
    ],
    payoffPath: 'M0,30 L20,30 L35,14 L65,14 L80,30 L100,30',
  },
  {
    id: 'short_iron_condor',
    name: 'Short Iron Condor',
    direction: 'NON_DIRECTIONAL',
    description:
      'Reverse of long iron condor — long wings pay off on a big move either way, short body caps upside if spot pins in the middle.',
    legs: [
      { side: 'SELL', optionType: 'PE', strikeOffset: -4, lots: 1 },
      { side: 'BUY', optionType: 'PE', strikeOffset: -2, lots: 1 },
      { side: 'BUY', optionType: 'CE', strikeOffset: 2, lots: 1 },
      { side: 'SELL', optionType: 'CE', strikeOffset: 4, lots: 1 },
    ],
    payoffPath: 'M0,10 L20,10 L35,26 L65,26 L80,10 L100,10',
  },
  {
    id: 'double_condor',
    name: 'Double Condor',
    direction: 'NON_DIRECTIONAL',
    description:
      'Call condor + put condor at different strikes. Two wide profit plateaus on either side of spot.',
    legs: [
      { side: 'BUY', optionType: 'PE', strikeOffset: -5, lots: 1 },
      { side: 'SELL', optionType: 'PE', strikeOffset: -4, lots: 1 },
      { side: 'SELL', optionType: 'PE', strikeOffset: -2, lots: 1 },
      { side: 'BUY', optionType: 'PE', strikeOffset: -1, lots: 1 },
      { side: 'BUY', optionType: 'CE', strikeOffset: 1, lots: 1 },
      { side: 'SELL', optionType: 'CE', strikeOffset: 2, lots: 1 },
      { side: 'SELL', optionType: 'CE', strikeOffset: 4, lots: 1 },
      { side: 'BUY', optionType: 'CE', strikeOffset: 5, lots: 1 },
    ],
    payoffPath: 'M0,30 L15,30 L25,12 L40,12 L50,30 L60,30 L70,12 L85,12 L95,30 L100,30',
  },
  {
    id: 'call_calendar',
    name: 'Call Calendar',
    direction: 'NON_DIRECTIONAL',
    description:
      'Sell near-expiry ATM CE, buy far-expiry ATM CE (same strike). Profits from near-leg theta while the long keeps time value.',
    legs: [
      { side: 'SELL', optionType: 'CE', strikeOffset: 0, lots: 1, expiryOffset: 0 },
      { side: 'BUY', optionType: 'CE', strikeOffset: 0, lots: 1, expiryOffset: 1 },
    ],
    // Asymmetric — steep left-side rise to a sharp peak, gentle fall off
    // to the right (calls lose value as spot drops; the far leg retains
    // value as spot rises so right-side decay is slower).
    payoffPath: 'M0,32 L25,28 L42,6 L65,18 L100,28',
  },
  {
    id: 'put_calendar',
    name: 'Put Calendar',
    direction: 'NON_DIRECTIONAL',
    description:
      'Sell near-expiry ATM PE, buy far-expiry ATM PE (same strike). Put-side equivalent of the call calendar.',
    legs: [
      { side: 'SELL', optionType: 'PE', strikeOffset: 0, lots: 1, expiryOffset: 0 },
      { side: 'BUY', optionType: 'PE', strikeOffset: 0, lots: 1, expiryOffset: 1 },
    ],
    // Mirror of the call calendar — gentle left-side rise, steep fall on
    // the right (puts lose value as spot rises; the far leg retains value
    // as spot falls).
    payoffPath: 'M0,28 L35,18 L58,6 L75,28 L100,32',
  },
  {
    id: 'diagonal_calendar',
    name: 'Diagonal Calendar',
    direction: 'NON_DIRECTIONAL',
    description:
      'Calendar with different strikes — sell near ATM CE, buy far OTM CE. Adds a mild directional tilt to a calendar.',
    legs: [
      { side: 'SELL', optionType: 'CE', strikeOffset: 0, lots: 1, expiryOffset: 0 },
      { side: 'BUY', optionType: 'CE', strikeOffset: 2, lots: 1, expiryOffset: 1 },
    ],
    // Diagonals show a widened peak — two small humps and a plateau
    // between the near-leg strike and the far-leg strike.
    payoffPath: 'M0,32 L20,28 L38,14 L50,10 L62,14 L78,22 L100,28',
  },
  {
    id: 'call_butterfly',
    name: 'Call Butterfly',
    direction: 'NON_DIRECTIONAL',
    description: 'Long call butterfly centred at ATM. Max profit if spot pins at the body strike.',
    legs: [
      { side: 'BUY', optionType: 'CE', strikeOffset: -2, lots: 1 },
      { side: 'SELL', optionType: 'CE', strikeOffset: 0, lots: 2 },
      { side: 'BUY', optionType: 'CE', strikeOffset: 2, lots: 1 },
    ],
    payoffPath: 'M0,30 L35,30 L50,6 L65,30 L100,30',
  },
  {
    id: 'put_butterfly',
    name: 'Put Butterfly',
    direction: 'NON_DIRECTIONAL',
    description: 'Long put butterfly centred at ATM. Put-side mirror of the call butterfly.',
    legs: [
      { side: 'BUY', optionType: 'PE', strikeOffset: 2, lots: 1 },
      { side: 'SELL', optionType: 'PE', strikeOffset: 0, lots: 2 },
      { side: 'BUY', optionType: 'PE', strikeOffset: -2, lots: 1 },
    ],
    payoffPath: 'M0,30 L35,30 L50,6 L65,30 L100,30',
  },
]

export function templatesByDirection(direction: Direction | 'ALL'): StrategyTemplate[] {
  if (direction === 'ALL') return STRATEGY_TEMPLATES
  return STRATEGY_TEMPLATES.filter((t) => t.direction === direction)
}

```


---

# FILE: frontend\src\lib\utils.ts

```ts
import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Sanitize a value for CSV export to prevent formula injection.
 * Prefixes dangerous characters (=, +, -, @) with a single quote.
 */
export function sanitizeCSV(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return ''
  const str = String(value)
  // Prefix dangerous formula characters with a single quote
  if (/^[=+\-@]/.test(str)) {
    return `'${str}`
  }
  // Escape quotes and wrap in quotes if contains comma
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    return `"${str.replace(/"/g, '""')}"`
  }
  return str
}

/**
 * Returns a currency formatter bound to the active broker.
 * - deltaexchange → USD ($)
 * - all other brokers  → INR (₹)
 */
export function makeFormatCurrency(broker?: string | null): (value: number) => string {
  const isUSD = broker === 'deltaexchange'
  return (value: number) =>
    isUSD
      ? new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 2,
        }).format(value)
      : new Intl.NumberFormat('en-IN', {
          style: 'currency',
          currency: 'INR',
          minimumFractionDigits: 2,
        }).format(value)
}

```
