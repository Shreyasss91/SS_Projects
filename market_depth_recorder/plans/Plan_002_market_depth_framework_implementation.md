# Plan_002 — Generic Market-Depth Framework — Implementation Plan

> **Status: F0 APPROVAL GATE. All forks in §20 are CLOSED (2026-08-25). No `market_depth_framework/`
> code exists, and none may be written until phase F1's scope is explicitly approved. Do not start F1.**

---

## 1. Document control

| Field | Value |
|---|---|
| Document | `plans/Plan_002_market_depth_framework_implementation.md` |
| Companion | `plans/Plan_001_market_depth_recorder_implementation.md` (recorder P0-P10; still authoritative for everything already built) |
| Opened | 2026-08-25 |
| State | Planning complete. §20 forks F3-F14 decided 2026-08-25. Awaiting F0 approval; F1 not started. |
| Authority | This document is the **only** plan for the framework, exactly as Plan_001 is the only plan for the recorder. Do not create a second copy anywhere (see the pointer stub in `Documents/Complete_Project_Plan_*.md` for why). |
| Live doc | Same convention as Plan_001: record decisions with rationale when a fork closes; embed a phase's exhaustive `- [ ]` checklist **before** implementing it; tick items as they complete. |

---

## 2. Context — why the framework exists

Plan_001 delivered a working recorder (P0-P10, 267 tests green). P10-F then established, and froze,
the depth-capacity reality that the recorder was built against a wrong model of:

- FYERS caps Market-Depth at **5 symbols per _connection_**, **3 connections per app/user**,
  **50 channels per connection that carry no capacity** (pause/resume grouping only).
- The effective ceiling is therefore **`tbt_budget = 15`**, not the 250 the earlier docs assumed.
- Consequence today: the recorder subscribes ~82 NIFTY legs at `:50` and only ~5 ever stream
  concurrently — roughly 6% of the chain. SENSEX is unaffected (BFO, 5-level, whole chain streams).

Plan_001 decision **17** reopened D2 and made the **hybrid** the design, not a fallback: near-ATM legs
at 50-level up to the budget, the rest at 5-level, with the *choice of which strikes* made by a
window/priority/allocation layer that is never hardcoded to an index name. Plan_001 decision **16**
requires that layer to consume **one logical `tbt_budget`** exposed by a broker-capability layer, so the
engine stays broker-agnostic (another broker may expose `1x20`, `5x10`, or full-chain-50).

**That layer is what Plan_002 builds.** It is the piece Plan_001 explicitly deferred.

---

## 3. Scope boundary — Plan_001 vs Plan_002

| Concern | Owner | Note |
|---|---|---|
| Feed transport, reconnect/backoff, raw tee | Plan_001 (`websocket_client.py`) | Unchanged |
| Lossless raw Tier-0 writer | Plan_001 (`file_writer.py`) | Unchanged |
| Metric computation, uniform 1s grid, degradation ladder | Plan_001 (`processor.py`) | Unchanged behaviour |
| Tier-1 live SQLite/WAL writer | Plan_001 (`database_writer.py`) | Unchanged |
| Tier-2 DuckDB rebuild by replay | Plan_001 (`replay.py`) | Unchanged |
| Instrument/expiry resolution, preflight depth probe | Plan_001 (`instrument_manager.py`, `websocket_client.py`) | Reused, possibly re-seamed |
| **Which legs are candidates** | **Plan_002** — Window Manager | New |
| **How candidates rank** | **Plan_002** — Priority Policy | New |
| **How the broker budget splits across underlyings** | **Plan_002** — Budget Allocator | New |
| **Which legs get premium depth** | **Plan_002** — Depth Allocator | New |
| **Desired vs live subscription reconciliation** | **Plan_002** — Subscription Manager | New |
| **What the broker can actually do** | **Plan_002** — Broker Capabilities + Adapter | New |

**Hard scope rules for this plan**

- Do **not** modify completed P0-P10 behaviour. Integration in a later phase is additive and
  flag-gated; the existing path stays runnable until the new path is validated live.
- Do **not** widen the degraded heavy-metric set or change P4 behaviour.
- Do **not** create `market_depth_framework/` code until phase F1's scope is explicitly approved.
  Planning is complete and all forks are closed (§20), but F0's approval gate (§22.1) is still open.

---

## 4. Source-document audit — authority ranking

Four Qwen-generated documents describe a framework. **They are drafts, not authority.** Existence is
not correctness; each claim below was checked against the frozen facts and the recorder's real code.

| Rank | Source | Authority |
|---|---|---|
| 1 | `market_depth_recorder_design.md` (in-folder) | **Source of truth** for the recorder |
| 2 | `plans/Plan_001_...md` decisions 15-18 | **Frozen** protocol + hybrid design decisions |
| 3 | `Documents/patches/tbt_concurrency_reconciliation_20260714.md` | **Canonical evidence** for `tbt_budget = 15` |
| 4 | The recorder source itself (`*.py`) | Ground truth for what is actually built |
| 5 | `Documents/qwen/planned_v1_GENERIC_FRAMEWORK_ARCHITECTURE.md` | **Draft.** Best of the four; layering and dataclasses are broadly sound; its concurrency contract and several allocation details are wrong (§21). |
| 6 | `Documents/qwen/framework_implementation_plan.md` | **Draft.** Week-by-week schedule; useful as a task inventory, not as a phase plan. Rewritten here as §22. |
| 7 | `Documents/qwen/comprehensive_implementation_guide_part1/2.md` | **Draft.** Large; treat as reference prose only. |
| 8 | `Documents/qwen/summary.md`, `prompt_generic_market_depth_framework.md` | Context only |

Where a Qwen document and a ranked-higher source disagree, the higher source wins and the
disagreement is recorded in §21.

---

## 5. Locked decisions carried in from Plan_001

These are **not reopened** by this plan.

