# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\frontend\src\hooks



---

# FILE: frontend\src\hooks\use-mobile.ts

```ts
import * as React from 'react'

const MOBILE_BREAKPOINT = 768

export function useIsMobile() {
  const [isMobile, setIsMobile] = React.useState<boolean | undefined>(undefined)

  React.useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`)
    const onChange = () => {
      setIsMobile(window.innerWidth < MOBILE_BREAKPOINT)
    }
    mql.addEventListener('change', onChange)
    setIsMobile(window.innerWidth < MOBILE_BREAKPOINT)
    return () => mql.removeEventListener('change', onChange)
  }, [])

  return !!isMobile
}

```


---

# FILE: frontend\src\hooks\useLivePrice.ts

```ts
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { type QuotesData, tradingApi } from '@/api/trading'
import { useMarketData } from '@/hooks/useMarketData'
import { useMarketStatus } from '@/hooks/useMarketStatus'
import { usePageVisibility } from '@/hooks/usePageVisibility'
import { useAuthStore } from '@/stores/authStore'

/**
 * Base interface for items that can have live price data
 */
export interface PriceableItem {
  symbol: string
  exchange: string
  ltp?: number
  pnl?: number
  pnlpercent?: number
  quantity?: number
  average_price?: number
  today_realized_pnl?: number // Sandbox: today's realized P&L from closed partial trades
  lot_size?: number // Contract multiplier (e.g. 0.01 for Delta Exchange ETHUSD.P)
}

/**
 * Configuration options for useLivePrice hook
 */
export interface UseLivePriceOptions {
  /** Whether the hook is enabled (default: true) */
  enabled?: boolean
  /** Time in ms after which WebSocket data is considered stale (default: 5000) */
  staleThreshold?: number
  /** Whether to use MultiQuotes API as fallback when WebSocket unavailable (default: true) */
  useMultiQuotesFallback?: boolean
  /** Interval in ms to refresh MultiQuotes data (default: 30000) */
  multiQuotesRefreshInterval?: number
  /** Pause WebSocket and polling when tab is hidden (default: true) */
  pauseWhenHidden?: boolean
  /** Time in ms to wait before pausing when hidden (default: 5000) */
  pauseDelay?: number
}

/**
 * Return type for useLivePrice hook
 */
export interface UseLivePriceResult<T extends PriceableItem> {
  /** Enhanced items with real-time LTP and recalculated PnL */
  data: T[]
  /** Whether real-time data is available (WebSocket connected AND market open) */
  isLive: boolean
  /** Whether WebSocket is connected */
  isConnected: boolean
  /** Whether WebSocket is paused due to tab being hidden */
  isPaused: boolean
  /** Whether using REST API fallback instead of WebSocket */
  isFallbackMode: boolean
  /** Whether any market is currently open */
  isAnyMarketOpen: boolean
  /** Map of MultiQuotes data for external access if needed */
  multiQuotes: Map<string, QuotesData>
  /** Manually refresh MultiQuotes data */
  refreshMultiQuotes: () => Promise<void>
}

/**
 * Centralized hook for real-time price data with automatic fallback.
 *
 * Priority chain:
 * 1. WebSocket LTP (when market is open and data is fresh)
 * 2. MultiQuotes API (fallback when WebSocket unavailable)
 * 3. REST API data (baseline from initial fetch)
 *
 * @example
 * ```tsx
 * const { data: enhancedHoldings, isLive } = useLivePrice(holdings, {
 *   enabled: holdings.length > 0,
 *   useMultiQuotesFallback: true,
 * });
 * ```
 */
export function useLivePrice<T extends PriceableItem>(
  items: T[],
  options: UseLivePriceOptions = {}
): UseLivePriceResult<T> {
  const {
    enabled = true,
    staleThreshold = 5000,
    useMultiQuotesFallback = true,
    multiQuotesRefreshInterval = 30000,
    pauseWhenHidden = true,
  } = options

  const { apiKey } = useAuthStore()
  const { isMarketOpen, isAnyMarketOpen } = useMarketStatus()
  const { isVisible, wasHidden, timeSinceHidden } = usePageVisibility()
  const anyMarketOpen = isAnyMarketOpen()

  // State for MultiQuotes fallback data
  const [multiQuotes, setMultiQuotes] = useState<Map<string, QuotesData>>(new Map())

  // Track last fetch time for visibility-aware refresh
  const lastFetchRef = useRef<number>(Date.now())

  // Extract symbols for WebSocket subscription
  const symbols = useMemo(
    () =>
      items.map((item) => ({
        symbol: item.symbol,
        exchange: item.exchange,
      })),
    [items]
  )

  // WebSocket market data - connect when enabled, with visibility awareness
  const {
    data: marketData,
    isConnected: wsConnected,
    isPaused: wsPaused,
    isFallbackMode,
  } = useMarketData({
    symbols,
    mode: 'LTP',
    enabled: enabled && items.length > 0,
  })

  // Effective live status
  const isLive = wsConnected && anyMarketOpen && !wsPaused

  /**
   * Fetch MultiQuotes data from API
   */
  const fetchMultiQuotes = useCallback(async () => {
    if (!apiKey || items.length === 0 || !useMultiQuotesFallback) return

    try {
      const symbolsList = items.map((item) => ({
        symbol: item.symbol,
        exchange: item.exchange,
      }))

      const response = await tradingApi.getMultiQuotes(apiKey, symbolsList)

      if (response.status === 'success' && response.results) {
        const quotesMap = new Map<string, QuotesData>()
        response.results.forEach((result) => {
          const key = `${result.exchange}:${result.symbol}`
          if (result.data) {
            quotesMap.set(key, result.data)
          }
        })
        setMultiQuotes(quotesMap)
      }
    } catch {
      // Silently fail - MultiQuotes is a fallback mechanism
    }
  }, [apiKey, items, useMultiQuotesFallback])

  // Fetch MultiQuotes on mount and when items change
  // Visibility-aware: pause polling when tab is hidden
  useEffect(() => {
    if (!enabled || items.length === 0 || !useMultiQuotesFallback) return

    // Don't poll when hidden (if pauseWhenHidden is true)
    if (pauseWhenHidden && !isVisible) return

    // Initial fetch
    fetchMultiQuotes()
    lastFetchRef.current = Date.now()

    // Set up periodic refresh
    const interval = setInterval(() => {
      fetchMultiQuotes()
      lastFetchRef.current = Date.now()
    }, multiQuotesRefreshInterval)

    return () => clearInterval(interval)
  }, [
    enabled,
    items.length,
    useMultiQuotesFallback,
    fetchMultiQuotes,
    multiQuotesRefreshInterval,
    pauseWhenHidden,
    isVisible,
  ])

  // Refresh MultiQuotes immediately when tab becomes visible after being hidden
  useEffect(() => {
    if (!wasHidden || !isVisible || !useMultiQuotesFallback || !enabled) return

    // If we were hidden for more than the refresh interval, fetch immediately
    if (timeSinceHidden > multiQuotesRefreshInterval) {
      fetchMultiQuotes()
      lastFetchRef.current = Date.now()
    }
  }, [
    wasHidden,
    isVisible,
    timeSinceHidden,
    multiQuotesRefreshInterval,
    useMultiQuotesFallback,
    enabled,
    fetchMultiQuotes,
  ])

  /**
   * Enhance items with real-time LTP and recalculated P&L
   * Priority: WebSocket (fresh + market open) → MultiQuotes → REST API
   *
   * For open positions (qty != 0): P&L and P&L% are recalculated using live LTP
   * For closed positions (qty = 0): P&L and P&L% from REST API (realized values)
   */
  const enhancedData = useMemo(() => {
    return items.map((item) => {
      const key = `${item.exchange}:${item.symbol}`
      const wsData = marketData.get(key)
      const mqData = multiQuotes.get(key)

      const qty = item.quantity || 0
      const avgPrice = item.average_price || 0

      // Check if market is open for this exchange
      const exchangeMarketOpen = isMarketOpen(item.exchange)

      // Check if WebSocket LTP is fresh AND market is open
      const hasWsData =
        exchangeMarketOpen &&
        wsData?.data?.ltp &&
        wsData.lastUpdate &&
        Date.now() - wsData.lastUpdate < staleThreshold

      // Check if we have MultiQuotes data (fallback when WebSocket not available)
      const hasMqData = !hasWsData && mqData?.ltp

      // Determine the best available LTP source
      let currentLtp: number | undefined
      let dataSource: 'websocket' | 'multiquotes' | 'rest' = 'rest'

      if (hasWsData && wsData?.data?.ltp) {
        currentLtp = wsData.data.ltp
        dataSource = 'websocket'
      } else if (hasMqData && mqData?.ltp) {
        currentLtp = mqData.ltp
        dataSource = 'multiquotes'
      } else {
        currentLtp = item.ltp
        dataSource = 'rest'
      }

      // For closed positions (qty=0), preserve ALL REST API values including LTP
      // This ensures P&L% calculation remains stable (realized values don't change)
      if (qty === 0) {
        return {
          ...item,
          // Keep item.ltp from REST API - don't update with live data
          // This prevents P&L% from recalculating with changing LTP
          _dataSource: 'rest',
        } as T & { _dataSource: string }
      }

      // For open positions: recalculate P&L and P&L% using live LTP
      // This ensures real-time updates as LTP changes
      let calculatedPnl = item.pnl || 0
      let calculatedPnlPercent = item.pnlpercent || 0

      // Get today's realized P&L if available (from sandbox mode)
      // This ensures cumulative P&L (realized + unrealized) is shown correctly
      const todayRealizedPnl = item.today_realized_pnl || 0

      if (currentLtp && avgPrice > 0) {
        // Contract multiplier: e.g. 0.01 for Delta Exchange ETHUSD.P (1 lot = 0.01 ETH)
        // Defaults to 1 for all standard brokers where qty is already in underlying units
        const lotSize = item.lot_size ?? 1

        // Calculate unrealized P&L based on position direction
        // Long (qty > 0): profit when ltp > avgPrice
        // Short (qty < 0): profit when ltp < avgPrice
        let unrealizedPnl: number
        if (qty > 0) {
          unrealizedPnl = (currentLtp - avgPrice) * qty * lotSize
        } else {
          unrealizedPnl = (avgPrice - currentLtp) * Math.abs(qty) * lotSize
        }

        // Total P&L = today's realized (from partial closes) + current unrealized
        calculatedPnl = todayRealizedPnl + unrealizedPnl

        // P&L% based on total P&L and investment
        const investment = Math.abs(avgPrice * qty)
        calculatedPnlPercent = investment > 0 ? (calculatedPnl / investment) * 100 : 0
      }

      return {
        ...item,
        ltp: currentLtp,
        pnl: calculatedPnl,
        pnlpercent: calculatedPnlPercent,
        _dataSource: dataSource,
      } as T & { _dataSource: string }
    })
  }, [items, marketData, multiQuotes, isMarketOpen, staleThreshold])

  return {
    data: enhancedData,
    isLive,
    isConnected: wsConnected,
    isPaused: wsPaused,
    isFallbackMode,
    isAnyMarketOpen: anyMarketOpen,
    multiQuotes,
    refreshMultiQuotes: fetchMultiQuotes,
  }
}

/**
 * Calculate aggregated stats from items with live price data
 */
