# Architecture — Market Depth Recorder

Living architecture doc. Tracks **what is actually built**, not the aspiration. Cites the design spec
`market_depth_recorder_design.md` (§) as the authority.

## What this service is

A standalone, config-driven microservice that captures real-time option market depth for the
configured weekly chains (initially NIFTY + SENSEX) off OpenAlgo and persists it through a
**three-tier pipeline** (§2.1):

- **Tier 0 — raw `.jsonl.gz`** (lossless source of truth; every packet, exchange-timestamped).
- **Tier 1 — thin live SQLite/WAL** (`recorder.live_metrics` subset, written during market hours).
- **Tier 2 — fat DuckDB analytics** (full §4 catalog, rebuilt offline by replaying Tier 0).

Both derived stores are reconstructable from Tier 0 (§2.1), so neither is a single point of loss.

## Package layout (§2.1)

The folder **is** the Python package; run it from the parent `SS_Projects/` with
`python -m market_depth_recorder …`.

```
market_depth_recorder/
├── __init__.py            # package marker; __version__, SCHEMA_VERSION=1  [P0 ✅]
├── __main__.py            # CLI surface (§8.2); --validate-config wired, rest stubbed  [P0 ✅]
├── config.py              # loader + full §7.3 validation, config_hash, frozen Config  [P0 ✅]
├── utils.py               # logging, IST/time, decay weights, atomic write, disk free  [P0 ✅]
├── config.yaml            # §7.1 template, materialized verbatim  [P0 ✅]
├── requirements.txt       # standalone pins (openalgo exact; rest ~=)  [P0 ✅]
├── metrics/
│   ├── __init__.py        # metric layer marker  [P0 ✅]
│   └── registry.py        # declarative M1–M29 + rolling + aggregate/regime metadata (§3.4.0)  [P0 ✅]
├── instrument_manager.py  # REST instruments/expiry, weekly-expiry, strike-step, O(1) maps (§3.2)  [P1 ✅]
├── file_writer.py         # Tier-0 gzip JSONL writer thread (§3.5)  [P2 ✅]
├── websocket_client.py    # raw-WS transport (primary), DSM, tee, reconnect, depth preflight (§3.3)  [P3 ✅]
├── processor.py           # 1s resampler + NumPy metric engine, thin/fat modes (§3.4)  [P4 ✅]
├── database_writer.py     # SQLiteLiveWriter (Tier 1, built P5) + DuckDBAnalyticalWriter (Tier 2, P7 stub) (§3.6)  [P5 ✅]
├── main.py                # orchestrator daemon, milestones, supervisor, teardown, health, reprocess (§3.1)  [P6 ✅]
├── replay.py              # offline raw → DuckDB rebuild, recv_ts clock, --catchup/--verify (§8)  [P7 ✅]
├── eod_report.py          # EOD health/sanity checks + dated report, --eod-report (§8.2)  [P10-C ✅]
├── Documents/             # this living doc set (incl. operator_notes.md, LIVE_RUN.md, phase_10E_notes.md)
├── tests/                 # pytest suites — no live feed needed
└── data/                  # runtime artifacts (gitignored); base = ops singletons, dated subdirs = data
```

**Storage layout (P10-B).** `recorder.output_dir` is `./market_depth_recorder/data` (inside the package).
With `recorder.date_partitioned: true`, each day's **data** is grouped in a dated sub-folder while
**operational singletons stay at the base** (so `--status` / the run-lock stay date-agnostic):
```
data/
├── health.json                 # liveness (base, un-dated)
├── reprocess.log / .lock        # reprocess ops (base, un-dated)
└── 2026-07-06/                  # one dated sub-folder per trading day (date also in filenames)
    ├── market_depth_raw_20260706.jsonl.gz      # Tier 0
    ├── market_depth_live_20260706.db(+wal/shm)  # Tier 1
    ├── market_depth_analytics_20260706.duckdb   # Tier 2 (built beside its raw)
    └── reports/                                  # P10-C EOD reports
```
Replay/`catchup` resolve the DuckDB/live paths **beside the raw log**, so the layout is
flat/partitioned-agnostic (`utils.session_output_dir`).

