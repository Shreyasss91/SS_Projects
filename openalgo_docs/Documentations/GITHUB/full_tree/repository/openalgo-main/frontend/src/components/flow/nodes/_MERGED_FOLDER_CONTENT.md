# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\frontend\src\components\flow\nodes



---

# FILE: frontend\src\components\flow\nodes\AndGateNode.tsx

[BINARY FILE]

Type: .tsx

Size: 2239 bytes

Path: frontend\src\components\flow\nodes\AndGateNode.tsx


---

# FILE: frontend\src\components\flow\nodes\BaseNode.tsx

[BINARY FILE]

Type: .tsx

Size: 5544 bytes

Path: frontend\src\components\flow\nodes\BaseNode.tsx


---

# FILE: frontend\src\components\flow\nodes\BasketOrderNode.tsx

[BINARY FILE]

Type: .tsx

Size: 1830 bytes

Path: frontend\src\components\flow\nodes\BasketOrderNode.tsx


---

# FILE: frontend\src\components\flow\nodes\CancelAllOrdersNode.tsx

[BINARY FILE]

Type: .tsx

Size: 1362 bytes

Path: frontend\src\components\flow\nodes\CancelAllOrdersNode.tsx


---

# FILE: frontend\src\components\flow\nodes\CancelOrderNode.tsx

[BINARY FILE]

Type: .tsx

Size: 1648 bytes

Path: frontend\src\components\flow\nodes\CancelOrderNode.tsx


---

# FILE: frontend\src\components\flow\nodes\ClosePositionsNode.tsx

[BINARY FILE]

Type: .tsx

Size: 2279 bytes

Path: frontend\src\components\flow\nodes\ClosePositionsNode.tsx


---

# FILE: frontend\src\components\flow\nodes\DelayNode.tsx

[BINARY FILE]

Type: .tsx

Size: 2150 bytes

Path: frontend\src\components\flow\nodes\DelayNode.tsx


---

# FILE: frontend\src\components\flow\nodes\ExpiryNode.tsx

[BINARY FILE]

Type: .tsx

Size: 2092 bytes

Path: frontend\src\components\flow\nodes\ExpiryNode.tsx


---

# FILE: frontend\src\components\flow\nodes\FundCheckNode.tsx

[BINARY FILE]

Type: .tsx

Size: 2504 bytes

Path: frontend\src\components\flow\nodes\FundCheckNode.tsx


---

# FILE: frontend\src\components\flow\nodes\FundsNode.tsx

[BINARY FILE]

Type: .tsx

Size: 1474 bytes

Path: frontend\src\components\flow\nodes\FundsNode.tsx


---

# FILE: frontend\src\components\flow\nodes\GetDepthNode.tsx

[BINARY FILE]

Type: .tsx

Size: 1691 bytes

Path: frontend\src\components\flow\nodes\GetDepthNode.tsx


---

# FILE: frontend\src\components\flow\nodes\GetOrderStatusNode.tsx

[BINARY FILE]

Type: .tsx

Size: 1707 bytes

Path: frontend\src\components\flow\nodes\GetOrderStatusNode.tsx


---

# FILE: frontend\src\components\flow\nodes\GetQuoteNode.tsx

[BINARY FILE]

Type: .tsx

Size: 1769 bytes

Path: frontend\src\components\flow\nodes\GetQuoteNode.tsx


---

# FILE: frontend\src\components\flow\nodes\GroupNode.tsx

[BINARY FILE]

Type: .tsx

Size: 1799 bytes

Path: frontend\src\components\flow\nodes\GroupNode.tsx


---

# FILE: frontend\src\components\flow\nodes\HistoryNode.tsx

[BINARY FILE]

Type: .tsx

Size: 2003 bytes

Path: frontend\src\components\flow\nodes\HistoryNode.tsx


---

# FILE: frontend\src\components\flow\nodes\HoldingsNode.tsx

[BINARY FILE]

Type: .tsx

Size: 1498 bytes

Path: frontend\src\components\flow\nodes\HoldingsNode.tsx


---

# FILE: frontend\src\components\flow\nodes\HolidaysNode.tsx

