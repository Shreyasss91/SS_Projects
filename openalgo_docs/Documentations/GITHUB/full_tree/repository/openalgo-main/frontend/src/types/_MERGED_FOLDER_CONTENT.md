# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\frontend\src\types



---

# FILE: frontend\src\types\admin.ts

```ts
// Admin types for Freeze Qty, Holidays, and Market Timings

export interface FreezeQty {
  id: number
  exchange: string
  symbol: string
  freeze_qty: number
}

export interface AddFreezeQtyRequest {
  exchange: string
  symbol: string
  freeze_qty: number
}

export interface UpdateFreezeQtyRequest {
  freeze_qty: number
}

export interface SpecialSessionExchange {
  exchange: string
  start_time: string // HH:MM format for UI, converted to epoch ms before sending
  end_time: string
}

export interface Holiday {
  id: number
  date: string
  day_name: string
  description: string
  holiday_type: 'TRADING_HOLIDAY' | 'SETTLEMENT_HOLIDAY' | 'SPECIAL_SESSION'
  closed_exchanges: string[]
  open_exchanges?: SpecialSessionExchange[]
}

export interface AddHolidayRequest {
  date: string
  description: string
  holiday_type: 'TRADING_HOLIDAY' | 'SETTLEMENT_HOLIDAY' | 'SPECIAL_SESSION'
  closed_exchanges: string[]
  open_exchanges?: Array<{
    exchange: string
    start_time: number // epoch milliseconds
    end_time: number
  }>
}

export interface HolidaysResponse {
  status: string
  data: Holiday[]
  current_year: number
  years: number[]
  exchanges: string[]
}

export interface MarketTiming {
  id: number | null
  exchange: string
  start_time: string
  end_time: string
  start_offset: number
  end_offset: number
}

export interface TodayTiming {
  exchange: string
  start_time: string
  end_time: string
}

export interface UpdateTimingRequest {
  start_time: string
  end_time: string
}

export interface TimingsResponse {
  status: string
  data: MarketTiming[]
  today_timings: TodayTiming[]
  today: string
  exchanges: string[]
}

export interface AdminStats {
  freeze_count: number
  holiday_count: number
}

// ============================================================================
// Diagnostics types
// ============================================================================

export interface ErrorEntry {
  ts?: string
  level?: string
  logger?: string
  module?: string
  file?: string
  message?: string
  exception?: string[] | string
  request?: { method?: string; path?: string; ip?: string }
}

export interface ErrorsListResponse {
  status: string
  data: ErrorEntry[]
  count: number
  scanned: number
  total_in_window: number
}

export interface ErrorsStats {
  status: string
  total: number
  by_level: Record<string, number>
  last_24h: number
  last_1h: number
}

export interface SystemMode {
  analyze_mode: boolean | null
  label: string
}

export interface SystemHost {
  system?: string
  release?: string
  version?: string
  machine?: string
  platform?: string
  distro?: { name?: string; id?: string; version_id?: string } | null
  in_docker?: boolean
  is_raspberry_pi?: boolean
  rpi_model?: string | null
  is_termux?: boolean
  is_android?: boolean
}

export interface SystemRuntime {
  python_version?: string
  python_implementation?: string
  eventlet_active?: boolean
  wsgi_hint?: string
  process_uptime_seconds?: number | null
}

export interface SystemHardware {
  cpu_count?: number | null
  cpu_model?: string | null
  memory_total_mb?: number | null
  memory_available_mb?: number | null
  memory_percent?: number | null
  disk_log?: { total_gb: number; free_gb: number; used_percent: number } | null
  disk_db?: { total_gb: number; free_gb: number; used_percent: number } | null
}

export interface SystemBuild {
  openalgo_version?: string | null
  openalgo_sdk_version?: string | null
  git_branch?: string | null
  git_commit?: string | null
  frontend_build_time?: string | null
}

export interface SystemConfig {
  valid_brokers: string[]
  log_level: string
  log_to_file: boolean
  log_dir: string
  websocket_host: string
  websocket_port: string
  max_symbols_per_websocket: string
  max_websocket_connections: string
  api_rate_limit: string
  flask_debug: boolean
  secrets_present: Record<string, boolean>
  /**
   * Per-secret randomization status. True = the value is plausibly
   * install-specific (random hex of sufficient length, not the publicly-
   * known sample placeholder). False = the value is a default/placeholder
   * — i.e. functionally no protection. See blueprints/admin.py:_secret_strength_status.
   */
  secret_strength?: Record<string, boolean>
}

export interface SystemBrokers {
  configured_brokers: string[]
  active_broker: string | null
  user_logged_in: boolean
}

export interface SystemDatabase {
  name: string
  exists: boolean
  size_mb: number
  modified: string | null
}

export interface SystemTime {
  server_time: string
  server_tz: string | null
  ist_time: string | null
}

export interface SystemInfo {
  mode: SystemMode
  host: SystemHost
  runtime: SystemRuntime
  hardware: SystemHardware
  build: SystemBuild
  config: SystemConfig
  brokers: SystemBrokers
  databases: SystemDatabase[]
  time: SystemTime
}

export interface DiagnosticCheck {
  name: string
  ok: boolean
  ms: number | null
  detail: string
}

export interface DiagnosticsResponse {
  status: string
  ran_at: string
  checks: DiagnosticCheck[]
}

export interface ErrorGroup {
  fingerprint: string
  count: number
  level?: string
  logger?: string
  module?: string
  first_seen?: string
  last_seen?: string
  sample: ErrorEntry
}

export interface ErrorGroupsResponse {
  status: string
  groups: ErrorGroup[]
  total_entries: number
  total_groups: number
}

// ============================================================================
// Remote MCP — admin types
// ============================================================================

export interface OAuthClient {
  client_id: string
  client_name: string
  redirect_uris: string[]
  scopes_requested: string[]
  is_public: boolean
  approved: boolean
  approved_at: string | null
  revoked_at: string | null
  created_at: string | null
  last_used_at: string | null
}

export interface OAuthClientsResponse {
  status: string
  mcp_enabled: boolean
  clients: OAuthClient[]
  summary: {
    pending: number
    approved: number
    revoked: number
  }
}

export interface MCPAuditEntry {
  ts?: string
  jti?: string
  client_id?: string
  tool?: string
  scope?: string
  params_hash?: string
  duration_ms?: number
  outcome?: string
  request_ip?: string
}

export interface MCPAuditResponse {
  status: string
  mcp_enabled: boolean
  data: MCPAuditEntry[]
  count: number
  scanned?: number
  total_in_window: number
}

export interface MCPSettings {
  http_enabled: boolean
  public_url: string
  mcp_url: string
  require_approval: boolean
  write_scope_enabled: boolean
}

export interface MCPSettingsResponse {
  status: string
  settings: MCPSettings
}

export interface MCPSettingsUpdateRequest {
  http_enabled?: boolean
  public_url?: string
  require_approval?: boolean
  write_scope_enabled?: boolean
}

export interface MCPSettingsUpdateResponse {
  status: string
  message?: string
  restart_required?: boolean
  restart_command?: string
  settings_pending?: MCPSettings
}

```