- **D15 — `tbt_budget = 15` is FROZEN.** 5 Market-Depth symbols per connection x 3 connections;
  channels are a pause/resume grouping and carry no capacity. Channel ids are **strings** (`"1"`).
  Do not revisit without new external evidence.
- **D16 — The allocator consumes ONE logical `tbt_budget`.** Connection management (3 x 5) is hidden
  behind the broker-capability layer. `tbt_budget` is a broker **capability**, never a framework
  constant and never a literal in engine code.
- **D17 — HYBRID is the design, not a fallback.** Near-ATM legs at 50-level up to the budget, the rest
  at 5-level. Which strikes get the scarce slots is decided by the Window Manager plus the allocators,
  from config — never hardcoded.
- **D18 — OPEN.** Perf/RSS at true scale (up to 15 legs @50-level plus the hybrid remainder) has never
  been measured. The P10-E numbers were taken at <=5 NFO @50 + ~120 SENSEX @5. **Closing D18 is a
  Plan_002 deliverable** (phase F10, §22).

---

## 6. Locked decisions — Plan_002

### F1 — DECIDED (2026-08-25): there is NO SUBSCRIPTION thread

The recorder has exactly **four** worker threads and the framework must conform to the existing
architecture rather than the other way round. **The framework itself is synchronous and threadless.**

| Thread | Class | Owns |
|---|---|---|
| **FEED** | `websocket_client.DepthWebSocketClient` | broker/WebSocket I/O, DSM, **subscription I/O** |
| **RAW WRITER** | `file_writer.RawTickFileWriter` | raw queue -> lossless Tier-0 raw file |
| **PROCESSOR** | `processor.TickProcessor` | spot/priority computation, `BudgetAllocator`, `DepthAllocator`, reconciliation / desired subscription state |
| **DB WRITER** | `database_writer.SQLiteLiveWriter` | live queue -> Tier-1 store |

Flow:

```
PROCESSOR --(desired subscription plan)--> SubscriptionManager --(subscription actions)--> FEED --> broker subscription I/O
```

**Rationale.** Adding a fifth thread would add a fifth FD-owning lifecycle, a fifth join in the
teardown drain order, and a second place that touches the broker socket — against a project whose
concurrency section is explicitly marked "High Risk" and whose FD hygiene rule is that every thread is
an FD. The framework's work is pure computation; it does not need a thread of its own, and broker I/O
already has exactly one owner.

**Binding consequences**

- `SubscriptionManager` is **not a thread** and owns no thread. It is a synchronous component whose
  `reconcile()` is a pure function called on PROCESSOR.
- Any framework contract that assumes `FEED / PROC / SUBSCRIPTION / DB` is replaced by
  `FEED / RAW WRITER / PROCESSOR / DB WRITER`. This **supersedes** Qwen `§0.1` and `§6.7`.
- **Do not introduce a fifth recorder thread.**
- The hand-off from PROCESSOR to FEED is a plan object crossing a boundary, not a queue drained by a
  new thread. How that hand-off is carried is an implementation question, listed in §20 (F14).
- *Factual note, not a change of decision:* the DB WRITER writes the **Tier-1 SQLite/WAL** store.
  DuckDB is the Tier-2 store, rebuilt offline by replay. The decision's ownership assignment is
  unaffected.

### F2 — DECIDED (2026-08-25): permanent standard-depth baseline + mutable premium-depth overlay

```
SubscriptionState
  baseline         -> eligible legs subscribed at standard depth
  premium_overlay  -> <= tbt_budget legs currently assigned 50-level depth
```

Two explicitly named invariants replace the now-ambiguous "`_subscriptions` never-shrink":

- **BASELINE MONOTONICITY** — once an eligible leg enters baseline coverage, it remains subscribed
  until graceful session shutdown/reset.
- **PREMIUM OVERLAY MUTABILITY** — premium 50-level assignment may be promoted, demoted, or
  reassigned during the session, subject to the broker's logical `tbt_budget`.

A premium **demotion is a depth transition 50 -> 5, not an unsubscribe**; a promotion is 5 -> 50.
`tbt_budget = 15` remains a broker capability, not a framework constant.

Desired-state transition table (binding):

| Current | Desired | Action |
|---|---|---|
| absent | standard | subscribe |
| absent | premium | subscribe at 50 |
| standard | standard | no-op |
| standard | premium | upgrade 5 -> 50 |
| premium | premium | no-op |
| premium | standard | downgrade 50 -> 5 |
| standard/premium | absent | **forbidden during normal session** |
| any | shutdown/reset | reset baseline/subscription state |

**"Never-shrink" must not be read as "premium assignments can never be demoted."** It constrains the
baseline only.

**Binding consequences**

- Qwen `§6.3 reconcile()` emits `UNSUBSCRIBE` for `allocation_diff.removed` and unsubscribe-then-
  subscribe for demotions. Both are **superseded**: `removed` cannot produce an unsubscribe (row 7 of
  the table), and a demotion is a depth transition whose mechanism is measured, not assumed
  (F8 -> §14.4; F9 -> §20.1).
- The recorder's `_subscriptions` map is keyed by **wire symbol**, and the wire symbol *encodes depth*
  (`wire_symbol()` appends `:50`). A depth transition therefore changes the key, which the current
  never-shrink map cannot express. Re-keying is required — F10, decided (§9).

---

## 7. Corrected concurrency contract (supersedes Qwen §0.1)

Rules that must hold, unchanged from Plan_001 and CLAUDE.md:

- Lock order is always `spot_lock -> RLock`. No framework component acquires them in the other order.
- **No network or file I/O inside a lock.** Framework components compute under lock (if at all),
  release, and hand the result on.
- Under overload the shed order is `proc_queue` first, then `db_queue`, `raw_file_queue` last.
  Framework work rides `proc_queue` and is therefore expendable by design — a dropped rebalance is
  recoverable on the next pass; a dropped raw packet is not.
