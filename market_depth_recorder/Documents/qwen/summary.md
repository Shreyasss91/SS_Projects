# Summary: Generic Market-Depth Framework Documents (qwen/)

**Author:** Buffy (AI) — reading notes / understanding of the five documents in this folder.
**Date:** 2026-08-03 · **Revised:** 2026-08-05 (post-reconciliation)

> **Revision note (2026-08-05).** The eight discrepancies catalogued in §5 have been **fixed in
> place** across `planned_v1_GENERIC_FRAMEWORK_ARCHITECTURE.md`, `framework_implementation_plan.md`,
> and both comprehensive guides. `prompt_generic_market_depth_framework.md` is the user's original
> requirement statement and was deliberately left untouched. §5 below now records each discrepancy
> **and its resolution**; §0 records the four decisions that governed the fixes.
**Scope:** Summarizes `prompt_generic_market_depth_framework.md`, `planned_v1_GENERIC_FRAMEWORK_ARCHITECTURE.md`, `framework_implementation_plan.md`, `comprehensive_implementation_guide_part1.md`, `comprehensive_implementation_guide_part2.md`.

---

## 0. Locked decisions (2026-08-05)

Four forks were put to the user before the reconciliation edits; the answers are binding on every
document in this folder and on the eventual implementation.

| # | Fork | Decision | Rationale |
|---|------|----------|-----------|
| D1 | Concurrency model | **Threads + bounded queues** — every framework interface is synchronous | The recorder already owns four threads and three bounded queues; an event loop would be a second, parallel concurrency framework. `asyncio.create_task` called from a thread with no running loop is a silent no-op, which is exactly the latent bug the old guides shipped. |
| D2 | Allocator naming collision | **Keep both, rename** — `BudgetAllocator` splits the broker budget across underlyings, then a per-underlying `DepthAllocator` assigns premium depth to top-N | The two documents described genuinely different jobs under one name. Merging them would have lost the multi-underlying split; renaming keeps both stages explicit. |
| D3 | Package path | **`market_depth_framework/`** | Matches the implementation plan; `src/market_depth/` is retired everywhere. |
| D4 | Ops scope | **Rescope to single-user** — keep circuit breaker, memory/disk monitors, data-integrity validation; replace Redis / PagerDuty / HTTP endpoints / active-active failover / S3 / user surveys with log-file + local-metrics equivalents, marked **Deferred** rather than deleted | One user, one host, one broker session. The deferred items are recorded so a future multi-instance deployment can pick them up rather than rediscover them. |

---

## 1. What this document set is

A Qwen-generated **architecture-and-implementation package** for evolving the existing FYERS-specific
Market Depth Recorder into a **broker-agnostic, capability-driven "Generic Market-Depth Framework."**

The five files form a strict dependency chain:

```
prompt_generic_market_depth_framework.md   ← the original user requirements
   ↓
planned_v1_GENERIC_FRAMEWORK_ARCHITECTURE.md   ← the design spec (authoritative architecture)
   ↓
framework_implementation_plan.md               ← the phased schedule (6 phases, ~12–16 weeks)
   ↓
comprehensive_implementation_guide_part1.md    ← deep-dive: Phase 1 (Foundation & Capabilities)
comprehensive_implementation_guide_part2.md    ← deep-dive: Phases 2–6
```

**Status: planning only.** None of this framework is implemented yet — the project root still contains
the legacy FYERS-specific recorder (`websocket_client.py`, `processor.py`, `instrument_manager.py`,
three-tier storage). The docs are the blueprint for a future migration.

---

## 2. Core design philosophy (from the prompt)

The single governing principle:

> **"FYERS is simply one broker implementation that advertises its market-data capabilities."**

- Stop thinking in terms of "how FYERS works"; think in terms of "what capabilities does this broker
  expose?"
- Tomorrow another broker may expose different TBT budgets, full-chain Level-2, Level-3, unlimited
  depth, premium feeds, or different subscription semantics — **the architecture remains unchanged;
  only the broker capability description changes.**