---

# FILE: frontend\src\types\auth.ts

```ts
export interface User {
  username: string
  broker?: string
  isLoggedIn: boolean
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface LoginResponse {
  status: 'success' | 'error'
  message?: string
}

export interface BrokerInfo {
  name: string
  displayName: string
  authType: 'oauth' | 'totp' | 'credentials'
  enabled: boolean
  logo?: string
}

export interface SessionInfo {
  logged_in: boolean
  user?: string
  broker?: string
  analyze_mode?: boolean
}

export interface TOTPCredentials {
  totp: string
  userid?: string
  password?: string
  apikey?: string
  apisecret?: string
}

```


---

# FILE: frontend\src\types\chartink.ts

```ts
// Chartink Strategy Types

export interface ChartinkStrategy {
  id: number
  name: string
  webhook_id: string
  is_active: boolean
  is_intraday: boolean
  start_time: string | null
  end_time: string | null
  squareoff_time: string | null
  created_at: string
  updated_at: string
}

export interface ChartinkSymbolMapping {
  id: number
  strategy_id: number
  chartink_symbol: string
  exchange: 'NSE' | 'BSE'
  quantity: number
  product_type: 'MIS' | 'CNC'
  created_at: string
}

export interface CreateChartinkStrategyRequest {
  name: string
  strategy_type: 'intraday' | 'positional'
  start_time?: string
  end_time?: string
  squareoff_time?: string
}

export interface AddChartinkSymbolRequest {
  symbol: string // Backend expects 'symbol', stores as 'chartink_symbol'
  exchange: 'NSE' | 'BSE'
  quantity: number
  product_type: 'MIS' | 'CNC'
}

// Chartink only supports NSE and BSE
export const CHARTINK_EXCHANGES = ['NSE', 'BSE'] as const
export type ChartinkExchange = (typeof CHARTINK_EXCHANGES)[number]

// Chartink only supports MIS and CNC
export const CHARTINK_PRODUCTS = ['MIS', 'CNC'] as const
export type ChartinkProduct = (typeof CHARTINK_PRODUCTS)[number]

```


---

# FILE: frontend\src\types\flow.ts

