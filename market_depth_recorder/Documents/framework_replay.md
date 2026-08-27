# framework_replay.py — the framework determinism harness (F9)

Module reference for `market_depth_recorder/framework_replay.py` and its companion tool
`tools/validation/framework_soak.py`. Describes the **implemented** state as of F9.

Design spec: `market_depth_recorder_design.md`. Plan: `plans/Plan_002_market_depth_framework_implementation.md`
§22.12 (forks F18–F21).

---

## 1. Why a second driver exists

`replay.replay_file` rebuilds the Tier-2 analytical store by driving `TickProcessor.ingest()` /
`emit_second()` **directly**. The framework pass hangs off `TickProcessor.run()`, which replay never
calls, and F8 asserts that deliberately
(`test_replay_emits_seconds_without_ever_rebalancing`: `passes == 0`, no pending plan, no adapter
frame). A Tier-2 rebuild is therefore framework-free, and that is correct — the metric catalogue must
not depend on which legs happened to be subscribed when the log was recorded.

So F9 adds a **second driver** rather than a flag on the first. `replay.py` is untouched.

## 2. What is real and what is simulated

| Component | In a framework replay |
|---|---|
| `FrameworkOrchestrator` and every layer inside it | **Real** |
| `BrokerAdapter`, wire rendering, connection pool, budget | **Real** |
| Release-before-claim ordering (the F7.6 fix) | **Real** |
| Spot prices | **Real** — read from the recording's own packets |
| Option depth packets | **Real** — fed verbatim to `adapter.observe()` |
| The broker | **Simulated** — `RecordingTransport` is a list with a `send` method |
| Delivery confirmation for a leg the recording never carries | **Simulated** and counted |

**Consequence, stated once and repeated in every artifact the harness produces:** nothing here is
broker evidence. A framework replay cannot establish reconnect depth restoration, the real premium
ceiling, or any other broker semantic — both of those remain **UNKNOWN** and are settled only by a
live run (F10). What it does establish is that the framework's allocation behaviour is a
deterministic function of the tick stream.

### 2.1 Why simulated confirmation is needed at all

The live snapshot the orchestrator plans against is **delivery-derived**: a leg becomes live when a
packet is observed on its wire symbol, never when the subscribe is accepted (F7B). With no broker,
a leg the recording does not carry never delivers, so every pass would re-plan the same subscription
forever. `--confirm-after-passes N` (default 1) synthesizes a delivery for legs still `REQUESTED`
after `N` passes. The synthesized packet carries the tier's nominal depth because that is what the
driver *claimed* — not because any broker said so, which is exactly why the count is reported per
record as `simulated_confirmations` and again in the terminal digest.

Setting `--confirm-after-passes` very high switches confirmation off entirely, which holds every leg
in the **pre-observation window** for the whole session — the window F7.6 exists for.

## 3. Flow

```
raw .jsonl.gz  ->  HEADER  ->  InstrumentManager.from_header  (no REST)
                              -> build_universe (framework_bridge)
                              -> orchestrator_for(config.framework, clock=virtual)
                              -> BrokerAdapter(orchestrator.capability, RecordingTransport)

per packet:  vclock["t"] = recv_ts
             adapter.observe(packet)          # real delivery, when the recording carries it
             spot map updated if the symbol is an underlying's spot_symbol
             trigger = orchestrator.due(spots)
             if trigger:  rebalance -> adapter.apply(plan) -> invariant check -> one log record
```

The clock is `lambda: vclock["t"]`, exactly the pattern `replay.py` uses. The module imports no
`time`, no `random`, and no `uuid`; a test asserts that at the source level.

## 4. Allocation log (fork F19 = A)

A plain `.jsonl`, one record per pass, canonically serialised (`sort_keys`, tight separators, floats
rounded to 6 places so two runs cannot differ by formatting alone). Fields:

| Field | Meaning |
|---|---|
| `seq` | Pass sequence number, 1-based. A pass that produced nothing consumes no number. |
| `at` | Virtual timestamp (the packet's `recv_ts`) |
| `trigger` | `initial` / `interval` / `window_change` |
| `spots` | Spot per underlying, `null` before its first spot packet |
| `windows` | Per underlying: status, spot, ATM, bounds, candidate count |
| `budgets` | Premium budget per **eligible** underlying |
| `desired` | Desired coverage as counts per underlying per tier |
| `actions` | Ordered plan actions as `[kind, depth, symbol]` |
| `removed` | Legs dropped from coverage |
| `wire` | The frames that actually went out, as `[action, wire_symbol]` |
| `dispatch` | `sent` / `failed` / `refused` / `skipped` counts |
| `premium_occupancy` | Premium legs the adapter holds after the pass |
| `effective_budget` | The one logical budget, from the capability layer |
| `simulated_confirmations` | Deliveries the **driver** synthesized this pass |

The file ends with a `meta_type: DIGEST` record: a sha256 over every preceding line, the record
count, and the run's stats.

### 4.1 `--verify`

`--verify REFERENCE CANDIDATE` diffs two allocation logs and reports the **first** divergence by
sequence number and field path, not a bare boolean:

```
records differ at record seq=3 field 'premium_occupancy': 15 != 16
```

Exit code 0 identical, 1 diverged. Record-count differences and digest mismatches are reported the
same way.

## 5. Invariants checked on every pass

Checked against the adapter itself, not against the plan that was requested:

1. `premium_leg_count() <= effective_budget`.
2. No `Instrument` owned at two tiers at once (`REQUESTED` or `DELIVERING` counts as owned).
3. For a symbol both released and claimed in one pass, the unsubscribe precedes the subscribe — the
   F7.6 invariant, now over a whole session.

Each violation increments a counter, logs at ERROR, and makes the CLI exit non-zero. The driver does
not abort: a soak that stops at the first violation reports one, and the point is to see all of them.

## 6. Threads, locks, FDs

None, none, and two. A framework replay is a single synchronous pass on the calling thread. The only
descriptors are the gzip reader and the allocation-log writer, both opened in `with` blocks. No
socket, no subprocess, no SQLite, no DuckDB. A test asserts `threading.active_count()` is unchanged
and that no store file is created.

## 7. Config consumed

Everything comes from the recorder config; no index name, exchange code, strike step, or depth
literal appears in the module.

| Key | Use |
|---|---|
| `underlyings[].name` / `.option_exchange` / `.initial_window` | Passed to `orchestrator_for` |
| `underlyings[].spot_symbol` | Which packets carry a spot |
| `market_depth_framework.*` | The whole framework configuration |

`market_depth_framework.enabled` is deliberately **not** consulted. Replaying is an offline analysis
of what the framework *would* do; refusing to analyse it because the live flag is off would make the
harness unusable exactly when it is most wanted. A config with no framework block at all is a
`ValueError` — there is nothing to replay.

## 8. CLI

```
python -m market_depth_recorder.framework_replay RAW [-o OUT] [-c CONFIG]
       [--from HH:MM] [--to HH:MM] [--max-packets N] [--confirm-after-passes N]
python -m market_depth_recorder.framework_replay --verify REFERENCE CANDIDATE
```

Its own entry point, so no existing command line changes. Exit codes: 0 clean, 1 an invariant
violation or a `--verify` divergence, 2 a missing recording or config.

**Fail closed.** A missing recording is reported and the run stops; no other file is ever substituted,
and no output is written.

## 9. The soak tool (fork F20 = A)

`tools/validation/framework_soak.py` replays a log N times (default 2), requires every run
byte-identical, and summarises the session: trigger mix, action counts, wire operations, tier-flip
churn per leg, the premium-occupancy histogram, the shortest observed gap between two flips of one
leg against the configured cooldown, per-pass wall time, and peak RSS. `--report` writes markdown;
`--ledger` appends one JSON record.

Its report always carries a "What this is not" section and a provenance block naming the recording's
path, size, and sha256.

The suite carries a **bounded** counterpart (`test_framework_replay.py`) over a short synthetic
session, so the invariants are enforced on every test run without adding minutes to the suite.

## 10. Test fixture policy (fork F21 = C)

The **normative** determinism fixture is a synthetic session generated inside the test suite — no
`data/` access, in-repo, reproducible anywhere. One real recording was additionally replayed
read-only for the written report (`Documents/framework_soak_report.md`), under an explicit,
recorded authorization. That real recording is not broker evidence, is not the test fixture, was not
modified, copied into the repository, or committed, and was not used to infer any broker semantic.
See Plan_002 §22.12 for the authorization text.

## 11. Related

- `Documents/framework_bridge.md` — the F8 seam this driver deliberately does not use
- `Documents/market_depth_framework.md` — the framework package itself
- `Documents/framework_soak_report.md` — the F9 written soak report
- `plans/Plan_002_market_depth_framework_implementation.md` §22.12 — scope, forks, checklist, gate