export function calculateLiveStats<T extends PriceableItem>(
  items: T[],
  originalStats?: {
    totalholdingvalue?: number
    totalinvvalue?: number
    totalprofitandloss?: number
    totalpnlpercentage?: number
  }
) {
  if (!originalStats) return null

  let totalPnl = 0
  let totalInvestment = 0
  let totalHoldingValue = 0

  items.forEach((item) => {
    totalPnl += item.pnl || 0
    const avgPrice = item.average_price || 0
    const qty = item.quantity || 0
    const ltp = item.ltp || avgPrice
    totalInvestment += avgPrice * qty
    totalHoldingValue += ltp * qty
  })

  const totalPnlPercent = totalInvestment > 0 ? (totalPnl / totalInvestment) * 100 : 0

  return {
    ...originalStats,
    totalholdingvalue: totalHoldingValue,
    totalinvvalue: totalInvestment,
    totalprofitandloss: totalPnl,
    totalpnlpercentage: totalPnlPercent,
  }
}

```


---

# FILE: frontend\src\hooks\useLiveQuote.ts

```ts
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { type DepthData, type DepthLevel, type QuotesData, tradingApi } from '@/api/trading'
import { useMarketData } from '@/hooks/useMarketData'
import { useMarketStatus } from '@/hooks/useMarketStatus'
import { useAuthStore } from '@/stores/authStore'

/**
 * Depth data in normalized format (used by both WebSocket and REST)
 */
export interface NormalizedDepth {
  buy: DepthLevel[]
  sell: DepthLevel[]
}

/**
 * Combined quote and depth data
 */
export interface LiveQuoteData {
  ltp?: number
  open?: number
  high?: number
  low?: number
  close?: number
  volume?: number
  oi?: number
  change?: number
  changePercent?: number
  bidPrice?: number
  askPrice?: number
  bidSize?: number
  askSize?: number
  depth?: NormalizedDepth
}

/**
 * Configuration options for useLiveQuote hook
 */
export interface UseLiveQuoteOptions {
  /** Whether the hook is enabled (default: true) */
  enabled?: boolean
  /** WebSocket subscription mode: 'LTP', 'Quote', or 'Depth' (default: 'Depth') */
  mode?: 'LTP' | 'Quote' | 'Depth'
  /** Whether to fetch REST quotes as fallback (default: true) */
  useQuotesFallback?: boolean
  /** Whether to fetch REST depth as fallback (default: true) */
  useDepthFallback?: boolean
  /** Time in ms after which WebSocket data is considered stale (default: 5000) */
  staleThreshold?: number
  /** Interval in ms to refresh REST data (default: 30000) */
  refreshInterval?: number
  /** Pause when tab is hidden (default: true) */
  pauseWhenHidden?: boolean
}

/**
 * Return type for useLiveQuote hook
 */
export interface UseLiveQuoteResult {
  /** Combined quote and depth data */
  data: LiveQuoteData
  /** Whether real-time data is available (WebSocket connected AND market open) */
  isLive: boolean
  /** Whether WebSocket is connected */
  isConnected: boolean
  /** Whether data is being loaded */
  isLoading: boolean
  /** Whether WebSocket is paused due to tab being hidden */
  isPaused: boolean
  /** Whether using REST API fallback instead of WebSocket */
  isFallbackMode: boolean
  /** Data source: 'websocket', 'rest', or 'none' */
  dataSource: 'websocket' | 'rest' | 'none'
  /** Manually refresh REST data */
  refresh: () => Promise<void>
}

/**
 * Centralized hook for real-time quote and depth data with automatic REST fallback.
 *
 * Similar to useLivePrice but for single symbol with full quote + depth support.
 * Use this for PlaceOrderDialog, symbol details, or anywhere you need live market data.
 *
 * Priority chain:
 * 1. WebSocket data (when market is open and data is fresh)
 * 2. REST API data (fallback when WebSocket unavailable)
 *
 * @example
 * ```tsx
 * const { data, isLive, isLoading } = useLiveQuote('RELIANCE', 'NSE', {
 *   enabled: dialogOpen,
 *   mode: 'Depth',
 * });
 *
 * // Access data
 * console.log(data.ltp, data.bidPrice, data.depth?.buy);
 * ```
 */
export function useLiveQuote(
  symbol: string,
  exchange: string,
  options: UseLiveQuoteOptions = {}
): UseLiveQuoteResult {
  const {
    enabled = true,
    mode = 'Depth',
    useQuotesFallback = true,
    useDepthFallback = true,
    staleThreshold = 5000,
    refreshInterval = 30000,
  } = options

  const { apiKey } = useAuthStore()
  const { isMarketOpen } = useMarketStatus()

  // REST fallback state
  const [restQuotes, setRestQuotes] = useState<QuotesData | null>(null)
  const [restDepth, setRestDepth] = useState<DepthData | null>(null)
  const [isLoadingRest, setIsLoadingRest] = useState(false)

  // Track last fetch time
  const lastFetchRef = useRef<number>(0)

  // Check if we have valid symbol/exchange
  const hasSymbol = !!symbol && !!exchange

  // WebSocket subscription
  const symbols = useMemo(
    () => (hasSymbol ? [{ symbol, exchange }] : []),
    [symbol, exchange, hasSymbol]
  )

  const {
    data: marketData,
    isConnected: wsConnected,
    isPaused: wsPaused,
    isFallbackMode,
  } = useMarketData({
    symbols,
    mode,
    enabled: enabled && hasSymbol,
  })

  const wsData = marketData.get(`${exchange}:${symbol}`)?.data
  const wsLastUpdate = marketData.get(`${exchange}:${symbol}`)?.lastUpdate

  // Check if market is open for this exchange
  const marketOpen = isMarketOpen(exchange)

  // Check if WebSocket data is fresh
  const hasWsData = !!(
    wsConnected &&
    wsData &&
    wsLastUpdate &&
    Date.now() - wsLastUpdate < staleThreshold
  )

  // Effective live status (WebSocket connected, data fresh, market open)
  const isLive = hasWsData && marketOpen && !wsPaused

  /**
   * Fetch REST data (quotes and/or depth)
   */
  const fetchRestData = useCallback(async () => {
    if (!apiKey || !hasSymbol) return

    setIsLoadingRest(true)
    try {
      // Fetch quotes and depth in parallel
      const promises: Promise<void>[] = []

      if (useQuotesFallback) {
        promises.push(
          tradingApi
            .getQuotes(apiKey, symbol, exchange)
            .then((response) => {
              if (response.status === 'success' && response.data) {
                setRestQuotes(response.data)
              }
            })
            .catch(() => {})
        )
      }

      if (useDepthFallback && mode === 'Depth') {
        promises.push(
          tradingApi
            .getDepth(apiKey, symbol, exchange)
            .then((response) => {
              if (response.status === 'success' && response.data) {
                setRestDepth(response.data)
              }
            })
            .catch(() => {})
        )
      }

      await Promise.all(promises)
      lastFetchRef.current = Date.now()
    } finally {
      setIsLoadingRest(false)
    }
  }, [apiKey, symbol, exchange, hasSymbol, useQuotesFallback, useDepthFallback, mode])

  // Fetch on mount and when symbol changes
  // Use refs to track current state and avoid stale closures in intervals
  const enabledRef = useRef(enabled)
  const hasSymbolRef = useRef(hasSymbol)
  const fetchRestDataRef = useRef(fetchRestData)

  // Keep refs in sync with latest values
  useEffect(() => {
    enabledRef.current = enabled
    hasSymbolRef.current = hasSymbol
    fetchRestDataRef.current = fetchRestData
  }, [enabled, hasSymbol, fetchRestData])

  useEffect(() => {
    if (!enabled || !hasSymbol) return

    // Initial fetch - use ref to ensure we have the latest function
    fetchRestDataRef.current()

    // Set up periodic refresh
    const interval = setInterval(() => {
      // Check current enabled state before fetching
      if (enabledRef.current && hasSymbolRef.current) {
        fetchRestDataRef.current()
      }
    }, refreshInterval)

    return () => clearInterval(interval)
    // Only depend on stable values that should trigger new interval setup
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, hasSymbol, symbol, exchange, refreshInterval])

  // Reset state when symbol changes
  useEffect(() => {
    setRestQuotes(null)
    setRestDepth(null)
  }, [symbol, exchange])

  // Convert REST depth format to normalized format
  const restDepthNormalized: NormalizedDepth | undefined = useMemo(() => {
    if (!restDepth) return undefined
    return {
      buy: restDepth.bids.map((level) => ({ price: level.price, quantity: level.quantity })),
      sell: restDepth.asks.map((level) => ({ price: level.price, quantity: level.quantity })),
    }
  }, [restDepth])

  // Merge WebSocket and REST data
  const mergedData: LiveQuoteData = useMemo(() => {
    // Determine best depth source
    const depth = wsData?.depth ?? restDepthNormalized

    // Determine best bid/ask from depth or quotes
    const bidPrice =
      wsData?.depth?.buy?.[0]?.price ??
      restDepthNormalized?.buy?.[0]?.price ??
      wsData?.bid_price ??
      restQuotes?.bid
    const askPrice =
      wsData?.depth?.sell?.[0]?.price ??
      restDepthNormalized?.sell?.[0]?.price ??
      wsData?.ask_price ??
      restQuotes?.ask
    const bidSize =
      wsData?.depth?.buy?.[0]?.quantity ??
      restDepthNormalized?.buy?.[0]?.quantity ??
      wsData?.bid_size
    const askSize =
      wsData?.depth?.sell?.[0]?.quantity ??
      restDepthNormalized?.sell?.[0]?.quantity ??
      wsData?.ask_size

    // Merge all data with priority: WebSocket > REST depth > REST quotes
    return {
      ltp: wsData?.ltp ?? restDepth?.ltp ?? restQuotes?.ltp,
      open: wsData?.open ?? restDepth?.open ?? restQuotes?.open,
      high: wsData?.high ?? restDepth?.high ?? restQuotes?.high,
      low: wsData?.low ?? restDepth?.low ?? restQuotes?.low,
      close: wsData?.close ?? restDepth?.prev_close ?? restQuotes?.prev_close,
      volume: wsData?.volume ?? restDepth?.volume ?? restQuotes?.volume,
      oi: restDepth?.oi ?? restQuotes?.oi,
      change: wsData?.change,
      changePercent: wsData?.change_percent,
      bidPrice,
      askPrice,
      bidSize,
      askSize,
      depth,
    }
  }, [wsData, restQuotes, restDepth, restDepthNormalized])

  // Calculate change if not available from WebSocket
  const dataWithChange: LiveQuoteData = useMemo(() => {
    if (mergedData.change !== undefined) return mergedData

    const change =
      mergedData.ltp && mergedData.close ? mergedData.ltp - mergedData.close : undefined
    const changePercent = change && mergedData.close ? (change / mergedData.close) * 100 : undefined

    return {
      ...mergedData,
      change,
      changePercent,
    }
  }, [mergedData])

  // Determine data source
  const dataSource: 'websocket' | 'rest' | 'none' = useMemo(() => {
    if (hasWsData) return 'websocket'
    if (restQuotes || restDepth) return 'rest'
    return 'none'
  }, [hasWsData, restQuotes, restDepth])

  return {
    data: dataWithChange,
    isLive,
    isConnected: wsConnected,
    isLoading: isLoadingRest && !restQuotes && !restDepth,
    isPaused: wsPaused,
    isFallbackMode,
    dataSource,
    refresh: fetchRestData,
  }
}