```ts
import type { Edge as ReactFlowEdge, Node as ReactFlowNode } from '@xyflow/react'

// =============================================================================
// TRIGGER NODE DATA TYPES
// =============================================================================

/** Schedule Trigger - Start workflow on schedule */
export interface StartNodeData {
  label?: string
  scheduleType: 'once' | 'daily' | 'weekly' | 'interval'
  time: string
  days?: number[]
  executeAt?: string
  intervalMinutes?: number // Legacy - kept for backward compatibility
  intervalValue?: number // New - interval value (e.g., 1, 5, 10)
  intervalUnit?: 'seconds' | 'minutes' | 'hours' // New - interval unit
  marketHoursOnly?: boolean
}

/** Price Alert Trigger - Start when price condition met */
export interface PriceAlertNodeData {
  label?: string
  symbol: string
  exchange: string
  condition: 'above' | 'below' | 'crosses_above' | 'crosses_below'
  price: number
  ltp?: number // Live LTP from quotes API
  enabled?: boolean
}

/** Webhook Trigger - Start from external webhook */
export interface WebhookNodeData {
  label?: string
  symbol?: string
  exchange?: string
  webhookId?: string
  webhookUrl?: string
  webhookUrlWithSymbol?: string
}

/** Position Trigger - Start when position changes */
export interface PositionTriggerNodeData {
  label?: string
  symbol: string
  exchange: string
  product: string
  condition: 'opened' | 'closed' | 'quantity_changed' | 'pnl_above' | 'pnl_below'
  threshold?: number
}

// =============================================================================
// ACTION NODE DATA TYPES
// =============================================================================

/** Place Order - Basic order placement */
export interface PlaceOrderNodeData {
  label?: string
  symbol: string
  exchange: string
  action: 'BUY' | 'SELL'
  quantity: number
  priceType: 'MARKET' | 'LIMIT' | 'SL' | 'SL-M'
  product: 'MIS' | 'CNC' | 'NRML'
  price?: number
  triggerPrice?: number
  disclosedQuantity?: number
  ltp?: number
}

/** Smart Order - Position-aware ordering */
export interface SmartOrderNodeData {
  label?: string
  symbol: string
  exchange: string
  action: 'BUY' | 'SELL'
  quantity: number
  positionSize: number
  priceType: 'MARKET' | 'LIMIT' | 'SL' | 'SL-M'
  product: 'MIS' | 'CNC' | 'NRML'
  price?: number
  triggerPrice?: number
  ltp?: number
}

/** Options Order - ATM/ITM/OTM options trading */
export interface OptionsOrderNodeData {
  label?: string
  underlying: string
  exchange: 'NSE_INDEX' | 'BSE_INDEX'
  expiryDate: string
  offset: string // ATM, ITM1-10, OTM1-10
  optionType: 'CE' | 'PE'
  action: 'BUY' | 'SELL'
  quantity: number
  priceType: 'MARKET' | 'LIMIT'
  product: 'MIS' | 'NRML'
  splitSize?: number
  price?: number
  ltp?: number
}

/** Options Multi-Order - Multi-leg strategies */
export interface OptionsMultiOrderNodeData {
  label?: string
  strategy:
    | 'iron_condor'
    | 'straddle'
    | 'strangle'
    | 'bull_call_spread'
    | 'bear_put_spread'
    | 'custom'
  underlying: string
  exchange: 'NSE_INDEX' | 'BSE_INDEX'
  expiryDate: string
  legs: Array<{
    offset: string
    optionType: 'CE' | 'PE'
    action: 'BUY' | 'SELL'
    quantity: number
    expiryDate?: string // For calendar spreads
  }>
  priceType: 'MARKET' | 'LIMIT'
  product: 'MIS' | 'NRML'
}

/** Basket Order - Multiple orders at once */
export interface BasketOrderNodeData {
  label?: string
  strategy?: string
  orders: Array<{
    symbol: string
    exchange: string
    action: 'BUY' | 'SELL'
    quantity: number
    priceType: 'MARKET' | 'LIMIT'
    product: 'MIS' | 'CNC' | 'NRML'
    price?: number
  }>
}

/** Split Order - Large order splitting */
export interface SplitOrderNodeData {
  label?: string
  symbol: string
  exchange: string
  action: 'BUY' | 'SELL'
  quantity: number
  splitSize: number
  priceType: 'MARKET' | 'LIMIT'
  product: 'MIS' | 'CNC' | 'NRML'
  price?: number
  delayMs?: number
}

/** Modify Order - Modify existing order */
export interface ModifyOrderNodeData {
  label?: string
  orderId: string
  symbol: string
  exchange: string
  action: 'BUY' | 'SELL'
  newQuantity?: number
  priceType?: 'MARKET' | 'LIMIT' | 'SL' | 'SL-M'
  product?: 'MIS' | 'CNC' | 'NRML'
  newPrice?: number
  newTriggerPrice?: number
}

/** Cancel Order - Cancel specific order */
export interface CancelOrderNodeData {
  label?: string
  orderId: string
}

/** Cancel All Orders - Cancel all open orders */
export interface CancelAllOrdersNodeData {
  label?: string
  // No specific fields needed
}

/** Close Positions - Square off positions */
export interface ClosePositionsNodeData {
  label?: string
  exchange?: string // Optional filter
  product?: string // Optional filter
}

// =============================================================================
// CONDITION NODE DATA TYPES
// =============================================================================

/** Condition Node - If/Else branching */
export interface ConditionNodeData {
  label?: string
  conditions: Array<{
    variable: string // e.g., 'ltp', 'position', 'pnl', 'time'
    operator: '>' | '<' | '==' | '>=' | '<=' | '!='
    value: string | number
  }>
  logic: 'AND' | 'OR'
}

/** Position Check - Check position before action */
export interface PositionCheckNodeData {
  label?: string
  symbol: string
  exchange: string
  product: 'MIS' | 'CNC' | 'NRML'
  condition:
    | 'exists'
    | 'not_exists'
    | 'quantity_above'
    | 'quantity_below'
    | 'pnl_above'
    | 'pnl_below'
  threshold?: number
}

/** Fund Check - Check available funds */
export interface FundCheckNodeData {
  label?: string
  minAvailable: number
}

/** Time Window - Check if within time range */
export interface TimeWindowNodeData {
  label?: string
  startTime: string
  endTime: string
  days?: number[]
  invertCondition?: boolean
}

/** Time Condition - Check if time equals/passes specific time (Entry/Exit) */
export interface TimeConditionNodeData {
  label?: string
  conditionType: 'entry' | 'exit' | 'custom'
  targetTime: string
  operator: '==' | '>=' | '<=' | '>' | '<'
}

/** Greeks Condition - Check option greeks */
export interface GreeksConditionNodeData {
  label?: string
  symbol: string
  exchange: string
  greek: 'delta' | 'gamma' | 'theta' | 'vega' | 'iv'
  operator: '>' | '<' | '==' | '>=' | '<=' | '!='
  value: number
}

/** Price Condition - Check price condition */
export interface PriceConditionNodeData {
  label?: string
  symbol: string
  exchange: string
  field: 'ltp' | 'open' | 'high' | 'low' | 'prev_close' | 'change_percent'
  operator: '>' | '<' | '==' | '>=' | '<=' | '!='
  value: number
}

// =============================================================================
// DATA NODE DATA TYPES
// =============================================================================

/** Get Quote - Fetch real-time quote */
export interface GetQuoteNodeData {
  label?: string
  symbol: string
  exchange: string
  outputVariable?: string
}

/** Get Multi-Quotes - Fetch multiple quotes */
export interface GetMultiQuotesNodeData {
  label?: string
  symbols: Array<{
    symbol: string
    exchange: string
  }>
  outputVariable?: string
}

/** Get Option Chain - Fetch option chain */
export interface GetOptionChainNodeData {
  label?: string
  underlying: string
  exchange: 'NSE_INDEX' | 'BSE_INDEX'
  expiryDate: string
  strikeCount?: number
  outputVariable?: string
}

/** Get Positions - Fetch current positions */
export interface GetPositionsNodeData {
  label?: string
  outputVariable?: string
}

/** Get Holdings - Fetch holdings */
export interface GetHoldingsNodeData {
  label?: string
  outputVariable?: string
}

/** Get Order Status - Check order status */
export interface GetOrderStatusNodeData {
  label?: string
  orderId: string
  waitForCompletion?: boolean
  outputVariable?: string
}

/** Calculate Greeks - Calculate option greeks */
export interface CalculateGreeksNodeData {
  label?: string
  symbol: string
  exchange: string
  underlyingSymbol: string
  underlyingExchange: string
  interestRate?: number
  outputVariable?: string
}

/** Get Market Depth - Fetch bid/ask depth */
export interface GetDepthNodeData {
  label?: string
  symbol: string
  exchange: string
  outputVariable?: string
}

/** Get History - Fetch historical OHLCV data */
export interface HistoryNodeData {
  label?: string
  symbol: string
  exchange: string
  interval: '1m' | '5m' | '15m' | '30m' | '1h' | '1d'
  days: number
  outputVariable?: string
}

/** Get Open Position - Fetch current position for a symbol */
export interface OpenPositionNodeData {
  label?: string
  symbol: string
  exchange: string
  product: 'MIS' | 'CNC' | 'NRML'
  outputVariable?: string
}

/** Get Expiry Dates - Fetch expiry dates for F&O */
export interface ExpiryNodeData {
  label?: string
  symbol: string
  exchange: string
  instrumenttype?: 'options' | 'futures'
  outputVariable?: string
}

/** Get Intervals - Fetch available intervals for historical data */
export interface IntervalsNodeData {
  label?: string
  outputVariable?: string
}

/** Symbol Node - Get symbol info (lotsize, tick_size, expiry, etc.) */
export interface SymbolNodeData {
  label?: string
  symbol: string // Can use {{variable}} interpolation
  exchange: string
  outputVariable?: string
}

/** OptionSymbol Node - Resolve option symbol from underlying */
export interface OptionSymbolNodeData {
  label?: string
  underlying: string // NIFTY, BANKNIFTY, etc. - can use {{variable}}
  exchange: 'NSE_INDEX' | 'BSE_INDEX'
  expiryDate: string // Format: 30DEC25 - can use {{variable}}
  offset: string // ATM, ITM1-10, OTM1-10 - can use {{variable}}
  optionType: 'CE' | 'PE'
  outputVariable?: string
}

/** OrderBook Node - Get order book */
export interface OrderBookNodeData {
  label?: string
  outputVariable?: string
}

/** TradeBook Node - Get trade book */
export interface TradeBookNodeData {
  label?: string
  outputVariable?: string
}

/** PositionBook Node - Get all positions */
export interface PositionBookNodeData {
  label?: string
  outputVariable?: string
}

/** SyntheticFuture Node - Calculate synthetic future price */
export interface SyntheticFutureNodeData {
  label?: string
  underlying: string // NIFTY, BANKNIFTY, etc.
  exchange: 'NSE_INDEX' | 'BSE_INDEX'
  expiryDate: string // Format: 25NOV25
  outputVariable?: string
}

/** OptionChain Node - Get option chain data */
export interface OptionChainNodeData {
  label?: string
  underlying: string // NIFTY, BANKNIFTY, etc.
  exchange: 'NSE_INDEX' | 'BSE_INDEX'
  expiryDate: string // Format: 30DEC25
  strikeCount?: number // Optional: limit strikes around ATM
  outputVariable?: string
}

/** Holidays Node - Get market holidays */
export interface HolidaysNodeData {
  label?: string
  year?: number // Optional: defaults to current year
  outputVariable?: string
}

/** Timings Node - Get market timings */
export interface TimingsNodeData {
  label?: string
  date?: string // Optional: YYYY-MM-DD format, defaults to today
  outputVariable?: string
}

// =============================================================================
// WEBSOCKET NODE DATA TYPES (Real-time streaming)
// =============================================================================

/** Subscribe LTP Node - Real-time LTP streaming */
export interface SubscribeLTPNodeData {
  label?: string
  symbol: string // Can use {{variable}} interpolation
  exchange: string
  outputVariable?: string // Variable to store live LTP
}

/** Subscribe Quote Node - Real-time Quote streaming (OHLC + volume) */
export interface SubscribeQuoteNodeData {
  label?: string
  symbol: string // Can use {{variable}} interpolation
  exchange: string
  outputVariable?: string // Variable to store live quote data
}

/** Subscribe Depth Node - Real-time Depth streaming (order book) */
export interface SubscribeDepthNodeData {
  label?: string
  symbol: string // Can use {{variable}} interpolation
  exchange: string
  outputVariable?: string // Variable to store live depth data
}

/** Unsubscribe Node - Stop real-time streaming */
export interface UnsubscribeNodeData {
  label?: string
  symbol?: string // Symbol to unsubscribe, or empty for all
  exchange?: string
  streamType: 'ltp' | 'quote' | 'depth' | 'all'
}

// =============================================================================
// RISK MANAGEMENT NODE DATA TYPES
// =============================================================================

/** Holdings Node - Get portfolio holdings */
export interface HoldingsNodeData {
  label?: string
  outputVariable?: string
}

/** Funds Node - Get account funds */
export interface FundsNodeData {
  label?: string
  outputVariable?: string
}

/** Margin Node - Calculate margin requirements */
export interface MarginNodeData {
  label?: string
  positions: Array<{
    symbol: string
    exchange: string
    action: 'BUY' | 'SELL'
    quantity: number
    product: 'MIS' | 'CNC' | 'NRML'
    priceType: 'MARKET' | 'LIMIT'
  }>
  outputVariable?: string
}

// =============================================================================
// UTILITY NODE DATA TYPES
// =============================================================================

/** Telegram Alert - Send notification */
export interface TelegramAlertNodeData {
  label?: string
  message: string
  username?: string
}

/** Delay Node - Wait for duration */
export interface DelayNodeData {
  label?: string
  delayMs?: number // Legacy: milliseconds
  delayValue?: number // New: value
  delayUnit?: 'seconds' | 'minutes' | 'hours' // New: unit
}

/** Wait Until Node - Pause until specific time */
export interface WaitUntilNodeData {
  label?: string
  targetTime: string
  checkIntervalMs?: number
}

/** Log Node - Log message */
export interface LogNodeData {
  label?: string
  message: string
  level: 'info' | 'warn' | 'error'
}

/** Variable Node - Store/calculate values */
export interface VariableNodeData {
  label?: string
  variableName: string
  operation:
    | 'set'
    | 'get'
    | 'add'
    | 'subtract'
    | 'multiply'
    | 'divide'
    | 'parse_json'
    | 'stringify'
    | 'increment'
    | 'decrement'
    | 'append'
  value: string | number | object
  sourceVariable?: string // For operations that read from another variable
  jsonPath?: string // For accessing nested JSON properties like "data.ltp"
}

/** Math Expression Node - Evaluate mathematical expressions */
export interface MathExpressionNodeData {
  label?: string
  expression: string // e.g., "({{ltp}} * {{lotSize}}) + {{brokerage}}"
  outputVariable: string // Variable to store result
}

/** Loop Node - Iterate over items */
export interface LoopNodeData {
  label?: string
  items: string[] | number
  itemVariable: string
}

// =============================================================================
// UNION TYPES
// =============================================================================

/** All Trigger Node Data Types */
export type TriggerNodeData =
  | StartNodeData
  | PriceAlertNodeData
  | WebhookNodeData
  | PositionTriggerNodeData

/** All Action Node Data Types */
export type ActionNodeData =
  | PlaceOrderNodeData
  | SmartOrderNodeData
  | OptionsOrderNodeData
  | OptionsMultiOrderNodeData
  | BasketOrderNodeData
  | SplitOrderNodeData
  | ModifyOrderNodeData
  | CancelOrderNodeData
  | CancelAllOrdersNodeData
  | ClosePositionsNodeData

/** All Condition Node Data Types */
export type ConditionNodeDataTypes =
  | ConditionNodeData
  | PositionCheckNodeData
  | FundCheckNodeData
  | TimeWindowNodeData
  | TimeConditionNodeData
  | GreeksConditionNodeData
  | PriceConditionNodeData

/** All Data Node Data Types */
export type DataNodeData =
  | GetQuoteNodeData
  | GetMultiQuotesNodeData
  | GetOptionChainNodeData
  | GetPositionsNodeData
  | GetHoldingsNodeData
  | GetOrderStatusNodeData
  | CalculateGreeksNodeData
  | GetDepthNodeData
  | HistoryNodeData
  | OpenPositionNodeData
  | ExpiryNodeData
  | IntervalsNodeData
  | SymbolNodeData
  | OptionSymbolNodeData
  | OrderBookNodeData
  | TradeBookNodeData
  | PositionBookNodeData
  | SyntheticFutureNodeData
  | OptionChainNodeData
  | HolidaysNodeData
  | TimingsNodeData
  | SubscribeLTPNodeData
  | SubscribeQuoteNodeData
  | SubscribeDepthNodeData
  | UnsubscribeNodeData
  | HoldingsNodeData
  | FundsNodeData
  | MarginNodeData

/** All Utility Node Data Types */
export type UtilityNodeData =
  | TelegramAlertNodeData
  | DelayNodeData
  | WaitUntilNodeData
  | LogNodeData
  | VariableNodeData
  | MathExpressionNodeData
  | LoopNodeData

/** Union of all node data types */
export type NodeData =
  | TriggerNodeData
  | ActionNodeData
  | ConditionNodeDataTypes
  | DataNodeData
  | UtilityNodeData

// =============================================================================
// TYPED NODE DEFINITIONS
// Using Node type directly instead of custom typed nodes to avoid type constraints
// =============================================================================

/** Generic custom node type - using any to avoid type constraints */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type CustomNode = ReactFlowNode<any>

/** Custom edge type */
export type CustomEdge = ReactFlowEdge

// =============================================================================
// NODE TYPE CONSTANTS
// =============================================================================

export const NODE_TYPES = {
  // Triggers
  START: 'start',
  PRICE_ALERT: 'priceAlert',
  WEBHOOK: 'webhook',
  POSITION_TRIGGER: 'positionTrigger',
  // Actions
  PLACE_ORDER: 'placeOrder',
  SMART_ORDER: 'smartOrder',
  OPTIONS_ORDER: 'optionsOrder',
  OPTIONS_MULTI_ORDER: 'optionsMultiOrder',
  BASKET_ORDER: 'basketOrder',
  SPLIT_ORDER: 'splitOrder',
  MODIFY_ORDER: 'modifyOrder',
  CANCEL_ORDER: 'cancelOrder',
  CANCEL_ALL_ORDERS: 'cancelAllOrders',
  CLOSE_POSITIONS: 'closePositions',
  // Conditions
  CONDITION: 'condition',
  POSITION_CHECK: 'positionCheck',
  FUND_CHECK: 'fundCheck',
  TIME_WINDOW: 'timeWindow',
  TIME_CONDITION: 'timeCondition',
  GREEKS_CONDITION: 'greeksCondition',
  PRICE_CONDITION: 'priceCondition',
  // Data
  GET_QUOTE: 'getQuote',
  GET_MULTI_QUOTES: 'getMultiQuotes',
  GET_OPTION_CHAIN: 'getOptionChain',
  GET_POSITIONS: 'getPositions',
  GET_HOLDINGS: 'getHoldings',
  GET_ORDER_STATUS: 'getOrderStatus',
  CALCULATE_GREEKS: 'calculateGreeks',
  GET_DEPTH: 'getDepth',
  HISTORY: 'history',
  OPEN_POSITION: 'openPosition',
  EXPIRY: 'expiry',
  INTERVALS: 'intervals',
  SYMBOL: 'symbol',
  OPTION_SYMBOL: 'optionSymbol',
  ORDER_BOOK: 'orderBook',
  TRADE_BOOK: 'tradeBook',
  POSITION_BOOK: 'positionBook',
  SYNTHETIC_FUTURE: 'syntheticFuture',
  OPTION_CHAIN: 'optionChain',
  HOLIDAYS: 'holidays',
  TIMINGS: 'timings',
  // WebSocket (Real-time)
  SUBSCRIBE_LTP: 'subscribeLtp',
  SUBSCRIBE_QUOTE: 'subscribeQuote',
  SUBSCRIBE_DEPTH: 'subscribeDepth',
  UNSUBSCRIBE: 'unsubscribe',
  // Risk Management
  HOLDINGS: 'holdings',
  FUNDS: 'funds',
  MARGIN: 'margin',
  // Utilities
  TELEGRAM_ALERT: 'telegramAlert',
  DELAY: 'delay',
  WAIT_UNTIL: 'waitUntil',
  LOG: 'log',
  VARIABLE: 'variable',
  LOOP: 'loop',
} as const

export type NodeType = (typeof NODE_TYPES)[keyof typeof NODE_TYPES]

// =============================================================================
// STORE STATE TYPES
// =============================================================================

/** Workflow Store State */
export interface WorkflowState {
  id: number | null
  name: string
  description: string
  nodes: CustomNode[]
  edges: CustomEdge[]
  selectedNodeId: string | null
  isModified: boolean
  variables: Record<string, unknown>
}

/** Settings State */
export interface SettingsState {
  openalgo_host: string
  openalgo_ws_url: string
  is_configured: boolean
  has_api_key: boolean
}

// =============================================================================
// EXECUTION CONTEXT
// =============================================================================

/** Execution context passed between nodes */
export interface ExecutionContext {
  variables: Record<string, unknown>
  previousResult?: unknown
  logs: Array<{
    time: string
    message: string
    level: 'info' | 'warn' | 'error'
  }>
}

```