As of **P7 both tiers are complete**: the live pipeline (P0–P6) writes Tier 0 + Tier 1, and the offline
`replay.py` rebuilds the fat Tier-2 DuckDB store from Tier 0 through the same `TickProcessor`. **P8** added
the automated soak harness; **P9** was the live run (partial pass — surfaced the FYERS TBT 5-symbol cap,
see `Documents/patches/Phase9_notes.md`); **P10** followed from it — **A** the OpenAlgo channel-spread
patch (`Documents/patches/OPENALGO_PATCH.md`), **B** dated storage inside the package, **C** the
`eod_report.py` EOD health/sanity tool. **P10-E** ran the live validation and **P10-F** then corrected it.

> **Depth-capacity reality (P10-F, 2026-07-14; FROZEN).** The cap is **5 Market-Depth symbols per
> _connection_**, not per channel — the P9/P10-E "5 per channel × 50 channels = 250" reading is
> **disproven**, and P10-E's "full chain streams" conclusion was a measurement artifact (the raw never
> showed >5 concurrent NFO legs). With **3 connections per app**, the confirmed ceiling is
> **`tbt_budget = 15`**. The channel-spread patch is kept (harmless, correct plumbing) but buys 15, not
> 250. **A full NIFTY chain at 50-level is therefore not achievable**: the recorder subscribes all ~82
> legs at `:50` and only ~5 stream. SENSEX (BFO, non-TBT) is unaffected and streams its whole chain at
> 5-level. The **hybrid** (near-ATM @50 within `tbt_budget`, rest @5) is the design and is **not yet
> built** — deferred to the framework effort, where `tbt_budget` is consumed as a broker **capability**
> so the engine stays broker-agnostic. Canonical:
> `Documents/patches/tbt_concurrency_reconciliation_20260714.md`.

## Threading & queue topology (§5.1) — full live pipeline built + orchestrated (P6)

**4 worker threads / 3 bounded queues / 2 shutdown events**, all constructed·started·supervised·joined
by the **main (orchestrator) thread** (P6). The feed receiver **tees** each packet with two independent
`put`s.

```
 main thread — RecorderOrchestrator: milestone loop, supervisor, health, teardown, reprocess   [P6 ✅]
   builds & owns → 3 queues + shutdown_event (feed·proc·raw) + db_shutdown_event (db) + error_queue

 FEED thread — RawWSTransport.run_forever receive loop + DSM + reconnect   [P3 ✅]
        │ tee (no lock, returns immediately)
        ├── put(timeout) ─► raw_file_queue ─► RawTickFileWriter ─► .jsonl.gz   (Tier 0, audit, protected)  [P2 ✅]
        └── put_nowait ───► proc_queue ─────► TickProcessor (1s) ─► db_queue ─► SQLiteLiveWriter ─► .db (Tier 1)  [P4/P5 ✅]
```

`RawTickFileWriter` (P2) drains `raw_file_queue` and owns the Tier-0 gzip handle exclusively. The
**FEED thread** (P3) is the producer. The `proc_queue → TickProcessor → db_queue → SQLiteLiveWriter`
analytics stages (P4/P5) turn each second into the four §4.1 row families and commit the thin subset.
The **orchestrator** (P6) is the conductor: it creates the queues + events, constructs the four workers,
starts consumers before the producer, runs the 1-second milestone loop, and drains + joins on teardown.

**Two shutdown events (P6, §3.1.4).** `shutdown_event` stops feed·processor·raw together;
`db_shutdown_event` stops the **db writer separately** so teardown joins the processor first (draining
`proc_queue` and flushing its final rows into `db_queue`) and only *then* signals the db writer —
otherwise both could observe the shared event set with `db_queue` momentarily empty and the db writer
could exit before the processor's final rows arrive. Join order: `feed → processor →` (set
`db_shutdown`) `→ db_writer → raw_writer`, each `join(timeout=10)`.

**Locks (P3, §3.3.3):** `_spot_lock` (spot cache + 10-tick median deque + boundaries), `_sub_lock`
(RLock, the never-shrink `_subscriptions` map), `_client_lock` (serializes sends into the transport).
Lock order `_spot_lock → _sub_lock` (never held together — subscription I/O happens after the spot
lock is released); `connect`/`disconnect` are FEED-thread-only and not under `_client_lock`; the tee
takes no lock; no I/O under any lock.

