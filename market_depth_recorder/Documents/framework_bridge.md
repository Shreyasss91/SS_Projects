# framework_bridge.py — module reference (F8, Plan_002 §20)

The **only** seam between the recorder and `market_depth_framework`. Everything the framework needs
from the recorder, and everything the recorder needs from the framework, crosses here — which is why
the framework itself still imports nothing from the recorder (AST-asserted in
`tests/test_framework_package.py`).

It exists because the two halves of a rebalance run on **different threads**: PROCESSOR decides, FEED
executes. The bridge is the hand-off, and it is deliberately the smallest thing that can be one:
two single-slot mailboxes and a counter block. **No thread, no lock, no queue, no timer, no file
descriptor** — a diff-against-HEAD audit asserts this.

## Responsibilities

1. Own the `FrameworkOrchestrator` and run its pass (`maybe_rebalance`, `force_rebalance`, `reset`).
2. Publish the resulting `SubscriptionPlan` to FEED as a `PlanEnvelope` (forward channel).
3. Receive FEED's delivery-derived live snapshot and rejections as an `Observation` (reverse channel),
   and feed them into the next pass.
4. Contain every framework failure: a raising orchestrator is counted, logged, and never reaches
   PROCESSOR's loop.
5. Build the framework's candidate universe from the recorder's `InstrumentManager`.

## Public API

| Symbol | Purpose |
| --- | --- |
| `LatestWinsMailbox` | `deque(maxlen=1)` hand-off. `publish(item)`, `take() -> item \| None`, `pending`, `stats()` (`published` / `taken` / `superseded`). |
| `PlanEnvelope` | Frozen: `plan`, `desired`, `trigger`, `sequence`, `at`. What FEED executes. |
| `Observation` | Frozen: `live` (whole snapshot, `leg -> DepthType`), `rejections`, `at`. What PROCESSOR's next pass consumes. |
| `build_universe(config, instrument_manager)` | Recorder config + `InstrumentManager` -> the framework's candidate universe. |
| `FrameworkBridge` | The seam itself (below). |
| `framework_bridge_for(config, instrument_manager, *, clock)` | Factory. Returns `None` when the block is absent or `enabled: false` — the single place the flag is interpreted. |

### `FrameworkBridge`

| Member | Thread | Notes |
| --- | --- | --- |
| `maybe_rebalance(spots)` | PROCESSOR | Runs a pass if the orchestrator says one is due; publishes a `PlanEnvelope` if the plan has actions. |
| `force_rebalance(spots, trigger)` | PROCESSOR | Same, unconditionally, with an explicit trigger label (`initial`, `window_change`). |
| `reset()` | PROCESSOR (shutdown) | Forgets desired coverage. Never raises. |
| `take_plan()` | FEED | The forward mailbox. |
| `publish_observation(live, rejections=())` | FEED | The reverse mailbox. **Never raises** — a broken clock is swallowed and logged. |
| `plans` / `observations` | — | The two mailboxes, exposed for stats and tests. |
| `orchestrator` / `capability` / `effective_budget` | — | The planning objects. `capability` is the orchestrator's **own** layer, so FEED's adapter renders the wire against the very budget the plan was allocated from. |
| `stats()` | PROCESSOR | JSON-safe: `passes`, `plans_published`, `failures`, `observations`, `last_trigger`, `last_pass_at`, `last_error`, `effective_budget`, `desired_legs`, `live_legs`, `pending_rejections`, `eligible_underlyings`, `plan_mailbox`, `observation_mailbox`. |

## The two mailboxes — why latest-wins, and why not a queue

Both channels carry **whole state**, never a delta: a plan is the full set of actions that converge
desired on live, and an `Observation` is the entire live snapshot. A stale item is therefore worse than
no item, and a backlog is worse than both — under a slow FEED a `Queue` would deliver a queue of plans
that each describe a world that no longer exists. `deque(maxlen=1)` makes supersession the default and
counts it (`superseded`), which is the honest reading: the newer plan already accounts for whatever the
older one wanted.

One exception is deliberate: **an empty plan is never published.** Publishing it would evict a pending
plan FEED had not executed yet while carrying no action of its own. The pass itself still counts.

Symmetrically, an **absent** observation means "no news", not "every leg died" — the orchestrator keeps
using the last snapshot it was given.

## Fault containment

`maybe_rebalance` / `force_rebalance` wrap the whole pass. A raising orchestrator increments `failures`,
records `last_error` (`Type: message`), logs at exception level, and returns `None`. `reset()` and
`publish_observation()` are likewise total. This is directive item 1's requirement: a framework failure
must never terminate PROCESSOR, and must never be mistaken for a plan.

## Threads, locks, FDs owned

**None of any kind.** `LatestWinsMailbox` relies on `deque.append` / `deque.popleft` being atomic under
the GIL, with exactly one writer and one reader per mailbox — which is what makes the fourth lock the
F15 directive forbids unnecessary. The bridge never performs I/O, never reads a real clock (the clock
is injected), and never touches a socket or a file.

## Config keys consumed

Only `market_depth_framework.*` (via `market_depth_framework/config.py`) plus `underlyings[]` for the
universe. The block is **excluded from `config_hash`** — a recorder config with the block hashes
identically to the same config without it, so enabling the framework does not look like a new session
to the DB.

## Tests

`tests/test_framework_bridge.py` (15) drives the bridge through a stubbed orchestrator — publication,
supersession, the empty-plan rule, the reverse channel, rejection hand-over-once, fault containment,
lifecycle, stats. `tests/test_framework_integration.py` (47) drives it through the **real** orchestrator
and the **real** adapter against a fake transport.

## See also

`Documents/market_depth_framework.md` (the framework itself, including `orchestrator.py`),
`Documents/websocket_client.md` (FEED-side execution, forks F15/F16),
`Documents/processor.md` (the pass trigger), `Documents/ARCHITECTURE.md` "Built state (F8)".