```


---

# FILE: frontend\src\hooks\useMarketData.ts

```ts
/**
 * useMarketData - Hook for real-time market data via shared WebSocket connection
 *
 * This hook delegates to the MarketDataManager singleton via MarketDataContext,
 * ensuring a single WebSocket connection is shared across all components.
 *
 * API is backward-compatible with the original implementation.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useMarketDataContextOptional } from '@/contexts/MarketDataContext'
import { MarketDataManager, type SubscriptionMode, type SymbolData } from '@/lib/MarketDataManager'

// Re-export types for backward compatibility
export type { DepthLevel, MarketData, SymbolData } from '@/lib/MarketDataManager'

interface UseMarketDataOptions {
  symbols: Array<{ symbol: string; exchange: string }>
  mode?: SubscriptionMode
  enabled?: boolean
  autoReconnect?: boolean
}

interface UseMarketDataReturn {
  data: Map<string, SymbolData>
  isConnected: boolean
  isAuthenticated: boolean
  isConnecting: boolean
  isPaused: boolean
  isFallbackMode: boolean
  error: string | null
  connect: () => Promise<void>
  disconnect: () => void
}

export function useMarketData({
  symbols,
  mode = 'LTP',
  enabled = true,
  autoReconnect = true,
}: UseMarketDataOptions): UseMarketDataReturn {
  // Try to get context (may be null if used outside provider, e.g., WebSocketTest page)
  const context = useMarketDataContextOptional()

  // Use context manager if available, otherwise get singleton directly (for standalone use)
  const managerRef = useRef<MarketDataManager>(context?.manager ?? MarketDataManager.getInstance())

  const [marketData, setMarketData] = useState<Map<string, SymbolData>>(new Map())
  const [connectionState, setConnectionState] = useState({
    isConnected: context?.isConnected ?? false,
    isAuthenticated: context?.isAuthenticated ?? false,
    isPaused: context?.isPaused ?? false,
    isFallbackMode: context?.isFallbackMode ?? false,
    error: context?.error ?? null,
  })

  // Track if we're in the process of connecting
  const [isConnecting, setIsConnecting] = useState(false)

  // Stable symbol key for dependency tracking
  const symbolsKey = useMemo(
    () =>
      symbols
        .map((s) => `${s.exchange}:${s.symbol}`)
        .sort()
        .join(','),
    [symbols]
  )

  // Configure autoReconnect on the manager
  useEffect(() => {
    const manager = managerRef.current
    manager.setAutoReconnect(autoReconnect)
  }, [autoReconnect])

  // Subscribe to connection state changes
  useEffect(() => {
    const manager = managerRef.current
    const unsubscribe = manager.addStateListener((state) => {
      setConnectionState({
        isConnected: state.isConnected,
        isAuthenticated: state.isAuthenticated,
        isPaused: state.isPaused,
        isFallbackMode: state.isFallbackMode,
        error: state.error,
      })
      setIsConnecting(
        state.connectionState === 'connecting' || state.connectionState === 'authenticating'
      )
    })

    return unsubscribe
  }, [])

  // Subscribe to symbols when enabled
  useEffect(() => {
    if (!enabled || symbols.length === 0) {
      // Clear data when disabled
      setMarketData(new Map())
      return
    }

    const manager = managerRef.current

    // Auto-connect if not connected (manager handles deduplication)
    if (!connectionState.isConnected && !connectionState.isPaused) {
      manager.connect()
    }

    // Subscribe to each symbol
    const unsubscribes: Array<() => void> = []

    for (const { symbol, exchange } of symbols) {
      const unsubscribe = manager.subscribe(symbol, exchange, mode, (data: SymbolData) => {
        setMarketData((prev) => {
          const key = `${data.exchange}:${data.symbol}`
          const updated = new Map(prev)
          updated.set(key, data)
          return updated
        })
      })
      unsubscribes.push(unsubscribe)

      // Initialize with cached data if available
      const cached = manager.getCachedData(symbol, exchange)
      if (cached) {
        const key = `${exchange}:${symbol}`
        setMarketData((prev) => {
          const updated = new Map(prev)
          updated.set(key, cached)
          return updated
        })
      }
    }

    return () => {
      // Unsubscribe from all symbols
      unsubscribes.forEach((unsub) => unsub())
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, symbolsKey, mode])

  // Connect function (for manual connection)
  const connect = useCallback(async () => {
    await managerRef.current.connect()
  }, [])

  // Disconnect function (note: this disconnects the shared connection)
  const disconnect = useCallback(() => {
    managerRef.current.disconnect()
  }, [])

  return {
    data: marketData,
    isConnected: connectionState.isConnected,
    isAuthenticated: connectionState.isAuthenticated,
    isConnecting,
    isPaused: connectionState.isPaused,
    isFallbackMode: connectionState.isFallbackMode,
    error: connectionState.error,
    connect,
    disconnect,
  }
}

```


---

# FILE: frontend\src\hooks\useMarketStatus.ts

```ts
import { useCallback, useEffect, useState } from 'react'

interface MarketTiming {
  exchange: string
  start_time: number
  end_time: number
}

interface HolidayOpenExchange {
  exchange: string
  start_time: number
  end_time: number
}

interface Holiday {
  date: string
  description: string
  holiday_type: string
  closed_exchanges: string[]
  open_exchanges: HolidayOpenExchange[]
}

interface MarketStatusState {
  timings: MarketTiming[]
  holidays: Holiday[]
  isLoading: boolean
  error: string | null
}

// Fetch CSRF token for authenticated requests
async function fetchCSRFToken(): Promise<string> {
  const response = await fetch('/auth/csrf-token', { credentials: 'include' })
  const data = await response.json()
  return data.csrf_token
}

// Crypto exchanges operate 24/7 - no holidays or weekends
const CRYPTO_EXCHANGES = new Set(['CRYPTO'])

export function useMarketStatus() {
  const [state, setState] = useState<MarketStatusState>({
    timings: [],
    holidays: [],
    isLoading: true,
    error: null,
  })

  useEffect(() => {
    const fetchMarketData = async () => {
      try {
        const csrfToken = await fetchCSRFToken()
        const headers = {
          'X-CSRFToken': csrfToken,
          'Content-Type': 'application/json',
        }

        // Fetch market timings and holidays in parallel
        // Note: These endpoints are under the admin blueprint (/admin prefix)
        const [timingsRes, holidaysRes] = await Promise.all([
          fetch('/admin/api/timings', { headers, credentials: 'include' }),
          fetch('/admin/api/holidays', { headers, credentials: 'include' }),
        ])

        const timingsData = await timingsRes.json()
        const holidaysData = await holidaysRes.json()

        setState({
          // Use market_status field which contains epoch timestamps for market open checks
          timings: timingsData.status === 'success' ? timingsData.market_status || [] : [],
          holidays: holidaysData.status === 'success' ? holidaysData.data || [] : [],
          isLoading: false,
          error: null,
        })
      } catch (err) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: `Failed to fetch market status: ${err}`,
        }))
      }
    }

    fetchMarketData()
  }, [])

  // Check if today is a holiday for a specific exchange
  const isHolidayForExchange = useCallback(
    (exchange: string): boolean => {
      // Crypto exchanges have no holidays
      if (CRYPTO_EXCHANGES.has(exchange)) return false

      const today = new Date().toISOString().split('T')[0] // YYYY-MM-DD format
      const todayHoliday = state.holidays.find((h) => h.date === today)

      if (!todayHoliday) return false

      // Check if exchange is in closed_exchanges
      if (todayHoliday.closed_exchanges?.includes(exchange)) {
        // Check if there's a special session for this exchange
        const specialSession = todayHoliday.open_exchanges?.find((e) => e.exchange === exchange)
        if (specialSession) {
          // There's a special session - check if we're within it
          const now = Date.now()
          return !(now >= specialSession.start_time && now <= specialSession.end_time)
        }
        return true // Closed with no special session
      }

      return false
    },
    [state.holidays]
  )

  // Check if market is currently open for a specific exchange
  const isMarketOpen = useCallback(
    (exchange: string): boolean => {
      // Crypto exchanges are always open (24/7)
      if (CRYPTO_EXCHANGES.has(exchange)) return true

      // First check if it's a holiday
      if (isHolidayForExchange(exchange)) {
        return false
      }

      // Check regular market timing
      const timing = state.timings.find((t) => t.exchange === exchange)
      if (!timing) {
        // If no timing found, assume market is closed (conservative approach)
        return false
      }

      const now = Date.now()
      return now >= timing.start_time && now <= timing.end_time
    },
    [state.timings, isHolidayForExchange]
  )

  // Check if any market is open (useful for deciding whether to connect WebSocket)
  const isAnyMarketOpen = useCallback((): boolean => {
    return state.timings.some((timing) => {
      // Crypto exchanges are always open (24/7)
      if (CRYPTO_EXCHANGES.has(timing.exchange)) return true

      const now = Date.now()
      const isWithinHours = now >= timing.start_time && now <= timing.end_time
      return isWithinHours && !isHolidayForExchange(timing.exchange)
    })
  }, [state.timings, isHolidayForExchange])

  // Get market status for display
  const getMarketStatus = useCallback(
    (exchange: string): 'open' | 'closed' | 'pre-market' | 'post-market' => {
      // Crypto exchanges are always open (24/7)
      if (CRYPTO_EXCHANGES.has(exchange)) return 'open'

      if (isHolidayForExchange(exchange)) {
        return 'closed'
      }

      const timing = state.timings.find((t) => t.exchange === exchange)
      if (!timing) {
        return 'closed'
      }

      const now = Date.now()
      const preMarketBuffer = 15 * 60 * 1000 // 15 minutes before market open

      if (now < timing.start_time - preMarketBuffer) {
        return 'closed'
      } else if (now < timing.start_time) {
        return 'pre-market'
      } else if (now <= timing.end_time) {
        return 'open'
      } else {
        return 'post-market'
      }
    },
    [state.timings, isHolidayForExchange]
  )

  return {
    isMarketOpen,
    isAnyMarketOpen,
    isHolidayForExchange,
    getMarketStatus,
    timings: state.timings,
    holidays: state.holidays,
    isLoading: state.isLoading,
    error: state.error,
  }
}

```


---

# FILE: frontend\src\hooks\useOptionChainLive.ts

```ts
import { useEffect, useMemo, useRef, useState } from 'react'
import type { OptionChainResponse, OptionStrike } from '@/types/option-chain'
import { useMarketData } from './useMarketData'
import { useOptionChainPolling } from './useOptionChainPolling'

// Index symbols that use NSE_INDEX/BSE_INDEX for quotes (matches backend lists)
const NSE_INDEX_SYMBOLS = new Set([
  'NIFTY',
  'BANKNIFTY',
  'FINNIFTY',
  'MIDCPNIFTY',
  'NIFTYNXT50',
  'NIFTYIT',
  'NIFTYPHARMA',
  'NIFTYBANK',
])
const BSE_INDEX_SYMBOLS = new Set(['SENSEX', 'BANKEX', 'SENSEX50'])

function getUnderlyingExchange(symbol: string, optionExchange: string): string {
  const normalizedExchange = optionExchange.toUpperCase()
  if (NSE_INDEX_SYMBOLS.has(symbol)) return 'NSE_INDEX'
  if (BSE_INDEX_SYMBOLS.has(symbol)) return 'BSE_INDEX'
  if (normalizedExchange === 'CRYPTO') return 'CRYPTO'
  if (normalizedExchange === 'BFO') return 'BSE'
  if (normalizedExchange === 'NFO') return 'NSE'
  return normalizedExchange
}

// Round price to nearest tick size (e.g., 0.05 for options)
// Fixes broker WebSocket data that may not be aligned to tick size
function roundToTickSize(
  price: number | undefined,
  tickSize: number | undefined
): number | undefined {
  if (price === undefined || price === null) return undefined
  if (!tickSize || tickSize <= 0) return price
  // Round to nearest tick and fix floating point precision
  return Number((Math.round(price / tickSize) * tickSize).toFixed(2))
}

interface UseOptionChainLiveOptions {
  enabled: boolean
  /** Polling interval for OI/Volume data in ms (default: 30000) */
  oiRefreshInterval?: number
  /** Pause WebSocket and polling when tab is hidden (default: true) */
  pauseWhenHidden?: boolean
}

