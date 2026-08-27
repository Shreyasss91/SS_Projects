# market_depth_framework — module reference

Generic market-depth allocation framework. Broker-agnostic layer that will decide **which** option legs
are subscribed and **at what depth tier**, so the recorder can run the hybrid (near-ATM legs at premium
depth within the broker's budget, the rest at standard depth) with no index name, exchange code, or
broker fact in engine code.

Planned in `plans/Plan_002_market_depth_framework_implementation.md`. This document describes the
**implemented** state only.

## Implemented state: phases F1-F8 (plus F7.6)

F1 delivered the package skeleton, the data models, the broker-capability dataclasses, and the
configuration schema with its fail-fast validation. F2 delivered the **Broker Capabilities layer** —
one logical `effective_budget` and per-exchange premium eligibility. F3 delivered the **Window
Manager** — which option legs are eligible candidates, and nothing about their order, depth, or
subscription. F4 delivered the **Priority Policy** — in what order those candidates matter, and nothing
about budget, depth, or subscription. F5 added the two **allocators** — the Budget Allocator, which
splits one logical premium budget across underlyings, and the Depth Allocator, which picks the premium
overlay within one underlying. F6 adds the **Subscription layer** — `SubscriptionState`, which holds the
desired coverage plus snapshot-derived `pending` / `failed` observability, and `SubscriptionManager`,
whose pure `reconcile(desired, current)` turns a desired and a live leg -> depth map into a
`SubscriptionPlan`. It says *what should be subscribed and how the desired state converges on the live
one*, and nothing about actual broker execution or what a depth transition costs on the wire.
Snapshot-derived means F6 makes **no** broker assumption: the live `current` snapshot is the
acknowledgement boundary (Plan_002 §20.4, Option A). **F7.5 adds the Broker Adapter** — the one module
in the package that knows a wire format exists. It renders each leg's wire identity per tier, executes a
plan by releasing before claiming, packs the scarce premium tier across broker connections, and supplies
the live snapshot F6 consumes — derived from delivered packets alone. It was written **from** the F7B
live evidence, after it, rather than ahead of it. **F8 adds the `FrameworkOrchestrator`** — one pass that runs every decision layer in order
and hands a `SubscriptionPlan` out — and wires the package into the live recorder through
`framework_bridge.py` (see `Documents/framework_bridge.md`), behind the `market_depth_framework.enabled`
flag.

| Layer | Phase | State |
|---|---|---|
| Data models (`Instrument`, `DepthType`) | F1 | Built |
| Broker-capability dataclasses | F1 | Built (shapes only) |
| Config schema + startup validation | F1 | Built |
| Broker Capabilities layer (`effective_budget`, eligibility) | F2 | Built |
| §13.2 `min_per_underlying` feasibility check | F2 | Built (not yet called from a live path — F8 wires it) |
| Window Manager (ATM-relative candidate eligibility) | F3 | Built |
| Priority Policy (`AtmDistancePolicy`, `rank_scores`) | F4 | Built |
| Budget Allocator (inter-underlying premium split) | F5 | Built |
| Depth Allocator (premium overlay within one underlying) | F5 | Built |
| Subscription state (`SubscriptionState`, snapshot-derived observability) | F6 | Built |
| Subscription Manager (`reconcile`, pure desired/current -> plan) | F6 | Built |
| Broker Adapter (`BrokerAdapter`, wire rendering + dispatch + delivery-derived snapshot) | F7.5 | **Built.** F7A prepared and **F7B measured 2026-08-26** — the contract is now derived from live evidence in `Documents/patches/depth_transition_probe_20260826.md` §19: promotion subscribes `SYMBOL:50`, demotion unsubscribes it, and no in-place depth edit exists. Implemented in F7.5 as its own approved phase — F7 itself is complete as the evidence phase; Plan_002 §20.1, §22.8, §22.9 |
| Orchestrator (`FrameworkOrchestrator`, one pass, `due()` triggers) | F8 | **Built** |
| Recorder integration (`framework_bridge.py`, FEED-side execution) | F8 | **Built**, behind `enabled` (default `false`); forks F15/F16 |

**The framework still imports nothing from the recorder** (AST-asserted), and importing it pulls in no
recorder module. Since F8 the recorder imports **it**, through exactly one seam
(`framework_bridge.py`), and only acts on it when `market_depth_framework.enabled` is `true`. With the
default `false` the recorder's existing subscribe-everything-at-`:50` DSM path is unchanged and remains
the active path.

## Package layout

```
market_depth_framework/
├── __init__.py        # public surface; no side effects at import
├── __main__.py        # --validate-config entrypoint; exit 0 valid / 1 invalid / 2 usage
├── models.py          # Instrument, DepthType
├── capabilities.py    # UNLIMITED_BUDGET, PremiumTier, StandardTier, BrokerCapability  [F1]
├── capability_layer.py # BrokerCapabilityLayer: effective_budget, eligibility  [F2]
├── window_manager.py   # WindowManager + SymbolCodec/ExpiryCalendar seams  [F3]
├── priority_policy.py  # AtmDistancePolicy, rank_scores, MarketContext  [F4]
├── budget_allocator.py # BudgetAllocator: premium budget split across underlyings  [F5]
├── depth_allocator.py  # DepthAllocator: premium overlay, hysteresis, cooldown  [F5]
├── subscription_state.py   # SubscriptionState + SubscriptionPlan/Action/ActionKind  [F6]
├── subscription_manager.py # SubscriptionManager.reconcile: pure desired/current -> plan  [F6]
├── broker_adapter.py   # BrokerAdapter: wire rendering, release-before-claim, live snapshot  [F7.5, F7.6]
├── orchestrator.py     # FrameworkOrchestrator: one pass across every layer + due() triggers  [F8]
├── config.py          # FRAMEWORK_SECTION, FrameworkConfig, FrameworkConfigError, validators
└── config.example.yaml # reference §17 block with the FYERS capability filled in  [F2]
```

## Public API

```python
from market_depth_recorder.market_depth_framework import (
    DepthType, Instrument,                                  # models
    UNLIMITED_BUDGET, BrokerCapability, PremiumTier, StandardTier,   # capabilities
    FRAMEWORK_SECTION, FrameworkConfig, FrameworkConfigError,
    load_framework_config, validate_framework_config,        # config
    BrokerCapabilityLayer, build_capability_layers,          # capability layer (F2)
    capability_layer_for, eligible_underlyings, check_premium_floor_feasible,
    WindowManager, WindowSpec, WindowResult, WindowStatus,   # window manager (F3)
    OptionSide, SymbolCodec, TagSymbolCodec,
    ExpiryCalendar, FixedExpiryCalendar, window_specs_from_underlyings,
    DEFAULT_POLICY, PriorityPolicy, AtmDistancePolicy,          # priority policy (F4)
    MarketContext, PriorityScore, rank_scores, policy_for,
    market_context_from_window, rank_candidates,
    BUDGET_POLICIES, DEFAULT_BUDGET_POLICY,                  # budget allocator (F5)
    BudgetAllocator, budget_allocator_for,
    DepthAllocator, DepthAllocation, DepthAllocationDiff,    # depth allocator (F5)
    depth_allocator_for, depth_allocators_for,
    SubscriptionState, SubscriptionManager,                 # subscription layer (F6)
    SubscriptionPlan, SubscriptionAction, ActionKind,
    BrokerAdapter, DepthTransport, DispatchResult,          # broker adapter (F7.5)
    LegState, LegView, TransportError, UNASSIGNED,
    WireDialect, WireOp, WireRequest, instruments_of,
)
```

- `validate_framework_config(root) -> FrameworkConfig | None` — validate the framework block inside an
  already-parsed config mapping. Returns `None` when the section is absent (framework off). Raises
  `FrameworkConfigError` carrying the complete error list.
- `load_framework_config(path) -> FrameworkConfig | None` — same, reading a YAML file first.
- `capability_layer_for(config, broker) -> BrokerCapabilityLayer` — resolve one broker's layer.
  Raises `FrameworkConfigError` when that broker has no capability configured.
- `build_capability_layers(config) -> Mapping[str, BrokerCapabilityLayer]` — wrap all of them.
- `eligible_underlyings(layer, underlying_exchanges) -> tuple[str, ...]`
- `check_premium_floor_feasible(layer, underlying_exchanges, min_per_underlying) -> tuple[str, ...]`
- `WindowManager(specs, codecs, calendars)` — construct from `WindowSpec`s plus the codec and expiry
  rules they name. Collects every construction problem in one pass and raises `FrameworkConfigError`.
- `WindowManager.candidates(underlying, spot, universe) -> WindowResult` — the eligible legs for one
  underlying at one spot.
- `WindowManager.candidates_for_all(spots, universe) -> tuple[WindowResult, ...]` — one result per
  configured underlying, in configured order; materialises the universe once so a generator survives.
- `window_specs_from_underlyings(underlyings, *, codec_rule, expiry_rule) -> tuple[WindowSpec, ...]` —
  build specs from recorder-shaped `underlyings[]` mappings. The rule names are keyword-only and
  required, so no seam is ever silently defaulted.
- `policy_for(name=None) -> PriorityPolicy` — resolve the configured policy. `None` means the
  documented default `atm_distance`. Any other name, including `blended`, raises
  `FrameworkConfigError` rather than degrading to the default.
- `AtmDistancePolicy().compute_priorities(candidates, ctx) -> tuple[PriorityScore, ...]` — the
  ranking for one underlying, rank 1 first.
- `rank_scores(scored) -> tuple[PriorityScore, ...]` — the single ordering site: turns
  `(Instrument, score)` pairs into 1-based ranked scores under the total order **score descending,
  then symbol ascending**.
- `market_context_from_window(result) -> MarketContext` — the F3 → F4 adapter. Raises on any
  non-`RESOLVED` `WindowResult`.
- `rank_candidates(policy, results) -> Mapping[str, tuple[PriorityScore, ...]]` — rank several
  underlyings, each independently from rank 1.
- `BudgetAllocator(min_per_underlying=0, weights={}, redistribute_unspent=True)` — the inter-underlying
  split. Holds no state between calls.
- `BudgetAllocator.allocate_budget(total_budget, candidate_counts) -> Dict[str, int]` — how many premium
  slots each underlying gets. Every configured underlying is answered; `0` is a valid answer and a
  missing key is not.
- `budget_allocator_for(config) -> BudgetAllocator` — build from a validated `budget_allocator` block.
  Raises `FrameworkConfigError` for the unimplemented `equal` / `proportional_to_candidates` policies
  rather than substituting `weighted`.
- `DepthAllocator(underlying, *, clock, hysteresis_buffer=0, churn_cooldown_seconds=0.0,
  history_limit=200)` — **one instance per underlying**. The clock is keyword-only and has no default.
- `DepthAllocator.allocate(ranked, budget) -> DepthAllocation` — the premium overlay for one pass.
  `budget` is passed per call and never stored.
- `depth_allocator_for(config, underlying, *, clock) -> DepthAllocator` and
  `depth_allocators_for(config, underlyings, *, clock) -> dict[str, DepthAllocator]` — build one, or one
  per underlying, from a validated `depth_allocator` block.
- `SubscriptionState(effective_budget, *, clock)` — the PROCESSOR-owned desired coverage plus
  snapshot-derived observability. `effective_budget` is a plain int (a broker capability, never
  reconstructed); the clock is keyword-only with no default. Mutators: `set_desired(desired)`,
  `record_dispatch(plan)`, `apply_live(current)`, `record_failed(legs)`, `reset()`. Read views
  (`baseline`, `premium_overlay`, `standard`, `pending`, `failed`, `last_updated`) return immutable
  frozensets; `desired() -> dict[Instrument, DepthType]` rebuilds the desired leg -> depth map.
- `SubscriptionManager()` — stateless, holds no subscription state, thread, or broker connection.
- `SubscriptionManager.reconcile(desired, current) -> SubscriptionPlan` — the pure reconciliation over
  two leg -> depth maps. Deterministic, mutates neither argument, performs no I/O, and never inspects
  `pending` / `failed`.
- `SubscriptionPlan(added_new, promoted_to_premium, demoted_to_standard, removed)` — the frozen result.
  `ordered_actions()` releases capacity before claiming it (demotions, then additions, then promotions);
  `actioned_instruments` is every group except `removed`; `is_empty` is the settled steady state.
- `SubscriptionAction(instrument, kind, depth)` and `ActionKind` (`SUBSCRIBE` / `UPGRADE` / `DOWNGRADE`)
  — one leg's transition intent and target depth, for the Broker Adapter to execute on the FEED thread.
- `BrokerAdapter(capability_layer, transport, *, clock, dialect=None, request_id_prefix="mdf")` — the
  wire executor. The transport is any object with `send(frame)`; the clock is keyword-only with no
  default. It creates no thread, no socket, and no FD.
- `BrokerAdapter.wire_symbol(instrument, tier) -> str` and `.tier_for_wire_symbol(wire) -> DepthType` —
  the rendering and its inverse. `SYMBOL` for standard, `SYMBOL:<premium_depth>` for premium.
- `BrokerAdapter.apply(plan) -> DispatchResult` — execute a `SubscriptionPlan`, in plan order, releasing
  before claiming. Reports `sent` / `failed` / `refused` / `skipped`; raises nothing on a leg failure.
- `BrokerAdapter.observe(message)` — feed it every inbound frame. Packets confirm delivery;
  acknowledgements only record acceptance or rejection. Unrecognised frames are ignored.
- `BrokerAdapter.live_snapshot() -> dict[Instrument, DepthType]` — the `current` map
  `SubscriptionManager.reconcile()` and `SubscriptionState.apply_live()` consume. Derived from
  **delivered packets**, never from acknowledgements.
- `BrokerAdapter.take_rejections() -> tuple[Instrument, ...]` — drain the legs the broker explicitly
  rejected, for `SubscriptionState.record_failed()`.
- `BrokerAdapter.handle_reconnect(desired) -> DispatchResult` — discard all bookkeeping, reissue the
  desired coverage, and confirm nothing until packets arrive again.
- `BrokerAdapter.legs()` / `.leg_for(instrument, tier)` / `.premium_leg_count()` / `.close()` —
  observability and teardown. `close()` releases the adapter's own bookkeeping only; the transport
  belongs to the caller.
- `DepthTransport` — the runtime-checkable `send(frame)` protocol the caller satisfies (in F8, the
  recorder's FEED-owned WebSocket client). `TransportError` is the failure the adapter expects.
- `WireDialect` — every frame key, the premium suffix template, and the accepted status vocabulary, in
  one frozen value object, so a second broker's wire format is a configuration rather than a fork.
- `WireRequest`, `WireOp`, `LegState`, `LegView`, `DispatchResult`, `UNASSIGNED`, `instruments_of` — the
  frozen value objects the adapter reports through.

## `models.py` — leg identity and depth tier (Plan_002 §9, fork F10)

`Instrument` is a frozen, hashable dataclass with six identity fields — `underlying`, `exchange`,
`symbol`, `expiry`, `strike`, `option_type` — and **no depth field**. `DepthType` is a two-member enum
(`STANDARD` / `PREMIUM`) naming the tier, not the level count.

This is the F10 decision, and it exists to fix a concrete defect (Plan_002 §21 D-9): the recorder's
`_subscriptions` map is keyed by *wire symbol*, and `wire_symbol()` appends `:50` for premium depth. A
depth transition therefore changes the key, so "the same leg at a different depth" is inexpressible and
one leg looks like two. Keying by `Instrument` with depth as a value makes the transition expressible at
all. The wire symbol and its suffix become a rendering detail owned by the Broker Adapter (F7).

The numeric depth (5, 20, 50, ...) stays on the capability rather than the tier because it is a broker
fact that varies by exchange — FYERS serves 50-level TBT on NSE/NFO but only 5-level on BFO. A broker
whose premium tier is 20 reuses `DepthType` unchanged.

`__post_init__` rejects empty or non-string identity fields and a non-numeric or non-finite strike, so no
partially-valid leg enters framework state.

## `capabilities.py` — broker-declared facts (Plan_002 §10.1, §16)

`PremiumTier` carries `depth`, `symbols_per_connection`, `max_connections`, and `max_channels`;
`StandardTier` carries `depth`; `BrokerCapability` groups both plus `premium_exchanges` and
`total_symbol_budget`. All frozen, all validating their fields at construction.

`UNLIMITED_BUDGET` is an **`int`** sentinel (`2**31 - 1`), never `float('inf')`, so every downstream
`-> int` contract stays honest and `min()` against it yields an int rather than promoting the
calculation to float. A fixed literal rather than `sys.maxsize`, so the value is identical on every
platform and replay stays deterministic. It is the meaning of an omitted `total_symbol_budget`: "this
broker imposes no account-wide cap beyond its connection math."

**`max_channels` is bookkeeping only and must never be multiplied into a budget.** The FROZEN FYERS
finding is 5 symbols per *connection* × 3 connections = **15**, not 5 per *channel* × 50 channels = 250;
channels are a pause/resume grouping carrying no capacity. Multiplying channels in is precisely the
error that produced a ceiling roughly 16× too large. Evidence:
`Documents/patches/tbt_concurrency_reconciliation_20260714.md`.

**The dataclasses deliberately expose no `effective_budget()` and no `supports_premium()`.** Those
belong to the *layer* below, and keeping data and behaviour in separate modules is what let F2 land
without touching a single F1 test. The F1 guard asserting their absence on `BrokerCapability` is still
green, unmodified, and now reads as a data/behaviour separation guard.

## `capability_layer.py` — the Broker Capabilities layer (Plan_002 §10.1, §13.1, §13.2, §16)

`BrokerCapabilityLayer` wraps one `BrokerCapability` and turns declared facts into the single logical
answers the rest of the framework consumes. It holds no mutable state (`__slots__`, no setters, frozen
capability), performs no I/O, and is safe to call from any thread including the PROCESSOR loop.

**The budget.** `effective_budget = min(total_symbol_budget, max_connections * symbols_per_connection)`,
computed once at construction from frozen inputs so it cannot drift mid-session. For the shipped FYERS
configuration that is `min(UNLIMITED, 3 x 5) = 15`.

**The number 15 appears nowhere in framework code.** It is derived from configuration, so a broker
exposing `1 x 20` or full-chain 50 changes only its capability block. Two tests enforce this on the
*source* rather than the result: one AST scan rejects any multiplication mentioning `max_channels`
anywhere in the package, another rejects a literal `15` assignment.

**Per-exchange eligibility (fork F13).** `supports_premium(exchange)` is exact, case-sensitive
membership in `premium_exchanges` — case-folding would be a silent normalization, and everywhere else
the framework fails loudly instead. A malformed exchange raises rather than answering `False`, because
a plausible-looking `False` would hide a caller bug. An ineligible exchange gets
`premium_capacity() == 0` (hence zero premium budget and no floor) while its standard-depth baseline is
untouched — eligibility governs the overlay only.

`depth_for(exchange, tier)` reports what the broker will *actually* serve: a `PREMIUM` request on an
ineligible exchange resolves to the standard depth, which is what makes a self-describing
`depth_levels` and `NULL` deep-book metrics correct rather than optimistic.

**What the layer does not know:** underlyings, strikes, ranking, priority scores, windows, subscription
state, allocation policy. Tests assert this over its public method names and over its annotations (no
parameter is typed `Instrument`) — eligibility is per-exchange, so two legs on the same exchange must
get identical answers regardless of strike or expiry.

**§13.2 startup feasibility.** `eligible_underlyings()` and `check_premium_floor_feasible()` are
module-level functions, not methods: they receive the underlying-to-exchange mapping as an argument, so
the layer stays ignorant of underlyings while the check still gets what it needs. The floor is scoped
to eligible underlyings only — read over all configured underlyings it would demand a floor for an
underlying on an exchange with no deep book, contradicting §13.1. Satisfying it at startup is what makes
the mid-session failure unreachable, which is why the Budget Allocator will have no raising path that
could kill the PROCESSOR thread. **Not yet called from a live startup path**: the underlyings mapping
comes from the recorder's config, and that wiring is F8.

## `window_manager.py` — candidate eligibility (Plan_002 §10.2, §15, §17)

`WindowManager` answers one question: **which option legs are eligible candidates** for an underlying at a
given spot. It does not rank them (F4), does not allocate budget or depth (F5), and does not decide what is
subscribed (F6). It is a pure synchronous function of `(spot, universe, configured window)` — no mutable
state, no I/O, nothing remembered between calls, safe to call from any thread.

**One window, one density (F3 Decision 1, Plan_002 §15).** Eligibility is a **single symmetric
points-from-spot window** resolved from `underlyings[]`. There is no ATM/expansion density split, no
fine-versus-coarse strike step, and no decimation — the strike step describes the instrument
universe/grid, not a second window density.

**The semantics are the recorder's, not new ones.** A window is symmetric **points from spot**:

```
lower = spot - window_points
upper = spot + window_points
candidate  <=>  lower <= strike <= upper
```

Membership is **inclusive at both bounds** and compared **exactly, with no epsilon**. That is
`websocket_client.py`'s DSM seeding rule (`st.b_lower <= k <= st.b_upper`) reproduced, not a parallel
definition. The `_in_window` helper in `metrics/aggregate.py` does use an EPS — it measures a different
thing (an aggregate radius) and is deliberately not reused here.

**ATM is the nearest strike to spot; on an exact tie the LOWER strike wins (F3 Decision 2,
Plan_002 §15).** This is a decided deterministic rule, not an artifact: it must not depend on list
order, dictionary order, or input ordering. Implemented by sorting distinct strikes ascending and
keeping only a strict improvement, with a direct regression test and a shuffled-input variant. It is
also the answer `processor._resolve_atm` gives — its `min(strikes, key=lambda k: abs(k - spot))` over
an ascending `active_strikes_list` returns the first minimum — so framework and recorder agree, with
what was incidental list order in the recorder made explicit here. The ATM is reported even when the window admits no legs at all, because it is a
property of the universe rather than of the window.

**The candidate set is not the subscription set (§15).** Boundary expansion, hysteresis, and the
never-shrink subscription rule remain FEED-owned in the recorder and, inside the framework, belong to F6.
Every call recomputes from scratch; no window state survives a pass. A test asserts that calling with a
shifted spot and then the original spot returns the original result exactly.

**Candidate order is identity order, explicitly not priority order.** Results are sorted by
`(strike, option_type, symbol)` so replay and tests are stable. A test asserts this is *not* a
distance-from-ATM ordering, so nothing downstream can mistake it for a ranking F4 has not computed yet.

**Identity is supplied, never constructed.** The universe arrives as `Instrument` values from the
instrument master; the framework parses no symbol and builds none. Two seams carry the meaning, registered
**per rule name, not per index name** (§10.2):

- `SymbolCodec.option_side(option_type) -> OptionSide` — implemented by
  `TagSymbolCodec(call_tags, put_tags)`. It rejects a blank tag, a tag registered on both sides, and an
  empty side; an unrecognised tag **raises** on the pass that saw it rather than being guessed at. A new
  exchange vocabulary needs a new registration, never an `if`.
- `ExpiryCalendar.active_expiry(underlying) -> str | None` — implemented by `FixedExpiryCalendar`. Legs on
  any other expiry are not candidates.

**Degenerate inputs get a named status, not an exception.** `WindowResult.status` is one of:

| Status | Meaning |
|---|---|
| `RESOLVED` | Window computed; `candidates` may still be empty if nothing falls inside |
| `NO_SPOT` | Spot missing, zero, negative, NaN, infinite — or a `bool`, which is not a price |
| `NO_EXPIRY` | The calendar has no active expiry for this underlying |
| `NO_UNIVERSE` | No leg in the supplied universe belongs to this underlying |

A **caller-side bug still raises**: an unknown underlying, or a leg claiming this underlying on an exchange
that contradicts the configured one.

**What the Window Manager does not know:** `tbt_budget`, `effective_budget`, premium slots, connection
counts, `max_channels`, ranking scores, hysteresis, cooldown, subscription state, broker adapters. Enforced
on the *source* by AST scans in the F1/F2 style: no capability-layer or recorder import; no budget, ranking,
or allocation token; no call-tag / put-tag / index / exchange literal in executable code; no `open` /
`connect` / `Thread` / `Popen` / `Queue` / `socket` call; no `time` / `random` / `socket` / `os` /
`threading` / `queue` / `asyncio` import; no ranking or allocation method on the class.

**No second config system (F3 Decision 3).** The framework's `window_manager` section stays deliberately
**keyless**: one source of truth for these window facts, no duplicate framework window settings.
`window_specs_from_underlyings()` reads the zones from the recorder's existing `underlyings[]`, consuming
only `name`, `option_exchange`, and `initial_window` (plus optional per-entry `codec_rule` / `expiry_rule`
overrides) and ignoring every other recorder key. It takes plain mappings, so the one-way dependency holds:
the framework still imports nothing from the recorder. Duplicating the zones into a second place is exactly
how a config and its source drift apart.

## `priority_policy.py` — candidate ranking (Plan_002 §10.3, §14.2, §14.6)

F4 answers exactly one question: **among the candidates for one underlying, in what order do they
matter.** It does not decide how many may be premium (Budget Allocator, F5), which ones get the premium
overlay (Depth Allocator, F5), or what is actually subscribed (Subscription Manager, F6). Keeping those
apart is what lets each be tested and replaced on its own; the ranking is an **input to F5**.

**The default policy is `atm_distance` (§14.6, fork F12).** `AtmDistancePolicy` scores each candidate
`-abs(strike - ctx.atm_strike)`, so the ATM leg scores exactly `0.0` and nearer outranks further. Its
only inputs are spot and ATM, both reliably present at every rebalance. The `blended` policy
(gamma/volume/OI weighting) is config-selectable in the §17 schema but **not implemented**, and
`policy_for("blended")` raises `FrameworkConfigError` rather than falling back to `atm_distance`: a
policy that silently degrades when its inputs are missing is exactly the silent default the fail-fast
contract forbids.

**Distance is measured from the ATM the Window Manager already resolved**, never re-derived here. §15
states the ATM rule — nearest strike to spot, and on an exact tie the **lower** strike — once, and F4
reads it through `market_context_from_window()`. Two implementations of one rule is how a live run and a
replay of the same raw log come to disagree about which leg was the ATM.

**`rank_scores()` is the single ordering site (§10.3).** Every policy returns through it, so the total
order lives in exactly one place:

```
sort key = (-score, symbol)      # score descending, then symbol ascending
rank     = position + 1          # 1-based, produced nowhere else
```

Equal-distance ties are the **common** case, not an edge case: the CE and PE at one strike always tie,
and so do mirrored strikes either side of the ATM. The symbol tie-break is what makes those deterministic
instead of dependent on the order the universe happened to arrive in — an unchanged market yields a
byte-identical ranking, which is what replay determinism rests on. `rank_scores` refuses duplicate
symbols, because the tie-break cannot separate two rows for one leg and guessing would be worse than
saying so.

**`PriorityScore.rank` is 1-based and is the only rank basis in the system (§14.2, fork F4).** The
drafted 0-based positional index was **deleted**, not reconciled — two bases in circulation is precisely
the off-by-one that §21 D-5 records. `PriorityScore.__post_init__` rejects `rank < 1`, so the floor is
enforced by the type rather than merely produced by the ranker, and `rank_scores` is the only place a
rank is ever constructed.

**`MarketContext` is a frozen per-pass snapshot** carrying `underlying`, `spot`, `atm_strike` and nothing
else. It is rebuilt each pass and never mutated in place, which is what makes a ranking reproducible from
a recorded pass. It deliberately carries no gamma/volume/OI bag: those fields belong to the phase that
implements the policy consuming them, and a field carried unused is a field whose semantics nobody has
decided.

**Candidate identity is preserved.** Each `PriorityScore` carries the exact `Instrument` object it scored
(asserted by `id()`), the scored set equals the candidate set, and the input sequence is not mutated. F5
receives what F3 produced, not a re-derived lookup that could drift out of step.

**Multiple underlyings rank independently**, each from rank 1 (`rank_candidates`). Ranking them into one
pool would presuppose a shared budget, and how budget is split across underlyings is §10.4 / F5's
question. A window that did not resolve contributes an empty tuple rather than vanishing from the result,
so the caller can still see the underlying was considered.

**Wiring errors raise; degenerate markets do not.** An empty candidate universe ranks to an empty tuple
— an ordinary outcome. A candidate whose `underlying` disagrees with the context, a non-`Instrument`
candidate, a non-`MarketContext` context, a non-finite score, or a non-`RESOLVED` `WindowResult` all
raise: a plausible-looking partial ranking would hide the bug.

**Deliberately absent, and asserted absent by source-level AST scans** rather than left to review:
`tbt_budget` and any budget concept, `max_channels`, the capability layer (not imported), premium overlay
selection, `DepthType` or any depth tier, hysteresis (§14.1), cooldown (§14.3), subscription state,
reconciliation, and broker I/O. `AtmDistancePolicy`'s entire public surface is `name` and
`compute_priorities`.

## `budget_allocator.py` — the inter-underlying premium split (Plan_002 §10.4, §13)

Answers **how many premium slots each underlying gets**, from a logical broker-wide budget. It does not
compute that budget: `total_budget` arrives as a plain integer, and the allocator contains no
`max_channels`, `symbols_per_connection`, `max_connections`, no `effective_budget` derivation, and no
hardcoded `15`. `tbt_budget` is a broker *capability* resolved by the F2 capability layer, so a broker
that exposes `1x20` or `5x10` changes config and nothing else.

**Largest-remainder on exact rationals.** Shares are computed with `fractions.Fraction`, never floats.
Independent per-underlying rounding can sum *above* the budget and blow a hard broker limit, and float
division can truncate an exact `13` to `12`; both are silent. Integer arithmetic throughout.

**Floors.** `min_per_underlying` applies to **premium-eligible** underlyings only (§13.2) — an
ineligible underlying reports `candidate_count = 0`, takes no floor, and receives `0`. A floor is capped
by that underlying's candidate count, so it never invents capacity. An infeasible floor degrades
deterministically and **never raises at runtime**: that check belongs to startup (F7), and raising here
would kill PROCESSOR mid-session.

**Redistribution is capacity-driven, not priority-driven** (§13.3, fork F6). Unspent slots go out one at
a time, round-robin in descending weight order with ties broken by name, to eligible underlyings that
still have headroom. It reads candidate counts and configured weights only — never a `PriorityScore`,
because coupling the inter-underlying split to individual leg priority collapses the §10.4/§10.3
separation. Termination is structural: every step decrements `leftover`, and the outer loop exits when
no underlying has headroom. `redistribute_unspent: false` leaves a genuine surplus unspent.

Worked examples from §13.4, both carried as fixtures: with `total_budget = 15`, NIFTY eligible with 20
candidates and SENSEX ineligible gives **NIFTY 15, SENSEX 0**; with NIFTY at 5 candidates and SENSEX at
20, weights 2.0 : 1.0 and `min_per_underlying = 2`, NIFTY caps at its 5 candidates and the 4 freed slots
redistribute, giving **NIFTY 5, SENSEX 10**.

Invariants asserted in code: `sum(result.values()) <= total_budget`; `result[u] <= candidate_counts[u]`;
every configured underlying answered.

**Owns:** no state between calls, no threads, no locks, no FDs.

## `depth_allocator.py` — the premium overlay within one underlying (Plan_002 §10.5, §14)

Answers **which of one underlying's ranked legs hold its premium slots**. It does not rank (F4), does
not decide how many slots the underlying gets (Budget Allocator), does not hold subscription state or
reconcile it (F6), and performs no broker I/O (F7).

**One instance per underlying (§10.5).** The allocator carries the current premium set, the last time
that set changed, and a bounded history ring — state that is per-underlying by nature. A shared instance
would let a busy chain's reallocation reset a quiet chain's cooldown, so churn control would silently
stop applying to the underlying that needed it least often.

**Hysteresis is effective-rank stickiness inside a bounded band** (§14.1, fork F3, resolved §20.3).
Selection takes the `budget` legs with the lowest *effective* rank:

- an **incumbent** — a leg holding a premium slot from the previous pass — competes at
  `rank - hysteresis_buffer` while `rank <= budget + hysteresis_buffer`, and at its true `rank` outside
  that band;
- a **challenger** always competes at its true `rank`;
- an effective-rank **tie is won by the challenger**.

Each clause earns its place. The subtraction stops a leg oscillating around `rank == budget` from being
promoted and demoted on alternate passes — pure churn against a hard budget, which puts a gap in the
very book being recorded. The band stops protection accumulating, so an incumbent that has genuinely
drifted away loses its advantage instead of holding a scarce slot forever. The tie rule is the
anti-lockout: an incumbent may out-hold a strictly worse challenger, never an equal or better one, so a
rank-1 leg — the ATM — can never be locked out. `hysteresis_buffer = 0` collapses all of it to ordinary
top-N on true rank.

With `budget = 3, buffer = 2`: an incumbent at rank 4 (effective 2) **keeps** its slot against a rank-3
challenger; an incumbent at rank 5 (effective 3) **loses** the tie to a rank-3 challenger; an incumbent
at rank 6 is outside the band and loses outright. **No `hysteresis_buffer < smallest premium budget`
startup guard exists** — the anti-lockout is a property of the selection rule, not of config (§20.3).

**The cooldown gates premium reshuffles only** (§14.3, fork F5). A baseline addition is immediate:
gating it would leave a newly-relevant strike entirely unsubscribed for the cooldown, a hole in the book
at exactly the moment it matters. The first allocation of the session is never gated either, or the
recorder would sit unsubscribed at startup for a full cooldown. Two things still happen inside a
cooldown: a leg that has left the candidate window loses its slot (disappearance, not churn), and a
shrunk budget still truncates, keeping the best-ranked held legs — the budget is a hard broker limit.

**Budget is passed per call and never stored** (§10.5): the split changes whenever another underlying's
candidate count moves, so a remembered budget would go stale unnoticed. **Rank basis is
`PriorityScore.rank`, 1-based and the only basis** (§14.2) — list position is never a second rank, so a
shuffled input produces an identical allocation. **The clock is injected and has no default**, so no
business logic reads a wall clock, a test advances time without sleeping, and a replay reproduces a live
pass exactly.

**Diff semantics** (§14.4, fork F8). `added_new` and `promoted_to_premium` are **disjoint by
construction** — a leg is "new" only if it was not a candidate last pass and "promoted" only if it was —
so a leg allocated straight to premium is subscribed once at premium depth rather than emitted as an add
followed by a promotion, which would subscribe it twice and burn a scarce slot on the round trip.
`removed` is **observability only** and produces no unsubscribe: baseline coverage is monotone within a
session (F6's invariant), so a leg leaving the window keeps its standard subscription and loses only its
premium slot. It is reported because an operator reading the logs still needs to see the window move.

**Owns:** per-underlying state (premium set, last-change timestamp, `deque(maxlen=history_limit)` debug
ring — bounded by construction, since an unbounded list is a slow leak in an all-session process). No
threads, no locks, no FDs.

## `subscription_state.py` — desired coverage plus snapshot-derived observability (Plan_002 §9, §12, §20.4)

`SubscriptionState(effective_budget, *, clock)` holds the desired coverage (`baseline` / `premium_overlay`)
and the broker-neutral observability annotations (`pending` / `failed`). It is PROCESSOR-owned and
single-writer (§7), so it carries no lock of its own; it is a plain synchronous object with no thread, no
handle, and no broker call. It also ships the reconciliation vocabulary — `SubscriptionPlan`,
`SubscriptionAction`, `ActionKind` — so the data model lives apart from the reconciliation algorithm.

**State is keyed by leg identity; depth is a value** (fork F10, §9). Every set is keyed by `Instrument`; a
leg's depth is membership in `premium_overlay`, never part of the key and never a `:50` wire suffix. This
is what makes "the same leg at a different depth" expressible — the recorder's old wire-symbol key encoded
`:50` and could not.

**`baseline` grows monotonically; `premium_overlay` is replaced each pass.** `set_desired(desired)` unions
every key into `baseline` and removes none, so a leg that leaves the candidate window keeps its standard
subscription; the premium set is *replaced* by the keys mapped to premium, so a leg dropped from the
premium selection demotes to standard while remaining baseline. `reset()` is the only operation that may
shrink `baseline` — used at graceful shutdown and as the post-reconnect starting point, after which the
whole desired state is re-issued (§12.6). `standard = baseline - premium_overlay` is derived, never stored.

**`effective_budget` is a plain integer** — a broker capability resolved by the F2 layer, never
reconstructed here from `max_connections` / `symbols_per_connection`, and never a hardcoded `15`.
`set_desired` enforces `len(premium_overlay) <= effective_budget`, so the §9 budget invariant holds before
any action is dispatched. Invariants asserted in code: `premium_overlay ⊆ baseline`; `pending ∩ failed =
∅`.

**`pending` / `failed` are snapshot-derived observability, not a broker ledger** (F6 fork, §20.4, Option
A). `record_dispatch(plan)` marks a plan's actioned legs (every group except `removed`) `pending` —
awaiting confirmation in a later live snapshot, **not** broker success — and clears them from `failed`
(a retry is now in flight). `apply_live(current)` reconciles observability against a broker-neutral live
snapshot the caller has already obtained: it clears any `pending` **or** `failed` leg the snapshot now
shows at its desired depth (the live snapshot is the §5 authoritative observation boundary, so it
overrides a stale failure record) and **never manufactures** a failure from a wrong-depth or missing leg
(§4). `record_failed(legs)` is the minimal, no-taxonomy path moving legs `pending -> failed`. None of
these perform I/O, and `apply_live` does not know or care how `current` was produced — acknowledgement,
polling, reconnect enumeration, subscription inspection, or a future mechanism, all owned outside F6.

**The clock is injected and has no default**, so no business logic reads a wall clock; `last_updated` is
stamped from it on construction and on every mutator, and a replay reproduces a live pass exactly.

**Owns:** four sets (`baseline`, `premium_overlay`, `pending`, `failed`) and a `last_updated` float. No
threads, no locks, no FDs.

## `subscription_manager.py` — pure desired/current reconciliation (Plan_002 §10.6, §14.4)

`SubscriptionManager.reconcile(desired, current) -> SubscriptionPlan` turns a desired leg -> depth map and
a live one into a plan. The manager is stateless (`__slots__ = ()`), clockless, holds no broker
connection, and starts no thread; it exists as a class rather than a bare function so the reconciliation
strategy has a named seam a later phase can extend without changing call sites.

**`reconcile` is pure** (§10.6, frozen there): synchronous, deterministic, mutates neither argument, does
no I/O, and makes **no broker assumption**. It does not inspect `pending` or `failed` and does not
suppress an action because a prior attempt is in flight — the live `current` snapshot is the sole
authority on the book, so a still-pending action that has not yet landed is simply re-emitted, and that
re-emission *is* the retry. The observability annotations are folded in by `SubscriptionState`,
deliberately outside this function.

**The eight §6 F2 transition rows**, realised by comparing two maps: `absent -> standard|premium` is
`added_new` at the target depth (a leg premium on first sight is `added_new` **alone**, never also
`promoted_to_premium` — §14.4 disjointness); `standard -> premium` is `promoted_to_premium` (UPGRADE);
`premium -> standard` is `demoted_to_standard` (DOWNGRADE); the two same-depth rows are no-ops; a leg in
`current` but absent from `desired` is `removed`, **observability only and never an unsubscribe** (row 7 —
baseline coverage is monotone within a session); `reset`/shutdown is `SubscriptionState.reset`, not a
reconcile concern (row 8). Depth transitions stay abstract — only logical `UPGRADE` / `DOWNGRADE` intent,
never a wire mechanism.

**Release-before-claim ordering.** `SubscriptionPlan.ordered_actions()` emits every demotion before any
addition or promotion, so a promotion never precedes the demotion that frees its slot against a hard
premium budget. Every group is sorted by `str(instrument)`, so the plan is deterministic regardless of
input-map iteration order. No numeric priority field, no priority-policy coupling.

**Owns:** nothing — no state, no threads, no locks, no FDs. Imports only `typing` plus the `models` and
`subscription_state` siblings.

**The F7 boundary is untouched — and as of 2026-08-26 it is measured.** F6 asked five questions it
could not answer, and F7B answered three of them on the wire:

- A bare re-subscribe does **not** change delivered depth. The acknowledgement claims it does; the
  wire disagrees, and nothing later corrects it. OBSERVED.
- The `:50` spelling is what selects the deep book, and the two spellings are **independent
  concurrent subscriptions** — so a retier is an add/remove overlap, never an edit. OBSERVED.
- Unsubscribe stops delivery end to end, measured against a re-subscribe control rather than
  inferred from acceptance. It is not required to *obtain* depth 50, but it **is** required to
  release the superseded leg. OBSERVED.

Two stay open, and both are **unrun measurements rather than negative answers**: behaviour at the
15-symbol ceiling (no slot counter is exposed, and measuring it means approaching the ceiling) and
reconnect depth restoration (the proxy was shared with a live client holding 180 symbols). The
adapter contract is conservative on exactly those two points — release before claim, and re-observe
after a reconnect. Full record: `Documents/patches/depth_transition_probe_20260826.md` §16-§19.

The harness that produced this lives entirely outside this package
(`tools/fyers/depth_transition_probe.py` and its broker-neutral model, 103 offline tests). F7 added
**no framework module**: `broker_adapter.py` still does not exist and a test asserts it. Writing it
is a separate, separately approved phase — F7 measures, the adapter executes.

## `broker_adapter.py` — wire execution and delivery-derived observation (Plan_002 §20.4, §22.9)

The only module in the package that knows a wire format exists, and the only one written **after** a
live measurement rather than from a specification. Every rule below traces to the F7B evidence
(`Documents/patches/depth_transition_probe_20260826.md` §16-§19).

**Wire identity is per tier, and the suffix never travels upward.** `Instrument` stays the framework's
identity everywhere; the adapter renders `SYMBOL` for `DepthType.STANDARD` and
`SYMBOL:<premium_depth>` for `DepthType.PREMIUM`, with the suffix built from
`capability.premium.depth` — a broker with a 20-level deep tier renders `:20` with no code change.
`live_snapshot()` is keyed by `Instrument`, and a test asserts no returned key carries a suffix.

**A retier is a release then a claim, never the reverse.** F7B measured that the two spellings are
independent concurrent subscriptions, so promotion is `unsubscribe SYMBOL` -> `subscribe SYMBOL:50`
and demotion is `unsubscribe SYMBOL:50` -> `subscribe SYMBOL`. Claiming first would transiently hold
both legs, which is the one sequence that can overshoot a premium ceiling nobody has measured. A
release that fails at the transport **abandons its claim for that pass**; the leg reappears in the next
reconciliation rather than being claimed on the strength of a release that may not have taken effect.
Plan-wide, the order from `ordered_actions()` is preserved: demotions, then additions, then promotions.
`removed` produces no wire traffic at all.

**What gets released is decided by the adapter's own leg book, not by the plan's vocabulary (F7.6,
fork F17).** The action's kind is computed upstream against the delivery-derived live snapshot, which
cannot see a leg that has been dispatched but has not yet delivered a packet — so a leg re-tiered inside
its own subscribe-to-first-packet window arrives spelled as a plain `SUBSCRIBE`. `_obsolete_tiers()`
therefore asks a different question: *which wire legs do I hold for this instrument at another tier?*
Held means `REQUESTED` or `DELIVERING`; `RELEASING` already has an unsubscribe in flight and is not
released twice, and `FAILED` is not held at all. The binding invariant is:

> For a given `Instrument`, the adapter must never claim a new wire tier while an obsolete wire tier is
> still adapter-owned — **even when neither leg has yet produced a delivered packet.**

This changes only *which* unsubscribe is emitted. **Owned is not observed**: three things stay distinct —
*desired* (what the framework wants), *owned* (what the adapter dispatched and has not released), and
*observed* (what delivered packets prove). An owned leg is still absent from `live_snapshot()`, an
acknowledgement still confirms nothing about depth, and no new claim about the broker is introduced.

**An acknowledgement is transport news; only a packet is depth evidence.** CASE A was acknowledged
`success` with `depth: 50` and delivered five levels, uncorrected. So an accepted ack sets `accepted`
and leaves the leg `REQUESTED` — out of `live_snapshot()`; an explicit rejection marks it `FAILED`,
frees any premium slot, and surfaces through `take_rejections()`; an unacknowledged request stays
`REQUESTED`, ambiguous rather than failed. Only a delivered packet on the leg's own wire symbol moves it
to `DELIVERING`.

**A leg's tier is fixed when its wire symbol is rendered.** Confirming a premium leg by counting levels
would leave an illiquid strike with a genuinely shallow book unconfirmed forever, churning. Since depth
is a property of the wire symbol, delivery on `SYMBOL:50` confirms premium at any level count. The
observed count is recorded as observability and never invalidates a leg.

**A released leg that keeps delivering stays visible.** `RELEASING` counts as live only when
`last_packet_at > released_at` — the same discrimination `_measure_unsubscribe_effect` used in F7B:
silence alone proves nothing, continued delivery proves the release did not take. An ineffective
release therefore surfaces on the next reconciliation instead of vanishing.

**Capacity is one logical budget; connection arithmetic stays here.** The adapter consumes
`BrokerCapabilityLayer.effective_budget` and packs premium legs into `(connection_id, channel_id)`
slots itself, filling a connection before opening the next; channel ids are **strings**. Standard legs
consume no premium slot and carry no connection assignment. A claim beyond the budget, or a premium
claim on an exchange the capability does not cover, is **refused** and reported — never dropped
silently. No allocator learns that connections exist: a test scans the four allocator/subscription
modules for `max_connections`, `symbols_per_connection`, and `channel_id`, and another scans the
adapter's own AST for the literals `15`, `50`, and `250`.

**Reconnect is conservative, and stays UNKNOWN.** Reconnect depth restoration was not measured, and the
module asserts nothing in either direction — a test greps it for both "preserves premium depth" and
"loses premium depth". `handle_reconnect(desired)` treats every prior subscription as unknown, reissues
the desired coverage baseline-first, and confirms nothing until packets return. The re-plan that follows
is absorbed at the adapter (a claim on a leg already `REQUESTED` or `DELIVERING` is skipped), so no wire
storm results.

**Retry is the next pass, not a loop.** A failed leg is simply absent from `live_snapshot()`, so
`reconcile()` re-plans it. A test fails the module on any `while` statement. Bookkeeping is pruned at
the start of each `apply()` — released legs that have gone silent, and failed legs — so a session of
retiering does not accumulate records.

**Threads: none. Sockets: none. FDs: none.** It runs synchronously on the caller's thread (FEED-owned in
F8) and writes through the caller's `DepthTransport`; it never creates that transport and never closes
it. `close()` drops the adapter's own bookkeeping, is idempotent, and leaves the adapter usable.

## `orchestrator.py` — one pass across every layer (Plan_002 §20, F8)

The layer that runs the others in order, so no caller has to know the order. Pure and synchronous: it
owns no thread, no lock, no socket, and no clock (the clock is injected).

`FrameworkOrchestrator(config, universe, *, clock)`:

| Member | Purpose |
| --- | --- |
| `due(spots) -> str \| None` | The trigger for this moment, or `None`: `"interval"` when the configured cadence has elapsed, `"window_change"` when the ATM/window key moved. No cross-thread signal is involved — the spot map the caller already holds is enough. |
| `rebalance(spots, live, *, rejected=(), trigger=None) -> RebalanceResult \| None` | One pass: `WindowManager` -> `PriorityPolicy` -> `BudgetAllocator` -> `DepthAllocator` -> `SubscriptionState.set_desired()` -> `SubscriptionManager.reconcile()`. Returns the plan plus the desired map, the windows, the per-underlying budgets, the trigger, and the timestamp. `None` when no pass was due. |
| `desired()` | The current desired coverage — what a reconnect must restore. |
| `reset()` | Forget desired coverage (graceful shutdown). |
| `capability` | The resolved `BrokerCapabilityLayer` this orchestrator planned with. Exposed so the **one** broker-facing consumer (FEED's `BrokerAdapter`) renders the wire against the very object the plan was budgeted against, instead of resolving a second layer that could silently disagree. |
| `underlyings` / `eligible` / `effective_budget` / `passes` / `last_pass_at` | Observability. |

`RebalanceResult.is_empty` is what lets the bridge refuse to publish an actionless plan.

Premium eligibility is per exchange (`premium_exchanges`), so with the shipped FYERS capability NIFTY/NFO
is eligible and SENSEX/BFO deliberately is not — the orchestrator plans premium for the eligible
underlyings only and leaves the rest entirely at standard depth.

Tests: `tests/test_framework_orchestrator.py` (90).

## `config.example.yaml` — the FYERS capability configuration (§16)

A version-controlled reference §17 block with the FYERS facts filled in: `symbols_per_connection: 5`,
`max_connections: 3`, `max_channels: 50` (bookkeeping only), premium depth 50, standard depth 5,
`premium_exchanges: [NSE, NFO]`. `total_symbol_budget` is omitted, meaning the `UNLIMITED_BUDGET`
sentinel — "no account-wide cap beyond the connection math".

It is a **copy source, not a live config**: `enabled: false`, and wiring the block into the recorder's
`config.yaml` is F8's integration step. A test loads it end to end and asserts `effective_budget == 15`,
NFO eligible, BFO not — so the FYERS facts are proven to reach a budget through configuration alone.

## `config.py` — schema and fail-fast validation (Plan_002 §17)

Mirrors the recorder's `config.py` conventions: a frozen typed config object, a validator that
**collects every error in one pass**, and an error type whose `report()` renders them all. Missing or
out-of-range values fail hard — no silent defaults.

Validated sections: `enabled`, `broker_capabilities` (typed all the way down), `priority_policy`,
`budget_allocator`, `depth_allocator`, `rebalance`, and the optional `window_manager` placeholder.
Enumerated keys are checked against their allowed sets. The behavioural sections stay read-only mappings
until the phase that owns each gives it a typed shape — typing them now would mean guessing at fields
those phases have not designed.

Three schema decisions worth knowing:

- **The whole `market_depth_framework` section is optional in the file.** Absent means the framework is
  off, which is the F1 state: the shipped `config.yaml` carries no such section and the recorder's own
  loader never sees one. Present-but-malformed still fails hard.
- **Unknown keys are rejected.** A typo'd key that validation ignores is a silent default by another
  name — the operator believes a setting is in force when it is not. This is also what keeps
  `premium_budget` and `premium_eligible` out of allocator config: the budget is a capability, and
  eligibility is a broker fact, so hand-copying either into config would let it drift from the broker.
- **F1 validates shape, not feasibility.** The §13.2 check
  `min_per_underlying * len(eligible_underlyings) <= effective_budget` needs both `effective_budget` and
  the eligible set, which F2 resolves. F1 checks that `min_per_underlying` is a well-formed non-negative
  int and stops there.

## Fail-fast / exit-1 contract

`python -m market_depth_recorder.market_depth_framework --config <path>` exits **0** (valid, or section
absent), **1** (validation failure, full report to stderr), **2** (CLI usage error) — matching the
recorder's convention. Deliberately a separate entrypoint from the recorder's `__main__.py`, since F1
must not change recorder behaviour.

## Threads, locks, FDs owned

- **Threads: none.** The recorder's four-thread architecture (FEED, RAW WRITER, PROCESSOR, DB WRITER) is
  preserved exactly. Plan_002 fork F1 settles that the framework is synchronous and threadless.
- **Locks: none.** No state is shared *between* components. The capability layer, the Window Manager,
  the Priority Policy, the Budget Allocator, and the `SubscriptionManager` are immutable or stateless and
  hold nothing between calls. The Depth Allocator and `SubscriptionState` are the stateful components —
  the allocator holds its underlying's premium set, cooldown timestamp, and history ring;
  `SubscriptionState` holds the desired coverage plus `pending` / `failed` — but each is PROCESSOR-owned
  and single-writer (Plan_002 §7): its state is read and written only from the one thread running the
  rebalance pass, so it needs no lock of its own. Should a later phase call `allocate()` for several
  underlyings concurrently, each still touches its own instance and nothing else.
- **FDs: one**, transiently — the config file handle in `load_framework_config`, opened under `with` and
  closed on every path including the YAML-error unwind. No socket, subprocess, DB handle, queue, or
  executor anywhere in the package. **The Broker Adapter adds none of these**: it writes through a
  transport the caller owns, so the WebSocket FD belongs to the recorder's FEED thread and its lifetime
  is unchanged. AST tests fail the module on any thread/process/executor/queue construction and on any
  `socket()` / `open()` / `connect()` / `sqlite3` / `duckdb` call.

A test imports the package in a fresh subprocess with `socket.socket` and `sqlite3.connect` nulled and
asserts the thread count is unchanged and nothing is printed, so inertness is verified rather than
asserted in prose.

## Config keys consumed

Every key under the top-level `market_depth_framework` section (Plan_002 §17). F1 validates them all at
startup (fail-fast, exit 1, enabled or not); since F8 they are also **consumed at runtime** — the
orchestrator reads the window, policy, budget, hysteresis, and rebalance keys, and `enabled` is
interpreted in exactly one place, `framework_bridge_for()` in `framework_bridge.py`. The section is
excluded from the recorder's `config_hash`.

## Tests

| File | Covers |
|---|---|
| `tests/test_framework_models.py` | `Instrument` / `DepthType`; the no-depth-field assertion (F10); hashability and set-key behaviour; field validation |
| `tests/test_framework_capabilities.py` | Tier and capability validation; `UNLIMITED_BUDGET` int-ness and arithmetic; the F1/F2 boundary guard |
| `tests/test_framework_config.py` | Valid shape; one negative case per rule; error collection; file loading; exit-1 in-process and via subprocess |
| `tests/test_framework_package.py` | Export surface; absence of later-phase modules; one-way dependency; import inertness; no index/exchange literals in executable code |
| `tests/test_framework_window_manager.py` | ATM resolution incl. ties-to-lower and order-independence; all five boundary positions; exact membership and counts; call and put sides verified **separately** plus their partition; the codec and expiry seams; degenerate spot/universe inputs; multiple underlyings with different windows; determinism under repetition and shuffling; two boundary property tests; source-level scope guards |
| `tests/test_framework_priority_policy.py` | ATM-distance ranking and score monotonicity; the 1-based rank basis enforced by both the ranker and the type; the score-desc-then-symbol total order incl. the CE/PE and mirrored-strike ties; candidate identity preservation; determinism under repetition and shuffling; empty and single-candidate universes; `MarketContext` immutability and validation; default-policy selection and the `blended` refusal; multiple underlyings ranking independently from rank 1; the F3 → F4 adapter; source-level scans asserting no budget, depth, overlay, hysteresis, cooldown, subscription, or broker concept |
| `tests/test_framework_budget_allocator.py` | Both §13.4 worked examples as fixtures; the three invariants incl. a randomised property sweep; largest-remainder behaviour and exact-integer shares (the float-truncation case); floors, floor capping, and the ineligible-underlying case; redistribution order, termination, opt-out, and capacity ceiling; degenerate budgets and candidate sets; determinism across repetition and mapping insertion order; construction and wiring validation; the unimplemented-policy refusal; source-level scans asserting no broker-capability arithmetic, no hardcoded `15`, no `PriorityScore`, and no depth/subscription concept |
| `tests/test_framework_depth_allocator.py` | The **five mandatory §20.3 hysteresis regressions** plus an exhaustive rank-1 anti-lockout sweep over every budget/buffer/incumbency combination; oscillation suppression and its buffer-0 control; the rank basis under shuffling and non-contiguous ranks; cooldown on both sides of the boundary, the baseline-addition bypass, the never-gated first pass, window departure, and budget truncation; diff disjointness, direct-to-premium adds, and `removed` as observability only; per-underlying independence; bounded history; determinism of a whole replayed sequence; source-level resource and scope scans incl. the no-wall-clock check |
| `tests/test_framework_capability_layer.py` | `effective_budget` incl. a `min()` property grid; `max_channels` exclusion (result **and** source); `UNLIMITED_BUDGET`; NFO/BFO eligibility; capability fail-fast; §13.2 floor check; independence from underlyings/ranking/policy; no-I/O and no-hardcoded-15 source scans |
| `tests/test_framework_subscription_state.py` | Construction and `effective_budget` / clock validation; empty state; standard and premium baselines; baseline monotonicity and window departure; the mutable premium overlay; the budget bound; the snapshot lifecycle (`record_dispatch` -> `pending`, `apply_live` clearing confirmed `pending`/`failed`, `record_failed` with no broker taxonomy); `pending ∩ failed` disjointness; `reset`; the injected clock advancing `last_updated`; the `SubscriptionPlan` / `SubscriptionAction` / `ActionKind` value semantics; source-level resource and scope scans (no broker execution, no unsubscribe, no wall clock, no import-time side effect) |
| `tests/test_framework_broker_adapter.py` | Wire rendering both tiers and its inverse, capability-derived suffix, custom dialects, and the no-suffix-in-`Instrument` guard; basic operations incl. correlation ids, accepted / rejected / unacknowledged, and `removed` emitting nothing; retiering — release-before-claim on both directions, no claim before its release, the two spellings as independent records, same-tier idempotence, plan-wide ordering; observability — ack never confirms depth, packets do, thin books stay premium, CASE A's bare-spelling packet never confirms premium, a released-but-still-delivering leg stays live, and the full `reconcile -> apply -> observe -> apply_live` loop; failure and retry incl. slot release on failure, no aborted plans, drained rejections, and the no-`while` guard; reconnect confirming nothing until packets return and asserting neither restoration nor loss; capacity — budget from the capability, refusal not dropping, string channel ids, connection packing, and no allocator knowledge of connections; resource safety and the structural/AST guards (no thread/socket/FD, no wall clock, no import-time statement, no hardcoded broker numbers); **F7.6** — retiering before observation: promotion and demotion each releasing the leg the adapter owns, only the superseded wire leg of the retiered instrument, a slot freed by a pre-observation release being reusable in the same pass, the observed path unchanged, repeated no-packet retiering, release failure abandoning the claim, no duplicate release in flight, and `owned` still not `observed` |
| `tests/test_framework_orchestrator.py` | One pass across every layer in order; `due()` interval and window-change triggers and their absence; `RebalanceResult` contents and `is_empty`; `desired()` and `reset()`; premium confined to eligible exchanges; per-underlying budget split; determinism across repeated passes; the injected clock |
| `tests/test_framework_bridge.py` | Envelope publication and sequencing; a pass that did not run publishing nothing; an empty plan never evicting an unexecuted one; the reverse channel — observation consumed once, absence meaning "no news", rejections handed over once and surviving a skipped pass; `publish_observation` never raising; fault containment on `rebalance` and `reset`; `force_rebalance` labelling; the stats key set; the clock type check |
| `tests/test_framework_integration.py` | The F8 matrix end to end against the **real** orchestrator and adapter with a fake transport: startup coverage, baseline + premium overlay within `effective_budget`, ineligible BFO getting no premium leg, the `_on_open` and `_on_message` drains, **tee-before-drain ordering**, the accepted silent-feed residual, latest-wins with one dispatch, delivered-packet-not-ack promotion, rejection reaching the next pass, `AdapterTransport` raising where `_send_frame` swallows, framework faults isolated from both PROCESSOR and FEED, reconnect reissuing without claiming depth and without double-subscribing, **DSM option-subscription calls == 0 with the flag on and > 0 with it off**, `active_subscriptions` matching the adapter's claimed symbols, flag-off inertness, and the real `_build_default_pipeline()` producing four workers sharing one bridge |
| `tests/test_framework_subscription_manager.py` | All eight §6 F2 transition rows individually; `added_new` / `promoted_to_premium` disjointness and direct-to-premium adds; `removed` as observability only with no unsubscribe; release-before-claim ordering; deterministic sorting under input reordering; idempotence; argument-non-mutation and malformed-map rejection; statelessness; source scans asserting `reconcile` never inspects `pending` / `failed`, emits no unsubscribe or broker execution, and reconstructs no broker capability |

No live broker, WebSocket, or market feed is required by any of them.
