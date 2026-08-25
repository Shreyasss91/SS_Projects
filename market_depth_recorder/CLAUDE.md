# CLAUDE.md

## Project
Standalone, high-throughput **Market Depth Recorder** microservice. It captures real-time option
market depth for the configured weekly chains (initially NIFTY + SENSEX) off the OpenAlgo SDK feed
and persists it through a **three-tier pipeline**: Tier 0 raw `.jsonl.gz` (lossless source of truth) →
Tier 1 thin live SQLite/WAL (small `live_metrics` subset, written during market hours) → Tier 2 fat
DuckDB analytics (full metric catalog, rebuilt offline by replaying Tier 0). It is config-driven and
broker/exchange/symbol-agnostic. Full detail lives in the design spec (see Scope); read `§`s from it,
never memory.

## Scope
- Project folder: `market_depth_recorder\`. Edit only inside it — never touch `trading_engine\`, the
  repo root, or sibling projects.
- **Source of truth (authoritative):** the in-folder design spec
  `market_depth_recorder_design.md` (this folder). When code and this file disagree with the spec, the
  spec wins; keep `PROJECT_NOTES.md` in sync. (A stale copy exists under
  `..\trading_engine\...\LLM_Spec_Chat\` — ignore it; the in-folder copy is canonical.)
- Ignore unless explicitly requested: `data/**`, `*.jsonl.gz`, `*.db`, `*.db-wal`, `*.db-shm`,
  `*.duckdb`, `*.log`, `__pycache__/**`. Source and config only.

## Workflow (full detail in `PROJECT_NOTES.md`)
For any non-trivial task: clarify scope first → wait for **"let's write the plan"** → phased plan →
implement one phase → **update the docs** → stop for approval. No silent scope creep, no large rewrites
without sign-off.

**Plan-doc is live, not write-once.** The **only authoritative** implementation plan lives at
`plans\Plan_001_market_depth_recorder_implementation.md` (in this folder, version-controlled with the
code). The former `$home\.claude\plans\refer-market-depth-recorder-design-md-an-peppy-dolphin.md` is a
pointer stub as of 2026-08-25 — never read or edit it. Keep the plan in sync
with reality: (a) when the user answers a decision fork, record the decision + rationale in the plan's
Locked-decisions/forks section; (b) before implementing a phase, embed its exhaustive subtask checklist
there; (c) as each subtask/phase completes, tick its checkbox in the plan doc. This runs alongside the
`Documents/` updates — the plan tracks *progress*, `Documents/` tracks the *implemented state*.

## Documentation (maintained from day one)
Documentation is a first-class deliverable, not an afterthought — it starts at P0 and lives in
`market_depth_recorder\Documents\`. **On every phase completion and every iteration, update the docs as
part of the Completion Audit** (a phase is not "done" until its docs are current). Keep at minimum:
- `Documents\ARCHITECTURE.md` — living architecture (modules, threading/queue topology, storage tiers,
  invariants) that tracks what is actually built.
- `Documents\CHANGELOG.md` — dated running log; one entry per phase/iteration (what changed, why,
  affected files, deferred work).
- `Documents\<module>.md` — per-module reference (responsibilities, public API, threads/locks/FDs owned,
  config keys consumed) added as each module lands.
Docs describe the **implemented** state and cite the design spec `§`; when the spec and code diverge,
fix the code or update `PROJECT_NOTES.md` — never let the docs drift silently.

## Implementation Discipline
- Modify, don't lose — never drop or silently remove existing functionality while editing.
- Edit, don't corrupt — preserve the logic of working code; don't reshape behavior outside the request.
- Go incrementally — one change at a time, verifiable as you go. No hurried multi-concern edits.
- If genuinely unsure mid-implementation, stop and ask — don't guess and proceed.

## Reading the Spec / Large Files
The design spec is ~1450 lines. Grep for the relevant `§`/symbol first, then read only that range with
`offset`/`limit`. Never read the whole spec (or any >300-line file) unless the task needs full-file context.

## Config over Hardcoding — Genericization Contract
No index name, exchange code, or strike step ever appears as a literal in engine code — all three come
from `underlyings[]` in `config.yaml`. Per-underlying state (strike maps, boundaries, subscriptions,
rows) is keyed by `name`; loops iterate `underlyings`, never branch on `NIFTY`/`SENSEX`. Every magic
constant (decay, thresholds, windows, watermarks, cadences) resolves from config — a missing or
out-of-range value **fast-fails at startup with exit code 1**, never a silent default.

## Concurrency — High Risk
Before touching threaded code, name: thread owner · lock owner · state owner.
- Four threads / three bounded queues. The feed receiver **tees** each packet with **two `put`s** —
  one to `raw_file_queue` (audit), one to `proc_queue` (analytics). Never let audit and analytics read
  the same queue: a single `queue.Queue` delivers each item to exactly one consumer, so they would each
  see only half the ticks.
- Lock all reads AND writes of shared state (`active_subscriptions`, `current_spot_prices`). Lock order
  is always `spot_lock → RLock`. Never do network/file I/O inside a lock. `connect()`/`disconnect()`
  are FEED-thread-only and deliberately not under `client_lock`.

## Data Integrity (the recorder's "trading safety")
The raw audit path is **lossless**. A raw packet is dropped **only** on genuine disk saturation, and
every such drop is counted and logged at ERROR — this is the single explicit exception. Under overload,
`proc_queue` (analytics) sheds first, then `db_queue`; `raw_file_queue` sheds last. Both derived stores
(live SQLite, fat DuckDB) are reconstructable from Tier 0, so never treat them as irreplaceable — but
never silently violate the raw guarantee either.

## FD Hygiene
Every gzip handle, SQLite/DuckDB connection, WS/SDK client, ZeroMQ or subprocess pipe, thread, and
queue is a file descriptor. Use shared singletons and `with`/close on every path (success, error,
reconnect, shutdown). WS adapter closes-before-reconnect. The end-of-session reprocess runs as a
**subprocess whose stdout/stderr go to a log file (never a PIPE)** and is `wait()`-reaped. After any
change touching files/sockets/threads/subprocess/DB, run a focused FD audit before calling it done.

## Recovery
Assume the process can crash at any line. On mid-day restart, resolve the current ATM via one REST
quote per underlying (don't wait for WS), then subscribe. On reconnect, resubscribe every symbol from
`active_subscriptions` (never-shrink: subscriptions are only reset at graceful 15:35 shutdown). On
SQLite corruption, archive the file (+`-wal`/`-shm`) and create a fresh DB — the fat store is rebuilt
from the untouched raw log regardless.

## Depth Reality
Never assume 50-level depth. True 50-level is FYERS TBT, restricted to NSE/NFO — so NIFTY/NFO → 50 but
SENSEX/BFO falls back to 5. Auto-detect the actual level per symbol via the startup preflight, store a
self-describing `depth_levels`, and emit deep-book-only metrics as `NULL` where the book is shallower
than the metric requires. **Authoritatively established & FROZEN (official FYERS TBT docs + single-connection
probe + multi-connection probe + both raws re-read + OpenAlgo code comparison; 2026-07-14, P10-E/P10-F):**
FYERS TBT caps at **5 Market-Depth symbols per _connection_** (not per channel), with **3 connections per app
per user** and **50 channels per connection**. Channels are a **pause/resume logical grouping, not extra
capacity**. Three independent connections **do** combine: **`tbt_budget = 15` (3 × 5)** — confirmed live
(15/15 distinct legs concurrent; a 4th connection refused). A full NIFTY chain at 50-level is **not**
achievable on one connection (only 5 legs stream); reaching 15 needs the **hybrid** (near-ATM @50 + rest @5)
over a multi-connection broker layer. The earlier "5/channel × 50 = 250" assumption and the P10-E "full 80-leg
chain streamed" reading are **disproven** (the latter was an interpretation artifact — the Jul-07 raw itself
never streamed >5 concurrent; TBT code was byte-identical across the intervening upgrade); channel ids must be
**strings** (`"1"`). **Architecture rule:** `tbt_budget = 15` is a **confirmed FYERS broker _capability_, not
an architectural constant** — the TBT Allocator consumes **one logical `tbt_budget`** exposed by the
broker-capability layer, and connection management (3 × 5) stays hidden behind it, so the engine is
broker-agnostic (another broker may expose `1×20`, `5×10`, or full-chain-50 — only the capability config
changes, never the allocator). **This protocol layer is FROZEN unless new external evidence emerges** — do not
revisit the FYERS TBT assumptions without it. Canonical evidence + reconciliation:
`Documents/patches/tbt_concurrency_reconciliation_20260714.md`; see also `OPENALGO_PATCH.md` §8 and the probes
`tools/fyers/tbt_channel_probe.py` / `tools/fyers/tbt_multiconn_probe.py`.

## Before Proposing Code
Verify: lock correctness & thread ownership · execution order · failure paths (reject/timeout/
reconnect/restart/shutdown/duplicate-event) · teardown drain order · startup & mid-day recovery ·
config validation · FD release on every path · lossless-raw invariant preserved · uniform-1s grid
preserved. If anything can't be verified, say so explicitly. Full checklist: `PROJECT_NOTES.md`.

## Testing
All business logic must be testable without a live broker/WebSocket/market feed — inject the clock,
feed, and writers. Replay from the raw `.jsonl.gz` is the determinism harness (same `TickProcessor`,
simulated clock); `--verify` diffs a rebuild against a reference to catch non-determinism.

## graphify
No knowledge graph exists yet. Run `graphify .` to build `graphify-out/` once there is code, then for
codebase questions use `graphify query "<q>"`, `graphify path "<A>" "<B>"`, `graphify explain "<c>"`
before raw grep, and `graphify update .` after modifying code.
