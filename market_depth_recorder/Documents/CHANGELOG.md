# Changelog — Market Depth Recorder

Dated running log; one entry per phase/iteration (what changed, why, affected files, deferred work).

## 2026-08-25 — Plan_002 F1: `market_depth_framework/` skeleton (contracts only, framework inert)

**Why.** Plan_002's seven behavioural layers all rest on three things the framework does not yet have: a
leg identity that survives a depth change, a place to put broker-declared capacity facts, and a
validated config schema. F1 delivers exactly those and stops. Building them as the first phase means F2
onward implement against fixed contracts rather than inventing them mid-layer; keeping *only* those in
F1 means the contracts can be reviewed without a behaviour change riding along.

Two of the three are load-bearing beyond convenience:

- **`Instrument` has no depth field** (fork F10). The recorder keys `_subscriptions` by *wire symbol*,
  and `wire_symbol()` appends `:50` for premium depth — so a 50→5 transition changes the key and one leg
  looks like two (§21 D-9). Depth must be a *value* on the leg, never part of its identity, or the
  hybrid's central operation is inexpressible. The `:50` suffix becomes a rendering detail owned by the
  Broker Adapter (F7).
- **`UNLIMITED_BUDGET` is an `int`** (`2**31 - 1`), not `float('inf')`, so downstream `-> int` contracts
  and `min()` arithmetic stay honest. A fixed literal rather than `sys.maxsize`, so the value is
  identical on every platform and replay stays deterministic.
- **`max_channels` is carried but never multiplied into a budget.** The FROZEN finding is 5 symbols per
  *connection* × 3 connections = **15**; channels are a pause/resume grouping with no capacity.
  Multiplying them in is precisely the error that produced a ceiling ~16× too large. F1 has no budget
  arithmetic at all, and a test asserts `5×3 == 15 ≠ 5×50` so F2 inherits the constraint.

**What.** New sub-package `market_depth_framework/` with a **one-way dependency** — it imports nothing
from the recorder (verified by an AST scan), so it stays independently testable and broker-reusable.

- `models.py` — `Instrument` (frozen, hashable, six identity fields, validating `__post_init__`) and
  `DepthType` (`STANDARD`/`PREMIUM`; names the tier, not the level count — the numeric depth is a broker
  fact that varies by exchange and lives on the capability).
- `capabilities.py` — `UNLIMITED_BUDGET`, `PremiumTier`, `StandardTier`, `BrokerCapability`; all frozen
  and self-validating (`premium.depth > standard.depth` enforced).
- `config.py` — `FRAMEWORK_SECTION`, `FrameworkConfig`, `FrameworkConfigError`,
  `validate_framework_config`, `load_framework_config`. Follows the recorder's conventions exactly:
  every error collected in one pass, `report()` renders them all, unknown keys rejected, no silent
  defaults. The section is optional — absent means the framework is off (the current runtime state);
  present-but-malformed fails hard.
- `__main__.py` — a **separate** `--validate-config` entrypoint (exit 0 valid / 1 invalid / 2 usage), so
  F1 changes no recorder behaviour. `main(argv)` returns the code rather than calling `sys.exit`, so the
  contract is testable in-process as well as via subprocess.

**Scope boundary, enforced by tests rather than by review.** F1 establishes contracts; it does not start
F2–F6. Deliberately absent and asserted absent: `effective_budget()` and `supports_premium()` (F2, the
Broker Capabilities *layer*); the §13.2 feasibility check (needs F2's `effective_budget` and eligible
set); and every `window_manager` / `priority_policy` / `budget_allocator` / `depth_allocator` /
`subscription_manager` / `broker_adapter` module (F3–F7). Subscription reconciliation is F6.

**Inertness.** The framework is not imported by any recorder module, not present in the shipped
`config.yaml`, and not reachable from the live pipeline. A subprocess import test with `socket.socket`
and `sqlite3.connect` nulled asserts the thread count is unchanged and nothing is printed.

**Threads:** none added — the four-thread architecture (FEED, RAW WRITER, PROCESSOR, DB WRITER) is
preserved; fork F1 settles that the framework is synchronous and threadless.
**FDs:** one, transiently — the config handle in `load_framework_config`, under `with`, closed on every
path including the YAML-error unwind. No socket, subprocess, DB handle, queue, or executor.

**Tests.** +187 new (`test_framework_models.py` 36, `test_framework_capabilities.py` 50,
`test_framework_config.py` 91, `test_framework_package.py` 10). Pre-existing suite verified unchanged at
**267** in isolation; full suite **454 passed**. No existing test was modified or weakened.

**Verified.** Shipped `config.yaml` (no framework section) → "no section … (framework off)", exit 0. A
valid framework block → `FRAMEWORK CONFIG OK`, exit 0. An invalid block →
`FRAMEWORK CONFIG VALIDATION FAILED:` with **12 errors collected in one pass**, exit 1. Recorder's own
CLI unchanged: `--validate-config` → `CONFIG OK`, same `config_hash`, exit 0.

**Affected files.** New: `market_depth_framework/{__init__,__main__,models,capabilities,config}.py`;
`tests/test_framework_{models,capabilities,config,package}.py`;
`Documents/market_depth_framework.md`. Modified: `Documents/ARCHITECTURE.md` (package-layout tree +
"Built state (F1)"), `Documents/CHANGELOG.md`, `plans/Plan_002_market_depth_framework_implementation.md`
(§22.1 checklist ticked). **No recorder source, no recorder test, and no `config.yaml` changed.**

**Deferred.** Everything behavioural: F2 Broker Capabilities layer, F3 Window Manager, F4 Priority
Policy, F5 Budget/Depth Allocators, F6 Subscription Manager, F7 Broker Adapter (itself blocked on the
depth-transition probe, Plan_002 §20.1), F8 recorder integration. The behavioural config sections stay
read-only mappings until the phase that owns each gives it a typed shape — typing them now would mean
guessing at fields those phases have not designed.

## 2026-08-25 — Plan_002: all forks closed; F0 approval gate prepared (planning only, still no code)

**Why.** Plan_002 was opened with fourteen forks. F1 (four-thread contract) and F2 (baseline
monotonicity / premium overlay mutability) were decided first and unblocked the architecture. The
remaining twelve were decided in one pass so that the plan states a single settled design rather than a
menu — a phase cannot be implemented against an open fork without the implementer silently deciding it.

**What.** Documentation and plan only. **No `market_depth_framework/` code exists, and none was
written.** P0-P10 behaviour, config, and tests are untouched.

*Decisions recorded (`plans/Plan_002_market_depth_framework_implementation.md` §20)*

| Fork | Decision | Specified in |
|---|---|---|
| F3 hysteresis | displacement-based: challenger inside top `budget` displaces the worst incumbent | §14.1 |
| F4 rank basis | 1-based `PriorityScore.rank` only; the 0-based index is deleted | §14.2 |
| F5 cooldown scope | premium reshuffles only; baseline additions apply immediately | §14.3 |
| F6 unspent budget | deterministic round-robin redistribution in weight order | §13.3 |
| F7 infeasible floors | startup validation, exit 1; no runtime raise | §13.2 |
| F8 diff semantics | `removed` is observability only; `added_new` / `promoted_to_premium` disjoint | §14.4 |
| F9 depth transition | **probe first** — measured in phase F7, never assumed | §20.1 |
| F10 state key | leg identity (`Instrument`); depth is a value, not part of the key | §9 |
| F11 rebalance trigger | interval OR window/ATM change, whichever fires first | §14.5 |
| F12 default policy | `AtmDistancePolicy`; blended is config-selectable, not default | §14.6 |
| F13 premium eligibility | broker/exchange capability; ineligible gets 0 premium, full baseline | §13.1 |
| F14 PROCESSOR -> FEED | latest-wins mailbox, **provisional**, validated in phase F8 | §20.2 |

*Two binding clarifications applied*

1. **`min_per_underlying` is scoped to premium-eligible underlyings.** Read over all configured
   underlyings, F7's startup check demanded a floor for SENSEX while F13 required SENSEX to receive
   zero — a direct contradiction that would have reserved 2 of 15 scarce slots for an exchange (BFO)
   physically unable to use them. Consequence recorded in §13.2: because runtime `active` is always a
   subset of the eligible set, the drafted mid-session `ConfigurationError` becomes **unreachable** and
   is deleted outright rather than guarded, so `allocate_budget()` gains no raising path that could
   kill the PROCESSOR thread.
2. **F14's mailbox is an implementation direction, not permission to add a thread or a second
   broker-I/O owner.** The F1 four-thread contract is absolute regardless of how the hand-off is
   carried.

*F6 specified as capacity-driven, not score-driven*

Redistribution reads **candidate capacity and configured weights only**, never a `PriorityScore` —
coupling it to individual ranking would collapse the Budget Allocator / Depth Allocator separation.
Both worked examples in §13.4 now spend the full budget (Example A: NIFTY 15 / SENSEX 0; Example B:
NIFTY 5 / SENSEX 10), superseding the drafts' three mutually inconsistent answers for identical inputs.

*F9 kept as a measurement, with a specification*

§20.1 defines the probe: all four transitions (`5->50`, `50->5`, `50->50`, `5->5`) and a seven-item
evidence checklist — whether a bare re-subscribe changes depth, whether unsubscribe is required,
whether unsubscribe exists at all through the current OpenAlgo/FYERS path, transient subscription loss,
whether a transition consumes an extra premium slot, behaviour at the 15-symbol ceiling, and reconnect
behaviour afterwards. Deliverable is a dated evidence document under `Documents/patches/`, held to the
standard of `tbt_concurrency_reconciliation_20260714.md`. **The Broker Adapter is written after that
document exists, not before** — this is the same class of assumption that produced the 250-symbol
error, and it is not to be guessed twice.

*Also recorded*

- §21 gains **D-9** (the recorder's `_subscriptions` key encodes depth via `wire_symbol()`'s `:50`
  suffix, so "the same leg at a different depth" is inexpressible — closed by F10) and **D-10** (the
  drafted `min_per_underlying` would starve the premium budget — closed by the §13.2 scoping).
- §22 phase table reworked: a per-phase **Implements** column, and an explicit ordering constraint that
  **F7 must complete before the Broker Adapter is written**, which must precede F8 integration.
- §22.1 is the new **F0 approval gate** — eight items ticked, one open: user approval of F1 scope.
- §23 expanded from three lines to a per-phase F1-F10 progress list.

