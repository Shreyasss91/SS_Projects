# market_depth_framework — module reference

Generic market-depth allocation framework. Broker-agnostic layer that will decide **which** option legs
are subscribed and **at what depth tier**, so the recorder can run the hybrid (near-ATM legs at premium
depth within the broker's budget, the rest at standard depth) with no index name, exchange code, or
broker fact in engine code.

Planned in `plans/Plan_002_market_depth_framework_implementation.md`. This document describes the
**implemented** state only.

## Implemented state: phases F1-F2

F1 delivered the package skeleton, the data models, the broker-capability dataclasses, and the
configuration schema with its fail-fast validation. F2 adds the **Broker Capabilities layer** — the
first behavioural layer: one logical `effective_budget` and per-exchange premium eligibility.

| Layer | Phase | State |
|---|---|---|
| Data models (`Instrument`, `DepthType`) | F1 | Built |
| Broker-capability dataclasses | F1 | Built (shapes only) |
| Config schema + startup validation | F1 | Built |
| Broker Capabilities layer (`effective_budget`, eligibility) | F2 | Built |
| §13.2 `min_per_underlying` feasibility check | F2 | Built (not yet called from a live path — F8 wires it) |
| Window Manager | F3 | Not built |
| Priority Policy | F4 | Not built |
| Budget Allocator / Depth Allocator | F5 | Not built |
| Subscription Manager | F6 | Not built |
| Broker Adapter | F7 | Not built (blocked on the F7 depth-transition probe, Plan_002 §20.1) |
| Recorder integration | F8 | Not built |

**The framework is inert.** It is not imported by any recorder module, not referenced from
`config.yaml`, and not reachable from the live pipeline. The recorder's existing
subscribe-everything-at-`:50` path is unchanged and remains the active path.

## Package layout

```
market_depth_framework/
├── __init__.py        # public surface; no side effects at import
├── __main__.py        # --validate-config entrypoint; exit 0 valid / 1 invalid / 2 usage
├── models.py          # Instrument, DepthType
├── capabilities.py    # UNLIMITED_BUDGET, PremiumTier, StandardTier, BrokerCapability  [F1]
├── capability_layer.py # BrokerCapabilityLayer: effective_budget, eligibility  [F2]
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
- **Locks: none.** No shared mutable state exists. The capability layer is immutable, so concurrent
  reads need no synchronization.
- **FDs: one**, transiently — the config file handle in `load_framework_config`, opened under `with` and
  closed on every path including the YAML-error unwind. No socket, subprocess, DB handle, queue, or
  executor anywhere in the package.

A test imports the package in a fresh subprocess with `socket.socket` and `sqlite3.connect` nulled and
asserts the thread count is unchanged and nothing is printed, so inertness is verified rather than
asserted in prose.

## Config keys consumed

Every key under the top-level `market_depth_framework` section (Plan_002 §17). None are consumed at
runtime yet — F1 validates them; the phases that own each section will read them.

## Tests

| File | Covers |
|---|---|
| `tests/test_framework_models.py` | `Instrument` / `DepthType`; the no-depth-field assertion (F10); hashability and set-key behaviour; field validation |
| `tests/test_framework_capabilities.py` | Tier and capability validation; `UNLIMITED_BUDGET` int-ness and arithmetic; the F1/F2 boundary guard |
| `tests/test_framework_config.py` | Valid shape; one negative case per rule; error collection; file loading; exit-1 in-process and via subprocess |
| `tests/test_framework_package.py` | Export surface; absence of later-phase modules; one-way dependency; import inertness; no index/exchange literals in executable code |
| `tests/test_framework_capability_layer.py` | `effective_budget` incl. a `min()` property grid; `max_channels` exclusion (result **and** source); `UNLIMITED_BUDGET`; NFO/BFO eligibility; capability fail-fast; §13.2 floor check; independence from underlyings/ranking/policy; no-I/O and no-hardcoded-15 source scans |

No live broker, WebSocket, or market feed is required by any of them.
