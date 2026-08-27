# `websocket_client.py` — Dynamic WebSocket Manager + DSM (§3.3, §6.1, §3.2.5/§9)

## Responsibility

The first **networked** module and the tick producer. It owns the feed transport to the OpenAlgo WS
proxy, the **Dynamic Strike Manager (DSM)**, the **tee** into `raw_file_queue`/`proc_queue`, the
recorder-owned **reconnect** state machine, and the live **depth-capability preflight**. It emits
normalized packets into the two (injected) queues and manages subscriptions — **no resampler / metrics
/ DB / gzip** (P4/P5) and **no orchestration / REST-quote seeding** (P6).

## Transport seam (plan decision 20)

`FeedTransport` (protocol) with `bind(on_open, on_message, on_close)`, `run_session()` (blocking receive
loop until close), `send(frame)`, `close()`.

| Impl | Status | Notes |
| --- | --- | --- |
| `RawWSTransport` | **built (default)** | `websocket-client` `WebSocketApp.run_forever(ping_interval=heartbeat_interval_sec, ping_timeout=heartbeat_timeout_sec)` — native heartbeat (decision 22). Preserves `feed_time`/`depth_levels`/`is_50_depth`/`total_*_qty`. |
| `SdkTransport` | **deferred stub** | raises `NotImplementedError` — the SDK depth callback strips the audit fields (`feed.py:456-467`). Built later against the same seam. |

`make_transport(config)` selects by `websocket.transport` (config validation restricts the enum).

## Public API

### `DepthWebSocketClient(config, instrument_manager, raw_file_queue, proc_queue, shutdown_event, *, time_fn=time.time, sleep_fn=time.sleep, transport=None, name="Feed")`
`threading.Thread` (daemon). Reads `openalgo.{websocket_url, api_key}`, `websocket.*` (heartbeat +
backoff), and `underlyings[]` (spot/option exchanges, `requested_depth`, `initial_window`,
`expansion_threshold`, `expansion_step`). Consumes the P1 `instrument_manager` read-only
(`strike_to_symbol_map`, `active_strikes_list`, `chains[name].probe_strike`). `transport=None` selects
by config; tests inject a fake. `time_fn` stamps `recv_ts`; `sleep_fn` drives deterministic backoff.

- `run()` — FEED-thread reconnect loop: `transport.run_session()` (blocks) → on return, backoff
  `min(backoff_max_sec, backoff_base^attempts · backoff_mult)` via `sleep_fn` → retry; `shutdown_event`
  breaks and closes the socket (§6.1).
- `stop()` — set `shutdown_event` and force `transport.close()` so `run_session` returns.
- `active_subscriptions` (property) — the never-shrink set of subscribed **wire** symbols (with `:50`).
- `boundaries(name) -> (b_lower, b_upper)`, `current_spot_prices` — DSM state (health/tests).
- Counters (FEED-thread-only writes): `raw_dropped_total`, `proc_dropped_total`, `_reconnect_attempts`.

**P6 orchestrator touches (decision 61).**
- `seed_spot(name, price)` — seed/advance the DSM from an out-of-band spot (the §3.1.2 mid-day REST
  quote); same entry as a live spot tick (validate → seed boundaries under `_spot_lock` → subscribe new
  strikes after the lock releases). Callable from the main thread.
- `freeze_dsm()` — stop boundary expansion at `session_end` (Milestone 4); never-shrink holds (no
  unsubscribe), so the feed keeps delivering final ticks through the teardown grace window.
- `connection_status` (property) — `"connected"`/`"disconnected"` for the health `websocket_status`
  (set on the FEED thread in `_on_open`/`_on_close`).
- `last_recv_ts` (attr) — the last delivered tick's `recv_ts` (health `last_raw_tick_time`).
- `actual_depth` (dict, keyed by `name`) — first observed `depth_levels` per underlying, first-write-wins
  (§9 silent 50→5 degrade alarm in the health file).

### Module helpers
- `wire_symbol(symbol, requested_depth)` — append `:50` when `requested_depth > 5` (decision 27).
- `normalize_market_data(msg, recv_ts)` — flatten a proxy `market_data` envelope to the canonical packet
  (decision 21): `symbol` kept **as received** (keeps `:50`, §3.3.3), plus `exchange`/`mode`/`recv_ts`
  and the payload fields (`ltp`/`timestamp`/`feed_time`/`depth_levels`/`is_50_depth`/`total_*_qty`/`depth`).

### `run_depth_preflight(config, instrument_manager, *, transport=None, timeout=10.0, time_fn=time.time) -> list[DepthProbeResult]`
Live §3.2.5/§9 probe: open one WS, subscribe a `:50` depth on each underlying's `probe_strike`, read the
first depth packet's `depth_levels`/`is_50_depth`/per-level `orders`, log the consolidated line + a
**WARNING on `actual < requested`**, then close (on every path). Unreachable WS → results marked
`reachable=False` and returns fast (breaks when the session dies without opening). `DepthProbeResult`:
`name, option_exchange, requested_depth, reachable, actual_depth, is_50_depth,
per_level_orders_available, note`.

## Data flow (one packet)

```
RawWSTransport.on_message → normalize_market_data → _on_message
   ├─ if spot key match → _route_spot → _on_spot (DSM: validate, seed/expand) → _subscribe_strikes
   └─ _tee: proc_queue.put_nowait (sheds first)  +  raw_file_queue.put(timeout) (sheds last)
```

## DSM (§3.3.2)