[BINARY FILE]

Type: .tsx

Size: 1808 bytes

Path: frontend\src\components\flow\nodes\HolidaysNode.tsx


---

# FILE: frontend\src\components\flow\nodes\HttpRequestNode.tsx

[BINARY FILE]

Type: .tsx

Size: 2408 bytes

Path: frontend\src\components\flow\nodes\HttpRequestNode.tsx


---

# FILE: frontend\src\components\flow\nodes\index.ts

```ts
/**
 * Node Components Index
 * Export all workflow node components
 */

// Logic Gate Nodes
import { AndGateNode } from './AndGateNode'
import { BasketOrderNode } from './BasketOrderNode'
import { CancelAllOrdersNode } from './CancelAllOrdersNode'
import { CancelOrderNode } from './CancelOrderNode'
import { ClosePositionsNode } from './ClosePositionsNode'
import { DelayNode } from './DelayNode'
import { ExpiryNode } from './ExpiryNode'
import { FundCheckNode } from './FundCheckNode'
import { FundsNode } from './FundsNode'
import { GetDepthNode } from './GetDepthNode'
import { GetOrderStatusNode } from './GetOrderStatusNode'
// Data Nodes
import { GetQuoteNode } from './GetQuoteNode'
import { GroupNode } from './GroupNode'
import { HistoryNode } from './HistoryNode'
// Risk Management Nodes
import { HoldingsNode } from './HoldingsNode'
import { HolidaysNode } from './HolidaysNode'
import { HttpRequestNode } from './HttpRequestNode'
import { IntervalsNode } from './IntervalsNode'
import { LogNode } from './LogNode'
import { MarginNode } from './MarginNode'
import { MathExpressionNode } from './MathExpressionNode'
import { ModifyOrderNode } from './ModifyOrderNode'
import { MultiQuotesNode } from './MultiQuotesNode'
import { NotGateNode } from './NotGateNode'
import { OpenPositionNode } from './OpenPositionNode'
import { OptionChainNode } from './OptionChainNode'
import { OptionSymbolNode } from './OptionSymbolNode'
import { OptionsMultiOrderNode } from './OptionsMultiOrderNode'
import { OptionsOrderNode } from './OptionsOrderNode'
import { OrderBookNode } from './OrderBookNode'
import { OrGateNode } from './OrGateNode'
// Action Nodes
import { PlaceOrderNode } from './PlaceOrderNode'
import { PositionBookNode } from './PositionBookNode'
// Condition Nodes
import { PositionCheckNode } from './PositionCheckNode'
import { PriceAlertNode } from './PriceAlertNode'
import { PriceConditionNode } from './PriceConditionNode'
import { SmartOrderNode } from './SmartOrderNode'
import { SplitOrderNode } from './SplitOrderNode'
// Trigger Nodes
import { StartNode } from './StartNode'
import { SubscribeDepthNode } from './SubscribeDepthNode'
// WebSocket Streaming Nodes
import { SubscribeLTPNode } from './SubscribeLTPNode'
import { SubscribeQuoteNode } from './SubscribeQuoteNode'
import { SymbolNode } from './SymbolNode'
import { SyntheticFutureNode } from './SyntheticFutureNode'
// Utility Nodes
import { TelegramAlertNode } from './TelegramAlertNode'
import { TimeConditionNode } from './TimeConditionNode'
import { TimeWindowNode } from './TimeWindowNode'
import { TimingsNode } from './TimingsNode'
import { TradeBookNode } from './TradeBookNode'
import { UnsubscribeNode } from './UnsubscribeNode'
import { VariableNode } from './VariableNode'
import { WaitUntilNode } from './WaitUntilNode'
import { WebhookTriggerNode } from './WebhookTriggerNode'

// Base Components
export { BaseNode, NodeBadge, NodeDataRow, NodeInfoRow } from './BaseNode'

// Re-export individual nodes
export {
  // Triggers
  StartNode,
  PriceAlertNode,
  WebhookTriggerNode,
  HttpRequestNode,
  // Actions
  PlaceOrderNode,
  SmartOrderNode,
  OptionsOrderNode,
  OptionsMultiOrderNode,
  CancelAllOrdersNode,
  ClosePositionsNode,
  CancelOrderNode,
  ModifyOrderNode,
  BasketOrderNode,
  SplitOrderNode,
  // Conditions
  PositionCheckNode,
  FundCheckNode,
  TimeWindowNode,
  TimeConditionNode,
  PriceConditionNode,
  // Logic Gates
  AndGateNode,
  OrGateNode,
  NotGateNode,
  // Data
  GetQuoteNode,
  GetDepthNode,
  GetOrderStatusNode,
  HistoryNode,
  OpenPositionNode,
  ExpiryNode,
  IntervalsNode,
  MultiQuotesNode,
  SymbolNode,
  OptionSymbolNode,
  OrderBookNode,
  TradeBookNode,
  PositionBookNode,
  SyntheticFutureNode,
  OptionChainNode,
  // WebSocket Streaming
  SubscribeLTPNode,
  SubscribeQuoteNode,
  SubscribeDepthNode,
  UnsubscribeNode,
  // Risk Management
  HoldingsNode,
  FundsNode,
  MarginNode,
  // Utilities
  TelegramAlertNode,
  DelayNode,
  WaitUntilNode,
  GroupNode,
  VariableNode,
  MathExpressionNode,
  LogNode,
  HolidaysNode,
  TimingsNode,
}

/**
 * Node type registry for ReactFlow
 * Maps node type strings to their components
 */
export const nodeTypes = {
  // Triggers
  start: StartNode,
  priceAlert: PriceAlertNode,
  webhookTrigger: WebhookTriggerNode,
  httpRequest: HttpRequestNode,

  // Actions
  placeOrder: PlaceOrderNode,
  smartOrder: SmartOrderNode,
  optionsOrder: OptionsOrderNode,
  optionsMultiOrder: OptionsMultiOrderNode,
  cancelAllOrders: CancelAllOrdersNode,
  closePositions: ClosePositionsNode,
  cancelOrder: CancelOrderNode,
  modifyOrder: ModifyOrderNode,
  basketOrder: BasketOrderNode,
  splitOrder: SplitOrderNode,

  // Conditions
  positionCheck: PositionCheckNode,
  fundCheck: FundCheckNode,
  timeWindow: TimeWindowNode,
  timeCondition: TimeConditionNode,
  priceCondition: PriceConditionNode,

  // Logic Gates
  andGate: AndGateNode,
  orGate: OrGateNode,
  notGate: NotGateNode,

  // Data
  getQuote: GetQuoteNode,
  getDepth: GetDepthNode,
  getOrderStatus: GetOrderStatusNode,
  history: HistoryNode,
  openPosition: OpenPositionNode,
  expiry: ExpiryNode,
  intervals: IntervalsNode,
  multiQuotes: MultiQuotesNode,
  symbol: SymbolNode,
  optionSymbol: OptionSymbolNode,
  orderBook: OrderBookNode,
  tradeBook: TradeBookNode,
  positionBook: PositionBookNode,
  syntheticFuture: SyntheticFutureNode,
  optionChain: OptionChainNode,

  // WebSocket Streaming
  subscribeLtp: SubscribeLTPNode,
  subscribeQuote: SubscribeQuoteNode,
  subscribeDepth: SubscribeDepthNode,
  unsubscribe: UnsubscribeNode,

  // Risk Management
  holdings: HoldingsNode,
  funds: FundsNode,
  margin: MarginNode,

  // Utilities
  telegramAlert: TelegramAlertNode,
  delay: DelayNode,
  waitUntil: WaitUntilNode,
  group: GroupNode,
  variable: VariableNode,
  mathExpression: MathExpressionNode,
  log: LogNode,
  holidays: HolidaysNode,
  timings: TimingsNode,
} as const

```