/**
 * Hook for real-time option chain data using hybrid approach:
 * - WebSocket for real-time LTP/Bid/Ask updates
 * - REST polling for OI/Volume data (less frequent)
 *
 * @param apiKey - OpenAlgo API key
 * @param underlying - Underlying symbol (NIFTY, BANKNIFTY, etc.)
 * @param exchange - Exchange code for underlying (NSE_INDEX, BSE_INDEX)
 * @param optionExchange - Exchange code for options (NFO, BFO)
 * @param expiryDate - Expiry date in DDMMMYY format
 * @param strikeCount - Number of strikes to fetch
 * @param options - Live options
 */
export function useOptionChainLive(
  apiKey: string | null,
  underlying: string,
  exchange: string,
  optionExchange: string,
  expiryDate: string,
  strikeCount: number,
  options: UseOptionChainLiveOptions = {
    enabled: true,
    oiRefreshInterval: 30000,
    pauseWhenHidden: true,
  }
) {
  const { enabled, oiRefreshInterval = 30000, pauseWhenHidden = true } = options

  // Track merged data with WebSocket updates
  const [mergedData, setMergedData] = useState<OptionChainResponse | null>(null)
  const [lastLtpUpdate, setLastLtpUpdate] = useState<Date | null>(null)

  // Polling for OI/Volume/Greeks (less frequent)
  const {
    data: polledData,
    isLoading,
    isConnected: isPollingConnected,
    isPaused: isPollingPaused,
    error,
    lastUpdate: lastPollUpdate,
    refetch,
  } = useOptionChainPolling(apiKey, underlying, exchange, expiryDate, strikeCount, {
    enabled,
    refreshInterval: oiRefreshInterval,
    pauseWhenHidden,
  })

  // Build symbol list from polled data for WebSocket subscription
  // Includes both option symbols AND underlying index for real-time spot price
  const wsSymbols = useMemo(() => {
    const symbols: Array<{ symbol: string; exchange: string }> = []

    // Add underlying symbol for real-time spot price
    // Use correct exchange based on whether it's an index or stock
    // For CRYPTO: bare underlying (e.g. BTC) isn't tradeable — use perpetual (e.g. BTCUSDFUT)
    const underlyingExch = getUnderlyingExchange(underlying, optionExchange)
    if (underlyingExch === 'CRYPTO') {
      symbols.push({ symbol: `${underlying}USDFUT`, exchange: underlyingExch })
    } else {
      symbols.push({ symbol: underlying, exchange: underlyingExch })
    }

    // Add all option symbols
    if (polledData?.chain) {
      for (const strike of polledData.chain) {
        if (strike.ce?.symbol) {
          symbols.push({ symbol: strike.ce.symbol, exchange: optionExchange })
        }
        if (strike.pe?.symbol) {
          symbols.push({ symbol: strike.pe.symbol, exchange: optionExchange })
        }
      }
    }

    return symbols
  }, [polledData?.chain, optionExchange, underlying])

  // WebSocket for real-time LTP + Depth (Bid/Ask) updates
  const {
    data: wsData,
    isConnected: isWsConnected,
    isAuthenticated: isWsAuthenticated,
    isPaused: isWsPaused,
  } = useMarketData({
    symbols: wsSymbols,
    mode: 'Depth', // Get LTP + Bid/Ask depth
    enabled: enabled && wsSymbols.length > 0,
  })

  // Track last LTP update time using ref to avoid triggering effect loops
  const lastLtpUpdateRef = useRef<number>(0)

  // Merge WebSocket LTP data into polled option chain data
  useEffect(() => {
    if (!polledData) {
      setMergedData(null)
      return
    }

    // If no WebSocket data yet, use polled data as-is
    if (wsData.size === 0) {
      setMergedData(polledData)
      return
    }

    // Create merged chain with WebSocket LTP updates
    const mergedChain: OptionStrike[] = polledData.chain.map((strike) => {
      const newStrike = { ...strike }

      // Update CE data from WebSocket
      if (strike.ce?.symbol) {
        const wsKey = `${optionExchange}:${strike.ce.symbol}`
        const wsSymbolData = wsData.get(wsKey)
        if (wsSymbolData?.data) {
          // Try depth data first (dp packets), fallback to quote data (sf packets)
          // Depth mode: depth.buy[0].price, depth.buy[0].quantity
          // Quote mode: bid_price, ask_price, bid_size, ask_size
          const depthBuy = wsSymbolData.data.depth?.buy?.[0]
          const depthSell = wsSymbolData.data.depth?.sell?.[0]
          const tickSize = strike.ce.tick_size
          newStrike.ce = {
            ...strike.ce,
            ltp: roundToTickSize(wsSymbolData.data.ltp, tickSize) ?? strike.ce.ltp,
            bid:
              roundToTickSize(depthBuy?.price ?? wsSymbolData.data.bid_price, tickSize) ??
              strike.ce.bid,
            ask:
              roundToTickSize(depthSell?.price ?? wsSymbolData.data.ask_price, tickSize) ??
              strike.ce.ask,
            bid_qty: depthBuy?.quantity ?? wsSymbolData.data.bid_size ?? strike.ce.bid_qty ?? 0,
            ask_qty: depthSell?.quantity ?? wsSymbolData.data.ask_size ?? strike.ce.ask_qty ?? 0,
          }
        }
      }

      // Update PE data from WebSocket
      if (strike.pe?.symbol) {
        const wsKey = `${optionExchange}:${strike.pe.symbol}`
        const wsSymbolData = wsData.get(wsKey)
        if (wsSymbolData?.data) {
          // Try depth data first (dp packets), fallback to quote data (sf packets)
          const depthBuy = wsSymbolData.data.depth?.buy?.[0]
          const depthSell = wsSymbolData.data.depth?.sell?.[0]
          const tickSize = strike.pe.tick_size
          newStrike.pe = {
            ...strike.pe,
            ltp: roundToTickSize(wsSymbolData.data.ltp, tickSize) ?? strike.pe.ltp,
            bid:
              roundToTickSize(depthBuy?.price ?? wsSymbolData.data.bid_price, tickSize) ??
              strike.pe.bid,
            ask:
              roundToTickSize(depthSell?.price ?? wsSymbolData.data.ask_price, tickSize) ??
              strike.pe.ask,
            bid_qty: depthBuy?.quantity ?? wsSymbolData.data.bid_size ?? strike.pe.bid_qty ?? 0,
            ask_qty: depthSell?.quantity ?? wsSymbolData.data.ask_size ?? strike.pe.ask_qty ?? 0,
          }
        }
      }

      return newStrike
    })

    // Check if any LTP was updated (using ref to avoid loop)
    let hasLtpUpdate = false
    for (const [, symbolData] of wsData) {
      if (symbolData.lastUpdate && symbolData.lastUpdate > lastLtpUpdateRef.current) {
        hasLtpUpdate = true
        lastLtpUpdateRef.current = symbolData.lastUpdate
        break
      }
    }

    if (hasLtpUpdate) {
      setLastLtpUpdate(new Date())
    }

    // Get real-time underlying spot price from WebSocket
    const underlyingExch = getUnderlyingExchange(underlying, optionExchange)
    const underlyingKey = `${underlyingExch}:${underlying}`
    const underlyingWsData = wsData.get(underlyingKey)
    const underlyingLtp = underlyingWsData?.data?.ltp ?? polledData.underlying_ltp

    setMergedData({
      ...polledData,
      underlying_ltp: underlyingLtp,
      chain: mergedChain,
    })
  }, [polledData, wsData, optionExchange, underlying])

  // Determine streaming status
  const isStreaming = isWsConnected && isWsAuthenticated && wsSymbols.length > 0
  const isPaused = isPollingPaused || isWsPaused

  // Combined last update (use LTP update if more recent)
  const lastUpdate = useMemo(() => {
    if (!lastPollUpdate && !lastLtpUpdate) return null
    if (!lastPollUpdate) return lastLtpUpdate
    if (!lastLtpUpdate) return lastPollUpdate
    return lastLtpUpdate > lastPollUpdate ? lastLtpUpdate : lastPollUpdate
  }, [lastPollUpdate, lastLtpUpdate])

  return {
    data: mergedData,
    isLoading,
    isConnected: isPollingConnected,
    isStreaming,
    isPaused,
    error,
    lastUpdate,
    streamingSymbols: wsSymbols.length,
    refetch,
  }
}

```


---

# FILE: frontend\src\hooks\useOptionChainPolling.ts

```ts
import { useCallback, useEffect, useRef, useState } from 'react'
import type { OptionChainResponse } from '@/types/option-chain'
import { usePageVisibility } from './usePageVisibility'

interface UseOptionChainPollingOptions {
  enabled: boolean
  refreshInterval?: number
  pauseWhenHidden?: boolean
}

interface UseOptionChainPollingState {
  data: OptionChainResponse | null
  isLoading: boolean
  isConnected: boolean
  isPaused: boolean
  error: string | null
  lastUpdate: Date | null
}

/**
 * Hook for polling option chain data from REST API.
 * Supports page visibility to pause polling when tab is hidden.
 *
 * @param apiKey - OpenAlgo API key
 * @param underlying - Underlying symbol (NIFTY, BANKNIFTY, etc.)
 * @param exchange - Exchange code (NSE_INDEX, BSE_INDEX)
 * @param expiryDate - Expiry date in DDMMMYY format
 * @param strikeCount - Number of strikes to fetch
 * @param options - Polling options
 */