Spot validation: drop `≤0`; drop a single tick `> 2%` from the 10-tick rolling **median** (spike guard —
real spot moves gradually, so large one-shot jumps are rejected). First valid tick seeds
`S_0`/`B_lower`/`B_upper` and `K_initial`. On breach (`S_t ≤ B_lower + T` / `S_t ≥ B_upper − T`) expand by
`E` and subscribe the newly covered strikes. **Never-shrink** (§3.3.4): only the set difference is
subscribed; nothing is unsubscribed intra-session.

## Threads · locks · FDs

- **One FEED thread** owns `run_session`, the reconnect loop, and the callbacks.
- `_spot_lock` (spot cache + median deque + boundaries) · `_sub_lock` RLock (`_subscriptions` map) ·
  `_client_lock` (serializes `send`). Order `_spot_lock → _sub_lock` (never held together — subscription
  I/O happens after the spot lock is released). `connect`/`disconnect` are FEED-thread-only, **not** under
  `_client_lock`. The tee takes no lock. **No I/O under any lock.**
- **One FD**: the WS socket, closed on every path (drop, reconnect, shutdown, preflight probe);
  close-before-reconnect.

## Config keys consumed
`openalgo.{websocket_url, api_key}`; `websocket.{transport, heartbeat_interval_sec, heartbeat_timeout_sec,
backoff_base, backoff_mult, backoff_max_sec}`; per-underlying `spot_symbol/spot_exchange/option_exchange/
requested_depth/initial_window/expansion_threshold/expansion_step`.

## Backpressure (§5.1, decision 28)
`proc_queue.put_nowait` — sheds **first** (WARNING + `proc_dropped_total`). `raw_file_queue.put(timeout=
0.5s)` — sheds **last** (ERROR + `raw_dropped_total`), the **single sanctioned raw-loss boundary**
(genuine disk saturation, §1.4).

## Deferred
`SdkTransport` body; `--status`/orchestration/teardown/mid-day REST-quote seeding (P6); the
`proc_queue` consumer — resampler + metrics (P4). The DB symbol stripping of `:50` is a P4/P5 concern.

## Genericization
No index/exchange/strike-step literal in engine code (state keyed by `name`). The only constants are
`_TBT_SUFFIX = ":50"` and `_TBT_MIN_DEPTH = 5` — the FYERS TBT trigger token + broker-default depth,
cited transport details, not index/exchange literals.
## Adaptive Depth Framework (F8, Plan_002 §20, forks F15/F16)

With `market_depth_framework.enabled: true` this module is also the framework's **only** broker-I/O
owner. With the flag off every path below is inert and the module behaves exactly as it did before F8.

**Construction.** `DepthWebSocketClient(..., framework=<FrameworkBridge | None>)`. `None` means the flag
is off. Otherwise the FEED thread builds one `BrokerAdapter(bridge.capability, AdapterTransport(...),
clock=self.time_fn)` — the capability object is the orchestrator's own, so planner and executor cannot
disagree about the premium budget.

**`AdapterTransport`** — a deliberate sibling of `_send_frame`, never a reuse. `_send_frame` swallows
send failures (right for a DSM frame in the never-shrink map); an adapter frame must fail loudly so the
leg is marked failed and re-planned, so this one **raises**, translating `TransportNotConnected` and
every other exception into the framework's `TransportError`. It borrows the existing connection and the
existing `_client_lock`, and creates no socket, thread, or connection lifecycle.

**Drain points (F15).** FEED is blocked inside `transport.run_session()` while connected, so the plan
mailbox is drained at the two callbacks that actually run on the FEED thread:

- tail of `_on_message`, **strictly after `_tee(packet)`** — audit first, always;
- end of `_on_open`, after authenticate + spot subscribe + coverage restore — the reconnect path.

Accepted residual: on a connected but silent feed a pending plan waits for the next packet. No timer.

**Ownership (F16).** With the flag on the framework owns **every** option-leg subscription. Both DSM
entry points (`seed_spot` and the `_route_spot` path) still advance boundaries — they feed the window
manager and the health file — but skip `_subscribe_strikes()`. Spot subscriptions stay DSM-owned. On
reconnect `_on_open` calls `_restore_framework_coverage()` **instead of** `_resubscribe_all()`, so
exactly one mechanism restores option coverage and no leg is subscribed twice.

**Observation.** Control frames reach `_observe_framework()` before the existing early return, so the
adapter sees subscribe acks and errors — an ack is never read as depth confirmation. Market-data packets
are observed after the tee. `_publish_framework_observation()` then recomputes `_live_wire` from the
adapter's `REQUESTED` / `DELIVERING` legs and hands `live_snapshot()` + `take_rejections()` back to the
bridge.

**`active_subscriptions`** is the union of the DSM never-shrink map (spots) and `_live_wire` (the
adapter's claimed wire symbols, `:50` where premium), so the health file reports real coverage. Written
whole, never mutated — no lock needed, and **no fourth lock was added**.

**`framework_stats()`** returns `plans_executed`, `plan_failures`, `desired_legs`, `premium_legs`,
`effective_budget`, `delivering_legs`, `claimed_wire_symbols` — or `None` when the flag is off.

**Reconnect is not a depth claim.** `handle_reconnect()` forgets everything and reissues baseline before
premium; nothing is confirmed until packets arrive. F7's UNKNOWN stays UNKNOWN.

**Threads / locks / FDs added: none.** `_close_adapter()` drops bookkeeping only — the adapter owns no
descriptor. See `Documents/framework_bridge.md` and `Documents/ARCHITECTURE.md` "Built state (F8)".
