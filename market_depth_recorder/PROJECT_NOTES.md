# PROJECT_NOTES.md

Open only when needed (non-trivial tasks, refactors, architecture changes, final review). Don't
`@import` into `CLAUDE.md`. The **design spec** is authoritative — this file is the working rulebook
and roadmap layered on top of it. Canonical spec: the in-folder `market_depth_recorder_design.md`
(the copy under `..\trading_engine\...\LLM_Spec_Chat\` is stale — ignore it).

# Planning & Implementation
1. Clarify scope first: in/out of scope, constraints, edge cases, and **"Anything else to add to
   scope?"** Never assume the request is complete.
2. Discussion only until the trigger phrase **"let's write the plan"** — no plan, subtasks, code, or
   patches before it.
3. On trigger, produce the full plan: ordered phases (each coherent and independently testable), scope
   & deliverables, dependencies/sequencing, assumptions/open questions.
4. Before implementing a phase, expand it into an exhaustive checklist of small, independently
   reviewable subtasks (the implementation contract):
   - Cover all applicable work: code, config, schema/DDL, tests, **docs (`Documents/`)**,
     compatibility, performance, FD hygiene, cleanup.
   - Identify affected files where practical.
   - Complete sequentially; don't silently skip, merge, or drop subtasks.
   - Classify new work as **Required**, **Scope change** (approval required), or **Future enhancement**.
5. Implement one phase at a time. After each: run the Completion Audit, **update `Documents/`**
   (ARCHITECTURE + a dated CHANGELOG entry + any new per-module doc), summarize changes, list
   completed subtasks, note deferred/remaining work, wait for approval. Never auto-proceed. A phase is
   not complete until its documentation is current.
6. No silent scope creep — any deviation from the approved plan needs confirmation.
7. Prefer incremental refactoring over rewrites. Before structural changes, present a migration plan
   (affected files, risks, rollout) and wait for approval; large rewrites need explicit justification.
8. While planning: prefer `grep`/`ripgrep` over full-file reads; read only required spec `§`s and files.
9. Keep the plan synced with actual progress — the plan doc is live, not write-once. Plan location
   (the **only authoritative** copy, in-repo since 2026-08-25):
   `market_depth_recorder\plans\Plan_001_market_depth_recorder_implementation.md`. The old
   `$home\.claude\plans\refer-market-depth-recorder-design-md-an-peppy-dolphin.md` is now a pointer
   stub — never read or edit it. Update the plan
   immediately after: (a) the user answers a decision fork — record the decision + rationale in the
   Locked-decisions/forks section; (b) before implementing a phase — embed its exhaustive subtask
   checklist; (c) a subtask/phase completes — tick its checkbox and refresh remaining/deferred work.
   This is separate from and in addition to the `Documents/` updates (plan tracks progress; `Documents/`
   tracks implemented state).

# Completion Audit
Before marking any subtask or phase complete, deep-audit the change against this checklist. Verify each
item against the actual diff — don't assume; state any unverified risk explicitly.
- Lock correctness / thread ownership (thread owner · lock owner · state owner named).
- Queue **tee** correctness (two independent `put`s, not a shared queue) and backpressure **order**
  (analytics `proc_queue` sheds first → `db_queue` → `raw_file_queue` last).
- **Lossless-raw invariant preserved** — a raw drop is possible only on disk saturation and is
  counted + logged ERROR.
- FD release on **every** path (success, error, reconnect, shutdown): gzip handle, SQLite/DuckDB conn,
  SDK/WS client, subprocess (log file not PIPE, `wait()`-reaped), threads, queues.
- Teardown drain order: `TickProcessor` fully drains `proc_queue` and flushes its final 1s cycle into
  `db_queue` **before** `SQLiteLiveWriter` finishes; `RawTickFileWriter` drains in parallel. Join order:
  **processor → db_writer**, raw_writer joined alongside.
- Config validation & fast-fail (missing/out-of-range → exit 1, no silent default).
- Startup & mid-day recovery (ATM via REST, resubscribe from `active_subscriptions`, never-shrink,
  SQLite corruption archive+rebuild).
- Uniform-1s resample grid preserved (never varied at runtime — degraded mode skips heavy work but
  keeps the cadence).
- **Docs updated in `Documents/`** — ARCHITECTURE reflects the built state, a dated CHANGELOG entry
  exists for this phase/iteration, and any new/changed module has its per-module doc.

# Documentation (`Documents/`)
Documentation is maintained **from P0 onward** and updated on **every phase completion and every
iteration** (enforced by the workflow step 5 and the Completion Audit above). Location:
`market_depth_recorder\Documents\`.
- `ARCHITECTURE.md` — living architecture: module map, 4-thread/3-queue tee topology, three storage
  tiers, and the design invariants — kept in sync with what is actually implemented (not aspirational).
- `CHANGELOG.md` — dated running log, one entry per phase/iteration: what changed, why, affected files,
  tests added, deferred/remaining work.
- `<module>.md` — per-module reference added as each module lands: responsibilities, public API,
  threads/locks/FDs owned, config keys consumed, and the spec `§` it implements.
Rules: docs describe the **implemented** state and cite the design spec `§`; created at P0 as skeletons
and filled in per phase; when spec and code diverge, fix the code or update these notes — never let the
docs drift silently. `Documents/` is tracked source, not ignored output.

# Decision Rules
When multiple valid implementations exist, prefer in order:
1. Preserve existing architecture / the spec's design.
2. Minimize code changes.
3. Reusable over specialized.
4. Correctness before performance.
5. Explicit over implicit.
6. Ask instead of assuming.

# Module Map & Threading Topology
Nine modules (spec §2.1):
- `config.yaml` — all parameters, thresholds, credentials, and the `underlyings[]` list (§7).
- `main.py` — orchestrator daemon: milestone state machine (09:00→15:35+), thread supervisor,
  teardown drain, health file, end-of-session reprocess launch (§3.1, §6.4).
- `instrument_manager.py` — REST instruments/expiry resolution, strike-step auto-detect (mode), O(1)
  lookup maps, depth-capability preflight (§3.2).
- `websocket_client.py` — raw-WS feed wrapper (**primary/default** — SDK depth callback strips
  `feed_time`/`depth_levels`/`is_50_depth`) + OpenAlgo SDK wrapper (alternate); the Dynamic Strike
  Manager (DSM), reconnect/backoff/resubscribe (`auto_reconnect=False`), never-shrink, `:50` suffix (§3.3, §6.1).
- `processor.py` — 1s resampler + NumPy metric engine (M1–M24, aggregates, regime); thin (live) and
  fat (offline) modes against one schema; degraded-mode backpressure (§3.4, §5.1).
- `database_writer.py` — two writers: `SQLiteLiveWriter` (thin live, per-second commits) and
  `DuckDBAnalyticalWriter` (fat offline bulk load: `executemany`, temp-file-then-rename, `built_by="replay"`) (§3.6).
- `file_writer.py` — thread-safe gzip JSONL Tier-0 logger, flush/fsync cadence, EOF marker; the HEADER
  carries the resolved chain (`instruments`, P7) so replay is self-contained (§3.5).
- `replay.py` — offline raw `.jsonl.gz` → DuckDB rebuild driving the **same** `TickProcessor` off a
  **`recv_ts`** virtual clock (full metric set); reconstructs instruments via
  `InstrumentManager.from_header()` (no REST); `--catchup` self-heal; `--verify` / `--verify-against-live` (§8).
- `utils.py` — math helpers (decay arrays), logging config, time/IST helpers.
- `metrics/registry.py` — declarative metric registry (spec §3.4.0): each metric declares inputs, min-depth,
  output columns, thin/fat eligibility; `live_metrics` is validated against it; adding M30+ is a pure registration.

The folder is renamed to `market_depth_recorder/` (the folder **is** the package); dependencies are a standalone
`requirements.txt` + venv. Four cross-cutting features layered on the spec (all additive, keyed to decisions taken
2026-07-03): the metric registry (above), provenance/versioning (raw HEADER line + `recorder_meta` stamp in both
stores), an operational CLI (`--validate-config`/`--preflight`/`--status`), and session guards (disk-space check +
optional trading-holiday skip). Transport default is **raw** (SDK strips audit fields).

Threading (§5.1): **4 threads / 3 bounded queues**.
```
 WebSocket receiver (SDK callback / raw thread)
        │ tee
        ├── put(timeout) ─► raw_file_queue ─► RawTickFileWriter ─► .jsonl.gz   (Tier 0, audit, protected)
        └── put_nowait ───► proc_queue ─────► TickProcessor (1s) ─► db_queue ─► SQLiteLiveWriter ─► .db (Tier 1, thin)
```
Storage tiers: Tier 0 raw (source of truth) → Tier 1 thin live SQLite/WAL → Tier 2 fat DuckDB, the last
built offline by `replay.py` re-running the same `TickProcessor` with the full metric set.

# Design Invariants (must not break)
- **Genericization contract** — no index/exchange/strike-step literal in engine code; all from
  `underlyings[]`; state keyed by `name`; adding an underlying is a pure config edit.
- **Lossless raw audit** — Tier 0 is 100% of the feed; the only permitted loss is disk saturation
  (counted + logged ERROR). Everything downstream is reconstructable from it.
- **Thin vs fat modes, one schema** — live computes only `recorder.live_metrics` (cheap, `< 15 ms`
  budget); offline replay computes the full §4 catalog. Same code, same tables, different metric set.
- **Never-shrink subscriptions** — once subscribed, a symbol stays until graceful 15:35 shutdown; no
  unsubscribe on pullback, keeping each strike's timeline contiguous.
- **Uniform 1s grid** — the resample interval is never varied at runtime; the resampler runs
  independently of WS state, forward-filling / NULL-padding so the time series has no gaps.
- **Depth preflight & self-describing rows** — auto-detect actual depth per (underlying, exchange);
  store `depth_levels`; never assume 50; NULL deep-book-only metrics where the book is shallower.
- **Replay is the normal Tier-2 path** — the fat store *exists* because of end-of-session replay, not
  as an exceptional recovery tool; it also serves formula changes and backtests.

# Agnosticism — avoid
| Axis | Avoid |
|------|-------|
| Symbol | Hardcoded index/option symbols or symbol-specific branching outside `instrument_manager` maps |
| Exchange | Hardcoded `NSE_INDEX`/`BSE_INDEX`/`NFO`/`BFO` in engine logic — read from `underlyings[]` |
| Broker | Broker/transport specifics leaking past `websocket_client` (SDK vs raw is config only) |
| Metric constant | Any magic number in code — decay, thresholds, windows, watermarks, cadences all from config |

# Proposed Implementation Roadmap
Ordered phases, each independently testable. This is a starting proposal — refine per the workflow
above before implementing any phase.
- **P0 Scaffolding** — **rename folder to `market_depth_recorder/`** (the folder is the package), `config.yaml`,
  config loader + **full §7.3 validation** (fast-fail, exit 1), logging + `utils`, **metric-registry skeleton**,
  `--validate-config`, standalone `requirements.txt`, and the **`Documents/` skeleton** (`ARCHITECTURE.md`,
  `CHANGELOG.md`). *Test:* config validation unit tests (good/bad configs); `--validate-config` exit codes.
- **P1 InstrumentManager** — REST `instruments`/`expiry`, weekly-expiry resolution, strike-step
  auto-detect (mode + validation), O(1) maps, depth preflight (§3.2). *Test:* mocked REST responses.
- **P2 File Writer (Tier 0)** — gzip JSONL writer thread, flush/fsync cadence, EOF marker (§3.5).
  *Test:* write/replay round-trip, crash-truncation tolerance.
- **P3 WebSocket client + DSM** — **raw-WS wrapper (primary)** + SDK wrapper (alternate),
  `subscribe_ltp`/`subscribe_depth`, **tee** into both queues, backoff/reconnect/resubscribe
  (`auto_reconnect=False`), never-shrink, `:50` suffix + preflight gate (§3.3, §6.1).
  *Test:* injected fake feed; reconnect resubscribes full set.
- **P4 Processor (thin live)** — cache ingest, 1s resampler (forward-fill/staleness), per-strike metrics
  + multi-strike aggregates + regime, degraded-mode backpressure (§3.4, §5.1). *Test:* deterministic
  metric fixtures; degraded mode keeps cadence.
- **P5 SQLite Live Writer (Tier 1)** — schema DDL, batched commits, WAL + checkpoint, corruption
  recovery (§3.6, §4, §6.3). *Test:* batch flush timing; corrupt-file archive+rebuild.
- **P6 Orchestrator (`main.py`)** — milestone state machine, thread supervisor (`is_alive` + error
  queue), teardown drain order, health file (§3.1, §6.4). *Test:* simulated clock drives milestones;
  supervisor restarts on injected crash.
- **P7 Replay + DuckDB Writer (Tier 2) — ✅ DONE (2026-07-06).** `replay.py` drives the same
  `TickProcessor` off a **`recv_ts`** virtual clock (full metric set) into `DuckDBAnalyticalWriter`
  (§4.1a DDL, `executemany` bulk, temp-file-then-rename idempotency, `built_by="replay"`); instruments
  reconstructed from the enriched HEADER (`from_header`, no REST); `--catchup` self-heal; `--verify` /
  `--verify-against-live`; robust reader (corrupt-line/missing-EOF/multi-HEADER). The P6 M6 subprocess
  (`--replay --catchup`, log file not PIPE, `wait()`-reaped) now runs a real build (§8, §3.6.5).
  *Verified:* replay determinism (`--verify` clean), perturbed→drift, catchup, against-live subset match,
  warm-up NULLs; end-to-end M6-command subprocess builds the DuckDB store.
- **P8 Offline integration & soak — ✅ DONE (2026-07-06).** The automated whole-pipeline harness
  (`tests/test_integration.py`, `@pytest.mark.integration`): the **real** four-thread
  `_build_default_pipeline` driven by a scripted `RecordedTransport` (NIFTY 50-level / SENSEX 5-level) +
  the **real** `--replay --catchup` subprocess; assertion-backed FD audit (clean joins, HEADER..EOF raw
  log with `instruments` + preserved `feed_time`/`depth_levels`/`is_50_depth`/per-level `orders`, populated
  live store, DuckDB determinism, no `.tmp`/`.building`/`.lock` residue). Adds perf/RSS instrumentation
  (`utils.process_rss_mb` stdlib; `emit_second` `perf_counter` → `cycle_ms_p50/max`; both + `rss_mb` in
  `health.json`/`--status`) and a **SIGTERM** graceful-teardown handler (§3.1.4). Corrected the P6 docs'
  claim of a committed real-four-thread e2e smoke (it was manual). *Verified:* full suite **228 passed**.
- **P9 Live-run session — ⚠️ PARTIAL PASS (2026-07-06).** Ran against a live OpenAlgo + FYERS session.
  Confirmed: chain resolution on the real master; preflight depth NIFTY/NFO→50, SENSEX/BFO→5 with per-level
  `orders`; §9 degrade alarm; Init→Connect→Record + mid-day REST ATM seed; raw audit fields + HEADER
  `instruments`; `cycle_ms_p50=10.5` (<15), `rss=51 MB`, drops=0. Fixed 3 bugs on first live contact
  (descriptive-`name` master match; invalid `heartbeat_timeout>interval`; preflight 5-level inference).
  **Headline finding (cannot be faked):** FYERS TBT caps Market-Depth at **5 symbols** and OpenAlgo pins
  channel `"1"` → 80 NIFTY `:50` legs starved (NIFTY captured 0 depth); SENSEX (non-TBT HSM 5-level)
  fine. **Corrected (P10-F, 2026-07-14): the 5 is per _connection_, not per channel** — channels carry
  no capacity; with 3 connections per app the ceiling is **`tbt_budget = 15`**. Full record:
  `plans/Plan_001_evidence/Phase9_notes.md`; canonical evidence:
  `Documents/evidence/fyers_tbt_concurrency_20260714/tbt_concurrency_reconciliation_20260714.md`. Remaining live checks (full 50-level, global-cap, authoritative
  perf/RSS, graceful teardown) → **P10-E** (next session).
- **P10 Full-chain 50-level + dated storage + EOD report (from the P9 finding).**
  - **P10-A ✅** OpenAlgo channel-spread **patch** (buckets 5/channel across 1–50; the claimed
    *ceiling 250* is **disproven — real ceiling `tbt_budget = 15`**, 3 connections × 5 per connection.
    Patch kept: it fixes the `channel="1"` pin but does not lift the cap) —
    `Documents/evidence/{OPENALGO_PATCH.md,openalgo_fyers_tbt_channels.patch}`. Platform-scope exception,
    user-authorized; takes effect on OpenAlgo restart (→ P10-E smoke).
  - **P10-B ✅** Dated storage inside the package: `output_dir=./market_depth_recorder/data`,
    `date_partitioned: true` → `data/<YYYY-MM-DD>/{raw,live,duckdb,reports}`; ops singletons (health/reprocess)
    stay at base. `utils.session_output_dir`; replay places stores beside the raw.
  - **P10-C ✅** `eod_report.py` + `--eod-report` → dated PASS/WARN/FAIL report (raw/live/duckdb/ops checks);
    exit 0/1. First real run flagged the NIFTY-no-depth gap. `Documents/eod_report.md`.
  - **P10-D ✅** Docs reconciliation (this pass). **P10-E** live validation → next market session.

# Source of Truth & Sync
The design spec governs. When it changes, update this file's invariants, module map, and roadmap to
match. Flag any code that would reduce future extensibility (more underlyings, `processor.mode: process`
sharding, added metric columns) — the architecture is built to scale by config, not rewrite (§5.2).

# Output Style
Explain reasoning briefly, show affected files, keep patches focused, avoid unrelated refactors, and
call out assumptions/tradeoffs/risks. Before a task is complete: existing behavior unchanged unless
requested; meaningful logging; config validated; errors handled explicitly; docs updated if behavior
changes.