---

# FILE: frontend\src\types\option-chain.ts

```ts
export interface OptionChainResponse {
  status: 'success' | 'error'
  underlying: string
  underlying_ltp: number
  underlying_prev_close: number
  expiry_date: string
  atm_strike: number
  chain: OptionStrike[]
  message?: string
}

export interface OptionStrike {
  strike: number
  ce: OptionData | null
  pe: OptionData | null
}

export interface OptionData {
  symbol: string
  label: string
  ltp: number
  bid: number
  ask: number
  bid_qty: number
  ask_qty: number
  open: number
  high: number
  low: number
  prev_close: number
  volume: number
  oi: number
  lotsize: number
  tick_size: number
}

export interface OptionChainParams {
  underlying: string
  exchange: string
  expiry_date: string
  strike_count?: number
}

export interface MarketMetrics {
  total_ce_oi: number
  total_pe_oi: number
  total_ce_volume: number
  total_pe_volume: number
  pcr: number
}

export interface OptionChainState {
  data: OptionChainResponse | null
  isLoading: boolean
  isConnected: boolean
  error: string | null
  lastUpdate: Date | null
}

// Column configuration types
export type ColumnKey =
  | 'ce_oi'
  | 'ce_volume'
  | 'ce_bid_qty'
  | 'ce_bid'
  | 'ce_ltp'
  | 'ce_ask'
  | 'ce_ask_qty'
  | 'ce_spread'
  | 'strike'
  | 'pe_spread'
  | 'pe_ask_qty'
  | 'pe_ask'
  | 'pe_ltp'
  | 'pe_bid'
  | 'pe_bid_qty'
  | 'pe_volume'
  | 'pe_oi'

export type ColumnSide = 'ce' | 'pe' | 'center'

export interface ColumnDefinition {
  key: ColumnKey
  label: string
  side: ColumnSide
  width: string
  align: 'left' | 'center' | 'right'
  defaultVisible: boolean
  formatter?: 'number' | 'price' | 'spread' | 'none'
}

export const COLUMN_DEFINITIONS: ColumnDefinition[] = [
  // CE columns (left side) - ordered left to right
  {
    key: 'ce_oi',
    label: 'OI',
    side: 'ce',
    width: 'w-20',
    align: 'right',
    defaultVisible: true,
    formatter: 'number',
  },
  {
    key: 'ce_volume',
    label: 'Volume',
    side: 'ce',
    width: 'w-20',
    align: 'right',
    defaultVisible: true,
    formatter: 'number',
  },
  {
    key: 'ce_bid_qty',
    label: 'Bid Qty',
    side: 'ce',
    width: 'w-16',
    align: 'right',
    defaultVisible: true,
    formatter: 'number',
  },
  {
    key: 'ce_bid',
    label: 'Bid',
    side: 'ce',
    width: 'w-16',
    align: 'right',
    defaultVisible: true,
    formatter: 'price',
  },
  {
    key: 'ce_ltp',
    label: 'LTP',
    side: 'ce',
    width: 'w-16',
    align: 'right',
    defaultVisible: true,
    formatter: 'price',
  },
  {
    key: 'ce_ask',
    label: 'Ask',
    side: 'ce',
    width: 'w-16',
    align: 'right',
    defaultVisible: true,
    formatter: 'price',
  },
  {
    key: 'ce_ask_qty',
    label: 'Ask Qty',
    side: 'ce',
    width: 'w-16',
    align: 'right',
    defaultVisible: true,
    formatter: 'number',
  },
  {
    key: 'ce_spread',
    label: 'Spread',
    side: 'ce',
    width: 'w-14',
    align: 'right',
    defaultVisible: true,
    formatter: 'spread',
  },
  // Center column
  {
    key: 'strike',
    label: 'Strike',
    side: 'center',
    width: 'w-20',
    align: 'center',
    defaultVisible: true,
    formatter: 'none',
  },
  // PE columns (right side) - ordered left to right
  {
    key: 'pe_spread',
    label: 'Spread',
    side: 'pe',
    width: 'w-14',
    align: 'left',
    defaultVisible: true,
    formatter: 'spread',
  },
  {
    key: 'pe_ask_qty',
    label: 'Ask Qty',
    side: 'pe',
    width: 'w-16',
    align: 'left',
    defaultVisible: true,
    formatter: 'number',
  },
  {
    key: 'pe_ask',
    label: 'Ask',
    side: 'pe',
    width: 'w-16',
    align: 'left',
    defaultVisible: true,
    formatter: 'price',
  },
  {
    key: 'pe_ltp',
    label: 'LTP',
    side: 'pe',
    width: 'w-16',
    align: 'left',
    defaultVisible: true,
    formatter: 'price',
  },
  {
    key: 'pe_bid',
    label: 'Bid',
    side: 'pe',
    width: 'w-16',
    align: 'left',
    defaultVisible: true,
    formatter: 'price',
  },
  {
    key: 'pe_bid_qty',
    label: 'Bid Qty',
    side: 'pe',
    width: 'w-16',
    align: 'left',
    defaultVisible: true,
    formatter: 'number',
  },
  {
    key: 'pe_volume',
    label: 'Volume',
    side: 'pe',
    width: 'w-20',
    align: 'left',
    defaultVisible: true,
    formatter: 'number',
  },
  {
    key: 'pe_oi',
    label: 'OI',
    side: 'pe',
    width: 'w-20',
    align: 'left',
    defaultVisible: true,
    formatter: 'number',
  },
]

export const DEFAULT_COLUMN_ORDER: ColumnKey[] = COLUMN_DEFINITIONS.map((col) => col.key)

export const DEFAULT_VISIBLE_COLUMNS: ColumnKey[] = COLUMN_DEFINITIONS.filter(
  (col) => col.defaultVisible
).map((col) => col.key)

export type BarDataSource = 'oi' | 'volume'
export type BarStyle = 'gradient' | 'solid'

export interface OptionChainPreferences {
  visibleColumns: ColumnKey[]
  columnOrder: ColumnKey[]
  strikeCount: number
  selectedUnderlying: string
  barDataSource: BarDataSource
  barStyle: BarStyle
}

export const DEFAULT_PREFERENCES: OptionChainPreferences = {
  visibleColumns: DEFAULT_VISIBLE_COLUMNS,
  columnOrder: DEFAULT_COLUMN_ORDER,
  strikeCount: 10,
  selectedUnderlying: 'NIFTY',
  barDataSource: 'oi',
  barStyle: 'gradient',
}

export const LOCALSTORAGE_KEY = 'openalgo_option_chain_prefs'

```