Backpressure shed order under overload: `proc_queue` (analytics) first → `db_queue` → `raw_file_queue`
last; a raw drop happens **only** on genuine disk saturation and is counted + logged ERROR (§1.4/§5.1).
On the write side, `RawTickFileWriter` treats a serialization/disk-write failure as that single
sanctioned boundary — counted (`write_error_count`) + logged ERROR, thread survives.

## Transport (locked decision, §3.3.1)

Default transport is **raw WebSocket** (primary), built in P3 as `RawWSTransport` on `websocket-client`
(`run_forever(ping_interval, ping_timeout)` for native heartbeat). The OpenAlgo SDK depth callback
strips `feed_time`/`depth_levels`/`is_50_depth`/`total_*_qty` (SDK `feed.py:456-467`) that the proxy
sends on the wire (`server.py:1821-1827`), so only raw preserves the recorder's self-describing,
exchange-timestamped audit. The transports sit behind a `FeedTransport` seam selected by
`websocket.transport`; **`SdkTransport` is a deferred stub** (P3, plan decision 20) that fails fast with
a clear message if selected — it will be built against the same seam later (with `auto_reconnect=False`,
the recorder owns reconnect/resubscribe).

## Cross-cutting features layered on the spec (all additive)

- **Metric registry** (`metrics/registry.py`, §3.4.0) — declarative; `live_metrics` validated against it.
- **Provenance + versioning** — `SCHEMA_VERSION` + `config_hash` in the raw HEADER line (§3.5.4) and both
  stores' `recorder_meta` (§4.1b). `config_hash` implemented in P0; the **raw HEADER/EOF stamp lands in
  P2** (`file_writer.py`); the stores' `recorder_meta` stamps land with the DB writers (P5/P7).
- **Operational CLI** — `--validate-config` (P0), `--preflight` (P3, offline chain resolution **plus**
  the live raw-WS depth probe; unreachable WS degrades gracefully to exit 0), `--status` (P6, pretty-prints
  `health.json`), and the `default` live-recorder entry → `RecorderOrchestrator.run()` (P6).
- **Session guards** — disk-space check + optional trading-holiday skip (§3.1.5); config keys validated in
  P0, **enforced by the orchestrator in P6** (startup + periodic disk ERROR; non-trading-day idle).

## Invariants (guard every phase)

- **Lossless raw** — Tier 0 is 100% of the feed; only permitted loss is disk saturation (counted + ERROR).
- **Genericization** — no index/exchange/strike-step literal in engine code; state keyed by `name`.
- **Uniform 1s grid** — never varied at runtime (degraded mode skips work, keeps cadence).
- **Never-shrink subscriptions** — until graceful 15:35 shutdown.
- **FD hygiene** — shared singletons, `with`/close on every path; subprocess logs to file, `wait()`-reaped.

## Built state (P0)

Scaffolding, config (loader + full §7.3 validation, fast-fail exit 1, `config_hash`), utils, the
declarative metric-registry skeleton (M1–M29 + rolling + aggregates + regime, **metadata only**), the
CLI surface (`--validate-config` wired end-to-end, rest stubbed with clean exits), standalone
`requirements.txt`, and this doc set. No live feed, no threads, no I/O pipeline yet — those start at P1.

## Built state (P1)

`instrument_manager.py` — the first live module (REST, still no threads/DB/sockets). `RestClient`
(stdlib `urllib`; instruments GET + expiry POST; 10 s timeout, ≤3 retries on network/5xx, 4xx
terminal) and `InstrumentManager` (weekly-expiry via the authoritative expiry endpoint, per-underlying
instrument filter with `name`/longest-prefix disambiguation, mode-based strike-step detection with a
warned config fallback, and the O(1) `strike_to_symbol_map` / `symbol_to_strike_map` /
`active_strikes_list` / `tick_size_map`). `--preflight` is wired to resolve every chain offline and
report the planned near-ATM probe strike per underlying (`actual_depth` pending the P3 raw-WS probe).
The only FD is a transient HTTP connection, closed on every path. See `instrument_manager.md`.