- Framework component state is single-writer, owned by PROCESSOR, and needs no lock of its own. Any
  state FEED must read is passed to it as an immutable plan, not shared.
- `connect()` / `disconnect()` remain FEED-thread-only and outside `client_lock`.

---

## 8. Corrected pipeline (supersedes Qwen §0.2)

```
Broker Capabilities  -> "What can this broker provide?"          effective_budget (FYERS: 15)
        |
Window Manager       -> "Which legs are candidates?"             per underlying
        |
Priority Policy      -> "Among candidates, which matter most?"   ranks; allocates nothing
        |
Budget Allocator     -> "How does the budget split by underlying?"  premium slots per underlying
        |
Depth Allocator      -> "Within an underlying, who gets premium?"   top-N of the ranking
        |
Subscription Manager -> "Desired vs live -> ordered actions"      synchronous, no thread (F1)
        |
Broker Adapter       -> "How does FYERS execute this?"            3 conns x 5 symbols, hidden
```

Stages 1-6 run on **PROCESSOR**. Stage 7 executes on **FEED**.

Qwen §0.2's worked example ("15 -> NIFTY 10, SENSEX 5") is **not** adopted — it disagrees with its own
allocator (§21 D-1) and it allocates premium slots to an underlying that cannot use them (F13, decided — §13.1).

---

## 9. State model

```
SubscriptionState                     # owned by PROCESSOR, single writer
  baseline:         Set[Instrument]   # monotone within a session (F2)
  premium_overlay:  Set[Instrument]   # |premium_overlay| <= effective_budget; mutable (F2)
  pending:          Set[Instrument]   # actions handed to FEED, not yet confirmed
  failed:           Set[Instrument]   # last action rejected; retried next pass
  last_updated:     float             # injected clock
```

Derived, never stored: `standard = baseline - premium_overlay`.

Invariants to assert in tests:

1. `premium_overlay` is a subset of `baseline` — a leg is always subscribed before it can be premium.
2. `len(premium_overlay) <= effective_budget` at every point, including mid-transition.
3. `baseline` is non-decreasing between `start()` and `reset()`.
4. No instrument appears in both `pending` and `failed`.
5. After `reset()`, all four sets are empty.

**Key = leg identity (F10, decided).** These sets are keyed by `Instrument`; **depth is a value, never
part of the key.** The wire symbol and its `:50` suffix become a rendering detail owned by the Broker
Adapter. This is what makes "the same leg at a different depth" expressible at all.

---

## 10. Component contracts

All interfaces are **synchronous** (Plan_001 D16 + F1). All clocks are **injected**. No component
imports an index name, exchange code, or strike step.

### 10.1 Broker Capabilities

- **Answers:** what depth levels this broker/exchange pair supports, and one logical premium budget.
- **Exposes:** `effective_budget = min(total_symbol_budget, max_connections * symbols_per_connection)`.
  `max_channels` **never** enters budget arithmetic.
- **Sentinel:** `UNLIMITED_BUDGET` is an `int` (not `float('inf')`) so budget arithmetic and the
  `-> int` contract stay honest.
- **Does not know:** underlyings, strikes, ranking, subscriptions.
- **Validated at startup**; a missing or out-of-range capability value is a fast-fail, exit 1.

### 10.2 Window Manager

- **Answers:** which legs are candidates for one underlying, given spot.
- **Owns:** the ATM zone and expansion zones, per-underlying, from `underlyings[]` config.
- **Seams:** `SymbolCodec` (symbol construction) and `ExpiryCalendar` (weekly/monthly rollover,
  holidays) are registered per rule, not per index name.
- **Does not know:** budgets, depth tiers, subscriptions, ranking.

### 10.3 Priority Policy

- **Answers:** among candidates, which matter most.
- **Interface:** `compute_priorities(candidates: List[Instrument], ctx: MarketContext) -> List[PriorityScore]`,
  returning `rank_scores(scores)` so ordering is defined in exactly one place, with a total order
  (score desc, then symbol) so an unchanged market yields an unchanged ranking.
- **`MarketContext` is a frozen snapshot**, rebuilt per pass, never mutated in place — this is what
  makes ranking replayable from the raw log.
- **Allocates nothing.**

### 10.4 Budget Allocator

- **Answers:** how one broker-wide premium budget splits across underlyings.
- **Interface:** `allocate_budget(total_budget: int, candidate_counts: Mapping[str, int]) -> Dict[str, int]`.
- **Invariants (assert in tests):** sum <= `total_budget`; `result[u] <= candidate_counts[u]`;
  every configured underlying answered (0 permitted).
- **Integer arithmetic throughout**, largest-remainder split — independent per-underlying rounding can
  sum above the budget and blow a hard broker limit.
- **`min_per_underlying` applies only to premium-eligible underlyings** (F7 + F13 clarification). A
  non-premium-capable underlying contributes no premium demand and receives no floor.
- **Unspent slots are redistributed** deterministically in weight order to eligible underlyings that
  still have headroom (F6). Redistribution reads candidate *capacity* and configured *weights* only —
  **never** individual priority scores, which would collapse the §10.4 / §10.3 separation.
- Full semantics and worked examples: §13.

### 10.5 Depth Allocator

- **Answers:** within one underlying, which ranked legs get premium depth.
- **One instance per underlying** — a shared instance would let a NIFTY reallocation reset SENSEX's
  cooldown.
- **Owns:** current allocation, last-allocation time, a `deque(maxlen=history_limit)` debug ring
  (bounded by construction; an unbounded list is a slow leak in an all-session process).
- **Budget is passed per call, not stored** — the split changes whenever another underlying's
  candidate count changes.
- **Hysteresis is displacement-based (F3):** a challenger ranked inside the top `budget` displaces the
  worst-ranked incumbent. Hysteresis protects against borderline flapping; it never locks out a
  genuinely top-ranked leg.