---

# FILE: frontend\src\types\plotly.d.ts

```ts
declare module 'react-plotly.js' {
  import type { Component } from 'react'
  import type * as Plotly from 'plotly.js'

  interface PlotParams {
    data: Plotly.Data[]
    layout?: Partial<Plotly.Layout>
    config?: Partial<Plotly.Config>
    style?: React.CSSProperties
    className?: string
    useResizeHandler?: boolean
    onInitialized?: (
      figure: { data: Plotly.Data[]; layout: Partial<Plotly.Layout> },
      graphDiv: HTMLElement
    ) => void
    onUpdate?: (
      figure: { data: Plotly.Data[]; layout: Partial<Plotly.Layout> },
      graphDiv: HTMLElement
    ) => void
    onRelayout?: (event: Plotly.PlotRelayoutEvent) => void
    onClick?: (event: Plotly.PlotMouseEvent) => void
    onHover?: (event: Plotly.PlotMouseEvent) => void
    revision?: number
  }

  class Plot extends Component<PlotParams> {}
  export default Plot
}

declare module 'plotly.js-dist-min' {
  import * as Plotly from 'plotly.js'
  export = Plotly
}

declare module 'react-plotly.js/factory' {
  import type { ComponentType } from 'react'
  import type { PlotParams } from 'react-plotly.js'
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  export default function createPlotlyComponent(plotly: any): ComponentType<PlotParams>
}

```