export function useOptionChainPolling(
  apiKey: string | null,
  underlying: string,
  exchange: string,
  expiryDate: string,
  strikeCount: number,
  options: UseOptionChainPollingOptions = {
    enabled: true,
    refreshInterval: 30000,
    pauseWhenHidden: true,
  }
) {
  const { enabled, refreshInterval = 30000, pauseWhenHidden = true } = options
  const { isVisible } = usePageVisibility()

  const [state, setState] = useState<UseOptionChainPollingState>({
    data: null,
    isLoading: false,
    isConnected: false,
    isPaused: false,
    error: null,
    lastUpdate: null,
  })

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  // Drop the previous chain whenever the request identity changes. Without
  // this, useOptionChainLive briefly pairs the prior chain's option symbols
  // with the newly-switched optionExchange (e.g. NFO:SENSEX..., BFO:NIFTY...),
  // which the broker rejects as invalid subscriptions.
  useEffect(() => {
    setState((prev) => ({ ...prev, data: null, lastUpdate: null }))
  }, [apiKey, underlying, exchange, expiryDate, strikeCount])

  // Determine if polling should be active
  const shouldPoll = enabled && (!pauseWhenHidden || isVisible)

  const fetchData = useCallback(async () => {
    if (!apiKey || !underlying || !exchange || !expiryDate) {
      return
    }

    // Skip if already fetching
    if (abortControllerRef.current) {
      return
    }

    setState((prev) => ({ ...prev, isLoading: true }))

    try {
      const controller = new AbortController()
      abortControllerRef.current = controller

      const response = await fetch('/api/v1/optionchain', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          apikey: apiKey,
          underlying,
          exchange,
          expiry_date: expiryDate,
          strike_count: strikeCount,
        }),
        signal: controller.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data: OptionChainResponse = await response.json()

      if (data.status === 'success') {
        setState((prev) => ({
          ...prev,
          data,
          isLoading: false,
          isConnected: true,
          error: null,
          lastUpdate: new Date(),
        }))
      } else {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: data.message || 'Failed to fetch option chain',
        }))
      }
    } catch (error) {
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          if (abortControllerRef.current === null) {
            setState((prev) => ({ ...prev, isLoading: false }))
          }
        } else {
          setState((prev) => ({
            ...prev,
            isLoading: false,
            error: error.message || 'Connection error',
            isConnected: false,
          }))
        }
      }
    } finally {
      abortControllerRef.current = null
    }
  }, [apiKey, underlying, exchange, expiryDate, strikeCount])

  // Handle polling start/stop based on visibility
  useEffect(() => {
    if (!shouldPoll) {
      // Pause polling
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      setState((prev) => ({ ...prev, isPaused: !enabled ? false : true }))
      return
    }

    // Resume/start polling
    setState((prev) => ({ ...prev, isConnected: true, isPaused: false }))

    // Fetch immediately when becoming visible
    fetchData()

    // Set up interval
    intervalRef.current = setInterval(fetchData, refreshInterval)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
        abortControllerRef.current = null
      }
    }
  }, [shouldPoll, fetchData, refreshInterval, enabled])

  const refetch = useCallback(() => {
    fetchData()
  }, [fetchData])

  return {
    ...state,
    refetch,
  }
}

```


---

# FILE: frontend\src\hooks\useOptionChainPreferences.ts

```ts
import { useCallback, useEffect, useState } from 'react'
import type {
  BarDataSource,
  BarStyle,
  ColumnKey,
  OptionChainPreferences,
} from '@/types/option-chain'
import { COLUMN_DEFINITIONS, DEFAULT_PREFERENCES, LOCALSTORAGE_KEY } from '@/types/option-chain'

interface UseOptionChainPreferencesReturn {
  preferences: OptionChainPreferences
  visibleColumns: ColumnKey[]
  columnOrder: ColumnKey[]
  strikeCount: number
  selectedUnderlying: string
  barDataSource: BarDataSource
  barStyle: BarStyle
  toggleColumn: (columnKey: ColumnKey) => void
  reorderColumns: (newOrder: ColumnKey[]) => void
  setStrikeCount: (count: number) => void
  setSelectedUnderlying: (underlying: string) => void
  setBarDataSource: (source: BarDataSource) => void
  setBarStyle: (style: BarStyle) => void
  resetToDefaults: () => void
  isColumnVisible: (columnKey: ColumnKey) => boolean
  getOrderedVisibleColumns: () => ColumnKey[]
}

function loadPreferences(): OptionChainPreferences {
  if (typeof window === 'undefined') {
    return DEFAULT_PREFERENCES
  }

  try {
    const stored = localStorage.getItem(LOCALSTORAGE_KEY)
    if (!stored) {
      return DEFAULT_PREFERENCES
    }

    const parsed = JSON.parse(stored) as Partial<OptionChainPreferences>

    // Validate and merge with defaults
    const validColumnKeys = new Set(COLUMN_DEFINITIONS.map((c) => c.key))

    const visibleColumns = Array.isArray(parsed.visibleColumns)
      ? parsed.visibleColumns.filter((key) => validColumnKeys.has(key))
      : DEFAULT_PREFERENCES.visibleColumns

    // Ensure strike column is always visible (mandatory)
    if (!visibleColumns.includes('strike')) {
      visibleColumns.push('strike')
    }

    const columnOrder = Array.isArray(parsed.columnOrder)
      ? parsed.columnOrder.filter((key) => validColumnKeys.has(key))
      : DEFAULT_PREFERENCES.columnOrder

    // Ensure all valid columns are in the order (add any missing ones)
    const orderSet = new Set(columnOrder)
    DEFAULT_PREFERENCES.columnOrder.forEach((key) => {
      if (!orderSet.has(key)) {
        columnOrder.push(key)
      }
    })

    return {
      visibleColumns,
      columnOrder,
      strikeCount:
        typeof parsed.strikeCount === 'number' && parsed.strikeCount > 0
          ? parsed.strikeCount
          : DEFAULT_PREFERENCES.strikeCount,
      selectedUnderlying:
        typeof parsed.selectedUnderlying === 'string' && parsed.selectedUnderlying
          ? parsed.selectedUnderlying
          : DEFAULT_PREFERENCES.selectedUnderlying,
      barDataSource:
        parsed.barDataSource === 'oi' || parsed.barDataSource === 'volume'
          ? parsed.barDataSource
          : DEFAULT_PREFERENCES.barDataSource,
      barStyle:
        parsed.barStyle === 'gradient' || parsed.barStyle === 'solid'
          ? parsed.barStyle
          : DEFAULT_PREFERENCES.barStyle,
    }
  } catch {
    return DEFAULT_PREFERENCES
  }
}

function savePreferences(preferences: OptionChainPreferences): void {
  if (typeof window === 'undefined') {
    return
  }

  try {
    localStorage.setItem(LOCALSTORAGE_KEY, JSON.stringify(preferences))
  } catch {
    // Silently fail if localStorage is unavailable
  }
}

export function useOptionChainPreferences(): UseOptionChainPreferencesReturn {
  const [preferences, setPreferences] = useState<OptionChainPreferences>(() => loadPreferences())

  // Persist changes to localStorage
  useEffect(() => {
    savePreferences(preferences)
  }, [preferences])

  const toggleColumn = useCallback((columnKey: ColumnKey) => {
    // Don't allow hiding the strike column
    if (columnKey === 'strike') {
      return
    }

    setPreferences((prev) => {
      const isVisible = prev.visibleColumns.includes(columnKey)
      const newVisibleColumns = isVisible
        ? prev.visibleColumns.filter((key) => key !== columnKey)
        : [...prev.visibleColumns, columnKey]

      return {
        ...prev,
        visibleColumns: newVisibleColumns,
      }
    })
  }, [])

  const reorderColumns = useCallback((newOrder: ColumnKey[]) => {
    setPreferences((prev) => ({
      ...prev,
      columnOrder: newOrder,
    }))
  }, [])

  const setStrikeCount = useCallback((count: number) => {
    setPreferences((prev) => ({
      ...prev,
      strikeCount: count,
    }))
  }, [])

  const setSelectedUnderlying = useCallback((underlying: string) => {
    setPreferences((prev) => ({
      ...prev,
      selectedUnderlying: underlying,
    }))
  }, [])

  const setBarDataSource = useCallback((source: BarDataSource) => {
    setPreferences((prev) => ({
      ...prev,
      barDataSource: source,
    }))
  }, [])

  const setBarStyle = useCallback((style: BarStyle) => {
    setPreferences((prev) => ({
      ...prev,
      barStyle: style,
    }))
  }, [])

  const resetToDefaults = useCallback(() => {
    setPreferences(DEFAULT_PREFERENCES)
  }, [])

  const isColumnVisible = useCallback(
    (columnKey: ColumnKey): boolean => {
      return preferences.visibleColumns.includes(columnKey)
    },
    [preferences.visibleColumns]
  )

  const getOrderedVisibleColumns = useCallback((): ColumnKey[] => {
    // Return columns in the specified order, filtered to only visible ones
    return preferences.columnOrder.filter((key) => preferences.visibleColumns.includes(key))
  }, [preferences.columnOrder, preferences.visibleColumns])

  return {
    preferences,
    visibleColumns: preferences.visibleColumns,
    columnOrder: preferences.columnOrder,
    strikeCount: preferences.strikeCount,
    selectedUnderlying: preferences.selectedUnderlying,
    barDataSource: preferences.barDataSource,
    barStyle: preferences.barStyle,
    toggleColumn,
    reorderColumns,
    setStrikeCount,
    setSelectedUnderlying,
    setBarDataSource,
    setBarStyle,
    resetToDefaults,
    isColumnVisible,
    getOrderedVisibleColumns,
  }
}

```


---

# FILE: frontend\src\hooks\useOrderEventRefresh.ts

```ts
import { useEffect, useRef } from 'react'
import { io, type Socket } from 'socket.io-client'

/**
 * Supported Socket.IO event types for order-related updates
 */
export type OrderEventType =
  | 'order_event'
  | 'analyzer_update'
  | 'close_position_event'
  | 'cancel_order_event'
  | 'modify_order_event'

/**
 * Configuration options for useOrderEventRefresh hook
 */
export interface UseOrderEventRefreshOptions {
  /** Events to listen for (default: ['order_event', 'analyzer_update']) */
  events?: OrderEventType[]
  /** Delay in ms before calling refresh function (default: 500) */
  delay?: number
  /** Whether the hook is enabled (default: true) */
  enabled?: boolean
}

/**
 * Centralized hook for Socket.IO order event listeners.
 *
 * Automatically sets up Socket.IO connection and listens for specified events,
 * calling the refresh function with an optional delay when events occur.
 *
 * @example
 * ```tsx
 * // Basic usage - listens to order_event and analyzer_update
 * useOrderEventRefresh(fetchPositions);
 *
 * // With additional events
 * useOrderEventRefresh(fetchPositions, {
 *   events: ['order_event', 'analyzer_update', 'close_position_event'],
 *   delay: 500,
 * });
 *
 * // Conditional enablement
 * useOrderEventRefresh(fetchPositions, {
 *   enabled: isAuthenticated,
 * });
 * ```
 *
 * @param refreshFn - Function to call when an event is received
 * @param options - Configuration options
 */
export function useOrderEventRefresh(
  refreshFn: () => void,
  options: UseOrderEventRefreshOptions = {}
): void {
  const { events = ['order_event', 'analyzer_update'], delay = 500, enabled = true } = options

  const socketRef = useRef<Socket | null>(null)
  const refreshFnRef = useRef(refreshFn)

  // Keep refresh function reference up to date
  useEffect(() => {
    refreshFnRef.current = refreshFn
  }, [refreshFn])

  useEffect(() => {
    if (!enabled) return

    // Build Socket.IO URL from current location
    const protocol = window.location.protocol
    const host = window.location.hostname
    const port = window.location.port

    socketRef.current = io(`${protocol}//${host}:${port}`, {
      transports: ['polling'],
      upgrade: false,
    })

    const socket = socketRef.current

    // Create handler for each event type
    const handleEvent = () => {
      // Delay slightly to allow server to process the event
      setTimeout(() => refreshFnRef.current(), delay)
    }

    // Register listeners for all specified events
    events.forEach((event) => {
      socket.on(event, handleEvent)
    })

    // Cleanup on unmount
    return () => {
      events.forEach((event) => {
        socket.off(event, handleEvent)
      })
      socket.disconnect()
    }
  }, [events, delay, enabled])
}