- **Rank is 1-based, one basis only (F4):** `PriorityScore.rank`. No positional index anywhere.
- **Cooldown gates premium reshuffles only (F5).** Baseline additions bypass it entirely.
- **`removed` produces no action (F8);** `added_new` and `promoted_to_premium` are disjoint by
  construction. Full semantics: §14.

### 10.6 Subscription Manager — **not a thread** (F1)

- **Answers:** given desired state and live state, what actions does FEED perform.
- **Interface:** `reconcile(desired, current) -> SubscriptionPlan` — **pure**, no I/O, no mutation,
  called on PROCESSOR.
- **Ordering is fixed, not priority-sorted:** all capacity-releasing actions (demotions) precede all
  capacity-claiming actions (promotions). Against a hard budget, a promotion issued before the
  demotion that frees its slot is rejected by the broker. A numeric priority field would invite an
  unstable sort that violates this; there is no such field.
- **Never emits an unsubscribe during a normal session** (F2, transition-table row 7).
- **The depth-transition mechanism is deliberately unspecified until phase F7 measures it (F9).** The
  Subscription Manager emits a *transition intent* (`upgrade` / `downgrade`); whether the adapter
  realises it as one call or as release-then-claim is the adapter's business, decided by evidence.
- **Plan hand-off to FEED is a single-slot latest-wins mailbox (F14, provisional).** Confirmed during
  phase F8 against the real FEED loop. It introduces **no thread and no second broker-I/O owner**.

### 10.7 Broker Adapter

- **Answers:** how a plan is executed for one broker.
- **Hides:** connections, channels, channel-id string typing, per-connection 5-symbol packing,
  and the fact that FYERS needs 3 connections at all.
- **Runs on FEED.** No other thread calls it.
- **FD contract:** closes before reconnect; every socket released on success, error, reconnect, and
  shutdown paths.

### 10.8 Framework Orchestrator

- A thin synchronous facade that PROCESSOR calls once per rebalance: snapshot -> window -> rank ->
  budget -> depth -> reconcile -> plan. Owns no state beyond the component instances.
- Exists so the recorder has **one** call site to integrate, not seven.

### 10.9 Configuration + validation

- Every framework knob resolves from `config.yaml`. Missing or out-of-range values **fast-fail at
  startup with exit code 1** — never a silent default.
- Validation is one pass at startup, before any thread starts.

---

## 11. Data flow — one rebalance pass

```
FEED       receives ticks -> tee -> raw_file_queue (lossless) + proc_queue
PROCESSOR  drains proc_queue, updates metrics on the uniform 1s grid
PROCESSOR  on a rebalance trigger (F11 = interval OR window change, §14.5):
             1. build frozen MarketContext (spot, ATM, LTP/greeks/volume if configured)
             2. WindowManager.candidates(u)             for each underlying
             3. PriorityPolicy.compute_priorities(...)  for each underlying
             4. BudgetAllocator.allocate_budget(effective_budget, candidate_counts)
             5. DepthAllocator[u].allocate(ranked, budget[u])   for each underlying
             6. SubscriptionManager.reconcile(desired, current) -> SubscriptionPlan
             7. hand the plan to FEED                   (F14 provisional, §20.2)
FEED       executes the plan via BrokerAdapter; reports outcome back as state
```

The rebalance is **expendable**: if `proc_queue` sheds, the pass is skipped and recomputed next
trigger. Nothing in this path may block the raw tee.

---

## 12. Reconciliation semantics

Binding rules, derived from F2:

1. The transition table in §6 F2 is the complete action set. There is no other transition.
2. `absent -> standard` and `absent -> premium` are the only ways `baseline` grows; it never shrinks
   until `reset()`.
3. A leg that leaves the candidate window stays in `baseline` at standard depth. It loses only its
   premium slot, if it had one.
4. Demotions are emitted before promotions within a single plan.
5. A plan is idempotent under replay: applying it twice to the same state yields the same state.
6. On reconnect, the desired state is `baseline` (all of it) with `premium_overlay` re-applied;
   the adapter reports zero live subscriptions and the whole set is re-issued.
7. A rejected action moves the leg to `failed`; the next pass retries it. Failures are never silently
   dropped and are logged.
8. A periodic full reconciliation is the backstop against drift, run on the same trigger as the
   ordinary pass (no second loop, no second thread).

---

## 13. Budget-allocation semantics

Settled by this plan:

- `effective_budget = min(total_symbol_budget, max_connections * symbols_per_connection)`;
  `max_channels` is never a factor.
- Largest-remainder integer split; `sum(result) <= total_budget` is asserted, not assumed.
- `min_per_underlying` is a floor so a small underlying is never starved to zero.
- There is deliberately **no** `premium_budget` key in allocator config — the budget is a broker
  capability, never a number hand-copied into config where it can drift from the broker's real ceiling.

### 13.1 Premium eligibility (F13)

Premium eligibility is a **broker/exchange capability**, resolved by the capability layer, never by
hand-maintained allocator config:

```
eligible(u) := broker supports premium depth on u.option_exchange
```

An underlying that is not eligible reports **`candidate_count = 0`** to the Budget Allocator, receives
**0** premium budget, and takes **no floor**. It still receives **full standard-depth baseline
coverage** — eligibility governs the premium overlay only, never the baseline.

Concretely for FYERS today: NIFTY on NFO is eligible; SENSEX on BFO is not, because BFO has no TBT.
Without this rule the drafts' own example spends 2 of 15 scarce slots on an underlying physically
unable to use them.

### 13.2 `min_per_underlying` applies to eligible underlyings only (F7 + F13)

Read literally over *all configured* underlyings, F7's startup check would demand a floor for SENSEX
and directly contradict F13's "SENSEX gets 0". The floor is therefore scoped to eligibility:

```
eligible_underlyings = [u for u in underlyings if eligible(u)]

# startup validation - fast-fail, exit 1
assert min_per_underlying * len(eligible_underlyings) <= effective_budget
```

Because runtime `active` is always a subset of `eligible_underlyings`, the startup check makes the
drafted mid-session `ConfigurationError` **unreachable**. It is therefore deleted, not merely guarded:
`allocate_budget()` has no raising path and cannot kill the PROCESSOR thread.

### 13.3 Redistribution of unspent slots (F6)

After the largest-remainder pass, each underlying is capped at its candidate count, which can leave
slots unspent. Those slots are redistributed, **one at a time, round-robin in descending weight order**
(ties broken by name for determinism), to eligible underlyings that still have headroom:

```
leftover = total_budget - sum(result.values())
while leftover > 0:
    receivers = [u for u in eligible if result[u] < candidate_counts[u]]
    if not receivers:
        break                      # genuine surplus: fewer candidates than budget
    for u in sorted(receivers, key=weight_desc_then_name):
        if leftover == 0:
            break
        result[u] += 1
        leftover -= 1
```

The loop terminates: every inner step decrements `leftover`, and the outer loop exits as soon as no
underlying has headroom. It reads **candidate capacity and configured weights only** — never a
`PriorityScore`. Coupling redistribution to individual ranking would collapse the §10.4 / §10.3
separation, which is why option (c) was rejected.

### 13.4 Worked examples

`effective_budget = 15`, `min_per_underlying = 2`, weights NIFTY 2.0 : SENSEX 1.0.

**Example A — one eligible underlying, demand exceeds budget.**

```
NIFTY  eligible, candidates = 20
SENSEX not eligible          ->  candidate_count = 0, no floor

eligible = {NIFTY};  floors = {NIFTY: 2};  remaining = 13
weighted split over eligible -> NIFTY 13
NIFTY = min(2 + 13, 20) = 15        SENSEX = 0
leftover = 0

=> NIFTY 15, SENSEX 0   (15 of 15)
```

**Example B — two eligible underlyings, one capped by its candidate count.**
(Hypothetical: both eligible, to exercise redistribution.)

```
NIFTY  candidates = 5
SENSEX candidates = 20

floors = {NIFTY: 2, SENSEX: 2};  remaining = 11
exact  = NIFTY 7.33, SENSEX 3.67  ->  share 7 / 3, leftover 1
largest remainder (.67 > .33)     ->  SENSEX +1  ->  7 / 4
NIFTY  = min(2 + 7, 5)  = 5       (capped; 4 slots freed)
SENSEX = min(2 + 4, 20) = 6
sum = 11, leftover = 4

redistribution: receivers = [SENSEX] (NIFTY has no headroom)
SENSEX += 4 -> 10

=> NIFTY 5, SENSEX 10   (15 of 15)
```

Both examples spend the full budget. The drafts' three conflicting answers (§21 D-1) are superseded by
the algorithm above; the example in Qwen §5.1.4 must be recomputed against it before reuse.

---

## 14. Depth-allocation and ranking semantics

Settled by this plan:

- Selection is top-N of the ranking, with hysteresis so a leg oscillating around `rank == budget` is
  not promoted and demoted on alternate passes — that is pure churn against a hard budget, and it puts
  a gap in the very book being recorded.
- A cooldown bounds how often premium assignments may change.
- The first pass always runs; cooldown is only skippable once an allocation exists, or the recorder
  would sit unsubscribed for a whole cooldown at startup.
- `hysteresis_buffer: 0` disables hysteresis. The `enable_hysteresis` /
  `min_rank_change_threshold` / `fallback_on_error` keys from earlier drafts stay deleted: the first
  two were two knobs for one behaviour, and `fallback_on_error` described a silent recovery path the
  fail-fast contract forbids.

### 14.1 Hysteresis is displacement-based (F3)

```
incumbent keeps its slot        while rank <= budget + hysteresis_buffer
challenger displaces the worst  when  rank <= budget
```

An incumbent that has drifted into the buffer band is protected from *borderline* churn, but is
displaced by any challenger that has genuinely entered the top `budget`. The drafted code protected
incumbents unconditionally, so a rank-1 leg could be locked out entirely while a rank-`budget+buffer`
incumbent held a slot — the opposite of what hysteresis is for, and directly harmful when the budget
is 15 and rank 1 is the ATM leg.

### 14.2 One rank basis (F4)

`PriorityScore.rank` is **1-based** and is the only rank basis in the system. The drafted 0-based
positional index is deleted, not reconciled — two bases for one concept is how the off-by-one arose,
and 1-based is what logs, metrics, and tests read.

### 14.3 Cooldown scope (F5)

| Change | Gated by cooldown? |
|---|---|
| Baseline addition (`absent -> standard`) | **No** — applied immediately |
| Premium promotion / demotion / reassignment | **Yes** |
| First allocation of the session | No — always runs |

Baseline is monotone, cheap, and unbounded by the broker budget; premium is the scarce, churning
resource. Gating both (as drafted) leaves a newly-relevant strike **entirely unsubscribed** for up to
`churn_cooldown_seconds` — a hole in the very book being recorded, at exactly the moment it matters.

### 14.4 Diff semantics under BASELINE MONOTONICITY (F8)

- `removed` is **observability only**. It never produces a subscription action. A leg leaving the
  candidate window stays in `baseline`; it loses only its premium slot.
- `added_new` and `promoted_to_premium` are **disjoint by construction**. A new leg allocated straight
  to premium appears in `added_new` alone and is subscribed once at premium depth — never emitted as
  an add plus a promotion.
- The dead `- (old_all - new_all)` subtraction from the drafted `_compute_diff` is removed.

### 14.5 Rebalance trigger (F11)

