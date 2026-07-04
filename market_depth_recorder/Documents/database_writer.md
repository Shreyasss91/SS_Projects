# `database_writer.py` — store writers (§3.6)

Two writers, one logical schema (§4), different backends. **P5 builds `SQLiteLiveWriter`** (the live
Tier-1 path); `DuckDBAnalyticalWriter` (offline Tier-2 fat store, §3.6.5) is a **deferred P7 stub**.

## Responsibility

`SQLiteLiveWriter` is the **fourth and final live thread** and the first reader of `db_queue`. It drains
the per-second row envelopes emitted by `TickProcessor` and batch-commits the `recorder.live_metrics`
subset to the thin Tier-1 SQLite/WAL store `market_depth_live_YYYYMMDD.db` (§4.1). Small, frequent WAL
commits are exactly SQLite's strength, so the live path never blocks the pipeline. It is a pure queue
consumer over one SQLite connection — **no sockets, subprocess, or compute**. It never touches the raw
audit path; live-store corruption is non-fatal (the fat store rebuilds from the untouched raw log, §6.3).

## Public API

### `SQLiteLiveWriter(config, db_queue, shutdown_event, session_date, *, schema_version=SCHEMA_VERSION, time_fn=time.time, error_queue=None, name="SQLiteLiveWriter")`
`threading.Thread` subclass (daemon). Constructor reads from `config`: `recorder.output_dir`,
`database.{batch_size, batch_write_interval_ms, cache_size_mb, wal_checkpoint_interval_sec}`, and
`config_hash`. `db_queue` + `shutdown_event` are owned by the P6 orchestrator and injected. `session_date`
(a `datetime.date`, from `now_ist().date()`) resolves the DB filename once. `time_fn` is the injected
clock — the single source of the commit/checkpoint cadence, `recorder_meta.build_time`, and the rollover
date — so every time branch is deterministic under test.

- `run()` — open DB (recover-if-corrupt → PRAGMA → DDL+provenance-if-new) → drain `db_queue` until
  `shutdown_event` is set **and** the queue is empty → final commit + teardown PRAGMAs on clean drain →
  close the connection on **every** path (hardened so a *partial* open still closes its FD).
- `mark_restart_boundary(boundary_ts: int)` — **called by the P6 orchestrator** (not the writer thread)
  after a mid-day restart so the single overlap second's commit uses `INSERT OR REPLACE` (§4.3 / fork A);
  the writer reverts to `INSERT OR IGNORE` once it has flushed at/past that second. A lone attribute
  assignment is atomic under the GIL → no lock needed.
- `SQLiteLiveWriter.resolve_filename(output_dir, d) -> str` — staticmethod; the daily live-DB path.
  Reused by the orchestrator.
- Health counters (read by P6 / tests): `rows_written`, `rows_ignored_total` (PK collisions),
  `commit_error_count`, `corruption_recoveries`, `unknown_table_total`.

### `DuckDBAnalyticalWriter(...)` — deferred (P7)
Construction raises `NotImplementedError`. The offline fat-store bulk-load body (§3.6.5) lands in P7.

## Input contract (`db_queue`)

One envelope per table per second: `{"table": <name>, "rows": [tuple, …]}`. Tuples are in **exact §4.1
column order**, guarded metrics `None`; the DB `symbol` has no `:50` suffix (the processor stripped it).
The four table→column tuples are **imported from `processor`** (`SPOT_COLUMNS`, `OPTION_COLUMNS`,
`STRIKE_WINDOW_COLUMNS`, `AGG_COLUMNS`) so the `INSERT` statements can never drift from the emitted order
(decision 49). An unknown `table` is counted (`unknown_table_total`) + logged, never fatal.

## Store layout (§4)

- **Four tables** (§4.1): `spot_states` + `aggregated_window_metrics` are `WITHOUT ROWID` (narrow);
  `option_strike_metrics` + `strike_window_metrics` are ROWID tables (wide — §4.3). Compound PKs as listed.