## Built state (P2)

`file_writer.py` — `RawTickFileWriter(threading.Thread)`, the first background writer and the first
thread in the pipeline. Drains `raw_file_queue`, serializes each packet to a JSONL line, and appends it
to the daily gzip log with a self-describing HEADER (open) + EOF (clean drain) provenance line stamping
`SCHEMA_VERSION`/`config_hash`/underlyings (§3.5.4). Two-tier flush (cheap `flush()` at
`flush_max_records`; bounded `os.fsync()` every `fsync_interval_sec`, §3.5.3). Single-owner gzip handle
(no lock), closed on every path via a guarded `finally`. Lossless-raw boundary: a serialization/disk
write failure is counted + ERROR-logged and the thread survives (§1.4). A defensive IST-based daily
rollover guard exists but never fires in a normal session. Still no sockets/DB/subprocess; the queue,
tee, and clock are injected by tests. See `file_writer.md`.

## Built state (P3)

`websocket_client.py` — `DepthWebSocketClient(threading.Thread)`, the first **networked** module and the
tick producer. Owns: (1) the **transport seam** — `RawWSTransport` on `websocket-client` (default,
native ping heartbeat) behind a `FeedTransport` protocol, with a deferred `SdkTransport` stub; (2) the
**DSM** (§3.3.2) — spot LTP validation (drop ≤0 and >2%-vs-10-tick-median spikes), lazy boundary
seeding, breach expansion, and strike selection via the P1 `strike_to_symbol_map`; (3) the **tee**
(§5.1) — `proc_queue.put_nowait` (sheds first, WARNING+count) then
`raw_file_queue.put(timeout)` (sheds last, ERROR+`raw_dropped_total`, the single sanctioned raw-loss
boundary); (4) the recorder-owned **reconnect** state machine (§6.1) — exponential backoff + resubscribe
every symbol in the **never-shrink** `active_subscriptions`; (5) the live **depth preflight**
(§3.2.5/§9) — `run_depth_preflight()` subscribes one `:50` depth per underlying's near-ATM probe strike,
reads actual `depth_levels`/`is_50_depth`/per-level `orders`, logs the consolidated line + a WARNING on
`actual < requested`. The only FD is the WS socket, closed on every path (drop, reconnect, shutdown,
preflight probe); close-before-reconnect holds. `--preflight` re-pointed from P1's offline-only resolve
to include this live probe (graceful-degrade to exit 0 when the WS is unreachable, plan decision 30).
Tests inject a fake transport + queues + clock + `sleep_fn` — no live feed. See `websocket_client.md`.

## Built state (P4a + P4b)

`processor.py` — `TickProcessor(threading.Thread)`, the compute core and the **third pipeline thread**.
It drains `proc_queue` into a `latest_ticks` cache and, on each clock-aligned 1-second boundary, fires
the pure `emit_second(now_epoch)` (the P7 replay seam) which builds a `BookSnapshot` per active option
strike, runs the bound metric bodies in dependency order — **per-strike (§3.4.2) → rolling windows
(§3.4.3) → multi-strike aggregates + regime (§3.4.4)** — and pushes **all four §4.1 tables** as row
envelopes (`{"table", "rows"}`, §4.1 column order) to `db_queue`: `spot_states`, `option_strike_metrics`
(incl. the back-filled instantaneous `ofi`), `strike_window_metrics` (one row per `(symbol, w)`), and
`aggregated_window_metrics` (one row per `(underlying, SMALL/MEDIUM/LARGE)`). Uniform 1-second grid
(§6.2): forward-fill from the last packet, staleness → NULL/NaN rows (`confidence=0.0`), degraded mode
preserves cadence (level ≥ 1 NULLs the heavy rolling reductions). **Single-owner state → no lock**
(decision 33); **holds no FDs** (only queues, NumPy arrays, `deque`s). The metric layer: `metrics/
registry.py` provides `bind(name)` + `resolve_active()` + `active_columns()`; `metrics/snapshot.py` holds
`BookSnapshot`/`MetricContext`/`StrikeHistory` (P4a) + `WindowSample`/`StrikeFeatures`/`TouchBook` (P4b);
`metrics/per_strike.py` implements M1–M29, `metrics/rolling.py` the §3.4.3 window bodies + OFI/ΔQ helpers,
`metrics/aggregate.py` the §3.4.4 aggregates + regime + the `compute_underlying` orchestrator (all bound
at import). Thin (live) vs fat (offline) is a pure selection over `METRIC_FUNCS`; dependency closure
(decision 37) computes unpersisted prerequisites when a dependent is active. See `processor.md` +
`metrics.md`.

