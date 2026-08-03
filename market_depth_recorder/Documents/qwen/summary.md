# Summary: Generic Market-Depth Framework Documents (qwen/)

**Author:** Buffy (AI) — reading notes / understanding of the five documents in this folder.
**Date:** 2026-08-03
**Scope:** Summarizes `prompt_generic_market_depth_framework.md`, `planned_v1_GENERIC_FRAMEWORK_ARCHITECTURE.md`, `framework_implementation_plan.md`, `comprehensive_implementation_guide_part1.md`, `comprehensive_implementation_guide_part2.md`.

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
Depth Allocator       →  "Given the premium-depth budget, who receives it?"
Subscription Manager  →  "How do I reconcile desired state with live subscriptions?"
Broker Adapter        →  "How do I execute those operations for this specific broker?"
```

The "college admission" analogy used throughout: Window Manager = *who applied?* (build candidates),
Priority Policy = *how should they be ranked?* (rank only, admit nobody), Depth Allocator = *we have
only 100 seats, who gets in?* (apply the budget).

---

## 3. The layered architecture (the spec, ~2,470 lines)

### 3.1 Broker Capabilities Layer (Phase 1)
- **Purpose:** the contract between broker implementations and the generic framework.
- **Data models:** `BrokerCapabilities` (top-level), `TbtCapability` (available, `total_symbol_budget`,
  `max_connections`, `symbols_per_connection`, `max_channels`, `supported_exchanges`),
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
- **Interface:** `compute_priorities(candidates, market_context) -> List[PriorityScore]` (higher score = higher priority).
- **Built-in policies:** `AtmDistancePolicy` (decay by distance from ATM), `GammaPolicy`, `VolumePolicy`,
  `HybridPolicy` (weighted normalized combo, e.g., 0.4/0.4/0.2), plus `CombinedPolicy` in the guides.
- **Properties:** pluggable (swap strategies without touching other components), stability/hysteresis
  settings, fallback to ATM-distance on missing context.

### 3.4 Depth Allocator (Phase 4)
- **One responsibility:** apply the limited premium-depth budget to the ranked list — top-N get premium,
  rest get standard.
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

### 3.6 Broker Adapter (Phase 6)
- **The ONLY broker-aware layer.** Translates generic subscribe/unsubscribe into broker-specific calls.
- **Interface:** `connect()` / `disconnect()` / `subscribe(instruments, depth_type)` / `unsubscribe()`
  / `get_capabilities()` / `is_connected()`; adapter factory + registry.
- **FYERS sample:** capability loading (`tbt_budget=15`, 3 connections, 5/connection, 50 channels), symbol
  formatting (`NSE:...`), standard vs. TBT subscription paths, depth message parsing.
- **⚠ See §5 — the FYERS channel logic in these docs is based on the *disproven* protocol model.**

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
| 3 | 2–3 wks | Depth Allocator & Subscription Manager | budget algorithms, connection/channel assignment, state + reconciliation + lifecycle + batching |
| 4 | 2–3 wks | Broker Adapter & Integration | base adapter, WebSocket layer, FYERS adapter, orchestrator, lifecycle/health/metrics |
| 5 | 2–3 wks | Testing, Validation & Migration | >95% coverage, integration + stress tests, migration tools/guide from legacy FYERS code |
| 6 | 1–2 wks | Production Readiness | full docs, Docker/CI-CD, monitoring, staging dry run, release |

Targets: end-to-end latency < 50ms, window computation < 10ms, ranking < 5ms per 100 instruments,
500+ instrument universe, 99.9% uptime. Success metric: test coverage > 95%.

---

## 5. Key observations / discrepancies (important!)

1. **TBT channel model in these docs is stale — it contradicts the frozen protocol findings.**
   - Docs assume: "5 symbols per **channel**", "50 channels", channel assignment
     `channel_id = (i // 5) % 50 + 1`, integer channel ids.
   - `CLAUDE.md` (authoritative, frozen 2026-07-14, verified via official FYERS docs + probes):
     **5 symbols per *connection*, 3 connections per app per user → `tbt_budget = 15`**; channels are a
     **pause/resume logical grouping, not extra capacity**; a full NIFTY chain at 50-level is **not**
     achievable on one connection (needs the hybrid near-ATM@50 + rest@5); channel ids must be **strings**
     (`"1"`); the broker layer should expose **one logical `tbt_budget`** to the allocator with
     connection management hidden behind it.
   - → The capability data model (`total_symbol_budget=15, max_connections=3, symbols_per_connection=5`)
     is correct and matches the frozen truth, but the FYERS adapter skeletons' channel-assignment code
     must be rewritten against the real protocol.
2. **Nothing is implemented.** The `market_depth_framework/` package does not exist in the repo. The
   current codebase is the "legacy FYERS-specific implementation" that Phase 5 of the plan targets for migration.
3. **Package path inconsistency between docs:** the guides use `src/market_depth/...` while the plan uses
   `market_depth_framework/...` — needs resolving before implementation.
4. **Aligned with existing project discipline:** config-over-hardcoding (all limits/thresholds from YAML,
   fast-fail on invalid config), injectable clock/feed/writers for testability, lossless-raw + three-tier
   storage remain untouched, churn minimization mirrors the "never-shrink subscriptions" recovery principle.

---

## 6. Glossary (as used by the docs)

- **TBT** — Tick-by-Tick depth feed (50+ levels; FYERS: NSE/NFO only).
- **HSM** — High-Speed Market data feed (enhanced depth, more symbols).
- **ATM** — At-The-Money strike (closest to spot).
- **Premium depth** — enhanced depth (TBT/HSM); **standard depth** — basic ~5 levels.
- **Window / Universe** — the set of candidate instruments under consideration.
- **Churn** — number of subscription changes per reallocation (to be minimized).
- **Depth Allocator** — applies the premium budget to ranked candidates.

---

## 7. Document history note

- Architecture spec version 1.0 dated 2026-07-22; implementation plan v1.0; guides split into
  Part 1 (Phase 1) and Part 2 (Phases 2–6).
- This summary adds no new design decisions; it is a reading aid only.