- **Secondary indexes** (§4.2): `idx_osm_strike`, `idx_osm_ts`, `idx_swm_symbol`, `idx_spot_ts`.
- **`recorder_meta`** (§4.1b): one provenance row stamped at DB creation — `schema_version`, `config_hash`,
  `built_by="live"`, `build_time`, `source_raw=NULL`. Mirrors the raw file's HEADER; `--verify` (P7) uses
  it to refuse mismatched-schema diffs. Not re-stamped on a same-day reopen.

## Batch / commit engine (§3.6.1)

Per-table in-memory buffers accumulate rows; `_maybe_flush()` commits when the total buffered rows reach
`database.batch_size` **or** `database.batch_write_interval_ms` has elapsed since the last commit (the time
trigger fires even while the queue is idle). One transaction per commit
(`BEGIN` → `executemany` per non-empty table → `COMMIT`); the connection is opened with
`isolation_level=None` (autocommit) so transactions are managed explicitly. PK-collision drops (steady-state
`INSERT OR IGNORE`) are counted via the `total_changes` delta and logged. A `sqlite3.Error` rolls the
transaction back and drops the batch with a count — **no poison-batch retry** (the fat store rebuilds from
raw regardless).

## PRAGMA tuning + maintenance (§3.6.2 / §4.4)

- Open: `journal_mode=WAL`, `synchronous=NORMAL`, `temp_store=MEMORY`,
  `cache_size=-(cache_size_mb × 1000)` (negative → KiB).
- Periodic: `PRAGMA wal_checkpoint(PASSIVE)` every `wal_checkpoint_interval_sec` to bound the `-wal`.
- Teardown (§4.4, authoritative over §3.6.4's shorter list): `PRAGMA wal_checkpoint(TRUNCATE)` +
  `PRAGMA optimize`. **No `VACUUM`** — the file is written append-mostly, once, rotated daily; VACUUM would
  cost ~2× disk and minutes for no query benefit.

## Corruption recovery (§6.3)

On open, `PRAGMA quick_check` probes the file (a `DatabaseError` counts as corrupt; a fresh file passes
trivially). On failure: close the bad connection → archive the `.db` (+ its `-wal`/`-shm`) to
`.corrupt_<epoch>.bak` → reconnect to a fresh file → recreate schema + `recorder_meta` → log **CRITICAL** →
`corruption_recoveries += 1`. Non-fatal to the catalog.

## Daily selection + defensive rollover (§3.6.3)

The DB is resolved once from `session_date`; the bounded ~09:00→15:35 session never crosses midnight, so
there is no normal rollover. A defensive `_maybe_rollover` (compared in **IST**, matching `session_date`'s
basis) fires only if an unusually long-lived process sees the date change: final-flush → teardown → close →
open the new-dated DB. Never fires in a normal session.

## Threads / locks / FDs

- **Thread owner:** the single `SQLiteLiveWriter` thread (`run()`).
- **State owner:** that same thread owns the connection, per-table buffers, counters, and `_current_date` —
  **no lock** (single owner, decision 48). The one deliberate cross-thread field is `_boundary_ts`, written
  by the P6 orchestrator via `mark_restart_boundary` and read here (atomic single-word assignment). Counters
  are monotonic ints read by the P6 health file.
- **FD owner:** the one `sqlite3.Connection` (+ its `-wal`/`-shm` sidecars). Opened in `run()` and closed
  in `run()`'s `finally` on every path (clean drain, exception, shutdown, corruption-rebuild, rollover);
  corruption recovery closes the bad connection before reconnecting. The DuckDB stub holds nothing.
- Cross-thread edges: only the thread-safe `db_queue` (in) and the atomic boundary hand-off.

## Config keys consumed

`recorder.output_dir`; `database.batch_size` (∈ [1,5000]), `database.batch_write_interval_ms` (∈ [500,5000]),
`database.cache_size_mb` (≥ 1), `database.wal_checkpoint_interval_sec` (≥ 30) — all §7.3-validated at
startup (fast-fail, exit 1). `config_hash` (for the provenance stamp).

## Genericization

No index/exchange/strike/CE-PE literal appears — table and column names are the §4 schema constants;
symbols and underlyings flow through from the envelopes.