- The framework's only question to a broker: **"What capabilities do you expose?"**
- Everything **above the Broker Adapter** must remain 100% broker-agnostic — it must never know
  "FYERS", "TBT", "HSM", channels, connection limits, or broker quirks.

### Build order (each layer one clear responsibility)

```
Broker Capabilities   →  "What can this broker provide?"
Window Manager        →  "Which instruments belong to the active market universe?"
Priority Policy       →  "Among candidates, which are most important?"
Budget Allocator      →  "How is the broker-wide premium budget split across underlyings?"
Depth Allocator       →  "Within one underlying's slice, who gets premium depth?"
Subscription Manager  →  "How do I reconcile desired state with live subscriptions?"
Broker Adapter        →  "How do I execute those operations for this specific broker?"
```

Seven layers, not six: the single "Depth Allocator" of the original prompt was split in two per
**D2**. Everything above the Broker Adapter is synchronous and runs on the recorder's existing
threads per **D1** — no component owns an event loop.

The "college admission" analogy used throughout: Window Manager = *who applied?* (build candidates),
Priority Policy = *how should they be ranked?* (rank only, admit nobody), Depth Allocator = *we have
only 100 seats, who gets in?* (apply the budget) — with the seats themselves first divided between
faculties by the Budget Allocator.

---

## 3. The layered architecture (the spec, ~2,470 lines)

### 3.1 Broker Capabilities Layer (Phase 1)
- **Purpose:** the contract between broker implementations and the generic framework.
- **Data models:** `BrokerCapabilities` (top-level), `TbtCapability` (available, `total_symbol_budget`,
  `max_connections`, `symbols_per_connection`, `max_channels`, `supported_exchanges`) — note
  `max_channels` is recorded for documentation only and is **never multiplied into the budget**:
  `effective_budget = min(total_symbol_budget, max_connections × symbols_per_connection)`,
  `HsmCapability` (available, `max_symbols`, `supported_exchanges`), `ExchangeCapability`
  (per-exchange flags + limits). `DepthType` enum: `STANDARD` (5 levels) / `PREMIUM` / `TBT` (50+) / `LEVEL3`.
- **Key behaviors:** `get_premium_budget()` (prefers TBT budget over HSM), `supports_depth_type_for_exchange()`,
  `validate_symbol_count()`. Capabilities are **immutable at runtime**, stateless, read-only / thread-safe.
- **Config:** YAML `broker:` section describing TBT/HSM/standard limits, per-exchange overrides, feature flags.
- **Loaders/validators:** `CapabilitiesLoader` (YAML→dataclasses, caching, error hierarchy), capability
  consistency validation, fast-fail on invalid config.
- **Exception hierarchy:** `FrameworkError` base → `ConfigurationError`, `CapabilityError`, `ValidationError`,
  `WindowError`, `AllocationError`, `SubscriptionError`, `BrokerAdapterError`, `ConnectionError`, `RateLimitError`.

### 3.2 Window Manager (Phase 2)
- **One responsibility:** determine the **candidate universe** — "which instruments should be considered right now?"
- Deliberately ignorant of: broker capabilities, budgets, TBT/HSM, priorities, subscriptions, websockets.
- **Mechanics:** given spot price + config, compute ATM strike, then generate strikes in an ATM zone
  (e.g., radius 300pts, step 50) and an outside zone (radius 1500pts, step 100); emit CE+PE instruments
  per strike. Zone model in the guides: `ZoneManager` / `PriceZone` (ATM/ITM/OTM/CUSTOM, distance in
  points or %, `side` = CE/PE/BOTH) / `ZoneConfiguration`.
- **Dynamic behavior:** recompute on significant spot moves (threshold %), rebalance cooldown, diff
  old vs. new window (to_add / to_remove), event callbacks, per-underlying state.
- **State/threading:** mutable spot cache + derived window result; RLock for spot updates vs. computation;
  recompute every 5–10s, not every tick.