/**
 * Hook to get direct access to Socket.IO connection for custom event handling.
 *
 * @example
 * ```tsx
 * const { socket, isConnected } = useSocketConnection();
 *
 * useEffect(() => {
 *   if (!socket) return;
 *   socket.on('custom_event', handleCustomEvent);
 *   return () => socket.off('custom_event', handleCustomEvent);
 * }, [socket]);
 * ```
 */
export function useSocketConnection(enabled = true): {
  socket: Socket | null
  isConnected: boolean
} {
  const socketRef = useRef<Socket | null>(null)

  useEffect(() => {
    if (!enabled) return

    const protocol = window.location.protocol
    const host = window.location.hostname
    const port = window.location.port

    socketRef.current = io(`${protocol}//${host}:${port}`, {
      transports: ['polling'],
      upgrade: false,
    })

    return () => {
      socketRef.current?.disconnect()
      socketRef.current = null
    }
  }, [enabled])

  return {
    socket: socketRef.current,
    isConnected: socketRef.current?.connected ?? false,
  }
}

```


---

# FILE: frontend\src\hooks\usePageTitle.ts

```ts
import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

const PAGE_TITLES: Record<string, string> = {
  '/': 'Home',
  '/faq': 'FAQ',
  '/setup': 'Setup',
  '/login': 'Login',
  '/reset-password': 'Reset Password',
  '/download': 'Download',
  '/broker': 'Select Broker',
  '/dashboard': 'Dashboard',
  '/positions': 'Positions',
  '/orderbook': 'Order Book',
  '/tradebook': 'Trade Book',
  '/holdings': 'Holdings',
  '/search': 'Search',
  '/search/token': 'Token Search',
  '/apikey': 'API Key',
  '/platforms': 'Platforms',
  '/tradingview': 'TradingView',
  '/gocharting': 'GoCharting',
  '/pnl-tracker': 'P&L Tracker',
  '/sandbox': 'Sandbox',
  '/sandbox/mypnl': 'Sandbox P&L',
  '/analyzer': 'Analyzer',
  '/tools': 'Tools',
  '/strategybuilder': 'Strategy Builder',
  '/strategybuilder/portfolio': 'Strategy Portfolio',
  '/optionchain': 'Option Chain',
  '/ivchart': 'IV Chart',
  '/oitracker': 'OI Tracker',
  '/maxpain': 'Max Pain',
  '/straddle': 'Straddle Chart',
  '/straddlepnl': 'Straddle P&L',
  '/volsurface': 'Vol Surface',
  '/gex': 'GEX Dashboard',
  '/ivsmile': 'IV Smile',
  '/oiprofile': 'OI Profile',
  '/websocket/test': 'WebSocket Test',
  '/strategy': 'Strategies',
  '/strategy/new': 'New Strategy',
  '/python': 'Python Strategies',
  '/python/new': 'New Python Strategy',
  '/python/guide': 'Python Strategy Guide',
  '/chartink': 'Chartink Strategies',
  '/chartink/new': 'New Chartink Strategy',
  '/flow': 'Flow',
  '/flow/shortcuts': 'Flow Shortcuts',
  '/leverage': 'Leverage',
  '/admin': 'Admin',
  '/admin/freeze': 'Freeze Qty',
  '/admin/holidays': 'Holidays',
  '/admin/timings': 'Market Timings',
  '/telegram': 'Telegram',
  '/telegram/config': 'Telegram Config',
  '/telegram/users': 'Telegram Users',
  '/telegram/analytics': 'Telegram Analytics',
  '/logs': 'Logs',
  '/logs/live': 'Live Logs',
  '/logs/sandbox': 'Sandbox Logs',
  '/logs/security': 'Security',
  '/logs/traffic': 'Traffic',
  '/logs/latency': 'Latency',
  '/health': 'Health Monitor',
  '/profile': 'Profile',
  '/master-contract': 'Master Contract',
  '/action-center': 'Action Center',
  '/playground': 'Playground',
  '/historify': 'Historify',
  '/historify/charts': 'Historify Charts',
}

/** Dynamic route patterns for parameterized routes */
const DYNAMIC_TITLES: Array<{ pattern: RegExp; title: string }> = [
  { pattern: /^\/strategy\/[^/]+\/configure$/, title: 'Configure Strategy' },
  { pattern: /^\/strategy\/[^/]+$/, title: 'View Strategy' },
  { pattern: /^\/python\/[^/]+\/edit$/, title: 'Edit Strategy' },
  { pattern: /^\/python\/[^/]+\/logs$/, title: 'Strategy Logs' },
  { pattern: /^\/python\/[^/]+\/schedule$/, title: 'Schedule Strategy' },
  { pattern: /^\/chartink\/[^/]+\/configure$/, title: 'Configure Chartink' },
  { pattern: /^\/chartink\/[^/]+$/, title: 'View Chartink Strategy' },
  { pattern: /^\/flow\/editor\/[^/]+$/, title: 'Flow Editor' },
  { pattern: /^\/historify\/charts\/[^/]+$/, title: 'Historify Charts' },
  { pattern: /^\/websocket\/test\/\d+$/, title: 'WebSocket Test' },
]

function getPageTitle(pathname: string): string {
  if (PAGE_TITLES[pathname]) {
    return PAGE_TITLES[pathname]
  }

  for (const { pattern, title } of DYNAMIC_TITLES) {
    if (pattern.test(pathname)) {
      return title
    }
  }

  return 'OpenAlgo'
}

export function usePageTitle() {
  const { pathname } = useLocation()

  useEffect(() => {
    const title = getPageTitle(pathname)
    document.title = title === 'OpenAlgo' ? 'OpenAlgo' : `${title} | OpenAlgo`
  }, [pathname])
}

```


---

# FILE: frontend\src\hooks\usePageVisibility.ts

```ts
import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Hook to detect page visibility state using the Page Visibility API.
 *
 * This hook helps optimize resource usage by detecting when the browser tab
 * is hidden (user switched tabs, minimized window, etc.) so that WebSocket
 * connections and polling can be paused.
 *
 * @example
 * ```tsx
 * const { isVisible, wasHidden, timeSinceVisible } = usePageVisibility()
 *
 * // Pause WebSocket when hidden
 * const { data } = useLivePrice(items, {
 *   enabled: items.length > 0 && isVisible,
 * })
 *
 * // Refresh data when tab becomes visible after being hidden
 * useEffect(() => {
 *   if (isVisible && wasHidden && timeSinceVisible > 30000) {
 *     refreshData()
 *   }
 * }, [isVisible, wasHidden, timeSinceVisible])
 * ```
 */
export interface UsePageVisibilityReturn {
  /** Whether the page is currently visible */
  isVisible: boolean
  /** Whether the page was previously hidden (useful for detecting tab return) */
  wasHidden: boolean
  /** Time in ms since the page became visible (0 if currently hidden) */
  timeSinceVisible: number
  /** Time in ms since the page became hidden (0 if currently visible) */
  timeSinceHidden: number
  /** Timestamp when visibility last changed */
  lastVisibilityChange: number
}

export function usePageVisibility(): UsePageVisibilityReturn {
  // Initialize based on current document state (SSR-safe)
  const [isVisible, setIsVisible] = useState<boolean>(() =>
    typeof document !== 'undefined' ? document.visibilityState === 'visible' : true
  )

  const [wasHidden, setWasHidden] = useState<boolean>(false)
  const [lastVisibilityChange, setLastVisibilityChange] = useState<number>(Date.now())
  const [timeSinceVisible, setTimeSinceVisible] = useState<number>(0)
  const [timeSinceHidden, setTimeSinceHidden] = useState<number>(0)

  // Track previous visibility state
  const previousVisibleRef = useRef<boolean>(isVisible)
  const hiddenTimestampRef = useRef<number | null>(null)
  const visibleTimestampRef = useRef<number>(Date.now())
  // Use ref to track visibility for timer updates (avoids callback recreation)
  const isVisibleRef = useRef<boolean>(isVisible)

  // Keep ref in sync with state
  useEffect(() => {
    isVisibleRef.current = isVisible
  }, [isVisible])

  // Update time counters - uses ref to avoid effect re-runs on visibility change
  const updateTimers = useCallback(() => {
    const now = Date.now()
    if (isVisibleRef.current) {
      setTimeSinceVisible(now - visibleTimestampRef.current)
      setTimeSinceHidden(0)
    } else {
      setTimeSinceHidden(hiddenTimestampRef.current ? now - hiddenTimestampRef.current : 0)
      setTimeSinceVisible(0)
    }
  }, []) // No dependencies - uses refs instead

  useEffect(() => {
    // SSR guard
    if (typeof document === 'undefined') return

    const handleVisibilityChange = () => {
      const nowVisible = document.visibilityState === 'visible'
      const now = Date.now()

      // Detect if returning from hidden state
      if (nowVisible && !previousVisibleRef.current) {
        setWasHidden(true)
        visibleTimestampRef.current = now

        // Calculate how long the tab was hidden
        if (hiddenTimestampRef.current) {
          setTimeSinceHidden(now - hiddenTimestampRef.current)
        }
      } else if (!nowVisible) {
        hiddenTimestampRef.current = now
        setWasHidden(false)
      }

      previousVisibleRef.current = nowVisible
      setIsVisible(nowVisible)
      setLastVisibilityChange(now)
      updateTimers()
    }

    // Listen for visibility changes
    document.addEventListener('visibilitychange', handleVisibilityChange)

    // Also listen for focus/blur as backup (some browsers)
    const handleFocus = () => {
      if (!previousVisibleRef.current) {
        handleVisibilityChange()
      }
    }

    const handleBlur = () => {
      // Only update if we haven't already detected hidden via visibilitychange
      if (previousVisibleRef.current && document.visibilityState === 'hidden') {
        handleVisibilityChange()
      }
    }

    window.addEventListener('focus', handleFocus)
    window.addEventListener('blur', handleBlur)

    // Update timers periodically when visible (for timeSinceVisible accuracy)
    const timerInterval = setInterval(updateTimers, 1000)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      window.removeEventListener('focus', handleFocus)
      window.removeEventListener('blur', handleBlur)
      clearInterval(timerInterval)
    }
  }, [updateTimers])

  // Reset wasHidden after a short delay (so consumers can react to it)
  useEffect(() => {
    if (wasHidden) {
      const timeout = setTimeout(() => setWasHidden(false), 100)
      return () => clearTimeout(timeout)
    }
  }, [wasHidden])

  return {
    isVisible,
    wasHidden,
    timeSinceVisible,
    timeSinceHidden,
    lastVisibilityChange,
  }
}

/**
 * Simplified hook that just returns visibility boolean.
 * Use this when you don't need the additional metadata.
 *
 * @example
 * ```tsx
 * const isVisible = useIsPageVisible()
 *
 * useEffect(() => {
 *   if (!isVisible) return // Skip when hidden
 *   // ... your effect
 * }, [isVisible])
 * ```
 */
export function useIsPageVisible(): boolean {
  const { isVisible } = usePageVisibility()
  return isVisible
}

```


---

# FILE: frontend\src\hooks\useSocket.ts

```ts
import { useCallback, useEffect, useRef } from 'react'
import { io, type Socket } from 'socket.io-client'
import { toast } from 'sonner'
import { type AlertCategories, useAlertStore } from '@/stores/alertStore'
import { useAuthStore } from '@/stores/authStore'
import { useSessionStore } from '@/stores/sessionStore'

// Audio throttling configuration
const AUDIO_THROTTLE_MS = 1000