---

# FILE: frontend\src\types\python-strategy.ts

```ts
// Python Strategy Types

export interface PythonStrategy {
  id: string
  name: string
  file_name: string
  exchange: string
  status: 'stopped' | 'running' | 'error' | 'scheduled' | 'paused' | 'manually_stopped'
  status_message?: string
  process_id: number | null
  last_started: string | null
  last_stopped: string | null
  error_message: string | null
  is_scheduled: boolean
  manually_stopped?: boolean
  schedule_start_time: string | null
  schedule_stop_time: string | null
  schedule_days: string[]
  created_at: string
  updated_at: string
}

export interface PythonStrategyContent {
  id: string
  name: string
  file_name: string
  content: string
  line_count: number
  size_kb: number
  last_modified: string
}

export interface LogFile {
  name: string
  path: string
  size_kb: number
  last_modified: string
}

export interface LogContent {
  content: string
  lines: number
  size_kb: number
  last_updated: string
}

export interface EnvironmentVariables {
  regular: Record<string, string>
  secure: Record<string, string>
}

export interface ScheduleConfig {
  start_time: string
  stop_time: string
  days: string[]
  exchange?: string
}

// Exchanges that drive the strategy's calendar/holiday awareness in /python.
// Labels show the default daily window only; per-date overrides (e.g. partial
// holidays, Muhurat sessions) come from the market calendar DB.
export const STRATEGY_EXCHANGES = [
  { value: 'NSE', label: 'NSE — Equity (09:15-15:30)' },
  { value: 'BSE', label: 'BSE — Equity (09:15-15:30)' },
  { value: 'NFO', label: 'NFO — NSE F&O (09:15-15:30)' },
  { value: 'BFO', label: 'BFO — BSE F&O (09:15-15:30)' },
  { value: 'CDS', label: 'CDS — NSE Currency (09:00-17:00)' },
  { value: 'BCD', label: 'BCD — BSE Currency (09:00-17:00)' },
  { value: 'MCX', label: 'MCX — Commodity (09:00-23:55)' },
  { value: 'CRYPTO', label: 'CRYPTO — 24/7' },
] as const

export const CRYPTO_EXCHANGE_VALUE = 'CRYPTO'

export interface MasterContractStatus {
  ready: boolean
  message: string
  last_updated: string | null
}

export const SCHEDULE_DAYS = [
  { value: 'mon', label: 'Monday' },
  { value: 'tue', label: 'Tuesday' },
  { value: 'wed', label: 'Wednesday' },
  { value: 'thu', label: 'Thursday' },
  { value: 'fri', label: 'Friday' },
  { value: 'sat', label: 'Saturday' },
  { value: 'sun', label: 'Sunday' },
] as const

export const STATUS_COLORS: Record<string, string> = {
  running: 'bg-green-500',
  stopped: 'bg-gray-500',
  error: 'bg-red-500',
  scheduled: 'bg-blue-500',
  paused: 'bg-yellow-500',
  manually_stopped: 'bg-orange-500',
}

export const STATUS_LABELS: Record<string, string> = {
  running: 'Running',
  stopped: 'Stopped',
  error: 'Error',
  scheduled: 'Scheduled',
  paused: 'Paused',
  manually_stopped: 'Manual Stop',
}

```