### Thread / queue topology (after P4b)
```
FEED thread (DepthWebSocketClient) ──tee──► raw_file_queue ──► RawTickFileWriter thread ──► .jsonl.gz
                                     └─────► proc_queue ──────► TickProcessor thread ──► db_queue ──► [P5 SQLiteLiveWriter]
```
The `TickProcessor` now emits the full four-table §4.1 catalog. Three of the four §5.1 threads exist
(FEED, raw writer, processor); the DB writer (P5) and the orchestrator (P6) close the pipeline.

## Built state (P5)

`database_writer.py` — `SQLiteLiveWriter(threading.Thread)`, the **fourth and final live thread** and the
first reader of `db_queue`. It drains the per-second `{"table","rows"}` envelopes and batch-commits the
`recorder.live_metrics` subset to the thin Tier-1 store `market_depth_live_YYYYMMDD.db` (§4.1). On open it
resolves the DB from `session_date`, runs `PRAGMA quick_check` and — on corruption — archives the bad file
to `.corrupt_<epoch>.bak` and rebuilds a fresh one (§6.3, non-fatal since the fat store rebuilds from raw),
applies WAL PRAGMA tuning (§3.6.2), and creates the four tables + secondary indexes (§4.2) + a one-row
`recorder_meta` provenance stamp (`built_by="live"`, §4.1b) when the file is new. It accumulates per-table
buffers and commits in one transaction when the buffer reaches `database.batch_size` rows **or**
`batch_write_interval_ms` elapses (§3.6.1), using `INSERT OR IGNORE` (counting PK-collision drops) in steady
state and `INSERT OR REPLACE` for the single restart-boundary second flagged by the P6-driven
`mark_restart_boundary(ts)` hook (§4.3). A PASSIVE WAL checkpoint runs on a time cadence
(`wal_checkpoint_interval_sec`, §4.4); teardown runs `wal_checkpoint(TRUNCATE)` + `optimize` (no VACUUM).
Column order is imported from `processor` (single source of truth). **Single-owner connection → no lock**
(decision 48); the **one FD** (the `sqlite3.Connection`) is opened in `run()` and closed in `run()`'s
`finally` on every path (clean drain, exception, shutdown, corruption-rebuild, defensive date-rollover).
`DuckDBAnalyticalWriter` is a deferred P7 stub (raises `NotImplementedError` at construction). Health
counters (`rows_written`/`rows_ignored_total`/`commit_error_count`/`corruption_recoveries`) are exposed for
the P6 health file. See `database_writer.md`.

### Thread / queue topology (after P5)
```
FEED thread (DepthWebSocketClient) ──tee──► raw_file_queue ──► RawTickFileWriter thread ──► .jsonl.gz  (Tier 0)
                                     └─────► proc_queue ──────► TickProcessor thread ──► db_queue ──► SQLiteLiveWriter thread ──► .db  (Tier 1, WAL)
```
All **four** §5.1 live threads now exist (FEED, raw writer, processor, DB writer) and the live path is
complete end-to-end. The P6 orchestrator (below) constructs the queues, launches + supervises the four
threads, drives milestones + mid-day recovery, writes the health file, and manages the teardown drain.

## Built state (P6)

`main.py` — `RecorderOrchestrator`, the **conductor**, driven by the `default` (no-mode) CLI entry. It
owns the §3.1.1 milestone state machine + 1-second loop, the three queues / two shutdown events /
`error_queue`, and the construction·start·supervision·teardown of all four worker threads.

- **Milestones (decision 56, act-at-launch).** Init (resolve chains once) → Connect (build + start the
  pipeline immediately, feed subscribes spot LTPs) → Record at `session_start` → Close at `session_end`
  (freeze the DSM — never-shrink holds, no unsubscribe) → Teardown at `session_end + teardown_grace_min`
  → Reprocess after a clean EOF. A launch inside the record window *is* the §3.1.2 mid-day-restart path.