### 3.3 Priority Policy (Phase 3)
- **One responsibility:** **rank** the candidates by importance. Allocates nothing, knows nothing about budget size.
- **Interface (single, unified):** `compute_priorities(candidates: List[Instrument], market_context:
  MarketContext) -> List[PriorityScore]` plus `get_policy_name()`. The guides' rival
  `score_instruments(...)` / `MarketDataSnapshot` pair is gone. `MarketContext` is frozen
  (`as_of`, `spot_prices`, `atm_strikes`, `ltp`, `volume`, `open_interest`, `gamma`), and a shared
  `rank_scores()` helper stamps 1-based ranks exactly once, tie-breaking on symbol.
- **Built-in policies:** `AtmDistancePolicy` (decay by distance from ATM), `GammaPolicy`, `VolumePolicy`,
  `HybridPolicy` (weighted normalized combo, e.g., 0.4/0.4/0.2), plus `CombinedPolicy` in the guides.
- **Properties:** pluggable (swap strategies without touching other components), stability/hysteresis
  settings, fallback to ATM-distance on missing context. Policies are **stateless, synchronous and
  pure** — the same inputs must rank identically on replay.

### 3.4 Budget Allocator + Depth Allocator (Phase 4)

Two stages, per **D2**:

- **`BudgetAllocator`** — splits the broker-wide premium budget across the configured underlyings
  (`EQUAL` / `WEIGHTED` / `PRIORITY` / `DYNAMIC`), honouring per-underlying `min_slots` / `max_slots`
  and a `reserve_buffer`. The sum of allocations can **never** exceed the budget; unsatisfiable
  minimums are a `ConfigurationError` at startup, not a runtime surprise.
- **`DepthAllocator`** — within one underlying's slice, applies that slice to the ranked list: top-N
  get premium depth, everyone else falls back to standard.