A pass runs on **interval OR window/ATM change, whichever fires first**; the cooldown (§14.3) is the
real rate limiter on premium churn. Interval alone makes a trending spot wait; window-change alone
leaves a flat market never reconciling drift.

### 14.6 Default priority policy (F12)

`AtmDistancePolicy` is the default; a blended policy (gamma / volume / OI) is config-selectable but
**not** default. ATM distance needs only spot, which is always available at rebalance time; the
blended inputs are not reliably present when a pass fires, and a policy that silently degrades when
its inputs are missing is exactly the silent-default behaviour the fail-fast contract forbids.

---

## 15. Window Manager semantics

- Candidate universe per underlying = ATM zone (fine strike step) plus expansion zones (coarser
  step), both in points from spot, both from config.
- The window moves when spot moves; boundary expansion in the recorder today is the DSM and is
  FEED-owned. The framework's Window Manager computes the *candidate set*; it does not itself
  subscribe.
- Expiry selection is delegated to a registered `ExpiryCalendar` so the *rule* — not the index name —
  carries holiday and rollover semantics.
- Under BASELINE MONOTONICITY, a shrinking window does not shrink the baseline. The candidate set is
  the input to ranking; it is not the subscription set.

---

## 16. Broker capability + adapter contract

- FYERS capability config encodes: `symbols_per_connection: 5`, `max_connections: 3`,
  `max_channels: 50` (bookkeeping only, excluded from budget math), premium depth `50`, standard
  depth `5`, and per-exchange premium eligibility (NSE/NFO yes; BFO no).
- The adapter packs premium legs across connections; the engine never sees a connection.
- Channel ids are **strings**.
- The existing `Documents/patches/openalgo_fyers_tbt_channels.patch` is kept — it fixes the genuine
  `channel="1"` pin — but it buys 15, not 250, and the plan does not depend on it lifting any ceiling.

---

## 17. Configuration surface (draft)

```yaml
broker_capabilities:
  fyers:
    premium:   { depth: 50, symbols_per_connection: 5, max_connections: 3, max_channels: 50 }
    standard:  { depth: 5 }
    premium_exchanges: [NSE, NFO]

window_manager:
  # per-underlying zones resolved from underlyings[]; no index names here

priority_policy:
  policy: atm_distance          # atm_distance | blended   (F12 = atm_distance, §14.6)

budget_allocator:
  policy: weighted              # weighted | equal | proportional_to_candidates
  min_per_underlying: 2         # floor per PREMIUM-ELIGIBLE underlying only (F7 + F13, see 13.2)
  weights: { }                  # must cover every premium-eligible underlying
  redistribute_unspent: true    # F6; round-robin in weight order, capacity-driven (see 13.3)

depth_allocator:
  churn_cooldown_seconds: 30    # gates PREMIUM reshuffles only; baseline adds bypass it (F5)
  hysteresis_buffer: 2          # incumbent held while rank <= budget + 2; displaced inside top budget (F3)
  history_limit: 200

rebalance:
  trigger: both                 # interval | window_change | both   (F11 = both)
  interval_seconds: 5
```

Every key above is validated at startup; missing or out-of-range is exit 1. Startup validation
includes the F7 feasibility check in §13.2, computed over **premium-eligible** underlyings.

**No `premium_eligible` key exists in allocator config.** Eligibility is derived from the broker
capability layer (§13.1). Putting it in config would let a broker fact drift from the broker.

---

## 18. Testing architecture

- **No live broker, WebSocket, or market feed required for any business-logic test.** Clock, feed, and
  writers are injected, exactly as in Plan_001.
- Unit tests per component, with the §10.4 and §9 invariants asserted directly.
- **Property tests on the allocators:** for random budgets and candidate counts, assert
  `sum <= total_budget`, `premium_overlay` subset of `baseline`, and
  `len(premium_overlay) <= effective_budget`.
- **Transition-table coverage:** one test per row of the F2 table, including the forbidden row
  asserting that no unsubscribe is ever emitted during a normal session.
- **Churn tests:** a leg oscillating across the budget boundary must not flip tiers on alternate
  passes; a cooldown must hold.
- **Replay determinism:** the raw `.jsonl.gz` is the harness. The same `TickProcessor` plus the
  framework, driven by a simulated clock, must produce a byte-identical allocation sequence.
  `--verify` diffs a rebuild against a reference to catch non-determinism.
- **FD audit** after every phase touching files, sockets, threads, subprocesses, or DB handles.

---

## 19. Integration with the existing recorder

- Integration is **additive and flag-gated**. The existing subscribe-everything-at-`:50` path stays
  runnable until the hybrid is validated live.
- One call site on PROCESSOR (the orchestrator, §10.8) and one execution site on FEED.
- Plan_001 behaviour for P0-P10 is unchanged with the flag off; the test suite must stay green at its
  current count throughout.
- The end-of-session reprocess stays a subprocess with stdout/stderr to a **log file, never a PIPE**,
  and is `wait()`-reaped.

---

## 20. Fork decisions — CLOSED (2026-08-25)

All forks are decided. F1 and F2 were decided earlier and are recorded in §6. F3-F14 were decided by
the user on 2026-08-25; the options considered are preserved so the reasoning stays auditable.