interface OrderEventData {
  symbol: string
  action: string
  orderid: string
  batch_order?: boolean
  is_last_order?: boolean
}

interface CancelOrderEventData {
  orderid: string
  batch_order?: boolean
}

interface ModifyOrderEventData {
  orderid: string
  status: string
}

interface ClosePositionEventData {
  message: string
  status: string
}

interface MasterContractData {
  message: string
}

interface AnalyzerUpdateData {
  request: {
    api_type: string
    symbol?: string
    action?: string
    quantity?: string
    orderid?: string
    position_size?: string
  }
  response: {
    status: string
    message?: string
    orderid?: string
    canceled_orders?: string[]
  }
}

// Helper to show toast only if enabled for category
const showCategoryToast = (
  type: 'success' | 'error' | 'warning' | 'info',
  message: string,
  category?: keyof AlertCategories
) => {
  const { shouldShowToast } = useAlertStore.getState()
  if (shouldShowToast(category)) {
    toast[type](message)
  }
}

export function useSocket() {
  const { isAuthenticated } = useAuthStore()
  const socketRef = useRef<Socket | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const lastAudioTimeRef = useRef<number>(0)
  const audioEnabledRef = useRef<boolean>(false)

  const playAlertSound = useCallback((category?: keyof AlertCategories) => {
    // Check if sound should play based on alert settings
    const { shouldPlaySound, shouldShowToast } = useAlertStore.getState()
    if (!shouldPlaySound()) return
    // If category specified, also check category is enabled
    if (category && !shouldShowToast(category)) return

    const now = Date.now()
    const timeSinceLastAttempt = now - lastAudioTimeRef.current

    if (timeSinceLastAttempt < AUDIO_THROTTLE_MS && lastAudioTimeRef.current !== 0) {
      return
    }

    lastAudioTimeRef.current = now

    if (audioRef.current) {
      audioRef.current
        .play()
        .then(() => {
          audioEnabledRef.current = true
        })
        .catch(() => {})
    }
  }, [])

  const enableAudio = useCallback(() => {
    if (!audioEnabledRef.current && audioRef.current) {
      const audio = audioRef.current
      const originalVolume = audio.volume
      audio.volume = 0
      audio
        .play()
        .then(() => {
          audio.pause()
          audio.currentTime = 0
          audio.volume = originalVolume
          audioEnabledRef.current = true
        })
        .catch(() => {
          audio.volume = originalVolume
        })
    }
  }, [])

  useEffect(() => {
    // Only connect when authenticated
    if (!isAuthenticated) {
      return
    }

    // Create audio element
    audioRef.current = new Audio('/sounds/alert.mp3')
    audioRef.current.preload = 'auto'

    // Enable audio on user interaction
    const handleInteraction = () => {
      enableAudio()
    }

    ;['click', 'touchstart', 'keydown'].forEach((eventType) => {
      document.addEventListener(eventType, handleInteraction, { once: true, passive: true })
    })

    // Connect to socket server
    const protocol = window.location.protocol
    const host = window.location.hostname
    const port = window.location.port

    // Use polling transport only - WebSocket upgrade fails with threading async mode
    // Polling is still real-time via HTTP long-polling
    socketRef.current = io(`${protocol}//${host}:${port}`, {
      transports: ['polling'],
      upgrade: false,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      timeout: 20000,
      forceNew: true, // Always create new session to avoid "Invalid session" errors on reconnect
    })

    const socket = socketRef.current

    // Force logout from another device
    socket.on('force_logout', (data: { message: string }) => {
      playAlertSound('system')
      // Clear auth store immediately
      useAuthStore.getState().logout()
      useSessionStore.getState().setActiveSessionCount(0)
      // Show persistent toast and redirect after a short delay so user sees it
      toast.error(data.message || 'Logged out from another device', {
        duration: 10000,
      })
      setTimeout(() => {
        window.location.href = '/login'
      }, 2000)
    })

    // Password change notification
    socket.on('password_change', (data: { message: string }) => {
      playAlertSound('system')
      showCategoryToast('info', data.message, 'system')
    })

    // Master contract download notification
    socket.on('master_contract_download', (data: MasterContractData) => {
      playAlertSound('system')
      showCategoryToast('info', `Master Contract: ${data.message}`, 'system')
    })

    // Cancel order notification - only play sound, UI handles toast
    socket.on('cancel_order_event', (data: CancelOrderEventData) => {
      if (!data.batch_order) {
        playAlertSound('orders')
      }
    })

    // Modify order notification - only play sound, UI handles toast
    socket.on('modify_order_event', (_data: ModifyOrderEventData) => {
      playAlertSound('orders')
    })

    // Close position notification
    socket.on('close_position_event', (data: ClosePositionEventData) => {
      playAlertSound('orders')
      showCategoryToast('success', data.message || 'All Open Positions Squared Off', 'positions')
    })

    // Order placement notification
    socket.on('order_event', (data: OrderEventData) => {
      const shouldPlayAudio = !data.batch_order || data.is_last_order
      if (shouldPlayAudio) {
        playAlertSound('orders')
      }

      const message = `${data.action.toUpperCase()} Order Placed for Symbol: ${data.symbol}, Order ID: ${data.orderid}`
      if (data.action.toUpperCase() === 'BUY') {
        showCategoryToast('success', message, 'orders')
      } else {
        showCategoryToast('error', message, 'orders')
      }
    })

    // Generic order notification handler
    socket.on(
      'order_notification',
      (data: { symbol?: string; status?: string; message?: string }) => {
        playAlertSound('orders')

        let type: 'success' | 'error' | 'warning' | 'info' = 'info'
        if (data.status && typeof data.status === 'string') {
          if (data.status.toLowerCase().includes('success')) {
            type = 'success'
          } else if (
            data.status.toLowerCase().includes('error') ||
            data.status.toLowerCase().includes('reject')
          ) {
            type = 'error'
          } else if (data.status.toLowerCase().includes('pending')) {
            type = 'warning'
          }
        }

        let message = ''
        if (data.symbol) {
          message += `${data.symbol}: `
        }
        if (data.status) {
          message += data.status
        }
        if (data.message) {
          message += data.message
        }

        showCategoryToast(type, message, 'orders')
      }
    )

    // Active sessions update (event-driven, no polling)
    socket.on('active_sessions_update', (data: { count: number }) => {
      useSessionStore.getState().setActiveSessionCount(data.count)
    })

    // Analyzer update notification
    socket.on('analyzer_update', (data: AnalyzerUpdateData) => {
      const passiveApiTypes = [
        'orderstatus',
        'openposition',
        'orderbook',
        'tradebook',
        'positions',
        'holdings',
      ]
      const isPassiveMonitoring = passiveApiTypes.includes(data.request.api_type)

      if (!isPassiveMonitoring) {
        playAlertSound('analyzer')
      }

      let message = ''
      let type: 'success' | 'error' | 'info' =
        data.response.status === 'success' ? 'success' : 'error'

      const action = data.request.action || ''
      const symbol = data.request.symbol || ''
      const quantity = data.request.quantity || ''
      const orderid = data.response.orderid || data.request.orderid || ''
      const apiType = data.request.api_type || ''

      if (data.response.status === 'error') {
        message = `Error: ${data.response.message}`
        if (symbol) message = `${symbol} - ${message}`
      } else if (apiType === 'cancelorder') {
        message = orderid ? `Order Cancelled - ID: ${orderid}` : 'Order Cancelled'
      } else if (apiType === 'cancelallorder') {
        message = data.response.message || 'All Orders Cancelled'
      } else if (apiType === 'modifyorder') {
        message = orderid ? `Order Modified - ID: ${orderid}` : 'Order Modified'
      } else if (apiType === 'closeposition') {
        message = data.response.message || 'Position Closed'
      } else if (
        apiType === 'placesmartorder' &&
        data.response.message &&
        (data.response.message.includes('Positions Already Matched') ||
          data.response.message.includes('No OpenPosition Found'))
      ) {
        message = data.response.message
        type = 'info'
      } else {
        if (!action && !symbol && !orderid) {
          return
        }

        if (action && symbol) {
          message = `${action} Order Placed for Symbol: ${symbol}`
          if (quantity) message += `, Qty: ${quantity}`
          if (orderid) message += `, Order ID: ${orderid}`

          if (apiType === 'placesmartorder' && data.request.position_size) {
            message += `, Size: ${data.request.position_size}`
          }
        } else if (orderid) {
          message = `Order Placed - ID: ${orderid}`
        } else {
          return
        }
      }

      if (message) {
        showCategoryToast(type, message, 'analyzer')
      }
    })

    return () => {
      socket.disconnect()
      ;['click', 'touchstart', 'keydown'].forEach((eventType) => {
        document.removeEventListener(eventType, handleInteraction)
      })
    }
  }, [isAuthenticated, playAlertSound, enableAudio])

  return {
    socket: socketRef.current,
    playAlertSound,
  }
}

```


---

# FILE: frontend\src\hooks\useSupportedExchanges.ts

```ts
import { useMemo } from 'react'
import { useBrokerStore } from '@/stores/brokerStore'

/** Exchange option for dropdowns */
export interface ExchangeOption {
  value: string
  label: string
}

/** Default underlyings per F&O exchange */
const UNDERLYINGS: Record<string, string[]> = {
  NFO: ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY'],
  BFO: ['SENSEX', 'BANKEX'],
  MCX: ['GOLDM', 'CRUDEOIL', 'SILVERM', 'NATURALGAS', 'COPPER'],
  CDS: ['USDINR', 'EURINR', 'GBPINR', 'JPYINR'],
  CRYPTO: ['BTC', 'ETH', 'SOL', 'BNB', 'XRP'],
}

/** Index exchanges excluded from trading/FNO lists */
const INDEX_EXCHANGES = new Set([
  'NSE_INDEX',
  'BSE_INDEX',
  'MCX_INDEX',
  'CDS_INDEX',
  'GLOBAL_INDEX',
])

/** F&O exchange codes (includes MCX/CDS/NCO which also have options) */
const FNO_CODES = new Set(['NFO', 'BFO', 'MCX', 'CDS', 'NCO', 'CRYPTO'])

/** Fallback exchanges when capabilities haven't loaded yet (backward compatible) */
const FALLBACK_EXCHANGES = ['NSE', 'BSE', 'NFO', 'BFO', 'CDS', 'MCX', 'CRYPTO']

/**
 * Central hook for broker-aware exchange filtering.
 *
 * All pages should use this instead of hardcoding exchange arrays.
 * Reads from brokerStore (populated at login via /api/broker/capabilities).
 *
 * Returns categorized exchange lists so each page picks what it needs:
 * - Tools pages → fnoExchanges, defaultFnoExchange, defaultUnderlyings
 * - TradingView/GoCharting → tradingExchanges, defaultExchange
 * - Historify → allExchanges
 * - Search → tradingExchanges
 */