---

# FILE: frontend\src\types\strategy.ts

```ts
// Strategy Types for Webhook-based Strategies

export interface Strategy {
  id: number
  name: string
  webhook_id: string
  platform: 'tradingview' | 'amibroker' | 'python' | 'metatrader' | 'excel' | 'others'
  is_active: boolean
  is_intraday: boolean
  trading_mode: 'LONG' | 'SHORT' | 'BOTH'
  start_time: string | null
  end_time: string | null
  squareoff_time: string | null
  created_at: string
  updated_at: string
}

export interface StrategySymbolMapping {
  id: number
  strategy_id: number
  symbol: string
  exchange: string
  quantity: number
  product_type: 'MIS' | 'CNC' | 'NRML'
  created_at: string
}

export interface CreateStrategyRequest {
  name: string
  platform: string
  strategy_type: 'intraday' | 'positional'
  trading_mode: 'LONG' | 'SHORT' | 'BOTH'
  start_time?: string
  end_time?: string
  squareoff_time?: string
}

export interface AddSymbolRequest {
  symbol: string
  exchange: string
  quantity: number
  product_type: string
}

export interface BulkSymbolRequest {
  csv_data: string
}

export interface SymbolSearchResult {
  symbol: string
  brsymbol: string
  name: string
  exchange: string
  token: string
  lotsize: number
}

export type Platform = 'tradingview' | 'amibroker' | 'python' | 'metatrader' | 'excel' | 'others'

export const PLATFORMS: { value: Platform; label: string }[] = [
  { value: 'tradingview', label: 'TradingView' },
  { value: 'amibroker', label: 'Amibroker' },
  { value: 'python', label: 'Python' },
  { value: 'metatrader', label: 'Metatrader' },
  { value: 'excel', label: 'Excel' },
  { value: 'others', label: 'Others' },
]

export const EXCHANGES = ['NSE', 'BSE', 'NFO', 'CDS', 'BFO', 'BCD', 'MCX', 'NCDEX', 'NCO'] as const
export type Exchange = (typeof EXCHANGES)[number]

export const EQUITY_EXCHANGES = ['NSE', 'BSE'] as const
export const DERIVATIVE_EXCHANGES = ['NFO', 'CDS', 'BFO', 'BCD', 'MCX', 'NCDEX', 'NCO'] as const

export function getProductTypes(exchange: string): string[] {
  if (EQUITY_EXCHANGES.includes(exchange as (typeof EQUITY_EXCHANGES)[number])) {
    return ['MIS', 'CNC']
  }
  return ['MIS', 'NRML']
}

export const TRADING_MODES = [
  {
    value: 'LONG',
    label: 'LONG Only',
    description: 'Only buy signals (BUY to open, SELL to close)',
  },
  {
    value: 'SHORT',
    label: 'SHORT Only',
    description: 'Only sell signals (SHORT to open, COVER to close)',
  },
  { value: 'BOTH', label: 'BOTH', description: 'Both long and short positions' },
] as const

```


---

# FILE: frontend\src\types\telegram.ts

```ts
// Telegram types

export interface TelegramBotStatus {
  is_running: boolean
  is_configured: boolean
  bot_username: string | null
  is_active: boolean
}

export interface TelegramConfig {
  bot_token?: string
  bot_username?: string
  broadcast_enabled: boolean
  rate_limit_per_minute: number
  is_active: boolean
}

export interface TelegramUser {
  id: number
  telegram_id: number
  telegram_username: string | null
  openalgo_username: string | null
  first_name: string | null
  last_name: string | null
  notifications_enabled: boolean
  created_at: string
  last_active: string | null
}

export interface CommandStats {
  command: string
  count: number
  last_used: string | null
}

export interface TelegramAnalytics {
  stats_7d: CommandStats[]
  stats_30d: CommandStats[]
  total_users: number
  active_users: number
  users: TelegramUser[]
}

export interface UpdateConfigRequest {
  token?: string
  broadcast_enabled?: boolean
  rate_limit_per_minute?: number
}

export interface BroadcastRequest {
  message: string
  filters?: {
    notifications_enabled?: boolean
  }
}

export interface BroadcastResponse {
  success_count: number
  fail_count: number
}

```


