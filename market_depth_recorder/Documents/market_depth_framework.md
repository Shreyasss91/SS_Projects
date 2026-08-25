# market_depth_framework — module reference

Generic market-depth allocation framework. Broker-agnostic layer that will decide **which** option legs
are subscribed and **at what depth tier**, so the recorder can run the hybrid (near-ATM legs at premium
depth within the broker's budget, the rest at standard depth) with no index name, exchange code, or
broker fact in engine code.

Planned in `plans/Plan_002_market_depth_framework_implementation.md`. This document describes the
**implemented** state only.

## Implemented state: phase F1 (contracts only)

F1 delivers the package skeleton, the data models, the broker-capability dataclasses, and the
configuration schema with its fail-fast validation. **None of the seven behavioural layers exists yet.**

| Layer | Phase | State |
|---|---|---|
| Data models (`Instrument`, `DepthType`) | F1 | Built |
| Broker-capability dataclasses | F1 | Built (shapes only) |
| Config schema + startup validation | F1 | Built |
| Broker Capabilities layer (`effective_budget`, eligibility) | F2 | Not built |
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
├── capabilities.py    # UNLIMITED_BUDGET, PremiumTier, StandardTier, BrokerCapability
└── config.py          # FRAMEWORK_SECTION, FrameworkConfig, FrameworkConfigError, validators
```

## Public API

```python
from market_depth_recorder.market_depth_framework import (
    DepthType, Instrument,                                  # models
    UNLIMITED_BUDGET, BrokerCapability, PremiumTier, StandardTier,   # capabilities
    FRAMEWORK_SECTION, FrameworkConfig, FrameworkConfigError,
    load_framework_config, validate_framework_config,        # config
)
```

- `validate_framework_config(root) -> FrameworkConfig | None` — validate the framework block inside an
  already-parsed config mapping. Returns `None` when the section is absent (framework off). Raises
  `FrameworkConfigError` carrying the complete error list.
- `load_framework_config(path) -> FrameworkConfig | None` — same, reading a YAML file first.

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

**F1 deliberately exposes no `effective_budget()` and no `supports_premium()`.** Both belong to the
Broker Capabilities *layer* in F2. A test asserts their absence so the boundary is checked, not merely
reviewed.

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
- **Locks: none.** No shared mutable state exists in F1.
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

No live broker, WebSocket, or market feed is required by any of them.