- **Never knows** connection math (e.g., FYERS's internal 3 connections × 5 symbols) — it only sees
  "Depth Budget = 15".
- **Key outputs:** `AllocationDecision` (premium vs. standard sets) and `AllocationDiff`
  (promoted/demoted/added/removed) → drives churn measurement.
- **Churn minimization:** churn cooldown (e.g., 30s), hysteresis buffer, retain still-relevant
  allocations, evict only obsolete ones, promote newly important strikes.
- **Worked example in spec:** NIFTY spot 24000→24050 with budget 6 — shows promote `{24050 PE, 24150 CE}`,
  demote `{24000 PE, 23900 PE}`.
- **Guides add:** allocation strategies enum (EQUAL / WEIGHTED / PRIORITY / DYNAMIC) and per-underlying
  min/max slot constraints.

### 3.5 Subscription Manager (Phase 5)
- **One responsibility:** the **reconciliation engine** — convert the allocator's desired state into the
  *minimum* set of broker operations.
- **Mechanics:** desired state vs. current live state → diff → ordered `SubscriptionOperation`s
  (SUBSCRIBE / UNSUBSCRIBE / PAUSE / RESUME / MODIFY) with priorities; unsubscribe-before-subscribe
  to free capacity; batching (e.g., 10/batch, 100ms delay); retries with backoff; heartbeats + stale
  detection; health-check loop; recovery (reconnect, session restoration, resubscription, periodic full
  reconciliation ~5min).
- **State:** `SubscriptionState` (premium/standard/failed/pending sets) — rebuilt on restart.
- **Split across two threads (D1).** `reconcile()` is pure and runs on PROC: it diffs desired vs. live
  and emits a `ReconciliationPlan` onto a bounded plan queue. The SUBSCRIPTION thread drains that
  queue and performs **all** broker I/O. Unsubscribes are always applied before subscribes so
  capacity is freed first. The two rival subscription-manager designs in the earlier documents were
  collapsed into this one.

### 3.6 Broker Adapter (Phase 6)
- **The ONLY broker-aware layer.** Translates generic subscribe/unsubscribe into broker-specific calls.
- **Interface:** `connect()` / `disconnect()` / `subscribe(instruments, depth_type)` / `unsubscribe()`
  / `get_capabilities()` / `is_connected()`; adapter factory + registry.
- **FYERS sample:** capability loading (`tbt_budget=15`, 3 connections, 5 **per connection**, channels
  as pause/resume grouping only), symbol formatting via the configured `SymbolCodec` (never a hardcoded
  `NSE:` prefix), standard vs. TBT subscription paths, depth parsing that reads the **actual**
  `depth_levels` rather than truncating at 5.
- Premium slots are tracked in a per-connection ledger (`_tbt_assignment: Dict[str, int]`); a 16th
  premium leg is refused with a WARNING rather than silently dropped. Channel ids are **strings**.

### 3.7 Integration & Lifecycle (spec §8–9)
- **Startup:** load config → init adapter → load capabilities → init allocator (budget from capabilities)
  → init subscription manager → init policy → init window manager → connect → start spot feed → allocation loop.
- **Runtime flow:** spot update → Window Manager (recompute) → Priority Policy (rank) → Depth Allocator
  (budget + diff) → Subscription Manager (reconcile + execute) → Broker Adapter → depth feed → processor
  → storage (raw log + live metrics).
- **Shutdown:** stop loop → flush pending ops → unsubscribe all → disconnect → flush buffers → close
  files/DBs → exit.
- **Failure modes:** 3-level recovery (component-level retries → cross-component reconciliation → systemic
  degradation/alerting).

---

## 4. Implementation plan (framework_implementation_plan.md)

6 phases, ~12–16 weeks, incremental + test-driven + backward compatible:

| Phase | Duration | Focus | Key deliverables |
|-------|----------|-------|------------------|
| 1 | 2 wks | Foundation & Broker Capabilities | package structure, exception hierarchy, data models, capability loader/validator, YAML config |
| 2 | 2–3 wks | Window Manager & Priority Policy | universe construction, dynamic updates, multi-underlying, 4 built-in policies, registry |
| 3 | 2–3 wks | Budget/Depth Allocators & Subscription Manager | budget split + per-underlying depth assignment, per-connection premium ledger, state + reconciliation plan queue + lifecycle + batching |
| 4 | 2–3 wks | Broker Adapter & Integration | base adapter, WebSocket layer, FYERS adapter, orchestrator, lifecycle/health/metrics |
| 5 | 2–3 wks | Testing, Validation & Migration | >95% coverage, integration + stress tests, migration tools/guide from legacy FYERS code |
| 6 | 1–2 wks | Production Readiness | full docs, Docker/CI-CD, monitoring, staging dry run, release |

Targets: end-to-end latency < 50ms, window computation < 10ms, ranking < 5ms per 100 instruments,
500+ instrument universe, 99.9% uptime. Success metric: test coverage > 95%.

Phase 6 was rescoped under **D4**: it now covers local runtime concerns (the four threads, log
rotation, disk headroom, the end-of-session reprocess subprocess writing to a log file — never a
PIPE) plus a `Deferred` list for the multi-instance items. Premium coverage (share of the session
with all 15 TBT slots filled), rebuild fidelity under `--verify`, and `raw.packets.dropped == 0`
joined the success metrics.

---

## 5. Discrepancies found — and how each was resolved

All eight were fixed in place on 2026-08-05. The table is kept as a record of *what was wrong*, so a
later reader does not reintroduce any of it.

| # | Discrepancy as originally written | Resolution |
|---|-----------------------------------|------------|
| a | **TBT model stale.** Docs assumed "5 symbols per **channel**", "50 channels", `channel_id = (i // 5) % 50 + 1`, integer channel ids — implying a 250-symbol budget. | Rewritten to the frozen protocol: **5 per *connection*, 3 connections → `tbt_budget = 15`**; channels are a pause/resume grouping carrying **no** capacity; channel ids are **strings** (`"1"`); `max_channels` never enters the budget arithmetic. A full NIFTY chain at 50-level is unreachable on one connection — hence the hybrid (near-ATM @50 + rest @5). Evidence: `Documents/evidence/fyers_tbt_concurrency_20260714/tbt_concurrency_reconciliation_20260714.md`. |
| b | **Two different components both called `DepthAllocator`** (one splitting across underlyings, one assigning depth within one). | Split and renamed per **D2**: `BudgetAllocator` → `DepthAllocator`. Both stages documented; neither lost. |
| c | **Two rival `SubscriptionManager` designs** with incompatible state models. | Unified into one: pure `reconcile()` on PROC producing a `ReconciliationPlan`, all broker I/O on the SUBSCRIPTION thread, unsubscribe-before-subscribe. |
| d | **Two rival priority interfaces** — `compute_priorities(...)`/`MarketContext` vs. `score_instruments(...)`/`MarketDataSnapshot`. | One interface survives: `compute_priorities(candidates, market_context)` + `get_policy_name()`, with ranks stamped once by a shared `rank_scores()`. |
| e | **`asyncio` throughout** — `async def`, `await`, `AsyncMock`, and an `asyncio.create_task(self.rebalance())` fired from a *synchronous* method (a silent no-op with no running loop: the window would have frozen at its startup strikes). | Every interface is now synchronous on the existing four-thread topology per **D1**. Tests dropped `pytest.mark.asyncio` / `AsyncMock` and drive the queues directly. |
| f | **Package path inconsistency** — guides used `src/market_depth/...`, plan used `market_depth_framework/...`. | `market_depth_framework/` everywhere per **D3**. |
| g | **Genericization leaks** — hardcoded `NIFTY`/`NFO`/`50`/`NSE:` literals, f-string symbol construction, and a `_generate_instruments` that built **monthly** `%y%b` symbols for a **weekly**-chain recorder. | All three now come from `underlyings[]` in config, through `SymbolCodec` / `ExpiryCalendar` ABCs + registries; unknown codec names fast-fail rather than falling back. |
| h | **Ops assumed a team + fleet** — Redis, PagerDuty, HTTP health endpoints, active-active failover, S3 archival, user-satisfaction surveys. | Rescoped to single-user per **D4**: log file + local metrics file + local archive dir. Circuit breaker, memory/disk monitors and data-integrity validation are kept; the rest is listed under **Deferred**, not deleted. |

Latent defects caught while rewriting (recorded so they are not re-implemented): `BudgetAllocator.allocate`
returning `success=True` on an over-allocation; `reconcile()` treating a leg subscribed at the *wrong depth*
as "unchanged"; `_parse_depth_data` truncating a 50-level book with `range(5)`; `disconnect()` dropping
socket references without closing them.

**Still true:** nothing is implemented. The `market_depth_framework/` package does not exist in the repo;
the current codebase is the legacy FYERS-specific recorder that the plan's migration phase targets.

**Aligned with existing project discipline:** config-over-hardcoding (all limits/thresholds from YAML,
fast-fail with exit code 1 on invalid config), injectable clock/feed/writers for testability
(`FakeClock` for replay determinism), lossless-raw + three-tier storage untouched, and churn
minimization mirroring the "never-shrink subscriptions" recovery principle.

---

## 6. Glossary (as used by the docs)

- **TBT** — Tick-by-Tick depth feed (50+ levels; FYERS: NSE/NFO only).
- **HSM** — High-Speed Market data feed (enhanced depth, more symbols).
- **ATM** — At-The-Money strike (closest to spot).
- **Premium depth** — enhanced depth (TBT/HSM); **standard depth** — basic ~5 levels.
- **Window / Universe** — the set of candidate instruments under consideration.
- **Churn** — number of subscription changes per reallocation (to be minimized).
- **Budget Allocator** — splits the broker-wide premium budget across underlyings.
- **Depth Allocator** — applies one underlying's slice of that budget to its ranked candidates.
- **Channel** — a FYERS TBT pause/resume grouping. Carries **no** capacity; ids are strings.
- **`effective_budget`** — `min(total_symbol_budget, max_connections × symbols_per_connection)` = 15 for FYERS.

---

## 7. Document history note

- Architecture spec version 1.0 dated 2026-07-22; implementation plan v1.0; guides split into
  Part 1 (Phase 1) and Part 2 (Phases 2–6).
- **2026-08-05:** discrepancies (a)–(h) reconciled in place across the architecture doc, the plan,
  and both guides under decisions D1–D4. `prompt_generic_market_depth_framework.md` remains the
  user's original, unmodified requirement statement.
- This summary records the decisions but originates none of them; the architecture doc's §0
  Locked-Decisions table is the authority.