---

# FILE: frontend\src\types\trading.ts

```ts
export interface Position {
  symbol: string
  exchange: string
  product: 'MIS' | 'NRML' | 'CNC'
  quantity: number
  average_price: number
  ltp: number
  pnl: number
  pnlpercent: number
  lot_size?: number // contract_value multiplier (e.g. 0.01 for ETHUSD.P)
  today_realized_pnl?: number // Sandbox: today's realized P&L from closed partial trades
}

export interface Order {
  symbol: string
  exchange: string
  action: 'BUY' | 'SELL'
  quantity: number
  price: number
  trigger_price: number
  pricetype: 'MARKET' | 'LIMIT' | 'SL' | 'SL-M'
  product: 'MIS' | 'NRML' | 'CNC'
  orderid: string
  order_status: 'complete' | 'rejected' | 'cancelled' | 'open' | 'pending' | 'trigger pending'
  timestamp: string
}

export interface Trade {
  symbol: string
  exchange: string
  action: 'BUY' | 'SELL'
  quantity: number
  average_price: number
  trade_value: number
  product: string
  orderid: string
  timestamp: string
}

export interface Holding {
  symbol: string
  exchange: string
  quantity: number
  product: string
  pnl: number
  pnlpercent: number
  ltp?: number
  average_price?: number
}

export interface PortfolioStats {
  totalholdingvalue: number
  totalinvvalue: number
  totalprofitandloss: number
  totalpnlpercentage: number
}

// Alias for consistency
export type HoldingsStats = PortfolioStats

export interface MarginData {
  availablecash: number
  collateral: number
  m2munrealized: number
  m2mrealized: number
  utiliseddebits: number
}

export interface OrderStats {
  total_buy_orders: number
  total_sell_orders: number
  total_completed_orders: number
  total_open_orders: number
  total_rejected_orders: number
}

// -----------------------------------------------------------------------------
// GTT (Good Till Triggered)
// -----------------------------------------------------------------------------

export interface GttLeg {
  action: string // "BUY" | "SELL"
  quantity: number
  price: number
  pricetype: string // usually "LIMIT"
  product: string // "MIS" | "NRML" | "CNC"
}

export type GttStatus =
  | 'active'
  | 'triggered'
  | 'disabled'
  | 'expired'
  | 'cancelled'
  | 'rejected'
  | 'deleted'
  | string // broker-specific statuses passed through as-is

export interface GttOrder {
  trigger_id: string
  trigger_type: 'single' | 'two-leg' | string
  status: GttStatus
  symbol: string
  exchange: string
  trigger_prices: number[]
  last_price: number
  legs: GttLeg[]
  created_at?: string
  updated_at?: string
  expires_at?: string
}

export interface PlaceOrderRequest {
  apikey: string
  strategy: string
  exchange: string
  symbol: string
  action: 'BUY' | 'SELL'
  quantity: number
  pricetype?: 'MARKET' | 'LIMIT' | 'SL' | 'SL-M'
  product?: 'MIS' | 'NRML' | 'CNC'
  price?: number
  trigger_price?: number
  disclosed_quantity?: number
}

export interface ApiResponse<T> {
  status: 'success' | 'error' | 'info'
  message?: string
  data?: T
}

```


---

# FILE: frontend\src\types\websocket.ts

```ts
export type MessageDirection = 'sent' | 'received' | 'error' | 'system'

export interface WebSocketMessage {
  id: string
  direction: MessageDirection
  timestamp: number
  data: unknown
  rawData?: string
}

export interface MessageTemplate {
  key: string
  label: string
  description: string
  template: Record<string, unknown>
}

export interface LatencySample {
  timestamp: number
  latency: number
}

```


---

# FILE: frontend\src\types\whatsapp.ts

```ts
// WhatsApp types — mirrors the JSON shapes returned by blueprints/whatsapp.py.

export interface WhatsAppBotStatus {
  is_running: boolean
  is_paired: boolean
  is_active: boolean
  own_jid: string | null
  own_phone: string | null
  bot_username: string | null
  paired_at: string | null
}

export interface WhatsAppConfig {
  is_paired: boolean
  is_active: boolean
  own_jid: string | null
  own_phone: string | null
  bot_username: string | null
  owner_user_id: number | null
  owner_username: string | null
  paired_at: string | null
  max_message_length: number
  rate_limit_per_minute: number
  broadcast_enabled: boolean
  is_running?: boolean
}

export type WhatsAppPairStatus = 'idle' | 'starting' | 'awaiting_scan' | 'paired' | 'failed'

export interface WhatsAppPairState {
  status: WhatsAppPairStatus
  qr_data_url: string | null
  pair_code: string | null
  error: string | null
  started_at: string | null
  paired_at: string | null
}

export interface WhatsAppConfigBundle {
  config: WhatsAppConfig
  pair_state: WhatsAppPairState
}

export interface WhatsAppUser {
  id: number
  whatsapp_jid: string
  phone_number: string
  openalgo_username: string
  display_name: string | null
  broker: string
  notifications_enabled: boolean
  created_at: string
  last_command_at: string | null
}

export interface WhatsAppCommandStats {
  total_commands: number
  by_command: Record<string, number>
  days: number
}

export interface WhatsAppUpdateConfigRequest {
  broadcast_enabled?: boolean
  rate_limit_per_minute?: number
  max_message_length?: number
}

export interface WhatsAppBroadcastRequest {
  message: string
  filters?: {
    broker?: string
    notifications_enabled?: boolean
  }
}

export interface WhatsAppSendToPhoneRequest {
  phone: string
  message: string
  image_path?: string | null
  document_path?: string | null
}

// Socket.IO event payloads emitted by services/whatsapp_bot_service.py.
export interface WhatsAppQrEvent {
  data_url: string | null
}

export interface WhatsAppPairCodeEvent {
  code: string
}

export interface WhatsAppPairedEvent {
  own_jid: string | null
  own_phone: string | null
}

export interface WhatsAppStatusEvent {
  is_running: boolean
  is_paired: boolean
}

```