| Fork | Decision | Where it is specified |
|---|---|---|
| F3 — hysteresis displacement | **(b)** challenger inside top `budget` displaces the worst incumbent | §14.1 |
| F4 — rank basis | **(a)** 1-based `PriorityScore.rank` only | §14.2 |
| F5 — cooldown scope | **(a)** premium reshuffles only; baseline adds immediate | §14.3 |
| F6 — unspent budget | **(b)** deterministic redistribution in weight order | §13.3 |
| F7 — infeasible floors | **(a)** startup validation, exit 1; no runtime raise | §13.2 |
| F8 — diff semantics | **(a)** `removed` is observability only; sets disjoint | §14.4 |
| F9 — depth-transition mechanism | **PROBE FIRST** — measured in phase F7, not assumed | §20.1 |
| F10 — state key | **(a)** leg identity (`Instrument`); depth is a value | §9 |
| F11 — rebalance trigger | **(c)** interval OR window/ATM change | §14.5 |
| F12 — default policy | **(a)** `AtmDistancePolicy`; blended optional | §14.6 |
| F13 — premium eligibility | **(a)** broker/exchange capability; ineligible = 0 premium, full baseline | §13.1 |
| F14 — PROCESSOR -> FEED hand-off | **(a) PROVISIONAL** — validated during phase F8 | §20.2 |

Two clarifications were issued with the decision set and are binding:

1. **`min_per_underlying` applies only to premium-capable underlyings.** Without this, F7's startup
   check and F13's "ineligible gets 0" contradict each other outright — the check would demand a floor
   for an underlying F13 says must receive nothing. Specified in §13.2.
2. **F14's latest-wins mailbox is an implementation direction, not permission to add a thread or a
   second broker-I/O owner.** F1 remains absolute.

Rationale for the accepted recommendations is in the sections named above; each one states the failure
the rejected options produce, not merely the choice.

### 20.1 F9 — depth-transition probe specification (phase F7)

**Do not write the generic Broker Adapter around an unverified assumption.** The recorder has never
sent an unsubscribe; `websocket_client.py` has no unsubscribe path at all. Whether a re-subscribe
changes depth, and what it costs, is unmeasured. This is the same class of assumption that produced
the 250-symbol error, and it is not to be guessed twice.

The spike must exercise all four transitions:

```
5  -> 50      (promotion)
50 -> 5       (demotion)
50 -> 50      (idempotent re-subscribe at premium)
5  -> 5       (idempotent re-subscribe at standard)
```

and must answer, with evidence, every one of:

- [ ] Does a bare re-subscribe change the delivered depth, or is the first subscription sticky?
- [ ] Does a depth change require an explicit unsubscribe first?
- [ ] Does unsubscribe exist and work through the current OpenAlgo/FYERS path at all?
- [ ] Is there a transient loss of subscription across a transition, and for how long?
- [ ] Does a transition consume an **additional** premium slot (even momentarily)?
- [ ] What happens when a transition is attempted while already at the 15-symbol ceiling?
- [ ] What is the reconnect behaviour afterwards — does the broker restore the pre- or post-transition
      depth?

**Deliverable:** a dated evidence document under `Documents/patches/`, held to the same standard as
`tbt_concurrency_reconciliation_20260714.md` — raw artifacts preserved unedited, conclusions traceable
to them. The Broker Adapter contract is written **after** that document exists, not before.

Until F7 completes, the Subscription Manager emits a **transition intent** (`upgrade` / `downgrade`)
and the adapter is free to realise it either way. No framework code above the adapter may assume a
mechanism.

### 20.2 F14 — provisional decision, validated in phase F8

**Working decision: a single-slot latest-wins mailbox** that FEED polls in its existing loop.

Reasoning: a subscription plan is *desired state*, so a superseded plan has no value. A queue would
buffer stale work and could deliver an obsolete plan after a burst; latest-wins cannot grow unbounded
and always reflects the newest computation. A queue is not warranted merely because the existing
architecture uses queues elsewhere — those carry *data*, which must not be lost; this carries *intent*,
which is meant to be replaced.

**Marked provisional because it depends on integration mechanics not yet examined.** Phase F8 must
confirm, against the real FEED loop, that the mailbox:

- [ ] can be read at a point in the FEED loop that does not delay the packet tee;
- [ ] does not require FEED to hold `_spot_lock` or `_sub_lock` while reading it;
- [ ] introduces no lock that could participate in or invert the `spot_lock -> RLock` order;
- [ ] adds no file descriptor and no thread;
- [ ] has defined behaviour when FEED is mid-reconnect and a plan is superseded before it is read.

If any of these fails, the alternative is re-opened **in phase F8 only** — not the F1 four-thread
decision, which is absolute regardless of how the hand-off is carried.

---

## 21. Discrepancies found in the source documents

Recorded so they are not silently re-inherited.

- **D-1 — The Budget Allocator worked example is arithmetically wrong, three different ways.**
  Qwen §5.1.4: with `effective_budget = 15`, `min_per_underlying = 2`, weights 2:1, floors take 4 and
  "the remaining 11 splits 7/4" — which gives **NIFTY 9, SENSEX 6 = 15**. The same sentence then
  concludes "**NIFTY 9, SENSEX 5** — 14 of 15". Qwen §0.2 states a third answer, "15 -> **NIFTY 10,
  SENSEX 5**". Tracing the drafted code gives 9/6. The example must be recomputed, and it also
  demonstrates the F13 waste. Superseded by §13.3 and the §13.4 worked examples.
- **D-2 — Qwen §0.1 mandates a SUBSCRIPTION thread.** Superseded by F1.
- **D-3 — Qwen §6.7 has `SubscriptionManager` own a non-daemon thread, a `_state_lock`, and a bounded
  plan queue; §6.3 `reconcile()` emits unsubscribes for `removed` and unsubscribe-then-subscribe for
  demotions.** All superseded by F1 and F2.
- **D-4 — `_compute_diff` contains a dead subtraction and a double-count.**
  `promoted_to_premium = new_premium - old_premium - (old_all - new_all)`: the third term is `removed`,
  which is disjoint from `new_all` (a superset of `new_premium`), so subtracting it is a no-op.
  Meanwhile a new instrument allocated straight to premium lands in both `added_new` and
  `promoted_to_premium`. Closed by F8 (§14.4).
- **D-5 — Rank basis mismatch.** 1-based `rank` field vs 0-based selection index. Closed by F4 (§14.2).
- **D-6 — `min_per_underlying` infeasibility raises at runtime**, not at startup, contradicting the
  fast-fail contract. Closed by F7 (§13.2), which also makes the runtime raise unreachable.