---

# FILE: frontend\src\components\flow\nodes\IntervalsNode.tsx

[BINARY FILE]

Type: .tsx

Size: 1622 bytes

Path: frontend\src\components\flow\nodes\IntervalsNode.tsx


---

# FILE: frontend\src\components\flow\nodes\LogNode.tsx

[BINARY FILE]

Type: .tsx

Size: 1902 bytes

Path: frontend\src\components\flow\nodes\LogNode.tsx


---

# FILE: frontend\src\components\flow\nodes\MarginNode.tsx

[BINARY FILE]

Type: .tsx

Size: 1936 bytes

Path: frontend\src\components\flow\nodes\MarginNode.tsx


---

# FILE: frontend\src\components\flow\nodes\MathExpressionNode.tsx

[BINARY FILE]

Type: .tsx

Size: 2026 bytes

Path: frontend\src\components\flow\nodes\MathExpressionNode.tsx


---

# FILE: frontend\src\components\flow\nodes\ModifyOrderNode.tsx

[BINARY FILE]

Type: .tsx

Size: 2212 bytes

Path: frontend\src\components\flow\nodes\ModifyOrderNode.tsx


---

# FILE: frontend\src\components\flow\nodes\MultiQuotesNode.tsx

[BINARY FILE]

Type: .tsx