- **Mid-day restart (§3.1.2).** In-window start/restart resolves each ATM via one `RestClient.get_quote`
  per underlying → `feed.seed_spot(name, ltp)`, flags the overlap second with
  `db_writer.mark_restart_boundary(ts)` (P5 hook → `INSERT OR REPLACE`), and falls back to the lazy WS
  spot seed on any quote failure (needs a live broker session).
- **Supervisor (§3.1.3).** Every `supervisor_interval_sec`, scan `is_alive()` on all four workers + drain
  `error_queue`; a dead worker / error → teardown + rebuild fresh queues·events·threads + re-seed, bounded
  by `max_restart_attempts` consecutive failures with backoff → **fail-fast** (exit non-zero) so an OS
  supervisor takes over. Old threads/queues are joined + dropped before new ones are built (no leak).
- **Teardown drain (§3.1.4, decision 60).** `shutdown_event.set()` + `feed.stop()`; join **feed →
  processor** (drains `proc_queue`, flushes its final rows into `db_queue`); *then* `db_shutdown_event.set()`
  + join **db_writer**; join **raw_writer**. Each `join(timeout=10)`. EOF/fsync/close happen in each
  thread's own `run()` `finally` (P2/P5). The two-event split guarantees the db writer sees the
  processor's final rows.
- **Health file (§6.4).** Every `health_write_interval_sec`, `utils.atomic_write` a JSON payload:
  milestone `state`, `websocket_status`, the three queue sizes, `last_raw_tick_time`, `active_contracts`,
  the drop counters, `degraded_level`, the per-underlying `actual_depth` map (§9 silent-degrade alarm),
  and the writer/processor counters + `restart_count`. `--status` pretty-prints it (missing file →
  friendly "not running" + exit 0).
- **Session guards (§3.1.5).** Startup + periodic disk check (ERROR below `min_free_disk_mb`, non-blocking);
  optional trading-calendar idle (`skip_non_trading_days` → idle until the next trading day).
- **Reprocess (§3.1.1 M6 / §8.6).** After a clean EOF (`RawTickFileWriter.eof_written`) and if
  `reprocess.auto_on_session_end`, launch `--replay --catchup` as a detached child with stdout/stderr → a
  **real log file (never a PIPE)**, guarded by an exclusive run lock (stale-steal by age), and `.wait()`-reaped.

**FDs added by P6:** the health temp fd (closed by `atomic_write`) and the reprocess child's log file +
run lock (both closed / `.wait()`-reaped / released). All four worker threads are joined on every path
(clean teardown, crash-restart, KeyboardInterrupt). **Additive touches to earlier modules:**
`RestClient.get_quote` (P1); feed `seed_spot`/`freeze_dsm`/`connection_status`/`last_recv_ts`/
per-underlying `actual_depth` (P3); `RawTickFileWriter.eof_written` (P2). See `main.md`.

## Built state (P7)

`replay.py` + `database_writer.py::DuckDBAnalyticalWriter` — the **offline** path that produces the fat
Tier-2 DuckDB analytics store. Replay drives the **same** `TickProcessor` (full metric catalog) over the
raw log **synchronously** (no thread) off a **`recv_ts` virtual clock** — the exact basis the live
resampler/staleness used, so the rebuild matches the live store second-for-second. The sink is
`DuckDBAnalyticalWriter` (a plain `with`-managed object, not a thread): fresh `.duckdb` → `memory_limit`/
`threads` PRAGMAs → §4.1a DDL → per-table buffers streamed through the **`write → buffer → _flush → backend
insert`** seam → `finalize()` (trailing partials) + `recorder_meta` (`built_by="replay"`) + `CHECKPOINT`;
**idempotent by fresh file** (build to a `.building_<pid>` temp then atomic `os.replace`; any failure —
including mid-`finalize()` — discards the temp, so canonical output is strictly all-or-nothing). The insert
**backend** is `analytics_db.write_backend` (`arrow` columnar bulk load — production, ~70× — or `executemany`
deprecated fallback), and `_flush` fires every `analytics_db.write_batch_rows` (§P-C streaming) so **writer
memory is bounded by the configured batch size rather than growing with replay duration** instead of
buffering the whole session. `_flush` is the single seam a future
streaming/parallel writer reuses — metrics and the replay loop never see batching. The instrument context is reconstructed from the **enriched raw HEADER** (`instruments`
block, P7 decision 65) via `InstrumentManager.from_header()` — **no REST**, so a log of any age replays
correctly. `--catchup` self-heals (rebuild any raw log whose store is missing/stale, oldest-first);
`--verify` / `--verify-against-live` diff a rebuild vs a prior build / the SQLite live store (schema gate +
tolerance diff). The P6 M6 launcher now runs a real `--replay --catchup` build.