export function useSupportedExchanges() {
  const capabilities = useBrokerStore((s) => s.capabilities)

  return useMemo(() => {
    // Use fallback exchanges when capabilities haven't loaded yet (backward compatible)
    const supported = capabilities?.supported_exchanges ?? FALLBACK_EXCHANGES
    const isCrypto = capabilities?.broker_type === 'crypto'

    // All exchanges from plugin.json
    const allExchanges: ExchangeOption[] = supported.map((e) => ({ value: e, label: e }))

    // Trading exchanges: exclude _INDEX suffixed exchanges
    const tradingExchanges: ExchangeOption[] = supported
      .filter((e) => !INDEX_EXCHANGES.has(e))
      .map((e) => ({ value: e, label: e }))

    // F&O exchanges: NFO, BFO, or CRYPTO (only those the broker supports)
    const fnoExchanges: ExchangeOption[] = supported
      .filter((e) => FNO_CODES.has(e))
      .map((e) => ({ value: e, label: e }))

    // Exchanges shown inside /tools pages (Strategy Builder, Option Chain,
    // OI Tracker, Straddle Chart, Custom Straddle etc.). MCX and CDS are
    // temporarily excluded — the option chain + quotes plumbing doesn't
    // fully support them yet. CRYPTO is retained for crypto-only brokers.
    const toolsFnoExchanges: ExchangeOption[] = fnoExchanges.filter(
      (e) => e.value !== 'MCX' && e.value !== 'CDS'
    )

    // Defaults
    const defaultExchange = tradingExchanges[0]?.value ?? (isCrypto ? 'CRYPTO' : 'NSE')
    const defaultFnoExchange = fnoExchanges[0]?.value ?? (isCrypto ? 'CRYPTO' : 'NFO')
    const defaultToolsFnoExchange = toolsFnoExchanges[0]?.value ?? (isCrypto ? 'CRYPTO' : 'NFO')

    // Underlyings filtered to only supported FNO exchanges
    const defaultUnderlyings: Record<string, string[]> = {}
    for (const ex of fnoExchanges) {
      if (UNDERLYINGS[ex.value]) {
        defaultUnderlyings[ex.value] = UNDERLYINGS[ex.value]
      }
    }

    return {
      /** All exchanges from plugin.json (including _INDEX) */
      allExchanges,
      /** Trading exchanges (no _INDEX) — for TradingView, GoCharting, Search */
      tradingExchanges,
      /** Broker-reported F&O exchanges (NFO, BFO, MCX, CDS, CRYPTO). */
      fnoExchanges,
      /**
       * F&O exchanges allowed in /tools pages today — NFO, BFO, CRYPTO only.
       * Prefer this over `fnoExchanges` in every route under /tools/* .
       */
      toolsFnoExchanges,
      /** First trading exchange */
      defaultExchange,
      /** First F&O exchange */
      defaultFnoExchange,
      /** First tools-supported F&O exchange */
      defaultToolsFnoExchange,
      /** Underlyings map filtered to supported F&O exchanges */
      defaultUnderlyings,
      /** Quick check: is this a crypto broker? */
      isCrypto,
    }
  }, [capabilities])
}

```


---

# FILE: frontend\src\hooks\useWebSocketTester.ts

```ts
import { useCallback, useEffect, useRef, useState } from 'react'
import type { LatencySample, WebSocketMessage } from '@/types/websocket'

// Fetch CSRF token for authenticated requests
async function fetchCSRFToken(): Promise<string> {
  const response = await fetch('/auth/csrf-token', { credentials: 'include' })
  const data = await response.json()
  return data.csrf_token
}

const MAX_MESSAGES = 1000
const MAX_LATENCY_SAMPLES = 100

interface UseWebSocketTesterReturn {
  // Connection state
  isConnected: boolean
  isConnecting: boolean
  isAuthenticated: boolean
  wsUrl: string | null
  error: string | null
  connect: () => Promise<void>
  disconnect: () => void

  // Messages
  sendMessage: (message: string | object) => boolean
  messages: WebSocketMessage[]
  clearMessages: () => void
  exportMessages: () => void

  // Latency testing
  ping: () => string
  lastLatency: number | null
  averageLatency: number | null

  // Config
  autoReconnect: boolean
  setAutoReconnect: (value: boolean) => void
}

export function useWebSocketTester(_apiKey?: string): UseWebSocketTesterReturn {
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [wsUrl, setWsUrl] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [messages, setMessages] = useState<WebSocketMessage[]>([])
  const [autoReconnect, setAutoReconnect] = useState(true)
  const [lastLatency, setLastLatency] = useState<number | null>(null)
  const [averageLatency, setAverageLatency] = useState<number | null>(null)

  const socketRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pingIdRef = useRef<string | null>(null)
  const pingStartTimeRef = useRef<number>(0)
  const latencySamplesRef = useRef<LatencySample[]>([])
  const isReconnectingRef = useRef(false)
  const userInitiatedCloseRef = useRef(false)

  const getCsrfToken = useCallback(async () => fetchCSRFToken(), [])

  // Add message to log
  const addMessage = useCallback(
    (direction: WebSocketMessage['direction'], data: unknown, rawData?: string) => {
      const message: WebSocketMessage = {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        direction,
        timestamp: Date.now(),
        data,
        rawData,
      }
      setMessages((prev) => {
        const updated = [message, ...prev]
        return updated.slice(0, MAX_MESSAGES)
      })
    },
    []
  )

  // Handle incoming WebSocket messages
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data)
        const type = (data.type || data.status) as string

        switch (type) {
          case 'auth':
            if (data.status === 'success') {
              setIsAuthenticated(true)
              setError(null)
              addMessage('system', { message: 'Authentication successful' })
            } else {
              setError(`Authentication failed: ${data.message}`)
              addMessage('error', { message: `Authentication failed: ${data.message}` })
            }
            break

          case 'pong':
            // Calculate latency from ping response
            if (data._pingId === pingIdRef.current) {
              const latency = Date.now() - pingStartTimeRef.current
              setLastLatency(latency)
              latencySamplesRef.current.push({ timestamp: Date.now(), latency })
              if (latencySamplesRef.current.length > MAX_LATENCY_SAMPLES) {
                latencySamplesRef.current.shift()
              }
              // Calculate average
              const avg =
                latencySamplesRef.current.reduce((sum, s) => sum + s.latency, 0) /
                latencySamplesRef.current.length
              setAverageLatency(Math.round(avg))
              pingIdRef.current = null
              addMessage('system', { message: `Pong received (${latency}ms)` })
            } else {
              // Show pong for manual ping messages (without _pingId)
              addMessage('received', data, event.data)
            }
            break

          case 'error':
            setError(`WebSocket error: ${data.message}`)
            addMessage('error', data)
            break

          default:
            // Log all other messages
            addMessage('received', data, event.data)
        }
      } catch {
        // Add raw message for non-JSON
        addMessage('received', event.data, event.data)
      }
    },
    [addMessage]
  )

  // Connect to WebSocket
  const connect = useCallback(async () => {
    if (socketRef.current?.readyState === WebSocket.OPEN || isReconnectingRef.current) {
      return
    }

    isReconnectingRef.current = true
    setIsConnecting(true)
    setError(null)

    try {
      const csrfToken = await getCsrfToken()

      // Get WebSocket config (URL from .env)
      const configResponse = await fetch('/api/websocket/config', {
        headers: { 'X-CSRFToken': csrfToken },
        credentials: 'include',
      })
      const configData = await configResponse.json()

      if (configData.status !== 'success') {
        throw new Error('Failed to get WebSocket configuration')
      }

      const url = configData.websocket_url
      setWsUrl(url)

      const socket = new WebSocket(url)

      socket.onopen = async () => {
        setIsConnected(true)
        setIsConnecting(false)
        addMessage('system', { message: 'Connected to WebSocket server' })

        try {
          // Get API key for authentication
          const authCsrfToken = await getCsrfToken()
          const apiKeyResponse = await fetch('/api/websocket/apikey', {
            headers: { 'X-CSRFToken': authCsrfToken },
            credentials: 'include',
          })
          const apiKeyData = await apiKeyResponse.json()

          if (apiKeyData.status === 'success' && apiKeyData.api_key) {
            const authMessage = { action: 'authenticate', api_key: apiKeyData.api_key }
            socket.send(JSON.stringify(authMessage))
            addMessage('sent', authMessage)
          } else {
            setError('No API key found - please generate one at /apikey')
            addMessage('error', { message: 'No API key found' })
          }
        } catch (err) {
          setError(`Authentication error: ${err}`)
          addMessage('error', { message: `Authentication error: ${err}` })
        }
      }

      socket.onclose = (event) => {
        setIsConnected(false)
        setIsConnecting(false)
        setIsAuthenticated(false)
        isReconnectingRef.current = false

        if (!event.wasClean) {
          addMessage('system', { message: `Connection closed unexpectedly: ${event.code}` })
        } else {
          addMessage('system', { message: `Connection closed: ${event.code}` })
        }

        // Only reconnect if NOT user-initiated AND autoReconnect is enabled
        if (autoReconnect && !userInitiatedCloseRef.current) {
          reconnectTimeoutRef.current = setTimeout(() => {
            userInitiatedCloseRef.current = false // Reset for next attempt
            connect()
          }, 3000)
        }
        userInitiatedCloseRef.current = false
      }

      socket.onerror = () => {
        setError('WebSocket connection error')
        setIsConnecting(false)
        addMessage('error', { message: 'WebSocket connection error' })
      }

      socket.onmessage = handleMessage

      socketRef.current = socket
    } catch (err) {
      setError(`Connection failed: ${err}`)
      setIsConnecting(false)
      addMessage('error', { message: `Connection failed: ${err}` })
    }
  }, [getCsrfToken, handleMessage, autoReconnect, addMessage])

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    userInitiatedCloseRef.current = true

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    if (socketRef.current) {
      socketRef.current.close(1000, 'User disconnect')
      socketRef.current = null
    }
    setIsConnected(false)
    setIsAuthenticated(false)
    addMessage('system', { message: 'Disconnected by user' })
  }, [addMessage])

  // Send message
  const sendMessage = useCallback(
    (message: string | object): boolean => {
      if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
        setError('Cannot send message: not connected')
        return false
      }

      try {
        const messageObj = typeof message === 'string' ? JSON.parse(message) : message
        const messageStr = JSON.stringify(messageObj)
        socketRef.current.send(messageStr)
        addMessage('sent', messageObj, messageStr)
        return true
      } catch (err) {
        setError(`Failed to send message: ${err}`)
        addMessage('error', { message: `Failed to send: ${err}` })
        return false
      }
    },
    [addMessage]
  )

  // Ping for latency testing
  const ping = useCallback((): string => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      setError('Cannot ping: not connected')
      return 'error'
    }

    const pingId = `ping-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    pingIdRef.current = pingId
    pingStartTimeRef.current = Date.now()

    const pingMessage = { _pingId: pingId, action: 'ping', timestamp: Date.now() }
    socketRef.current.send(JSON.stringify(pingMessage))
    addMessage('sent', pingMessage)

    return pingId
  }, [addMessage])

  // Clear messages
  const clearMessages = useCallback(() => {
    setMessages([])
    latencySamplesRef.current = []
    setLastLatency(null)
    setAverageLatency(null)
  }, [])

  // Export messages
  const exportMessages = useCallback(() => {
    const exportData = {
      exportedAt: new Date().toISOString(),
      totalMessages: messages.length,
      messages: messages.map((m) => ({
        ...m,
        timestamp: new Date(m.timestamp).toISOString(),
      })),
    }
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `websocket-messages-${Date.now()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }, [messages])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (socketRef.current) {
        socketRef.current.close()
      }
    }
  }, [])

  return {
    isConnected,
    isConnecting,
    isAuthenticated,
    wsUrl,
    error,
    connect,
    disconnect,
    sendMessage,
    messages,
    clearMessages,
    exportMessages,
    ping,
    lastLatency,
    averageLatency,
    autoReconnect,
    setAutoReconnect,
  }
}

```