Size: 2484 bytes

Path: frontend\src\components\flow\nodes\MultiQuotesNode.tsx


---

# FILE: frontend\src\components\flow\nodes\NotGateNode.tsx

[BINARY FILE]

Type: .tsx

Size: 1836 bytes

Path: frontend\src\components\flow\nodes\NotGateNode.tsx


---

# FILE: frontend\src\components\flow\nodes\OpenPositionNode.tsx

[BINARY FILE]

Type: .tsx

Size: 1766 bytes

Path: frontend\src\components\flow\nodes\OpenPositionNode.tsx


---

# FILE: frontend\src\components\flow\nodes\OptionChainNode.tsx

[BINARY FILE]

Type: .tsx

Size: 2361 bytes

Path: frontend\src\components\flow\nodes\OptionChainNode.tsx


---

# FILE: frontend\src\components\flow\nodes\OptionsMultiOrderNode.tsx

[BINARY FILE]

Type: .tsx

Size: 3579 bytes

Path: frontend\src\components\flow\nodes\OptionsMultiOrderNode.tsx


---

# FILE: frontend\src\components\flow\nodes\OptionsOrderNode.tsx

[BINARY FILE]

Type: .tsx

Size: 3503 bytes

Path: frontend\src\components\flow\nodes\OptionsOrderNode.tsx


---

# FILE: frontend\src\components\flow\nodes\OptionSymbolNode.tsx

[BINARY FILE]

Type: .tsx

Size: 2155 bytes

Path: frontend\src\components\flow\nodes\OptionSymbolNode.tsx


---

# FILE: frontend\src\components\flow\nodes\OrderBookNode.tsx

[BINARY FILE]

Type: .tsx

Size: 1499 bytes

Path: frontend\src\components\flow\nodes\OrderBookNode.tsx


---

# FILE: frontend\src\components\flow\nodes\OrGateNode.tsx

[BINARY FILE]

Type: .tsx

Size: 2223 bytes

Path: frontend\src\components\flow\nodes\OrGateNode.tsx


---

# FILE: frontend\src\components\flow\nodes\PlaceOrderNode.tsx

[BINARY FILE]

Type: .tsx

Size: 2752 bytes

Path: frontend\src\components\flow\nodes\PlaceOrderNode.tsx


---

# FILE: frontend\src\components\flow\nodes\PositionBookNode.tsx

[BINARY FILE]

Type: .tsx

Size: 1513 bytes

Path: frontend\src\components\flow\nodes\PositionBookNode.tsx


---

# FILE: frontend\src\components\flow\nodes\PositionCheckNode.tsx

[BINARY FILE]

Type: .tsx

Size: 3251 bytes

Path: frontend\src\components\flow\nodes\PositionCheckNode.tsx


---

# FILE: frontend\src\components\flow\nodes\PriceAlertNode.tsx

[BINARY FILE]

Type: .tsx

Size: 3513 bytes

Path: frontend\src\components\flow\nodes\PriceAlertNode.tsx


---

# FILE: frontend\src\components\flow\nodes\PriceConditionNode.tsx

[BINARY FILE]

Type: .tsx

Size: 3113 bytes