**Verification.** No code changed, so no test run was performed or claimed. Sweep of
`Plan_002_market_depth_framework_implementation.md` for open-fork language ("Unsettled", "Open
semantics", "OPEN FORKS", "decisions required", "See fork Fn") returns nothing; the nine surviving
`fork Fn` references were reworded to name the section that settles each.

**Not done / deferred.**
- **Phase F1 is not started.** Explicitly withheld pending approval of the F0 gate.
- **F9 is undecided by design** until the phase-F7 probe produces evidence.
- **F14 is provisional** until the phase-F8 checklist in §20.2 is satisfied against the real FEED loop.
- Plan_001 **Decision 18** remains open; it closes in Plan_002 phase F10.

## 2026-08-25 — Plan_002 opened: generic market-depth framework, planning cycle only (no code)

**Why.** Plan_001 decisions 16 and 17 made the hybrid the design (near-ATM legs at 50-level within
`tbt_budget = 15`, the rest at 5-level) and required a broker-capability layer so the engine stays
broker-agnostic. Neither exists. Plan_002 is the plan for that work, and it is the only one — the same
one-plan-one-location rule Plan_001 follows.

**What.** Documentation only. **No code was written; `market_depth_framework/` does not exist.**

- `plans/Plan_002_market_depth_framework_implementation.md` — new, 23 sections: scope boundary against
  Plan_001, an authority ranking for the four Qwen draft documents, the two decided forks, the
  corrected concurrency contract and pipeline, the subscription state model, nine component contracts,
  reconciliation/allocation/window semantics, config surface, testing architecture, integration plan,
  fourteen forks (two closed, twelve open with recommendations), eight source-document discrepancies,
  and an eleven-phase sequence F0-F10.
- `plans/Plan_001_market_depth_recorder_implementation.md` — cross-reference to the successor plan
  added to the decisions block; decision 18 (perf/RSS at true scale) is carried to Plan_002 phase F10.

**Decisions recorded (user, 2026-08-25; not to be reopened).**
- **F1 — there is no SUBSCRIPTION thread.** The recorder keeps exactly four worker threads (FEED, RAW
  WRITER, PROCESSOR, DB WRITER) and the framework is synchronous and threadless. `SubscriptionManager`
  is a pure component called on PROCESSOR; broker I/O stays on FEED. This supersedes the Qwen drafts'
  §0.1 and §6.7, which mandated a fifth thread.
- **F2 — permanent standard-depth baseline plus mutable premium overlay.** BASELINE MONOTONICITY (an
  eligible leg stays subscribed until graceful shutdown) and PREMIUM OVERLAY MUTABILITY (50-level
  assignment may be promoted, demoted, or reassigned within `tbt_budget`) replace the ambiguous
  "`_subscriptions` never-shrink". A demotion is a depth transition 50 -> 5, never an unsubscribe. An
  eight-row transition table is binding.

**Findings worth carrying (not previously written down).**
- The Qwen Budget Allocator worked example gives three different answers for the same inputs (its own
  split arithmetic yields NIFTY 9 / SENSEX 6, its prose says 9/5, and §0.2 says 10/5).
- The same example allocates 2 of the 15 scarce premium slots to SENSEX, which trades on BFO and can
  never receive 50-level depth. Premium eligibility belongs in the capability layer (fork F13).
- The recorder has **no unsubscribe path at all** — `websocket_client.py` never sends one. Whether a
  depth transition needs unsubscribe-then-subscribe or is a single re-subscribe is therefore unverified
  broker behaviour, and is scheduled as a live probe (phase F7) rather than assumed (fork F9).
- `_subscriptions` is keyed by wire symbol, and `wire_symbol()` encodes depth in the key (`:50`), so
  "the same leg at a different depth" is inexpressible today. Re-keying by leg identity is required
  (fork F10).

**Deferred.** Everything. Twelve forks (F3-F14) need decisions before phase F1 begins, and no
implementation phase starts until its scope is approved.

## 2026-08-25 — Repo-wide doc-accuracy sweep: the disproven FYERS TBT model marked superseded everywhere (no behavior change)

**Why.** A code-vs-plan audit ("has all the phases of Plan_001 completed? check with the code base, not
just the plan doc") confirmed every phase P0-P10 has real backing code, but found the **disproven** FYERS
TBT capacity model still stated as live fact in many places. The false model is *"5 Market-Depth symbols
per **channel** x 50 channels = ceiling 250"*. The true, FROZEN model (official FYERS TBT docs +
single-connection probe + multi-connection probe + a re-read of both live raws) is **5 symbols per
_connection_**, **3 connections per app per user**, **50 channels per connection that are a pause/resume
grouping carrying no capacity** -> **`tbt_budget = 15` (3 x 5)**.

The gap matters: the stale docs promise a ceiling roughly **16x** too large. P10 is titled "Full-chain
50-level" and fully ticked, so a reader would conclude the recorder captures the whole NIFTY chain at
50-level. It does not - it subscribes ~82 legs at `:50` and only ~5 ever stream concurrently (~6% of the
chain). SENSEX is unaffected (BFO -> 5-level, whole chain streams). Left unmarked, these documents would
have mis-anchored the framework design whose entire reason to exist is the hybrid the corrected ceiling
forces.

**What.** Documentation, comments, and one log-message string. **No logic, no constants, no config, and no
behavior changed anywhere.** P0-P10 behavior is untouched; the test suite is green at the same count.

*Sources of truth and plan*
- `market_depth_recorder_design.md` (spec, source of truth) - depth-level reality note rewritten to the
  frozen per-connection model, `tbt_budget = 15`, the hybrid as the design, and the broker-capability
  framing that keeps the engine broker-agnostic.
- `plans/Plan_001_market_depth_recorder_implementation.md` - `PHASE OBJECTIVE NOT DELIVERED` banner on the
  P10 heading; `-> SUPERSEDED (P10-F)` markers on D1, D2, the P10-A section, and A1. `SUPERSEDED` count
  7 -> 12; both remaining bare "250" assertions (lines 1448, 1493) now sit under a banner with a marker
  immediately following.
- `PROJECT_NOTES.md` - P9 headline finding and the P10-A summary corrected.

*Living architecture and operator docs*
- `Documents/ARCHITECTURE.md` - new FROZEN "Depth-capacity reality" block in the phase history, and a
  caveat on the perf targets recording that `cycle_ms_p50 ~ 22 ms` / `< 500 MB` were **not** measured at
  "full 80x50-level" (real load: <=5 NFO @50 + ~120 SENSEX @5) and remain unvalidated at the hybrid's
  profile.
- `Documents/SETUP.md` - the operator precondition no longer claims the patch enables a full 50-level
  chain; states the ~15-leg reality, why the patch is still worth applying, and what remains until the
  allocator lands.
- `Documents/operator_notes.md` - same correction in the operator-precautions list.
- `Documents/LIVE_RUN.md` - markers on the P9 headline finding and on the **E2** result (the "80 legs /
  16 channels / no global cap" pass was a measurement artifact; E2 did not actually pass).
- `Documents/phase_10E_notes.md` - markers on the section-1 objectives and on "D2 holds".

*Patches folder (`Documents/patches/`)*
- `OPENALGO_PATCH.md` - status line corrected (the "live-validated" claim was the artifact); top banner
  strengthened with the full evidence chain and the real ceiling; `-> SUPERSEDED` markers added to section 1
  (per-channel inference), section 2 (the unreachable 250 bound), section 3 (the pro/cons table, which now
  carries both "as costed" and "true" ceiling columns - the verdict is unchanged, since the correction
  lowers options A and B equally), and section 5 (the channel-distribution check passes and proves nothing;
  the meaningful check counts legs *streaming* per second, not subscribes - exactly how the P10-E artifact
  arose).
- `Phase9_notes.md` - section-3 banner strengthened; markers on the per-channel inference (the root of the
  mistake), the design decision, "recorder needs no depth-code change", "still to verify live" (now
  RESOLVED), and the platform-code reading (per-channel batch subscribe is message *coalescing*, not
  capacity - misreading it was part of the original misdiagnosis).
- `openalgo_fyers_tbt_channels.patch` - **regenerated** (88 -> 116 lines) so the reference diff matches the
  corrected source. Verified with `git apply --check --reverse` against the working tree.
- `tbt_concurrency_reconciliation_20260714.md` - unchanged; it is the canonical corrected evidence.
- `tbt_probe_20260714.json`, `tbt_multiconn_20260714.json` - **deliberately untouched**: raw measurement
  artifacts are evidence and must not be edited.

*Stale second copy of the plan removed*
- `Documents/Complete_Project_Plan_refer-market-depth-recorder-design-md-an-peppy-dolphin.md` - was a
  **1,556-line pre-P10-F snapshot of the plan** with **zero** supersession markers, asserting the 250
  ceiling as fact. Replaced its body with a **pointer stub** to
  `plans/Plan_001_market_depth_recorder_implementation.md`, matching what was already done to
  `~/.claude/plans/refer-market-depth-recorder-design-md-an-peppy-dolphin.md`. The stub records why the copy
  was dangerous rather than merely redundant, and links the corrected sources. One plan, one location.

*Code comments (recorder)*
- `eod_report.py` - the `_CYCLE_MS_TARGET` rationale comment claimed the 30 ms figure was measured "at the
  real full 80x50-level NIFTY scale". Corrected: that scale is unreachable on FYERS, the measurement was
  <=5 NFO @50 + ~120 SENSEX @5, and the target is unvalidated at the hybrid's profile. Threshold value
  unchanged at 30.0.

*Platform code (the existing P10-A scope exception, still uncommitted)*
- `broker/fyers/streaming/fyers_websocket_adapter.py` - three text corrections, no logic change:
  the class-constant comment block (rewritten to the per-connection model with a dated CORRECTION note and
  an explicit "these two constants must not be multiplied into a budget"); the `_assign_tbt_channel`
  docstring (records that the `None` return is effectively unreachable and the loop bounds are not a symbol
  budget); and the call-site comment. The operator-facing ERROR message was reworded from asserting
  "50 channels x 5 = 250 symbols" to naming it a channel-bookkeeping limit and pointing at the real
  per-connection cap. `TBT_SYMBOLS_PER_CHANNEL = 5`, `TBT_MAX_CHANNELS = 50`, and every code path are
  unchanged.

**Verification.**
- `pytest market_depth_recorder/tests/ -q` (run from `strategies/SS_Projects` with `PYTHONPATH` set to that
  directory, which the package imports require) -> **267 passed**, same as before the sweep.
- `python -m py_compile` on `eod_report.py` and `broker/fyers/streaming/fyers_websocket_adapter.py` -> OK.
- `git apply --check --reverse Documents/patches/openalgo_fyers_tbt_channels.patch` -> clean, confirming the
  regenerated diff matches the working tree.
- Repo-wide sweep: every file still containing old-model phrasing ("per channel", "5x50", "ceiling 250",
  "symbols/channel", "no hybrid", "full-chain", "80x50") was re-checked to confirm it also carries
  correction markers. All do. The two remaining zero-marker hits are false positives: "full-chain Level-2"
  in `Documents/qwen/prompt_generic_market_depth_framework.md` (a generic capability phrase, not a capacity
  claim) and the message-coalescing comments in `broker/fyers/streaming/fyers_tbt_websocket.py` ("one JSON
  per channel" - batching, not capacity). `Documents/archive/**` was excluded by design.

**Not done / deferred.**
- **The `250` bound in `_assign_tbt_channel` was deliberately NOT corrected to 15.** That is a *behavior*
  change to platform code, outside a doc-accuracy sweep, and the wrong home for the fix: the budget belongs
  in the broker-capability layer the framework defines, so the engine stays broker-agnostic. It is harmless
  meanwhile - unreachable, because FYERS refuses the 6th symbol on a connection first.
- **The hybrid itself is still not built** (near-ATM @50 within `tbt_budget = 15`, rest @5). It requires new
  subscription logic - a per-leg depth decision and the ability to demote 50->5 - which conflicts with the
  recorder's current never-shrink `_subscriptions` invariant. Deferred to the framework effort.
- **Perf targets are unvalidated** at the hybrid's real load profile and must be re-measured once the
  allocator lands; this is now recorded in `ARCHITECTURE.md` and `eod_report.py` rather than implied away.
- **Decision #18 remains open**; not touched by this sweep.

## 2026-08-25 — P4b checklist reconciled; P0–P10 confirmed complete (no code change)

**Why.** A phase-state audit against `plans/Plan_001_market_depth_recorder_implementation.md` found P4b's
B1/B2/B3 still unticked, while the same phase's B4 (tests), B5 (docs) and B6 (completion audit) were
signed off on 2026-07-04 and `metrics/rolling.py` + `metrics/aggregate.py` existed in the tree. The
question was whether this was missing work or a bookkeeping omission.

**What.** Bookkeeping omission — verified, then ticked. **No implementation code was changed**; the
working tree carried no modifications to engine code at any point in this audit.
- **B1** verified: `metrics/rolling.py` binds all thirteen §3.4.3 rolling specs plus `ofi_instant` /
  `liquidity_delta_instant`, both `None` on the boundary second.
- **B2** verified: `metrics/aggregate.py` binds the seven §3.4.4 specs incl. `regime`/`pinning_score`,
  with `compute_underlying()` doing K_ATM + SMALL/MEDIUM/LARGE grouping from config radii.
- **B3** verified: `processor.py` back-fills `ofi` (line 382), emits both new envelopes (lines 286/290),
  and applies the degraded heavy-skip against `rolling.HEAVY_METRICS` (line 495).
- **P0-J6** stale gate marker ("awaiting approval before P1") reconciled — approval is evidenced by
  P1–P10 all being complete.

**Verification.** `pytest market_depth_recorder/tests/ -q` → **267 passed** in 133s (no live feed);
`python -m market_depth_recorder --validate-config --config market_depth_recorder/config.yaml` → **exit 0**
(`config_hash sha256:8a48bcdd…`, transport `raw`); `compileall` on `metrics/` + `processor.py` → clean;
genericization grep → clean (sole `NIFTY` hit in engine code is a non-functional comment,
`processor.py:144`); no-asyncio grep → clean; `openalgo==2.0.2` pin intact; feed tee still two independent
puts (`websocket_client.py:447` proc / `:454` raw-with-timeout, raw shedding last).

**Affected files.** `plans/Plan_001_market_depth_recorder_implementation.md` (4 checkboxes + a dated P4b
reconciliation note) and `Documents/CHANGELOG.md` (this entry) — documentation only.
`Documents/ARCHITECTURE.md` needed **no** change: its "Built state (P4a + P4b)" section already described
all four §4.1 tables and the per-strike → rolling → aggregate order correctly, i.e. the implemented-state
docs were right all along and only the progress checkboxes had drifted.

**Nuance recorded, deliberately not "fixed".** Decision 39's P4a-era parenthetical lists "wall-score
median, quote stability" as degraded-skippable; the implemented and documented heavy set is rolling-only
(`Documents/processor.md:87`, `Documents/metrics.md:82`). Those two are cheap per-strike bodies over a
bounded deque. Docs match code — the planning text is the stale side. Changing behavior in an audited
phase was out of scope for a reconciliation.

**Deferred / open.** The only remaining unticked item in Plan_001 is the **generic framework**
(`market_depth_framework/`), which the plan explicitly records as *not* covered by P0–P10 and as
requiring a fresh scope-clarification → "let's write the plan" cycle. P0–P10 of the recorder are complete.

## 2026-07-14 — FYERS TBT budget = 15 confirmed; Jul-07/Jul-14 reconciled; protocol layer frozen (P10-F)

**Why.** Two questions remained before locking the architecture: (a) do FYERS' 3 connections × 5 symbols
actually combine to **15** concurrent 50-level symbols, and (b) why did the P10-E (2026-07-07) run appear to
show a full 80-leg 50-level chain when 2026-07-14 showed only 5? Both are now resolved from evidence.

**What.**
- New **multi-connection probe** `tools/fyers/tbt_multiconn_probe.py` + shared `tools/fyers/_tbt_common.py`
  (factored out of `tbt_channel_probe.py`). Drives 3 independent `FyersTbtWebSocket` connections
  concurrently. Result (evidence `Documents/patches/tbt_multiconn_20260714.json`): **C1** 5/5, **C3**
  **15/15 distinct legs streamed concurrently** (each conn 5/5, sustained increments, 0 drops), **C4** 4th
  connection **refused** (`429`). ⇒ **`tbt_budget = 15` (3 × 5)**; single-connection ceiling stays 5.
- **Reconciliation** (`Documents/patches/tbt_concurrency_reconciliation_20260714.md`, **canonical**): a
  per-second re-read of both raws shows **max 5 concurrent** NFO legs on **both** days (Jul-07: 9 distinct
  all session, 0 seconds >5; Jul-14: 5). The `git pull --rebase` between runs left the **TBT streaming code
  byte-identical** (`fyers_tbt_websocket.py`/`fyers_websocket_adapter.py`/`msg_pb2.py` unchanged; changes were
  REST/proxy only). Hypotheses: FYERS-change ✗, code-change ✗, **interpretation-artifact ✓** — P10-E read the
  80-leg *subscription* + genuine 50-*level* depth on ≤5 legs as "80 legs *streaming*."
- **P10-E cascade corrected** (superseded interpretation marked, original preserved; each doc summarizes +
  points to the canonical reconciliation): E2 "no cap/patch works" → artifact; E4 perf/RSS "at full scale"
  → was ≤5 NFO@50 + 120 SENSEX@5, **true 80×50 perf still untested**; E9 NIFTY coverage → ≤5 legs; **D2
  "no hybrid" reopened** → hybrid (near-ATM @50 + rest @5) or multi-connection, budget 15.
- Docs: `OPENALGO_PATCH.md §8.4` (RESOLVED), `Phase9_notes.md` (P10-F callout), `CLAUDE.md` "Depth Reality"
  (budget 15, allocator consumes one logical budget), plan doc P10-E section, `phase_10E_notes.md`/`LIVE_RUN.md`
  (correction banners), `tools/README.md` + `tools/fyers/README.md`. Separate OpenAlgo issue recorded for the
  `_run_websocket` retry-on-return storm (`openalgo_tbt_reconnect_storm_issue.md`) — not a protocol finding.

**Design impact.** Protocol layer **FROZEN unless new external evidence emerges** — do not revisit the FYERS
TBT assumptions without new evidence. FYERS capability = 5 syms/conn, 3 conns, `tbt_budget = 15`, channels =
pause/resume grouping. **`tbt_budget = 15` is a confirmed FYERS broker _capability_, not an architectural
constant** — the allocator consumes a logical TBT Budget exposed by the broker-capability layer; another
broker may expose a different budget with no architectural change. Next effort moves entirely to the generic
allocation framework (Broker Capabilities → Window Manager → TBT Allocator → Allocation Policy → Subscription
Manager), consuming that budget as one broker config. **Open (real):** perf/RSS at true 15 × 50-level +
hybrid remainder — never yet load-tested.

**Affected files.** `tools/fyers/tbt_multiconn_probe.py` (new), `tools/fyers/_tbt_common.py` (new),
`tools/fyers/tbt_channel_probe.py` (refactor to shared module), `Documents/patches/tbt_multiconn_20260714.json`
(new evidence), `Documents/patches/tbt_concurrency_reconciliation_20260714.md` (new, canonical),
`Documents/patches/openalgo_tbt_reconnect_storm_issue.md` (new), `Documents/patches/OPENALGO_PATCH.md`,
`Documents/patches/Phase9_notes.md`, `CLAUDE.md`, `tools/README.md`, `tools/fyers/README.md`,
`Documents/phase_10E_notes.md`, `Documents/LIVE_RUN.md`, plan doc.

## 2026-07-14 — FYERS TBT 50-level ceiling: channel-spread patch disproven (P10-E)

**Why.** Live validation (OpenAlgo's own feed stopped) of the P10-A channel-spread patch, plus the official
FYERS TBT WebSocket docs, **independently disprove** the "5 symbols/channel × 50 = 250" premise the patch was
built on. FYERS caps 50-level Market Depth at **5 symbols per _connection_** (docs: 3 connections/app/user, 5
symbols/connection, 50 channels/connection); **channels are a pause/resume logical grouping, not extra
capacity.** In the 2026-07-14 recorder run, of 40 NIFTY `:50` legs (spread across channels 1–8) **only 5
streamed** (channel 1's five); SENSEX/BFO (5-level HSM) ran all 120 legs normally.

**What.**
- New diagnostics tool **`tools/fyers/tbt_channel_probe.py`** (+ `tools/fyers/README.md`) — drives
  `FyersTbtWebSocket` directly, fresh connection per test, capturing subscribe requests, FYERS ACKs/errors,
  and per-symbol packet counts. Probe matrix: T1 ch1 ✓, T2 ch2-alone ✓, **T2p int-channel silent** (resume
  needs *string* ids), **T3 ch1+ch2 → only 5 stream + "exceeds limit: 5"** (channels share one 5-symbol
  budget). Read-only w.r.t. platform code (documented scope exception, like the patch).
- Docs corrected to the experimentally + officially validated behavior: `Documents/patches/OPENALGO_PATCH.md`
  (new authoritative §8; annotated §2/§6), `Documents/patches/Phase9_notes.md` (dated P10-E callouts),
  `CLAUDE.md` ("Depth Reality"), `tools/README.md` (index). Frozen evidence:
  `Documents/patches/tbt_probe_20260714.json`.

**Design impact.** Full NIFTY 50-level chain is **not** achievable on one connection. The channel-spread
patch is a no-op for the ceiling (harmless; kept for now). Path forward — **hybrid** (5 near-ATM @50 + rest
@5) or **multi-connection** (≤ 3×5; unconfirmed whether budgets combine) — **decision deferred**, to begin as
its own scoped effort. Open question if multi-connection is pursued: whether 3 conns × 5 syms truly yields 15
concurrent depth symbols (extend the probe to a 2-/3-connection test before committing).

**Affected files.** `market_depth_recorder/tools/fyers/tbt_channel_probe.py` (new), `tools/fyers/README.md`
(new), `tools/README.md`, `Documents/patches/OPENALGO_PATCH.md`, `Documents/patches/Phase9_notes.md`,
`Documents/patches/tbt_probe_20260714.json` (new evidence), `CLAUDE.md`.

## 2026-07-13 — Default write backend flipped to `arrow`; `executemany` deprecated; PERFORMANCE.md

**Why.** The milestone review after Phase P-C confirmed the two gating conditions the user set for the
flip are both met: chunked-Arrow **preserves (in fact improves) throughput** *and* **bounds peak RSS**
(800 MB on the representative ~100-min dataset — suitable for the 8 GB target for current workloads; a true
full-session replay is not yet measured on this hardware), with **determinism bit-exact** vs the canonical
reference. **Offline replay on the representative ~100-min dataset improved from ~3h52m to 244.8 s (~57×)**
(671,481-packet / 5,951,233-row dataset).

**What.**
- `config.yaml`: `analytics_db.write_backend` default flipped **`executemany` → `arrow`**.
- **`executemany` is now DEPRECATED** — retained one release cycle as a fallback, selectable via
  `write_backend: executemany` or the `--backend executemany` CLI override. Marked deprecated in
  `config.yaml`, `ARCHITECTURE.md`, and `database_writer.md`.
- Precise wording pass: docs/code that said writer memory is "independent of replay length" now read
  "**bounded by the configured batch size rather than growing with replay duration**" (DuckDB's own
  working set can still vary — the more accurate engineering statement).
- New **`Documents/PERFORMANCE.md`** — the permanent engineering report of the whole optimization journey
  (problem, the measurement turning point that overturned the cProfile mis-diagnosis, every optimization +
  its measured contribution, the `_slope`/reference investigation, Arrow + chunked-Arrow redesigns, final
  benchmark tables, lessons learned, deferred framework work).

**Determinism / tests.** No logic change beyond the default; full suite green. Determinism unchanged
(default `arrow` now takes the already-bit-exact path).

**Affected files.** `config.yaml`, `database_writer.py` (comment), `Documents/ARCHITECTURE.md`,
`Documents/database_writer.md`, `Documents/CHANGELOG.md`, new `Documents/PERFORMANCE.md`.

**Remaining (framework evolution, not blockers).** DuckDB-side `verify()` rewrite (fixes the O(rows)
Python-dict OOM); `atol + rtol` verification semantics; Phase 2 multi-process (deferred, unlikely needed
for current workloads); future incremental real-time rolling engine. Offline replay optimization is
**complete**.

## 2026-07-13 — Phase P-C: chunked-Arrow streaming writer (peak RSS 4× lower, bounded by batch size not duration)

**Why.** Arrow was correctness/perf-validated but its `finalize()` buffered the **whole session** in
`self._buffers` (5.95M row tuples) then pivoted the largest table ~3× at once → **~3.6 GB RSS on ~100-min
data**, projecting to ~20 GB full-day — over the 8 GB target machine. Root cause (measured): the long-lived
per-table buffers dominate RSS; the Arrow pivot only adds a transient peak on top.

**What.** Stream fixed-size batches **during `write()`** instead of buffering the whole session. New
config key **`analytics_db.write_batch_rows`** (default **100_000**; validated positive int ≤ 5_000_000,
fast-fail). The write path is now the single seam **`write → buffer → _flush → backend insert`**: `write()`
flushes a table when its buffer reaches `write_batch_rows`; `_flush(table)` is the **only** place batching
lives (boolify option rows, dispatch to the arrow/executemany insert per batch, advance
`rows_written`/`batches_written`); `finalize()` flushes the trailing partials then stamps + `CHECKPOINT`.
The replay engine and metrics are **completely unaware** of batching — the seam a future streaming/parallel
writer reuses. Also **hardened `close()`**: a mid-`finalize()` failure now discards the partial temp in the
`finally` (previously it orphaned a `.building_<pid>` — exactly how the stale orphan on disk was created).

**Benchmark (~100-min dataset, backend=arrow, one process per run for clean peak RSS):**

| batch | wall | finalize | peak RSS | batches |
|---|---|---|---|---|
| 5_000_000 (unchunked control) | 300.8 s | 86.4 s | **3190 MB** | 4 |
| 250_000 | 247.1 s | 4.1 s | 1278 MB | 26 |
| **100_000 (default)** | **244.8 s** | 1.2 s | **800 MB** | 62 |
| 50_000 | 249.8 s | 0.6 s | 932 MB | 121 |

→ **100k is empirically optimal: 4× lower peak RSS (3190→800 MB) AND fastest wall** (finalize collapses
86→1.2 s as the write overlaps replay). Peak RSS floor is now DuckDB's own working set (`memory_limit`
PRAGMA), not the Python buffer → **writer memory is bounded by the configured batch size rather than growing
with replay duration** (validated on the representative ~100-min dataset; suitable for the 8 GB target for
current workloads — DuckDB's own working set can still vary, and a full session is not yet measured). Default kept at 100k
(data-backed, not assumed).

**Determinism.** Chunked-100k build (62 batches) vs the canonical reference (built pre-chunking, buffer-all)
→ **bit-exact, 0 divergent rows** across all 4 tables (5,951,233 rows) via the memory-safe DuckDB-side
`EXCEPT`. Chunking changes only *when* rows insert, never the data.

**Failure semantics (verified, all-or-nothing canonical).** Injection tests for mid-batch, between-batches,
final-partial-batch, and **after `CHECKPOINT` before rename** all confirm the canonical store is either
complete or absent, no partial output. **267 tests pass.** FD audit: FD-neutral (same single `with`-managed
connection; per-batch Arrow view `unregister`ed in `finally`), cleanup strictly improved.

**Affected files.** `database_writer.py` (`write`/`_flush`/`finalize`/`close`/ctor + `batches_written`),
`config.py` (validation), `config.yaml` (`write_batch_rows`), `tests/conftest.py`, `tests/test_database_writer.py`
(chunk parity + 4 failure-injection tests), `tests/test_replay.py` (chunked==unchunked). Docs:
`ARCHITECTURE.md`, `Documents/database_writer.md`.

**Remaining.** Milestone review → decision on flipping the config default to `arrow` (RSS now bounded) →
final performance report. Then offline optimization is complete; only the separate framework work
(DuckDB-side `verify()` + tolerance) remains.

## 2026-07-13 — Golden reference regenerated from current code; `_slope` validated superior; `--backend` override; verify() OOM found

**Why.** Validating the Arrow write path against the existing 652 MB `data/2026-07-07` analytics store
surfaced a mismatch, which investigation resolved into three benign, fully-understood facts — none an Arrow
defect — making that store **obsolete** rather than a valid reference:

1. **`_slope` (Phase-1b) is numerically *superior*, not merely equivalent.** A tolerance-aware DuckDB-side
   diff (matching `--verify`'s `atol=1e-9`) found the *only* divergence was **45 / 4,440,585**
   `strike_window_metrics.book_pressure_slope` rows at max **abs 1.42e-9 / rel 1.01e-12** (|slope| up to
   ~1.15e6). High-precision adjudication — recomputing each of the 45 slopes with numpy pairwise sums, the
   pure-Python sequential closed form, and an **exact `fractions.Fraction`** reference on the exact float
   inputs (captured via a wrapped-`_window_rows` replay, 45/45, `eps=1e-8`) — showed pure-Python is closer
   to exact in **41/45** rows, mean abs err **2.51e-10 vs 1.07e-9** (~4×), max rel err **8.90e-14 vs
   9.24e-13** (~10×). So the old store (numpy) was the *less* accurate artifact. `_slope` kept as-is.
2. **The provenance `config_hash` differs for a capture-only reason.** Old store `fb97f393` (config commit
   `3b6ceb5`) vs current `8a48bcdd` (`212fb90`): the only hashed-section change is NIFTY DSM
   **subscription-window** knobs (`initial_window` 1000→500, `expansion_threshold` 200→100, `expansion_step`
   300→100). Those govern *which strikes get subscribed during live capture* — **zero** effect on any
   replayed value (the raw log already holds the ticks). `compute_config_hash` hashes `underlyings`
   wholesale, so these live-only knobs flip the stamp regardless. This (not `write_backend`, which is **not**
   hashed) is why the earlier `--verify` aborted on config_hash.
3. **Arrow is value-preserving** (write path only; bit-identical to `executemany`, proven by slice A/B).

**What.** (a) **Archived** the old store → `data/2026-07-07/legacy_pre_p1b/…pre-p1b.legacy.duckdb` with a
provenance `README.md`. (b) Added a per-run **`--backend {executemany,arrow}`** CLI override (threaded
through `replay_file`/`catchup` via a new `write_backend` param on the writer seam) so a canonical rebuild
can pick Arrow **without** editing the committed config default — keeping the default `executemany` until
the flip is approved. (c) **Rebuilt the canonical reference** from current code via the canonical replay
path (`--replay … --backend arrow`, ~6m14s): `data/2026-07-07/market_depth_analytics_20260707.duckdb`,
**607.3 MB**, `config_hash=sha256:8a48bcdd…`, rows spot 11,433 · option 1,480,195 · window 4,440,585 · agg
19,020. (d) **Determinism re-verified bit-exact**: a second `--backend arrow` replay diffed against the new
reference via a memory-safe DuckDB-side symmetric `EXCEPT` → **0 divergent rows** across all 4 tables.

**⚠ New finding — `verify()` is not memory-safe at scale.** The canonical `--verify` **OOM'd**
(`MemoryError` in `replay._read_table`, `replay.py:407`): it materializes **both** the built and reference
tables into nested Python dicts (4.44M rows × 2 × ~30 cols) before comparing — unbounded O(rows) memory. It
cannot run on the ~100-min dataset here, and would fail hard on the 8 GB target machine / full-day data. The
determinism check above used a **DuckDB-side** diff instead (ATTACH both + per-table SQL), which is bounded
and fast. **Recommended (separate framework proposal, deferred): reimplement `verify()`'s per-table
comparison DuckDB-side** — this simultaneously fixes the OOM *and* lets the tolerance become numpy-`isclose`
style `abs(a-b) <= atol + rtol*|b|` (the pure-absolute `_VERIFY_ATOL` mis-scales for unbounded quantities
like slopes — the mechanism behind the 45-row finding). Per user direction, the `_values_equal`/verify
framework change is **not** bundled into this Arrow work.

**Affected files.** `__main__.py` (`--backend` arg + guard + wiring), `replay.py` (`write_backend` param on
`replay_file`/`catchup`), `tests/test_replay.py` (`write_backend` override parity test). Data:
`data/2026-07-07/market_depth_analytics_20260707.duckdb` (regenerated), `…/legacy_pre_p1b/` (archived old
store + README).

**Default NOT flipped (deliberate sequencing).** `config.yaml` `write_backend` **stays `executemany`**.
Arrow is fully validated for correctness + performance, but its `finalize()` buffers all rows → ~3.6 GB RSS
on ~100-min data, which won't scale to a full session on the 8 GB target machine. Per user direction the
default flip is **gated on chunked-Arrow** bounding peak RSS first. Arrow remains selectable now via the
config key or `--backend`. Suite green (**259 passed**).

**Remaining (priority order).** (1) **Chunked-Arrow `finalize()`** — stream fixed-size Arrow batches into
DuckDB instead of buffering all rows; keep throughput, bound peak RSS for the 8 GB machine. **Highest-
priority engineering task before the offline pipeline is production-ready.** On pass (determinism + memory),
flip the default to `arrow`. (2) Separate framework proposal: DuckDB-side, tolerance-scaled `verify()`
(fixes the OOM + the mis-scaled absolute tolerance in one change). (3) Later: remove the legacy `executemany`
path after one clean production cycle on Arrow.

## 2026-07-13 — Write-path pivot: Arrow columnar bulk-load backend for DuckDB finalize (30× replay)

**Why.** The offline replay's real bottleneck is the **DuckDB write**, not metric compute (Phase 0
mis-diagnosed it via cProfile — see the 1b entry's critical-finding note). An un-profiled phase-breakdown of
the fixed slice: `finalize()` **206.9 s** vs all metric compute **4.3 s** (~98 % / ~2 %). Root cause:
`finalize()` did row-by-row `con.executemany("INSERT … VALUES (?,…)", rows)` — a pathological anti-pattern
for DuckDB's vectorized columnar engine. It scales linearly and reproduces the user's original 3h52m
full-day run (206.9 s × 5.95M/74k ≈ 4.4 h).

**What.** Added a config-switchable write backend `analytics_db.write_backend` (`executemany` | `arrow`).
The `arrow` path pivots each table's buffered row tuples into per-column arrays, builds one
`pyarrow.Table`, and `INSERT … SELECT`s it in a single vectorized pass (DuckDB casts each column to the
destination type → bit-identical output). Default stays `executemany` until the full-day `--verify`
confirms `arrow`; `arrow` requires `pyarrow` (now pinned in `requirements.txt`; fast-fail at `_open()` if
selected-but-missing). Legacy path retained for now.

**Validation (A/B, fixed slice, full metric set, both `--verify` clean, exact 73,952-row parity):**

| backend | wall | finalize | peak RSS |
|---|---|---|---|
| executemany | 211.4 s | 206.9 s | 192.5 MB |
| **arrow** | **6.96 s** | **0.77 s** | 258.1 MB |

→ **finalize 269.8×, total wall 30.4×** (the ~6 s read+compute loop is now the floor). Peak RSS +66 MB
(transient columnar copy — watch at full-day scale). Full-day projection: ~3h52m → **single-digit minutes**.

**Affected files.** `database_writer.py` (backend dispatch + `_insert_arrow`/`_insert_executemany` +
pyarrow fast-fail + constructor override), `config.py` (enum validation), `config.yaml` (`write_backend`),
`requirements.txt` (`pyarrow~=23.0.1`), `tests/conftest.py` (fixture key), `tests/test_replay.py`
(arrow-vs-executemany parity test). Suite: **257 passed**.

**Reprioritization (validated).** Arrow write path is the offline #1 lever. **Phase 1c/1a/1d deferred**
(optimize the ~2 % compute slice — not worth it offline). **Phase 2 (multi-process) deferred pending
evaluation after chunked Arrow** — on current measurements a single process rebuilds a full day in minutes,
so it is unlikely to be required for today's workloads, but the design remains available if future datasets
or workflows justify parallelism. Phase 1b retained (correct, verified, and the right work for
the future real-time path).

**Remaining.** (1) full-day `arrow` rebuild + `--verify` against a full-day reference + peak-RSS check;
(2) on pass, flip `config.yaml` default to `arrow`; (3) later, remove the legacy `executemany` path if it
no longer adds value.

## 2026-07-12 — Phase 1b: replay perf, NumPy→pure-Python (in progress, one hotspot per commit)

**Why.** Offline analytics replay took ~3h52m for a full day (single synchronous pass; cost is entirely
per-strike-per-second Python/NumPy metric compute, not the DuckDB write). Phase 0 established a fixed-slice
benchmark harness (`benchmark.py`), a slice reference, a measured baseline (wall 204.3 s), and a cProfile
hotspot ranking. Phase 1b converts the tiny-array NumPy bodies to pure Python, one hotspot per commit,
each gated by `--verify` zero-drift.

**Measurement methodology (user-approved).** Full-slice wall has ~±10 % run-to-run variance (~±20 s), which
swamps a single hotspot's ~2–5 s contribution — so per hotspot: (1) an **isolated microbenchmark** is the
primary gain signal, (2) `--verify` is the correctness gate, (3) the full-slice replay is used only as a
regression check + to measure the **cumulative** phase gain. A periodic full-replay re-profile keeps the
microbench honest — the profiler is the tie-breaker on the real workload.

**Hotspots landed.**
1. **`round_number_depth` (M18), `metrics/per_strike.py:_round_depth`** — vectorised
   `np.isclose(np.remainder(px, r), …)` mask + `qty[mask].sum()` → pure-Python loop reproducing numpy's
   default isclose tolerances exactly (`|rem| ≤ 1e-8`, or `|rem − r| ≤ 1e-8 + 1e-5·r`). Microbench (mult
   `(5,10)`): **33.7× @ n=5, 11.5× @ n=20, 5.0× @ n=50**. `--verify`: no drift. Commit `99b1302`.
2. **rolling window reduces, `metrics/rolling.py`** — `_slope` (closed-form exact `sum(x)`/`sum(x²)` +
   pure-Python y-sums), `_spread_stats` + `_wobi_stats` (shared `_mean_std_minmax()`: one-pass mean /
   population std / min / max); dropped the module's unused `import numpy as np`. (`_micro_price_rv` was
   already pure Python — its cost is series re-extraction, a 1c item.) Microbench: `_slope` 4.9–11.9×,
   `_spread_stats` 6.8–22.3×, `_wobi_stats` 7.3–14.8× (n=5/10/30); max abs diff vs numpy **2.2e-16**.
   `--verify`: no drift. **Cumulative slice wall 204.3 → 179.7 s** (CPU 148.3 → 125.7 s). Re-profile:
   `np.isclose` gone, `ufunc reduce` 2.81 → 1.18 s, `_var` 1.50 → 0.47 s. Commit `db55f31`.
3. **per-strike reduces, `metrics/per_strike.py`** — `_side_wall_score` (`np.argmax`/`np.delete`/`np.median`
   → pure Python: inline first-max argmax, comprehension delete+filter, sort-based median) and `_confidence`
   (`np.std` → `_pop_std()` population std). `_wall` (M20) argmax **kept numpy** — microbench showed the
   pure-Python loop is 2.5× slower on 50-level NIFTY books (~84% of load), so converting would regress.
   Microbench: `_side_wall_score` 3.3–16×, `_confidence` std 22–25×; max abs diff 0.0 / 2.2e-16. `--verify`:
   no drift. Re-profile: `_side_wall_score` dropped out of the top-18, `_var` calls 33577 → 17160 (remainder
   is `processor._wall`), cProfile compute 17.9 → 15.3 s (−2.6 s). Commit `b03e14d`. *(Full-slice wall was
   contention-noisy this session — 179.7/209.9/235.3 s across runs — so microbench + cProfile are the
   authoritative signals; a clean cumulative wall is taken at the 1b phase boundary.)*

4. **`processor.py:TickProcessor._wall`** — `np.concatenate` + `np.argmax` + `.mean()` + `.std()` over the
   combined book (≤100 levels) → pure-Python argmax + one-pass mean/std. **Net win at every size** (8.9× @ 10,
   2.84× @ 60, 1.81× @ 100) *because* it makes 4 numpy calls + an allocation (contrast the per-strike `_wall`,
   argmax-only, where numpy won). Outputs are exact array elements; mean/std only pick the boolean threshold —
   microbench: max abs diff 0.0, **0 flips / 40k**. `--verify`: no drift. Re-profile: `_var` gone from the
   top-16, `ufunc reduce` 0.97 → 0.85 s, cProfile compute 15.29 → **14.57 s**. Commit `b7c6343`.

**Cumulative so far (baseline → after hotspot 4), cProfile on the fixed slice (contention-independent
metric-compute measure):** **28.33 s → 14.57 s (−13.76 s, ~49 % of profiled compute eliminated, 1.94×)** —
28.33 (baseline) → 17.93 (1+2) → 15.29 (3) → 14.57 (4). The slice row count is fixed; this is pure compute
reduction. An authoritative wall/CPU number is deferred to the 1b phase boundary (after hotspot 5) on a
quiet machine.

5. **`snapshot._parse_side` — KEPT numpy (negative result).** Microbench: only 1.06× at 50 levels (NIFTY,
   the dominant load), and `np.argsort` (quicksort, unstable) vs Python stable `sorted` produced different
   tie-order on 40,458/50,000 duplicate-price cases — a divergence-from-reference risk for ~0.2 % overall
   gain. Per the stopping criterion, left as-is. No code change.

**Affected files.** `metrics/per_strike.py`, `metrics/rolling.py`, `processor.py` (+ dev-only `benchmark.py`
from Phase 0). Docs: this CHANGELOG + the peppy-dolphin plan doc.

**Phase 1b concluded** (hotspots 1–4 converted, 5 kept numpy).

### ⚠ Critical finding while measuring the 1b phase boundary — the real bottleneck is the DuckDB write

An **un-profiled** phase-breakdown of the fixed slice (201 s wall) shows metric compute (`emit_second`) is
only **4.3 s (~2 %)**; **`DuckDBAnalyticalWriter.finalize()` is 196.8 s (~98 %)**. Root cause: `finalize()`
(`database_writer.py:729`) uses `con.executemany("INSERT … VALUES (?,…)", rows)` — row-by-row parameterized
INSERT, a pathological anti-pattern for DuckDB's vectorized columnar engine. It scales linearly and
**explains the original 3h52m full-day run** (196.8 s × 5.95M/74k ≈ 4.4 h). Phase 0's "cost is in metric
compute, not the write" was a cProfile artifact (cProfile inflates the Python metric loop and under-weights
the single GIL-released `executemany` C-call). **Proven fix:** Arrow columnar bulk insert
(`pa.table(cols)` + `INSERT … SELECT * FROM arrow_tbl`) — **1.06 s vs 77.2 s, 72.6×**, exact row parity.
This becomes the #1 lever (offline); Phase 1c/1a/1d deferred, Phase 2 deferred pending evaluation after
chunked Arrow (unlikely required for today's workloads, but retained if future workloads justify it). **Implementation
pending user go-ahead** (see the peppy-dolphin plan's "CRITICAL FINDING" section).
Then cumulative full-slice benchmark + re-profile → 1c.

**Deferred (per-strike `.sum()` family).** The M5–M17 numpy `.sum()` reduces are left as numpy: the ratio
sums (raw_obi, stack ratios, OBI) are individually below the profile noise floor, and the absolute persisted
sums (`book_pressure`, `effective_depth`, magnitude ~1e6) carry an 8-way-vs-sequential summation-order risk
(~1e-8 abs) that could breach the 1e-9 verify gate. Revisit only if the profile elevates them.

## 2026-07-07 — P10-E: live validation (patched platform) + 4 bug fixes

**What / why.** Ran P10-E live against the channel-spread-patched OpenAlgo (fresh instance) with a
compressed session to exercise the real timer-based graceful teardown. **Result: PASS with two known
WARNs** (SENSEX 5-level BFO degrade §9; `cycle_ms` > 15 ms). Whole NIFTY chain now streams true TBT depth
(NFO `depth_levels` up to 47 across ~16 channels; no global FYERS cap); `actual_depth={NIFTY:50,SENSEX:5}`;
handles flat (no leak); graceful teardown → clean EOF → auto-reprocess → DuckDB (291 837 rows, 0 corrupt);
EOD report exit 0, no FAIL. Full results in `LIVE_RUN.md` §C (P10-E) and the detailed `phase_10E_notes.md`;
operator guide added in `operator_notes.md`. Four bugs the live full-depth data surfaced were fixed, plus a
perf micro-opt, an E4 target re-tune, and an E8 verify tolerance (regression tests added; suite **257 green**):

1. **regime `theta_pressure: 5.0e6` → PyYAML string** crashed the classifier mid-session (`float > str`)
   once full-depth NIFTY made NOP non-null. Fixed literal → `5000000.0` **and** added numeric validation
   of all regime thresholds in `config.py` (loud startup failure instead of a live crash).
2. **`crossed/zero market` logged at CRITICAL** per level/second (expiry-day flood) → **DEBUG** (rate is
   in the EOD report; data unchanged).
3. **`actual_depth` health map first-write-wins** (froze on an OTM strike, dropped BFO/SENSEX) → **max-seen
   with populated-level fallback** → correct `{NIFTY:50, SENSEX:5}`.
4. **`test_integration` hardcoded a past `SESSION_DATE`** (date-rollover emptied the inspected file) →
   `now_ist().date()`.

Plus three follow-through changes (user-directed):
5. **Perf micro-opt** — removed a redundant weighted_obi/book_pressure double-compute in `processor._core`
   (output-preserving; reuses the persisted per-strike values).
6. **E4 target re-tuned 15 → 30 ms** (`eod_report._CYCLE_MS_TARGET`): `cycle_ms_p50 ≈ 22 ms` is the honest
   full-50-level cost and keeps real-time pace (~45× headroom). Per-underlying `process` sharding is
   **rejected** (wrong lever — NIFTY ≈ 84 % of load in one shard); intra-underlying parallelism **deferred**.
7. **E8 `--verify-against-live` tolerance** — added `_LIVE_SUBSET_TOLERANCE_PCT = 2.0` in `replay.verify()`
   so the disposable live store's expected second-boundary divergence passes (real session: 0.88 % of rows,
   `VERIFY OK: 658/74697 rows differ`); the strict duckdb-vs-duckdb determinism gate stays zero-tolerance.

**Affected files.** `metrics/per_strike.py`, `websocket_client.py`, `processor.py`, `config.py`,
`config.yaml`, `eod_report.py`, `replay.py`; tests `test_metrics_per_strike.py`, `test_websocket_client.py`,
`test_config.py`, `test_integration.py`, `test_replay.py`, `test_eod_report.py`; docs
`Documents/{LIVE_RUN,CHANGELOG,phase_10E_notes,operator_notes}.md` + the plan doc.

**Remaining.** Intra-underlying parallelism for further `cycle_ms` headroom is **deferred** (not needed for
real-time pace today; per-underlying sharding is documented as a non-solution).

## 2026-07-06 — P10-D: docs reconciliation (5-per-channel TBT reality)

**What / why.** Brought every doc in line with the P9 finding and the P10 build. Recorded the **live-verified
FYERS TBT cap (5 symbols/channel; OpenAlgo pins channel `"1"`)** into the **authoritative design spec** §1
depth-reality note (spec wins), and mirrored it into `CLAUDE.md` "Depth Reality" and the `PROJECT_NOTES.md`
roadmap (P9 partial pass + P10-A..E). Filled `LIVE_RUN.md` §C with the P9 results and added the
channel-patch precondition to §A. `SETUP.md` gained the dated-storage layout, `--eod-report`/`--catchup`
usage, and the TBT-patch precondition. `ARCHITECTURE.md` gained the `eod_report.py` module entry and the
P8/P9/P10 built-state narrative (storage topology was added in P10-B). No code changes.

**Affected files.** `market_depth_recorder_design.md`, `CLAUDE.md`, `PROJECT_NOTES.md`, `Documents/{SETUP,
ARCHITECTURE,LIVE_RUN}.md`. All cite `Documents/patches/{OPENALGO_PATCH,Phase9_notes}.md`.

**Remaining.** **P10-E** — live validation next market session (apply patch + restart OpenAlgo → full NIFTY
50-level, global-cap check, authoritative perf/RSS, graceful teardown, EOD report on the session).

## 2026-07-06 — P10-C: EOD health & sanity-check report

**What / why.** New offline `eod_report.py` + `--eod-report [--date YYYY-MM-DD]` CLI that verifies a day's
captured artifacts and writes a dated PASS/WARN/FAIL report (markdown + JSON) into
`<dated-dir>/reports/eod_healthcheck_<date>.{md,json}`. It is the operator's automated "did the day capture
cleanly?" gate — it would have caught the P9 NIFTY-no-depth failure without a human noticing.

**Checks.** Tier 0 raw (HEADER/instruments/config_hash, EOF cleanliness, record count, timespan,
**per-underlying depth coverage → FAIL on 0 depth**, actual-vs-requested depth = §9 alarm, `feed_time`
coverage among TBT packets, per-level `orders`, crossed/locked share); Tier 1 live SQLite (tables +
**per-underlying option-row coverage**); Tier 2 DuckDB (tables populated + `recorder_meta` stamps, SKIP if
unbuilt); ops `health.json` (drops→FAIL, cycle<15 ms, rss<500, degraded). Worst-wins overall; **exit 0 clean
/ 1 on any FAIL**. Report-only thresholds are fixed spec (§5.1) targets, not config keys.

**First real run** on the P9 capture: **FAIL** — correctly flagged `raw.depth_coverage.NIFTY` +
`live.option_rows.NIFTY`, plus WARNs on missing EOF, SENSEX 5-level degrade, and `cycle_ms_max=25.96 > 15`.

**Affected files.** New `eod_report.py`, `tests/test_eod_report.py` (15), `Documents/eod_report.md`;
`__main__.py` (CLI wiring + `--date` guard). Full suite **252 passed**.

**Deferred.** SETUP.md `--eod-report` usage + ARCHITECTURE/spec reconciliation → **P10-D**.

## 2026-07-06 — P10-B: dated storage inside the package

**What / why.** Relocated the recorder's data **inside** the package (`output_dir → ./market_depth_recorder/
data`) and added an **opt-in dated-sub-folder layout** so every artifact for a trading day is grouped:
`data/<YYYY-MM-DD>/{raw .jsonl.gz, live .db, .duckdb, reports/}`. New `recorder.date_partitioned: true`
(validated bool, optional→flat). **Operational singletons stay at the base dir** (`health.json`,
`reprocess.log/.lock`) so `--status`, the run-lock, and the reprocess launcher stay date-agnostic.

**How.** New `utils.session_output_dir(output_dir, session_date, date_partitioned)` → the effective per-day
dir; wired into `RawTickFileWriter` + `SQLiteLiveWriter`. Replay/reprocess place the canonical DuckDB and
derived live-store **beside the raw log** (`os.path.dirname(raw)`) — flat/partitioned-agnostic — and
`catchup` globs both the base and dated sub-folders (union, sorted by filename). `config_hash` unchanged
(paths aren't part of the formula).

**Affected files.** `config.yaml`, `config.py`, `utils.py`, `file_writer.py`, `database_writer.py`,
`replay.py`; new `tests/test_paths.py` (9 tests). Full suite **237 passed**.

**Deferred.** ARCHITECTURE/spec storage-topology reconciliation → **P10-D**. The P9 data captured under the
old flat `SS_Projects/data` is orphaned by the relocation — the P10-C EOD tool will read an explicit
dir/date, so it can still be pointed at it.

## 2026-07-06 — P9 live run (partial pass) + P10-A OpenAlgo TBT channel-spread patch

**P9 live run.** Executed the recorder against a live OpenAlgo + FYERS session (IST market hours). Confirmed
(cannot be faked): real chain resolution; preflight actual depth **NIFTY/NFO→50, SENSEX/BFO→5** with
per-level `orders`; §9 degrade alarm; Init→Connect→Record + mid-day REST ATM seed; raw audit fields +
HEADER `instruments`; `cycle_ms_p50=10.5`/`max=14.2` (<15), `rss=51 MB`, drops=0. **3 bugs fixed** (228
tests green): (1) `instrument_manager._matches_underlying` — live master `name` is the full contract label,
not the base underlying → symbol-prefix fallback now fires whenever exact-name fails; (2) invalid
`heartbeat_timeout(12) > interval(10)` crashed `run_forever` → config `8` + new `config.py` validation rule;
(3) preflight infers depth level count from `len(depth["buy"])` when `depth_levels` absent (5-level packets).
Full record: `Documents/patches/Phase9_notes.md`.

**Headline finding.** FYERS TBT 50-level depth caps at **5 symbols per channel**, and OpenAlgo hardcoded
`channel="1"` → effective ceiling 5 total. 80 NIFTY `:50` legs → NIFTY captured **0 depth**; SENSEX (non-TBT
HSM 5-level) fine. → P10.

**P10-A (this entry).** Patched the **platform** FYERS adapter to pack 50-depth subs 5-per-channel across
channels 1–50 (ceiling 5→250). New `_assign_tbt_channel()` + class consts; reuses an existing symbol's
channel on reconnect (race-free — caller holds `self.lock`); 250-ceiling → ERROR. TBT client already resumes
new channels + resubscribes per channel, so no client change. `py_compile` OK.

**Affected files.** *Platform:* `broker/fyers/streaming/fyers_websocket_adapter.py` (patch). *Recorder fixes:*
`instrument_manager.py`, `config.py`, `config.yaml`, `websocket_client.py`, `tests/conftest.py`. *Docs:* new
`Documents/patches/Phase9_notes.md`, `Documents/patches/OPENALGO_PATCH.md`, `Documents/patches/openalgo_fyers_tbt_channels.patch`.

**Deferred.** Live smoke of the patch (needs OpenAlgo restart) → **P10-E1/E2**; whole-chain 50-level,
global-cap check, authoritative perf/RSS, graceful teardown → **P10-E**. Dated storage (**P10-B**), EOD
health/sanity report (**P10-C**), and the ARCHITECTURE/CLAUDE/spec Depth-Reality reconciliation (**P10-D**)
are the next phases.

## 2026-07-06 — P8: Offline integration & soak harness + perf/RSS instrument + SIGTERM

**What / why.** The final planned phase. Builds the **automated whole-pipeline harness** (the real
four-thread pipeline end-to-end, driven by a scripted recorded feed + the real reprocess subprocess) that
the P6 docs had claimed but never committed as code; adds the perf/memory instrumentation the `<15 ms` /
`<500 MB` targets need; and closes the managed-shutdown gap with a SIGTERM handler. The **live**
confirmations (FYERS actually delivering 50-level depth, per-level `orders`) become a separate operator
phase **P9** — see `Documents/LIVE_RUN.md` — because they cannot be faked; run when the market is open.

**Forks resolved (user, 2026-07-06).** (1) E2E approach → **build both**: P8 = offline harness (now),
P9 = live run (runbook now, executed later). (2) RSS → **stdlib platform-adaptive** (`ctypes` on Windows,
`getrusage` on Unix — no `psutil`). (3) SIGTERM → **add a graceful-teardown handler**. (4) Cycle timing →
**permanent, surfaced in `health.json`**.

**Added.**
- `tests/test_integration.py` — `@pytest.mark.integration` whole-pipeline harness: `RecordedTransport`
  (a real `FeedTransport` playing a self-paced NIFTY-50-level / SENSEX-5-level feed) drives the real
  `_build_default_pipeline`; asserts clean thread joins, a `HEADER..EOF`-framed raw `.gz` with the
  `instruments` block, depth audit fields preserved (`feed_time`/`depth_levels`/`is_50_depth`/per-level
  `orders`), a populated live `.db`, `health.json` perf fields, and **no FD residue**; then runs the real
  `--replay --catchup` **subprocess** → DuckDB (`built_by="replay"`) and proves determinism via
  `replay.verify`.
- `Documents/integration.md` (harness + whole-pipeline FD audit); `Documents/LIVE_RUN.md` (P9 runbook).

**Edited (small, additive).**
- `utils.py` — `process_rss_mb()` (F6): stdlib platform-adaptive RSS in MiB (Windows working set via
  `ctypes`/`K32GetProcessMemoryInfo` with explicit `restype`/`argtypes`; Unix peak `ru_maxrss`).
- `processor.py` — `perf_counter` around `emit_second` (single-owner, no lock); `cycle_ms_p50`/
  `cycle_ms_max` in `stats()`.
- `main.py` — `build_health()` adds `cycle_ms_p50`/`cycle_ms_max`/`rss_mb`; `read_status` prints them.
- `__main__.py` — `_install_sigterm_handler` / `_make_sigterm_handler` wired into `_cmd_run` (live daemon
  only) → `orchestrator.stop()`.
- `tests/{test_utils,test_processor,test_main}.py` — RSS, cycle-time, SIGTERM, and health/status field
  coverage. `tests/conftest.py` — register the `integration` marker.

**Verification.** Full `pytest market_depth_recorder/tests/ -q` **228 passed** (221 prior + 7 new), no
live feed/broker; the integration harness rebuilds a DuckDB store from a thread-produced raw log via the
genuine subprocess and verifies determinism. **Whole-pipeline FD audit** (assertion-backed): every worker
joined (no `is_alive()` after teardown), raw gzip HEADER..EOF, live SQLite opened+closed, DuckDB build
conn closed, subprocess reaped, no `.tmp_`/`.building_`/`.lock` residue; `process_rss_mb`/SIGTERM add no
FD. **Genericization** grep of `utils/processor/main/__main__.py` clean (NIFTY/SENSEX live only in the
test's canned chain). **Doc correction:** the P6 "real four-thread e2e smoke" claim (which was a manual
check, not committed code) is now accurate.

**Deferred.** P9 live-run execution (needs a live FYERS session during market hours).

## 2026-07-06 — P7: Replay + DuckDB writer (`replay.py`, `database_writer.py::DuckDBAnalyticalWriter`)

**What / why.** Builds the **offline** path — replay the lossless Tier-0 raw `.jsonl.gz` through the
**same** `TickProcessor` (full metric catalog) and bulk-load the fat Tier-2 DuckDB analytics store. This
is the normal way Tier 2 exists (the P6 M6 reprocess shells out to `--replay --catchup`; it now runs a
real build) and the determinism harness (`--verify`). After P7 both tiers are complete — only P8
(integration & soak) remains. Verified end-to-end: the exact M6 `--replay --catchup` subprocess rebuilds
a DuckDB store (5 spot / 30 option / 15 agg rows, `built_by="replay"`) from an enriched raw log.

**Forks resolved (user, 2026-07-05).** (1) Instrument context → **enrich the raw HEADER** with the
resolved chain (self-contained, correct for any-age log). (2) Replay clock → **`recv_ts`** (the recorder
clock the live resampler/staleness used → second-for-second parity). (3) DuckDB bulk load →
**`executemany`, no new dep**. (4) Verify → **both modes**.

**Decisions (plan doc 65–72).** HEADER enrichment via `to_header_dict`/`from_header` (65); `recv_ts`
virtual clock (66); synchronous processor reuse + a thin public `TickProcessor.ingest` (67); plain
`with`-managed `DuckDBAnalyticalWriter`, `executemany` bulk, temp-file-then-rename idempotency (68);
`--catchup` oldest-first self-heal (69); `--verify` both modes with schema/config_hash gate + tolerance
diff (70); robust reader — corrupt-line/missing-EOF/multi-HEADER (71); `--underlying`/`--from`/`--to`
filters with a warm-up caveat (72).

**Added files.**
- `replay.py` — `_load_header`/robust packet reader; `replay_file` (recv_ts-driven synchronous drive →
  DuckDB); `catchup`; `verify` (+ `_read_table`/`_read_meta`/`_values_equal`/`_live_column_set`);
  path resolvers (`canonical_output`/`replay_side_output`/`live_store_path`).
- `tests/test_replay.py` — 15 offline tests. `Documents/replay.md`.

**Edited files.**
- `database_writer.py` — `DuckDBAnalyticalWriter` body + `_DUCKDB_DDL` (§4.1a). `tests/test_database_writer.py`
  — replaced the deferred-stub test with 4 DuckDB writer tests (DDL/provenance, round-trip + NULL +
  `is_50_depth`→BOOLEAN, idempotent fresh file, discard-on-error).
- `instrument_manager.py` — `to_header_dict()` + `from_header()` (+ `_extract_data_obj` already from P6).
- `file_writer.py` — HEADER `instruments` block (new optional `instruments=` arg).
- `main.py` — orchestrator passes `im.to_header_dict()` to the raw writer (guarded for fakes).
- `processor.py` — thin public `ingest(pkt)`.
- `__main__.py` — replaced the `--replay/--catchup` stub with `_cmd_replay` (output resolution, verify
  dispatch, filters, exit codes).
- `market_depth_recorder_design.md` §8.3 (recv_ts basis) + §3.5.4 (HEADER `instruments`); `PROJECT_NOTES.md`.
- `Documents/{database_writer,file_writer,instrument_manager,ARCHITECTURE}.md`.

**Verification.** Full `pytest market_depth_recorder/tests/ -q` **221 passed** (203 prior − 1 removed stub
+ 4 DuckDB + 15 replay). `--replay` builds the four §4.1a tables + `recorder_meta`; `--verify` clean on a
re-replay (determinism); a perturbed metric → drift; `--catchup` self-heals; `--verify-against-live`
live-subset matches a real SQLite live store; rolling warm-up NULLs. **FD audit:** the DuckDB build
connection is `with`-closed + CHECKPOINT + temp→rename on every path (finalize/exception/discard); the gzip
reader is `with`-closed; `verify`/`catchup` read-only connections closed in `finally`; replay adds **no**
thread/subprocess/lock. **Genericization:** `replay.py`/DuckDB writer keyed by `name`; table/column names
are §4 schema constants imported from `processor`. **Invariants:** idempotent fresh file (§8.5); determinism
proven by `--verify`; warm-up reproduced; recv_ts live-parity; lossless raw untouched (read-only).

**Deferred.** P8 — live end-to-end + whole-pipeline FD/soak, live-FYERS depth confirmations, performance
sanity. A pre-enrichment (headerless-`instruments`) log is not self-contained → `from_header` raises a
clear error (there are no such production logs; all P7+ logs carry the block).

## 2026-07-05 — P6: Orchestrator (`main.py::RecorderOrchestrator`)

**What / why.** Builds the **conductor** — the missing piece that constructs, wires, supervises, and
tears down the four-thread live pipeline P0–P5 built as standalone workers. `main.py` owns the §3.1.1
milestone state machine + 1-second loop, the three queues / two shutdown events / `error_queue`,
mid-day-restart recovery, the health file, the session guards (disk + trading calendar), and the
end-of-session reprocess subprocess launcher. It is the `default` (no-mode) CLI entry and implements
`--status`. After P6 the only unbuilt module is P7 (replay/DuckDB). Verified end-to-end against a no-op
transport: real threads build/start/join cleanly (none left alive → no leak), raw `.gz` framed
`HEADER..EOF`, live `.db` created, `health.json` written, reprocess launched with the right command.

**Decisions (plan doc 56–64).** Act-at-launch milestones, record-gate at `session_start` (56);
mid-day-restart ATM seed via new `RestClient.get_quote` + `mark_restart_boundary`, WS fallback (57);
in-process supervisor restart, bounded → fail-fast (58); build the M6 reprocess launcher now, tested
against a stub (59); two-signal teardown in spec drain order **feed → processor → db_writer** (raw
parallel) (60); small additive touches to P1/P2/P3 (61); the §6.4 health payload + `--status` (62);
disk + trading-calendar guards (63); two new config keys `supervisor_interval_sec`/`max_restart_attempts`
(64). **Forks resolved:** add `get_quote` (spec-faithful §3.1.2); init+connect at launch, record-gate at
`session_start`; in-process supervisor restart; build the reprocess launcher now.

**Key design point — two shutdown events.** `shutdown_event` (feed·processor·raw) is separate from
`db_shutdown_event` so teardown joins the processor first (draining `proc_queue` + flushing its final
rows into `db_queue`) and only then signals the db writer — closing the race where both would see a
shared event set with `db_queue` momentarily empty and the db writer could exit before the processor's
final rows land (§3.1.4). No change to any worker's code.

**Added files.**
- `main.py` — `RecorderOrchestrator` (milestone loop, `_build_default_pipeline`, `_seed_restart`,
  `_supervisor_tick`, `_teardown_pipeline`, `build_health`/`_write_health`, disk/holiday guards,
  `_launch_reprocess` + run-lock, `_default_reprocess_launcher`) + `Milestone` enum + `read_status`.
- `tests/test_main.py` — 16 offline tests (virtual clock + fake workers via `pipeline_factory`).
- `Documents/main.md`.

**Edited files.**
- `instrument_manager.py` — `RestClient.get_quote` (+ `_extract_data_obj`); `InstrumentManager.resolved`
  property. `tests/test_instrument_manager.py` — 4 `get_quote` tests.
- `websocket_client.py` — `seed_spot`, `freeze_dsm`, `connection_status`, `last_recv_ts`,
  `_capture_actual_depth`/`actual_depth`. `tests/test_websocket_client.py` — 6 P6-touch tests
  (+ `FakeInstrumentManager.symbol_to_strike_map`).
- `file_writer.py` — `eof_written` flag (the reprocess clean-EOF gate).
- `__main__.py` — `--status` reader wired; the `default` entry now runs `RecorderOrchestrator.run()`.
- `config.py` + `config.yaml` + `tests/conftest.py` + `tests/test_config.py` — `supervisor_interval_sec`
  (≥1) and `max_restart_attempts` (≥0) §7.3 validation + negative tests.
- `Documents/{ARCHITECTURE,instrument_manager,websocket_client}.md`.

**Verification.** Full `pytest market_depth_recorder/tests/ -q` **203 passed** (175 prior + 16 main + 4
`get_quote` + 6 WS touches + 2 config); `--validate-config` → 0 (incl. two new keys); `--status` → 0 with
a friendly message when no health file exists; genericization grep of `main.py` clean; an end-to-end smoke
of the real four-thread pipeline was run **manually** here (the automated committed harness lands in P8 —
`tests/test_integration.py`). **FD/thread audit:** all four workers joined on every
path (clean teardown, crash-restart, KeyboardInterrupt); reprocess child → real log file + `.wait()`-reap
+ lock release; health temp fd closed by `atomic_write`; no thread/queue/FD leak across a supervised
restart (old objects joined + dropped before rebuild).

**Deferred.** P7 replay + `DuckDBAnalyticalWriter` (the reprocess launcher already emits the `--replay
--catchup` command against a stub in tests). Multi-day continuous looping in one process (one `run()` =
one session; the OS scheduler relaunches daily). Live end-to-end + whole-pipeline soak = P8.

## 2026-07-04 — P5: SQLite live writer (`database_writer.py::SQLiteLiveWriter`)

**What / why.** Builds the fourth and final **live thread** — the batching consumer that drains
`db_queue` (the per-second envelopes P4 emits, previously unread) and commits the `recorder.live_metrics`
subset to the thin Tier-1 SQLite/WAL store `market_depth_live_YYYYMMDD.db` (§4.1). Closes the live path
end-to-end (feed → tee → processor → **DB**); the only unbuilt live piece left is the P6 orchestrator.

**Decisions (plan doc 48–55).** Single-owner `sqlite3.Connection`, no lock, opened inside `run()`
(decision 48); column order imported from `processor` so INSERTs can't drift from the emitted tuples (49);
injected clock + session date (50); batch commit on size OR `batch_write_interval_ms` (51); `recorder_meta`
stamped once at DB creation, `built_by="live"` (52); PASSIVE checkpoint cadence + teardown TRUNCATE +
optimize, **no VACUUM** — §4.4 authoritative over §3.6.4 (53); corruption recovery on open — `quick_check`
→ archive `.corrupt_<epoch>.bak` + rebuild, non-fatal since the fat store rebuilds from raw (54); health
counters `rows_written`/`rows_ignored_total`/`commit_error_count`/`corruption_recoveries` (55).

**Forks resolved (plan doc A–C).** (A) Boundary-second `INSERT OR REPLACE` **deferred to P6**: P5 ships
steady-state `INSERT OR IGNORE` + count/log and exposes `mark_restart_boundary(ts)` for P6 to drive.
(B) Added §7.3 validation for `batch_size`/`cache_size_mb`/`wal_checkpoint_interval_sec`. (C) Deferred
`DuckDBAnalyticalWriter` stub raising `NotImplementedError` at construction (P3 `SdkTransport` precedent).

**Added files.**
- `database_writer.py` — `SQLiteLiveWriter(threading.Thread)`: DDL constants (4 tables §4.1 + 4 indexes
  §4.2 + `recorder_meta` §4.1b), `_open_db`/`_quick_check_ok`/`_recover_corrupt_db`/`_apply_pragmas`/
  `_create_schema`, `_buffer`/`_maybe_flush`/`_commit` (IGNORE/REPLACE + PK-collision count), periodic
  `_maybe_checkpoint`, `_teardown_pragmas`, defensive `_maybe_rollover`, `mark_restart_boundary`, and the
  deferred `DuckDBAnalyticalWriter` stub.
- `tests/test_database_writer.py` (14 tests).
- `Documents/database_writer.md`.

**Changed files.**
- `config.py` — §7.3 rules: `batch_size` ∈ [1,5000], `cache_size_mb ≥ 1`, `wal_checkpoint_interval_sec ≥ 30`.
- `config.yaml` — annotated the three keys' bounds.
- `tests/test_config.py` — one negative case per new rule.
- `Documents/{ARCHITECTURE,CHANGELOG}.md`.

**Verification.** Full suite **175 passed** (158 prior + 14 writer + 3 config) with no live feed.
`--validate-config` → 0 on the shipped config, → 1 with the exact message on each seeded-bad key.
Round-trip proof for all four tables (`None` → NULL, column-for-column), batch flush by size and by time,
PK-collision IGNORE count, `mark_restart_boundary` → REPLACE + revert, PASSIVE checkpoint cadence,
teardown TRUNCATE+optimize (no VACUUM), corruption archive+rebuild, graceful drain via the real thread.
**FD audit:** one `sqlite3.Connection` opened in `run()` and closed in `run()`'s `finally` on every path
(clean, exception, shutdown, corruption-rebuild, date-rollover); `run()` hardened so a *partial* `_open_db`
still closes its FD; corruption recovery closes the bad conn before reconnecting; DuckDB stub holds nothing.
**Concurrency:** single-owner connection + state, no lock; cross-thread edges only the thread-safe
`db_queue` and the atomic single-word `mark_restart_boundary` hand-off. **Genericization:** no
index/exchange/strike/CE-PE literal — table/column names are §4 schema constants; symbols flow from
envelopes.

**Deferred.** Boundary-`INSERT OR REPLACE` wiring (P6 drives `mark_restart_boundary`); orchestrator +
health file + `proc_queue`-side shedding (P6); DuckDB analytical writer + replay `--verify` (P7).

## 2026-07-04 — P4b: Rolling windows + aggregates + regime (`metrics/rolling.py`, `metrics/aggregate.py`)

**What / why.** Completes the compute core's metric catalog. `TickProcessor.emit_second` now emits **all
four** §4.1 tables: it back-fills the instantaneous `ofi` on `option_strike_metrics`, emits
`strike_window_metrics` (§3.4.3 rolling windows, one row per `(symbol, w∈time_windows_sec)`), and
`aggregated_window_metrics` (§3.4.4 multi-strike aggregates + regime, one row per `(underlying,
SMALL/MEDIUM/LARGE)`). Compute order is per-strike → rolling → aggregate → regime (decision 37). P7 reuses
all these bodies verbatim (adds only replay + DuckDB, no new math).

**Decisions (plan doc 43–47).** Family-specific bound signatures — rolling `fn(hist, n, ctx)`, aggregate
`fn(ce, pe, ctx)`, scalar `fn(view, ctx)` (43); single-owner P4b engine state (`_window` deques +
`_prev` touch-books, `maxlen = 2·max(window)+1`), no lock (44); windowed liquidity = window **sums** of
per-second price-aligned ΔQ (45); per-underlying regime + pinning written identically into all three
window rows (46); rolling `min_depth` inherited via `None` inputs — a shallow/stale second contributes
`None` and is skipped (47).

**Added files.**
- `metrics/rolling.py` — §3.4.3 window bodies (price_return, spread/wobi stats, regression slopes,
  micro-price RV, windowed liquidity flow/churn/intensity, pressure velocity/accel, wall persistence/
  events, `ofi_sum`) + the instantaneous `ofi_instant` / `liquidity_delta_instant` helpers + the
  `HEAVY_METRICS` degraded-skip set.
- `metrics/aggregate.py` — §3.4.4 per-window bodies (depth_pcr, consolidated_pressures, pooled `bnet`,
  spread_diff, net_options_pressure), per-underlying `pinning_score`/`regime`, and the `compute_underlying`
  ATM-window-slicing orchestrator.
- `tests/test_metrics_rolling.py` + `tests/test_metrics_aggregate.py`.

**Changed files.**
- `processor.py` — P4b wiring in `emit_second`: `_compute_option` (per-strike + rolling + aggregate
  feature), `_core`/`_wall`/`_instantaneous`/`_append_sample`/`_window_rows`/`_agg_rows`/`_strike_step`,
  `STRIKE_WINDOW_COLUMNS`/`AGG_COLUMNS`, degraded heavy-skip, per-underlying agg radii. Still no lock, no
  FDs.
- `metrics/snapshot.py` — `WindowSample`, `StrikeFeatures`, `TouchBook` + `touch_book()`; `MetricContext`
  gains `regime`.
- `metrics/__init__.py` — imports `rolling` + `aggregate` so their bodies bind at package import.
- `tests/test_processor.py` — P4b integration (four tables, `ofi` back-fill, dependency closure, degraded
  heavy-skip keeps cadence, full determinism); the P4a envelope test now tolerates the two new tables.
- `Documents/{processor,metrics,ARCHITECTURE}.md`.

**Verification.** Full suite **158 passed** (130 prior + P4b, incl. two fixed pre-existing tests) with no
live feed. Rolling/aggregate bodies verified against hand-computed fixtures (price-aligned add/remove,
slopes, RV with a skipped stale second, OFI sign + boundary NULL, wall persistence/events, both-sides PCR,
pooled `bnet` window-invariance, all five regime labels); engine integration covers four-table emission,
`ofi` back-fill after the boundary second, dependency closure, degraded heavy-skip keeping the 1s cadence,
and full `emit_second` determinism. **FD audit:** processor still holds no files/sockets/DB/subprocess —
only queues/arrays/deques. **Concurrency:** single-owner state, no lock; cross-thread edges only the two
thread-safe queues. **Genericization:** no index/exchange/strike/CE/PE literal in `rolling.py`/
`aggregate.py`/`processor.py` — CE/PE from the InstrumentManager map, windows/radii/thresholds from config,
all state keyed by `name`.

**Also fixed (pre-existing, exposed by this run).** (1) `test_write_error_counted_and_thread_survives`
(P2) was **date-dependent**: it used the real clock, so the defensive IST rollover fired once the calendar
passed its hardcoded `session_date` (2026-07-03 → -04) and consumed the FakeHandle's one failing write on
the EOF marker — fixed by injecting the existing fixed `Clock()` (the design's inject-the-clock rule). No
production code changed. (2) The P4a `test_emit_produces_spot_and_option_envelopes` assertion was tightened
to a subset check now that `active="all"` emits four tables.

**Deferred.** SQLite live writer (P5 — *now done, see the P5 entry above*), orchestrator + health file +
proc_queue-side shedding (P6), DuckDB analytical writer + replay `--verify` (P7). Process-sharding
(`processor.mode: process`) remains §5.2 headroom.

## 2026-07-03 — P4a: Processor engine + per-strike metrics (`processor.py`, `metrics/`)

**What / why.** The compute core: `TickProcessor`, the third pipeline thread, drains `proc_queue`,
keeps a uniform 1-second grid, and turns each second's option-book snapshots into `spot_states` +
`option_strike_metrics` rows on `db_queue` (§3.4.1). It binds the actual NumPy metric bodies (M1–M29,
§3.4.2) to the registry specs P0 declared as metadata-only. P4 is split (user fork): **P4a** = engine +
single-snapshot per-strike metrics; **P4b** = §3.4.3 rolling (+ `ofi`) and §3.4.4 aggregates/regime.

**Decisions (recorded in the plan doc, decisions 31–41).** Split P4a/P4b (31); metric bodies in
`metrics/` compute modules bound via a new `registry.bind()` (32); single-owner processor thread, no
lock (33); injected clock + pure `emit_second` seam for P7 replay (34); `BookSnapshot` `__slots__`
built once per (symbol,second) (35); `:50`-stripped DB symbol + option/spot/unknown classifier (36);
dependency closure + per-strike→rolling→aggregate order (37); `db_queue` `{"table","rows"}` envelope
contract in §4.1 column order (38); staleness/forward-fill + degraded skeleton keeping the 1s cadence
(39); NULL/guard matrix from `min_depth` + spec caveats (40); M22/M24 touch-history deque as P4a engine
infra, `ofi` deferred to P4b (41).

**Added files.**
- `processor.py` — `TickProcessor(threading.Thread)` (drain/classify/cache, `emit_second`, ATM
  resolution, forward-fill/staleness, degraded skeleton + critical shed, `db_queue` back-pressure,
  `stats()`); `strip_suffix`, `SPOT_COLUMNS`/`OPTION_COLUMNS`. No lock, no FDs.
- `metrics/snapshot.py` — `BookSnapshot` (best-first NumPy arrays, `__slots__`), `MetricContext`,
  `StrikeHistory`.
- `metrics/per_strike.py` — M1–M29 bodies bound via `@bind`, with all §3.4.2 corrections + guards.
- `tests/test_metrics_per_strike.py` (17 tests) + `tests/test_processor.py` (15 tests).
- `Documents/processor.md`, `Documents/metrics.md`.

**Changed files.**
- `metrics/registry.py` — added `bind(name)` (bind body to an existing spec; unknown-name fast-fail),
  `resolve_active(live_metrics)` (ordered active spec set), `active_columns()`.
- `metrics/__init__.py` — imports `per_strike` so bodies bind at package import.
- `config.yaml` + `config.py` — new `metrics.fill_probe_qty` (M25 probe size) + its positive validation;
  `tests/conftest.py` fixture updated.
- `Documents/ARCHITECTURE.md` — P4a built state + updated thread/queue topology.

**Verification.** Full suite **129 passed** (98 prior + 31 new) with no live feed; per-strike metrics
verified against hand-computed values + every guard; engine covers classify/emit/ATM/staleness/
forward-fill/thin-selection/degraded/determinism + a real-thread graceful-drain. FD audit: the
processor holds no files/sockets/DB/subprocess — only queues/arrays/deques (zero FD surface).
Concurrency: single-owner state, no lock; cross-thread edges are only the two thread-safe queues.
Genericization: no index/exchange/strike/CE/PE literal in `processor.py` or the metric modules.

**Deferred.** §3.4.3 rolling metrics + the `ofi` column and §3.4.4 aggregates/regime → **P4b** (so only
`spot_states` + `option_strike_metrics` are emitted now). Heavy-rolling degraded skip set, proc_queue-side
shedding + health-file wiring → P4b/P6. Minor structural refinement: `BookSnapshot`/`MetricContext` live
in `metrics/snapshot.py` (not `processor.py`) to avoid a processor↔metrics circular import.

## 2026-07-03 — P3: WebSocket client + DSM (`websocket_client.py`)

**What / why.** The first **networked** module and the tick producer: a `DepthWebSocketClient` FEED
thread that owns the feed transport, the Dynamic Strike Manager (DSM), the tee into
`raw_file_queue`/`proc_queue`, the recorder-owned reconnect state machine, and the live
depth-capability preflight (§3.3/§6.1/§3.2.5/§9). It closes the loop from "resolved chains" (P1) to
"packets flowing into the audit + analytics queues" (P2 writer downstream).

**Decisions (recorded in the plan doc, decisions 20–30).**
- **Transport seam (20)** — `FeedTransport` protocol; `RawWSTransport` built (default), `SdkTransport`
  a deferred fail-fast stub. The SDK depth callback strips the audit fields, so raw stays default.
- **Canonical packet = wire message, lightly normalized (21)** — `symbol` kept **as received** (keeps
  `:50` on depth topics, §3.3.3); the same dict is teed to both queues; DB-symbol stripping is downstream.
- **Native heartbeat (22)** — `run_forever(ping_interval, ping_timeout)`, no hand-rolled monitor thread.
- **One FEED thread + three locks (23/24)** — `_spot_lock → _sub_lock` order, `_client_lock` independent;
  `connect/disconnect` off `_client_lock`; no I/O under any lock; the tee is lock-free.
- **Lazy DSM seeding (25)** — boundaries seed from the first valid spot tick; P6's REST one-shot feeds the
  same `on_spot` entry, so P3 needs no REST/quotes.
- **Never-shrink (26)** — subscriptions only grow intra-session; `active_subscriptions` holds wire symbols.
- **Tee backpressure (28)** — proc sheds first (WARNING+count), raw sheds last (ERROR+count, the single
  sanctioned raw-loss boundary).
- **`--preflight` graceful-degrade (30)** — offline resolve is a prerequisite (exit 1 on REST failure);
  the live depth probe is best-effort (unreachable WS → `actual_depth=<unreachable>`, exit 0).

**Added files.**
- `websocket_client.py` — `FeedTransport`/`RawWSTransport`/`SdkTransport(stub)`/`make_transport`;
  `DepthWebSocketClient(threading.Thread)` (tee, DSM `_on_spot`/`_check_boundaries`, subscription flow +
  never-shrink, reconnect loop with injected `sleep_fn`, `on_open` auth+resubscribe); module helpers
  `wire_symbol`/`normalize_market_data`; `run_depth_preflight` + `DepthProbeResult` (§3.2.5/§9). One FD
  (WS socket), closed on every path; close-before-reconnect.
- `tests/test_websocket_client.py` (19 tests) — tee both-queues + shed order + raw-drop accounting;
  spot routing; DSM seed/upper-breach/lower-breach (gradual ramps within the 2% spike guard)/spike +
  non-positive rejection; never-shrink on pullback; reconnect auth+spot+resubscribe; disconnected-
  subscribe flushed on reconnect; deterministic backoff sequence; wire-symbol + normalize helpers;
  live preflight reads `depth_levels`/`is_50_depth`/`orders` + WARNs on `actual<requested`; unreachable
  probe degrades fast. All offline (fake transport + injected clock/sleep).
- `Documents/websocket_client.md` (new per-module doc).

**Changed files.**
- `__main__.py` — `_cmd_preflight` re-pointed from P1's offline `<pending>` to the live probe
  (graceful-degrade to `<unreachable>` + exit 0).
- `tests/test_instrument_manager.py` — the two `--preflight` tests updated for the live-probe output
  (`actual_depth=50` / `<unreachable`); added a WS-unreachable-exit-0 CLI test.
- `Documents/ARCHITECTURE.md` (P3 built state; topology now shows the FEED thread + tee + locks;
  transport + CLI notes updated), `Documents/instrument_manager.md` (`--preflight` now live).
- Live plan doc P3 section expanded with decisions 20–30 + subtask checklist.

**Deferred.** `SdkTransport` body (post-P3, additive against the seam); `--status`/orchestration/
teardown/REST-quote mid-day seeding (P6); the resampler/metrics that consume `proc_queue` (P4).

**Verification.** `python -m pytest market_depth_recorder/tests/ -q` → **98 passed** (79 prior + 19
new), no live feed. `--validate-config` → exit 0; `--preflight` without a server → exit 1 at REST
resolution (the documented prerequisite). Genericization grep on `websocket_client.py` → only a
doc-comment `NIFTY/SENSEX` mention; `:50`/`5` are cited transport constants (`_TBT_SUFFIX`/
`_TBT_MIN_DEPTH`). A **real bug the tests caught:** the initial breach tests jumped spot >2% in one
tick and were (correctly) rejected by the DSM's own spike guard — fixed the tests to ramp gradually,
confirming the guard behaves as specified.

## 2026-07-03 — P2: Tier-0 gzip file writer (`file_writer.py`)

**What / why.** The first background writer thread and the first stage of the pipeline: drains
`raw_file_queue` and appends every WS packet to the daily gzip JSON Lines log — the **lossless source
of truth** (§1.4) both derived stores rebuild from. Isolating file I/O to this thread shields the feed
receiver from disk latency (§3.5).

**Decisions (recorded in the plan doc, decisions 15–19).**
- **Single-owner FD, no lock** — the gzip handle is touched only by `run()`; exclusive ownership is
  stronger than a lock.
- **Injected clock (`time_fn`)** — sole source of epoch timestamps, the fsync cadence, and the rollover
  date, so every time branch is deterministic under test.
- **Append mode (`gzip.open("at")`)** — a same-day restart appends a second HEADER (records the restart)
  rather than truncating prior audit data.
- **Write-failure = the one sanctioned raw-loss boundary** — caught, `write_error_count`++, ERROR-logged,
  thread continues (§1.4). Sentinel-error-queue wiring deferred to P6 (optional `error_queue` hook left).
- **Tests round-trip via stdlib `gzip`+`json`** (pandas isn't a pinned dep); one `importorskip("pandas")`
  compat check honors the §3.5.1 tooling claim.

**Added files.**
- `file_writer.py` — `RawTickFileWriter(threading.Thread)`: `resolve_filename` (staticmethod), HEADER at
  open + EOF on clean drain (`SCHEMA_VERSION`/`config_hash`/underlyings stamp, §3.5.4), two-tier flush
  (§3.5.3), defensive IST daily rollover, per-packet write-error accounting; `records_written` /
  `write_error_count` counters for P6 health. One gzip FD, closed on every path via a guarded `finally`.
- `tests/test_file_writer.py` (10 tests) — HEADER/data/EOF round-trip + exact packet equality;
  provenance stamping; cheap-flush cadence; bounded fsync cadence (spied `os.fsync` + controllable
  clock); missing-EOF + byte-truncated-tail tolerance (clean-prefix recovery); defensive rollover;
  write-error accounting (thread survives); graceful drain through the real thread; optional
  `pandas.read_json` compat.
- `Documents/file_writer.md` (new per-module doc).

**Changed files.** `Documents/ARCHITECTURE.md` (P2 built state; threading/queue topology now shows the
raw writer built; provenance bullet notes the HEADER/EOF stamp landed). Live plan doc P2 section
expanded with decisions 15–19 + subtask checklist, boxes ticked.

**Verification.** `python -m pytest market_depth_recorder/tests/ -q` → **79 passed** (69 prior + 10
new), no live feed. Tests run the writer synchronously (`run()` with a pre-set shutdown event) and via
a real started thread (`start()`/`q.join()`/`join()`), reading logs back with stdlib `gzip`+`json`.
The `-o addopts=""` flag is needed only to detach from the openalgo repo's root `pytest` addopts
(`--timeout`), unrelated to this package.

**Robustness fix caught while testing.** The rollover guard originally compared the **machine-local**
date against `session_date` (derived from `now_ist()`); on a non-IST host that mismatch would trigger a
spurious rollover on the first write. Changed to compare in **IST** (`datetime.fromtimestamp(...,
tz=IST)`), matching `session_date`'s basis — the guard now never fires spuriously in a normal session.

**FD audit (P2 surface).** Exactly one gzip handle per open, created in `_open_file` and released by a
guarded, idempotent `_close_file` (`flush` → `fsync` → `close`) inside a `finally`, so it closes on
clean drain, mid-loop exception, rollover, and shutdown alike. `fsync` guards a closed/invalid `fileno`
(`OSError`/`ValueError`). No sockets/DB/subprocess; the single thread is `join()`-reaped by the
orchestrator (P6) and is a daemon as a backstop. Tests leak no handles (fakes hold no real FD). Clean.

**Deferred.** Receiver + tee + the queues themselves → P3; sentinel `error_queue` wiring → P6; the
stores' `recorder_meta` provenance stamps → P5/P7.

## 2026-07-03 — P1: InstrumentManager (`instrument_manager.py`)

**What / why.** First live module: resolve each configured underlying's current weekly option chain
over the OpenAlgo REST API and compile the O(1) lookup structures the DSM (P3) and processor (P4)
consume. Pure resolution — no threads/DB/sockets; the only FD is a transient HTTP connection.

**Decisions (recorded in the plan doc, decisions 10–14).**
- **Live depth probe deferred to P3** (user-confirmed): reading `depth_levels`/`is_50_depth` needs a
  raw-WS subscription (the SDK strips them) and that client is P3. `--preflight` resolves the chain
  offline and reports `actual_depth=<pending P3 raw-WS probe>`.
- **`E_weekly` via `/api/v1/expiry`** (`data[0]`; the service already drops past expiries, sorts, and
  includes the expiry day → rollover gate satisfied). Master used only for the strike grid + tick_size.
- **Underlying match on the `name` column** (exact), longest-prefix `symbol` fallback for blank names
  (NIFTYNXT50 not shadowed by NIFTY).
- **Maps built from master `symbol` rows** (never string-constructed); integral strikes → `int` keys.
- **REST via stdlib `urllib`** (no new dependency).

**Added files.**
- `instrument_manager.py` — `RestClient` (urllib; instruments GET + expiry POST; 10 s timeout, ≤3
  retries on network/5xx, 4xx terminal; injectable opener), `InstrumentManager.resolve()` /
  `preflight_report()`, frozen `ResolvedChain`, and the maps (`strike_to_symbol_map`,
  `symbol_to_strike_map`, `active_strikes_list`, `tick_size_map`). Mode-based strike-step detection
  (§3.2.3) with a warned `strike_step_fallback`.
- `tests/test_instrument_manager.py` — RestClient (success/retry/timeout/5xx/4xx/bad-status/expiry
  body), resolution happy path + contaminant exclusion + blank-name prefix fallback, empty-expiry and
  no-contracts fast-fail, strike-step edge cases (wide-gap mode / single-strike / unexpected→fallback),
  expiry parse, `_option_type`/`_norm_strike`, and `--preflight` exit codes (ok/REST-fail/bad-config).

**Changed files.** `__main__.py` — `--preflight` wired to `_cmd_preflight` (offline resolve + report,
exit 0/1), replacing the P0 stub; imports `setup_logging`. `Documents/ARCHITECTURE.md` (P1 built
state), `Documents/instrument_manager.md` (new per-module doc). Live plan doc P1 boxes ticked.

**Verification.** `python -m pytest market_depth_recorder/tests/ -q` → **69 passed** (48 P0 + 21 new),
no live feed. `--validate-config` still exits 0; `--preflight` with no REST server up exits 1 with a
clean `RestError` (no traceback). All tests run against a scripted fake opener / injected `FakeRest`.
A test caught a real bug: the blank-`name` longest-prefix fallback matched `NIFTYNXT50…` to `NIFTY`
(NIFTYNXT50 isn't a configured underlying) — fixed by requiring the char after the base name to be a
digit (an F&O symbol is `BASE + DDMMMYY…`), so `…NXT50` is rejected.

**FD audit (P1 surface).** Every REST call opens one HTTP connection under `with` (response read then
closed); the `HTTPError` error-body path explicitly `.close()`s the error response before raising or
retrying. No thread/lock/DB/subprocess introduced; `InstrumentManager` holds no long-lived descriptor
after `resolve()`. Clean.

**Deferred.** Live §3.2.5 depth probe + §9 `actual < requested` WARNING → P3; DSM/true-ATM → P3.

## 2026-07-03 — P0: Scaffolding, config, utils, registry skeleton

**What / why.** Stood up the package skeleton so every later phase has a validated config, shared
primitives, and a declarative metric registry to build against. No live feed, threads, or I/O pipeline
yet — those begin at P1.

**Folder rename (P0-A).** `MarketDepth_Recorder/` → `market_depth_recorder/` (the folder *is* the
package, §2.1). The directory-level `git mv` failed (a stale process holds the old dir's handle), so
the three docs were moved **per-file** with `git mv` instead — content and working-tree doc-sync edits
preserved. The now-empty, untracked `MarketDepth_Recorder/` remnant is harmless (git ignores empty
dirs); delete once the holding process closes.

**Added files.**
- `__init__.py` — `__version__ = "0.1.0"`, `SCHEMA_VERSION = 1` (stamped into raw HEADER §3.5.4 and
  `recorder_meta` §4.1b).
- `config.yaml` — §7.1 template materialized verbatim, `transport: "raw"` default, NIFTY+SENSEX.
- `config.py` — YAML load + **all** §7.3 rules (collect-all-errors, fast-fail `ConfigError` → exit 1),
  `compute_config_hash` (sha256 of metrics+regime+underlyings, §3.5.4/§4.1b), frozen typed `Config`
  with typed `Underlying` entries.
- `utils.py` — logging setup (idempotent, single handler, thread name), IST/time helpers
  (`parse_ist_hhmm`, `now_ist`, `to_epoch_seconds`), decay-weight factory (`w_i = exp(-k·(i-1))`,
  §3.4.2 M8), atomic file write, disk-free helper (§3.1.5).
- `metrics/registry.py` — declarative `MetricSpec` + `register`/`resolve`/`known_names`/`GROUPS`;
  **full M1–M29 + §3.4.3 rolling-window + §3.4.4 aggregate/regime metadata**, no function bodies
  (deferred P4/P7). `live_metrics` validation resolves against the complete set from day one.
- `__main__.py` — §8.2 CLI surface; `--validate-config` wired end-to-end (0/1 exit), other subcommands
  parsed + stubbed with clean exits, arg-dependency guards (`--output` needs `--replay`; `--from/--to`
  parse as IST `HH:MM`).
- `requirements.txt` — standalone pins: `openalgo==2.0.2` exact (load-bearing), `numpy/duckdb/PyYAML/
  websocket-client/pytest` compatible-release `~=` against installed versions.
- `.gitignore` — runtime artifacts (`data/**`, `*.jsonl.gz`, `*.db*`, `*.duckdb`, `*.log`, venv, caches).
- `Documents/` — `ARCHITECTURE.md`, this `CHANGELOG.md`, `SETUP.md`, `config.md`, `utils.md`, `registry.md`.
- `tests/` — `conftest.py` (good-config fixture + writer), `test_config.py` (happy path, one negative
  per §7.3 rule, `--validate-config` exit codes, `config_hash` determinism, `live_metrics` membership),
  `test_utils.py` (decay values, IST parse, atomic round-trip, disk free).

**Verification.** `--validate-config` on the shipped config exits 0; **48 tests pass**, no live feed.
Arg guards return exit 2 on misuse; stubs exit 0.

**FD audit (P0 surface).** `config.py` write-probe closes its `mkstemp` fd and unlinks the temp on all
paths; `utils.atomic_write` adopts the raw fd into a file object (closing the bare fd if adoption
fails) and cleans the temp on error; logging adds a single guarded `StreamHandler` (no stacking). No
sockets/DB/subprocess/threads exist yet. Clean.

**Deferred.** Metric function bodies (P4/P7); `recorder_meta`/HEADER stamping (P2/P5/P7); `--preflight`
(P1), `--status` (P6), `--replay`/`--catchup`/`--verify` (P7). Empty `MarketDepth_Recorder/` dir removal
(pending stale handle release).
