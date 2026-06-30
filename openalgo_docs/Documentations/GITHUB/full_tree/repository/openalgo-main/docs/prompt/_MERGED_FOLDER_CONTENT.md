# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\docs\prompt



---

# FILE: docs\prompt\flow-import-format.md

```md
# Flow Editor — Import JSON Reference

This document is the source of truth for hand-writing or generating workflow
JSON that can be imported into the OpenAlgo Flow Editor. It covers the
top-level workflow shape, every node type, every edge variant, the variable
interpolation grammar, and the source-handle vocabulary that drives condition
branching.

If you are writing a tool that produces flow JSON (an LLM agent, a script,
another editor), feed this file in as a system prompt — it is written in a
flat declarative style suitable for that purpose.

---

## 1. Workflow shape

A workflow is a JSON object with the following top-level keys (the snippet
below is a *shape diagram*, not import-ready — see §8 for runnable examples):

```jsonc
{
  "name": "My Workflow",
  "description": "Optional one-line summary",
  "nodes": [ /* array of nodes */ ],
  "edges": [ /* array of edges */ ],
  "viewport": { "x": 0, "y": 0, "zoom": 1 }
}
```

| Key | Required for import | Required for execution | Notes |
|---|---|---|---|
| `name` | **yes** | no | Importer rejects without it. The UI suffixes `(imported)` to whatever you supply. |
| `description` | no | no | Free-text. Defaults to empty. |
| `nodes` | **yes** (array, can be empty) | yes | See §2 + §7. |
| `edges` | **yes** (array, can be empty) | yes | See §3. |
| `viewport` | no | no | Restores canvas position only. Importers may omit. |

### Importer validation

The importer (`POST /api/workflows/import`, called from the Flow Editor's
**Import** dialog) runs this check on the parsed JSON before saving:

```js
if (!parsed.name || !Array.isArray(parsed.nodes) || !Array.isArray(parsed.edges)) {
  // -> "Invalid workflow format. Must have name, nodes, and edges."
}
```

If `JSON.parse` itself throws (smart quotes, missing comma, real newline
inside a string, BOM at the start), the message is the more generic
**"Invalid JSON format. Please check the workflow data."** — that always
indicates a syntax problem with the JSON text itself, not a missing field.

### Persisted vs minimal node

The DB stores additional UI-only fields per node (`measured`, `dragging`,
`selected`). They are not required for import — the executor reads only `id`,
`type`, `position`, and `data`. A minimal valid node:

```json
{ "id": "node_1", "type": "start", "position": { "x": 0, "y": 0 }, "data": { "scheduleType": "daily", "time": "09:15" } }
```

---

## 2. Node common structure

Every node has the same outer shape:

| Key | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | Must be unique within the workflow. Convention: `node_1`, `node_2`, ... |
| `type` | string | yes | One of the values listed in [§7](#7-node-reference). Case-sensitive. |
| `position` | `{ x: number, y: number }` | yes | Canvas coordinates. Anything works; group nodes ~200px apart. |
| `data` | object | yes | Per-node configuration. Each node type defines its own keys. |

Every node's `data` object also accepts an optional `label` (string) used
purely as a UI display override. The executor ignores it.

---

## 3. Edge common structure

Edges connect nodes. Each edge:

| Key | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | Any unique string. Convention: `edge-<timestamp>`. |
| `source` | string | yes | The upstream node's `id`. |
| `target` | string | yes | The downstream node's `id`. |
| `sourceHandle` | string \| null | conditional | See [§5](#5-condition-source-handles). Required when fanning out from a condition or gate node. |
| `targetHandle` | string \| null | no | Almost always `null`. Only AND/OR gates use it (see `andGate`/`orGate`). |
| `type` | string | no | UI styling hint. `"insertable"` is the default the editor saves; importers can omit it. |
| `animated` | boolean | no | UI-only flag. Importers can omit. |

Minimal edge:

```json
{ "id": "edge-1", "source": "node_1", "target": "node_2" }
```

---

## 4. Variable interpolation

Inside any string field of any node's `data`, you can reference variables that
upstream nodes have produced or that the executor exposes as built-ins. The
syntax is `{{path}}`.

### Path grammar

- **Dotted keys** for dict access: `{{order.data.orderid}}`
- **Bracket index** for list/tuple access: `{{expiries.data[0]}}`
- **Combined**: `{{chain.data.results[0].ce.ltp}}`
- **Negative indices are not supported.** Use a positive index.

If any segment of the path is missing or the variable does not exist, the
entire `{{...}}` placeholder is left **literally** in the rendered string —
the workflow does **not** error out. Useful for spotting typos in logs.

### Built-in variables

These resolve to the runtime value of the executor process clock at the moment
the node fires:

| Token | Example value |
|---|---|
| `{{timestamp}}` | `2026-04-29 09:15:42` |
| `{{date}}` | `2026-04-29` |
| `{{time}}` | `09:15:42` |
| `{{year}}` | `2026` |
| `{{month}}` | `04` |
| `{{day}}` | `29` |
| `{{hour}}` | `09` |
| `{{minute}}` | `15` |
| `{{second}}` | `42` |
| `{{weekday}}` | `Wednesday` |
| `{{iso_timestamp}}` | `2026-04-29T09:15:42.123456` |

### Output variables

Most data and action nodes accept an `outputVariable` field in their `data`
object. When set, the result of that node is stored in the workflow context
under that name and can be read by every downstream node.

```json
{ "type": "getQuote", "data": { "symbol": "RELIANCE", "exchange": "NSE", "outputVariable": "quote" } }
```

Then a downstream node can use `{{quote.data.ltp}}` in any string field.

If `outputVariable` is empty or unset, the node still runs but its result is
not exposed.

### Webhook payload

When the trigger is a `webhookTrigger`, the inbound JSON body is exposed as
`{{webhook.<key>}}`. For example, a TradingView alert sending
`{"symbol": "RELIANCE", "action": "BUY", "qty": 10}` exposes
`{{webhook.symbol}}`, `{{webhook.action}}`, `{{webhook.qty}}`.

---

## 5. Condition source handles

Six node types fan out into a TRUE branch and a FALSE branch:

| Node | Handle vocabulary used in `sourceHandle` |
|---|---|
| `positionCheck` | `"true"` / `"false"` |
| `fundCheck` | `"true"` / `"false"` |
| `priceCondition` | `"true"` / `"false"` |
| `timeWindow` | `"true"` / `"false"` |
| `timeCondition` | `"yes"` / `"no"` |
| `notGate` | `"yes"` / `"no"` |

The executor accepts both vocabularies as synonyms — `{yes, true}` is the
truthy branch, `{no, false}` is the falsy branch — but it is good practice
to use the vocabulary native to each node so saved workflows match the UI.

Edges that source from a condition node and **do not** specify a `sourceHandle`
are followed unconditionally on every run (use this for "fire-and-forget" log
or telegram nodes that want to see every result).

`andGate` / `orGate` source handles are not bool branches — they emit a single
`condition` value to whatever connects to them downstream. Their **incoming**
edges do use `targetHandle` to pin a specific input slot:
`targetHandle: "input-0"`, `"input-1"`, ... up to `inputCount - 1`.

---

## 6. ID generation

`id` strings only need to be unique within the workflow. The UI uses the
pattern `node_<N>` for nodes and `edge-<unix-millis>` for edges, but any
non-empty string works.

Snake/camel case in `data` keys: **camelCase** (e.g. `expiryType`,
`triggerPrice`, `outputVariable`). The one exception is the Expiry node's
`instrumenttype` field which is lowercase to match the OpenAlgo REST API.

---

## 7. Node reference

Every node type the executor recognizes is documented below. Examples show
the full node JSON; in workflow JSON, paste the example as one element of
the `nodes` array.

### 7.1 Trigger nodes

A workflow must contain exactly one trigger node, and that node must be one
of: `start`, `priceAlert`, `webhookTrigger`. Every other path of execution
flows from there.

#### start — Schedule Trigger

Fires on a clock schedule.

| Field | Type | Default | Notes |
|---|---|---|---|
| `scheduleType` | `"once"` \| `"daily"` \| `"weekly"` \| `"interval"` | `"daily"` | |
| `time` | `"HH:MM"` | `"09:15"` | Required for `once` / `daily` / `weekly`. |
| `days` | `number[]` | `[0,1,2,3,4]` | For `daily`/`weekly`. 0=Mon, 1=Tue, ..., 6=Sun. |
| `executeAt` | `"YYYY-MM-DD"` | — | Required when `scheduleType="once"`. |
| `intervalValue` | number | `1` | For `interval` mode. |
| `intervalUnit` | `"seconds"` \| `"minutes"` \| `"hours"` | `"minutes"` | For `interval` mode. |
| `marketHoursOnly` | boolean | `true` | If true, the schedule pauses outside 09:15–15:30 IST on weekdays. |

```json
{
  "id": "node_1",
  "type": "start",
  "position": { "x": 100, "y": 100 },
  "data": {
    "scheduleType": "daily",
    "time": "09:20",
    "days": [0, 1, 2, 3, 4],
    "marketHoursOnly": true
  }
}
```

#### priceAlert — Price Alert Trigger

Fires when an LTP condition is met. The price-monitor service polls the
configured symbol on a 1-second tick.

| Field | Type | Default | Notes |
|---|---|---|---|
| `symbol` | string | — | OpenAlgo symbol format. |
| `exchange` | string | `"NSE"` | See [§9 Exchange codes](#9-exchanges). |
| `condition` | `"above"` \| `"below"` \| `"crosses_above"` \| `"crosses_below"` | `"above"` | |
| `price` | number | — | Target price. For channel modes, see `priceLower`/`priceUpper`. |
| `priceLower` | number | — | Used by `entering_channel` / `inside_channel` / etc. (advanced). |
| `priceUpper` | number | — | |
| `trigger` | `"once"` \| `"every_time"` | `"once"` | Whether to re-fire after first match. |
| `expiration` | `"none"` \| `"1h"` \| `"4h"` \| `"1d"` \| `"1w"` | `"none"` | Auto-disable after this duration. |
| `playSound` | boolean | `true` | UI-only. |
| `message` | string | — | Optional custom message. |

```json
{
  "id": "node_1",
  "type": "priceAlert",
  "position": { "x": 100, "y": 100 },
  "data": {
    "symbol": "RELIANCE",
    "exchange": "NSE",
    "condition": "crosses_above",
    "price": 1500,
    "trigger": "once",
    "expiration": "1d"
  }
}
```

#### webhookTrigger — Webhook Trigger

Fires when an external system POSTs JSON to the workflow's webhook URL. The
URL and secret are minted by the server when the workflow is saved (you cannot
hand-write them; you can only configure the symbol/exchange filter).

| Field | Type | Default | Notes |
|---|---|---|---|
| `label` | string | — | Display name (e.g. `"TradingView Alert"`). |
| `symbol` | string | — | Optional. If set, only requests whose URL ends in `/{symbol}` or whose body has matching `symbol` are accepted. |
| `exchange` | `"NSE"` \| `"BSE"` \| `"NFO"` \| `"CDS"` \| `"MCX"` | `"NSE"` | Default exchange to assume in the payload. |

The inbound JSON body is exposed as `{{webhook.<key>}}` to all downstream
nodes (e.g. `{{webhook.action}}`, `{{webhook.qty}}`, `{{webhook.strike}}`).

```json
{
  "id": "node_1",
  "type": "webhookTrigger",
  "position": { "x": 100, "y": 100 },
  "data": {
    "label": "TradingView Long Entry",
    "symbol": "NIFTY",
    "exchange": "NFO"
  }
}
```

---

### 7.2 Action nodes

#### placeOrder — Place Order

Single-leg order on any segment.

| Field | Type | Default | Notes |
|---|---|---|---|
| `symbol` | string | — | OpenAlgo symbol format. |
| `exchange` | string | `"NSE"` | |
| `action` | `"BUY"` \| `"SELL"` | `"BUY"` | |
| `quantity` | int | `1` | In shares (not lots). |
| `priceType` | `"MARKET"` \| `"LIMIT"` \| `"SL"` \| `"SL-M"` | `"MARKET"` | |
| `product` | `"MIS"` \| `"CNC"` \| `"NRML"` | `"MIS"` | |
| `price` | number | `0` | Required for `LIMIT`/`SL`. |
| `triggerPrice` | number | `0` | Required for `SL`/`SL-M`. |
| `outputVariable` | string | — | If set, exposes `{{name.orderid}}`, `{{name.status}}`. |

```json
{
  "id": "node_2",
  "type": "placeOrder",
  "position": { "x": 100, "y": 200 },
  "data": {
    "symbol": "RELIANCE",
    "exchange": "NSE",
    "action": "BUY",
    "quantity": 10,
    "priceType": "LIMIT",
    "product": "CNC",
    "price": 1450.50,
    "outputVariable": "buyOrder"
  }
}
```

#### smartOrder — Smart Order

Position-aware order. The broker computes the delta between current position
and `positionSize` and places the appropriate order to reach it.

| Field | Type | Default | Notes |
|---|---|---|---|
| `symbol`, `exchange`, `action`, `priceType`, `product` | (as `placeOrder`) | | |
| `quantity` | int | `1` | Used only when `positionSize=0`. |
| `positionSize` | int | `0` | Target net position. Positive=long, negative=short, 0=use `quantity`. |
| `outputVariable` | string | — | |

```json
{
  "id": "node_2",
  "type": "smartOrder",
  "position": { "x": 100, "y": 200 },
  "data": {
    "symbol": "TATAMOTORS",
    "exchange": "NSE",
    "action": "SELL",
    "quantity": 0,
    "positionSize": -5,
    "priceType": "MARKET",
    "product": "MIS",
    "outputVariable": "smartResult"
  }
}
```

#### optionsOrder — Options Order

Single-leg options order resolved from underlying + offset + option type.

| Field | Type | Default | Notes |
|---|---|---|---|
| `underlying` | `"NIFTY"` \| `"BANKNIFTY"` \| `"FINNIFTY"` \| `"MIDCPNIFTY"` \| `"NIFTYNXT50"` \| `"SENSEX"` \| `"BANKEX"` \| `"SENSEX50"` | `"NIFTY"` | |
| `expiryType` | `"current_week"` \| `"next_week"` \| `"current_month"` \| `"next_month"` | `"current_week"` | The Symbol service resolves to actual date. |
| `offset` | `"ATM"` \| `"ITM1"`–`"ITM5"` \| `"OTM1"`–`"OTM10"` | `"ATM"` | |
| `optionType` | `"CE"` \| `"PE"` | `"CE"` | |
| `action` | `"BUY"` \| `"SELL"` | `"BUY"` | |
| `quantity` | int | `1` | **In lots** (executor multiplies by lot size). |
| `priceType` | `"MARKET"` \| `"LIMIT"` \| `"SL"` \| `"SL-M"` | `"MARKET"` | |
| `product` | `"MIS"` \| `"NRML"` | `"NRML"` | |
| `price` | number | `0` | For `LIMIT`/`SL`. |
| `triggerPrice` | number | `0` | For `SL`/`SL-M`. |
| `splitSize` | int | `0` | If >0, splits into chunks. |
| `outputVariable` | string | — | |

```json
{
  "id": "node_2",
  "type": "optionsOrder",
  "position": { "x": 100, "y": 200 },
  "data": {
    "underlying": "NIFTY",
    "expiryType": "current_week",
    "offset": "ATM",
    "optionType": "CE",
    "action": "BUY",
    "quantity": 1,
    "priceType": "MARKET",
    "product": "NRML",
    "outputVariable": "ceLong"
  }
}
```

#### optionsMultiOrder — Multi-Leg Options Strategy

Pre-defined or custom multi-leg strategies (straddle / strangle / iron condor /
spreads / custom).

| Field | Type | Default | Notes |
|---|---|---|---|
| `strategy` | `"straddle"` \| `"strangle"` \| `"iron_condor"` \| `"bull_call_spread"` \| `"bear_put_spread"` \| `"custom"` | `"straddle"` | |
| `underlying` | (as `optionsOrder`) | `"NIFTY"` | |
| `expiryType` | (as `optionsOrder`) | `"current_week"` | |
| `action` | `"BUY"` \| `"SELL"` | — | Direction for the strategy (BUY=long volatility, SELL=short volatility). |
| `quantity` | int | `1` | Lots per leg. |
| `priceType` | `"MARKET"` \| `"LIMIT"` | `"MARKET"` | |
| `product` | `"MIS"` \| `"NRML"` | `"NRML"` | |
| `legs` | `Leg[]` | `[]` | **Only for `strategy="custom"`.** Each leg: `{ offset, optionType, action, quantity, expiryDate? }`. |
| `outputVariable` | string | — | Result includes `{{name.results}}` array per leg. |

```json
{
  "id": "node_2",
  "type": "optionsMultiOrder",
  "position": { "x": 100, "y": 200 },
  "data": {
    "strategy": "iron_condor",
    "underlying": "NIFTY",
    "expiryType": "current_week",
    "action": "SELL",
    "quantity": 1,
    "product": "NRML",
    "outputVariable": "ironCondor"
  }
}
```

#### basketOrder — Basket Order

Place multiple orders in a single API call.

| Field | Type | Default | Notes |
|---|---|---|---|
| `basketName` | string | `"flow_basket"` | |
| `orders` | string | — | Multi-line, comma-separated `SYMBOL,EXCHANGE,ACTION,QTY` per line. |
| `product` | `"MIS"` \| `"CNC"` \| `"NRML"` | `"MIS"` | |
| `priceType` | `"MARKET"` \| `"LIMIT"` | `"MARKET"` | |
| `outputVariable` | string | — | `{{name.results}}` is the per-order result array. |

```json
{
  "id": "node_2",
  "type": "basketOrder",
  "position": { "x": 100, "y": 200 },
  "data": {
    "basketName": "Morning Long Book",
    "orders": "RELIANCE,NSE,BUY,10\nINFY,NSE,BUY,5\nSBIN,NSE,SELL,20",
    "product": "MIS",
    "priceType": "MARKET",
    "outputVariable": "basket"
  }
}
```

#### splitOrder — Split Order

Splits a large order into chunks.

| Field | Type | Default | Notes |
|---|---|---|---|
| `symbol`, `exchange`, `action`, `priceType`, `product` | (as `placeOrder`) | | |
| `quantity` | int | `100` | Total to fill. |
| `splitSize` | int | `50` | Chunk size. Last chunk may be smaller. |
| `outputVariable` | string | — | `{{name.results}}` is the per-chunk result. |

```json
{
  "id": "node_2",
  "type": "splitOrder",
  "position": { "x": 100, "y": 200 },
  "data": {
    "symbol": "YESBANK",
    "exchange": "NSE",
    "action": "SELL",
    "quantity": 105,
    "splitSize": 20,
    "priceType": "MARKET",
    "product": "MIS",
    "outputVariable": "splitOut"
  }
}
```

#### modifyOrder — Modify Order

| Field | Type | Default | Notes |
|---|---|---|---|
| `orderId` | string | — | Usually `{{prevOrder.orderid}}`. |
| `symbol`, `exchange`, `action`, `priceType`, `product` | as `placeOrder` | | Required if the broker expects them on modify. |
| `newQuantity` | int | — | Empty = keep existing. |
| `newPrice` | number | — | Empty = keep existing. |
| `newTriggerPrice` | number | — | Empty = keep existing. |

```json
{
  "id": "node_3",
  "type": "modifyOrder",
  "position": { "x": 100, "y": 300 },
  "data": {
    "orderId": "{{buyOrder.orderid}}",
    "symbol": "RELIANCE",
    "exchange": "NSE",
    "action": "BUY",
    "newPrice": 1455,
    "priceType": "LIMIT",
    "product": "CNC"
  }
}
```

#### cancelOrder — Cancel Order

| Field | Type | Default | Notes |
|---|---|---|---|
| `orderId` | string | — | Usually `{{prevOrder.orderid}}`. |

```json
{ "id": "node_3", "type": "cancelOrder", "position": { "x": 100, "y": 300 }, "data": { "orderId": "{{buyOrder.orderid}}" } }
```

#### cancelAllOrders — Cancel All Orders

Cancels every open order. No fields.

```json
{ "id": "node_3", "type": "cancelAllOrders", "position": { "x": 100, "y": 300 }, "data": {} }
```

#### closePositions — Close All Positions

Squares off every open position. No fields.

```json
{ "id": "node_3", "type": "closePositions", "position": { "x": 100, "y": 300 }, "data": {} }
```

---

### 7.3 Logic / condition nodes

These nodes set a `condition` boolean that the executor uses to route edges
via `sourceHandle` — see [§5](#5-condition-source-handles).

#### positionCheck — Position Check

| Field | Type | Default | Notes |
|---|---|---|---|
| `symbol` | string | — | |
| `exchange` | string | `"NSE"` | |
| `product` | `"MIS"` \| `"CNC"` \| `"NRML"` | `"MIS"` | |
| `condition` | `"exists"` \| `"not_exists"` \| `"quantity_above"` \| `"quantity_below"` \| `"pnl_above"` \| `"pnl_below"` | `"exists"` | |
| `threshold` | number | `0` | Only used by the `quantity_*` and `pnl_*` modes. |

Result: `condition=True` if the rule matches the live position.

```json
{
  "id": "node_2",
  "type": "positionCheck",
  "position": { "x": 100, "y": 100 },
  "data": {
    "symbol": "RELIANCE",
    "exchange": "NSE",
    "product": "MIS",
    "condition": "not_exists"
  }
}
```

#### fundCheck — Fund Check

| Field | Type | Default | Notes |
|---|---|---|---|
| `minAvailable` | number | `0` | Triggers True when `availablecash >= minAvailable`. |

```json
{ "id": "node_2", "type": "fundCheck", "position": { "x": 100, "y": 100 }, "data": { "minAvailable": 10000 } }
```

#### priceCondition — Price Check

| Field | Type | Default | Notes |
|---|---|---|---|
| `symbol` | string | — | |
| `exchange` | string | `"NSE"` | |
| `field` | `"ltp"` \| `"open"` \| `"high"` \| `"low"` \| `"prev_close"` \| `"change_percent"` | `"ltp"` | `change_percent` is computed from `(ltp - prev_close) / prev_close * 100`. |
| `operator` | `">"` \| `"<"` \| `"=="` \| `">="` \| `"<="` \| `"!="` | `">"` | |
| `value` | number | `0` | The threshold to compare against. |

```json
{
  "id": "node_2",
  "type": "priceCondition",
  "position": { "x": 100, "y": 100 },
  "data": {
    "symbol": "RELIANCE",
    "exchange": "NSE",
    "field": "ltp",
    "operator": ">",
    "value": 1500
  }
}
```

#### timeWindow — Time Window

| Field | Type | Default | Notes |
|---|---|---|---|
| `startTime` | `"HH:MM"` | `"09:15"` | |
| `endTime` | `"HH:MM"` | `"15:30"` | |
| `invertCondition` | boolean | `false` | If true, fires when **outside** the window. |

```json
{
  "id": "node_2",
  "type": "timeWindow",
  "position": { "x": 100, "y": 100 },
  "data": { "startTime": "09:30", "endTime": "15:15", "invertCondition": false }
}
```

#### timeCondition — Time Condition (uses `yes`/`no` handles)

| Field | Type | Default | Notes |
|---|---|---|---|
| `conditionType` | `"entry"` \| `"exit"` \| `"custom"` | — | UI-only categorization. |
| `operator` | `"=="` \| `">="` \| `"<="` \| `">"` \| `"<"` | `">="` | |
| `targetTime` | `"HH:MM"` | `"09:30"` | |
| `label` | string | — | Optional. |

```json
{
  "id": "node_2",
  "type": "timeCondition",
  "position": { "x": 100, "y": 100 },
  "data": {
    "conditionType": "entry",
    "operator": ">=",
    "targetTime": "09:30",
    "label": "Market Open Entry"
  }
}
```

#### andGate — AND Gate

True only if every input is True.

| Field | Type | Default | Notes |
|---|---|---|---|
| `inputCount` | 2..5 | `2` | Number of input slots. Incoming edges should set `targetHandle` to `"input-0"`, `"input-1"`, ... |

Edges feeding it:
```json
{ "id": "edge-x", "source": "cond1", "sourceHandle": "true", "target": "and1", "targetHandle": "input-0" }
{ "id": "edge-y", "source": "cond2", "sourceHandle": "true", "target": "and1", "targetHandle": "input-1" }
```

```json
{ "id": "node_3", "type": "andGate", "position": { "x": 200, "y": 100 }, "data": { "inputCount": 2 } }
```

#### orGate — OR Gate

True if any input is True. Same `inputCount` and `targetHandle` mechanics as
`andGate`.

```json
{ "id": "node_3", "type": "orGate", "position": { "x": 200, "y": 100 }, "data": { "inputCount": 2 } }
```

#### notGate — NOT Gate (uses `yes`/`no` handles)

Inverts the single incoming `condition`.

```json
{ "id": "node_3", "type": "notGate", "position": { "x": 200, "y": 100 }, "data": {} }
```

---

### 7.4 Data nodes

Each data node takes its inputs and stores its result under `outputVariable`
(if set). The shape returned by each maps onto the OpenAlgo REST API's
response — see `docs/prompt/services_documentation.md` for full response
schemas.

#### getQuote — Get Quote

| Field | Type | Default | Notes |
|---|---|---|---|
| `symbol`, `exchange`, `outputVariable` | | | |

`{{quote.data.ltp}}`, `{{quote.data.bid}}`, `{{quote.data.ask}}`, `{{quote.data.open}}`, ...

```json
{
  "id": "node_2",
  "type": "getQuote",
  "position": { "x": 100, "y": 100 },
  "data": { "symbol": "RELIANCE", "exchange": "NSE", "outputVariable": "quote" }
}
```

#### getDepth — Market Depth

| Field | Type | Default | Notes |
|---|---|---|---|
| `symbol`, `exchange`, `outputVariable` | | | |

`{{depth.data.bids[0].price}}`, `{{depth.data.asks[0].quantity}}`, `{{depth.data.totalbuyqty}}`.

#### history — Historical OHLCV

| Field | Type | Default | Notes |
|---|---|---|---|
| `symbol`, `exchange` | | | |
| `interval` | `"1m"` \| `"5m"` \| `"15m"` \| `"1h"` \| `"1d"` (or any interval the broker supports — call `intervals` first) | `"5m"` | |
| `startDate` | `"YYYY-MM-DD"` | — | **Required.** Note: the Config Panel currently writes a `days` integer instead — the executor does not consume it, so for import JSON write explicit `startDate`/`endDate` strings. |
| `endDate` | `"YYYY-MM-DD"` | — | **Required.** See note above. |
| `outputVariable` | string | — | |

```json
{
  "id": "node_2",
  "type": "history",
  "position": { "x": 100, "y": 100 },
  "data": {
    "symbol": "RELIANCE",
    "exchange": "NSE",
    "interval": "5m",
    "startDate": "2026-04-22",
    "endDate": "2026-04-29",
    "outputVariable": "ohlcv"
  }
}
```

#### openPosition — Open Position For Symbol

| Field | Type | Default | Notes |
|---|---|---|---|
| `symbol`, `exchange`, `product`, `outputVariable` | | | |

`{{position.quantity}}` and `{{position.pnl}}` are exposed.

#### getOrderStatus — Order Status

| Field | Type | Default | Notes |
|---|---|---|---|
| `orderId` | string | — | Usually `{{prevOrder.orderid}}`. |
| `outputVariable` | string | — | |

`{{orderStatus.data.order_status}}` is `"complete" / "open" / "rejected" / ...`.

#### orderBook / tradeBook / positionBook / holdings / funds

All five take only `outputVariable`. Common patterns:

```json
{ "id": "node_2", "type": "orderBook",    "position": { "x": 100, "y": 100 }, "data": { "outputVariable": "orders" } }
{ "id": "node_2", "type": "tradeBook",    "position": { "x": 100, "y": 100 }, "data": { "outputVariable": "trades" } }
{ "id": "node_2", "type": "positionBook", "position": { "x": 100, "y": 100 }, "data": { "outputVariable": "positions" } }
{ "id": "node_2", "type": "holdings",     "position": { "x": 100, "y": 100 }, "data": { "outputVariable": "holdings" } }
{ "id": "node_2", "type": "funds",        "position": { "x": 100, "y": 100 }, "data": { "outputVariable": "funds" } }
```

Useful interpolations: `{{orders.data.orders[0].orderid}}`,
`{{positions.data[0].quantity}}`, `{{holdings.data[0].symbol}}`,
`{{funds.data.availablecash}}`.

#### symbol — Symbol Info

| Field | Type | Default | Notes |
|---|---|---|---|
| `symbol`, `exchange`, `outputVariable` | | | Returns `{ data: { lotsize, tick_size, expiry, ... } }`. |

#### optionSymbol — Resolve Option Symbol

| Field | Type | Default | Notes |
|---|---|---|---|
| `underlying` | string | `"NIFTY"` | |
| `exchange` | `"NSE_INDEX"` \| `"BSE_INDEX"` | `"NSE_INDEX"` | |
| `expiryDate` | string | — | Format `"30DEC25"`. Can be `{{expiries.data[0]}}` after a normalization step. |
| `offset` | `"ATM"` \| `"ITM1"`–`"ITM2"` \| `"OTM1"`–`"OTM3"` | `"ATM"` | |
| `optionType` | `"CE"` \| `"PE"` | `"CE"` | |
| `outputVariable` | string | — | |

#### expiry — Get Expiry Dates

| Field | Type | Default | Notes |
|---|---|---|---|
| `symbol` | string | `"NIFTY"` | |
| `exchange` | `"NFO"` \| `"BFO"` \| `"MCX"` \| `"CDS"` | `"NFO"` | |
| `instrumenttype` | `"options"` \| `"futures"` | `"options"` | **Lowercase.** Different calendars per type. |
| `outputVariable` | string | — | List sorted ascending. `{{expiries.data[0]}}` = nearest. |

```json
{
  "id": "node_2",
  "type": "expiry",
  "position": { "x": 100, "y": 100 },
  "data": {
    "symbol": "NIFTY",
    "exchange": "NFO",
    "instrumenttype": "options",
    "outputVariable": "expiries"
  }
}
```

#### intervals — Available Time Intervals

| Field | Type | Default | Notes |
|---|---|---|---|
| `outputVariable` | string | — | |

```json
{ "id": "node_2", "type": "intervals", "position": { "x": 100, "y": 100 }, "data": { "outputVariable": "ivs" } }
```

#### multiQuotes — Quotes For Many Symbols

| Field | Type | Default | Notes |
|---|---|---|---|
| `symbols` | string | — | Comma-separated, e.g. `"RELIANCE,INFY,TCS"`. |
| `exchange` | string | `"NSE"` | Applied to each symbol. |
| `outputVariable` | string | — | `{{quotes.results[0].data.ltp}}`. |

#### optionChain — Option Chain

| Field | Type | Default | Notes |
|---|---|---|---|
| `underlying` | string | `"NIFTY"` | |
| `exchange` | `"NSE_INDEX"` \| `"BSE_INDEX"` | `"NSE_INDEX"` | |
| `expiryDate` | string | — | Format `"30DEC25"`. |
| `strikeCount` | int | `10` | Number of strikes above and below ATM. |
| `outputVariable` | string | — | `{{chain.atm_strike}}`, `{{chain.chain[0].ce.ltp}}`. |

#### syntheticFuture — Synthetic Future Price

| Field | Type | Default | Notes |
|---|---|---|---|
| `underlying`, `exchange`, `expiryDate`, `outputVariable` | (as `optionChain`) | | `{{synthFuture.synthetic_future_price}}`. |

#### holidays — Market Holidays

| Field | Type | Default | Notes |
|---|---|---|---|
| `exchange` | string | `"NSE"` | |
| `outputVariable` | string | — | |

#### timings — Market Timings

| Field | Type | Default | Notes |
|---|---|---|---|
| `exchange` | string | `"NSE"` | |
| `outputVariable` | string | — | |

#### margin — Margin Calculator

| Field | Type | Default | Notes |
|---|---|---|---|
| `symbol`, `exchange`, `quantity`, `price`, `product`, `action`, `priceType` | | | (Same shape as `placeOrder`.) |
| `outputVariable` | string | — | |

```json
{
  "id": "node_2",
  "type": "margin",
  "position": { "x": 100, "y": 100 },
  "data": {
    "symbol": "NIFTY30DEC25FUT",
    "exchange": "NFO",
    "quantity": 75,
    "price": 0,
    "product": "NRML",
    "action": "BUY",
    "priceType": "MARKET",
    "outputVariable": "marginCalc"
  }
}
```

---

### 7.5 Utility nodes

#### log — Log Message

| Field | Type | Default | Notes |
|---|---|---|---|
| `message` | string | — | Supports `{{vars}}`. |
| `level` | `"info"` \| `"warn"` \| `"error"` | `"info"` | |

```json
{ "id": "node_3", "type": "log", "position": { "x": 100, "y": 300 }, "data": { "message": "First expiry: {{expiries.data[0]}}", "level": "info" } }
```

#### telegramAlert — Telegram Alert

Sends a Telegram message via the per-user Telegram bot configured in OpenAlgo
settings.

| Field | Type | Default | Notes |
|---|---|---|---|
| `username` | string | — | OpenAlgo login ID linked to a Telegram user. |
| `message` | string | — | Supports `{{vars}}`. |

```json
{
  "id": "node_3",
  "type": "telegramAlert",
  "position": { "x": 100, "y": 300 },
  "data": {
    "username": "rajandran",
    "message": "Order placed: {{buyOrder.orderid}} for {{buyOrder.symbol}}"
  }
}
```

#### variable — Set / Update Variable

The UI dropdown offers eleven operations but only four are implemented by
the executor today; pick from those when authoring import JSON:

| Operation | Behaviour |
|---|---|
| `"set"` | Stores `value` under `variableName`. JSON-shaped strings (starting with `{` or `[`) are auto-parsed via `json.loads`, so you can carry structured data. |
| `"add"` | `current + value` (numeric coercion). Initialises to 0 if unset. |
| `"increment"` | `current + 1`. Initialises to 0 if unset. |
| `"decrement"` | `current - 1`. Initialises to 0 if unset. |

| Field | Type | Default | Notes |
|---|---|---|---|
| `variableName` | string | — | The name to set in workflow context. |
| `operation` | `"set"` \| `"add"` \| `"increment"` \| `"decrement"` | `"set"` | Other UI options (`subtract`, `multiply`, `divide`, `append`, `parse_json`, `stringify`, `get`) are **no-ops** on the executor side as of this writing — use `mathExpression` for arithmetic and `set` with a JSON-shaped string for structured assignment. |
| `value` | any | — | Strings accept `{{vars}}`. |

```json
{ "id": "node_3", "type": "variable", "position": { "x": 100, "y": 300 }, "data": { "variableName": "qty", "operation": "set", "value": "10" } }
```

For richer arithmetic, use `mathExpression`:

```json
{ "id": "node_3", "type": "mathExpression", "position": { "x": 100, "y": 300 }, "data": { "expression": "{{quote.data.ltp}} * 0.99", "outputVariable": "stopPrice" } }
```

#### mathExpression — Evaluate Math Expression

| Field | Type | Default | Notes |
|---|---|---|---|
| `expression` | string | — | Supports `+`, `-`, `*`, `/`, `%`, `**`, parentheses. Variables via `{{name}}`. |
| `outputVariable` | string | `"result"` | |

```json
{
  "id": "node_3",
  "type": "mathExpression",
  "position": { "x": 100, "y": 300 },
  "data": {
    "expression": "({{quote.data.ltp}} * {{lotSize}}) + {{brokerage}}",
    "outputVariable": "totalCost"
  }
}
```

#### httpRequest — HTTP Request

| Field | Type | Default | Notes |
|---|---|---|---|
| `method` | `"GET"` \| `"POST"` \| `"PUT"` \| `"DELETE"` \| `"PATCH"` | `"GET"` | |
| `url` | string | — | Supports `{{vars}}`. |
| `headers` | object \| JSON-string | `{}` | e.g. `{"Authorization": "Bearer {{token}}"}`. |
| `body` | string | — | JSON string, only used for POST/PUT/PATCH. Supports `{{vars}}`. |
| `timeout` | int | `30` | Seconds. |
| `outputVariable` | string | — | `{{apiResponse.data}}`, `{{apiResponse.status}}`. |

```json
{
  "id": "node_3",
  "type": "httpRequest",
  "position": { "x": 100, "y": 300 },
  "data": {
    "method": "POST",
    "url": "https://hooks.example.com/notify",
    "headers": "{\"Authorization\": \"Bearer {{secret}}\"}",
    "body": "{\"symbol\": \"{{webhook.symbol}}\", \"action\": \"{{webhook.action}}\"}",
    "timeout": 30,
    "outputVariable": "notifyResp"
  }
}
```

#### delay — Delay

| Field | Type | Default | Notes |
|---|---|---|---|
| `delayValue` | int | `1` | |
| `delayUnit` | `"seconds"` \| `"minutes"` \| `"hours"` | `"seconds"` | |

```json
{ "id": "node_3", "type": "delay", "position": { "x": 100, "y": 300 }, "data": { "delayValue": 30, "delayUnit": "seconds" } }
```

#### waitUntil — Wait Until Time

| Field | Type | Default | Notes |
|---|---|---|---|
| `targetTime` | `"HH:MM"` | `"09:30"` | If already past, the node returns immediately. |
| `label` | string | — | UI-only. |

```json
{ "id": "node_3", "type": "waitUntil", "position": { "x": 100, "y": 300 }, "data": { "targetTime": "15:25", "label": "Square-off entry" } }
```

#### group — Group / Visual Container

UI-only grouping. Has no executor behavior — the group's children execute on
their own edges. The Group node itself is a no-op when traversed.

| Field | Type | Default | Notes |
|---|---|---|---|
| `label` | string | — | |
| `color` | `"default"` \| `"blue"` \| `"green"` \| `"red"` \| `"purple"` \| `"orange"` | `"default"` | |

---

### 7.6 Stream nodes

These maintain a WebSocket subscription and either pass the latest tick to
their `outputVariable` (one-shot, used inside scheduled flows) or keep the
subscription alive across runs of the same workflow.

If WebSocket is unavailable for any reason, every stream node falls back to a
single REST call. Behaviour is identical from the workflow's point of view.

#### subscribeLtp — Subscribe LTP

| Field | Type | Default | Notes |
|---|---|---|---|
| `symbol`, `exchange`, `outputVariable` | | `outputVariable` defaults to `"ltp"`. | The variable receives the float LTP directly. |

```json
{ "id": "node_2", "type": "subscribeLtp", "position": { "x": 100, "y": 100 }, "data": { "symbol": "RELIANCE", "exchange": "NSE", "outputVariable": "rltp" } }
```

#### subscribeQuote — Subscribe Quote

| Field | Type | Default | Notes |
|---|---|---|---|
| `symbol`, `exchange`, `outputVariable` | | | Variable receives `{ ltp, open, high, low, close, volume, ... }`. |

#### subscribeDepth — Subscribe Depth

| Field | Type | Default | Notes |
|---|---|---|---|
| `symbol`, `exchange`, `outputVariable` | | | Variable receives `{ bids: [...], asks: [...], totalbuyqty, totalsellqty, ltp }`. |

#### unsubscribe — Unsubscribe

| Field | Type | Default | Notes |
|---|---|---|---|
| `streamType` | `"ltp"` \| `"quote"` \| `"depth"` \| `"all"` | `"all"` | |
| `symbol` | string | — | Empty = all symbols for this user. |
| `exchange` | string | `"NSE"` | |

---

## 8. End-to-end examples

### 8.1 Simple scheduled workflow

Run every weekday at 09:20 IST: place a 10-share BUY of RELIANCE if a
position does not already exist.

```json
{
  "name": "Daily RELIANCE Buy",
  "description": "Place a 10-share intraday BUY of RELIANCE at 09:20 if no existing position",
  "nodes": [
    {
      "id": "node_1",
      "type": "start",
      "position": { "x": 100, "y": 100 },
      "data": { "scheduleType": "daily", "time": "09:20", "days": [0,1,2,3,4], "marketHoursOnly": true }
    },
    {
      "id": "node_2",
      "type": "positionCheck",
      "position": { "x": 100, "y": 200 },
      "data": { "symbol": "RELIANCE", "exchange": "NSE", "product": "MIS", "condition": "not_exists" }
    },
    {
      "id": "node_3",
      "type": "placeOrder",
      "position": { "x": 100, "y": 300 },
      "data": {
        "symbol": "RELIANCE", "exchange": "NSE",
        "action": "BUY", "quantity": 10,
        "priceType": "MARKET", "product": "MIS",
        "outputVariable": "buyOrder"
      }
    },
    {
      "id": "node_4",
      "type": "log",
      "position": { "x": 300, "y": 300 },
      "data": { "message": "Skipped: position exists ({{buyOrder.orderid}} not placed)", "level": "info" }
    }
  ],
  "edges": [
    { "id": "e1", "source": "node_1", "target": "node_2" },
    { "id": "e2", "source": "node_2", "sourceHandle": "true",  "target": "node_3" },
    { "id": "e3", "source": "node_2", "sourceHandle": "false", "target": "node_4" }
  ]
}
```

### 8.2 Webhook-triggered options buy with expiry resolution

TradingView posts `{ "symbol": "NIFTY", "action": "BUY" }` to the webhook.
The workflow fetches the nearest weekly expiry, resolves the ATM CE symbol,
and places a 1-lot BUY.

```json
{
  "name": "TV NIFTY Long ATM CE",
  "description": "Webhook -> ATM weekly CE long entry on NIFTY",
  "nodes": [
    {
      "id": "node_1",
      "type": "webhookTrigger",
      "position": { "x": 100, "y": 100 },
      "data": { "label": "TV NIFTY Long", "symbol": "NIFTY", "exchange": "NFO" }
    },
    {
      "id": "node_2",
      "type": "expiry",
      "position": { "x": 100, "y": 200 },
      "data": { "symbol": "NIFTY", "exchange": "NFO", "instrumenttype": "options", "outputVariable": "expiries" }
    },
    {
      "id": "node_3",
      "type": "optionsOrder",
      "position": { "x": 100, "y": 300 },
      "data": {
        "underlying": "NIFTY",
        "expiryType": "current_week",
        "offset": "ATM",
        "optionType": "CE",
        "action": "BUY",
        "quantity": 1,
        "priceType": "MARKET",
        "product": "NRML",
        "outputVariable": "ceLong"
      }
    },
    {
      "id": "node_4",
      "type": "telegramAlert",
      "position": { "x": 300, "y": 300 },
      "data": { "username": "rajandran", "message": "Bought ATM CE: {{ceLong.orderid}} (expiry {{expiries.data[0]}})" }
    }
  ],
  "edges": [
    { "id": "e1", "source": "node_1", "target": "node_2" },
    { "id": "e2", "source": "node_2", "target": "node_3" },
    { "id": "e3", "source": "node_3", "target": "node_4" }
  ]
}
```

### 8.3 Funds-aware split entry

Every weekday at 09:30, fetch funds. If available cash >= ₹50k, split a 100-qty
SBIN buy into 5 chunks of 20; otherwise log the skip.

```json
{
  "name": "SBIN Funds-Gated Split Buy",
  "description": "Conditional split entry on SBIN with available-cash guard",
  "nodes": [
    { "id": "node_1", "type": "start",      "position": { "x": 100, "y":  60 }, "data": { "scheduleType": "daily", "time": "09:30", "days": [0,1,2,3,4], "marketHoursOnly": true } },
    { "id": "node_2", "type": "fundCheck",  "position": { "x": 100, "y": 180 }, "data": { "minAvailable": 50000 } },
    { "id": "node_3", "type": "splitOrder", "position": { "x":   0, "y": 300 }, "data": { "symbol": "SBIN", "exchange": "NSE", "action": "BUY", "quantity": 100, "splitSize": 20, "priceType": "MARKET", "product": "MIS", "outputVariable": "splitOut" } },
    { "id": "node_4", "type": "log",        "position": { "x": 240, "y": 300 }, "data": { "message": "Skipped SBIN entry: available cash below 50k", "level": "warn" } }
  ],
  "edges": [
    { "id": "e1", "source": "node_1", "target": "node_2" },
    { "id": "e2", "source": "node_2", "sourceHandle": "true",  "target": "node_3" },
    { "id": "e3", "source": "node_2", "sourceHandle": "false", "target": "node_4" }
  ]
}
```

### 8.4 Realized P&L Telegram every minute

Pings the configured Telegram user with realized + unrealized P&L every minute
during market hours. Useful for "watchdog" supervision.

```json
{
  "name": "Realized PnL Telegram Watchdog",
  "description": "Funds snapshot to Telegram every 1 min during market hours",
  "nodes": [
    { "id": "node_1", "type": "start",         "position": { "x": 100, "y": 100 }, "data": { "scheduleType": "interval", "intervalValue": 1, "intervalUnit": "minutes", "marketHoursOnly": true } },
    { "id": "node_2", "type": "funds",         "position": { "x": 100, "y": 220 }, "data": { "outputVariable": "funds" } },
    { "id": "node_3", "type": "telegramAlert", "position": { "x": 100, "y": 340 }, "data": { "username": "rajandran", "message": "Realized: Rs {{funds.data.m2mrealized}} | Unrealized: Rs {{funds.data.m2munrealized}} | Cash: Rs {{funds.data.availablecash}} | At {{time}} IST" } }
  ],
  "edges": [
    { "id": "e1", "source": "node_1", "target": "node_2" },
    { "id": "e2", "source": "node_2", "target": "node_3" }
  ]
}
```

Note `m2mrealized` and `m2munrealized` are returned as **strings** (e.g.
`"1234.50"`). They interpolate into the Telegram message correctly; if you
want to use them in a `priceCondition`, wrap them via `mathExpression` first.

### 8.5 P&L stop-loss circuit breaker

Polls the position book every 30 seconds. If aggregate P&L drops below
₹-2000, square off everything and notify Telegram.

```json
{
  "name": "Aggregate PnL Stop-Loss",
  "description": "Square off when total open-position pnl falls below -2000",
  "nodes": [
    { "id": "node_1", "type": "start",          "position": { "x": 100, "y":  60 }, "data": { "scheduleType": "interval", "intervalValue": 30, "intervalUnit": "seconds", "marketHoursOnly": true } },
    { "id": "node_2", "type": "funds",          "position": { "x": 100, "y": 180 }, "data": { "outputVariable": "f" } },
    { "id": "node_3", "type": "mathExpression", "position": { "x": 100, "y": 300 }, "data": { "expression": "{{f.data.m2mrealized}} + {{f.data.m2munrealized}}", "outputVariable": "totalPnL" } },
    { "id": "node_4", "type": "priceCondition", "position": { "x": 100, "y": 420 }, "data": { "symbol": "RELIANCE", "exchange": "NSE", "field": "ltp", "operator": "<", "value": -2000 } },
    { "id": "node_5", "type": "closePositions","position": { "x":   0, "y": 540 }, "data": {} },
    { "id": "node_6", "type": "telegramAlert",  "position": { "x": 240, "y": 540 }, "data": { "username": "rajandran", "message": "PnL stop-loss tripped at {{totalPnL}}, all positions squared off" } }
  ],
  "edges": [
    { "id": "e1", "source": "node_1", "target": "node_2" },
    { "id": "e2", "source": "node_2", "target": "node_3" },
    { "id": "e3", "source": "node_3", "target": "node_4" },
    { "id": "e4", "source": "node_4", "sourceHandle": "true", "target": "node_5" },
    { "id": "e5", "source": "node_5", "target": "node_6" }
  ]
}
```

> Note: today the `priceCondition` node compares against a quote-fetched
> field (`ltp`/`open`/etc.). If you want to compare a workflow variable like
> `{{totalPnL}}` directly, you currently need to write the value into a quote
> via the broker — or wait for a `varCondition` node. For now the example
> above is illustrative; in practice, square off via a `priceCondition` on
> the actual symbol's LTP, or use a `mathExpression` -> negative-result
> heuristic gate built from `andGate`.

### 8.6 Iron condor with custom legs

`optionsMultiOrder` accepts a `legs` array when `strategy="custom"` —
useful for any structure the preset enums don't cover (calendars, ratios,
butterflies). Each leg is `{ offset, optionType, action, quantity }` and
optionally a leg-specific `expiryDate` for diagonals.

```json
{
  "name": "NIFTY Custom Iron Fly",
  "description": "ATM straddle hedged with OTM3 wings, current-week expiry",
  "nodes": [
    { "id": "node_1", "type": "start",             "position": { "x": 100, "y": 100 }, "data": { "scheduleType": "daily", "time": "09:25", "days": [0,1,2,3,4], "marketHoursOnly": true } },
    { "id": "node_2", "type": "optionsMultiOrder", "position": { "x": 100, "y": 240 }, "data": {
      "strategy": "custom",
      "underlying": "NIFTY",
      "expiryType": "current_week",
      "action": "SELL",
      "quantity": 1,
      "priceType": "MARKET",
      "product": "NRML",
      "legs": [
        { "offset": "ATM",  "optionType": "CE", "action": "SELL", "quantity": 1 },
        { "offset": "ATM",  "optionType": "PE", "action": "SELL", "quantity": 1 },
        { "offset": "OTM3", "optionType": "CE", "action": "BUY",  "quantity": 1 },
        { "offset": "OTM3", "optionType": "PE", "action": "BUY",  "quantity": 1 }
      ],
      "outputVariable": "ironFly"
    } }
  ],
  "edges": [ { "id": "e1", "source": "node_1", "target": "node_2" } ]
}
```

### 8.7 Webhook → external HTTP forward

Receive a webhook, then fan out: place an OpenAlgo order **and** post a
copy of the payload to an external system (e.g. a Discord bot or a
spreadsheet endpoint) for audit.

```json
{
  "name": "Webhook to Order + External Audit",
  "description": "Place order from webhook payload and POST to external audit URL",
  "nodes": [
    { "id": "node_1", "type": "webhookTrigger", "position": { "x": 100, "y":  80 }, "data": { "label": "TV Webhook", "exchange": "NSE" } },
    { "id": "node_2", "type": "placeOrder",     "position": { "x":   0, "y": 220 }, "data": {
      "symbol": "{{webhook.symbol}}",
      "exchange": "{{webhook.exchange}}",
      "action": "{{webhook.action}}",
      "quantity": "{{webhook.qty}}",
      "priceType": "MARKET",
      "product": "MIS",
      "outputVariable": "ord"
    } },
    { "id": "node_3", "type": "httpRequest",    "position": { "x": 240, "y": 220 }, "data": {
      "method": "POST",
      "url": "https://audit.example.com/orders",
      "headers": "{\"Content-Type\": \"application/json\"}",
      "body": "{\"symbol\": \"{{webhook.symbol}}\", \"action\": \"{{webhook.action}}\", \"orderid\": \"{{ord.orderid}}\", \"ts\": \"{{iso_timestamp}}\"}",
      "timeout": 10,
      "outputVariable": "auditResp"
    } }
  ],
  "edges": [
    { "id": "e1", "source": "node_1", "target": "node_2" },
    { "id": "e2", "source": "node_1", "target": "node_3" }
  ]
}
```

### 8.8 Three-condition AND gate

Time-window AND price-above AND no-existing-position. Demonstrates
`inputCount: 3` and `targetHandle: "input-N"`.

```json
{
  "name": "Triple-Condition Long Entry",
  "description": "Long RELIANCE only inside trading window, above 1500, with no existing long",
  "nodes": [
    { "id": "node_1", "type": "start",          "position": { "x": 200, "y":  20 }, "data": { "scheduleType": "interval", "intervalValue": 1, "intervalUnit": "minutes", "marketHoursOnly": true } },
    { "id": "node_2", "type": "timeWindow",     "position": { "x":   0, "y": 140 }, "data": { "startTime": "09:30", "endTime": "14:30" } },
    { "id": "node_3", "type": "priceCondition", "position": { "x": 200, "y": 140 }, "data": { "symbol": "RELIANCE", "exchange": "NSE", "field": "ltp", "operator": ">", "value": 1500 } },
    { "id": "node_4", "type": "positionCheck",  "position": { "x": 400, "y": 140 }, "data": { "symbol": "RELIANCE", "exchange": "NSE", "product": "MIS", "condition": "not_exists" } },
    { "id": "node_5", "type": "andGate",        "position": { "x": 200, "y": 280 }, "data": { "inputCount": 3 } },
    { "id": "node_6", "type": "placeOrder",     "position": { "x": 200, "y": 400 }, "data": { "symbol": "RELIANCE", "exchange": "NSE", "action": "BUY", "quantity": 1, "priceType": "MARKET", "product": "MIS", "outputVariable": "ord" } }
  ],
  "edges": [
    { "id": "e1", "source": "node_1", "target": "node_2" },
    { "id": "e2", "source": "node_1", "target": "node_3" },
    { "id": "e3", "source": "node_1", "target": "node_4" },
    { "id": "e4", "source": "node_2", "sourceHandle": "true", "target": "node_5", "targetHandle": "input-0" },
    { "id": "e5", "source": "node_3", "sourceHandle": "true", "target": "node_5", "targetHandle": "input-1" },
    { "id": "e6", "source": "node_4", "sourceHandle": "true", "target": "node_5", "targetHandle": "input-2" },
    { "id": "e7", "source": "node_5", "sourceHandle": "true", "target": "node_6" }
  ]
}
```

### 8.9 Place order, wait, then auto-cancel

Demonstrates `delay` + variable interpolation of an upstream order id. Places a
LIMIT BUY at LTP - 0.5%, waits 90s, and cancels if it hasn't filled yet. The
broker will silently no-op the cancel if the order already completed, so this
is safe.

```json
{
  "name": "RELIANCE LIMIT with 90s Auto-Cancel",
  "description": "Place a sub-LTP limit and cancel if unfilled after 90 seconds",
  "nodes": [
    { "id": "node_1", "type": "start",         "position": { "x": 100, "y":  60 }, "data": { "scheduleType": "daily", "time": "09:30", "days": [0,1,2,3,4], "marketHoursOnly": true } },
    { "id": "node_2", "type": "getQuote",      "position": { "x": 100, "y": 180 }, "data": { "symbol": "RELIANCE", "exchange": "NSE", "outputVariable": "q" } },
    { "id": "node_3", "type": "mathExpression","position": { "x": 100, "y": 300 }, "data": { "expression": "{{q.data.ltp}} * 0.995", "outputVariable": "limitPx" } },
    { "id": "node_4", "type": "placeOrder",    "position": { "x": 100, "y": 420 }, "data": { "symbol": "RELIANCE", "exchange": "NSE", "action": "BUY", "quantity": 5, "priceType": "LIMIT", "product": "MIS", "price": "{{limitPx}}", "outputVariable": "ord" } },
    { "id": "node_5", "type": "delay",         "position": { "x": 100, "y": 540 }, "data": { "delayValue": 90, "delayUnit": "seconds" } },
    { "id": "node_6", "type": "cancelOrder",   "position": { "x": 100, "y": 660 }, "data": { "orderId": "{{ord.orderid}}" } },
    { "id": "node_7", "type": "log",           "position": { "x": 100, "y": 780 }, "data": { "message": "Auto-cancel sent for {{ord.orderid}} at {{time}} IST", "level": "info" } }
  ],
  "edges": [
    { "id": "e1", "source": "node_1", "target": "node_2" },
    { "id": "e2", "source": "node_2", "target": "node_3" },
    { "id": "e3", "source": "node_3", "target": "node_4" },
    { "id": "e4", "source": "node_4", "target": "node_5" },
    { "id": "e5", "source": "node_5", "target": "node_6" },
    { "id": "e6", "source": "node_6", "target": "node_7" }
  ]
}
```

### 8.10 Wait until square-off, then close + log

Use `waitUntil` to pause execution until 15:15 IST, then close all open
positions and log the action. Useful as a tail-end of any intraday flow.

```json
{
  "name": "Intraday Square-Off at 15:15",
  "description": "Wait until 15:15 IST, close all open positions, log the squareoff",
  "nodes": [
    { "id": "node_1", "type": "start",          "position": { "x": 100, "y":  60 }, "data": { "scheduleType": "daily", "time": "09:25", "days": [0,1,2,3,4], "marketHoursOnly": true } },
    { "id": "node_2", "type": "waitUntil",      "position": { "x": 100, "y": 180 }, "data": { "targetTime": "15:15", "label": "Square-off window" } },
    { "id": "node_3", "type": "closePositions", "position": { "x": 100, "y": 300 }, "data": {} },
    { "id": "node_4", "type": "log",            "position": { "x": 100, "y": 420 }, "data": { "message": "Daily square-off completed at {{time}} IST", "level": "info" } },
    { "id": "node_5", "type": "telegramAlert",  "position": { "x": 100, "y": 540 }, "data": { "username": "rajandran", "message": "[OpenAlgo] Daily square-off done at {{time}} IST on {{date}}" } }
  ],
  "edges": [
    { "id": "e1", "source": "node_1", "target": "node_2" },
    { "id": "e2", "source": "node_2", "target": "node_3" },
    { "id": "e3", "source": "node_3", "target": "node_4" },
    { "id": "e4", "source": "node_4", "target": "node_5" }
  ]
}
```

### 8.11 Quantity from a math expression

Sizes a position based on a fraction of available cash divided by LTP. Shows
`getQuote` → `funds` → `mathExpression` → `variable` (set with computed value)
→ `placeOrder` referencing the computed quantity.

```json
{
  "name": "RELIANCE 5%-of-Cash Sizing",
  "description": "Size BUY quantity at floor(0.05 * available_cash / ltp)",
  "nodes": [
    { "id": "node_1", "type": "start",          "position": { "x": 100, "y":  60 }, "data": { "scheduleType": "daily", "time": "09:30", "days": [0,1,2,3,4], "marketHoursOnly": true } },
    { "id": "node_2", "type": "funds",          "position": { "x": 100, "y": 180 }, "data": { "outputVariable": "f" } },
    { "id": "node_3", "type": "getQuote",       "position": { "x": 100, "y": 300 }, "data": { "symbol": "RELIANCE", "exchange": "NSE", "outputVariable": "q" } },
    { "id": "node_4", "type": "mathExpression", "position": { "x": 100, "y": 420 }, "data": { "expression": "(0.05 * {{f.data.availablecash}}) / {{q.data.ltp}}", "outputVariable": "sizedQty" } },
    { "id": "node_5", "type": "placeOrder",     "position": { "x": 100, "y": 540 }, "data": { "symbol": "RELIANCE", "exchange": "NSE", "action": "BUY", "quantity": "{{sizedQty}}", "priceType": "MARKET", "product": "CNC", "outputVariable": "ord" } },
    { "id": "node_6", "type": "log",            "position": { "x": 100, "y": 660 }, "data": { "message": "Sized BUY {{sizedQty}} units at LTP {{q.data.ltp}} (cash={{f.data.availablecash}}) -> orderid {{ord.orderid}}", "level": "info" } }
  ],
  "edges": [
    { "id": "e1", "source": "node_1", "target": "node_2" },
    { "id": "e2", "source": "node_2", "target": "node_3" },
    { "id": "e3", "source": "node_3", "target": "node_4" },
    { "id": "e4", "source": "node_4", "target": "node_5" },
    { "id": "e5", "source": "node_5", "target": "node_6" }
  ]
}
```

> The `mathExpression` result will be a float (e.g. `1.234`). The
> placeOrder node coerces the `quantity` field via `int(...)` so a float
> truncates toward zero as in Python. Wrap with `floor()` in your math if
> you want explicit rounding logic.

### 8.12 Per-day order counter (variable increment)

Keep an in-context counter of how many orders have been placed today. The
`variable` node's `increment` operation initialises to 0 if unset, so no
explicit reset is needed at the workflow's first run.

```json
{
  "name": "Hourly Buy with Daily Counter",
  "description": "Place 1 order per hour and track count via variable.increment",
  "nodes": [
    { "id": "node_1", "type": "start",       "position": { "x": 100, "y":  60 }, "data": { "scheduleType": "interval", "intervalValue": 1, "intervalUnit": "hours", "marketHoursOnly": true } },
    { "id": "node_2", "type": "placeOrder",  "position": { "x": 100, "y": 180 }, "data": { "symbol": "TATAMOTORS", "exchange": "NSE", "action": "BUY", "quantity": 1, "priceType": "MARKET", "product": "MIS", "outputVariable": "ord" } },
    { "id": "node_3", "type": "variable",    "position": { "x": 100, "y": 300 }, "data": { "variableName": "todayCount", "operation": "increment" } },
    { "id": "node_4", "type": "log",         "position": { "x": 100, "y": 420 }, "data": { "message": "Order #{{todayCount}} placed: {{ord.orderid}}", "level": "info" } }
  ],
  "edges": [
    { "id": "e1", "source": "node_1", "target": "node_2" },
    { "id": "e2", "source": "node_2", "target": "node_3" },
    { "id": "e3", "source": "node_3", "target": "node_4" }
  ]
}
```

> **Counter scope.** `variable` storage is per-workflow-run today. Across
> separate scheduled runs the counter resets to 0 each time. For a true
> daily-persistent counter, write to the DB via an `httpRequest` to your
> own endpoint, or use the broker's order-book and count the orders.

### 8.13 Compound condition (AND gate, two inputs)

Place an order only when (a) it is between 09:30–14:30 **and** (b) the symbol's
LTP is above 1500.

```json
{
  "name": "RELIANCE Long Above 1500 in Window",
  "description": "Buy 1 share of RELIANCE only when LTP > 1500 between 09:30 and 14:30",
  "nodes": [
    { "id": "node_1", "type": "start",          "position": {"x":100,"y": 50}, "data": { "scheduleType": "interval", "intervalValue": 1, "intervalUnit": "minutes", "marketHoursOnly": true } },
    { "id": "node_2", "type": "timeWindow",     "position": {"x":100,"y":150}, "data": { "startTime": "09:30", "endTime": "14:30" } },
    { "id": "node_3", "type": "priceCondition", "position": {"x":300,"y":150}, "data": { "symbol": "RELIANCE", "exchange": "NSE", "field": "ltp", "operator": ">", "value": 1500 } },
    { "id": "node_4", "type": "andGate",        "position": {"x":200,"y":250}, "data": { "inputCount": 2 } },
    { "id": "node_5", "type": "placeOrder",     "position": {"x":200,"y":350}, "data": { "symbol": "RELIANCE", "exchange": "NSE", "action": "BUY", "quantity": 1, "priceType": "MARKET", "product": "MIS", "outputVariable": "ord" } }
  ],
  "edges": [
    { "id": "e1", "source": "node_1", "target": "node_2" },
    { "id": "e2", "source": "node_1", "target": "node_3" },
    { "id": "e3", "source": "node_2", "sourceHandle": "true", "target": "node_4", "targetHandle": "input-0" },
    { "id": "e4", "source": "node_3", "sourceHandle": "true", "target": "node_4", "targetHandle": "input-1" },
    { "id": "e5", "source": "node_4", "sourceHandle": "true", "target": "node_5" }
  ]
}
```

---

## 9. Exchanges

Valid `exchange` values across all nodes:

| Code | Segment |
|---|---|
| `NSE` | NSE Equity |
| `BSE` | BSE Equity |
| `NFO` | NSE F&O |
| `BFO` | BSE F&O |
| `CDS` | NSE Currency |
| `BCD` | BSE Currency |
| `MCX` | Commodity |
| `NCDEX` | Commodity |
| `NSE_INDEX` | NSE Indices (for `optionsOrder`/`optionChain`/`optionSymbol`/`syntheticFuture`) |
| `BSE_INDEX` | BSE Indices (same usage as above) |

---

## 10. Symbol format

OpenAlgo standardizes broker-specific symbols to the following format. See
`docs/prompt/symbol-format.md` for the complete spec; the short form:

- **Equity:** `INFY`, `RELIANCE`, `TATAMOTORS`
- **Futures:** `<base><DDMMMYY>FUT` — `BANKNIFTY24APR24FUT`, `CRUDEOILM20MAY24FUT`
- **Options:** `<base><DDMMMYY><strike><CE|PE>` — `NIFTY28MAR2420800CE`, `VEDL25APR24292.5CE`
- **Indices:** `NIFTY`, `SENSEX`, `BANKNIFTY` etc. on `NSE_INDEX` / `BSE_INDEX`

---

## 11. Order constants

For convenience in one place:

- **Action:** `BUY`, `SELL`
- **Product:** `CNC` (cash & carry / delivery), `NRML` (futures & options carry), `MIS` (intraday)
- **Price type:** `MARKET`, `LIMIT`, `SL` (stop-loss limit), `SL-M` (stop-loss market)
- **Option type:** `CE`, `PE`
- **Strike offset:** `ATM`, `ITM1`–`ITM5`, `OTM1`–`OTM10`
- **Expiry type (preset):** `current_week`, `next_week`, `current_month`, `next_month`

---

## 12. Common patterns

### Use the first expiry from the dynamic list

```
expiry node (outputVariable=expiries)  →  symbol-using node ({{expiries.data[0]}})
```

### Place an order conditional on free margin

```
fundCheck (minAvailable=50000)
   ├── true  → placeOrder ...
   └── false → log "Insufficient funds"
```

### Cancel an order after a fixed delay

```
placeOrder (outputVariable=ord)  →  delay (60s)  →  cancelOrder (orderId={{ord.orderid}})
```

### Square off everything if MTM crosses a P&L threshold

```
positionBook (outputVariable=positions)
  → mathExpression (expression=sum of {{positions.data[i].pnl}})
  → priceCondition (operator="<", value=-5000) on the computed MTM
      └── true  → closePositions
```

---

## 13. Pitfalls

- **Missing top-level `name` on import.** The Flow Editor's import dialog
  rejects any JSON missing a `name` field with *"Invalid workflow format.
  Must have name, nodes, and edges."* The executor itself never reads it —
  only the importer does. See §1.
- **`JSON.parse` failures during paste.** *"Invalid JSON format. Please
  check the workflow data."* always means the text isn't valid JSON. Common
  causes: smart-quote conversion (`"` → `"` `"`) by Slack/Discord/word
  processors, BOM/zero-width characters from doc editors, real newlines
  injected inside a string value (use `\n` if you need a newline, never a
  literal line break inside `"..."`). The fix-of-last-resort is to save the
  JSON to a `.json` file and use the **file upload** button in the import
  dialog — that path goes through `FileReader` and bypasses clipboard
  munging entirely.
- **Output variable not set.** If a downstream node references `{{name.field}}`
  but the upstream producer doesn't have `outputVariable: "name"` set, the
  literal `{{name.field}}` string is passed through. The workflow runs but
  the value is wrong. The Execution Log will show the placeholder verbatim.
- **`sourceHandle` mismatch.** PositionCheck/FundCheck/PriceCondition/TimeWindow
  fork on `"true"`/`"false"`, while NotGate/TimeCondition fork on `"yes"`/`"no"`.
  Both vocabularies are accepted, but be consistent within a workflow.
- **AND/OR gate target slots.** Without `targetHandle: "input-N"`, multiple
  edges into a gate are treated ambiguously. Always pin them.
- **Webhook trigger without saved workflow.** The webhook URL is minted on
  save. Importing a workflow with a `webhookTrigger` node and trying to use
  the URL before saving will fail. Save first, then copy the URL from the
  ConfigPanel.
- **`expiryDate` format.** Strings like `"30DEC25"` (no separator, uppercase
  month). The `expiry` node returns `"30-DEC-25"` (with hyphens) — pass that
  through `_format_expiry_for_api` if hand-converting, or use `expiryType`
  presets which the executor resolves automatically.
- **Lot size handling differs per node.** `optionsOrder` and
  `optionsMultiOrder` accept `quantity` **in lots** (multiplied by lot size
  internally). `placeOrder` / `smartOrder` / `splitOrder` / `basketOrder`
  accept `quantity` **in shares**. Check this when generating from a single
  source.

---

## 14. Where this is enforced

- Node type strings: `services/flow_executor_service.py` (top-level
  `execute_node_chain` dispatch).
- Per-node field reads: each `execute_*` method in
  `services/flow_executor_service.py`.
- UI defaults: `frontend/src/lib/flow/constants.ts` (`DEFAULT_NODE_DATA`).
- UI ↔ field mapping: `frontend/src/components/flow/panels/ConfigPanel.tsx`.
- Edge filtering: `services/flow_executor_service.py:execute_node_chain`
  → the `if result and "condition" in result:` block.

If this doc and the code disagree, the code wins. Open a PR.

```


---

# FILE: docs\prompt\hybrid - openalgo indicators.md

```md
# Hybrid

Hybrid indicators combine multiple analytical approaches to provide comprehensive market analysis. These indicators often merge trend, momentum, volatility, and volume components for enhanced signal quality.

### Import Statement

```python
from openalgo import api, ta

# Get data using OpenAlgo API
client = api(api_key='your_api_key_here', host='http://127.0.0.1:5000')
df = client.history(symbol="SBIN", exchange="NSE", interval="5m", 
                   start_date="2025-04-01", end_date="2025-04-08")
```

### Available Hybrid Indicators

***

### Average Directional Index (ADX)

ADX measures the strength of a trend regardless of direction, providing both directional indicators (+DI, -DI) and trend strength (ADX).

#### Usage

```python
di_plus, di_minus, adx = ta.adx(high, low, close, period=14)
```

#### Parameters

* **high** *(array-like)*: High prices
* **low** *(array-like)*: Low prices
* **close** *(array-like)*: Closing prices
* **period** *(int, default=14)*: Period for ADX calculation

#### Returns

* **tuple**: (+DI, -DI, ADX) arrays in the same format as input

#### Example

```python
# Calculate ADX system
di_plus, di_minus, adx = ta.adx(df['high'], df['low'], df['close'], period=14)

df['DI_Plus'] = di_plus
df['DI_Minus'] = di_minus  
df['ADX'] = adx

# Trend analysis
df['Trend_Strength'] = df['ADX'].apply(lambda x: 'Strong' if x > 25 else 'Weak' if x > 20 else 'No Trend')
df['Trend_Direction'] = df.apply(lambda row: 'Bullish' if row['DI_Plus'] > row['DI_Minus'] 
                                 else 'Bearish' if row['DI_Minus'] > row['DI_Plus'] else 'Neutral', axis=1)

print(df[['close', 'DI_Plus', 'DI_Minus', 'ADX', 'Trend_Strength', 'Trend_Direction']].tail())
```

***

### Aroon Indicator

Aroon indicators measure the time since the highest high and lowest low, indicating trend strength and potential reversals.

#### Usage

```python
aroon_up, aroon_down = ta.aroon(high, low, period=14)
```

#### Parameters

* **high** *(array-like)*: High prices
* **low** *(array-like)*: Low prices
* **period** *(int, default=14)*: Period for Aroon calculation

#### Returns

* **tuple**: (aroon\_up, aroon\_down) arrays in the same format as input

#### Example

```python
# Calculate Aroon indicators
aroon_up, aroon_down = ta.aroon(df['high'], df['low'], period=25)

df['Aroon_Up'] = aroon_up
df['Aroon_Down'] = aroon_down
df['Aroon_Oscillator'] = df['Aroon_Up'] - df['Aroon_Down']

# Signal interpretation
df['Aroon_Signal'] = df.apply(lambda row: 
    'Strong Uptrend' if row['Aroon_Up'] > 70 and row['Aroon_Down'] < 30
    else 'Strong Downtrend' if row['Aroon_Down'] > 70 and row['Aroon_Up'] < 30
    else 'Sideways' if abs(row['Aroon_Up'] - row['Aroon_Down']) < 20
    else 'Trending', axis=1)

print(df[['close', 'Aroon_Up', 'Aroon_Down', 'Aroon_Oscillator', 'Aroon_Signal']].tail())
```

***

### Pivot Points

Traditional pivot points calculate support and resistance levels based on previous period's high, low, and close.

#### Usage

```python
pivot, r1, s1, r2, s2, r3, s3 = ta.pivot_points(high, low, close)
```

#### Parameters

* **high** *(array-like)*: High prices
* **low** *(array-like)*: Low prices
* **close** *(array-like)*: Closing prices

#### Returns

* **tuple**: (pivot, r1, s1, r2, s2, r3, s3) arrays

#### Example

```python
# Calculate Pivot Points
pivot, r1, s1, r2, s2, r3, s3 = ta.pivot_points(df['high'], df['low'], df['close'])

df['Pivot'] = pivot
df['Resistance_1'] = r1
df['Support_1'] = s1
df['Resistance_2'] = r2
df['Support_2'] = s2
df['Resistance_3'] = r3
df['Support_3'] = s3

# Identify price position relative to pivot
df['Price_Position'] = df.apply(lambda row:
    'Above R2' if row['close'] > row['Resistance_2']
    else 'Above R1' if row['close'] > row['Resistance_1']
    else 'Above Pivot' if row['close'] > row['Pivot']
    else 'Below Pivot' if row['close'] < row['Support_1']
    else 'Below S1' if row['close'] < row['Support_2']
    else 'Below S2' if row['close'] < row['Support_2']
    else 'Near Pivot', axis=1)

print(df[['close', 'Pivot', 'Resistance_1', 'Support_1', 'Price_Position']].tail())
```

***

### Parabolic SAR

Parabolic SAR provides trailing stop levels and trend direction signals.

#### Usage

```python
sar_values, trend_direction = ta.psar(high, low, acceleration=0.02, maximum=0.2)
```

#### Parameters

* **high** *(array-like)*: High prices
* **low** *(array-like)*: Low prices
* **acceleration** *(float, default=0.02)*: Acceleration factor
* **maximum** *(float, default=0.2)*: Maximum acceleration factor

#### Returns

* **tuple**: (sar\_values, trend\_direction) arrays

#### Example

```python
# Calculate Parabolic SAR
sar_values, trend_direction = ta.psar(df['high'], df['low'])

df['SAR'] = sar_values
df['SAR_Trend'] = trend_direction

# Generate trading signals
df['SAR_Signal'] = df.apply(lambda row:
    'Buy' if row['close'] > row['SAR'] and row['SAR_Trend'] == -1  # Uptrend
    else 'Sell' if row['close'] < row['SAR'] and row['SAR_Trend'] == 1  # Downtrend
    else 'Hold', axis=1)

# Calculate distance from SAR (risk management)
df['SAR_Distance'] = abs(df['close'] - df['SAR'])
df['SAR_Distance_Pct'] = (df['SAR_Distance'] / df['close']) * 100

print(df[['close', 'SAR', 'SAR_Signal', 'SAR_Distance_Pct']].tail())
```

***

### Directional Movement Index (DMI)

DMI focuses on the directional indicators (+DI and -DI) without the ADX component.

#### Usage

```python
di_plus, di_minus = ta.dmi(high, low, close, period=14)
```

#### Parameters

* **high** *(array-like)*: High prices
* **low** *(array-like)*: Low prices
* **close** *(array-like)*: Closing prices
* **period** *(int, default=14)*: Period for DMI calculation

#### Returns

* **tuple**: (+DI, -DI) arrays in the same format as input

#### Example

```python
# Calculate DMI
di_plus, di_minus = ta.dmi(df['high'], df['low'], df['close'])

df['DI_Plus'] = di_plus
df['DI_Minus'] = di_minus
df['DI_Spread'] = df['DI_Plus'] - df['DI_Minus']

# Generate directional signals
df['DMI_Signal'] = df.apply(lambda row:
    'Strong Buy' if row['DI_Plus'] > row['DI_Minus'] and row['DI_Spread'] > 10
    else 'Buy' if row['DI_Plus'] > row['DI_Minus']
    else 'Strong Sell' if row['DI_Minus'] > row['DI_Plus'] and row['DI_Spread'] < -10
    else 'Sell' if row['DI_Minus'] > row['DI_Plus']
    else 'Neutral', axis=1)

print(df[['close', 'DI_Plus', 'DI_Minus', 'DI_Spread', 'DMI_Signal']].tail())
```

***

### Williams Fractals

Williams Fractals identify turning points (fractals) in price action using local highs and lows.

#### Usage

```python
fractal_up, fractal_down = ta.fractals(high, low, periods=2)
```

#### Parameters

* **high** *(array-like)*: High prices
* **low** *(array-like)*: Low prices
* **periods** *(int, default=2)*: Number of periods to check (minimum 2)

#### Returns

* **tuple**: (fractal\_up, fractal\_down) boolean arrays indicating fractal points

#### Example

```python
# Calculate Williams Fractals
fractal_up, fractal_down = ta.fractals(df['high'], df['low'], periods=2)

df['Fractal_Up'] = fractal_up
df['Fractal_Down'] = fractal_down

# Mark fractal levels
df['Fractal_High'] = df['high'].where(df['Fractal_Up'])
df['Fractal_Low'] = df['low'].where(df['Fractal_Down'])

# Count recent fractals for market structure analysis
window = 20
df['Recent_Fractal_Highs'] = df['Fractal_Up'].rolling(window).sum()
df['Recent_Fractal_Lows'] = df['Fractal_Down'].rolling(window).sum()

df['Market_Structure'] = df.apply(lambda row:
    'Bullish Structure' if row['Recent_Fractal_Lows'] > row['Recent_Fractal_Highs']
    else 'Bearish Structure' if row['Recent_Fractal_Highs'] > row['Recent_Fractal_Lows']
    else 'Balanced', axis=1)

print(df[['close', 'Fractal_High', 'Fractal_Low', 'Market_Structure']].dropna().tail())
```

***

### Random Walk Index (RWI)

RWI measures how much a security's price movement differs from a random walk, helping identify trending vs. random price movements.

#### Usage

```python
rwi_high, rwi_low = ta.rwi(high, low, close, period=14)
```

#### Parameters

* **high** *(array-like)*: High prices
* **low** *(array-like)*: Low prices
* **close** *(array-like)*: Closing prices
* **period** *(int, default=14)*: Period for RWI calculation

#### Returns

* **tuple**: (rwi\_high, rwi\_low) arrays in the same format as input

#### Example

```python
# Calculate Random Walk Index
rwi_high, rwi_low = ta.rwi(df['high'], df['low'], df['close'], period=14)

df['RWI_High'] = rwi_high
df['RWI_Low'] = rwi_low
df['RWI_Max'] = df[['RWI_High', 'RWI_Low']].max(axis=1)

# Interpret RWI signals
df['RWI_Signal'] = df.apply(lambda row:
    'Strong Uptrend' if row['RWI_High'] > 1.0 and row['RWI_High'] > row['RWI_Low']
    else 'Strong Downtrend' if row['RWI_Low'] > 1.0 and row['RWI_Low'] > row['RWI_High']
    else 'Weak Uptrend' if row['RWI_High'] > row['RWI_Low'] and row['RWI_High'] > 0.6
    else 'Weak Downtrend' if row['RWI_Low'] > row['RWI_High'] and row['RWI_Low'] > 0.6
    else 'Random Walk', axis=1)

# Calculate trend strength
df['Trend_Strength_RWI'] = df['RWI_Max'].apply(lambda x:
    'Very Strong' if x > 1.5
    else 'Strong' if x > 1.0
    else 'Moderate' if x > 0.6
    else 'Weak')

print(df[['close', 'RWI_High', 'RWI_Low', 'RWI_Signal', 'Trend_Strength_RWI']].tail())
```

***

### Complete Example: Comprehensive Trend Analysis

```python
import pandas as pd
from openalgo import api, ta

# Get market data
client = api(api_key='your_api_key_here', host='http://127.0.0.1:5000')
df = client.history(symbol="SBIN", exchange="NSE", interval="5m", 
                   start_date="2025-04-01", end_date="2025-04-08")

# Calculate multiple hybrid indicators
print("Calculating hybrid indicators...")

# ADX System
di_plus, di_minus, adx = ta.adx(df['high'], df['low'], df['close'])
df['DI_Plus'] = di_plus
df['DI_Minus'] = di_minus
df['ADX'] = adx

# Aroon System
aroon_up, aroon_down = ta.aroon(df['high'], df['low'])
df['Aroon_Up'] = aroon_up
df['Aroon_Down'] = aroon_down
df['Aroon_Osc'] = df['Aroon_Up'] - df['Aroon_Down']

# Parabolic SAR
sar_values, sar_trend = ta.psar(df['high'], df['low'])
df['SAR'] = sar_values
df['SAR_Trend'] = sar_trend

# Random Walk Index
rwi_high, rwi_low = ta.rwi(df['high'], df['low'], df['close'])
df['RWI_High'] = rwi_high
df['RWI_Low'] = rwi_low

# Williams Fractals
fractal_up, fractal_down = ta.fractals(df['high'], df['low'])
df['Fractal_Up'] = fractal_up
df['Fractal_Down'] = fractal_down

# Create comprehensive trend signal
def comprehensive_trend_signal(row):
    signals = []
    
    # ADX Signal
    if row['ADX'] > 25:
        if row['DI_Plus'] > row['DI_Minus']:
            signals.append('ADX_Bull')
        else:
            signals.append('ADX_Bear')
    
    # Aroon Signal
    if row['Aroon_Up'] > 70:
        signals.append('Aroon_Bull')
    elif row['Aroon_Down'] > 70:
        signals.append('Aroon_Bear')
    
    # SAR Signal
    if row['close'] > row['SAR']:
        signals.append('SAR_Bull')
    else:
        signals.append('SAR_Bear')
    
    # RWI Signal
    if row['RWI_High'] > 1.0 and row['RWI_High'] > row['RWI_Low']:
        signals.append('RWI_Bull')
    elif row['RWI_Low'] > 1.0 and row['RWI_Low'] > row['RWI_High']:
        signals.append('RWI_Bear')
    
    # Count bullish vs bearish signals
    bull_count = len([s for s in signals if 'Bull' in s])
    bear_count = len([s for s in signals if 'Bear' in s])
    
    if bull_count > bear_count and bull_count >= 2:
        return f'Bullish ({bull_count}/{len(signals)})'
    elif bear_count > bull_count and bear_count >= 2:
        return f'Bearish ({bear_count}/{len(signals)})'
    else:
        return f'Neutral ({bull_count}B/{bear_count}B)'

df['Comprehensive_Signal'] = df.apply(comprehensive_trend_signal, axis=1)

# Calculate signal strength
df['Signal_Strength'] = df.apply(lambda row:
    row['ADX'] * 0.3 + abs(row['Aroon_Osc']) * 0.3 + 
    max(row['RWI_High'], row['RWI_Low']) * 40, axis=1)

# Display results
result_columns = ['close', 'ADX', 'Aroon_Osc', 'SAR', 'RWI_High', 'RWI_Low', 
                 'Comprehensive_Signal', 'Signal_Strength']

print("\nComprehensive Trend Analysis:")
print(df[result_columns].tail(10))

# Summary statistics
print(f"\nSignal Distribution:")
print(df['Comprehensive_Signal'].value_counts())

print(f"\nAverage Signal Strength: {df['Signal_Strength'].mean():.2f}")
print(f"Current Signal Strength: {df['Signal_Strength'].iloc[-1]:.2f}")
```

### Advanced Usage: Multi-Timeframe Analysis

```python
# Function to get multiple timeframe data
def get_multi_timeframe_data(symbol, exchange, start_date, end_date):
    timeframes = ['1m', '5m', '15m', '1h']
    data = {}
    
    for tf in timeframes:
        try:
            df = client.history(symbol=symbol, exchange=exchange, interval=tf,
                              start_date=start_date, end_date=end_date)
            data[tf] = df
        except Exception as e:
            print(f"Error fetching {tf} data: {e}")
    
    return data

# Multi-timeframe trend analysis
def analyze_multi_timeframe_trend(data_dict):
    results = {}
    
    for timeframe, df in data_dict.items():
        # Calculate key hybrid indicators
        di_plus, di_minus, adx = ta.adx(df['high'], df['low'], df['close'])
        aroon_up, aroon_down = ta.aroon(df['high'], df['low'])
        
        latest_adx = adx.iloc[-1] if not pd.isna(adx.iloc[-1]) else 0
        latest_di_plus = di_plus.iloc[-1] if not pd.isna(di_plus.iloc[-1]) else 0
        latest_di_minus = di_minus.iloc[-1] if not pd.isna(di_minus.iloc[-1]) else 0
        latest_aroon_up = aroon_up.iloc[-1] if not pd.isna(aroon_up.iloc[-1]) else 0
        latest_aroon_down = aroon_down.iloc[-1] if not pd.isna(aroon_down.iloc[-1]) else 0
        
        # Determine trend
        if latest_adx > 25:
            if latest_di_plus > latest_di_minus:
                trend = 'Bullish'
            else:
                trend = 'Bearish'
        else:
            trend = 'Sideways'
        
        results[timeframe] = {
            'Trend': trend,
            'ADX': latest_adx,
            'Aroon_Strength': abs(latest_aroon_up - latest_aroon_down)
        }
    
    return results

# Example usage
# mtf_data = get_multi_timeframe_data("SBIN", "NSE", "2025-04-01", "2025-04-08")
# mtf_analysis = analyze_multi_timeframe_trend(mtf_data)
# print("Multi-Timeframe Analysis:", mtf_analysis)
```

### Performance Tips

1. **Vectorized Operations**: Use pandas operations for better performance with large datasets
2. **Memory Optimization**: Calculate only needed indicators to reduce memory usage
3. **Caching**: Store intermediate calculations for reuse across multiple indicators
4. **Batch Processing**: Process multiple symbols together when possible

### Common Use Cases

1. **Trend Confirmation**: Use ADX with Aroon for trend strength validation
2. **Entry Timing**: Combine SAR with DMI for precise entry points
3. **Support/Resistance**: Use Pivot Points with Fractals for key levels
4. **Risk Management**: Use RWI to distinguish trending from random movements
5. **Multi-Timeframe**: Align signals across different timeframes for higher probability trades


---

# Agent Instructions: Querying This Documentation

If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.openalgo.in/trading-platform/python/indicators/hybrid.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

```


---

# FILE: docs\prompt\LotSize.md

```md
Symbol,Lot Size (Apr 2026),Lot Size (May 2026),Lot Size (Jun 2026)
BANKNIFTY,30,30,30
FINNIFTY,60,60,60
MIDCPNIFTY,120,120,120
NIFTY,65,65,65
NIFTYNXT50,25,25,25
360ONE,500,500,500
ABB,125,125,125
ABCAPITAL,3100,3100,3100
ADANIENSOL,675,675,675
ADANIENT,309,309,309
ADANIGREEN,600,600,600
ADANIPORTS,475,475,475
ADANIPOWER,3550,3550,3550
ALKEM,125,125,125
AMBER,100,100,100
AMBUJACEM,1050,1050,1050
ANGELONE,2500,2500,2500
APLAPOLLO,350,350,350
APOLLOHOSP,125,125,125
ASHOKLEY,5000,5000,5000
ASIANPAINT,250,250,250
ASTRAL,425,425,425
AUBANK,1000,1000,1000
AUROPHARMA,550,550,550
AXISBANK,625,625,625
BAJAJ-AUTO,75,75,75
BAJAJFINSV,250,250,250
BAJAJHLDNG,50,50,50
BAJFINANCE,750,750,750
BANDHANBNK,3600,3600,3600
BANKBARODA,2925,2925,2925
BANKINDIA,5200,5200,5200
BDL,350,350,350
BEL,1425,1425,1425
BHARATFORG,500,500,500
BHARTIARTL,475,475,475
BHEL,2625,2625,2625
BIOCON,2500,2500,2500
BLUESTARCO,325,325,325
BOSCHLTD,25,25,25
BPCL,1975,1975,1975
BRITANNIA,125,125,125
BSE,375,375,375
CAMS,750,750,750
CANBK,6750,6750,6750
CDSL,475,475,475
CGPOWER,850,850,850
CHOLAFIN,625,625,625
CIPLA,375,375,375
COALINDIA,1350,1350,1350
COCHINSHIP,400,400,400
COFORGE,375,375,375
COLPAL,225,225,225
CONCOR,1250,1250,1250
CROMPTON,1800,1800,1800
CUMMINSIND,200,200,200
DABUR,1250,1250,1250
DALBHARAT,325,325,325
DELHIVERY,2075,2075,2075
DIVISLAB,100,100,100
DIXON,50,50,50
DLF,825,825,825
DMART,150,150,150
DRREDDY,625,625,625
EICHERMOT,100,100,100
ETERNAL,2425,2425,2425
EXIDEIND,1800,1800,1800
FEDERALBNK,5000,5000,5000
FORCEMOT,25,25,25
FORTIS,775,775,775
GAIL,3150,3150,3150
GLENMARK,375,375,375
GMRAIRPORT,6975,6975,6975
GODFRYPHLP,275,275,275
GODREJCP,500,500,500
GODREJPROP,275,275,275
GRASIM,250,250,250
HAL,150,150,150
HAVELLS,500,500,500
HCLTECH,350,350,350
HDFCAMC,300,300,300
HDFCBANK,550,550,550
HDFCLIFE,1100,1100,1100
HEROMOTOCO,150,150,150
HINDALCO,700,700,700
HINDPETRO,2025,2025,2025
HINDUNILVR,300,300,300
HINDZINC,1225,1225,1225
HUDCO,2775,-,-
HYUNDAI,275,275,275
ICICIBANK,700,700,700
ICICIGI,325,325,325
ICICIPRULI,925,925,925
IDEA,71475,71475,71475
IDFCFIRSTB,9275,9275,9275
IEX,3750,3750,3750
INDHOTEL,1000,1000,1000
INDIANB,1000,1000,1000
INDIGO,150,150,150
INDUSINDBK,700,700,700
INDUSTOWER,1700,1700,1700
INFY,400,400,400
INOXWIND,3575,3575,3575
IOC,4875,4875,4875
IREDA,3450,3450,3450
IRFC,4250,4250,4250
ITC,1600,1600,1600
JINDALSTEL,625,625,625
JIOFIN,2350,2350,2350
JSWENERGY,1000,1000,1000
JSWSTEEL,675,675,675
JUBLFOOD,1250,1250,1250
KALYANKJIL,1175,1175,1175
KAYNES,100,100,100
KEI,175,175,175
KFINTECH,500,500,500
KOTAKBANK,2000,2000,2000
KPITTECH,425,425,425
LAURUSLABS,850,850,850
LICHSGFIN,1000,1000,1000
LICI,700,700,700
LODHA,450,450,450
LT,175,175,175
LTF,2250,2250,2250
LTM,150,150,150
LUPIN,425,425,425
M&M,200,200,200
MANAPPURAM,3000,3000,3000
MANKIND,225,225,225
MARICO,1200,1200,1200
MARUTI,50,50,50
MAXHEALTH,525,525,525
MAZDOCK,200,200,200
MCX,625,625,625
MFSL,400,400,400
MOTHERSON,6150,6150,6150
MOTILALOFS,775,775,775
MPHASIS,275,275,275
MUTHOOTFIN,275,275,275
NAM-INDIA,625,625,625
NATIONALUM,3750,3750,3750
NAUKRI,375,375,375
NBCC,6500,6500,6500
NESTLEIND,500,500,500
NHPC,6400,6400,6400
NMDC,6750,6750,6750
NTPC,1500,1500,1500
NUVAMA,500,500,500
NYKAA,3125,3125,3125
OBEROIRLTY,350,350,350
OFSS,75,75,75
OIL,1400,1400,1400
ONGC,2250,2250,2250
PAGEIND,15,15,15
PATANJALI,900,900,900
PAYTM,725,725,725
PERSISTENT,100,100,100
PETRONET,1900,1900,1900
PFC,1300,1300,1300
PGEL,950,950,950
PHOENIXLTD,350,350,350
PIDILITIND,500,500,500
PIIND,175,175,175
PNB,8000,8000,8000
PNBHOUSING,650,650,650
POLICYBZR,350,350,350
POLYCAB,125,125,125
POWERGRID,1900,1900,1900
POWERINDIA,50,50,50
PPLPHARMA,2625,-,-
PREMIERENE,575,575,575
PRESTIGE,450,450,450
RBLBANK,3175,3175,3175
RECLTD,1400,1400,1400
RELIANCE,500,500,500
RVNL,1525,1525,1525
SAIL,4700,4700,4700
SAMMAANCAP,4300,4300,4300
SBICARD,800,800,800
SBILIFE,375,375,375
SBIN,750,750,750
SHREECEM,25,25,25
SHRIRAMFIN,825,825,825
SIEMENS,175,175,175
SOLARINDS,50,50,50
SONACOMS,1225,1225,1225
SRF,200,200,200
SUNPHARMA,350,350,350
SUPREMEIND,175,175,175
SUZLON,9025,9025,9025
SWIGGY,1300,1300,1300
TATACONSUM,550,550,550
TATAELXSI,100,100,100
TATAPOWER,1450,1450,1450
TATASTEEL,5500,5500,5500
TATATECH,800,-,-
TCS,175,175,175
TECHM,600,600,600
TIINDIA,200,200,200
TITAN,175,175,175
TMPV,800,800,800
TORNTPHARM,250,250,250
TORNTPOWER,425,-,-
TRENT,100,100,100
TVSMOTOR,175,175,175
ULTRACEMCO,50,50,50
UNIONBANK,4425,4425,4425
UNITDSPR,400,400,400
UNOMINDA,550,550,550
UPL,1355,1355,1355
VBL,1125,1125,1125
VEDL,1150,1150,1150
VMM,4850,4850,4850
VOLTAS,375,375,375
WAAREEENER,175,175,175
WIPRO,3000,3000,3000
YESBANK,31100,31100,31100
ZYDUSLIFE,900,900,900

```


---

# FILE: docs\prompt\momentum - openalgo indicators.md

```md
# Momentum

Momentum indicators measure the speed and strength of price movements, helping identify overbought/oversold conditions and potential trend reversals.

### Import Statement

```python
from openalgo import ta
```

### Available Momentum Indicators

***

### Relative Strength Index (RSI)

RSI is a momentum oscillator that measures the speed and magnitude of price changes, oscillating between 0 and 100.

#### Usage

```python
rsi_result = ta.rsi(data, period=14)
```

#### Parameters

* **data** *(array-like)*: Price data (typically closing prices)
* **period** *(int, default=14)*: Number of periods for RSI calculation

#### Returns

* **array**: RSI values (range: 0 to 100) in the same format as input

#### Example

```python
from openalgo import api, ta

# Get market data
client = api(api_key='your_api_key_here', host='http://127.0.0.1:5000')
df = client.history(symbol="SBIN", exchange="NSE", interval="5m", 
                   start_date="2025-04-01", end_date="2025-04-08")

# Calculate RSI
df['RSI_14'] = ta.rsi(df['close'], 14)
df['RSI_21'] = ta.rsi(df['close'], 21)

print(df[['close', 'RSI_14', 'RSI_21']].tail())
```

***

### Moving Average Convergence Divergence (MACD)

MACD is a trend-following momentum indicator showing the relationship between two exponential moving averages.

#### Usage

```python
macd_line, signal_line, histogram = ta.macd(data, fast_period=12, slow_period=26, signal_period=9)
```

#### Parameters

* **data** *(array-like)*: Price data (typically closing prices)
* **fast\_period** *(int, default=12)*: Period for fast EMA
* **slow\_period** *(int, default=26)*: Period for slow EMA
* **signal\_period** *(int, default=9)*: Period for signal line EMA

#### Returns

* **tuple**: (macd\_line, signal\_line, histogram) arrays

#### Example

```python
# Calculate MACD
macd_line, signal_line, histogram = ta.macd(df['close'])

# Add to DataFrame
df['MACD'] = macd_line
df['MACD_Signal'] = signal_line
df['MACD_Histogram'] = histogram

# Custom parameters
macd_fast, signal_fast, hist_fast = ta.macd(df['close'], fast_period=8, slow_period=21, signal_period=5)

print(df[['close', 'MACD', 'MACD_Signal', 'MACD_Histogram']].tail())
```

***

### Stochastic Oscillator

The Stochastic Oscillator compares a security's closing price to its price range over a given time period.

#### Usage

```python
k_percent, d_percent = ta.stochastic(high, low, close, k_period=14, d_period=3)
```

#### Parameters

* **high** *(array-like)*: High prices
* **low** *(array-like)*: Low prices
* **close** *(array-like)*: Closing prices
* **k\_period** *(int, default=14)*: Period for %K calculation
* **d\_period** *(int, default=3)*: Period for %D calculation (SMA of %K)

#### Returns

* **tuple**: (k\_percent, d\_percent) arrays

#### Example

```python
# Calculate Stochastic Oscillator
stoch_k, stoch_d = ta.stochastic(df['high'], df['low'], df['close'])

# Add to DataFrame
df['Stoch_K'] = stoch_k
df['Stoch_D'] = stoch_d

# Custom parameters
stoch_k_fast, stoch_d_fast = ta.stochastic(df['high'], df['low'], df['close'], 
                                          k_period=5, d_period=3)

print(df[['close', 'Stoch_K', 'Stoch_D']].tail())
```

***

### Commodity Channel Index (CCI)

CCI measures the current price level relative to an average price level over a given period.

#### Usage

```python
cci_result = ta.cci(high, low, close, period=20)
```

#### Parameters

* **high** *(array-like)*: High prices
* **low** *(array-like)*: Low prices
* **close** *(array-like)*: Closing prices
* **period** *(int, default=20)*: Number of periods for CCI calculation

#### Returns

* **array**: CCI values in the same format as input

#### Example

```python
# Calculate CCI
df['CCI_20'] = ta.cci(df['high'], df['low'], df['close'], 20)
df['CCI_14'] = ta.cci(df['high'], df['low'], df['close'], 14)

print(df[['close', 'CCI_20', 'CCI_14']].tail())
```

***

### Williams %R

Williams %R is a momentum indicator that measures overbought and oversold levels on a scale from 0 to -100.

#### Usage

```python
williams_r = ta.williams_r(high, low, close, period=14)
```

#### Parameters

* **high** *(array-like)*: High prices
* **low** *(array-like)*: Low prices
* **close** *(array-like)*: Closing prices
* **period** *(int, default=14)*: Number of periods for Williams %R calculation

#### Returns

* **array**: Williams %R values (range: 0 to -100) in the same format as input

#### Example

```python
# Calculate Williams %R
df['Williams_R'] = ta.williams_r(df['high'], df['low'], df['close'])
df['Williams_R_21'] = ta.williams_r(df['high'], df['low'], df['close'], 21)

print(df[['close', 'Williams_R', 'Williams_R_21']].tail())
```

***

### Balance of Power (BOP)

Balance of Power measures the strength of buyers versus sellers by assessing the ability of each side to drive prices to an extreme level.

#### Usage

```python
bop_result = ta.bop(open_prices, high, low, close)
```

#### Parameters

* **open\_prices** *(array-like)*: Opening prices
* **high** *(array-like)*: High prices
* **low** *(array-like)*: Low prices
* **close** *(array-like)*: Closing prices

#### Returns

* **array**: BOP values in the same format as input

#### Example

```python
# Calculate Balance of Power
df['BOP'] = ta.bop(df['open'], df['high'], df['low'], df['close'])

print(df[['close', 'BOP']].tail())
```

***

### Elder Ray Index

Elder Ray Index consists of Bull Power and Bear Power, measuring the ability of bulls and bears to drive prices above or below an EMA.

#### Usage

```python
bull_power, bear_power = ta.elderray(high, low, close, period=13)
```

#### Parameters

* **high** *(array-like)*: High prices
* **low** *(array-like)*: Low prices
* **close** *(array-like)*: Closing prices
* **period** *(int, default=13)*: Period for EMA calculation

#### Returns

* **tuple**: (bull\_power, bear\_power) arrays

#### Example

```python
# Calculate Elder Ray Index
bull_power, bear_power = ta.elderray(df['high'], df['low'], df['close'])

# Add to DataFrame
df['Bull_Power'] = bull_power
df['Bear_Power'] = bear_power

print(df[['close', 'Bull_Power', 'Bear_Power']].tail())
```

***

### Fisher Transform

The Fisher Transform converts prices into a Gaussian normal distribution, making it easier to identify turning points.

#### Usage

```python
fisher, trigger = ta.fisher(high, low, length=9)
```

#### Parameters

* **high** *(array-like)*: High prices
* **low** *(array-like)*: Low prices
* **length** *(int, default=9)*: Length for highest/lowest calculation

#### Returns

* **tuple**: (fisher, trigger) arrays

#### Example

```python
# Calculate Fisher Transform
fisher, fisher_trigger = ta.fisher(df['high'], df['low'])

# Add to DataFrame
df['Fisher'] = fisher
df['Fisher_Trigger'] = fisher_trigger

# Custom length
fisher_14, trigger_14 = ta.fisher(df['high'], df['low'], length=14)

print(df[['close', 'Fisher', 'Fisher_Trigger']].tail())
```

***

### Connors RSI (CRSI)

Connors RSI is a composite momentum oscillator consisting of three components: RSI of price, RSI of updown streak, and percent rank of 1-period ROC.

#### Usage

```python
crsi_result = ta.crsi(data, lenrsi=3, lenupdown=2, lenroc=100)
```

#### Parameters

* **data** *(array-like)*: Price data (typically closing prices)
* **lenrsi** *(int, default=3)*: RSI Length (period for price RSI)
* **lenupdown** *(int, default=2)*: UpDown Length (period for streak RSI)
* **lenroc** *(int, default=100)*: ROC Length (period for ROC percent rank)

#### Returns

* **array**: Connors RSI values in the same format as input

#### Example

```python
# Calculate Connors RSI
df['CRSI'] = ta.crsi(df['close'])

# Custom parameters
df['CRSI_Custom'] = ta.crsi(df['close'], lenrsi=5, lenupdown=3, lenroc=50)

print(df[['close', 'CRSI', 'CRSI_Custom']].tail())
```

***

### Complete Example: Multiple Momentum Indicators

```python
from openalgo import api, ta
import pandas as pd

# Get market data
client = api(api_key='your_api_key_here', host='http://127.0.0.1:5000')
df = client.history(symbol="SBIN", exchange="NSE", interval="5m", 
                   start_date="2025-04-01", end_date="2025-04-08")

# Calculate momentum indicators
df['RSI'] = ta.rsi(df['close'], 14)

# MACD
macd_line, signal_line, histogram = ta.macd(df['close'])
df['MACD'] = macd_line
df['MACD_Signal'] = signal_line
df['MACD_Histogram'] = histogram

# Stochastic
stoch_k, stoch_d = ta.stochastic(df['high'], df['low'], df['close'])
df['Stoch_K'] = stoch_k
df['Stoch_D'] = stoch_d

# CCI
df['CCI'] = ta.cci(df['high'], df['low'], df['close'], 20)

# Williams %R
df['Williams_R'] = ta.williams_r(df['high'], df['low'], df['close'])

# Balance of Power
df['BOP'] = ta.bop(df['open'], df['high'], df['low'], df['close'])

# Elder Ray
bull_power, bear_power = ta.elderray(df['high'], df['low'], df['close'])
df['Bull_Power'] = bull_power
df['Bear_Power'] = bear_power

# Fisher Transform
fisher, fisher_trigger = ta.fisher(df['high'], df['low'])
df['Fisher'] = fisher
df['Fisher_Trigger'] = fisher_trigger

# Connors RSI
df['CRSI'] = ta.crsi(df['close'])

# Display results
momentum_cols = ['close', 'RSI', 'MACD', 'MACD_Signal', 'Stoch_K', 'Stoch_D', 
                'CCI', 'Williams_R', 'BOP', 'Bull_Power', 'Bear_Power', 
                'Fisher', 'CRSI']

print(df[momentum_cols].tail(10))

# Trading signals example
df['RSI_Oversold'] = df['RSI'] < 30
df['RSI_Overbought'] = df['RSI'] > 70
df['MACD_Bullish'] = df['MACD'] > df['MACD_Signal']
df['Stoch_Oversold'] = (df['Stoch_K'] < 20) & (df['Stoch_D'] < 20)

# Combine signals
df['Bullish_Signal'] = (df['RSI_Oversold']) & (df['MACD_Bullish']) & (df['Stoch_Oversold'])

print("\nBullish signals:")
print(df[df['Bullish_Signal']][['close', 'RSI', 'MACD', 'Stoch_K']].head())
```

### Signal Interpretation Guide

#### RSI

* **> 70**: Overbought (potential sell signal)
* **< 30**: Oversold (potential buy signal)
* **50**: Neutral momentum

#### MACD

* **MACD > Signal**: Bullish momentum
* **MACD < Signal**: Bearish momentum
* **Histogram > 0**: Increasing bullish momentum
* **Histogram < 0**: Increasing bearish momentum

#### Stochastic

* **%K > 80**: Overbought conditions
* **%K < 20**: Oversold conditions
* **%K crossing above %D**: Bullish signal
* **%K crossing below %D**: Bearish signal

#### CCI

* **> +100**: Strong uptrend
* **< -100**: Strong downtrend
* **-100 to +100**: Ranging market

#### Williams %R

* **> -20**: Overbought
* **< -80**: Oversold
* **Crossing -50**: Trend change signal

### Performance Tips

1. **Use appropriate periods**: Shorter periods for more sensitive signals, longer for smoother trends
2. **Combine indicators**: Use multiple momentum indicators to confirm signals
3. **Market context**: Consider overall market trend when interpreting momentum signals
4. **Divergences**: Look for divergences between price and momentum indicators


---

# Agent Instructions: Querying This Documentation

If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.openalgo.in/trading-platform/python/indicators/momentum.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

```


---

# FILE: docs\prompt\openalgo indicators - introduction.md

```md
# Indicators

## OpenAlgo Technical Indicators Library

OpenAlgo Technical Indicators is a high-performance Python library designed for comprehensive technical analysis with a focus on speed, accuracy, and ease of use. Built from the ground up with modern optimization techniques, it provides over 80 technical indicators across all major categories.

### Import Statement

```python
from openalgo import ta
```

### List of Supported Indicators

### Trend Indicators

* **SMA** - Simple Moving Average
* **EMA** - Exponential Moving Average
* **WMA** - Weighted Moving Average
* **DEMA** - Double Exponential Moving Average
* **TEMA** - Triple Exponential Moving Average
* **HMA** - Hull Moving Average
* **VWMA** - Volume Weighted Moving Average
* **ALMA** - Arnaud Legoux Moving Average
* **KAMA** - Kaufman's Adaptive Moving Average
* **ZLEMA** - Zero Lag Exponential Moving Average
* **T3** - T3 Moving Average
* **FRAMA** - Fractal Adaptive Moving Average
* **TRIMA** - Triangular Moving Average
* **McGinley** - McGinley Dynamic
* **VIDYA** - Variable Index Dynamic Average
* **Alligator** - Bill Williams Alligator
* **MovingAverageEnvelopes** - Moving Average Envelopes
* **Supertrend** - Supertrend Indicator
* **Ichimoku** - Ichimoku Cloud
* **ChandeKrollStop** - Chande Kroll Stop

### Momentum Indicators

* **RSI** - Relative Strength Index
* **MACD** - Moving Average Convergence Divergence
* **Stochastic** - Stochastic Oscillator
* **CCI** - Commodity Channel Index
* **WilliamsR** - Williams %R
* **BOP** - Balance of Power
* **ElderRay** - Elder Ray Index (Bull/Bear Power)
* **Fisher** - Fisher Transform
* **CRSI** - Connors RSI

### Volatility Indicators

* **ATR** - Average True Range
* **BollingerBands** - Bollinger Bands
* **Keltner** - Keltner Channel
* **Donchian** - Donchian Channel
* **Chaikin** - Chaikin Volatility
* **NATR** - Normalized Average True Range
* **RVI** - Relative Volatility Index (volatility version)
* **ULTOSC** - Ultimate Oscillator
* **TRANGE** - True Range
* **MASS** - Mass Index
* **BBPercent** - Bollinger Bands %B
* **BBWidth** - Bollinger Bandwidth
* **ChandelierExit** - Chandelier Exit
* **HistoricalVolatility** - Historical Volatility
* **UlcerIndex** - Ulcer Index
* **STARC** - STARC Bands

### Volume Indicators

* **OBV** - On Balance Volume
* **OBVSmoothed** - On Balance Volume with Smoothing
* **VWAP** - Volume Weighted Average Price
* **MFI** - Money Flow Index
* **ADL** - Accumulation/Distribution Line
* **CMF** - Chaikin Money Flow
* **EMV** - Ease of Movement
* **FI** - Elder Force Index
* **NVI** - Negative Volume Index
* **PVI** - Positive Volume Index
* **VOLOSC** - Volume Oscillator
* **VROC** - Volume Rate of Change
* **KlingerVolumeOscillator** - Klinger Volume Oscillator
* **PriceVolumeTrend** - Price Volume Trend
* **RVOL** - Relative Volume

### Oscillators

* **ROC** - Rate of Change
* **CMO** - Chande Momentum Oscillator
* **TRIX** - Triple Exponential Average
* **UO** - Ultimate Oscillator
* **AO** - Awesome Oscillator
* **AC** - Accelerator Oscillator
* **PPO** - Percentage Price Oscillator
* **PO** - Price Oscillator
* **DPO** - Detrended Price Oscillator
* **AROONOSC** - Aroon Oscillator
* **StochRSI** - Stochastic RSI
* **RVI** - Relative Vigor Index (oscillator version)
* **CHO** - Chaikin Oscillator
* **CHOP** - Choppiness Index
* **KST** - Know Sure Thing
* **TSI** - True Strength Index
* **VI** - Vortex Indicator
* **STC** - Schaff Trend Cycle
* **GatorOscillator** - Gator Oscillator
* **Coppock** - Coppock Curve

### Statistical Indicators

* **LINREG** - Linear Regression
* **LRSLOPE** - Linear Regression Slope
* **CORREL** - Pearson Correlation Coefficient
* **BETA** - Beta Coefficient
* **VAR** - Variance
* **TSF** - Time Series Forecast
* **MEDIAN** - Rolling Median
* **MedianBands** - Median with Bands
* **MODE** - Rolling Mode

### Hybrid Indicators

* **ADX** - Average Directional Index
* **Aroon** - Aroon Indicator
* **PivotPoints** - Pivot Points
* **SAR** - Parabolic SAR
* **DMI** - Directional Movement Index
* **WilliamsFractals** - Williams Fractals
* **RWI** - Random Walk Index

### Utility Functions

* **crossover** - Series crossover detection
* **crossunder** - Series crossunder detection
* **highest** - Highest value over period
* **lowest** - Lowest value over period
* **change** - Change in value
* **roc** - Rate of change
* **stdev** - Standard deviation
* **exrem** - Excess removal
* **flip** - Flip function
* **valuewhen** - Value when condition
* **rising** - Rising detection
* **falling** - Falling detection
* **cross** - Cross detection (both directions)

### Perfect For

* **Quantitative Analysts** building trading strategies
* **Financial Engineers** developing risk management systems
* **Algorithmic Traders** requiring fast, reliable technical analysis
* **Research Teams** conducting market analysis and backtesting
* **Financial Applications** needing embedded technical analysis capabilities

OpenAlgo Indicators bridges the gap between ease of use and performance, making sophisticated technical analysis accessible to both beginners and experts while maintaining the speed and accuracy demanded by professional trading systems.


---

# Agent Instructions: Querying This Documentation

If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.openalgo.in/trading-platform/python/indicators.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

```


---

# FILE: docs\prompt\openalgo python sdk.md

```md
# Python

To install the OpenAlgo Python library, use pip:

```bash
# Trading API only  
pip install openalgo 

# JIT-accelerated indicators                                                                 
pip install openalgo[indicators]  
```

### Get the OpenAlgo apikey

Make Sure that your OpenAlgo Application is running. Login to OpenAlgo Application with valid credentials and get the OpenAlgo apikey

For detailed function parameters refer to the [API Documentation](https://docs.openalgo.in/api-documentation/v1)

### Getting Started with OpenAlgo

First, import the `api` class from the OpenAlgo library and initialize it with your API key:

```python
from openalgo import api

# Replace 'your_api_key_here' with your actual API key
# Specify the host URL with your hosted domain or ngrok domain. 
# If running locally in windows then use the default host value. 
client = api(api_key='your_api_key_here', host='http://127.0.0.1:5000')

```

### Check OpenAlgo Version

```python
import openalgo 
openalgo.__version__
```

### Examples

Please refer to the documentation on [order constants](https://docs.openalgo.in/api-documentation/v1/order-constants), and consult the API reference for details on optional parameters

### PlaceOrder example

To place a new market order:

```python
response = client.placeorder(
    strategy="Python",
    symbol="NHPC",
    action="BUY",
    exchange="NSE",
    price_type="MARKET",
    product="MIS",
    quantity=1
)
print(response)

```

Place Market Order Response

```json
{'orderid': '250408000989443', 'status': 'success'}
```

To place a new limit order:

```python
response = client.placeorder(
    strategy="Python",
    symbol="YESBANK",
    action="BUY",
    exchange="NSE",
    price_type="LIMIT",
    product="MIS",
    quantity="1",
    price="16",
    trigger_price="0",
    disclosed_quantity ="0",
)
print(response)
```

Place Limit Order Response

```json
{'orderid': '250408001003813', 'status': 'success'}
```

### PlaceSmartOrder Example

To place a smart order considering the current position size:

```python
response = client.placesmartorder(
    strategy="Python",
    symbol="TATAMOTORS",
    action="SELL",
    exchange="NSE",
    price_type="MARKET",
    product="MIS",
    quantity=1,
    position_size=5
)
print(response)

```

Place Smart Market Order Response

```json
{'orderid': '250408000997543', 'status': 'success'}
```

### OptionsOrder Example

To place ATM options order

```python
response = client.optionsorder(
      strategy="python",
      underlying="NIFTY",
      exchange="NSE_INDEX",
      expiry_date="28OCT25",
      offset="ATM",
      option_type="CE",
      action="BUY",
      quantity=75,
      pricetype="MARKET",
      product="NRML",
      splitsize = 0
  )

print(response)
```

Place Options Order Response

```json
{
  "exchange": "NFO",
  "offset": "ATM",
  "option_type": "CE",
  "orderid": "25102800000006",
  "status": "success",
  "symbol": "NIFTY28OCT2525950CE",
  "underlying": "NIFTY28OCT25FUT",
  "underlying_ltp": 25966.05
}
```

To place ITM options order

```python
response = client.optionsorder(
      strategy="python",
      underlying="NIFTY",
      exchange="NSE_INDEX",
      expiry_date="28OCT25",
      offset="ITM4",
      option_type="PE",
      action="BUY",
      quantity=75,
      pricetype="MARKET",
      product="NRML",
      splitsize = 0
  )

print(response)
```

Place Options Order Response

```json
{
  "exchange": "NFO",
  "offset": "ITM4",
  "option_type": "PE",
  "orderid": "25102800000007",
  "status": "success",
  "symbol": "NIFTY28OCT2526150PE",
  "underlying": "NIFTY28OCT25FUT",
  "underlying_ltp": 25966.05
}
```

To place OTM options order

```python
response = client.optionsorder(
      strategy="python",
      underlying="NIFTY",
      exchange="NSE_INDEX",
      expiry_date="28OCT25",
      offset="OTM5",
      option_type="CE",
      action="BUY",
      quantity=75,
      pricetype="MARKET",
      product="NRML",
      splitsize = 0
  )

print(response)
```

Place Options Order Response

```json
{
  "exchange": "NFO",
  "mode": "analyze",
  "offset": "OTM5",
  "option_type": "CE",
  "orderid": "25102800000008",
  "status": "success",
  "symbol": "NIFTY28OCT2526200CE",
  "underlying": "NIFTY28OCT25FUT",
  "underlying_ltp": 25966.05
}
```

### OptionsMultiOrder Example

To place Iron options order (Same Expiry)

```python
response = client.optionsmultiorder(
    strategy="Iron Condor Test",
    underlying="NIFTY",
    exchange="NSE_INDEX",
    expiry_date="25NOV25",
    legs=[
        {"offset": "OTM6", "option_type": "CE", "action": "BUY", "quantity": 75},
        {"offset": "OTM6", "option_type": "PE", "action": "BUY", "quantity": 75},
        {"offset": "OTM4", "option_type": "CE", "action": "SELL", "quantity": 75},
        {"offset": "OTM4", "option_type": "PE", "action": "SELL", "quantity": 75}
    ]
)

print(response)
```

Place OptionsMultiOrder Response

```json
{
    'status': 'success',
    'underlying': 'NIFTY',
    'underlying_ltp': 26050.45,
    'results': [
        {
            'action': 'BUY',
            'leg': 1,
            'mode': 'analyze',
            'offset': 'OTM6',
            'option_type': 'CE',
            'orderid': '25111996859688',
            'status': 'success',
            'symbol': 'NIFTY25NOV2526350CE'
        },
        {
            'action': 'BUY',
            'leg': 2,
            'mode': 'analyze',
            'offset': 'OTM6',
            'option_type': 'PE',
            'orderid': '25111996042210',
            'status': 'success',
            'symbol': 'NIFTY25NOV2525750PE'
        },
        {
            'action': 'SELL',
            'leg': 3,
            'mode': 'analyze',
            'offset': 'OTM4',
            'option_type': 'CE',
            'orderid': '25111922189638',
            'status': 'success',
            'symbol': 'NIFTY25NOV2526250CE'
        },
        {
            'action': 'SELL',
            'leg': 4,
            'mode': 'analyze',
            'offset': 'OTM4',
            'option_type': 'PE',
            'orderid': '25111919252668',
            'status': 'success',
            'symbol': 'NIFTY25NOV2525850PE'
        }
    ]
}

```

To place Diagonal Spread options order (Different Expiry)

```python
response = client.optionsmultiorder(
      strategy="Diagonal Spread Test",
      underlying="NIFTY",
      exchange="NSE_INDEX",
      legs=[
          {"offset": "ITM2", "option_type": "CE", "action": "BUY", "quantity": 75, "expiry_date": "30DEC25"},
          {"offset": "OTM2", "option_type": "CE", "action": "SELL", "quantity": 75, "expiry_date": "25NOV25"}
      ]
  )

print(response)

```

Place OptionsMultiOrder Response

```json
{
    "results": [
        {
            "action": "BUY",
            "leg": 1,
            "mode": "analyze",
            "offset": "ITM2",
            "option_type": "CE",
            "orderid": "25111933337854",
            "status": "success",
            "symbol": "NIFTY30DEC2525950CE"
        },
        {
            "action": "SELL",
            "leg": 2,
            "mode": "analyze",
            "offset": "OTM2",
            "option_type": "CE",
            "orderid": "25111957475473",
            "status": "success",
            "symbol": "NIFTY25NOV2526150CE"
        }
    ],
    "status": "success",
    "underlying": "NIFTY",
    "underlying_ltp": 26052.65
}

```

### BasketOrder example

To place a new basket order:

```python
basket_orders = [
        {
            "symbol": "BHEL",
            "exchange": "NSE",
            "action": "BUY",
            "quantity": 1,
            "pricetype": "MARKET",
            "product": "MIS"
        },
        {
            "symbol": "ZOMATO",
            "exchange": "NSE",
            "action": "SELL",
            "quantity": 1,
            "pricetype": "MARKET",
            "product": "MIS"
        }
    ]
response = client.basketorder(orders=basket_orders)
print(response)
```

**Basket Order Response**

```json
{
  "status": "success",
  "results": [
    {
      "symbol": "BHEL",
      "status": "success",
      "orderid": "250408000999544"
    },
    {
      "symbol": "ZOMATO",
      "status": "success",
      "orderid": "250408000997545"
    }
  ]
}

```

### SplitOrder example

To place a new split order:

```python
response = client.splitorder(
    symbol="YESBANK",
    exchange="NSE",
    action="SELL",
    quantity=105,
    splitsize=20,
    price_type="MARKET",
    product="MIS"
    )
print(response)

```

**SplitOrder Response**

```json
{
  "status": "success",
  "split_size": 20,
  "total_quantity": 105,
  "results": [
    {
      "order_num": 1,
      "orderid": "250408001021467",
      "quantity": 20,
      "status": "success"
    },
    {
      "order_num": 2,
      "orderid": "250408001021459",
      "quantity": 20,
      "status": "success"
    },
    {
      "order_num": 3,
      "orderid": "250408001021466",
      "quantity": 20,
      "status": "success"
    },
    {
      "order_num": 4,
      "orderid": "250408001021470",
      "quantity": 20,
      "status": "success"
    },
    {
      "order_num": 5,
      "orderid": "250408001021471",
      "quantity": 20,
      "status": "success"
    },
    {
      "order_num": 6,
      "orderid": "250408001021472",
      "quantity": 5,
      "status": "success"
    }
  ]
}

```

### ModifyOrder Example

To modify an existing order:

```python
response = client.modifyorder(
    order_id="250408001002736",
    strategy="Python",
    symbol="YESBANK",
    action="BUY",
    exchange="NSE",
    price_type="LIMIT",
    product="CNC",
    quantity=1,
    price=16.5
)
print(response)
```

**Modify Order Response**

```json
{'orderid': '250408001002736', 'status': 'success'}
```

### CancelOrder Example

To cancel an existing order:

```python
response = client.cancelorder(
    order_id="250408001002736",
    strategy="Python"
)
print(response)
```

**Cancelorder Response**

```json
{'orderid': '250408001002736', 'status': 'success'}
```

### CancelAllOrder Example

To cancel all open orders and trigger pending orders

```python
response = client.cancelallorder(
    strategy="Python"
)
print(response)
```

**Cancelallorder Response**

```json
{
  "status": "success",
  "message": "Canceled 5 orders. Failed to cancel 0 orders.",
  "canceled_orders": [
    "250408001042620",
    "250408001042667",
    "250408001042642",
    "250408001043015",
    "250408001043386"
  ],
  "failed_cancellations": []
}

```

### ClosePosition Example

To close all open positions across various exchanges

```python
response = client.closeposition(
    strategy="Python"
)
print(response)
```

**ClosePosition Response**

```json
{'message': 'All Open Positions Squared Off', 'status': 'success'}
```

### OrderStatus Example

To Get the Current OrderStatus

```python
response = client.orderstatus(
    order_id="250828000185002",
    strategy="Test Strategy"
    )
print(response)
```

**Orderstatus Response**

```json
{
  "data": {
    "action": "BUY",
    "average_price": 18.95,
    "exchange": "NSE",
    "order_status": "complete",
    "orderid": "250828000185002",
    "price": 0,
    "pricetype": "MARKET",
    "product": "MIS",
    "quantity": "1",
    "symbol": "YESBANK",
    "timestamp": "28-Aug-2025 09:59:10",
    "trigger_price": 0
  },
  "status": "success"
}
```

### OpenPosition Example

To Get the Current OpenPosition

```python
response = client.openposition(
            strategy="Test Strategy",
            symbol="YESBANK",
            exchange="NSE",
            product="MIS"
        )
print(response)
```

OpenPosition Response

```json
{'quantity': '-10', 'status': 'success'}
```

### Quotes Example

```python
response = client.quotes(symbol="RELIANCE", exchange="NSE")
print(response)
```

**Quotes response**

```json
{
  "status": "success",
  "data": {
    "open": 1172.0,
    "high": 1196.6,
    "low": 1163.3,
    "ltp": 1187.75,
    "ask": 1188.0,
    "bid": 1187.85,
    "prev_close": 1165.7,
    "volume": 14414545
  }
}
```

### MultiQuotes Example

```python
response = client.multiquotes(symbols=[
    {"symbol": "RELIANCE", "exchange": "NSE"},
    {"symbol": "TCS", "exchange": "NSE"},
    {"symbol": "INFY", "exchange": "NSE"}
])

print(response)
```

**Quotes response**

```json
{
  "status": "success",
  "results": [
    {
      "symbol": "RELIANCE",
      "exchange": "NSE",
      "data": {
        "open": 1542.3,
        "high": 1571.6,
        "low": 1540.5,
        "ltp": 1569.9,
        "prev_close": 1539.7,
        "ask": 1569.9,
        "bid": 0,
        "oi": 0,
        "volume": 14054299
      }
    },
    {
      "symbol": "TCS",
      "exchange": "NSE",
      "data": {
        "open": 3118.8,
        "high": 3178,
        "low": 3117,
        "ltp": 3162.9,
        "prev_close": 3119.2,
        "ask": 0,
        "bid": 3162.9,
        "oi": 0,
        "volume": 2508527
      }
    },
    {
      "symbol": "INFY",
      "exchange": "NSE",
      "data": {
        "open": 1532.1,
        "high": 1560.3,
        "low": 1532.1,
        "ltp": 1557.9,
        "prev_close": 1530.6,
        "ask": 0,
        "bid": 1557.9,
        "oi": 0,
        "volume": 7575038
      }
    }
  ]
}

```

### Depth Example

```python
response = client.depth(symbol="SBIN", exchange="NSE")
print(response)
```

**Depth Response**

```json
{
  "status": "success",
  "data": {
    "open": 760.0,
    "high": 774.0,
    "low": 758.15,
    "ltp": 769.6,
    "ltq": 205,
    "prev_close": 746.9,
    "volume": 9362799,
    "oi": 161265750,
    "totalbuyqty": 591351,
    "totalsellqty": 835701,
    "asks": [
      {
        "price": 769.6,
        "quantity": 767
      },
      {
        "price": 769.65,
        "quantity": 115
      },
      {
        "price": 769.7,
        "quantity": 162
      },
      {
        "price": 769.75,
        "quantity": 1121
      },
      {
        "price": 769.8,
        "quantity": 430
      }
    ],
    "bids": [
      {
        "price": 769.4,
        "quantity": 886
      },
      {
        "price": 769.35,
        "quantity": 212
      },
      {
        "price": 769.3,
        "quantity": 351
      },
      {
        "price": 769.25,
        "quantity": 343
      },
      {
        "price": 769.2,
        "quantity": 399
      }
    ]
  }
}

```

### History Example

Download Data Directly from Broker API

```python
response = client.history(symbol="SBIN", 
    exchange="NSE", 
    interval="5m", 
    start_date="2025-04-01", 
    end_date="2025-04-08",
    source = "api"
    )
print(response)
```

Download Data Directly from Historify DuckDB (Stored Data)

```python
response = client.history(symbol="SBIN", 
    exchange="NSE", 
    interval="5m", 
    start_date="2025-04-01", 
    end_date="2025-04-08",
    source = "db"
    )
print(response)
```

**History Response**

```json
                            close    high     low    open  volume
timestamp                                                        
2025-04-01 09:15:00+05:30  772.50  774.00  763.20  766.50  318625
2025-04-01 09:20:00+05:30  773.20  774.95  772.10  772.45  197189
2025-04-01 09:25:00+05:30  775.15  775.60  772.60  773.20  227544
2025-04-01 09:30:00+05:30  777.35  777.50  774.85  775.15  134596
2025-04-01 09:35:00+05:30  778.00  778.00  776.25  777.50  145385
...                           ...     ...     ...     ...     ...
2025-04-08 14:00:00+05:30  768.25  770.70  767.85  768.50  142478
2025-04-08 14:05:00+05:30  769.10  769.80  766.60  768.15  128283
2025-04-08 14:10:00+05:30  769.05  769.85  768.40  769.10  119084
2025-04-08 14:15:00+05:30  770.05  770.50  769.05  769.05  158299
2025-04-08 14:20:00+05:30  769.95  770.50  769.40  770.05  125485

[437 rows x 5 columns]
```

### Intervals Example

```python
response = client.intervals()
print(response)
```

**Intervals response**

```json
{
  "status": "success",
  "data": {
    "months": [],
    "weeks": [],
    "days": ["D"],
    "hours": ["1h"],
    "minutes": ["10m", "15m", "1m", "30m", "3m", "5m"],
    "seconds": []
  }
}
```

### OptionChain Example

Note : To fetch entire option chain for a expiry remove the strike\_count (optional) parameter

```python
chain = client.optionchain(
    underlying="NIFTY",
    exchange="NSE_INDEX",
    expiry_date="30DEC25",
    strike_count=10
)
```

**Symbols Response**

```json
{
    "status": "success",
    "underlying": "NIFTY",
    "underlying_ltp": 26215.55,
    "expiry_date": "30DEC25",
    "atm_strike": 26200.0,
    "chain": [
        {
            "strike": 26100.0,
            "ce": {
                "symbol": "NIFTY30DEC2526100CE",
                "label": "ITM2",
                "ltp": 490,
                "bid": 490,
                "ask": 491,
                "open": 540,
                "high": 571,
                "low": 444.75,
                "prev_close": 496.8,
                "volume": 1195800,
                "oi": 0,
                "lotsize": 75,
                "tick_size": 0.05
            },
            "pe": {
                "symbol": "NIFTY30DEC2526100PE",
                "label": "OTM2",
                "ltp": 193,
                "bid": 191.2,
                "ask": 193,
                "open": 204.1,
                "high": 229.95,
                "low": 175.6,
                "prev_close": 215.95,
                "volume": 1832700,
                "oi": 0,
                "lotsize": 75,
                "tick_size": 0.05
            }
        },
        {
            "strike": 26150.0,
            "ce": {
                "symbol": "NIFTY30DEC2526150CE",
                "label": "ITM1",
                "ltp": 460.5,
                "bid": 452.9,
                "ask": 463,
                "open": 475.8,
                "high": 535.7,
                "low": 414.6,
                "prev_close": 461.05,
                "volume": 183525,
                "oi": 0,
                "lotsize": 75,
                "tick_size": 0.05
            },
            "pe": {
                "symbol": "NIFTY30DEC2526150PE",
                "label": "OTM1",
                "ltp": 208.5,
                "bid": 207.85,
                "ask": 210.1,
                "open": 218.2,
                "high": 248.8,
                "low": 190.75,
                "prev_close": 233.7,
                "volume": 332100,
                "oi": 0,
                "lotsize": 75,
                "tick_size": 0.05
            }
        },
        {
            "strike": 26200.0,
            "ce": {
                "symbol": "NIFTY30DEC2526200CE",
                "label": "ATM",
                "ltp": 427,
                "bid": 425.05,
                "ask": 427,
                "open": 449.95,
                "high": 503.5,
                "low": 384,
                "prev_close": 433.2,
                "volume": 2994000,
                "oi": 0,
                "lotsize": 75,
                "tick_size": 0.05
            },
            "pe": {
                "symbol": "NIFTY30DEC2526200PE",
                "label": "ATM",
                "ltp": 227.4,
                "bid": 227.35,
                "ask": 228.5,
                "open": 251.9,
                "high": 269.15,
                "low": 205.95,
                "prev_close": 251.9,
                "volume": 3745350,
                "oi": 0,
                "lotsize": 75,
                "tick_size": 0.05
            }
        },
        {
            "strike": 26250.0,
            "ce": {
                "symbol": "NIFTY30DEC2526250CE",
                "label": "OTM1",
                "ltp": 398,
                "bid": 395.4,
                "ask": 400.5,
                "open": 442.1,
                "high": 468.5,
                "low": 355.75,
                "prev_close": 401.9,
                "volume": 407100,
                "oi": 0,
                "lotsize": 75,
                "tick_size": 0.05
            },
            "pe": {
                "symbol": "NIFTY30DEC2526250PE",
                "label": "ITM1",
                "ltp": 243.85,
                "bid": 243.6,
                "ask": 246.15,
                "open": 264.25,
                "high": 288,
                "low": 222.15,
                "prev_close": 269.7,
                "volume": 487575,
                "oi": 0,
                "lotsize": 75,
                "tick_size": 0.05
            }
        },
        {
            "strike": 26300.0,
            "ce": {
                "symbol": "NIFTY30DEC2526300CE",
                "label": "OTM2",
                "ltp": 367.55,
                "bid": 364,
                "ask": 367.55,
                "open": 378,
                "high": 437.4,
                "low": 327.25,
                "prev_close": 371.45,
                "volume": 2416350,
                "oi": 0,
                "lotsize": 75,
                "tick_size": 0.05
            },
            "pe": {
                "symbol": "NIFTY30DEC2526300PE",
                "label": "ITM2",
                "ltp": 266,
                "bid": 264.2,
                "ask": 266.5,
                "open": 263.1,
                "high": 311.55,
                "low": 240,
                "prev_close": 289.85,
                "volume": 2891100,
                "oi": 0,
                "lotsize": 75,
                "tick_size": 0.05
            }
        }
    ]
}

```

### Symbol Example

```python
response = client.symbol(
            symbol="NIFTY30DEC25FUT",
            exchange="NFO"
            )
print(response)
```

**Symbols Response**

```json
{
  "data": {
    "brexchange": "NSE_FO",
    "brsymbol": "NIFTY FUT 30 DEC 25",
    "exchange": "NFO",
    "expiry": "30-DEC-25",
    "freeze_qty": 1800,
    "id": 57900,
    "instrumenttype": "FUT",
    "lotsize": 75,
    "name": "NIFTY",
    "strike": 0,
    "symbol": "NIFTY30DEC25FUT",
    "tick_size": 10,
    "token": "NSE_FO|49543"
  },
  "status": "success"
}
```

### Search Example

```python
response = client.search(query="NIFTY 26000 DEC CE",exchange="NFO")
print(response)
```

**Search Response**

```json
{
  "data": [
    {
      "brexchange": "NSE_FO",
      "brsymbol": "NIFTY 26000 CE 30 DEC 25",
      "exchange": "NFO",
      "expiry": "30-DEC-25",
      "freeze_qty": 1800,
      "instrumenttype": "CE",
      "lotsize": 75,
      "name": "NIFTY",
      "strike": 26000,
      "symbol": "NIFTY30DEC2526000CE",
      "tick_size": 5,
      "token": "NSE_FO|71399"
    },
    {
      "brexchange": "NSE_FO",
      "brsymbol": "NIFTY 26000 CE 29 DEC 26",
      "exchange": "NFO",
      "expiry": "29-DEC-26",
      "freeze_qty": 1800,
      "instrumenttype": "CE",
      "lotsize": 75,
      "name": "NIFTY",
      "strike": 26000,
      "symbol": "NIFTY29DEC2626000CE",
      "tick_size": 5,
      "token": "NSE_FO|71505"
    },
    {
      "brexchange": "NSE_FO",
      "brsymbol": "NIFTY 26000 CE 26 DEC 28",
      "exchange": "NFO",
      "expiry": "26-DEC-28",
      "freeze_qty": 1800,
      "instrumenttype": "CE",
      "lotsize": 75,
      "name": "NIFTY",
      "strike": 26000,
      "symbol": "NIFTY26DEC2826000CE",
      "tick_size": 5,
      "token": "NSE_FO|67786"
    },
    {
      "brexchange": "NSE_FO",
      "brsymbol": "NIFTY 26000 CE 28 DEC 27",
      "exchange": "NFO",
      "expiry": "28-DEC-27",
      "freeze_qty": 1800,
      "instrumenttype": "CE",
      "lotsize": 75,
      "name": "NIFTY",
      "strike": 26000,
      "symbol": "NIFTY28DEC2726000CE",
      "tick_size": 5,
      "token": "NSE_FO|53628"
    },
    {
      "brexchange": "NSE_FO",
      "brsymbol": "FINNIFTY 26000 CE 30 DEC 25",
      "exchange": "NFO",
      "expiry": "30-DEC-25",
      "freeze_qty": 1200,
      "instrumenttype": "CE",
      "lotsize": 65,
      "name": "FINNIFTY",
      "strike": 26000,
      "symbol": "FINNIFTY30DEC2526000CE",
      "tick_size": 5,
      "token": "NSE_FO|61709"
    },
    {
      "brexchange": "NSE_FO",
      "brsymbol": "NIFTY 26000 CE 24 DEC 29",
      "exchange": "NFO",
      "expiry": "24-DEC-29",
      "freeze_qty": 1800,
      "instrumenttype": "CE",
      "lotsize": 75,
      "name": "NIFTY",
      "strike": 26000,
      "symbol": "NIFTY24DEC2926000CE",
      "tick_size": 5,
      "token": "NSE_FO|61778"
    },
    {
      "brexchange": "NSE_FO",
      "brsymbol": "NIFTY 26000 CE 23 DEC 25",
      "exchange": "NFO",
      "expiry": "23-DEC-25",
      "freeze_qty": 1800,
      "instrumenttype": "CE",
      "lotsize": 75,
      "name": "NIFTY",
      "strike": 26000,
      "symbol": "NIFTY23DEC2526000CE",
      "tick_size": 5,
      "token": "NSE_FO|57005"
    }
  ],
  "message": "Found 7 matching symbols",
  "status": "success"
}
```

### OptionSymbol Example

ATM Option

```python
response = client.optionsymbol(
      underlying="NIFTY",
      exchange="NSE_INDEX",
      expiry_date="30DEC25",
      offset="ATM",
      option_type="CE"
  )

print(response)
```

**OptionSymbol Response**

```json
{
  "status": "success",
  "symbol": "NIFTY30DEC2525950CE",
  "exchange": "NFO",
  "lotsize": 75,
  "tick_size": 5,
  "freeze_qty": 1800,
  "underlying_ltp": 25966.4
}
```

ITM Option

```python
response = client.optionsymbol(
      underlying="NIFTY",
      exchange="NSE_INDEX",
      expiry_date="30DEC25",
      offset="ITM3",
      option_type="PE"
  )

print(response)
```

**OptionSymbol Response**

```json
{
  "status": "success",
  "symbol": "NIFTY30DEC2526100PE",
  "exchange": "NFO",
  "lotsize": 75,
  "tick_size": 5,
  "freeze_qty": 1800,
  "underlying_ltp": 25966.4
}
```

OTM Option

```python
response = client.optionsymbol(
      underlying="NIFTY",
      exchange="NSE_INDEX",
      expiry_date="30DEC25",
      offset="OTM4",
      option_type="CE"
  )

print(response)
```

**OptionSymbol Response**

```json
{
  "status": "success",
  "symbol": "NIFTY30DEC2526150CE",
  "exchange": "NFO",
  "lotsize": 75,
  "tick_size": 5,
  "freeze_qty": 1800,
  "underlying_ltp": 25966.4
}
```

### SyntheticFuture Example

```python
response = client.syntheticfuture(
      underlying="NIFTY",
      exchange="NSE_INDEX",
      expiry_date="25NOV25"
  )

print(response)
```

SyntheticFuture **Response**

```
{
 'atm_strike': 25900.0,
 'expiry': '25NOV25',
 'status': 'success',
 'synthetic_future_price': 25980.05,
 'underlying': 'NIFTY',
 'underlying_ltp': 25910.05
}
```

### OptionGreeks Example

```python
response = client.optiongreeks(
      symbol="NIFTY25NOV2526000CE",
      exchange="NFO",
      interest_rate=0.00,
      underlying_symbol="NIFTY",
      underlying_exchange="NSE_INDEX"
  )

print(response)
```

OptionGreeks  **Response**

```
{
'days_to_expiry': 28.5071,
 'exchange': 'NFO',
 'expiry_date': '25-Nov-2025',
 'greeks': {'delta': 0.4967,
  'gamma': 0.000352,
  'rho': 9.733994,
  'theta': -7.919,
  'vega': 28.9489},
 'implied_volatility': 15.6,
 'interest_rate': 0.0,
 'option_price': 435,
 'option_type': 'CE',
 'spot_price': 25966.05,
 'status': 'success',
 'strike': 26000.0,
 'symbol': 'NIFTY25NOV2526000CE',
 'underlying': 'NIFTY'
}
```

### Expiry Example

```python
response = client.expiry(
    symbol="NIFTY",
    exchange="NFO",
    instrumenttype="options"
)

response
```

**Expiry Response**

```
{'data': ['10-JUL-25',
  '17-JUL-25',
  '24-JUL-25',
  '31-JUL-25',
  '07-AUG-25',
  '28-AUG-25',
  '25-SEP-25',
  '24-DEC-25',
  '26-MAR-26',
  '25-JUN-26',
  '31-DEC-26',
  '24-JUN-27',
  '30-DEC-27',
  '29-JUN-28',
  '28-DEC-28',
  '28-JUN-29',
  '27-DEC-29',
  '25-JUN-30'],
 'message': 'Found 18 expiry dates for NIFTY options in NFO',
 'status': 'success'}
```

### Instruments Example

```python
response = client.instruments(exchange="NSE")

print(response.tail())
```

Instruments **Response**

```json
     brexchange           brsymbol exchange expiry instrumenttype  lotsize  \
3041        NSE      NSE:NEOGEN-EQ      NSE   None             EQ        1   
3042        NSE     NSE:ALANKIT-EQ      NSE   None             EQ        1   
3043        NSE  NSE:EVERESTIND-EQ      NSE   None             EQ        1   
3044        NSE   NSE:VIKASLIFE-EQ      NSE   None             EQ        1   
3045        NSE    NSE:ONEPOINT-EQ      NSE   None             EQ        1   

                          name  strike      symbol  tick_size           token  
3041  NEOGEN CHEMICALS LIMITED    -1.0      NEOGEN       0.10  10100000009917  
3042           ALANKIT LIMITED    -1.0     ALANKIT       0.01  10100000009921  
3043    EVEREST INDUSTRIES LTD    -1.0  EVERESTIND       0.05   1010000000993  
3044    VIKAS LIFECARE LIMITED    -1.0   VIKASLIFE       0.01  10100000009931  
3045     ONE POINT ONE SOL LTD    -1.0    ONEPOINT       0.01  10100000009939  
```

### Telegram Alert Example

```python
response = client.telegram(
      username="<openalgo_loginid>",
      message="NIFTY crossed 26000!"
  )

print(response)
```

**Telegram Alert Response**

```json
{
  "message": "Notification sent successfully",
  "status": "success"
}
```

### WhatsApp Alert Example

Prerequisites: open `/whatsapp` in the OpenAlgo web UI, click **Pair**, scan the QR with your phone. Pairing is admin-only on purpose — the REST API exposes only the send endpoint so a leaked API key cannot re-pair the device. Once paired, the bot auto-reconnects on every server boot from the encrypted session blob stored in `openalgo.db`.

One unified call handles every common case — text, image, document, self-send, single recipient, or small broadcast (max 5).

#### Send to yourself (simplest case)

```python
response = client.whatsapp("NIFTY crossed 26000!")
print(response)
```

**WhatsApp Alert Response (`wait_for_delivery=True`, the default):**

```json
{
  "status": "success",
  "message": "Delivered to 1, failed 0",
  "data": {
    "sent":    ["<self>"],
    "failed":  [],
    "skipped": 0
  }
}
```

#### Send to a single phone number

```python
response = client.whatsapp(
    "Order placed: BUY RELIANCE x 10 @ MARKET",
    to="919876543210",
)
```

#### Small broadcast (up to 5 recipients)

```python
response = client.whatsapp(
    "Server maintenance starting in 10 minutes",
    to=["919876543210", "919812345678", "919900112233"],
)
```

#### Send an image with caption

The path is read from the OpenAlgo server's filesystem. It must lie under `WHATSAPP_ATTACHMENT_ROOTS` (defaults to `<openalgo>/db/attachments/`).

```python
response = client.whatsapp(
    to="919876543210",
    image="/srv/charts/nifty_eod.png",
    caption="NIFTY end-of-day chart",
)
```

#### Send a document (PDF, CSV, ...)

```python
response = client.whatsapp(
    "Daily P&L report attached.",
    to="919876543210",
    document="/srv/reports/2026-05-17.pdf",
    filename="DailyPnL.pdf",
)
```

#### Fire-and-forget (skip the delivery report)

```python
response = client.whatsapp(
    "Stop-loss hit on BANKNIFTY!",
    wait_for_delivery=False,
)
```

#### Send to a linked OpenAlgo user (legacy multi-recipient path)

```python
response = client.whatsapp(
    "Position update: BANKNIFTY 48000 CE now at +21% P&L.",
    username="alice",
)
```

#### Receiving messages (bot commands)

Type slash-commands from your own phone in the **"Message yourself"** chat — the OpenAlgo linked device sees those as `is_from_me=True` and responds in the same chat. Random contacts who message your number cannot drive the bot.

```
/help                   List all commands
/status                 Bot connection + paired status
/orderbook              Today's orders
/tradebook              Today's trades
/positions              Open positions
/holdings               Holdings
/funds                  Available cash / margin
/pnl                    Net P&L
/quote RELIANCE NSE     Last traded price
/closeall               Square off all positions
/mode                   Live or analyze mode
```

### Funds Example

```python
response = client.funds()
print(response)
```

**Funds Response**

```json
{
  "status": "success",
  "data": {
    "availablecash": "320.66",
    "collateral": "0.00",
    "m2mrealized": "3.27",
    "m2munrealized": "-7.88",
    "utiliseddebits": "679.34"
  }
}

```

### Margin Example

```python
response = client.margin(positions=[
      {
          "symbol": "NIFTY25NOV2525000CE",
          "exchange": "NFO",
          "action": "BUY",
          "product": "NRML",
          "pricetype": "MARKET",
          "quantity": "75"
      },
      {
          "symbol": "NIFTY25NOV2525500CE",
          "exchange": "NFO",
          "action": "SELL",
          "product": "NRML",
          "pricetype": "MARKET",
          "quantity": "75"
      }
  ])
```

**Margin Response**

```json
{
    "status": "success",
    "data": {
      "total_margin_required": 91555.7625,
      "span_margin": 0.0,
      "exposure_margin": 91555.7625
    }
}
```

### OrderBook Example

```python
response = client.orderbook()
print(response)
```

```json
{
  "status": "success",
  "data": {
    "orders": [
      {
        "action": "BUY",
        "symbol": "RELIANCE",
        "exchange": "NSE",
        "orderid": "250408000989443",
        "product": "MIS",
        "quantity": "1",
        "price": 1186.0,
        "pricetype": "MARKET",
        "order_status": "complete",
        "trigger_price": 0.0,
        "timestamp": "08-Apr-2025 13:58:03"
      },
      {
        "action": "BUY",
        "symbol": "YESBANK",
        "exchange": "NSE",
        "orderid": "250408001002736",
        "product": "MIS",
        "quantity": "1",
        "price": 16.5,
        "pricetype": "LIMIT",
        "order_status": "cancelled",
        "trigger_price": 0.0,
        "timestamp": "08-Apr-2025 14:13:45"
      }
    ],
    "statistics": {
      "total_buy_orders": 2.0,
      "total_sell_orders": 0.0,
      "total_completed_orders": 1.0,
      "total_open_orders": 0.0,
      "total_rejected_orders": 0.0
    }
  }
}

```

### TradeBook Example

```python
response = client.tradebook()
print(response)
```

TradeBook Response

```python
{
  "status": "success",
  "data": [
    {
      "action": "BUY",
      "symbol": "RELIANCE",
      "exchange": "NSE",
      "orderid": "250408000989443",
      "product": "MIS",
      "quantity": 0.0,
      "average_price": 1180.1,
      "timestamp": "13:58:03",
      "trade_value": 1180.1
    },
    {
      "action": "SELL",
      "symbol": "NHPC",
      "exchange": "NSE",
      "orderid": "250408001086129",
      "product": "MIS",
      "quantity": 0.0,
      "average_price": 83.74,
      "timestamp": "14:28:49",
      "trade_value": 83.74
    }
  ]
}

```

### PositionBook Example

```python
response = client.positionbook()
print(response)
```

**PositionBook Response**

```json
{
  "status": "success",
  "data": [
    {
      "symbol": "NHPC",
      "exchange": "NSE",
      "product": "MIS",
      "quantity": "-1",
      "average_price": "83.74",
      "ltp": "83.72",
      "pnl": "0.02"
    },
    {
      "symbol": "RELIANCE",
      "exchange": "NSE",
      "product": "MIS",
      "quantity": "0",
      "average_price": "0.0",
      "ltp": "1189.9",
      "pnl": "5.90"
    },
    {
      "symbol": "YESBANK",
      "exchange": "NSE",
      "product": "MIS",
      "quantity": "-104",
      "average_price": "17.2",
      "ltp": "17.31",
      "pnl": "-10.44"
    }
  ]
}

```

### Holdings Example

```python
response = client.holdings()
print(response)
```

Holdings Response

```json
{
  "status": "success",
  "data": {
    "holdings": [
      {
        "symbol": "RELIANCE",
        "exchange": "NSE",
        "product": "CNC",
        "quantity": 1,
        "pnl": -149.0,
        "pnlpercent": -11.1
      },
      {
        "symbol": "TATASTEEL",
        "exchange": "NSE",
        "product": "CNC",
        "quantity": 1,
        "pnl": -15.0,
        "pnlpercent": -10.41
      },
      {
        "symbol": "CANBK",
        "exchange": "NSE",
        "product": "CNC",
        "quantity": 5,
        "pnl": -69.0,
        "pnlpercent": -13.43
      }
    ],
    "statistics": {
      "totalholdingvalue": 1768.0,
      "totalinvvalue": 2001.0,
      "totalprofitandloss": -233.15,
      "totalpnlpercentage": -11.65
    }
  }
}

```

### Holidays Example

```python
response = client.holidays(year=2026)
print(response)
```

#### Holidays Response

```json
{'data': [
    {'closed_exchanges': ['NSE', 'BSE', 'NFO', 'BFO', 'CDS', 'BCD', 'MCX'
      ], 'date': '2026-01-26', 'description': 'Republic Day', 'holiday_type': 'TRADING_HOLIDAY', 'open_exchanges': []
    },
    {'closed_exchanges': [], 'date': '2026-02-19', 'description': 'Chhatrapati Shivaji Maharaj Jayanti', 'holiday_type': 'SETTLEMENT_HOLIDAY', 'open_exchanges': []
    },
    {'closed_exchanges': ['NSE', 'BSE', 'NFO', 'BFO', 'CDS', 'BCD'
      ], 'date': '2026-03-10', 'description': 'Holi', 'holiday_type': 'TRADING_HOLIDAY', 'open_exchanges': [
        {'end_time': 1741677900000, 'exchange': 'MCX', 'start_time': 1741624200000
        }
      ]
    },
    {'closed_exchanges': ['NSE', 'BSE', 'NFO', 'BFO', 'CDS', 'BCD'
      ], 'date': '2026-03-20', 'description': 'Id-Ul-Fitr (Ramadan)', 'holiday_type': 'TRADING_HOLIDAY', 'open_exchanges': [
        {'end_time': 1742541900000, 'exchange': 'MCX', 'start_time': 1742488200000
        }
      ]
    },
    {'closed_exchanges': ['NSE', 'BSE', 'NFO', 'BFO', 'CDS', 'BCD'
      ], 'date': '2026-03-25', 'description': 'Holi (Dhuleti)', 'holiday_type': 'TRADING_HOLIDAY', 'open_exchanges': [
        {'end_time': 1742973900000, 'exchange': 'MCX', 'start_time': 1742920200000
        }
      ]
    }
```

### Timings Example

```python
response = client.timings(date="2025-12-19")
print(response)
```

#### Timings Response

```json
{'data': [
    {'end_time': 1766138400000, 'exchange': 'NSE', 'start_time': 1766115900000
    },
    {'end_time': 1766138400000, 'exchange': 'BSE', 'start_time': 1766115900000
    },
    {'end_time': 1766138400000, 'exchange': 'NFO', 'start_time': 1766115900000
    },
    {'end_time': 1766138400000, 'exchange': 'BFO', 'start_time': 1766115900000
    },
    {'end_time': 1766168700000, 'exchange': 'MCX', 'start_time': 1766115000000
    },
    {'end_time': 1766143800000, 'exchange': 'BCD', 'start_time': 1766115000000
    },
    {'end_time': 1766143800000, 'exchange': 'CDS', 'start_time': 1766115000000
    }
  ], 'status': 'success'
}
```

### Analyzer Status Example

```python
response  = client.analyzerstatus()
print(response)
```

Analyzer Status Response

```json
{'data': {'analyze_mode': True, 'mode': 'analyze', 'total_logs': 2},
 'status': 'success'}
```

### Analyzer Toggle Example

```python
# Switch to analyze mode (simulated responses)
response = client.analyzertoggle(mode=True)
print(response)
```

Analyzer Toggle Response

```
{'data': {'analyze_mode': True,
  'message': 'Analyzer mode switched to analyze',
  'mode': 'analyze',
  'total_logs': 2},
 'status': 'success'}
```

### LTP Data (Streaming Websocket)

```python
from openalgo import api
import time

# Initialize OpenAlgo client
client = api(
    api_key="your_api_key",                  # Replace with your actual OpenAlgo API key
    host="http://127.0.0.1:5000",            # REST API host
    ws_url="ws://127.0.0.1:8765"             # WebSocket host
)

# Define instruments to subscribe for LTP
instruments = [
    {"exchange": "NSE", "symbol": "RELIANCE"},
    {"exchange": "NSE", "symbol": "INFY"}
]

# Callback function for LTP updates
def on_ltp(data):
    print("LTP Update Received:")
    print(data)

# Connect and subscribe
client.connect()
client.subscribe_ltp(instruments, on_data_received=on_ltp)

# Run for a few seconds to receive data
try:
    time.sleep(10)
finally:
    client.unsubscribe_ltp(instruments)
    client.disconnect()

```

### Quotes (Streaming Websocket)

```python
from openalgo import api
import time

# Initialize OpenAlgo client
client = api(
    api_key="your_api_key",                  # Replace with your actual OpenAlgo API key
    host="http://127.0.0.1:5000",            # REST API host
    ws_url="ws://127.0.0.1:8765"             # WebSocket host
)

# Instruments list
instruments = [
    {"exchange": "NSE", "symbol": "RELIANCE"},
    {"exchange": "NSE", "symbol": "INFY"}
]

# Callback for Quote updates
def on_quote(data):
    print("Quote Update Received:")
    print(data)

# Connect and subscribe to quote stream
client.connect()
client.subscribe_quote(instruments, on_data_received=on_quote)

# Keep the script running to receive data
try:
    time.sleep(10)
finally:
    client.unsubscribe_quote(instruments)
    client.disconnect()

```

### Depth (Streaming Websocket)

```python
from openalgo import api
import time

# Initialize OpenAlgo client
client = api(
    api_key="your_api_key",                  # Replace with your actual OpenAlgo API key
    host="http://127.0.0.1:5000",            # REST API host
    ws_url="ws://127.0.0.1:8765"             # WebSocket host
)

# Instruments list for depth
instruments = [
    {"exchange": "NSE", "symbol": "RELIANCE"},
    {"exchange": "NSE", "symbol": "INFY"}
]

# Callback for market depth updates
def on_depth(data):
    print("Market Depth Update Received:")
    print(data)

# Connect and subscribe to depth stream
client.connect()
client.subscribe_depth(instruments, on_data_received=on_depth)

# Run for a few seconds to collect data
try:
    time.sleep(10)
finally:
    client.unsubscribe_depth(instruments)
    client.disconnect()

```


---

# Agent Instructions: Querying This Documentation

If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.openalgo.in/trading-platform/python.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

```


---

# FILE: docs\prompt\order-constants.md

```md
# Order Constants

## Order Constants

### Exchange

* NSE: NSE Equity
* NFO: NSE Futures & Options
* CDS: NSE Currency
* BSE: BSE Equity
* BFO: BSE Futures & Options
* BCD: BSE Currency
* MCX: MCX Commodity
* NCDEX: NCDEX Commodity
* NCO: NSE Commodities (futures + options) — Zerodha only
* NSE_INDEX: NSE Index (quote-only)
* BSE_INDEX: BSE Index (quote-only)
* GLOBAL_INDEX: Global indices like US30, JAPAN225, HANGSENG, GIFTNIFTY (quote-only) — Zerodha only

### Product Type

* CNC: Cash & Carry for equity
* NRML: Normal for futures and options
* MIS: Intraday Square off

### Price Type

* MARKET: Market Order
* LIMIT: Limit Order
* SL: Stop Loss Limit Order
* SL-M: Stop Loss Market Order

### Action

* BUY: Buy
* SELL: Sell
```


---

# FILE: docs\prompt\services_documentation.md

```md
# OpenAlgo Services Documentation

## Overview

OpenAlgo Services are Python functions that provide programmatic access to trading operations. These services mirror the functionality of the OpenAlgo SDK but are designed for internal use within the OpenAlgo application. Each service function accepts the same request parameters and returns the same responses as documented in the OpenAlgo SDK.

## Table of Contents

1. [Order Management Services](#order-management-services)
   - [PlaceOrder](#placeorder)
   - [PlaceSmartOrder](#placesmartorder)
   - [OptionsOrder](#optionsorder)
   - [OptionsMultiOrder](#optionsmultiorder)
   - [BasketOrder](#basketorder)
   - [SplitOrder](#splitorder)
   - [ModifyOrder](#modifyorder)
   - [CancelOrder](#cancelorder)
   - [CancelAllOrder](#cancelallorder)
   - [ClosePosition](#closeposition)
2. [Order Information Services](#order-information-services)
   - [OrderStatus](#orderstatus)
   - [OpenPosition](#openposition)
3. [Market Data Services](#market-data-services)
   - [Quotes](#quotes)
   - [MultiQuotes](#multiquotes)
   - [Depth](#depth)
   - [History](#history)
   - [Intervals](#intervals)
4. [Symbol Services](#symbol-services)
   - [Symbol](#symbol)
   - [Search](#search)
   - [Expiry](#expiry)
   - [Instruments](#instruments)
5. [Options Services](#options-services)
   - [OptionSymbol](#optionsymbol)
   - [OptionChain](#optionchain)
   - [SyntheticFuture](#syntheticfuture)
   - [OptionGreeks](#optiongreeks)
6. [Account Services](#account-services)
   - [Funds](#funds)
   - [Margin](#margin)
   - [OrderBook](#orderbook)
   - [TradeBook](#tradebook)
   - [PositionBook](#positionbook)
   - [Holdings](#holdings)
7. [Market Calendar Services](#market-calendar-services)
   - [Holidays](#holidays)
   - [Timings](#timings)
   - [CheckHoliday](#checkholiday)
8. [Analyzer Services](#analyzer-services)
   - [AnalyzerStatus](#analyzerstatus)
   - [AnalyzerToggle](#analyzertoggle)
9. [Telegram Service](#telegram-service)
   - [TelegramAlertService](#telegramalertservice)

---

## Order Management Services

### PlaceOrder

Place a new order with the broker.

**Function:** `place_order(order_data, api_key=None, auth_token=None, broker=None)`

**Location:** `openalgo/services/place_order_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| order_data | dict | Yes | Order details |
| api_key | str | Conditional | OpenAlgo API key (for API-based calls) |
| auth_token | str | Conditional | Direct broker authentication token (for internal calls) |
| broker | str | Conditional | Broker name (for internal calls) |

**Order Data Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| strategy | str | Yes | Strategy identifier |
| symbol | str | Yes | Trading symbol |
| action | str | Yes | BUY or SELL |
| exchange | str | Yes | Exchange (NSE, NFO, etc.) |
| pricetype | str | Yes | MARKET, LIMIT, SL, SL-M |
| product | str | Yes | MIS, CNC, NRML |
| quantity | int/str | Yes | Order quantity |
| price | float/str | No | Order price (for LIMIT orders) |
| trigger_price | float/str | No | Trigger price (for SL orders) |
| disclosed_quantity | int/str | No | Disclosed quantity |

**Example - Market Order:**

```python
from services.place_order_service import place_order

order_data = {
    "strategy": "Python",
    "symbol": "NHPC",
    "action": "BUY",
    "exchange": "NSE",
    "pricetype": "MARKET",
    "product": "MIS",
    "quantity": 1
}

success, response, status_code = place_order(
    order_data=order_data,
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "orderid": "250408000989443",
  "status": "success"
}
```

**Example - Limit Order:**

```python
from services.place_order_service import place_order

order_data = {
    "strategy": "Python",
    "symbol": "YESBANK",
    "action": "BUY",
    "exchange": "NSE",
    "pricetype": "LIMIT",
    "product": "MIS",
    "quantity": "1",
    "price": "16",
    "trigger_price": "0",
    "disclosed_quantity": "0"
}

success, response, status_code = place_order(
    order_data=order_data,
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "orderid": "250408001003813",
  "status": "success"
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Response data with orderid and status
- `status_code` (int): HTTP status code

---

### PlaceSmartOrder

Place a smart order that considers current position size.

**Function:** `place_smart_order(order_data, api_key=None, auth_token=None, broker=None, smart_order_delay=None)`

**Location:** `openalgo/services/place_smart_order_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| order_data | dict | Yes | Smart order details |
| api_key | str | Conditional | OpenAlgo API key |
| auth_token | str | Conditional | Direct broker authentication token |
| broker | str | Conditional | Broker name |
| smart_order_delay | str | No | Delay in seconds (default: 0.5) |

**Order Data Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| strategy | str | Yes | Strategy identifier |
| symbol | str | Yes | Trading symbol |
| action | str | Yes | BUY or SELL |
| exchange | str | Yes | Exchange (NSE, NFO, etc.) |
| pricetype | str | Yes | MARKET, LIMIT, SL, SL-M |
| product | str | Yes | MIS, CNC, NRML |
| quantity | int/str | Yes | Order quantity |
| position_size | int | Yes | Target position size |
| price | float/str | No | Order price (for LIMIT orders) |

**Example:**

```python
from services.place_smart_order_service import place_smart_order

order_data = {
    "strategy": "Python",
    "symbol": "TATAMOTORS",
    "action": "SELL",
    "exchange": "NSE",
    "pricetype": "MARKET",
    "product": "MIS",
    "quantity": 1,
    "position_size": 5
}

success, response, status_code = place_smart_order(
    order_data=order_data,
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "orderid": "250408000997543",
  "status": "success"
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Response data
- `status_code` (int): HTTP status code

---

### OptionsOrder

Place an options order by resolving the symbol from offset (ATM/ITM/OTM) and placing the order.

**Function:** `place_options_order(options_data, api_key=None, auth_token=None, broker=None)`

**Location:** `openalgo/services/place_options_order_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| options_data | dict | Yes | Options order details |
| api_key | str | Conditional | OpenAlgo API key (for API-based calls) |
| auth_token | str | Conditional | Direct broker authentication token (for internal calls) |
| broker | str | Conditional | Broker name (for internal calls) |

**Options Data Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| underlying | str | Yes | Underlying symbol (e.g., NIFTY, BANKNIFTY) |
| exchange | str | Yes | Exchange (NSE_INDEX, BSE_INDEX, NFO, BFO) |
| expiry_date | str | Yes | Expiry date in DDMMMYY format (e.g., 28OCT25) |
| offset | str | Yes | Strike offset (ATM, ITM1-ITM50, OTM1-OTM50) |
| option_type | str | Yes | CE or PE |
| action | str | Yes | BUY or SELL |
| quantity | int | Yes | Order quantity |
| pricetype | str | Yes | MARKET, LIMIT, SL, SL-M |
| product | str | Yes | MIS or NRML |
| strategy | str | No | Strategy identifier |
| splitsize | int | No | Split large orders (0 = no split) |
| price | float | No | Limit price (for LIMIT orders) |
| trigger_price | float | No | Trigger price (for SL orders) |

**Example - ATM Options Order:**

```python
from services.place_options_order_service import place_options_order

options_data = {
    "strategy": "python",
    "underlying": "NIFTY",
    "exchange": "NSE_INDEX",
    "expiry_date": "28OCT25",
    "offset": "ATM",
    "option_type": "CE",
    "action": "BUY",
    "quantity": 75,
    "pricetype": "MARKET",
    "product": "NRML",
    "splitsize": 0
}

success, response, status_code = place_options_order(
    options_data=options_data,
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "exchange": "NFO",
  "offset": "ATM",
  "option_type": "CE",
  "orderid": "25102800000006",
  "status": "success",
  "symbol": "NIFTY28OCT2525950CE",
  "underlying": "NIFTY28OCT25FUT",
  "underlying_ltp": 25966.05
}
```

**Example - ITM Options Order:**

```python
options_data = {
    "strategy": "python",
    "underlying": "NIFTY",
    "exchange": "NSE_INDEX",
    "expiry_date": "28OCT25",
    "offset": "ITM4",
    "option_type": "PE",
    "action": "BUY",
    "quantity": 75,
    "pricetype": "MARKET",
    "product": "NRML",
    "splitsize": 0
}

success, response, status_code = place_options_order(
    options_data=options_data,
    api_key='your_api_key_here'
)
```

**Response:**

```json
{
  "exchange": "NFO",
  "offset": "ITM4",
  "option_type": "PE",
  "orderid": "25102800000007",
  "status": "success",
  "symbol": "NIFTY28OCT2526150PE",
  "underlying": "NIFTY28OCT25FUT",
  "underlying_ltp": 25966.05
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Response data with orderid, symbol, and underlying details
- `status_code` (int): HTTP status code

---

### OptionsMultiOrder

Place multiple option legs with common underlying. BUY legs execute first for margin efficiency.

**Function:** `place_options_multiorder(multiorder_data, api_key=None, auth_token=None, broker=None)`

**Location:** `openalgo/services/options_multiorder_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| multiorder_data | dict | Yes | Multi-order details with legs |
| api_key | str | Conditional | OpenAlgo API key (for API-based calls) |
| auth_token | str | Conditional | Direct broker authentication token (for internal calls) |
| broker | str | Conditional | Broker name (for internal calls) |

**MultiOrder Data Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| strategy | str | No | Strategy identifier |
| underlying | str | Yes | Underlying symbol (e.g., NIFTY) |
| exchange | str | Yes | Exchange (NSE_INDEX, BSE_INDEX) |
| expiry_date | str | No | Common expiry date (can be overridden per leg) |
| legs | array | Yes | Array of leg objects |

**Leg Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| offset | str | Yes | Strike offset (ATM, ITM1-ITM50, OTM1-OTM50) |
| option_type | str | Yes | CE or PE |
| action | str | Yes | BUY or SELL |
| quantity | int | Yes | Order quantity |
| expiry_date | str | No | Leg-specific expiry (for diagonal spreads) |
| pricetype | str | No | MARKET (default), LIMIT |
| product | str | No | MIS, NRML (default) |
| splitsize | int | No | Split size for this leg |

**Example - Iron Condor (Same Expiry):**

```python
from services.options_multiorder_service import place_options_multiorder

multiorder_data = {
    "strategy": "Iron Condor Test",
    "underlying": "NIFTY",
    "exchange": "NSE_INDEX",
    "expiry_date": "25NOV25",
    "legs": [
        {"offset": "OTM6", "option_type": "CE", "action": "BUY", "quantity": 75},
        {"offset": "OTM6", "option_type": "PE", "action": "BUY", "quantity": 75},
        {"offset": "OTM4", "option_type": "CE", "action": "SELL", "quantity": 75},
        {"offset": "OTM4", "option_type": "PE", "action": "SELL", "quantity": 75}
    ]
}

success, response, status_code = place_options_multiorder(
    multiorder_data=multiorder_data,
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
    "status": "success",
    "underlying": "NIFTY",
    "underlying_ltp": 26050.45,
    "results": [
        {
            "action": "BUY",
            "leg": 1,
            "mode": "analyze",
            "offset": "OTM6",
            "option_type": "CE",
            "orderid": "25111996859688",
            "status": "success",
            "symbol": "NIFTY25NOV2526350CE"
        },
        {
            "action": "BUY",
            "leg": 2,
            "mode": "analyze",
            "offset": "OTM6",
            "option_type": "PE",
            "orderid": "25111996042210",
            "status": "success",
            "symbol": "NIFTY25NOV2525750PE"
        },
        {
            "action": "SELL",
            "leg": 3,
            "mode": "analyze",
            "offset": "OTM4",
            "option_type": "CE",
            "orderid": "25111922189638",
            "status": "success",
            "symbol": "NIFTY25NOV2526250CE"
        },
        {
            "action": "SELL",
            "leg": 4,
            "mode": "analyze",
            "offset": "OTM4",
            "option_type": "PE",
            "orderid": "25111919252668",
            "status": "success",
            "symbol": "NIFTY25NOV2525850PE"
        }
    ]
}
```

**Example - Diagonal Spread (Different Expiry):**

```python
multiorder_data = {
    "strategy": "Diagonal Spread Test",
    "underlying": "NIFTY",
    "exchange": "NSE_INDEX",
    "legs": [
        {"offset": "ITM2", "option_type": "CE", "action": "BUY", "quantity": 75, "expiry_date": "30DEC25"},
        {"offset": "OTM2", "option_type": "CE", "action": "SELL", "quantity": 75, "expiry_date": "25NOV25"}
    ]
}

success, response, status_code = place_options_multiorder(
    multiorder_data=multiorder_data,
    api_key='your_api_key_here'
)
```

**Response:**

```json
{
    "results": [
        {
            "action": "BUY",
            "leg": 1,
            "mode": "analyze",
            "offset": "ITM2",
            "option_type": "CE",
            "orderid": "25111933337854",
            "status": "success",
            "symbol": "NIFTY30DEC2525950CE"
        },
        {
            "action": "SELL",
            "leg": 2,
            "mode": "analyze",
            "offset": "OTM2",
            "option_type": "CE",
            "orderid": "25111957475473",
            "status": "success",
            "symbol": "NIFTY25NOV2526150CE"
        }
    ],
    "status": "success",
    "underlying": "NIFTY",
    "underlying_ltp": 26052.65
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Response data with results array
- `status_code` (int): HTTP status code

**Note:** BUY legs are always executed before SELL legs for margin efficiency.

---

### BasketOrder

Place multiple orders simultaneously.

**Function:** `place_basket_order(basket_data, api_key=None, auth_token=None, broker=None)`

**Location:** `openalgo/services/basket_order_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| basket_data | dict | Yes | Basket order details with orders array |
| api_key | str | Conditional | OpenAlgo API key |
| auth_token | str | Conditional | Direct broker authentication token |
| broker | str | Conditional | Broker name |

**Basket Data Structure:**

```python
{
    "strategy": "Strategy Name",
    "orders": [
        {
            "symbol": "BHEL",
            "exchange": "NSE",
            "action": "BUY",
            "quantity": 1,
            "pricetype": "MARKET",
            "product": "MIS"
        },
        {
            "symbol": "ZOMATO",
            "exchange": "NSE",
            "action": "SELL",
            "quantity": 1,
            "pricetype": "MARKET",
            "product": "MIS"
        }
    ]
}
```

**Example:**

```python
from services.basket_order_service import place_basket_order

basket_data = {
    "strategy": "Python",
    "orders": [
        {
            "symbol": "BHEL",
            "exchange": "NSE",
            "action": "BUY",
            "quantity": 1,
            "pricetype": "MARKET",
            "product": "MIS"
        },
        {
            "symbol": "ZOMATO",
            "exchange": "NSE",
            "action": "SELL",
            "quantity": 1,
            "pricetype": "MARKET",
            "product": "MIS"
        }
    ]
}

success, response, status_code = place_basket_order(
    basket_data=basket_data,
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "status": "success",
  "results": [
    {
      "symbol": "BHEL",
      "status": "success",
      "orderid": "250408000999544"
    },
    {
      "symbol": "ZOMATO",
      "status": "success",
      "orderid": "250408000997545"
    }
  ]
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Response data with results array
- `status_code` (int): HTTP status code

---

### SplitOrder

Split a large order into multiple smaller orders.

**Function:** `split_order(split_data, api_key=None, auth_token=None, broker=None)`

**Location:** `openalgo/services/split_order_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| split_data | dict | Yes | Split order details |
| api_key | str | Conditional | OpenAlgo API key |
| auth_token | str | Conditional | Direct broker authentication token |
| broker | str | Conditional | Broker name |

**Split Data Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| symbol | str | Yes | Trading symbol |
| exchange | str | Yes | Exchange (NSE, NFO, etc.) |
| action | str | Yes | BUY or SELL |
| quantity | int | Yes | Total quantity to split |
| splitsize | int | Yes | Size of each split order |
| pricetype | str | Yes | MARKET, LIMIT, SL, SL-M |
| product | str | Yes | MIS, CNC, NRML |
| price | float/str | No | Order price (for LIMIT orders) |

**Example:**

```python
from services.split_order_service import split_order

split_data = {
    "symbol": "YESBANK",
    "exchange": "NSE",
    "action": "SELL",
    "quantity": 105,
    "splitsize": 20,
    "pricetype": "MARKET",
    "product": "MIS"
}

success, response, status_code = split_order(
    split_data=split_data,
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "status": "success",
  "split_size": 20,
  "total_quantity": 105,
  "results": [
    {
      "order_num": 1,
      "orderid": "250408001021467",
      "quantity": 20,
      "status": "success"
    },
    {
      "order_num": 2,
      "orderid": "250408001021459",
      "quantity": 20,
      "status": "success"
    },
    {
      "order_num": 3,
      "orderid": "250408001021466",
      "quantity": 20,
      "status": "success"
    },
    {
      "order_num": 4,
      "orderid": "250408001021470",
      "quantity": 20,
      "status": "success"
    },
    {
      "order_num": 5,
      "orderid": "250408001021471",
      "quantity": 20,
      "status": "success"
    },
    {
      "order_num": 6,
      "orderid": "250408001021472",
      "quantity": 5,
      "status": "success"
    }
  ]
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Response data with split details
- `status_code` (int): HTTP status code

**Note:** Maximum 100 orders allowed per split.

---

### ModifyOrder

Modify an existing order.

**Function:** `modify_order(order_data, api_key=None, auth_token=None, broker=None)`

**Location:** `openalgo/services/modify_order_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| order_data | dict | Yes | Modified order details |
| api_key | str | Conditional | OpenAlgo API key |
| auth_token | str | Conditional | Direct broker authentication token |
| broker | str | Conditional | Broker name |

**Order Data Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| orderid | str | Yes | Order ID to modify |
| strategy | str | No | Strategy identifier |
| symbol | str | Yes | Trading symbol |
| action | str | Yes | BUY or SELL |
| exchange | str | Yes | Exchange (NSE, NFO, etc.) |
| pricetype | str | Yes | MARKET, LIMIT, SL, SL-M |
| product | str | Yes | MIS, CNC, NRML |
| quantity | int/str | Yes | New order quantity |
| price | float/str | Yes | New order price |

**Example:**

```python
from services.modify_order_service import modify_order

order_data = {
    "orderid": "250408001002736",
    "strategy": "Python",
    "symbol": "YESBANK",
    "action": "BUY",
    "exchange": "NSE",
    "pricetype": "LIMIT",
    "product": "CNC",
    "quantity": 1,
    "price": 16.5
}

success, response, status_code = modify_order(
    order_data=order_data,
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "orderid": "250408001002736",
  "status": "success"
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Response data
- `status_code` (int): HTTP status code

---

### CancelOrder

Cancel an existing order.

**Function:** `cancel_order(orderid, api_key=None, auth_token=None, broker=None)`

**Location:** `openalgo/services/cancel_order_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| orderid | str | Yes | Order ID to cancel |
| api_key | str | Conditional | OpenAlgo API key |
| auth_token | str | Conditional | Direct broker authentication token |
| broker | str | Conditional | Broker name |

**Example:**

```python
from services.cancel_order_service import cancel_order

success, response, status_code = cancel_order(
    orderid="250408001002736",
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "orderid": "250408001002736",
  "status": "success"
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Response data
- `status_code` (int): HTTP status code

---

### CancelAllOrder

Cancel all open orders and trigger pending orders.

**Function:** `cancel_all_orders(order_data=None, api_key=None, auth_token=None, broker=None)`

**Location:** `openalgo/services/cancel_all_order_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| order_data | dict | No | Additional order data (optional) |
| api_key | str | Conditional | OpenAlgo API key |
| auth_token | str | Conditional | Direct broker authentication token |
| broker | str | Conditional | Broker name |

**Example:**

```python
from services.cancel_all_order_service import cancel_all_orders

success, response, status_code = cancel_all_orders(
    order_data={"strategy": "Python"},
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "status": "success",
  "message": "Canceled 5 orders. Failed to cancel 0 orders.",
  "canceled_orders": [
    "250408001042620",
    "250408001042667",
    "250408001042642",
    "250408001043015",
    "250408001043386"
  ],
  "failed_cancellations": []
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Response data with canceled and failed lists
- `status_code` (int): HTTP status code

---

### ClosePosition

Close all open positions across various exchanges.

**Function:** `close_position(position_data=None, api_key=None, auth_token=None, broker=None)`

**Location:** `openalgo/services/close_position_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| position_data | dict | No | Additional position data (optional) |
| api_key | str | Conditional | OpenAlgo API key |
| auth_token | str | Conditional | Direct broker authentication token |
| broker | str | Conditional | Broker name |

**Example:**

```python
from services.close_position_service import close_position

success, response, status_code = close_position(
    position_data={"strategy": "Python"},
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "message": "All Open Positions Squared Off",
  "status": "success"
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Response data
- `status_code` (int): HTTP status code

---

## Order Information Services

### OrderStatus

Get the current status of an order.

**Function:** `get_order_status(status_data, api_key=None, auth_token=None, broker=None)`

**Location:** `openalgo/services/orderstatus_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| status_data | dict | Yes | Order status request data |
| api_key | str | Conditional | OpenAlgo API key |
| auth_token | str | Conditional | Direct broker authentication token |
| broker | str | Conditional | Broker name |

**Status Data Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| orderid | str | Yes | Order ID to query |
| strategy | str | No | Strategy identifier |

**Example:**

```python
from services.orderstatus_service import get_order_status

status_data = {
    "orderid": "250828000185002",
    "strategy": "Test Strategy"
}

success, response, status_code = get_order_status(
    status_data=status_data,
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "data": {
    "action": "BUY",
    "average_price": 18.95,
    "exchange": "NSE",
    "order_status": "complete",
    "orderid": "250828000185002",
    "price": 0,
    "pricetype": "MARKET",
    "product": "MIS",
    "quantity": "1",
    "symbol": "YESBANK",
    "timestamp": "28-Aug-2025 09:59:10",
    "trigger_price": 0
  },
  "status": "success"
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Response data with order details
- `status_code` (int): HTTP status code

---

### OpenPosition

Get the current open position for a symbol.

**Function:** `get_open_position(position_data, api_key=None, auth_token=None, broker=None)`

**Location:** `openalgo/services/openposition_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| position_data | dict | Yes | Position query data |
| api_key | str | Conditional | OpenAlgo API key |
| auth_token | str | Conditional | Direct broker authentication token |
| broker | str | Conditional | Broker name |

**Position Data Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| symbol | str | Yes | Trading symbol |
| exchange | str | Yes | Exchange (NSE, NFO, etc.) |
| product | str | Yes | MIS, CNC, NRML |
| strategy | str | No | Strategy identifier |

**Example:**

```python
from services.openposition_service import get_open_position

position_data = {
    "symbol": "YESBANK",
    "exchange": "NSE",
    "product": "MIS",
    "strategy": "Test Strategy"
}

success, response, status_code = get_open_position(
    position_data=position_data,
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "quantity": "-10",
  "status": "success"
}
```

**Note:** The service internally fetches the positionbook and filters by symbol, exchange, and product. Returns 0 if position not found.

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Response data with position quantity
- `status_code` (int): HTTP status code

---

## Market Data Services

### Quotes

Get market quotes for a symbol.

**Function:** `get_quotes(symbol, exchange, api_key=None, auth_token=None, broker=None)`

**Location:** `openalgo/services/quotes_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| symbol | str | Yes | Trading symbol |
| exchange | str | Yes | Exchange (NSE, NFO, etc.) |
| api_key | str | Conditional | OpenAlgo API key |
| auth_token | str | Conditional | Direct broker authentication token |
| broker | str | Conditional | Broker name |

**Example:**

```python
from services.quotes_service import get_quotes

success, response, status_code = get_quotes(
    symbol="RELIANCE",
    exchange="NSE",
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "open": 1172.0,
    "high": 1196.6,
    "low": 1163.3,
    "ltp": 1187.75,
    "ask": 1188.0,
    "bid": 1187.85,
    "prev_close": 1165.7,
    "volume": 14414545
  }
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Response data with quote information
- `status_code` (int): HTTP status code

---

### MultiQuotes

Get real-time quotes for multiple symbols in a single call.

**Function:** `get_multiquotes(symbols, api_key=None, auth_token=None, feed_token=None, broker=None)`

**Location:** `openalgo/services/quotes_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| symbols | list | Yes | List of dicts with 'symbol' and 'exchange' keys |
| api_key | str | Conditional | OpenAlgo API key |
| auth_token | str | Conditional | Direct broker authentication token |
| feed_token | str | Conditional | Direct broker feed token |
| broker | str | Conditional | Broker name |

**Symbols List Structure:**

```python
[
    {"symbol": "RELIANCE", "exchange": "NSE"},
    {"symbol": "TCS", "exchange": "NSE"},
    {"symbol": "INFY", "exchange": "NSE"}
]
```

**Example:**

```python
from services.quotes_service import get_multiquotes

symbols = [
    {"symbol": "RELIANCE", "exchange": "NSE"},
    {"symbol": "TCS", "exchange": "NSE"},
    {"symbol": "INFY", "exchange": "NSE"}
]

success, response, status_code = get_multiquotes(
    symbols=symbols,
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "status": "success",
  "results": [
    {
      "symbol": "RELIANCE",
      "exchange": "NSE",
      "data": {
        "open": 1542.3,
        "high": 1571.6,
        "low": 1540.5,
        "ltp": 1569.9,
        "prev_close": 1539.7,
        "ask": 1569.9,
        "bid": 0,
        "oi": 0,
        "volume": 14054299
      }
    },
    {
      "symbol": "TCS",
      "exchange": "NSE",
      "data": {
        "open": 3118.8,
        "high": 3178,
        "low": 3117,
        "ltp": 3162.9,
        "prev_close": 3119.2,
        "ask": 0,
        "bid": 3162.9,
        "oi": 0,
        "volume": 2508527
      }
    },
    {
      "symbol": "INFY",
      "exchange": "NSE",
      "data": {
        "open": 1532.1,
        "high": 1560.3,
        "low": 1532.1,
        "ltp": 1557.9,
        "prev_close": 1530.6,
        "ask": 0,
        "bid": 1557.9,
        "oi": 0,
        "volume": 7575038
      }
    }
  ]
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Response data with results array
- `status_code` (int): HTTP status code

**Note:** Invalid symbols are returned with an error field. If broker doesn't support multiquotes, the service falls back to fetching quotes individually.

---

### Depth

Get market depth for a symbol.

**Function:** `get_depth(symbol, exchange, api_key=None, auth_token=None, broker=None)`

**Location:** `openalgo/services/depth_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| symbol | str | Yes | Trading symbol |
| exchange | str | Yes | Exchange (NSE, NFO, etc.) |
| api_key | str | Conditional | OpenAlgo API key |
| auth_token | str | Conditional | Direct broker authentication token |
| broker | str | Conditional | Broker name |

**Example:**

```python
from services.depth_service import get_depth

success, response, status_code = get_depth(
    symbol="SBIN",
    exchange="NSE",
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "open": 760.0,
    "high": 774.0,
    "low": 758.15,
    "ltp": 769.6,
    "ltq": 205,
    "prev_close": 746.9,
    "volume": 9362799,
    "oi": 161265750,
    "totalbuyqty": 591351,
    "totalsellqty": 835701,
    "asks": [
      {
        "price": 769.6,
        "quantity": 767
      },
      {
        "price": 769.65,
        "quantity": 115
      }
    ],
    "bids": [
      {
        "price": 769.4,
        "quantity": 886
      },
      {
        "price": 769.35,
        "quantity": 212
      }
    ]
  }
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Response data with market depth
- `status_code` (int): HTTP status code

---

### History

Get historical data for a symbol.

**Function:** `get_history(symbol, exchange, interval, start_date, end_date, api_key=None, auth_token=None, broker=None)`

**Location:** `openalgo/services/history_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| symbol | str | Yes | Trading symbol |
| exchange | str | Yes | Exchange (NSE, NFO, etc.) |
| interval | str | Yes | Time interval (1m, 5m, 15m, 1h, D) |
| start_date | str | Yes | Start date (YYYY-MM-DD) |
| end_date | str | Yes | End date (YYYY-MM-DD) |
| api_key | str | Conditional | OpenAlgo API key |
| auth_token | str | Conditional | Direct broker authentication token |
| broker | str | Conditional | Broker name |

**Example:**

```python
from services.history_service import get_history

success, response, status_code = get_history(
    symbol="SBIN",
    exchange="NSE",
    interval="5m",
    start_date="2025-04-01",
    end_date="2025-04-08",
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```
                            close    high     low    open  volume
timestamp
2025-04-01 09:15:00+05:30  772.50  774.00  763.20  766.50  318625
2025-04-01 09:20:00+05:30  773.20  774.95  772.10  772.45  197189
2025-04-01 09:25:00+05:30  775.15  775.60  772.60  773.20  227544
...
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (pandas.DataFrame or dict): Historical data
- `status_code` (int): HTTP status code

---

### Intervals

Get available time intervals for historical data.

**Function:** `get_intervals(api_key=None, auth_token=None, broker=None)`

**Location:** `openalgo/services/intervals_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| api_key | str | Conditional | OpenAlgo API key |
| auth_token | str | Conditional | Direct broker authentication token |
| broker | str | Conditional | Broker name |

**Example:**

```python
from services.intervals_service import get_intervals

success, response, status_code = get_intervals(
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "months": [],
    "weeks": [],
    "days": ["D"],
    "hours": ["1h"],
    "minutes": ["10m", "15m", "1m", "30m", "3m", "5m"],
    "seconds": []
  }
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Available intervals
- `status_code` (int): HTTP status code

---

## Symbol Services

### Symbol

Get detailed information about a symbol.

**Function:** `get_symbol(symbol, exchange, api_key=None, auth_token=None, broker=None)`

**Location:** `openalgo/services/symbol_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| symbol | str | Yes | Trading symbol |
| exchange | str | Yes | Exchange (NSE, NFO, etc.) |
| api_key | str | Conditional | OpenAlgo API key |
| auth_token | str | Conditional | Direct broker authentication token |
| broker | str | Conditional | Broker name |

**Example:**

```python
from services.symbol_service import get_symbol

success, response, status_code = get_symbol(
    symbol="RELIANCE",
    exchange="NSE",
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "id": 979,
    "name": "RELIANCE",
    "symbol": "RELIANCE",
    "brsymbol": "RELIANCE-EQ",
    "exchange": "NSE",
    "brexchange": "NSE",
    "instrumenttype": "",
    "expiry": "",
    "strike": -0.01,
    "lotsize": 1,
    "tick_size": 0.05,
    "token": "2885"
  }
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Symbol details
- `status_code` (int): HTTP status code

---

### Search

Search for symbols.

**Function:** `search_symbol(query, exchange, api_key=None, auth_token=None, broker=None)`

**Location:** `openalgo/services/search_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | str | Yes | Search query |
| exchange | str | Yes | Exchange (NSE, NFO, etc.) |
| api_key | str | Conditional | OpenAlgo API key |
| auth_token | str | Conditional | Direct broker authentication token |
| broker | str | Conditional | Broker name |

**Example:**

```python
from services.search_service import search_symbol

success, response, status_code = search_symbol(
    query="NIFTY 25000 JUL CE",
    exchange="NFO",
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "data": [
    {
      "brexchange": "NFO",
      "brsymbol": "NIFTY17JUL2525000CE",
      "exchange": "NFO",
      "expiry": "17-JUL-25",
      "instrumenttype": "OPTIDX",
      "lotsize": 75,
      "name": "NIFTY",
      "strike": 25000,
      "symbol": "NIFTY17JUL2525000CE",
      "tick_size": 0.05,
      "token": "47275"
    }
  ],
  "message": "Found 6 matching symbols",
  "status": "success"
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Search results
- `status_code` (int): HTTP status code

---

### Expiry

Get expiry dates for a symbol.

**Function:** `get_expiry(symbol, exchange, instrumenttype, api_key=None, auth_token=None, broker=None)`

**Location:** `openalgo/services/expiry_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| symbol | str | Yes | Trading symbol |
| exchange | str | Yes | Exchange (NSE, NFO, etc.) |
| instrumenttype | str | Yes | Instrument type (options, futures) |
| api_key | str | Conditional | OpenAlgo API key |
| auth_token | str | Conditional | Direct broker authentication token |
| broker | str | Conditional | Broker name |

**Example:**

```python
from services.expiry_service import get_expiry

success, response, status_code = get_expiry(
    symbol="NIFTY",
    exchange="NFO",
    instrumenttype="options",
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "data": [
    "10-JUL-25",
    "17-JUL-25",
    "24-JUL-25",
    "31-JUL-25",
    "07-AUG-25",
    "28-AUG-25",
    "25-SEP-25"
  ],
  "message": "Found 18 expiry dates for NIFTY options in NFO",
  "status": "success"
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Expiry dates
- `status_code` (int): HTTP status code

---

### Instruments

Get all instruments/symbols from the database.

**Function:** `get_instruments(exchange=None, api_key=None, format='json')`

**Location:** `openalgo/services/instruments_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| exchange | str | No | Exchange filter (NSE, BSE, NFO, BFO, etc.) |
| api_key | str | Yes | OpenAlgo API key |
| format | str | No | Output format ('json' or 'csv', default: 'json') |

**Example:**

```python
from services.instruments_service import get_instruments

success, response, status_code, headers = get_instruments(
    exchange="NSE",
    api_key='your_api_key_here',
    format='json'
)

print(response)
```

**Response (JSON):**

```json
{
  "status": "success",
  "message": "Found 3046 instruments",
  "data": [
    {
      "symbol": "RELIANCE",
      "brsymbol": "RELIANCE-EQ",
      "name": "RELIANCE INDUSTRIES LTD",
      "exchange": "NSE",
      "brexchange": "NSE",
      "token": "2885",
      "expiry": null,
      "strike": -1.0,
      "lotsize": 1,
      "instrumenttype": "EQ",
      "tick_size": 0.05
    },
    {
      "symbol": "TCS",
      "brsymbol": "TCS-EQ",
      "name": "TATA CONSULTANCY SERVICES",
      "exchange": "NSE",
      "brexchange": "NSE",
      "token": "11536",
      "expiry": null,
      "strike": -1.0,
      "lotsize": 1,
      "instrumenttype": "EQ",
      "tick_size": 0.05
    }
  ]
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict or str): Response data (JSON dict or CSV string)
- `status_code` (int): HTTP status code
- `headers` (dict): Response headers (for CSV downloads)

**Note:** When format='csv', the response is a CSV string and headers include Content-Disposition for file download.

---

## Options Services

### OptionSymbol

Get option symbol based on underlying, expiry, strike offset, and option type.

**Function:** `get_option_symbol(underlying, exchange, expiry_date, strike_int, offset, option_type, api_key, underlying_ltp=None)`

**Location:** `openalgo/services/option_symbol_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| underlying | str | Yes | Underlying symbol (e.g., NIFTY, BANKNIFTY) |
| exchange | str | Yes | Exchange (NSE_INDEX, BSE_INDEX, NFO, BFO) |
| expiry_date | str | No | Expiry date in DDMMMYY format |
| strike_int | int | No | Strike interval (optional - uses actual strikes if not provided) |
| offset | str | Yes | Strike offset (ATM, ITM1-ITM50, OTM1-OTM50) |
| option_type | str | Yes | CE or PE |
| api_key | str | Yes | OpenAlgo API key |
| underlying_ltp | float | No | Pre-fetched LTP to avoid redundant quote requests |

**Example - ATM Option:**

```python
from services.option_symbol_service import get_option_symbol

success, response, status_code = get_option_symbol(
    underlying="NIFTY",
    exchange="NSE_INDEX",
    expiry_date="30DEC25",
    strike_int=None,
    offset="ATM",
    option_type="CE",
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "status": "success",
  "symbol": "NIFTY30DEC2525950CE",
  "exchange": "NFO",
  "lotsize": 75,
  "tick_size": 5,
  "freeze_qty": 1800,
  "underlying_ltp": 25966.4
}
```

**Example - ITM Option:**

```python
success, response, status_code = get_option_symbol(
    underlying="NIFTY",
    exchange="NSE_INDEX",
    expiry_date="30DEC25",
    strike_int=None,
    offset="ITM3",
    option_type="PE",
    api_key='your_api_key_here'
)
```

**Response:**

```json
{
  "status": "success",
  "symbol": "NIFTY30DEC2526100PE",
  "exchange": "NFO",
  "lotsize": 75,
  "tick_size": 5,
  "freeze_qty": 1800,
  "underlying_ltp": 25966.4
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Symbol details with lotsize, tick_size, freeze_qty
- `status_code` (int): HTTP status code

**Note:** If `strike_int` is not provided, the service uses actual strikes from the database for more accurate symbol resolution.

---

### OptionChain

Get option chain data for a given underlying and expiry.

**Function:** `get_option_chain(underlying, exchange, expiry_date, strike_count, api_key)`

**Location:** `openalgo/services/option_chain_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| underlying | str | Yes | Underlying symbol (e.g., NIFTY, BANKNIFTY) |
| exchange | str | Yes | Exchange (NSE_INDEX, BSE_INDEX) |
| expiry_date | str | Yes | Expiry date in DDMMMYY format |
| strike_count | int | Yes | Number of strikes above and below ATM |
| api_key | str | Yes | OpenAlgo API key |

**Example:**

```python
from services.option_chain_service import get_option_chain

success, response, status_code = get_option_chain(
    underlying="NIFTY",
    exchange="NSE_INDEX",
    expiry_date="30DEC25",
    strike_count=10,
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
    "status": "success",
    "underlying": "NIFTY",
    "underlying_ltp": 26215.55,
    "expiry_date": "30DEC25",
    "atm_strike": 26200.0,
    "chain": [
        {
            "strike": 26100.0,
            "ce": {
                "symbol": "NIFTY30DEC2526100CE",
                "label": "ITM2",
                "ltp": 490,
                "bid": 490,
                "ask": 491,
                "open": 540,
                "high": 571,
                "low": 444.75,
                "prev_close": 496.8,
                "volume": 1195800,
                "oi": 0,
                "lotsize": 75,
                "tick_size": 0.05
            },
            "pe": {
                "symbol": "NIFTY30DEC2526100PE",
                "label": "OTM2",
                "ltp": 193,
                "bid": 191.2,
                "ask": 193,
                "open": 204.1,
                "high": 229.95,
                "low": 175.6,
                "prev_close": 215.95,
                "volume": 1832700,
                "oi": 0,
                "lotsize": 75,
                "tick_size": 0.05
            }
        },
        {
            "strike": 26200.0,
            "ce": {
                "symbol": "NIFTY30DEC2526200CE",
                "label": "ATM",
                "ltp": 427,
                "bid": 425.05,
                "ask": 427,
                "open": 449.95,
                "high": 503.5,
                "low": 384,
                "prev_close": 433.2,
                "volume": 2994000,
                "oi": 0,
                "lotsize": 75,
                "tick_size": 0.05
            },
            "pe": {
                "symbol": "NIFTY30DEC2526200PE",
                "label": "ATM",
                "ltp": 227.4,
                "bid": 227.35,
                "ask": 228.5,
                "open": 251.9,
                "high": 269.15,
                "low": 205.95,
                "prev_close": 251.9,
                "volume": 3745350,
                "oi": 0,
                "lotsize": 75,
                "tick_size": 0.05
            }
        }
    ]
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Option chain data with ATM strike and chain array
- `status_code` (int): HTTP status code

**Note:** Each strike has CE and PE objects with their own labels (ATM, ITM1, OTM1, etc.). Strikes below ATM have CE as ITM and PE as OTM, and vice versa for strikes above ATM.

---

### SyntheticFuture

Calculate synthetic futures price using ATM options.

**Function:** `calculate_synthetic_future(underlying, exchange, expiry_date, api_key)`

**Location:** `openalgo/services/synthetic_future_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| underlying | str | Yes | Underlying symbol (e.g., NIFTY, BANKNIFTY) |
| exchange | str | Yes | Exchange (NSE_INDEX, BSE_INDEX) |
| expiry_date | str | Yes | Expiry date in DDMMMYY format |
| api_key | str | Yes | OpenAlgo API key |

**Formula:**
```
Synthetic Future Price = Strike Price + Call Premium - Put Premium
```

**Example:**

```python
from services.synthetic_future_service import calculate_synthetic_future

success, response, status_code = calculate_synthetic_future(
    underlying="NIFTY",
    exchange="NSE_INDEX",
    expiry_date="25NOV25",
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "status": "success",
  "underlying": "NIFTY",
  "underlying_ltp": 25910.05,
  "expiry": "25NOV25",
  "atm_strike": 25900.0,
  "synthetic_future_price": 25980.05
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Synthetic future price and ATM strike details
- `status_code` (int): HTTP status code

**Note:** The basis (Synthetic Future Price - Spot Price) indicates the cost of carry.

---

### OptionGreeks

Calculate Option Greeks (Delta, Gamma, Theta, Vega, Rho) and Implied Volatility.

**Function:** `get_option_greeks(option_symbol, exchange, interest_rate=None, forward_price=None, underlying_symbol=None, underlying_exchange=None, expiry_time=None, api_key=None)`

**Location:** `openalgo/services/option_greeks_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| option_symbol | str | Yes | Option symbol (e.g., NIFTY25NOV2526000CE) |
| exchange | str | Yes | Exchange (NFO, BFO, CDS, MCX) |
| interest_rate | float | No | Risk-free interest rate (annualized %) |
| forward_price | float | No | Custom forward/synthetic futures price |
| underlying_symbol | str | No | Underlying symbol for spot price |
| underlying_exchange | str | No | Underlying exchange |
| expiry_time | str | No | Custom expiry time in "HH:MM" format |
| api_key | str | Yes | OpenAlgo API key |

**Example:**

```python
from services.option_greeks_service import get_option_greeks

success, response, status_code = get_option_greeks(
    option_symbol="NIFTY25NOV2526000CE",
    exchange="NFO",
    interest_rate=0.00,
    underlying_symbol="NIFTY",
    underlying_exchange="NSE_INDEX",
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "status": "success",
  "symbol": "NIFTY25NOV2526000CE",
  "exchange": "NFO",
  "underlying": "NIFTY",
  "strike": 26000.0,
  "option_type": "CE",
  "expiry_date": "25-Nov-2025",
  "days_to_expiry": 28.5071,
  "spot_price": 25966.05,
  "option_price": 435,
  "interest_rate": 0.0,
  "implied_volatility": 15.6,
  "greeks": {
    "delta": 0.4967,
    "gamma": 0.000352,
    "theta": -7.919,
    "vega": 28.9489,
    "rho": 9.733994
  }
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Greeks data with IV and all Greek values
- `status_code` (int): HTTP status code

**Note:** Uses Black-76 model (appropriate for options on futures/forwards). For deep ITM options with no time value, theoretical Greeks are returned (delta = +/-1, other Greeks = 0).

---

## Account Services

### Funds

Get account funds information.

**Function:** `get_funds(api_key=None, auth_token=None, broker=None)`

**Location:** `openalgo/services/funds_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| api_key | str | Conditional | OpenAlgo API key |
| auth_token | str | Conditional | Direct broker authentication token |
| broker | str | Conditional | Broker name |

**Example:**

```python
from services.funds_service import get_funds

success, response, status_code = get_funds(
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "availablecash": "320.66",
    "collateral": "0.00",
    "m2mrealized": "3.27",
    "m2munrealized": "-7.88",
    "utiliseddebits": "679.34"
  }
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Funds data
- `status_code` (int): HTTP status code

---

### Margin

Calculate margin requirement for a basket of positions.

**Function:** `calculate_margin(margin_data, api_key=None, auth_token=None, broker=None)`

**Location:** `openalgo/services/margin_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| margin_data | dict | Yes | Margin calculation data with positions array |
| api_key | str | Conditional | OpenAlgo API key (for API-based calls) |
| auth_token | str | Conditional | Direct broker authentication token (for internal calls) |
| broker | str | Conditional | Broker name (for internal calls) |

**Margin Data Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| apikey | str | Yes | OpenAlgo API key |
| positions | array | Yes | Array of position objects (max 50) |

**Position Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| exchange | str | Yes | Exchange (NSE, NFO, BFO, etc.) |
| symbol | str | Yes | Trading symbol |
| action | str | Yes | BUY or SELL |
| quantity | int | Yes | Position quantity |
| product | str | Yes | MIS, CNC, NRML |
| pricetype | str | Yes | MARKET, LIMIT, SL, SL-M |
| price | float | No | Order price (default: 0) |

**Example:**

```python
from services.margin_service import calculate_margin

margin_data = {
    "apikey": "your_api_key_here",
    "positions": [
        {
            "exchange": "NFO",
            "symbol": "NIFTY25DEC2526000CE",
            "action": "BUY",
            "quantity": 75,
            "product": "NRML",
            "pricetype": "MARKET",
            "price": 0
        },
        {
            "exchange": "NFO",
            "symbol": "NIFTY25DEC2526000PE",
            "action": "SELL",
            "quantity": 75,
            "product": "NRML",
            "pricetype": "MARKET",
            "price": 0
        }
    ]
}

success, response, status_code = calculate_margin(
    margin_data=margin_data,
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "total_margin": 125000.50,
    "span_margin": 100000.00,
    "exposure_margin": 25000.50,
    "margin_benefit": 15000.00,
    "positions": [
      {
        "exchange": "NFO",
        "symbol": "NIFTY25DEC2526000CE",
        "margin_required": 75000.25
      },
      {
        "exchange": "NFO",
        "symbol": "NIFTY25DEC2526000PE",
        "margin_required": 65000.25
      }
    ]
  }
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Margin calculation results
- `status_code` (int): HTTP status code

**Note:** Maximum 50 positions allowed per request. Margin calculation support depends on broker implementation.

---

### OrderBook

Get the order book.

**Function:** `get_orderbook(api_key=None, auth_token=None, broker=None)`

**Location:** `openalgo/services/orderbook_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| api_key | str | Conditional | OpenAlgo API key |
| auth_token | str | Conditional | Direct broker authentication token |
| broker | str | Conditional | Broker name |

**Example:**

```python
from services.orderbook_service import get_orderbook

success, response, status_code = get_orderbook(
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "orders": [
      {
        "action": "BUY",
        "symbol": "RELIANCE",
        "exchange": "NSE",
        "orderid": "250408000989443",
        "product": "MIS",
        "quantity": "1",
        "price": 1186.0,
        "pricetype": "MARKET",
        "order_status": "complete",
        "trigger_price": 0.0,
        "timestamp": "08-Apr-2025 13:58:03"
      }
    ],
    "statistics": {
      "total_buy_orders": 2.0,
      "total_sell_orders": 0.0,
      "total_completed_orders": 1.0,
      "total_open_orders": 0.0,
      "total_rejected_orders": 0.0
    }
  }
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Order book data
- `status_code` (int): HTTP status code

---

### TradeBook

Get the trade book.

**Function:** `get_tradebook(api_key=None, auth_token=None, broker=None)`

**Location:** `openalgo/services/tradebook_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| api_key | str | Conditional | OpenAlgo API key |
| auth_token | str | Conditional | Direct broker authentication token |
| broker | str | Conditional | Broker name |

**Example:**

```python
from services.tradebook_service import get_tradebook

success, response, status_code = get_tradebook(
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "status": "success",
  "data": [
    {
      "action": "BUY",
      "symbol": "RELIANCE",
      "exchange": "NSE",
      "orderid": "250408000989443",
      "product": "MIS",
      "quantity": 0.0,
      "average_price": 1180.1,
      "timestamp": "13:58:03",
      "trade_value": 1180.1
    }
  ]
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Trade book data
- `status_code` (int): HTTP status code

---

### PositionBook

Get the position book.

**Function:** `get_positionbook(api_key=None, auth_token=None, broker=None)`

**Location:** `openalgo/services/positionbook_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| api_key | str | Conditional | OpenAlgo API key |
| auth_token | str | Conditional | Direct broker authentication token |
| broker | str | Conditional | Broker name |

**Example:**

```python
from services.positionbook_service import get_positionbook

success, response, status_code = get_positionbook(
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "status": "success",
  "data": [
    {
      "symbol": "NHPC",
      "exchange": "NSE",
      "product": "MIS",
      "quantity": "-1",
      "average_price": "83.74",
      "ltp": "83.72",
      "pnl": "0.02"
    }
  ]
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Position book data
- `status_code` (int): HTTP status code

---

### Holdings

Get account holdings.

**Function:** `get_holdings(api_key=None, auth_token=None, broker=None)`

**Location:** `openalgo/services/holdings_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| api_key | str | Conditional | OpenAlgo API key |
| auth_token | str | Conditional | Direct broker authentication token |
| broker | str | Conditional | Broker name |

**Example:**

```python
from services.holdings_service import get_holdings

success, response, status_code = get_holdings(
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "holdings": [
      {
        "symbol": "RELIANCE",
        "exchange": "NSE",
        "product": "CNC",
        "quantity": 1,
        "pnl": -149.0,
        "pnlpercent": -11.1
      }
    ],
    "statistics": {
      "totalholdingvalue": 1768.0,
      "totalinvvalue": 2001.0,
      "totalprofitandloss": -233.15,
      "totalpnlpercentage": -11.65
    }
  }
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Holdings data
- `status_code` (int): HTTP status code

---

## Market Calendar Services

### Holidays

Get market holidays for a specific year or current year.

**Function:** `get_holidays(year=None)`

**Location:** `openalgo/services/market_calendar_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| year | int | No | Year to get holidays for (default: current year) |

**Example:**

```python
from services.market_calendar_service import get_holidays

success, response, status_code = get_holidays(year=2025)

print(response)
```

**Response:**

```json
{
  "status": "success",
  "year": 2025,
  "timezone": "Asia/Kolkata",
  "data": [
    {
      "date": "2025-02-26",
      "description": "Maha Shivaratri",
      "holiday_type": "TRADING_HOLIDAY",
      "closed_exchanges": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD"],
      "open_exchanges": [
        {"exchange": "MCX", "start_time": 1740549000000, "end_time": 1740602700000}
      ]
    },
    {
      "date": "2025-03-14",
      "description": "Holi",
      "holiday_type": "TRADING_HOLIDAY",
      "closed_exchanges": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD"],
      "open_exchanges": [
        {"exchange": "MCX", "start_time": 1741964400000, "end_time": 1742018100000}
      ]
    },
    {
      "date": "2025-08-15",
      "description": "Independence Day",
      "holiday_type": "TRADING_HOLIDAY",
      "closed_exchanges": ["NSE", "BSE", "NFO", "BFO", "CDS", "BCD", "MCX"],
      "open_exchanges": []
    }
  ]
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Holiday data with year and timezone
- `status_code` (int): HTTP status code

**Note:**
- Year must be between 2020 and 2050
- `holiday_type` can be: `TRADING_HOLIDAY`, `SETTLEMENT_HOLIDAY`, or `SPECIAL_SESSION`
- `closed_exchanges` lists exchanges that are fully closed
- `open_exchanges` lists exchanges with special trading sessions (e.g., MCX evening session, Muhurat trading)
- Times in `open_exchanges` are epoch milliseconds

---

### Timings

Get market timings for a specific date.

**Function:** `get_timings(date_str)`

**Location:** `openalgo/services/market_calendar_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| date_str | str | Yes | Date in YYYY-MM-DD format |

**Example:**

```python
from services.market_calendar_service import get_timings

success, response, status_code = get_timings(date_str="2025-01-15")

print(response)
```

**Response:**

```json
{
  "status": "success",
  "data": [
    {"exchange": "NSE", "start_time": 1736926500000, "end_time": 1736949000000},
    {"exchange": "BSE", "start_time": 1736926500000, "end_time": 1736949000000},
    {"exchange": "NFO", "start_time": 1736926500000, "end_time": 1736949000000},
    {"exchange": "BFO", "start_time": 1736926500000, "end_time": 1736949000000},
    {"exchange": "CDS", "start_time": 1736925600000, "end_time": 1736954400000},
    {"exchange": "BCD", "start_time": 1736925600000, "end_time": 1736954400000},
    {"exchange": "MCX", "start_time": 1736925600000, "end_time": 1736979300000}
  ]
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Market timing data
- `status_code` (int): HTTP status code

**Note:**
- Date must be between 2020-01-01 and 2050-12-31
- Times are returned as epoch milliseconds
- Returns empty array for weekends and full holidays
- For special sessions (e.g., Muhurat trading), returns only the special session timings

---

### CheckHoliday

Check if a specific date is a market holiday.

**Function:** `check_holiday(date_str, exchange=None)`

**Location:** `openalgo/services/market_calendar_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| date_str | str | Yes | Date in YYYY-MM-DD format |
| exchange | str | No | Optional exchange code to check (NSE, BSE, NFO, etc.) |

**Example:**

```python
from services.market_calendar_service import check_holiday

success, response, status_code = check_holiday(
    date_str="2025-01-26",
    exchange="NSE"
)

print(response)
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "date": "2025-01-26",
    "exchange": "NSE",
    "is_holiday": true
  }
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Holiday check result
- `status_code` (int): HTTP status code

---

## Analyzer Services

### AnalyzerStatus

Get analyzer mode status.

**Function:** `get_analyzer_status(analyzer_data, api_key=None, auth_token=None, broker=None)`

**Location:** `openalgo/services/analyzer_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| analyzer_data | dict | Yes | Analyzer data (can be empty dict) |
| api_key | str | Conditional | OpenAlgo API key |
| auth_token | str | Conditional | Direct broker authentication token |
| broker | str | Conditional | Broker name |

**Example:**

```python
from services.analyzer_service import get_analyzer_status

success, response, status_code = get_analyzer_status(
    analyzer_data={},
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "data": {
    "analyze_mode": true,
    "mode": "analyze",
    "total_logs": 2
  },
  "status": "success"
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Analyzer status
- `status_code` (int): HTTP status code

---

### AnalyzerToggle

Toggle analyzer mode on/off.

**Function:** `toggle_analyzer_mode(analyzer_data, api_key=None, auth_token=None, broker=None)`

**Location:** `openalgo/services/analyzer_service.py`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| analyzer_data | dict | Yes | Analyzer data containing mode |
| api_key | str | Conditional | OpenAlgo API key |
| auth_token | str | Conditional | Direct broker authentication token |
| broker | str | Conditional | Broker name |

**Analyzer Data Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| mode | bool | Yes | True to enable analyze mode, False to disable |

**Example:**

```python
from services.analyzer_service import toggle_analyzer_mode

# Switch to analyze mode (simulated responses)
analyzer_data = {
    "mode": True
}

success, response, status_code = toggle_analyzer_mode(
    analyzer_data=analyzer_data,
    api_key='your_api_key_here'
)

print(response)
```

**Response:**

```json
{
  "data": {
    "analyze_mode": true,
    "message": "Analyzer mode switched to analyze",
    "mode": "analyze",
    "total_logs": 2
  },
  "status": "success"
}
```

**Returns:**

Tuple containing:
- `success` (bool): Operation success status
- `response` (dict): Analyzer toggle response
- `status_code` (int): HTTP status code

---

## Telegram Service

### TelegramAlertService

The Telegram Alert Service provides automated notifications for order-related events via Telegram. This service is not part of the SDK yet but is available for internal use within OpenAlgo.

**Location:** `openalgo/services/telegram_alert_service.py`

**Features:**

- Asynchronous order notifications
- Support for all order types (place, modify, cancel, etc.)
- Analyze mode and live mode indicators
- Formatted messages with order details
- User-specific notifications based on API key

**Service Instance:**

```python
from services.telegram_alert_service import telegram_alert_service
```

**Methods:**

#### send_order_alert

Send order alert to a Telegram user (non-blocking).

**Function:** `telegram_alert_service.send_order_alert(order_type, order_data, response, api_key=None)`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| order_type | str | Yes | Type of order (placeorder, basketorder, etc.) |
| order_data | dict | Yes | Original order data |
| response | dict | Yes | Order response |
| api_key | str | No | API key to identify user |

**Supported Order Types:**

- `placeorder` - New order placement
- `placesmartorder` - Smart order placement
- `basketorder` - Basket order execution
- `splitorder` - Split order execution
- `modifyorder` - Order modification
- `cancelorder` - Order cancellation
- `cancelallorder` - Cancel all orders
- `closeposition` - Position closure

**Example:**

```python
from services.telegram_alert_service import telegram_alert_service

# This is typically called automatically by order services
# Manual usage example:
telegram_alert_service.send_order_alert(
    order_type='placeorder',
    order_data={
        'symbol': 'RELIANCE',
        'action': 'BUY',
        'quantity': 1,
        'pricetype': 'MARKET',
        'exchange': 'NSE',
        'product': 'MIS',
        'strategy': 'My Strategy'
    },
    response={
        'status': 'success',
        'orderid': '250408000989443',
        'mode': 'live'
    },
    api_key='your_api_key_here'
)
```

**Alert Message Format:**

The service formats alerts with the following information:

- Mode indicator (Live/Analyze)
- Order details (symbol, action, quantity, etc.)
- Order status and ID
- Timestamp
- Strategy name (if provided)

**Example Alert Message:**

```
📈 Order Placed
💰 LIVE MODE - Real Order
─────────────────────
Strategy: My Strategy
Symbol: RELIANCE
Action: BUY
Quantity: 1
Price Type: MARKET
Exchange: NSE
Product: MIS
Order ID: 250408000989443
⏰ Time: 14:35:20
```

#### send_broadcast_alert

Send broadcast alert to multiple users.

**Function:** `telegram_alert_service.send_broadcast_alert(message, filters=None)`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| message | str | Yes | Message to broadcast |
| filters | dict | No | User filters (optional) |

**Example:**

```python
from services.telegram_alert_service import telegram_alert_service

telegram_alert_service.send_broadcast_alert(
    message="🚨 Market Update: NIFTY crossed 25000!",
    filters={'notifications_enabled': True}
)
```

#### toggle_alerts

Enable or disable Telegram alerts globally.

**Function:** `telegram_alert_service.toggle_alerts(enabled)`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| enabled | bool | Yes | True to enable, False to disable |

**Example:**

```python
from services.telegram_alert_service import telegram_alert_service

# Disable all alerts
telegram_alert_service.toggle_alerts(False)

# Enable all alerts
telegram_alert_service.toggle_alerts(True)
```

**Database Integration:**

The service integrates with the following database functions:

- `get_telegram_user_by_username()` - Get user's Telegram ID
- `get_bot_config()` - Get bot configuration
- `add_notification()` - Queue notifications for offline delivery
- `get_username_by_apikey()` - Map API key to username

**Thread Pool Executor:**

The service uses a thread pool executor for non-blocking alert delivery:

```python
# Thread pool configuration
alert_executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="telegram_alert")
```

**Error Handling:**

- Errors are logged but don't affect order processing
- Failed notifications are queued for retry
- Offline messages are stored in database
- Timeout protection (10 seconds max per notification)

**Requirements:**

- User must have linked their Telegram account
- Telegram bot must be running
- User must have enabled notifications in settings
- Valid API key mapping to username

**Note:** This service is automatically invoked by all order-related services and typically doesn't need to be called manually.

---

## Authentication Methods

All service functions support two authentication methods:

### Method 1: API Key Authentication

Used when calling services via API endpoints.

```python
success, response, status_code = service_function(
    data=data,
    api_key='your_api_key_here'
)
```

### Method 2: Direct Authentication

Used for internal calls within the application.

```python
success, response, status_code = service_function(
    data=data,
    auth_token='broker_auth_token',
    broker='broker_name'
)
```

**Note:** You must provide either `api_key` OR both `auth_token` and `broker`. Mixing both methods will result in an error.

---

## Analyze Mode

All order-related services support analyze mode, which simulates order operations without executing real trades. When analyze mode is enabled:

- Orders are validated but not sent to the broker
- Simulated order IDs are generated
- All responses include `"mode": "analyze"` field
- Events are logged to the analyzer database
- SocketIO events are emitted for UI updates

To enable analyze mode:

```python
from services.analyzer_service import toggle_analyzer

success, response, status_code = toggle_analyzer(
    mode=True,
    api_key='your_api_key_here'
)
```

---

## Error Handling

All service functions return a consistent tuple format:

```python
(success, response, status_code)
```

- `success` (bool): `True` if operation succeeded, `False` otherwise
- `response` (dict): Response data or error message
- `status_code` (int): HTTP status code

**Common Error Responses:**

```json
{
  "status": "error",
  "message": "Error description"
}
```

**Common HTTP Status Codes:**

- `200` - Success
- `400` - Bad Request (validation error)
- `403` - Forbidden (invalid API key)
- `404` - Not Found (broker module not found)
- `500` - Internal Server Error

**Example Error Handling:**

```python
success, response, status_code = place_order(
    order_data=order_data,
    api_key='your_api_key'
)

if not success:
    print(f"Error: {response.get('message')}")
    print(f"Status Code: {status_code}")
else:
    print(f"Order ID: {response.get('orderid')}")
```

---

## SocketIO Events

Services emit real-time events via SocketIO for UI updates:

**Order Events:**

```python
socketio.emit('order_event', {
    'symbol': 'RELIANCE',
    'action': 'BUY',
    'orderid': '250408000989443',
    'exchange': 'NSE',
    'pricetype': 'MARKET',
    'product': 'MIS',
    'mode': 'live'
})
```

**Analyzer Events:**

```python
socketio.emit('analyzer_update', {
    'request': {...},
    'response': {...}
})
```

**Cancel Events:**

```python
socketio.emit('cancel_order_event', {
    'status': 'success',
    'orderid': '250408001002736',
    'mode': 'live'
})
```

---

## Logging

All services use structured logging:

```python
from utils.logging import get_logger

logger = get_logger(__name__)
logger.info("Order placed successfully")
logger.error("Failed to place order", exc_info=True)
```

Logs are automatically stored in the API log database:

```python
from database.apilog_db import async_log_order

executor.submit(async_log_order, 'placeorder', request_data, response_data)
```

---

## Concurrency

Services use thread pool executors for async operations:

```python
from concurrent.futures import ThreadPoolExecutor

# For API logging
executor = ThreadPoolExecutor(max_workers=10)

# For Telegram alerts
alert_executor = ThreadPoolExecutor(max_workers=5)
```

**Batch Operations:**

Basket orders and split orders use concurrent execution:

```python
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(place_single_order, order) for order in orders]
    results = [future.result() for future in as_completed(futures)]
```

---

## Best Practices

1. **Always handle errors gracefully:**
   ```python
   success, response, status_code = service_function(...)
   if not success:
       handle_error(response)
   ```

2. **Use appropriate authentication method:**
   - API key for external calls
   - Direct auth for internal calls

3. **Enable analyze mode for testing:**
   ```python
   toggle_analyzer(mode=True, api_key='...')
   ```

4. **Monitor SocketIO events for real-time updates**

5. **Check API logs for debugging:**
   - Database: `apilog_db`
   - Analyzer logs: `analyzer_db`

6. **Use batch operations for multiple orders:**
   - `place_basket_order()` for different symbols
   - `split_order()` for large quantities

7. **Handle Telegram notifications:**
   - Ensure users have linked accounts
   - Check notification settings
   - Monitor alert queue

---

## Service Dependencies

Services depend on the following modules:

**Database:**
- `database.auth_db` - Authentication
- `database.apilog_db` - API logging
- `database.settings_db` - Settings
- `database.analyzer_db` - Analyzer logs
- `database.telegram_db` - Telegram users

**Utils:**
- `utils.api_analyzer` - Request analysis
- `utils.constants` - Validation constants
- `utils.logging` - Logging utilities

**Extensions:**
- `extensions.socketio` - Real-time events

**Broker Modules:**
- `broker.{broker_name}.api.order_api` - Broker-specific APIs

---

## Support

For issues or questions:
- GitHub: https://github.com/marketcalls/openalgo
- Documentation: https://docs.openalgo.in
- Discord: Join our community

---

**Last Updated:** January 2025
**Version:** OpenAlgo Dawn

```


---

# FILE: docs\prompt\statistical - openalgo indicators.md

```md
# Statistical

## OpenAlgo Statistical Indicators Documentation

Statistical indicators analyze price data using mathematical and statistical methods to identify patterns, relationships, and forecast future price movements.

### Import Statement

```python
from openalgo import ta
```

### Getting Market Data

```python
from openalgo import api

client = api(api_key='your_api_key_here', host='http://127.0.0.1:5000')

# Fetch historical data
df = client.history(symbol="SBIN", 
                   exchange="NSE", 
                   interval="5m", 
                   start_date="2025-04-01", 
                   end_date="2025-04-08")
```

### Available Statistical Indicators

***

### Linear Regression (LINREG)

Linear Regression calculates the linear regression line for a given period using the least squares method to identify the underlying trend.

#### Usage

```python
linreg_result = ta.linreg(data, period)
```

#### Parameters

* **data** *(array-like)*: Price data (typically closing prices)
* **period** *(int, default=14)*: Period for linear regression calculation

#### Returns

* **array**: Linear regression values in the same format as input

#### Example

```python
# Calculate 20-period Linear Regression
linreg_20 = ta.linreg(df['close'], 20)

# Add to DataFrame
df['LINREG_20'] = linreg_20

print(df[['close', 'LINREG_20']].tail())
```

***

### Linear Regression Slope (LRSLOPE)

Linear Regression Slope measures the rate of change of the linear regression line, indicating the strength and direction of the trend.

#### Usage

```python
slope_result = ta.lrslope(data, period=100, interval=1)
```

#### Parameters

* **data** *(array-like)*: Price data (typically closing prices)
* **period** *(int, default=100)*: Period for linear regression calculation
* **interval** *(int, default=1)*: Interval divisor for slope calculation

#### Returns

* **array**: Slope values in the same format as input

#### Example

```python
# Calculate Linear Regression Slope
slope_50 = ta.lrslope(df['close'], period=50)

# Add to DataFrame
df['LR_SLOPE_50'] = slope_50

print(df[['close', 'LR_SLOPE_50']].tail())
```

***

### Pearson Correlation Coefficient (CORREL)

Correlation measures the statistical relationship between two data series, ranging from -1 (perfect negative correlation) to +1 (perfect positive correlation).

#### Usage

```python
correlation_result = ta.correlation(data1, data2, period)
```

#### Parameters

* **data1** *(array-like)*: First data series
* **data2** *(array-like)*: Second data series
* **period** *(int, default=20)*: Period for correlation calculation

#### Returns

* **array**: Correlation values in the same format as input

#### Example

```python
# Calculate correlation between close and volume
correlation_20 = ta.correlation(df['close'], df['volume'], 20)

# Add to DataFrame
df['CORREL_CLOSE_VOLUME'] = correlation_20

print(df[['close', 'volume', 'CORREL_CLOSE_VOLUME']].tail())

# Calculate correlation between high and low
correlation_hl = ta.correlation(df['high'], df['low'], 15)
df['CORREL_HIGH_LOW'] = correlation_hl
```

***

### Beta Coefficient (BETA)

Beta measures the volatility of a security relative to the market, indicating how much the security price moves relative to market movements.

#### Usage

```python
beta_result = ta.beta(asset, market, period=252)
```

#### Parameters

* **asset** *(array-like)*: Asset price data
* **market** *(array-like)*: Market price data (benchmark)
* **period** *(int, default=252)*: Period for beta calculation (typically 1 year = 252 trading days)

#### Returns

* **array**: Beta values in the same format as input

#### Example

```python
# Assuming you have market index data
# For demonstration, we'll use another stock as market proxy
market_df = client.history(symbol="NIFTY", 
                          exchange="NSE_INDEX", 
                          interval="5m", 
                          start_date="2025-04-01", 
                          end_date="2025-04-08")

# Calculate 50-period Beta
beta_50 = ta.beta(df['close'], market_df['close'], 50)

# Add to DataFrame
df['BETA_50'] = beta_50

print(df[['close', 'BETA_50']].tail())
```

***

### Variance (VAR)

Variance measures the dispersion of price data, supporting both logarithmic returns and price modes with smoothing and signal generation.

#### Usage

```python
variance_result = ta.variance(data, lookback=20, mode="PR", ema_period=20, 
                             filter_lookback=20, ema_length=14, return_components=False)
```

#### Parameters

* **data** *(array-like)*: Price data (close prices)
* **lookback** *(int, default=20)*: Variance lookback period
* **mode** *(str, default="PR")*: Variance mode ("LR" for Logarithmic Returns, "PR" for Price)
* **ema\_period** *(int, default=20)*: EMA period for variance smoothing
* **filter\_lookback** *(int, default=20)*: Lookback period for variance filter
* **ema\_length** *(int, default=14)*: EMA length for z-score smoothing
* **return\_components** *(bool, default=False)*: If True, returns all components

#### Returns

* **array or tuple**: Variance values or (variance, ema\_variance, zscore, ema\_zscore, stdev) if return\_components=True

#### Example

```python
# Calculate basic variance
variance_20 = ta.variance(df['close'], lookback=20)
df['VARIANCE_20'] = variance_20

# Calculate variance with all components
var_components = ta.variance(df['close'], lookback=20, return_components=True)
variance, ema_var, zscore, ema_zscore, stdev = var_components

df['VARIANCE'] = variance
df['EMA_VARIANCE'] = ema_var
df['VAR_ZSCORE'] = zscore

print(df[['close', 'VARIANCE', 'EMA_VARIANCE', 'VAR_ZSCORE']].tail())
```

***

### Time Series Forecast (TSF)

Time Series Forecast predicts the next value using linear regression analysis.

#### Usage

```python
tsf_result = ta.tsf(data, period=14)
```

#### Parameters

* **data** *(array-like)*: Price data
* **period** *(int, default=14)*: Period for forecast calculation

#### Returns

* **array**: Time Series Forecast values in the same format as input

#### Example

```python
# Calculate 14-period Time Series Forecast
tsf_14 = ta.tsf(df['close'], 14)

# Add to DataFrame
df['TSF_14'] = tsf_14

print(df[['close', 'TSF_14']].tail())

# Compare actual vs forecast
df['TSF_DIFF'] = df['close'] - df['TSF_14']
print("Forecast accuracy (last 10 periods):")
print(df[['close', 'TSF_14', 'TSF_DIFF']].tail(10))
```

***

### Rolling Median (MEDIAN)

Rolling Median calculates the median value over a rolling window, which is less sensitive to outliers than mean-based indicators.

#### Usage

```python
median_result = ta.median(data, period=3)
```

#### Parameters

* **data** *(array-like)*: Price data (default hl2 in Pine Script)
* **period** *(int, default=3)*: Period for median calculation

#### Returns

* **array**: Median values in the same format as input

#### Example

```python
# Calculate 5-period Rolling Median
median_5 = ta.median(df['close'], 5)

# Calculate median of typical price
typical_price = (df['high'] + df['low'] + df['close']) / 3
median_typical = ta.median(typical_price, 7)

# Add to DataFrame
df['MEDIAN_5'] = median_5
df['MEDIAN_TYPICAL'] = median_typical

print(df[['close', 'MEDIAN_5', 'MEDIAN_TYPICAL']].tail())
```

***

### Median Bands (MEDIAN\_BANDS)

Median Bands combine median calculation with ATR-based bands and EMA smoothing for comprehensive analysis.

#### Usage

```python
median, upper_band, lower_band, median_ema = ta.median_bands.calculate_with_bands(
    high, low, close, source=None, median_length=3, atr_length=14, atr_mult=2.0
)
```

#### Parameters

* **high** *(array-like)*: High prices
* **low** *(array-like)*: Low prices
* **close** *(array-like)*: Close prices
* **source** *(array-like, optional)*: Source data for median (default: hl2)
* **median\_length** *(int, default=3)*: Period for median calculation
* **atr\_length** *(int, default=14)*: Period for ATR calculation
* **atr\_mult** *(float, default=2.0)*: ATR multiplier for bands

#### Returns

* **tuple**: (median, upper\_band, lower\_band, median\_ema) arrays

#### Example

```python
# Calculate Median Bands
median, upper, lower, median_ema = ta.median_bands.calculate_with_bands(
    df['high'], df['low'], df['close']
)

# Add to DataFrame
df['MEDIAN'] = median
df['MEDIAN_UPPER'] = upper
df['MEDIAN_LOWER'] = lower
df['MEDIAN_EMA'] = median_ema

print(df[['close', 'MEDIAN', 'MEDIAN_UPPER', 'MEDIAN_LOWER']].tail())
```

***

### Rolling Mode (MODE)

Rolling Mode calculates the most frequent value over a rolling window using discretization.

#### Usage

```python
mode_result = ta.mode(data, period=20, bins=10)
```

#### Parameters

* **data** *(array-like)*: Price data
* **period** *(int, default=20)*: Period for mode calculation
* **bins** *(int, default=10)*: Number of bins for discretization

#### Returns

* **array**: Mode values in the same format as input

#### Example

```python
# Calculate 15-period Rolling Mode
mode_15 = ta.mode(df['close'], period=15, bins=8)

# Add to DataFrame
df['MODE_15'] = mode_15

print(df[['close', 'MODE_15']].tail())

# Calculate mode for volume (often useful for volume analysis)
volume_mode = ta.mode(df['volume'], period=20, bins=12)
df['VOLUME_MODE'] = volume_mode
```

***

### Complete Example: Statistical Analysis Dashboard

```python
import pandas as pd
from openalgo import api, ta

# Get market data
client = api(api_key='your_api_key_here', host='http://127.0.0.1:5000')

df = client.history(symbol="SBIN", 
                   exchange="NSE", 
                   interval="5m", 
                   start_date="2025-04-01", 
                   end_date="2025-04-08")

# Calculate comprehensive statistical indicators
print("Calculating Statistical Indicators...")

# Trend Analysis
df['LINREG_20'] = ta.linreg(df['close'], 20)
df['LR_SLOPE_20'] = ta.lrslope(df['close'], 20)
df['TSF_14'] = ta.tsf(df['close'], 14)

# Central Tendency
df['MEDIAN_5'] = ta.median(df['close'], 5)
df['MODE_15'] = ta.mode(df['close'], 15)

# Variability Analysis
df['VARIANCE_20'] = ta.variance(df['close'], 20)

# Get variance components for detailed analysis
var_components = ta.variance(df['close'], lookback=20, return_components=True)
variance, ema_var, zscore, ema_zscore, stdev = var_components

df['VARIANCE'] = variance
df['EMA_VARIANCE'] = ema_var
df['VAR_ZSCORE'] = zscore
df['STDEV'] = stdev

# Correlation Analysis
df['CORREL_CLOSE_VOLUME'] = ta.correlation(df['close'], df['volume'], 20)
df['CORREL_HIGH_LOW'] = ta.correlation(df['high'], df['low'], 15)

# Median Bands Analysis
median, upper, lower, median_ema = ta.median_bands.calculate_with_bands(
    df['high'], df['low'], df['close'], median_length=5, atr_length=14
)

df['MEDIAN_BANDS'] = median
df['MEDIAN_UPPER'] = upper
df['MEDIAN_LOWER'] = lower
df['MEDIAN_EMA'] = median_ema

# Create analysis summary
analysis_cols = [
    'close', 'LINREG_20', 'LR_SLOPE_20', 'TSF_14', 
    'MEDIAN_5', 'VARIANCE_20', 'VAR_ZSCORE', 
    'CORREL_CLOSE_VOLUME', 'MEDIAN_BANDS'
]

print("\nStatistical Analysis Summary (Last 10 periods):")
print(df[analysis_cols].tail(10))

# Generate trading signals based on statistical indicators
print("\nGenerating Statistical Trading Signals...")

# Trend Strength Signal (based on Linear Regression Slope)
df['TREND_SIGNAL'] = 'NEUTRAL'
df.loc[df['LR_SLOPE_20'] > 0.5, 'TREND_SIGNAL'] = 'BULLISH'
df.loc[df['LR_SLOPE_20'] < -0.5, 'TREND_SIGNAL'] = 'BEARISH'

# Variance-based Volatility Signal
df['VOLATILITY_SIGNAL'] = 'NORMAL'
df.loc[df['VAR_ZSCORE'] > 1.5, 'VOLATILITY_SIGNAL'] = 'HIGH'
df.loc[df['VAR_ZSCORE'] < -1.5, 'VOLATILITY_SIGNAL'] = 'LOW'

# Price Position relative to Statistical Measures
df['PRICE_VS_LINREG'] = (df['close'] - df['LINREG_20']) / df['LINREG_20'] * 100
df['PRICE_VS_MEDIAN'] = (df['close'] - df['MEDIAN_5']) / df['MEDIAN_5'] * 100

# Forecast Accuracy
df['FORECAST_ERROR'] = abs(df['close'] - df['TSF_14'].shift(1))
df['FORECAST_ACCURACY'] = (1 - df['FORECAST_ERROR'] / df['close']) * 100

print("\nTrading Signals Summary:")
signal_summary = df[['TREND_SIGNAL', 'VOLATILITY_SIGNAL', 'PRICE_VS_LINREG', 
                    'PRICE_VS_MEDIAN', 'FORECAST_ACCURACY']].tail(5)
print(signal_summary)

# Statistical Summary
print("\nStatistical Metrics Summary:")
print(f"Average Correlation (Close vs Volume): {df['CORREL_CLOSE_VOLUME'].mean():.4f}")
print(f"Average Variance: {df['VARIANCE_20'].mean():.4f}")
print(f"Average Forecast Accuracy: {df['FORECAST_ACCURACY'].mean():.2f}%")
print(f"Current Trend Slope: {df['LR_SLOPE_20'].iloc[-1]:.4f}")

# Volatility Analysis
recent_volatility = df['VAR_ZSCORE'].tail(20)
print(f"Recent Volatility Z-Score: {recent_volatility.mean():.2f}")
print(f"Volatility Regime: {df['VOLATILITY_SIGNAL'].iloc[-1]}")
```

### Advanced Statistical Analysis

```python
# Advanced correlation matrix
def calculate_correlation_matrix(df, period=20):
    """Calculate correlation matrix for OHLCV data"""
    correlations = {}
    
    price_cols = ['open', 'high', 'low', 'close', 'volume']
    
    for i, col1 in enumerate(price_cols):
        for col2 in price_cols[i+1:]:
            corr_name = f"CORR_{col1.upper()}_{col2.upper()}"
            correlations[corr_name] = ta.correlation(df[col1], df[col2], period)
    
    return correlations

# Calculate all correlations
correlations = calculate_correlation_matrix(df, 20)
for name, values in correlations.items():
    df[name] = values

print("\nCorrelation Matrix (Latest Values):")
corr_cols = [col for col in df.columns if col.startswith('CORR_')]
latest_corr = df[corr_cols].iloc[-1]
print(latest_corr)

# Statistical anomaly detection
def detect_statistical_anomalies(df, z_threshold=2.0):
    """Detect statistical anomalies in price data"""
    
    # Price anomalies based on variance z-score
    df['PRICE_ANOMALY'] = abs(df['VAR_ZSCORE']) > z_threshold
    
    # Volume anomalies
    volume_zscore = (df['volume'] - df['volume'].rolling(20).mean()) / df['volume'].rolling(20).std()
    df['VOLUME_ANOMALY'] = abs(volume_zscore) > z_threshold
    
    # Return anomalies
    returns = df['close'].pct_change()
    returns_zscore = (returns - returns.rolling(20).mean()) / returns.rolling(20).std()
    df['RETURN_ANOMALY'] = abs(returns_zscore) > z_threshold
    
    return df

# Detect anomalies
df = detect_statistical_anomalies(df)

# Summary of anomalies
anomaly_summary = df[['PRICE_ANOMALY', 'VOLUME_ANOMALY', 'RETURN_ANOMALY']].sum()
print(f"\nAnomaly Detection Summary:")
print(f"Price Anomalies: {anomaly_summary['PRICE_ANOMALY']}")
print(f"Volume Anomalies: {anomaly_summary['VOLUME_ANOMALY']}")
print(f"Return Anomalies: {anomaly_summary['RETURN_ANOMALY']}")
```

### Performance Tips

1. **Period Selection**: Choose appropriate periods based on your analysis timeframe
2. **Data Quality**: Ensure clean data for accurate statistical calculations
3. **Correlation Interpretation**: Remember correlation doesn't imply causation
4. **Statistical Significance**: Consider sample size when interpreting results
5. **Regime Changes**: Monitor for changes in statistical relationships over time

### Common Use Cases

1. **Trend Analysis**: Use Linear Regression and slopes for trend identification
2. **Risk Management**: Apply variance and correlation for portfolio risk assessment
3. **Anomaly Detection**: Use statistical z-scores to identify unusual market behavior
4. **Forecasting**: Combine TSF with other indicators for price prediction
5. **Market Relationships**: Analyze correlations between different assets or timeframes


---

# Agent Instructions: Querying This Documentation

If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.openalgo.in/trading-platform/python/indicators/statistical.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

```


---

# FILE: docs\prompt\symbol-format.md

```md
# Symbol Format

#### OpenAlgo Symbol Format Standardization

OpenAlgo standardizes financial instrument identification via a common symbol format across all exchanges and brokers, enhancing compatibility and simplifying automated trading. This uniform symbology eliminates the need for traders to adapt to varied broker-specific formats, streamlining algorithm development and execution. The format integrates key identifiers such as the base symbol, expiration date, and option type, ensuring consistent and error-free communication within trading systems. With OpenAlgo, developers can efficiently extend platform capabilities while traders focus on strategy, not syntax.

{% embed url="<https://www.youtube.com/watch?v=DcmDYpGYdJY>" %}

### Equity Symbol Format

In the context of OpenAlgo, equity symbols are constructed based on the base symbol of the stock.

**Examples:**

1. **NSE Equity for Infosys:** Given the base symbol `INFY`, the OpenAlgo symbol for Infosys on the National Stock Exchange (NSE) would be `INFY`.
2. **BSE Equity for Tata Motors:** With the base symbol `TATAMOTORS`, the symbol on the Bombay Stock Exchange (BSE) would be `TATAMOTORS`.
3. **NSE Equity for State Bank of India:** If the base symbol is `SBIN`, the OpenAlgo symbol on NSE would be `SBIN`.

### Future Symbol Format

For futures, the OpenAlgo symbology specifies that the symbol should consist of the base symbol followed by the expiration date and "FUT" to denote that it is a futures contract.

**Format:** `[Base Symbol][Expiration Date]FUT`

Below are the extended examples for various futures contracts:

**NSE Futures:**

* **Example:** For Bank Nifty futures expiring in April 2024, the symbol would be `BANKNIFTY24APR24FUT`.

**BSE Futures:**

* **Example:** For SENSEX futures expiring in April 2024, the symbol would be `SENSEX24APR24FUT`.

**Currency Futures:**

* **Example:** For USDINR currency futures expiring in May 2024, the symbol would be `USDINR10MAY24FUT`.

**MCX Futures:**

* **Example:** For crude oil futures on MCX expiring in May 2024, the symbol would be `CRUDEOILM20MAY24FUT`.

**IRC Futures:**

* **Example:** For government bond futures, specifically the 7.26% 2033 bond expiring in April 2024, the symbol in OpenAlgo would be `726GS203325APR24FUT`.

### Options Symbol Format

Options symbols in OpenAlgo are structured to include the base symbol, the expiration date, the strike price, and whether it's a Call or Put option.

**Format:** `[Base Symbol][Expiration Date][Strike Price][Option Type]`

**Examples:**

**NSE Index Options:**

* **Example:** For a Nifty call option with a strike price of 20,800, expiring on 28th March 2024, the symbol would be `NIFTY28MAR2420800CE`.

**NSE Stock Options:**

* **Example:** For a Vedanta Limited (VEDL) call option with a strike price of 292.50, expiring on 25th April 2024, the symbol would be `VEDL25APR24292.5CE`.

**Currency Options:**

* **Example:** For a US Dollar to Indian Rupee (USDINR) call option with a strike price of 82, expiring on 19th April 2024, the symbol would be `USDINR19APR2482CE`.

**MCX Options:**

* **Example:** For a Crude Oil call option with a strike price of 6,750, expiring on 17th April 2024, the symbol would be `CRUDEOIL17APR246750CE`.

**IRC Options:**

* **Example:** For an Goverent bond (726GS2032) put option with a strike price of 97, expiring on 25th April 2024, the symbol would be `726GS203225APR2497PE`.

### Common NSE Index Symbols (Exchange Code : NSE\_INDEX)

{% columns %}
{% column %}
NIFTY
\
NIFTYNXT50
\
FINNIFTY
\
BANKNIFTY
\
MIDCPNIFTY
\
INDIAVIX
\
HANGSENGBEESNAV
\
NIFTY100
\
NIFTY200
\
NIFTY500
\
NIFTYALPHA50
\
NIFTYAUTO
\
NIFTYCOMMODITIES
\
NIFTYCONSUMPTION
\
NIFTYCPSE
\
NIFTYDIVOPPS50
\
NIFTYENERGY
\
NIFTYFMCG
\
NIFTYGROWSECT15
\
NIFTYGS10YR
\
NIFTYGS10YRCLN
\
NIFTYGS1115YR
\
NIFTYGS15YRPLUS
\
NIFTYGS48YR
\
NIFTYGS813YR
\
NIFTYGSCOMPSITE
\
NIFTYINFRA
\
NIFTYIT
{% endcolumn %}

{% column %}
NIFTYMEDIA
\
NIFTYMETAL
\
NIFTYMIDLIQ15
\
NIFTYMIDCAP100
\
NIFTYMIDCAP150
\
NIFTYMIDCAP50
\
NIFTYMIDSML400
\
NIFTYMNC
\
NIFTYPHARMA
\
NIFTYPSE
\
NIFTYPSUBANK
\
NIFTYPVTBANK
\
NIFTYREALTY
\
NIFTYSERVSECTOR
\
NIFTYSMLCAP100
\
NIFTYSMLCAP250
\
NIFTYSMLCAP50
\
NIFTY100EQLWGT
\
NIFTY100LIQ15
\
NIFTY100LOWVOL30
\
NIFTY100QUALTY30
\
NIFTY200QUALTY30
\
NIFTY50DIVPOINT
\
NIFTY50EQLWGT
\
NIFTY50PR1XINV
\
NIFTY50PR2XLEV
\
NIFTY50TR1XINV
\
NIFTY50TR2XLEV
\
NIFTY50VALUE20
{% endcolumn %}
{% endcolumns %}

{% columns %}
{% column %}

{% endcolumn %}

{% column %}

{% endcolumn %}
{% endcolumns %}

### Common BSE Index Symbols (Exchange Code : BSE\_INDEX)

SENSEX
\
BANKEX
\
SENSEX50
\
BSE100
\
BSE150MIDCAPINDEX
\
BSE200
\
BSE250LARGEMIDCAPINDEX
\
BSE400MIDSMALLCAPINDEX
\
BSE500
\
BSEAUTO
\
BSECAPITALGOODS
\
BSECARBONEX
\
BSECONSUMERDURABLES
\
BSECPSE
\
BSEDOLLEX100
\
BSEDOLLEX200
\
BSEDOLLEX30
\
BSEENERGY
\
BSEFASTMOVINGCONSUMERGOODS
\
BSEFINANCIALSERVICES
\
BSEGREENEX
\
BSEHEALTHCARE
\
BSEINDIAINFRASTRUCTUREINDEX
\
BSEINDUSTRIALS
\
BSEINFORMATIONTECHNOLOGY
\
BSEIPO
\
BSELARGECAP
\
BSEMETAL
\
BSEMIDCAP
\
BSEMIDCAPSELECTINDEX
\
BSEOIL\&GAS
\
BSEPOWER
\
BSEPSU
\
BSEREALTY
\
BSESENSEXNEXT50
\
BSESMALLCAP
\
BSESMALLCAPSELECTINDEX
\
BSESMEIPO
\
BSETECK
\
BSETELECOM

### NCO Commodity Underlyings (Exchange Code : NCO)

NCO (NSE Commodities) hosts commodity futures and options on NSE. Currently supported by Zerodha. Underlying symbol list:

ALUMINIUMFUTURES\
ALUMINIUMMINIFUTURES\
BRENTCRUDEOIL\
BRENTCRUDEOILMINI\
COPPER\
CRUDEDEGUMSOYBEANOIL\
ELECTRICITYFUTURES\
GOLD\
GOLD10GM\
GOLD1GM\
GOLDGUINEA8GM\
GOLDMINI\
LEADFUTURES\
LEADMINIFUTURES\
NATURALGASHENRYHUB\
NATURALGASMINI\
NICKELFUTURES\
PLATTSDATEDBRENTASSESS\
SILVER\
SILVERMICRO\
SILVERMINI\
WTICRUDEOIL\
WTICRUDEOILMINI\
XAUGOLD\
ZINCFUTURES\
ZINCMINIFUTURES

**NCO Futures example:** `ALUMINI26MAYFUT` — `[Underlying][Expiration]FUT`

**NCO Options example:** `COPPER26MAY1195CE` — `[Underlying][Expiration][Strike][CE/PE]`

### MCX Index Symbols (Exchange Code : MCX\_INDEX)

MCX hosts a small set of index-only feeds (commodity sectoral indices). Currently sourced from Zerodha. Quote-only — these symbols are valid for `quotes`, `ltp`, `history`, `depth` and websocket subscriptions. The corresponding tradable index futures/options live on the regular `MCX` exchange (e.g. `MCXBULLDEX27MAY26FUT`).

MCXAGRI\
MCXBULLDEX\
MCXCOMDEX\
MCXCOMPDEX\
MCXCOPRDEX\
MCXCRUDEX\
MCXENERGY\
MCXGOLDEX\
MCXMETAL\
MCXMETLDEX\
MCXSILVDEX

### Common Global Index Symbols (Exchange Code : GLOBAL\_INDEX)

Quote-only feed for global indices. No trading is supported — use these symbols for `quotes`, `ltp`, `history`, and websocket subscriptions only. Currently sourced from Zerodha.

AUS200\
FRANCE40\
GERMANY40\
GIFTNIFTY\
HANGSENG\
JAPAN225\
SHANGHAICHINA\
UK100\
US100\
US10YRYIELD\
US30\
US500\
USCOMPOSITE

> `GIFTNIFTY` is sourced from NSE IFSC (broker-side exchange code `NSEIX`) but is exposed under `GLOBAL_INDEX` so users have a single bucket for all index-only quote feeds.

### Exchange  Codes

The supported exchange symbol formats in OpenAlgo allow for an identification system that denotes where the instrument is traded, along with specific details that vary by instrument type:

* **NSE:** `NSE` for National Stock Exchange equities.
* **BSE:** `BSE` for Bombay Stock Exchange equities.
* **NFO:** `NFO` for NSE Futures and Options.
* **BFO:** `BFO` for BSE Futures and Options.
* **BCD:** `BCD` for BSE Currency Derivatives.
* **CDS:** `CDS` for NSE Currency Derivatives.
* **MCX:** `MCX` for commodities traded on the Multi Commodity Exchange.
* **NCO:** `NCO` for NSE Commodities (futures + options). Zerodha only.
* **NSE\_INDEX:** `NSE_INDEX` for indices on the National Stock Exchange.
* **BSE\_INDEX:** `BSE_INDEX` for indices on the Bombay Stock Exchange.
* **MCX\_INDEX:** `MCX_INDEX` for MCX commodity sectoral indices (MCXBULLDEX, MCXMETLDEX, MCXAGRI, ...). Quote-only.
* **GLOBAL\_INDEX:** `GLOBAL_INDEX` for global indices (US30, JAPAN225, HANGSENG, FRANCE40, AUS200, GIFTNIFTY, ...). Quote-only. Zerodha only.

### Database Schema (Common Symbols)

For developers, understanding the database schema is essential for managing data effectively within OpenAlgo:

1. **id:** A unique identifier for each record in the database.
2. **symbol:** The standard trading symbol of the instrument as per OpenAlgo's symbology.
3. **brsymbol:** The broker-specific symbol for the instrument, if applicable.
4. **name:** The common name of the instrument (e.g., the company name for equities).
5. **exchange:** The standard exchange identifier code (e.g NSE, BSE, MCX CDS etc) where the instrument is traded as per OpenAlgo's symbology.
6. **brexchange:** The specific broker exchange identifier, if different from the standard exchange code.
7. **token:** A unique token or code assigned to the instrument, possibly for internal tracking or broker-specific identification.
8. **expiry:** The expiration date for derivatives contracts, formatted as per broker/exchange standards.
9. **strike:** The strike price for options contracts.
10. **lotsize:** The standardized lot size for the instrument, particularly relevant for derivatives trading.
11. **instrumenttype:** The type of instrument (e.g., equity, future, option).
12. **tick\_size:** The minimum price movement of the instrument on the exchange.

<figure><img src="https://17901342-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FmBwEhITzgv0O0fEGIIRN%2Fuploads%2FvUWO49dLv5Pklo6qPtIV%2Fimage.png?alt=media&#x26;token=7cea9426-f5b9-4c29-b29f-a2e4b9ea7030" alt=""><figcaption></figcaption></figure>

This schema captures both the standardized OpenAlgo symbology and the potentially divergent broker-specific information, enabling algorithms and traders to operate across multiple platforms without confusion. It allows for the storage of instrument metadata necessary for trading activities and ensures that all financial instruments are identifiable and their market details readily accessible.


---

# Agent Instructions: Querying This Documentation

If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.openalgo.in/symbol-format.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

```


---

# FILE: docs\prompt\trend - openalgo indicators.md

```md
# Trend

Trend indicators help identify the direction and strength of market trends. All examples use real market data fetched via OpenAlgo API.

### Data Setup

```python
from openalgo import api, ta
import pandas as pd

# Initialize API client
client = api(api_key='your_api_key_here', host='http://127.0.0.1:5000')

# Fetch historical data
df = client.history(symbol="SBIN", 
                   exchange="NSE", 
                   interval="5m", 
                   start_date="2025-04-01", 
                   end_date="2025-04-08")

print(df.head())
#                            close    high     low    open  volume
# timestamp                                                        
# 2025-04-01 09:15:00+05:30  772.50  774.00  763.20  766.50  318625
# 2025-04-01 09:20:00+05:30  773.20  774.95  772.10  772.45  197189
```

***

### Simple Moving Average (SMA)

**Description**: The most basic trend indicator, calculated by averaging closing prices over a specified period.

#### Parameters

* **data** *(array-like)*: Price data (typically closing prices)
* **period** *(int)*: Number of periods for the moving average

#### Returns

* **pandas.Series**: SMA values with original index preserved

#### Usage Example

```python
# Calculate 20-period SMA
df['SMA_20'] = ta.sma(df['close'], 20)

# Calculate multiple SMAs
df['SMA_10'] = ta.sma(df['close'], 10)
df['SMA_50'] = ta.sma(df['close'], 50)

print(df[['close', 'SMA_10', 'SMA_20', 'SMA_50']].tail())
#                            close   SMA_10   SMA_20   SMA_50
# timestamp                                                  
# 2025-04-08 14:00:00+05:30  768.25  770.12  771.45  773.28
# 2025-04-08 14:05:00+05:30  769.10  769.98  771.33  773.22
```

***

### Exponential Moving Average (EMA)

**Description**: Gives more weight to recent prices, making it more responsive to new information than SMA.

#### Parameters

* **data** *(array-like)*: Price data (typically closing prices)
* **period** *(int)*: Number of periods for the moving average

#### Returns

* **pandas.Series**: EMA values with original index preserved

#### Usage Example

```python
# Calculate 20-period EMA
df['EMA_20'] = ta.ema(df['close'], 20)

# Compare with SMA
df['SMA_20'] = ta.sma(df['close'], 20)

# Plot comparison
import matplotlib.pyplot as plt
plt.figure(figsize=(12, 6))
plt.plot(df.index, df['close'], label='Close Price', alpha=0.7)
plt.plot(df.index, df['SMA_20'], label='SMA 20', alpha=0.8)
plt.plot(df.index, df['EMA_20'], label='EMA 20', alpha=0.8)
plt.legend()
plt.title('SBIN: Close Price vs Moving Averages')
plt.show()
```

***

### Weighted Moving Average (WMA)

**Description**: Assigns greater weight to recent data points using a linear weighting scheme.

#### Parameters

* **data** *(array-like)*: Price data (typically closing prices)
* **period** *(int)*: Number of periods for the moving average

#### Returns

* **numpy.ndarray**: WMA values

#### Usage Example

```python
# Calculate 20-period WMA
df['WMA_20'] = ta.wma(df['close'], 20)

# Compare responsiveness of different MAs
df['MA_Comparison'] = df['close'] - df['SMA_20']
df['EMA_Comparison'] = df['close'] - df['EMA_20'] 
df['WMA_Comparison'] = df['close'] - df['WMA_20']

print(df[['MA_Comparison', 'EMA_Comparison', 'WMA_Comparison']].tail())
```

***

### Hull Moving Average (HMA)

**Description**: Attempts to minimize lag while improving smoothing using weighted moving averages.

#### Parameters

* **data** *(array-like)*: Price data (typically closing prices)
* **period** *(int)*: Number of periods for the moving average

#### Returns

* **pandas.Series**: HMA values with original index preserved

#### Usage Example

```python
# Calculate 16-period HMA (common period for HMA)
df['HMA_16'] = ta.hma(df['close'], 16)

# Compare lag between different MAs
df['Price_Change'] = df['close'].pct_change()
df['HMA_Change'] = df['HMA_16'].pct_change()
df['EMA_Change'] = df['EMA_20'].pct_change()

# Calculate correlation to measure responsiveness
correlation_hma = df['Price_Change'].corr(df['HMA_Change'])
correlation_ema = df['Price_Change'].corr(df['EMA_Change'])
print(f"HMA Correlation: {correlation_hma:.4f}")
print(f"EMA Correlation: {correlation_ema:.4f}")
```

***

### Volume Weighted Moving Average (VWMA)

**Description**: Gives more weight to periods with higher volume, making it more responsive to volume-driven price movements.

#### Parameters

* **data** *(array-like)*: Price data (typically closing prices)
* **volume** *(array-like)*: Volume data
* **period** *(int)*: Number of periods for the moving average

#### Returns

* **pandas.Series**: VWMA values with original index preserved

#### Usage Example

```python
# Calculate 20-period VWMA
df['VWMA_20'] = ta.vwma(df['close'], df['volume'], 20)

# Compare VWMA with regular SMA during high/low volume periods
df['Volume_MA'] = ta.sma(df['volume'], 20)
df['High_Volume'] = df['volume'] > df['Volume_MA']

# Analyze performance during high volume periods
high_vol_periods = df[df['High_Volume'] == True]
print("VWMA vs SMA during high volume periods:")
print(high_vol_periods[['close', 'SMA_20', 'VWMA_20', 'volume']].tail())
```

***

### Kaufman's Adaptive Moving Average (KAMA)

**Description**: Adjusts its smoothing based on market volatility, becoming more responsive in trending markets and smoother in sideways markets.

#### Parameters

* **data** *(array-like)*: Price data (typically closing prices)
* **length** *(int, default=14)*: Period for efficiency ratio calculation
* **fast\_length** *(int, default=2)*: Fast EMA length
* **slow\_length** *(int, default=30)*: Slow EMA length

#### Returns

* **pandas.Series**: KAMA values with original index preserved

#### Usage Example

```python
# Calculate KAMA with default parameters
df['KAMA_14'] = ta.kama(df['close'])

# Calculate market efficiency ratio manually for analysis
def calculate_efficiency_ratio(prices, period):
    direction = abs(prices.iloc[-1] - prices.iloc[-period-1])
    volatility = abs(prices.diff()).rolling(period).sum().iloc[-1]
    return direction / volatility if volatility > 0 else 0

# Analyze KAMA adaptation
df['ER'] = df['close'].rolling(14).apply(lambda x: calculate_efficiency_ratio(x, 14))
df['KAMA_vs_Close'] = abs(df['KAMA_14'] - df['close'])

print("KAMA Efficiency and Adaptation:")
print(df[['close', 'KAMA_14', 'ER', 'KAMA_vs_Close']].tail(10))
```

***

### Supertrend

**Description**: A trend-following indicator that uses ATR to calculate dynamic support and resistance levels.

#### Parameters

* **high** *(array-like)*: High prices
* **low** *(array-like)*: Low prices
* **close** *(array-like)*: Closing prices
* **period** *(int, default=10)*: ATR period
* **multiplier** *(float, default=3.0)*: ATR multiplier

#### Returns

* **tuple**: (supertrend\_values, direction\_values) as pandas.Series
  * **direction**: -1 for uptrend (green), 1 for downtrend (red)

#### Usage Example

```python
# Calculate Supertrend with default parameters
df['Supertrend'], df['ST_Direction'] = ta.supertrend(df['high'], df['low'], df['close'])

# Calculate custom Supertrend for shorter timeframes
df['ST_Fast'], df['ST_Fast_Dir'] = ta.supertrend(df['high'], df['low'], df['close'], 
                                                period=7, multiplier=2.0)

# Identify trend changes
df['Trend_Change'] = df['ST_Direction'].diff() != 0

# Analyze trend statistics
uptrend_periods = len(df[df['ST_Direction'] == -1])
downtrend_periods = len(df[df['ST_Direction'] == 1])
trend_changes = df['Trend_Change'].sum()

print(f"Uptrend periods: {uptrend_periods}")
print(f"Downtrend periods: {downtrend_periods}")
print(f"Trend changes: {trend_changes}")

# Show recent Supertrend signals
print("\nRecent Supertrend Data:")
print(df[['close', 'Supertrend', 'ST_Direction']].tail())
```

***

### Ichimoku Cloud

**Description**: A comprehensive indicator that defines support and resistance, identifies trend direction, and provides trading signals.

#### Parameters

* **high** *(array-like)*: High prices
* **low** *(array-like)*: Low prices
* **close** *(array-like)*: Closing prices
* **conversion\_periods** *(int, default=9)*: Conversion Line Length
* **base\_periods** *(int, default=26)*: Base Line Length
* **lagging\_span2\_periods** *(int, default=52)*: Leading Span B Length
* **displacement** *(int, default=26)*: Lagging Span displacement

#### Returns

* **tuple**: (conversion\_line, base\_line, leading\_span\_a, leading\_span\_b, lagging\_span) as pandas.Series

#### Usage Example

```python
# Calculate Ichimoku Cloud components
(df['Ichimoku_Conversion'], 
 df['Ichimoku_Base'], 
 df['Ichimoku_SpanA'], 
 df['Ichimoku_SpanB'], 
 df['Ichimoku_Lagging']) = ta.ichimoku(df['high'], df['low'], df['close'])

# Analyze cloud signals
df['Cloud_Top'] = df[['Ichimoku_SpanA', 'Ichimoku_SpanB']].max(axis=1)
df['Cloud_Bottom'] = df[['Ichimoku_SpanA', 'Ichimoku_SpanB']].min(axis=1)
df['Above_Cloud'] = df['close'] > df['Cloud_Top']
df['Below_Cloud'] = df['close'] < df['Cloud_Bottom']
df['In_Cloud'] = ~(df['Above_Cloud'] | df['Below_Cloud'])

# TK Cross signals
df['TK_Bullish'] = (df['Ichimoku_Conversion'] > df['Ichimoku_Base']) & \
                   (df['Ichimoku_Conversion'].shift(1) <= df['Ichimoku_Base'].shift(1))
df['TK_Bearish'] = (df['Ichimoku_Conversion'] < df['Ichimoku_Base']) & \
                   (df['Ichimoku_Conversion'].shift(1) >= df['Ichimoku_Base'].shift(1))

print("Ichimoku Analysis:")
print(f"Periods above cloud: {df['Above_Cloud'].sum()}")
print(f"Periods below cloud: {df['Below_Cloud'].sum()}")
print(f"Periods in cloud: {df['In_Cloud'].sum()}")
print(f"TK Bullish signals: {df['TK_Bullish'].sum()}")
print(f"TK Bearish signals: {df['TK_Bearish'].sum()}")
```

***

### Arnaud Legoux Moving Average (ALMA)

**Description**: Combines the features of SMA and EMA with a configurable phase and smoothing factor.

#### Parameters

* **data** *(array-like)*: Price data (typically closing prices)
* **period** *(int, default=21)*: Number of periods for the moving average
* **offset** *(float, default=0.85)*: Phase offset (0 to 1)
* **sigma** *(float, default=6.0)*: Smoothing factor

#### Returns

* **pandas.Series**: ALMA values with original index preserved

#### Usage Example

```python
# Calculate ALMA with different configurations
df['ALMA_Default'] = ta.alma(df['close'])  # Default: period=21, offset=0.85, sigma=6.0
df['ALMA_Fast'] = ta.alma(df['close'], period=14, offset=0.9, sigma=4.0)
df['ALMA_Smooth'] = ta.alma(df['close'], period=21, offset=0.5, sigma=8.0)

# Compare responsiveness
df['ALMA_vs_EMA'] = df['ALMA_Default'] - ta.ema(df['close'], 21)
print("ALMA vs EMA difference (last 10 periods):")
print(df['ALMA_vs_EMA'].tail(10))
```

***

### Zero Lag Exponential Moving Average (ZLEMA)

**Description**: Attempts to eliminate lag by using price momentum in its calculation.

#### Parameters

* **data** *(array-like)*: Price data (typically closing prices)
* **period** *(int)*: Number of periods for the moving average

#### Returns

* **pandas.Series**: ZLEMA values with original index preserved

#### Usage Example

```python
# Calculate ZLEMA and compare with regular EMA
df['ZLEMA_20'] = ta.zlema(df['close'], 20)
df['EMA_20'] = ta.ema(df['close'], 20)

# Measure responsiveness to price changes
df['Price_Change'] = df['close'].diff()
df['ZLEMA_Change'] = df['ZLEMA_20'].diff()
df['EMA_Change'] = df['EMA_20'].diff()

# Calculate lead/lag relationship
correlation_zlema = df['Price_Change'].corr(df['ZLEMA_Change'])
correlation_ema = df['Price_Change'].corr(df['EMA_Change'])

print(f"ZLEMA responsiveness: {correlation_zlema:.4f}")
print(f"EMA responsiveness: {correlation_ema:.4f}")
```

***

### Multiple Exponential Moving Average (DEMA & TEMA)

**Description**: DEMA and TEMA reduce lag by applying exponential smoothing multiple times.

#### Parameters

* **data** *(array-like)*: Price data (typically closing prices)
* **period** *(int)*: Number of periods for the moving average

#### Returns

* **pandas.Series**: DEMA/TEMA values with original index preserved

#### Usage Example

```python
# Calculate DEMA and TEMA
df['DEMA_20'] = ta.dema(df['close'], 20)
df['TEMA_20'] = ta.tema(df['close'], 20)
df['EMA_20'] = ta.ema(df['close'], 20)

# Compare lag characteristics
price_peaks = df['close'].rolling(5).max() == df['close']
df['Peak_Signals'] = price_peaks

# Analyze how quickly each MA responds to peaks
peak_periods = df[df['Peak_Signals']]
print("Response at price peaks:")
print(peak_periods[['close', 'EMA_20', 'DEMA_20', 'TEMA_20']].tail())
```

***

### Complete Trading Analysis Example

```python
from openalgo import api, ta
import pandas as pd
import matplotlib.pyplot as plt

# Fetch data
client = api(api_key='your_api_key_here', host='http://127.0.0.1:5000')
df = client.history(symbol="SBIN", exchange="NSE", interval="5m", 
                   start_date="2025-04-01", end_date="2025-04-08")

# Calculate multiple trend indicators
df['SMA_20'] = ta.sma(df['close'], 20)
df['EMA_20'] = ta.ema(df['close'], 20)
df['KAMA_14'] = ta.kama(df['close'])
df['Supertrend'], df['ST_Direction'] = ta.supertrend(df['high'], df['low'], df['close'])

# Calculate Ichimoku components
(df['Conversion'], df['Base'], df['SpanA'], 
 df['SpanB'], df['Lagging']) = ta.ichimoku(df['high'], df['low'], df['close'])

# Generate trading signals
df['MA_Bullish'] = (df['close'] > df['SMA_20']) & (df['EMA_20'] > df['SMA_20'])
df['ST_Bullish'] = df['ST_Direction'] == -1
df['Ichimoku_Bullish'] = (df['close'] > df[['SpanA', 'SpanB']].max(axis=1)) & \
                         (df['Conversion'] > df['Base'])

# Combined signal
df['Combined_Signal'] = (df['MA_Bullish'] & df['ST_Bullish'] & df['Ichimoku_Bullish']).astype(int)

# Performance analysis
signal_changes = df['Combined_Signal'].diff()
buy_signals = signal_changes == 1
sell_signals = signal_changes == -1

print(f"Buy signals: {buy_signals.sum()}")
print(f"Sell signals: {sell_signals.sum()}")

# Show recent analysis
print("\nRecent Trading Analysis:")
columns_to_show = ['close', 'SMA_20', 'EMA_20', 'Supertrend', 'ST_Direction', 'Combined_Signal']
print(df[columns_to_show].tail(10))

# Plot results
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)

# Price and moving averages
ax1.plot(df.index, df['close'], label='Close', linewidth=1)
ax1.plot(df.index, df['SMA_20'], label='SMA 20', alpha=0.7)
ax1.plot(df.index, df['EMA_20'], label='EMA 20', alpha=0.7)
ax1.plot(df.index, df['Supertrend'], label='Supertrend', alpha=0.8)
ax1.legend()
ax1.set_title('SBIN Price and Trend Indicators')
ax1.grid(True, alpha=0.3)

# Signals
ax2.plot(df.index, df['Combined_Signal'], label='Combined Signal', linewidth=2)
ax2.fill_between(df.index, 0, df['Combined_Signal'], alpha=0.3)
ax2.set_ylabel('Signal')
ax2.set_xlabel('Time')
ax2.set_title('Combined Trading Signals')
ax2.grid(True, alpha=0.3)
ax2.legend()

plt.tight_layout()
plt.show()
```

This documentation demonstrates how to use OpenAlgo trend indicators with real market data fetched via the OpenAlgo API, maintaining pandas DataFrame structure throughout the analysis process.


---

# Agent Instructions: Querying This Documentation

If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.openalgo.in/trading-platform/python/indicators/trend.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

```


---

# FILE: docs\prompt\utility - openalgo indicators.md

```md
# Utility

## OpenAlgo Utility Indicators Documentation

Utility indicators provide essential market analysis functions for signal detection, condition checking, and mathematical operations. These functions are fundamental building blocks for creating trading strategies and market analysis systems.

### Import Statement

```python
from openalgo import ta, api
```

### Sample Data Setup

```python
# Initialize API client
client = api(api_key='your_api_key_here', host='http://127.0.0.1:5000')

# Fetch historical data
df = client.history(symbol="SBIN", 
                   exchange="NSE", 
                   interval="5m", 
                   start_date="2025-04-01", 
                   end_date="2025-04-08")

# Extract price series
close = df['close']
high = df['high']
low = df['low']
open_prices = df['open']
volume = df['volume']
```

***

### Signal Detection Utilities

#### Crossover

Detects when one series crosses above another series. Essential for identifying bullish signal points.

**Usage**

```python
crossover_signals = ta.crossover(series1, series2)
```

**Parameters**

* **series1** *(array-like)*: First series (typically fast indicator)
* **series2** *(array-like)*: Second series (typically slow indicator)

**Returns**

* **array**: Boolean array indicating crossover points (True where crossover occurs)

**Example**

```python
# Calculate moving averages
sma_10 = ta.sma(close, 10)
sma_20 = ta.sma(close, 20)

# Detect when SMA(10) crosses above SMA(20)
bullish_signals = ta.crossover(sma_10, sma_20)

# Find crossover points
crossover_points = df[bullish_signals]
print("Bullish crossover signals:")
print(crossover_points[['close']].head())
```

***

#### Crossunder

Detects when one series crosses below another series. Used for identifying bearish signal points.

**Usage**

```python
crossunder_signals = ta.crossunder(series1, series2)
```

**Parameters**

* **series1** *(array-like)*: First series (typically fast indicator)
* **series2** *(array-like)*: Second series (typically slow indicator)

**Returns**

* **array**: Boolean array indicating crossunder points (True where crossunder occurs)

**Example**

```python
# Detect when SMA(10) crosses below SMA(20)
bearish_signals = ta.crossunder(sma_10, sma_20)

# Find crossunder points
crossunder_points = df[bearish_signals]
print("Bearish crossunder signals:")
print(crossunder_points[['close']].head())
```

***

#### Cross

Detects when one series crosses another in either direction (combines crossover and crossunder).

**Usage**

```python
cross_signals = ta.cross(series1, series2)
```

**Parameters**

* **series1** *(array-like)*: First series
* **series2** *(array-like)*: Second series

**Returns**

* **array**: Boolean array indicating any cross points (both over and under)

**Example**

```python
# Detect any crossing between price and moving average
price_ma_cross = ta.cross(close, sma_20)

# Find all crossing points
all_crosses = df[price_ma_cross]
print("All price/MA crossing points:")
print(all_crosses[['close']].head())
```

***

### Range and Extremes

#### Highest

Finds the highest value over a rolling window.

**Usage**

```python
highest_values = ta.highest(data, period)
```

**Parameters**

* **data** *(array-like)*: Input data series
* **period** *(int)*: Window size for finding highest value

**Returns**

* **array**: Array of highest values over the specified period

**Example**

```python
# Find highest high over last 20 periods
highest_20 = ta.highest(high, 20)

# Create resistance levels
df['Resistance_20'] = highest_20
print("Recent resistance levels:")
print(df[['high', 'Resistance_20']].tail())
```

***

#### Lowest

Finds the lowest value over a rolling window.

**Usage**

```python
lowest_values = ta.lowest(data, period)
```

**Parameters**

* **data** *(array-like)*: Input data series
* **period** *(int)*: Window size for finding lowest value

**Returns**

* **array**: Array of lowest values over the specified period

**Example**

```python
# Find lowest low over last 20 periods
lowest_20 = ta.lowest(low, 20)

# Create support levels
df['Support_20'] = lowest_20
print("Recent support levels:")
print(df[['low', 'Support_20']].tail())
```

***

### Change and Rate Calculations

#### Change

Calculates the change in value over a specified number of periods.

**Usage**

```python
change_values = ta.change(data, length=1)
```

**Parameters**

* **data** *(array-like)*: Input data series
* **length** *(int, default=1)*: Number of periods to look back

**Returns**

* **array**: Array of change values

**Example**

```python
# Calculate 1-period change (price difference)
price_change_1 = ta.change(close, 1)

# Calculate 5-period change
price_change_5 = ta.change(close, 5)

# Add to dataframe
df['Change_1'] = price_change_1
df['Change_5'] = price_change_5
print("Price changes:")
print(df[['close', 'Change_1', 'Change_5']].tail())
```

***

#### Rate of Change (ROC)

Calculates the rate of change as a percentage.

**Usage**

```python
roc_values = ta.roc(data, length)
```

**Parameters**

* **data** *(array-like)*: Input data series
* **length** *(int)*: Number of periods to look back

**Returns**

* **array**: Array of ROC values as percentages

**Example**

```python
# Calculate 10-period rate of change
roc_10 = ta.roc(close, 10)

# Calculate 20-period rate of change
roc_20 = ta.roc(close, 20)

df['ROC_10'] = roc_10
df['ROC_20'] = roc_20
print("Rate of change analysis:")
print(df[['close', 'ROC_10', 'ROC_20']].tail())
```

***

### Statistical Utilities

#### Standard Deviation

Calculates rolling standard deviation for volatility measurement.

**Usage**

```python
stdev_values = ta.stdev(data, period)
```

**Parameters**

* **data** *(array-like)*: Input data series
* **period** *(int)*: Window size for standard deviation calculation

**Returns**

* **array**: Array of standard deviation values

**Example**

```python
# Calculate 20-period standard deviation
volatility_20 = ta.stdev(close, 20)

# Calculate relative volatility
relative_volatility = volatility_20 / close * 100

df['Volatility_20'] = volatility_20
df['Rel_Volatility'] = relative_volatility
print("Volatility analysis:")
print(df[['close', 'Volatility_20', 'Rel_Volatility']].tail())
```

***

### Trend Direction Utilities

#### Rising

Checks if data is rising (current value > value n periods ago).

**Usage**

```python
rising_condition = ta.rising(data, length)
```

**Parameters**

* **data** *(array-like)*: Input data series
* **length** *(int)*: Number of periods to look back

**Returns**

* **array**: Boolean array indicating rising periods

**Example**

```python
# Check if price is rising over 5 periods
price_rising_5 = ta.rising(close, 5)

# Check if volume is rising over 3 periods
volume_rising_3 = ta.rising(volume, 3)

# Combine conditions for strong bullish signal
strong_bullish = price_rising_5 & volume_rising_3

df['Price_Rising_5'] = price_rising_5
df['Volume_Rising_3'] = volume_rising_3
df['Strong_Bullish'] = strong_bullish

print("Rising trend analysis:")
print(df[['close', 'volume', 'Price_Rising_5', 'Volume_Rising_3', 'Strong_Bullish']].tail())
```

***

#### Falling

Checks if data is falling (current value < value n periods ago).

**Usage**

```python
falling_condition = ta.falling(data, length)
```

**Parameters**

* **data** *(array-like)*: Input data series
* **length** *(int)*: Number of periods to look back

**Returns**

* **array**: Boolean array indicating falling periods

**Example**

```python
# Check if price is falling over 5 periods
price_falling_5 = ta.falling(close, 5)

# Check if price is falling but volume is rising (potential reversal)
potential_reversal = price_falling_5 & volume_rising_3

df['Price_Falling_5'] = price_falling_5
df['Potential_Reversal'] = potential_reversal

print("Falling trend analysis:")
print(df[['close', 'Price_Falling_5', 'Potential_Reversal']].tail())
```

***

### Advanced Signal Processing

#### Excess Removal (ExRem)

Eliminates excessive signals by ensuring alternating signal types.

**Usage**

```python
filtered_signals = ta.exrem(primary_signals, secondary_signals)
```

**Parameters**

* **primary\_signals** *(array-like)*: Primary signal array (boolean-like)
* **secondary\_signals** *(array-like)*: Secondary signal array (boolean-like)

**Returns**

* **array**: Boolean array with excess signals removed

**Example**

```python
# Generate buy and sell signals
buy_signals = ta.crossover(sma_10, sma_20)
sell_signals = ta.crossunder(sma_10, sma_20)

# Remove excessive buy signals (only allow buy after sell)
filtered_buys = ta.exrem(buy_signals, sell_signals)

# Remove excessive sell signals (only allow sell after buy)
filtered_sells = ta.exrem(sell_signals, buy_signals)

df['Raw_Buy'] = buy_signals
df['Raw_Sell'] = sell_signals
df['Filtered_Buy'] = filtered_buys
df['Filtered_Sell'] = filtered_sells

print("Signal filtering comparison:")
print(df[['close', 'Raw_Buy', 'Raw_Sell', 'Filtered_Buy', 'Filtered_Sell']].tail(20))
```

***

#### Flip

Creates a toggle state based on two signals.

**Usage**

```python
state_array = ta.flip(primary_signals, secondary_signals)
```

**Parameters**

* **primary\_signals** *(array-like)*: Primary signal array (boolean-like)
* **secondary\_signals** *(array-like)*: Secondary signal array (boolean-like)

**Returns**

* **array**: Boolean array representing flip state

**Example**

```python
# Create a position state indicator
position_state = ta.flip(filtered_buys, filtered_sells)

# Calculate position returns
df['Position_State'] = position_state
df['Daily_Return'] = close.pct_change()
df['Strategy_Return'] = df['Daily_Return'] * df['Position_State'].shift(1)

print("Position state analysis:")
print(df[['close', 'Position_State', 'Daily_Return', 'Strategy_Return']].tail())
```

***

#### Value When

Returns the value of an array when a condition was true for the nth most recent time.

**Usage**

```python
conditional_values = ta.valuewhen(condition_array, value_array, n=1)
```

**Parameters**

* **condition\_array** *(array-like)*: Expression array (boolean-like)
* **value\_array** *(array-like)*: Value array to sample from
* **n** *(int, default=1)*: Which occurrence to get (1 = most recent)

**Returns**

* **array**: Array of values when condition was true

**Example**

```python
# Get the close price when buy signals occurred
buy_prices = ta.valuewhen(filtered_buys, close, 1)

# Get the close price from 2 buy signals ago
previous_buy_prices = ta.valuewhen(filtered_buys, close, 2)

# Calculate profit potential from last buy
profit_potential = (close - buy_prices) / buy_prices * 100

df['Last_Buy_Price'] = buy_prices
df['Profit_Potential'] = profit_potential

print("Buy price tracking:")
print(df[['close', 'Filtered_Buy', 'Last_Buy_Price', 'Profit_Potential']].tail())
```

***

### Complete Utility Example: Trading Signal System

```python
import pandas as pd
from openalgo import ta, api

# Fetch data
client = api(api_key='your_api_key_here', host='http://127.0.0.1:5000')
df = client.history(symbol="SBIN", exchange="NSE", interval="5m", 
                   start_date="2025-04-01", end_date="2025-04-08")

close = df['close']
high = df['high']
low = df['low']
volume = df['volume']

# Calculate indicators
sma_10 = ta.sma(close, 10)
sma_20 = ta.sma(close, 20)
rsi = ta.rsi(close, 14)

# Generate basic signals
ma_bullish = ta.crossover(sma_10, sma_20)
ma_bearish = ta.crossunder(sma_10, sma_20)

# Add conditions for signal quality
price_rising = ta.rising(close, 3)
volume_rising = ta.rising(volume, 3)
volatility = ta.stdev(close, 20)
roc_5 = ta.roc(close, 5)

# Enhanced signal conditions
strong_bullish = ma_bullish & price_rising & volume_rising & (rsi < 70)
strong_bearish = ma_bearish & ta.falling(close, 3) & (rsi > 30)

# Filter signals to avoid excessive entries
filtered_long = ta.exrem(strong_bullish, strong_bearish)
filtered_short = ta.exrem(strong_bearish, strong_bullish)

# Create position state
position_long = ta.flip(filtered_long, filtered_short)

# Track entry prices and stops
entry_prices = ta.valuewhen(filtered_long, close, 1)
stop_levels = ta.lowest(low, 10)

# Calculate unrealized P&L for long positions
unrealized_pnl = ((close - entry_prices) / entry_prices * 100) * position_long

# Combine all analysis
df_analysis = pd.DataFrame({
    'Close': close,
    'SMA_10': sma_10,
    'SMA_20': sma_20,
    'RSI': rsi,
    'ROC_5': roc_5,
    'Volatility': volatility,
    'Strong_Bullish': strong_bullish,
    'Strong_Bearish': strong_bearish,
    'Filtered_Long': filtered_long,
    'Filtered_Short': filtered_short,
    'Position_Long': position_long,
    'Entry_Price': entry_prices,
    'Stop_Level': stop_levels,
    'Unrealized_PnL': unrealized_pnl
})

# Display signal summary
print("=== Trading Signal Analysis ===")
print(f"Total Long Signals: {filtered_long.sum()}")
print(f"Total Short Signals: {filtered_short.sum()}")
print(f"Current Position: {'LONG' if position_long.iloc[-1] else 'FLAT'}")

if position_long.iloc[-1]:
    print(f"Entry Price: {entry_prices.iloc[-1]:.2f}")
    print(f"Current Price: {close.iloc[-1]:.2f}")
    print(f"Unrealized P&L: {unrealized_pnl.iloc[-1]:.2f}%")
    print(f"Stop Level: {stop_levels.iloc[-1]:.2f}")

print("\nRecent signals:")
signal_points = df_analysis[filtered_long | filtered_short].tail()
print(signal_points[['Close', 'RSI', 'Filtered_Long', 'Filtered_Short']])
```

### Best Practices for Utility Functions

1. **Signal Filtering**: Always use `exrem()` to filter excessive signals
2. **State Management**: Use `flip()` to maintain position states
3. **Condition Combining**: Combine multiple utilities for robust signal generation
4. **Historical Reference**: Use `valuewhen()` to track important price levels
5. **Trend Confirmation**: Use `rising()` and `falling()` to confirm trend direction

### Common Signal Patterns

1. **Momentum Confirmation**: `crossover() + rising() + volume_confirmation`
2. **Reversal Detection**: `falling() + oversold_condition + volume_spike`
3. **Breakout Validation**: `cross() + highest()/lowest() + volatility_expansion`
4. **Trend Following**: `flip() + moving_average_alignment + momentum_filter`


---

# Agent Instructions: Querying This Documentation

If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.openalgo.in/trading-platform/python/indicators/utility.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

```


---

# FILE: docs\prompt\volatility - openalgo indicators.md

```md
# Volatility

Volatility indicators measure the degree of price variation in financial instruments. They help traders assess market uncertainty, risk levels, and potential breakout conditions. OpenAlgo provides a comprehensive collection of volatility indicators optimized for performance and accuracy.

### Import Statement

```python
from openalgo import ta
from openalgo import api

# Initialize API client
client = api(api_key='your_api_key_here', host='http://127.0.0.1:5000')

# Get sample data
df = client.history(symbol="SBIN", exchange="NSE", interval="5m", 
                   start_date="2025-04-01", end_date="2025-04-08")
```

### Available Volatility Indicators

***

### Average True Range (ATR)

ATR measures market volatility by decomposing the entire range of an asset price for that period. It's one of the most widely used volatility indicators.

#### Usage

```python
atr_result = ta.atr(high, low, close, period=14)
```

#### Parameters

* **high** *(array-like)*: High prices
* **low** *(array-like)*: Low prices
* **close** *(array-like)*: Closing prices
* **period** *(int, default=14)*: Number of periods for ATR calculation

#### Returns

* **array**: ATR values in the same format as input

#### Example

```python
# Calculate 14-period ATR
atr_14 = ta.atr(df['high'], df['low'], df['close'], period=14)
df['ATR_14'] = atr_14

# Calculate 21-period ATR
atr_21 = ta.atr(df['high'], df['low'], df['close'], period=21)
df['ATR_21'] = atr_21

print(df[['close', 'ATR_14', 'ATR_21']].tail())
```

***

### Bollinger Bands

Bollinger Bands consist of a middle band (SMA) and two outer bands that are standard deviations away from the middle band, used to identify overbought and oversold conditions.

#### Usage

```python
upper, middle, lower = ta.bbands(data, period=20, std_dev=2.0)
```

#### Parameters

* **data** *(array-like)*: Price data (typically closing prices)
* **period** *(int, default=20)*: Number of periods for moving average and standard deviation
* **std\_dev** *(float, default=2.0)*: Number of standard deviations for the bands

#### Returns

* **tuple**: (upper\_band, middle\_band, lower\_band) arrays

#### Example

```python
# Calculate Bollinger Bands
bb_upper, bb_middle, bb_lower = ta.bbands(df['close'], period=20, std_dev=2.0)
df['BB_Upper'] = bb_upper
df['BB_Middle'] = bb_middle
df['BB_Lower'] = bb_lower

# Calculate tighter bands
bb_upper_tight, bb_middle_tight, bb_lower_tight = ta.bbands(df['close'], period=20, std_dev=1.5)
df['BB_Upper_Tight'] = bb_upper_tight
df['BB_Lower_Tight'] = bb_lower_tight

print(df[['close', 'BB_Upper', 'BB_Middle', 'BB_Lower']].tail())
```

***

### Keltner Channel

Keltner Channels are volatility-based envelopes set above and below an exponential moving average, using ATR to set channel distance.

#### Usage

```python
upper, middle, lower = ta.keltner(high, low, close, ema_period=20, atr_period=10, multiplier=2.0)
```

#### Parameters

* **high** *(array-like)*: High prices
* **low** *(array-like)*: Low prices
* **close** *(array-like)*: Closing prices
* **ema\_period** *(int, default=20)*: Period for the EMA calculation
* **atr\_period** *(int, default=10)*: Period for the ATR calculation
* **multiplier** *(float, default=2.0)*: Multiplier for the ATR

#### Returns

* **tuple**: (upper\_channel, middle\_line, lower\_channel) arrays

#### Example

```python
# Calculate Keltner Channel
kc_upper, kc_middle, kc_lower = ta.keltner(df['high'], df['low'], df['close'])
df['KC_Upper'] = kc_upper
df['KC_Middle'] = kc_middle
df['KC_Lower'] = kc_lower

# Custom parameters
kc_upper_custom, kc_middle_custom, kc_lower_custom = ta.keltner(
    df['high'], df['low'], df['close'], 
    ema_period=14, atr_period=14, multiplier=1.5
)

print(df[['close', 'KC_Upper', 'KC_Middle', 'KC_Lower']].tail())
```

***

### Donchian Channel

Donchian Channels are formed by taking the highest high and lowest low of the last n periods, providing dynamic support and resistance levels.

#### Usage

```python
upper, middle, lower = ta.donchian(high, low, period=20)
```

#### Parameters

* **high** *(array-like)*: High prices
* **low** *(array-like)*: Low prices
* **period** *(int, default=20)*: Number of periods for the channel calculation

#### Returns

* **tuple**: (upper\_channel, middle\_line, lower\_channel) arrays

#### Example

```python
# Calculate Donchian Channel
dc_upper, dc_middle, dc_lower = ta.donchian(df['high'], df['low'], period=20)
df['DC_Upper'] = dc_upper
df['DC_Middle'] = dc_middle
df['DC_Lower'] = dc_lower

# Different periods
dc_upper_10, dc_middle_10, dc_lower_10 = ta.donchian(df['high'], df['low'], period=10)
df['DC_Upper_10'] = dc_upper_10
df['DC_Lower_10'] = dc_lower_10

print(df[['high', 'low', 'DC_Upper', 'DC_Middle', 'DC_Lower']].tail())
```

***

### Chaikin Volatility

Chaikin Volatility measures the rate of change of the trading range, indicating periods of increasing or decreasing volatility.

#### Usage

```python
cv_result = ta.chaikin(high, low, ema_period=10, roc_period=10)
```

#### Parameters

* **high** *(array-like)*: High prices
* **low** *(array-like)*: Low prices
* **ema\_period** *(int, default=10)*: Period for EMA of high-low range
* **roc\_period** *(int, default=10)*: Period for rate of change calculation

#### Returns

* **array**: Chaikin Volatility values

#### Example

```python
# Calculate Chaikin Volatility
cv = ta.chaikin(df['high'], df['low'])
df['Chaikin_Volatility'] = cv

# Custom parameters
cv_custom = ta.chaikin(df['high'], df['low'], ema_period=14, roc_period=14)
df['CV_Custom'] = cv_custom

print(df[['close', 'Chaikin_Volatility', 'CV_Custom']].tail())
```

***

### Normalized Average True Range (NATR)

NATR is ATR expressed as a percentage of closing price, making it useful for comparing volatility across different price levels.

#### Usage

```python
natr_result = ta.natr(high, low, close, period=14)
```

#### Parameters

* **high** *(array-like)*: High prices
* **low** *(array-like)*: Low prices
* **close** *(array-like)*: Closing prices
* **period** *(int, default=14)*: Period for ATR calculation

#### Returns

* **array**: NATR values (percentage)

#### Example

```python
# Calculate NATR
natr = ta.natr(df['high'], df['low'], df['close'], period=14)
df['NATR'] = natr

# Different period
natr_21 = ta.natr(df['high'], df['low'], df['close'], period=21)
df['NATR_21'] = natr_21

print(df[['close', 'NATR', 'NATR_21']].tail())
```

***

### Relative Volatility Index (RVI)

RVI applies the RSI calculation to standard deviation instead of price changes, measuring volatility momentum.

#### Usage

```python
rvi_result = ta.rvi(data, stdev_period=10, rsi_period=14)
```

#### Parameters

* **data** *(array-like)*: Price data (typically closing prices)
* **stdev\_period** *(int, default=10)*: Period for standard deviation calculation
* **rsi\_period** *(int, default=14)*: Period for RSI calculation

#### Returns

* **array**: RVI values (0-100 range)

#### Example

```python
# Calculate RVI
rvi = ta.rvi(df['close'])
df['RVI'] = rvi

# Custom parameters
rvi_custom = ta.rvi(df['close'], stdev_period=14, rsi_period=21)
df['RVI_Custom'] = rvi_custom

print(df[['close', 'RVI', 'RVI_Custom']].tail())
```

***

### Ultimate Oscillator

Ultimate Oscillator combines short, medium, and long-term price action into one oscillator, incorporating volatility analysis.

#### Usage

```python
uo_result = ta.ultimate_oscillator(high, low, close, period1=7, period2=14, period3=28)
```

#### Parameters

* **high** *(array-like)*: High prices
* **low** *(array-like)*: Low prices
* **close** *(array-like)*: Closing prices
* **period1** *(int, default=7)*: Short period
* **period2** *(int, default=14)*: Medium period
* **period3** *(int, default=28)*: Long period

#### Returns

* **array**: Ultimate Oscillator values (0-100 range)

#### Example

```python
# Calculate Ultimate Oscillator
uo = ta.ultimate_oscillator(df['high'], df['low'], df['close'])
df['Ultimate_Oscillator'] = uo

# Custom periods
uo_custom = ta.ultimate_oscillator(df['high'], df['low'], df['close'], 
                                  period1=5, period2=10, period3=20)
df['UO_Custom'] = uo_custom

print(df[['close', 'Ultimate_Oscillator', 'UO_Custom']].tail())
```

***

### True Range

True Range measures volatility that accounts for gaps between periods.

#### Usage

```python
tr_result = ta.true_range(high, low, close)
```

#### Parameters

* **high** *(array-like)*: High prices
* **low** *(array-like)*: Low prices
* **close** *(array-like)*: Closing prices

#### Returns

* **array**: True Range values

#### Example

```python
# Calculate True Range
tr = ta.true_range(df['high'], df['low'], df['close'])
df['True_Range'] = tr

print(df[['high', 'low', 'close', 'True_Range']].tail())
```

***

### Mass Index

Mass Index uses the high-low range to identify trend reversals based on range expansion.

#### Usage

```python
mass_result = ta.massindex(high, low, length=10)
```

#### Parameters

* **high** *(array-like)*: High prices
* **low** *(array-like)*: Low prices
* **length** *(int, default=10)*: Period for sum calculation

#### Returns

* **array**: Mass Index values

#### Example

```python
# Calculate Mass Index
mass = ta.massindex(df['high'], df['low'])
df['Mass_Index'] = mass

# Different period
mass_14 = ta.massindex(df['high'], df['low'], length=14)
df['Mass_Index_14'] = mass_14

print(df[['close', 'Mass_Index', 'Mass_Index_14']].tail())
```

***

### Bollinger Bands %B

%B shows where price is in relation to the Bollinger Bands, with 1 indicating price at upper band and 0 at lower band.

#### Usage

```python
percent_b = ta.bbpercent(data, period=20, std_dev=2.0)
```

#### Parameters

* **data** *(array-like)*: Price data (typically closing prices)
* **period** *(int, default=20)*: Period for moving average and standard deviation
* **std\_dev** *(float, default=2.0)*: Number of standard deviations for the bands

#### Returns

* **array**: %B values

#### Example

```python
# Calculate Bollinger Bands %B
bb_percent = ta.bbpercent(df['close'])
df['BB_Percent_B'] = bb_percent

# Custom parameters
bb_percent_tight = ta.bbpercent(df['close'], period=14, std_dev=1.5)
df['BB_Percent_B_Tight'] = bb_percent_tight

print(df[['close', 'BB_Percent_B', 'BB_Percent_B_Tight']].tail())
```

***

### Bollinger Bandwidth

Bollinger Bandwidth measures the width of the Bollinger Bands, useful for identifying volatility squeezes.

#### Usage

```python
bandwidth = ta.bbwidth(data, period=20, std_dev=2.0)
```

#### Parameters

* **data** *(array-like)*: Price data (typically closing prices)
* **period** *(int, default=20)*: Period for moving average and standard deviation
* **std\_dev** *(float, default=2.0)*: Number of standard deviations for the bands

#### Returns

* **array**: Bandwidth values

#### Example

```python
# Calculate Bollinger Bandwidth
bb_width = ta.bbwidth(df['close'])
df['BB_Bandwidth'] = bb_width

# Different standard deviation
bb_width_tight = ta.bbwidth(df['close'], std_dev=1.5)
df['BB_Bandwidth_Tight'] = bb_width_tight

print(df[['close', 'BB_Bandwidth', 'BB_Bandwidth_Tight']].tail())
```

***

### Chandelier Exit

Chandelier Exit is a trailing stop-loss technique that follows price action using highest/lowest values and ATR.

#### Usage

```python
long_exit, short_exit = ta.chandelier_exit(high, low, close, period=22, multiplier=3.0)
```

#### Parameters

* **high** *(array-like)*: High prices
* **low** *(array-like)*: Low prices
* **close** *(array-like)*: Closing prices
* **period** *(int, default=22)*: Period for highest/lowest and ATR calculation
* **multiplier** *(float, default=3.0)*: ATR multiplier

#### Returns

* **tuple**: (long\_exit, short\_exit) arrays

#### Example

```python
# Calculate Chandelier Exit
ce_long, ce_short = ta.chandelier_exit(df['high'], df['low'], df['close'])
df['CE_Long_Exit'] = ce_long
df['CE_Short_Exit'] = ce_short

# Custom parameters
ce_long_custom, ce_short_custom = ta.chandelier_exit(
    df['high'], df['low'], df['close'], period=14, multiplier=2.0
)
df['CE_Long_Custom'] = ce_long_custom
df['CE_Short_Custom'] = ce_short_custom

print(df[['close', 'CE_Long_Exit', 'CE_Short_Exit']].tail())
```

***

### Historical Volatility

Historical Volatility measures the standard deviation of logarithmic returns over a specified period.

#### Usage

```python
hv_result = ta.hv(close, length=10, annual=365, per=1)
```

#### Parameters

* **close** *(array-like)*: Closing prices
* **length** *(int, default=10)*: Period for volatility calculation
* **annual** *(int, default=365)*: Annual periods for scaling
* **per** *(int, default=1)*: Timeframe periods (1 for daily/intraday, 7 for weekly+)

#### Returns

* **array**: Historical volatility values (annualized percentages)

#### Example

```python
# Calculate Historical Volatility
hv = ta.hv(df['close'], length=20)
df['Historical_Volatility'] = hv

# Different periods
hv_10 = ta.hv(df['close'], length=10)
hv_30 = ta.hv(df['close'], length=30)
df['HV_10'] = hv_10
df['HV_30'] = hv_30

print(df[['close', 'Historical_Volatility', 'HV_10', 'HV_30']].tail())
```

***

### Ulcer Index

Ulcer Index measures downside risk by calculating the depth and duration of drawdowns from recent highs.

#### Usage

```python
ui_result = ta.ulcerindex(data, length=14, smooth_length=14, signal_length=52, 
                         signal_type="SMA", return_signal=False)
```

#### Parameters

* **data** *(array-like)*: Price data (typically closing prices)
* **length** *(int, default=14)*: Period for highest calculation
* **smooth\_length** *(int, default=14)*: Period for smoothing squared drawdowns
* **signal\_length** *(int, default=52)*: Period for signal line calculation
* **signal\_type** *(str, default="SMA")*: Signal smoothing type ("SMA" or "EMA")
* **return\_signal** *(bool, default=False)*: Whether to return signal line

#### Returns

* **array** or **tuple**: Ulcer Index values (and signal if return\_signal=True)

#### Example

```python
# Calculate Ulcer Index
ui = ta.ulcerindex(df['close'])
df['Ulcer_Index'] = ui

# With signal line
ui_with_signal, ui_signal = ta.ulcerindex(df['close'], return_signal=True)
df['UI_Signal'] = ui_signal

# Custom parameters
ui_custom = ta.ulcerindex(df['close'], length=21, smooth_length=21)
df['UI_Custom'] = ui_custom

print(df[['close', 'Ulcer_Index', 'UI_Signal', 'UI_Custom']].tail())
```

***

### STARC Bands

STARC Bands use a Simple Moving Average and Average True Range to create volatility-based bands.

#### Usage

```python
upper, middle, lower = ta.starc(high, low, close, ma_period=5, atr_period=15, multiplier=1.33)
```

#### Parameters

* **high** *(array-like)*: High prices
* **low** *(array-like)*: Low prices
* **close** *(array-like)*: Closing prices
* **ma\_period** *(int, default=5)*: Period for SMA calculation
* **atr\_period** *(int, default=15)*: Period for ATR calculation
* **multiplier** *(float, default=1.33)*: ATR multiplier

#### Returns

* **tuple**: (upper\_band, middle\_line, lower\_band) arrays

#### Example

```python
# Calculate STARC Bands
starc_upper, starc_middle, starc_lower = ta.starc(df['high'], df['low'], df['close'])
df['STARC_Upper'] = starc_upper
df['STARC_Middle'] = starc_middle
df['STARC_Lower'] = starc_lower

# Custom parameters
starc_upper_custom, starc_middle_custom, starc_lower_custom = ta.starc(
    df['high'], df['low'], df['close'], 
    ma_period=10, atr_period=20, multiplier=2.0
)

print(df[['close', 'STARC_Upper', 'STARC_Middle', 'STARC_Lower']].tail())
```

***

### Complete Example: Volatility Analysis

```python
from openalgo import ta, api
import pandas as pd

# Initialize API and get data
client = api(api_key='your_api_key_here', host='http://127.0.0.1:5000')
df = client.history(symbol="SBIN", exchange="NSE", interval="5m", 
                   start_date="2025-04-01", end_date="2025-04-08")

# Calculate multiple volatility indicators
df['ATR'] = ta.atr(df['high'], df['low'], df['close'], period=14)
df['NATR'] = ta.natr(df['high'], df['low'], df['close'], period=14)

# Bollinger Bands
bb_upper, bb_middle, bb_lower = ta.bbands(df['close'], period=20, std_dev=2.0)
df['BB_Upper'] = bb_upper
df['BB_Middle'] = bb_middle
df['BB_Lower'] = bb_lower
df['BB_Width'] = ta.bbwidth(df['close'], period=20, std_dev=2.0)
df['BB_Percent_B'] = ta.bbpercent(df['close'], period=20, std_dev=2.0)

# Keltner Channel
kc_upper, kc_middle, kc_lower = ta.keltner(df['high'], df['low'], df['close'])
df['KC_Upper'] = kc_upper
df['KC_Middle'] = kc_middle
df['KC_Lower'] = kc_lower

# Donchian Channel
dc_upper, dc_middle, dc_lower = ta.donchian(df['high'], df['low'], period=20)
df['DC_Upper'] = dc_upper
df['DC_Middle'] = dc_middle
df['DC_Lower'] = dc_lower

# Advanced volatility indicators
df['RVI'] = ta.rvi(df['close'])
df['Historical_Vol'] = ta.hv(df['close'], length=20)
df['Ulcer_Index'] = ta.ulcerindex(df['close'])
df['Mass_Index'] = ta.massindex(df['high'], df['low'])

# Chandelier Exit levels
ce_long, ce_short = ta.chandelier_exit(df['high'], df['low'], df['close'])
df['CE_Long'] = ce_long
df['CE_Short'] = ce_short

# Volatility analysis
print("=== Volatility Analysis ===")
print(f"Average ATR: {df['ATR'].mean():.2f}")
print(f"Average NATR: {df['NATR'].mean():.2f}%")
print(f"Average Historical Volatility: {df['Historical_Vol'].mean():.2f}%")
print(f"Average BB Width: {df['BB_Width'].mean():.4f}")

# Recent values
print("\n=== Recent Volatility Indicators ===")
recent_data = df[['close', 'ATR', 'NATR', 'BB_Width', 'RVI', 'Historical_Vol']].tail()
print(recent_data)

# Volatility squeeze detection (BB Width < KC Width equivalent)
df['Squeeze'] = (df['BB_Upper'] - df['BB_Lower']) < (df['KC_Upper'] - df['KC_Lower'])
print(f"\nVolatility Squeeze periods: {df['Squeeze'].sum()} out of {len(df)} periods")
```

### Common Use Cases

1. **Volatility Breakouts**: Use BB Width and Mass Index to identify low volatility periods before breakouts
2. **Risk Management**: Use ATR and NATR for position sizing and stop-loss placement
3. **Overbought/Oversold**: Use BB %B and RVI to identify extreme price levels
4. **Trend Strength**: Higher volatility often accompanies strong trends
5. **Market Regime**: Compare different volatility measures to understand market conditions

### Performance Tips

1. **Efficient Calculations**: Use vectorized operations for multiple timeframes
2. **Memory Management**: Calculate only needed indicators to save memory
3. **Parameter Optimization**: Test different periods for your specific market and timeframe
4. **Combination Analysis**: Use multiple volatility indicators together for confirmation


---

# Agent Instructions: Querying This Documentation

If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.openalgo.in/trading-platform/python/indicators/volatility.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

```


---

# FILE: docs\prompt\volume - openalgo indicators.md

```md
# Volume

Volume indicators analyze trading volume to assess the strength of price movements and identify potential trend changes. These indicators help determine whether price movements are supported by volume activity.

### Import Statement

```python
from openalgo import ta, api
```

### Getting Sample Data

```python
# Initialize API client
client = api(api_key='your_api_key_here', host='http://127.0.0.1:5000')

# Fetch historical data
df = client.history(symbol="SBIN", 
                   exchange="NSE", 
                   interval="5m", 
                   start_date="2025-04-01", 
                   end_date="2025-04-08")

# Extract OHLCV data
high = df['high']
low = df['low'] 
close = df['close']
open_price = df['open']
volume = df['volume']
```

***

### On Balance Volume (OBV)

OBV is a momentum indicator that uses volume flow to predict changes in stock price by adding volume on up days and subtracting volume on down days.

#### Usage

```python
obv = ta.obv(close, volume)
```

#### Parameters

* **close** *(pandas.Series)*: Closing prices
* **volume** *(pandas.Series)*: Volume data

#### Returns

* **pandas.Series**: OBV values with same index as input

#### Example

```python
# Calculate OBV
obv_values = ta.obv(df['close'], df['volume'])

# Add to DataFrame
df['OBV'] = obv_values

print(df[['close', 'volume', 'OBV']].tail())
```

***

### On Balance Volume with Smoothing (OBV Smoothed)

Enhanced OBV with various smoothing options including moving averages and Bollinger Bands support.

#### Usage

```python
# Basic smoothed OBV
obv_smoothed = ta.obv_smoothed(close, volume, ma_type="SMA", ma_length=20)

# With Bollinger Bands
obv_bb_middle, obv_bb_upper, obv_bb_lower = ta.obv_smoothed(
    close, volume, ma_type="SMA + Bollinger Bands", bb_length=20, bb_mult=2.0
)
```

#### Parameters

* **close** *(pandas.Series)*: Closing prices
* **volume** *(pandas.Series)*: Volume data
* **ma\_type** *(str, default="None")*: Smoothing type - "None", "SMA", "SMA + Bollinger Bands", "EMA", "SMMA (RMA)", "WMA", "VWMA"
* **ma\_length** *(int, default=20)*: Moving average length
* **bb\_length** *(int, default=20)*: Bollinger Bands length
* **bb\_mult** *(float, default=2.0)*: Bollinger Bands multiplier

#### Returns

* **pandas.Series**: Smoothed OBV values (for most ma\_types)
* **tuple**: (middle, upper, lower) for "SMA + Bollinger Bands"

#### Example

```python
# Calculate various OBV smoothing options
obv_sma = ta.obv_smoothed(df['close'], df['volume'], ma_type="SMA", ma_length=20)
obv_ema = ta.obv_smoothed(df['close'], df['volume'], ma_type="EMA", ma_length=20)

# OBV with Bollinger Bands
obv_bb_mid, obv_bb_up, obv_bb_low = ta.obv_smoothed(
    df['close'], df['volume'], ma_type="SMA + Bollinger Bands"
)

df['OBV_SMA'] = obv_sma
df['OBV_EMA'] = obv_ema
df['OBV_BB_Mid'] = obv_bb_mid
df['OBV_BB_Upper'] = obv_bb_up
df['OBV_BB_Lower'] = obv_bb_low
```

***

### Volume Weighted Average Price (VWAP)

VWAP is the average price a security has traded at throughout the day, based on both volume and price, giving more weight to prices with higher volume.

#### Usage

```python
vwap = ta.vwap(high, low, close, volume, source="hlc3", anchor="Session")
```

#### Parameters

* **high** *(pandas.Series)*: High prices
* **low** *(pandas.Series)*: Low prices
* **close** *(pandas.Series)*: Closing prices
* **volume** *(pandas.Series)*: Volume data
* **source** *(str, default="hlc3")*: Price source - "hlc3", "hl2", "ohlc4", "close"
* **anchor** *(str, default="Session")*: Anchor period - "Session", "Week", "Month", etc.

#### Returns

* **pandas.Series**: VWAP values

#### Example

```python
# Calculate VWAP
vwap_values = ta.vwap(df['high'], df['low'], df['close'], df['volume'])

# VWAP with different source
vwap_close = ta.vwap(df['high'], df['low'], df['close'], df['volume'], source="close")

df['VWAP'] = vwap_values
df['VWAP_Close'] = vwap_close

print(df[['close', 'VWAP', 'VWAP_Close']].tail())
```

***

### Money Flow Index (MFI)

MFI is a momentum indicator that uses both price and volume to measure buying and selling pressure. Also known as Volume-Weighted RSI.

#### Usage

```python
mfi = ta.mfi(high, low, close, volume, period=14)
```

#### Parameters

* **high** *(pandas.Series)*: High prices
* **low** *(pandas.Series)*: Low prices
* **close** *(pandas.Series)*: Closing prices
* **volume** *(pandas.Series)*: Volume data
* **period** *(int, default=14)*: Number of periods for MFI calculation

#### Returns

* **pandas.Series**: MFI values (range: 0 to 100)

#### Example

```python
# Calculate MFI with default period
mfi_14 = ta.mfi(df['high'], df['low'], df['close'], df['volume'])

# Calculate MFI with different period
mfi_21 = ta.mfi(df['high'], df['low'], df['close'], df['volume'], period=21)

df['MFI_14'] = mfi_14
df['MFI_21'] = mfi_21

print(df[['close', 'volume', 'MFI_14']].tail())
```

***

### Accumulation/Distribution Line (ADL)

ADL is a volume-based indicator designed to measure the cumulative flow of money into and out of a security.

#### Usage

```python
adl = ta.adl(high, low, close, volume)
```

#### Parameters

* **high** *(pandas.Series)*: High prices
* **low** *(pandas.Series)*: Low prices
* **close** *(pandas.Series)*: Closing prices
* **volume** *(pandas.Series)*: Volume data

#### Returns

* **pandas.Series**: ADL values

#### Example

```python
# Calculate Accumulation/Distribution Line
adl_values = ta.adl(df['high'], df['low'], df['close'], df['volume'])

df['ADL'] = adl_values

print(df[['close', 'volume', 'ADL']].tail())
```

***

### Chaikin Money Flow (CMF)

CMF is the sum of Money Flow Volume over a period divided by the sum of volume over the same period.

#### Usage

```python
cmf = ta.cmf(high, low, close, volume, period=20)
```

#### Parameters

* **high** *(pandas.Series)*: High prices
* **low** *(pandas.Series)*: Low prices
* **close** *(pandas.Series)*: Closing prices
* **volume** *(pandas.Series)*: Volume data
* **period** *(int, default=20)*: Number of periods for CMF calculation

#### Returns

* **pandas.Series**: CMF values

#### Example

```python
# Calculate Chaikin Money Flow
cmf_20 = ta.cmf(df['high'], df['low'], df['close'], df['volume'])

# CMF with different period
cmf_10 = ta.cmf(df['high'], df['low'], df['close'], df['volume'], period=10)

df['CMF_20'] = cmf_20
df['CMF_10'] = cmf_10

print(df[['close', 'CMF_20']].tail())
```

***

### Ease of Movement (EMV)

EMV relates price change to volume and is particularly useful for assessing the strength of a trend.

#### Usage

```python
emv = ta.emv(high, low, volume, length=14, divisor=10000)
```

#### Parameters

* **high** *(pandas.Series)*: High prices
* **low** *(pandas.Series)*: Low prices
* **volume** *(pandas.Series)*: Volume data
* **length** *(int, default=14)*: Period for SMA smoothing
* **divisor** *(int, default=10000)*: Divisor for scaling EMV values

#### Returns

* **pandas.Series**: EMV values

#### Example

```python
# Calculate Ease of Movement
emv_14 = ta.emv(df['high'], df['low'], df['volume'])

# EMV with custom parameters
emv_custom = ta.emv(df['high'], df['low'], df['volume'], length=21, divisor=50000)

df['EMV_14'] = emv_14
df['EMV_Custom'] = emv_custom

print(df[['close', 'volume', 'EMV_14']].tail())
```

***

### Elder Force Index (FI)

Force Index combines price and volume to assess the power used to move the price of an asset.

#### Usage

```python
fi = ta.force_index(close, volume, length=13)
```

#### Parameters

* **close** *(pandas.Series)*: Closing prices
* **volume** *(pandas.Series)*: Volume data
* **length** *(int, default=13)*: Period for EMA smoothing

#### Returns

* **pandas.Series**: Elder Force Index values

#### Example

```python
# Calculate Elder Force Index
fi_13 = ta.force_index(df['close'], df['volume'])

# Force Index with different period
fi_21 = ta.force_index(df['close'], df['volume'], length=21)

df['Force_Index_13'] = fi_13
df['Force_Index_21'] = fi_21

print(df[['close', 'volume', 'Force_Index_13']].tail())
```

***

### Negative Volume Index (NVI)

NVI focuses on days when volume decreases from the previous day, using cumulative rate of change.

#### Usage

```python
# Basic NVI
nvi = ta.nvi(close, volume)

# NVI with EMA signal line
nvi, nvi_ema = ta.nvi_with_ema(close, volume, ema_length=255)
```

#### Parameters

* **close** *(pandas.Series)*: Closing prices
* **volume** *(pandas.Series)*: Volume data
* **ema\_length** *(int, default=255)*: EMA period for signal line

#### Returns

* **pandas.Series**: NVI values
* **tuple**: (nvi, nvi\_ema) for nvi\_with\_ema method

#### Example

```python
# Calculate NVI
nvi_values = ta.nvi(df['close'], df['volume'])

# Calculate NVI with EMA signal
nvi_line, nvi_signal = ta.nvi_with_ema(df['close'], df['volume'])

df['NVI'] = nvi_values
df['NVI_Line'] = nvi_line
df['NVI_Signal'] = nvi_signal

print(df[['close', 'volume', 'NVI']].tail())
```

***

### Positive Volume Index (PVI)

PVI focuses on days when volume increases from the previous day.

#### Usage

```python
# Basic PVI
pvi = ta.pvi(close, volume, initial_value=100.0)

# PVI with signal line
pvi, pvi_signal = ta.pvi_with_signal(close, volume, signal_type="EMA", signal_length=255)
```

#### Parameters

* **close** *(pandas.Series)*: Closing prices
* **volume** *(pandas.Series)*: Volume data
* **initial\_value** *(float, default=100.0)*: Initial PVI value
* **signal\_type** *(str, default="EMA")*: Signal smoothing type ("EMA" or "SMA")
* **signal\_length** *(int, default=255)*: Signal line period

#### Returns

* **pandas.Series**: PVI values
* **tuple**: (pvi, signal) for pvi\_with\_signal method

#### Example

```python
# Calculate PVI
pvi_values = ta.pvi(df['close'], df['volume'])

# Calculate PVI with signal line
pvi_line, pvi_signal = ta.pvi_with_signal(df['close'], df['volume'])

df['PVI'] = pvi_values
df['PVI_Line'] = pvi_line
df['PVI_Signal'] = pvi_signal

print(df[['close', 'volume', 'PVI']].tail())
```

***

### Volume Oscillator (VOLOSC)

Volume Oscillator shows the relationship between two exponential moving averages of volume.

#### Usage

```python
vo = ta.volosc(volume, short_length=5, long_length=10)
```

#### Parameters

* **volume** *(pandas.Series)*: Volume data
* **short\_length** *(int, default=5)*: Short EMA length
* **long\_length** *(int, default=10)*: Long EMA length
* **check\_volume\_validity** *(bool, default=True)*: Check for valid volume data

#### Returns

* **pandas.Series**: Volume Oscillator values

#### Example

```python
# Calculate Volume Oscillator
vo_5_10 = ta.volosc(df['volume'])

# Volume Oscillator with custom periods
vo_3_15 = ta.volosc(df['volume'], short_length=3, long_length=15)

df['VO_5_10'] = vo_5_10
df['VO_3_15'] = vo_3_15

print(df[['volume', 'VO_5_10']].tail())
```

***

### Volume Rate of Change (VROC)

VROC measures the rate of change in volume over a specified period.

#### Usage

```python
vroc = ta.vroc(volume, period=25)
```

#### Parameters

* **volume** *(pandas.Series)*: Volume data
* **period** *(int, default=25)*: Number of periods to look back

#### Returns

* **pandas.Series**: VROC values

#### Example

```python
# Calculate Volume Rate of Change
vroc_25 = ta.vroc(df['volume'])

# VROC with different period
vroc_12 = ta.vroc(df['volume'], period=12)

df['VROC_25'] = vroc_25
df['VROC_12'] = vroc_12

print(df[['volume', 'VROC_25']].tail())
```

***

### Klinger Volume Oscillator (KVO)

KVO is designed to predict price reversals by comparing volume to price movement.

#### Usage

```python
kvo, kvo_trigger = ta.kvo(high, low, close, volume, trig_len=13, fast_x=34, slow_x=55)
```

#### Parameters

* **high** *(pandas.Series)*: High prices
* **low** *(pandas.Series)*: Low prices
* **close** *(pandas.Series)*: Closing prices
* **volume** *(pandas.Series)*: Volume data
* **trig\_len** *(int, default=13)*: Trigger line EMA period
* **fast\_x** *(int, default=34)*: Fast EMA period
* **slow\_x** *(int, default=55)*: Slow EMA period

#### Returns

* **tuple**: (kvo, trigger) pandas.Series

#### Example

```python
# Calculate Klinger Volume Oscillator
kvo_line, kvo_trigger = ta.kvo(df['high'], df['low'], df['close'], df['volume'])

# KVO with custom parameters
kvo_custom, kvo_trig_custom = ta.kvo(df['high'], df['low'], df['close'], df['volume'], 
                                    trig_len=9, fast_x=21, slow_x=34)

df['KVO'] = kvo_line
df['KVO_Trigger'] = kvo_trigger

print(df[['close', 'volume', 'KVO', 'KVO_Trigger']].tail())
```

***

### Price Volume Trend (PVT)

PVT combines price and volume to show cumulative volume based on price changes.

#### Usage

```python
pvt = ta.pvt(close, volume)
```

#### Parameters

* **close** *(pandas.Series)*: Closing prices
* **volume** *(pandas.Series)*: Volume data

#### Returns

* **pandas.Series**: PVT values

#### Example

```python
# Calculate Price Volume Trend
pvt_values = ta.pvt(df['close'], df['volume'])

df['PVT'] = pvt_values

print(df[['close', 'volume', 'PVT']].tail())
```

***

### Relative Volume (RVOL)

RVOL compares current volume to average volume over a specified period.

#### Usage

```python
rvol = ta.rvol(volume, period=20)
```

#### Parameters

* **volume** *(pandas.Series)*: Volume data
* **period** *(int, default=20)*: Period for average volume calculation

#### Returns

* **pandas.Series**: RVOL values

#### Example

```python
# Calculate Relative Volume
rvol_20 = ta.rvol(df['volume'])

# RVOL with different period
rvol_10 = ta.rvol(df['volume'], period=10)

df['RVOL_20'] = rvol_20
df['RVOL_10'] = rvol_10

print(df[['volume', 'RVOL_20']].tail())
```

***

### Complete Volume Analysis Example

```python
from openalgo import ta, api
import pandas as pd

# Get data
client = api(api_key='your_api_key_here', host='http://127.0.0.1:5000')
df = client.history(symbol="SBIN", exchange="NSE", interval="5m", 
                   start_date="2025-04-01", end_date="2025-04-08")

# Calculate multiple volume indicators
df['OBV'] = ta.obv(df['close'], df['volume'])
df['VWAP'] = ta.vwap(df['high'], df['low'], df['close'], df['volume'])
df['MFI'] = ta.mfi(df['high'], df['low'], df['close'], df['volume'])
df['ADL'] = ta.adl(df['high'], df['low'], df['close'], df['volume'])
df['CMF'] = ta.cmf(df['high'], df['low'], df['close'], df['volume'])
df['EMV'] = ta.emv(df['high'], df['low'], df['volume'])
df['Force_Index'] = ta.force_index(df['close'], df['volume'])
df['Volume_Osc'] = ta.volosc(df['volume'])
df['PVT'] = ta.pvt(df['close'], df['volume'])
df['RVOL'] = ta.rvol(df['volume'])

# KVO requires multiple returns
df['KVO'], df['KVO_Trigger'] = ta.kvo(df['high'], df['low'], df['close'], df['volume'])

# Display results
volume_indicators = ['close', 'volume', 'OBV', 'VWAP', 'MFI', 'ADL', 'CMF', 
                    'EMV', 'Force_Index', 'Volume_Osc', 'PVT', 'RVOL', 'KVO']

print("Volume Indicators Analysis:")
print(df[volume_indicators].tail(10))

# Volume analysis summary
print("\nVolume Indicators Summary (Last Period):")
last_row = df.iloc[-1]
print(f"Close Price: {last_row['close']:.2f}")
print(f"Volume: {last_row['volume']:,}")
print(f"VWAP: {last_row['VWAP']:.2f}")
print(f"MFI: {last_row['MFI']:.2f}")
print(f"Relative Volume: {last_row['RVOL']:.2f}")
print(f"Volume Oscillator: {last_row['Volume_Osc']:.2f}")
```

### Volume Analysis Interpretation

1. **OBV**: Rising OBV confirms uptrend, falling OBV confirms downtrend
2. **VWAP**: Price above VWAP suggests bullish momentum, below suggests bearish
3. **MFI**: Values above 80 indicate overbought, below 20 indicate oversold
4. **ADL**: Rising ADL confirms price uptrend with strong accumulation
5. **CMF**: Positive values indicate buying pressure, negative indicate selling
6. **Volume Oscillator**: Positive values show increasing volume momentum
7. **Relative Volume**: Values above 1.0 indicate higher than average volume


---

# Agent Instructions: Querying This Documentation

If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.openalgo.in/trading-platform/python/indicators/volume.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

```


---

# FILE: docs\prompt\websockets-format.md

```md
# Websockets

## OpenAlgo WebSocket Protocol Documentation

### Overview

The OpenAlgo WebSocket protocol allows clients to receive **real-time market data** using a standardized and broker-agnostic interface. It supports data streaming for **LTP (Last Traded Price)**, **Quotes (OHLC + Volume)**, and **Market Depth** (up to 50 levels depending on broker capability).

The protocol ensures efficient, scalable, and secure communication between client applications (such as trading bots, dashboards, or analytics tools) and the OpenAlgo platform. Authentication is handled using the OpenAlgo API key, and subscriptions are maintained per session.

### Version

* Protocol Version: 1.0
* Last Updated: May 28, 2025
* Platform: OpenAlgo Trading Framework

### WebSocket URL

```
ws://<host>:8765
```

Replace `<host>` with the IP/domain of your OpenAlgo instance. For local development setups, use thee hostname as`127.0.0.1`

```
ws://127.0.0.1:8765
```

In the production ubuntu server if your host is <https://yourdomain.com> then&#x20;

WebSocket url will be

```
wss://yourdomain.com/ws
```

In the production ubuntu server if your host is <https://sub.yourdomain.com> then&#x20;

WebSocket url will be

```
wss://sub.yourdomain.com/ws
```

### Authentication

All WebSocket sessions must begin with API key authentication:

```json
{
  "action": "authenticate", 
  "api_key": "YOUR_OPENALGO_API_KEY"
}
```

On success, the server confirms authentication. On failure, the connection is closed or an error message is returned.

### Data Modes

Clients can subscribe to different types of market data using the `mode` parameter. Each mode corresponds to a specific level of detail:

| Mode | Description    | Details                                    |
| ---- | -------------- | ------------------------------------------ |
| 1    | **LTP Mode**   | Last traded price and timestamp only       |
| 2    | **Quote Mode** | Includes OHLC, LTP, volume, change, etc.   |
| 3    | **Depth Mode** | Includes buy/sell order book (5–50 levels) |

> Note: Mode 3 supports optional parameter `depth_level` to define the number of depth levels requested (e.g., 5, 20, 30, 50). Actual support depends on the broker.

### Subscription Format

#### Basic Subscription

```json
{
  "action": "subscribe",
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "mode": 1
}
```

#### Depth Subscription (with levels)

```json
{
  "action": "subscribe",
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "mode": 3,
  "depth_level": 5
}
```

### Unsubscription

To unsubscribe from a stream:

```json
{
  "action": "unsubscribe",
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "mode": 2
}
```

### Error Handling

If a client requests a depth level not supported by their broker:

```json
{
  "type": "error",
  "code": "UNSUPPORTED_DEPTH_LEVEL",
  "message": "Depth level 50 is not supported by broker Angel for exchange NSE",
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "requested_mode": 3,
  "requested_depth": 50,
  "supported_depths": [5, 20]
}
```

### Market Data Format

#### LTP (Mode 1)

```json
{
  "type": "market_data",
  "mode": 1,
  "topic": "RELIANCE.NSE",
  "data": {
    "symbol": "RELIANCE",
    "exchange": "NSE",
    "ltp": 1424.0,
    "timestamp": "2025-05-28T10:30:45.123Z"
  }
}
```

#### Quote (Mode 2)

```json
{
  "type": "market_data",
  "mode": 2,
  "topic": "RELIANCE.NSE",
  "data": {
    "symbol": "RELIANCE",
    "exchange": "NSE",
    "ltp": 1424.0,
    "change": 6.0,
    "change_percent": 0.42,
    "volume": 100000,
    "open": 1415.0,
    "high": 1432.5,
    "low": 1408.0,
    "close": 1418.0,
    "last_trade_quantity": 50,
    "avg_trade_price": 1419.35,
    "timestamp": "2025-05-28T10:30:45.123Z"
  }
}
```

#### Depth (Mode 3 with depth\_level = 5)

```json
{
  "type": "market_data",
  "mode": 3,
  "depth_level": 5,
  "topic": "RELIANCE.NSE",
  "data": {
    "symbol": "RELIANCE",
    "exchange": "NSE",
    "ltp": 1424.0,
    "depth": {
      "buy": [
        {"price": 1423.9, "quantity": 50, "orders": 3},
        {"price": 1423.5, "quantity": 35, "orders": 2},
        {"price": 1423.0, "quantity": 42, "orders": 4},
        {"price": 1422.5, "quantity": 28, "orders": 1},
        {"price": 1422.0, "quantity": 33, "orders": 5}
      ],
      "sell": [
        {"price": 1424.1, "quantity": 47, "orders": 2},
        {"price": 1424.5, "quantity": 39, "orders": 3},
        {"price": 1425.0, "quantity": 41, "orders": 4},
        {"price": 1425.5, "quantity": 32, "orders": 2},
        {"price": 1426.0, "quantity": 30, "orders": 1}
      ]
    },
    "timestamp": "2025-05-28T10:30:45.123Z",
    "broker_supported": true
  }
}
```

### Heartbeat and Reconnection

* Server sends `ping` messages every 30 seconds.
* Clients must respond with `pong` or will be disconnected.
* Upon reconnection, clients must re-authenticate and re-subscribe to streams.
* Proxy may automatically restore prior subscriptions if supported by broker.

### Security & Compliance

* All clients must authenticate with an API key.
* Unauthorized or malformed requests are rejected.
* Rate limits may apply to prevent abuse.
* TLS encryption recommended for production deployments.

The OpenAlgo WebSocket feed provides a reliable and structured method for receiving real-time trading data. Proper mode selection and parsing allow efficient integration into trading algorithms and monitoring systems.


---

# Agent Instructions: Querying This Documentation

If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.openalgo.in/api-documentation/v1/websockets.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

```


---

# FILE: docs\prompt\websockets-verbose-control.md

```md
# Websockets (Verbose Control)

The `verbose` parameter manages SDK-level logging for WebSocket feed operations (LTP, Quote, Depth).\
This helps developers toggle between silent mode, basic logs, or full debug-level market data streaming.

***

### **Verbose Levels**

| Level      | Value          | Description                                        |
| ---------- | -------------- | -------------------------------------------------- |
| **Silent** | `False` or `0` | Errors only (default)                              |
| **Basic**  | `True` or `1`  | Connection, authentication, subscription logs      |
| **Debug**  | `2`            | All market data updates, including LTP/Quote/Depth |

***

### **Usage**

```python
from openalgo import api

# Silent mode (default) - no SDK output
client = api(api_key="...", host="...", ws_url="...", verbose=False)

# Basic logging - connection/subscription info
client = api(api_key="...", host="...", ws_url="...", verbose=True)

# Full debug - all data updates
client = api(api_key="...", host="...", ws_url="...", verbose=2)
```

***

## **Test Example**

```python
"""
Test verbose control in OpenAlgo WebSocket Feed
"""
from openalgo import api
import time

# Change this to test different levels: False, True, 1, 2
VERBOSE_LEVEL = True

client = api(
    api_key="your_api_key_here",
    host="http://127.0.0.1:5000",
    ws_url="ws://127.0.0.1:8765",
    verbose=VERBOSE_LEVEL
)

instruments_list = [
    {"exchange": "NSE_INDEX", "symbol": "NIFTY"},
    {"exchange": "NSE", "symbol": "INFY"}
]

def on_data_received(data):
    # User callback: always executed regardless of verbose mode
    print(f"MY CALLBACK: {data['symbol']} LTP: {data['data'].get('ltp')}")

print(f"\n=== Testing with verbose={VERBOSE_LEVEL} ===\n")

# Connect and subscribe
client.connect()
client.subscribe_quote(instruments_list, on_data_received=on_data_received)

# Poll few times
for i in range(5):
    print(f"\n--- Poll {i+1} ---")
    quotes = client.get_quotes()
    for exch, symbols in quotes.get('quote', {}).items():
        for sym, data in symbols.items():
            print(f"  {exch}:{sym} = {data.get('ltp')}")
    time.sleep(1)

# Cleanup
client.unsubscribe_quote(instruments_list)
client.disconnect()
```

***

## **Expected Output**

### **verbose=False (Silent)**

```
=== Testing with verbose=False ===

MY CALLBACK: NIFTY LTP: 26008.5

--- Poll 1 ---
  NSE_INDEX:NIFTY = 26008.5
  NSE:INFY = 1531.0
```

***

### **verbose=True (Basic)**

```
=== Testing with verbose=True ===

[WS]    Connected to ws://127.0.0.1:8765
[AUTH]  Authenticating with API key: bf1267a1...7cf9169f
[AUTH]  Success | Broker: upstox | User: rajandran
[SUB]   Subscribing NSE_INDEX:NIFTY Quote...
[SUB]   NSE_INDEX:NIFTY | Mode: Quote | Status: success
[SUB]   Subscribing NSE:INFY Quote...
[SUB]   NSE:INFY | Mode: Quote | Status: success
MY CALLBACK: NIFTY LTP: 26008.5

--- Poll 1 ---
  NSE_INDEX:NIFTY = 26008.5
  NSE:INFY = 1531.0
```

***

### **verbose=2 (Full Debug)**

```
=== Testing with verbose=2 ===

[WS]    Connected to ws://127.0.0.1:8765
[AUTH]  Authenticating with API key: bf1267a1...7cf9169f
[AUTH]  Success | Broker: upstox | User: rajandran
[AUTH]  Full response: {'type': 'auth', 'status': 'success', ...}
[SUB]   Subscribing NSE_INDEX:NIFTY Quote...
[SUB]   NSE_INDEX:NIFTY | Mode: Quote | Status: success
[SUB]   Full response: {'type': 'subscribe', ...}
[QUOTE] NSE_INDEX:NIFTY      | O: 25998.5    H: 26025.5    L: 25924.15   C: 26008.5    LTP: 26008.5
MY CALLBACK: NIFTY LTP: 26008.5
[QUOTE] NSE:INFY             | O: 1549.0     H: 1550.6     L: 1525.9     C: 1531.0     LTP: 1531.0

--- Poll 1 ---
  NSE_INDEX:NIFTY = 26008.5
  NSE:INFY = 1531.0
```

***

## **Log Categories**

| Tag          | Meaning                             |
| ------------ | ----------------------------------- |
| **\[WS]**    | WebSocket connection events         |
| **\[AUTH]**  | Authentication requests & responses |
| **\[SUB]**   | Subscription operations             |
| **\[UNSUB]** | Unsubscription logs                 |
| **\[LTP]**   | LTP updates *(verbose=2)*           |
| **\[QUOTE]** | Quote updates *(verbose=2)*         |
| **\[DEPTH]** | Market depth updates *(verbose=2)*  |
| **\[ERROR]** | Error messages *(always shown)*     |


---

# Agent Instructions: Querying This Documentation

If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.openalgo.in/trading-platform/python/websockets-verbose-control.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

```