Path: frontend\src\components\flow\nodes\PriceConditionNode.tsx


---

# FILE: frontend\src\components\flow\nodes\SmartOrderNode.tsx

[BINARY FILE]

Type: .tsx

Size: 2667 bytes

Path: frontend\src\components\flow\nodes\SmartOrderNode.tsx


---

# FILE: frontend\src\components\flow\nodes\SplitOrderNode.tsx

[BINARY FILE]

Type: .tsx

Size: 2165 bytes

Path: frontend\src\components\flow\nodes\SplitOrderNode.tsx


---

# FILE: frontend\src\components\flow\nodes\StartNode.tsx

[BINARY FILE]

Type: .tsx

Size: 2983 bytes

Path: frontend\src\components\flow\nodes\StartNode.tsx


---

# FILE: frontend\src\components\flow\nodes\SubscribeDepthNode.tsx

[BINARY FILE]

Type: .tsx

Size: 2040 bytes

Path: frontend\src\components\flow\nodes\SubscribeDepthNode.tsx


---

# FILE: frontend\src\components\flow\nodes\SubscribeLTPNode.tsx

[BINARY FILE]

Type: .tsx

Size: 2021 bytes

Path: frontend\src\components\flow\nodes\SubscribeLTPNode.tsx


---

# FILE: frontend\src\components\flow\nodes\SubscribeQuoteNode.tsx

[BINARY FILE]

Type: .tsx

Size: 2052 bytes

Path: frontend\src\components\flow\nodes\SubscribeQuoteNode.tsx


---

# FILE: frontend\src\components\flow\nodes\SymbolNode.tsx

[BINARY FILE]

Type: .tsx

Size: 1758 bytes

Path: frontend\src\components\flow\nodes\SymbolNode.tsx


---

# FILE: frontend\src\components\flow\nodes\SyntheticFutureNode.tsx

[BINARY FILE]

Type: .tsx

Size: 2123 bytes

Path: frontend\src\components\flow\nodes\SyntheticFutureNode.tsx


---

# FILE: frontend\src\components\flow\nodes\TelegramAlertNode.tsx

[BINARY FILE]

Type: .tsx

Size: 1787 bytes

Path: frontend\src\components\flow\nodes\TelegramAlertNode.tsx


---

# FILE: frontend\src\components\flow\nodes\TimeConditionNode.tsx

[BINARY FILE]

Type: .tsx

Size: 2826 bytes

Path: frontend\src\components\flow\nodes\TimeConditionNode.tsx


---

# FILE: frontend\src\components\flow\nodes\TimeWindowNode.tsx

[BINARY FILE]

Type: .tsx

Size: 2827 bytes

Path: frontend\src\components\flow\nodes\TimeWindowNode.tsx


---

# FILE: frontend\src\components\flow\nodes\TimingsNode.tsx

[BINARY FILE]

Type: .tsx

Size: 1742 bytes

Path: frontend\src\components\flow\nodes\TimingsNode.tsx


---

# FILE: frontend\src\components\flow\nodes\TradeBookNode.tsx

[BINARY FILE]

Type: .tsx

Size: 1497 bytes

Path: frontend\src\components\flow\nodes\TradeBookNode.tsx


---

# FILE: frontend\src\components\flow\nodes\UnsubscribeNode.tsx

[BINARY FILE]

Type: .tsx

Size: 1914 bytes

Path: frontend\src\components\flow\nodes\UnsubscribeNode.tsx


---

# FILE: frontend\src\components\flow\nodes\VariableNode.tsx

[BINARY FILE]

Type: .tsx

Size: 2960 bytes

Path: frontend\src\components\flow\nodes\VariableNode.tsx


---

# FILE: frontend\src\components\flow\nodes\WaitUntilNode.tsx

[BINARY FILE]

Type: .tsx

Size: 1858 bytes

Path: frontend\src\components\flow\nodes\WaitUntilNode.tsx


---

# FILE: frontend\src\components\flow\nodes\WebhookTriggerNode.tsx

[BINARY FILE]

Type: .tsx

Size: 1778 bytes

Path: frontend\src\components\flow\nodes\WebhookTriggerNode.tsx