- **D-7 — The DB WRITER writes Tier-1 SQLite/WAL, not DuckDB.** DuckDB is the Tier-2 offline store.
  Noted for accuracy; it does not affect the F1 ownership decision.
- **D-8 — Qwen §6.11 case 5 asserts "a bare re-subscribe at a new tier is not assumed to be idempotent
  at the broker."** That is an assumption, not a finding, and it is unverified. Resolved by measurement
  in phase F7 (§20.1), not by adopting the assumption.
- **D-9 — The recorder's subscription key encodes depth.** `_subscriptions` is keyed by wire symbol and
  `wire_symbol()` appends `:50` for premium, so a 50 -> 5 transition changes the key and "the same leg
  at a different depth" is inexpressible. Closed by F10: framework state is keyed by leg identity with
  depth as a value.
- **D-10 — The drafted `min_per_underlying` would starve the premium budget.** Applied over all
  configured underlyings it reserves a floor for underlyings that cannot use premium depth at all,
  which both wastes the scarcest resource and makes F7's feasibility check contradict F13. Closed by
  the §13.2 clarification: the floor is scoped to premium-eligible underlyings.

---

## 22. Proposed phase sequence

Phases are `F<n>` to avoid collision with Plan_001's `P<n>`. §20 is closed, so the remaining gate is
per-phase scope approval. **Each phase begins only when its scope is explicitly approved**, and its
exhaustive `- [ ]` checklist is embedded here immediately before implementation, per the live-doc
convention.

| Phase | Deliverable | Implements | Gate |
|---|---|---|---|
| **F0** | This plan; all forks decided and recorded with rationale | F1, F2, F3-F14 | **Awaiting approval** |
| **F1** | `market_depth_framework/` skeleton, data models (`Instrument`, `DepthType`, capability dataclasses), config schema + startup validation. No behaviour change, flag off. | F10 key model | Tests green at current count + new unit tests |
| **F2** | Broker Capabilities layer; FYERS capability config; `effective_budget`; per-exchange premium eligibility | F13, §13.2 startup check | Unit tests incl. `UNLIMITED_BUDGET` and an ineligible-exchange case |
| **F3** | Window Manager + `SymbolCodec` / `ExpiryCalendar` seams | §15 | Unit tests; no index literals in engine code |
| **F4** | Priority Policy + `rank_scores`; `AtmDistancePolicy` | F12, F4 rank basis | Total-order and stability tests |
| **F5** | Budget Allocator + Depth Allocator | F3, F5, F6, F7, F8 | Property tests on all invariants; both §13.4 worked examples as fixtures |
| **F6** | `SubscriptionState` + synchronous `SubscriptionManager` | F2, F10 | One test per transition-table row, incl. the forbidden row |
| **F7** | **Live depth-transition probe** (§20.1), *then* the Broker Adapter contract | F9 | Evidence document in `Documents/patches/`, same standard as the TBT reconciliation |
| **F8** | Recorder integration: orchestrator on PROCESSOR, execution on FEED. Flag-gated; old path retained. | F11, F14 confirmation (§20.2) | Full suite green; FD audit; §20.2 checklist satisfied |
| **F9** | Replay/determinism harness for the framework; hybrid soak | §18 | `--verify` byte-identical |
| **F10** | Live validation at true scale; re-measure `cycle_ms` and RSS at up to 15 legs @50 plus remainder | — | **Closes Plan_001 D18** |

Ordering constraint: **F7 must complete before the Broker Adapter is written**, and the adapter must
be written before F8 integration. No phase above F7 may assume a depth-transition mechanism.

Documentation is updated as part of each phase's Completion Audit — `Documents/ARCHITECTURE.md`,
`Documents/CHANGELOG.md`, and a per-module `Documents/<module>.md` — and a phase is not done until its
docs are current.

### 22.1 F0 approval gate

F0 is complete when every box below is ticked. **F1 does not begin until then.**

- [x] Both architecture decisions (F1, F2) recorded as binding, with the transition table (§6)
- [x] All twelve remaining forks decided and recorded with rationale (§20)
- [x] `min_per_underlying` scoped to premium-eligible underlyings, resolving the F7/F13 conflict (§13.2)
- [x] F6 redistribution specified as a deterministic, capacity-and-weight-driven rule, with worked
      examples that spend the full budget (§13.3, §13.4)
- [x] F9 kept as a measurement, with an explicit probe specification and deliverable (§20.1)
- [x] F14 recorded as provisional with the conditions that validate it in F8 (§20.2)
- [x] Source-document discrepancies recorded so they are not re-inherited (§21)
- [x] Phase sequence F0-F10 with per-phase gates and the F7-before-adapter ordering constraint (§22)
- [ ] **User approves F1 scope** — the only remaining item

---

## 23. Progress tracking

- [x] F0 — plan drafted; F1 and F2 recorded as decided (2026-08-25)
- [x] F0 — §20 forks F3-F14 decided and recorded, with both clarifications applied (2026-08-25)
- [ ] F0 — user approves F1 scope (§22.1)
- [ ] F1 — skeleton, data models, config schema + startup validation
- [ ] F2 — Broker Capabilities layer
- [ ] F3 — Window Manager
- [ ] F4 — Priority Policy
- [ ] F5 — Budget Allocator + Depth Allocator
- [ ] F6 — SubscriptionState + SubscriptionManager
- [ ] F7 — live depth-transition probe, then Broker Adapter
- [ ] F8 — recorder integration (confirms F14)
- [ ] F9 — replay/determinism harness + hybrid soak
- [ ] F10 — true-scale live validation; closes Plan_001 D18

Per-phase exhaustive checklists are embedded in §22 immediately before each phase is implemented.