**Tier-0 HEADER enrichment (P7):** `RawTickFileWriter` now embeds the resolved chain (per underlying:
`option_exchange`, `expiry`, `strike_step`, `[strike, ce_sym, pe_sym, tick_size]` contracts) in the HEADER
so the raw log is a **self-contained** replay source (§3.5.4). **FDs added by P7:** the DuckDB build
connection (`with`-closed + CHECKPOINT + temp→rename) and the gzip reader (`with`-closed) — replay adds no
thread/subprocess/lock. See `replay.md` + `database_writer.md`.

### Storage tiers — all built
```
Tier 0  raw .jsonl.gz   (RawTickFileWriter, P2; HEADER carries the resolved chain, P7)  ── lossless source of truth
   │  replay (recv_ts clock, same TickProcessor, full catalog, P7)
   ├─► Tier 1  market_depth_live_YYYYMMDD.db      (SQLiteLiveWriter, P5; thin live_metrics subset, WAL)
   └─► Tier 2  market_depth_analytics_*.duckdb    (DuckDBAnalyticalWriter, P7; full §4 catalog, bulk)
```

## Built state (P8)

The **whole pipeline is now exercised end-to-end** by an automated, offline harness, and the two runtime
observability targets are instrumented:

- **Perf instrumentation.** `processor.py` times each `emit_second` (`perf_counter`, single-owner, no lock)
  and reports `cycle_ms_p50` / `cycle_ms_max` via `stats()`. `utils.process_rss_mb()` reads process RSS
  (stdlib: Windows working set via `ctypes`; Unix `getrusage`). Both, plus the queue depths, surface in
  `health.json` (`build_health`) and `--status`. Targets: cycle `< 30 ms` (re-tuned from 15 ms after P10-E —
  `cycle_ms_p50 ≈ 22 ms` keeps real-time pace; see `phase_10E_notes.md`), RSS `< 500 MB`.
  **Caveat (P10-F):** that measurement was **not** taken at "full 80×50-level" — the actual load was
  ≤5 NFO legs @50-level plus ~120 SENSEX legs @5-level, because the per-connection 5-cap was in force.
  The `< 30 ms` / `< 500 MB` targets have **never** been exercised at the hybrid's real profile (up to
  `tbt_budget = 15` legs @50 plus the rest @5) and must be re-measured once the allocator lands.
- **SIGTERM graceful teardown.** The live daemon (`_cmd_run`) registers a SIGTERM handler →
  `orchestrator.stop()` → the full drain / EOF / FD-close path, so a managed shutdown (systemd /
  `docker stop`) no longer hard-kills the daemon workers mid-write. SIGINT already mapped to
  `KeyboardInterrupt`. Best-effort (main thread + SIGTERM support required).
- **Integration harness.** `tests/test_integration.py` (`@pytest.mark.integration`) drives the real
  `_build_default_pipeline` with a scripted `RecordedTransport` (NIFTY 50-level / SENSEX 5-level) and the
  real `--replay --catchup` subprocess; asserts clean thread joins, a `HEADER..EOF` raw log with the
  `instruments` block + preserved depth audit fields, a populated live store, DuckDB determinism, and no FD
  residue. See `integration.md`. The **live** confirmations are **P9** (`LIVE_RUN.md`).

**FDs added by P8:** none in the daemon — `process_rss_mb`/SIGTERM hold no descriptor; the harness's gz /
SQLite / DuckDB / subprocess handles are all `with`/`finally`-closed and reaped.
