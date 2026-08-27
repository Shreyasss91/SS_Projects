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
├── market_depth_framework/ # generic depth-allocation framework — inert, not wired in  [F1-F7.5 ✅]
│   ├── __init__.py         # public surface; no side effects at import  [F1 ✅]
│   ├── __main__.py         # separate --validate-config CLI (exit 0/1/2)  [F1 ✅]
│   ├── models.py           # Instrument (no depth field), DepthType  [F1 ✅]
│   ├── capabilities.py     # UNLIMITED_BUDGET, PremiumTier, StandardTier, BrokerCapability  [F1 ✅]
│   ├── capability_layer.py # BrokerCapabilityLayer: effective_budget, premium eligibility  [F2 ✅]
│   ├── window_manager.py    # WindowManager: ATM-relative candidate legs (no ranking)  [F3 ✅]
│   ├── priority_policy.py   # AtmDistancePolicy + rank_scores: ranking only, 1-based rank  [F4 ✅]
│   ├── budget_allocator.py  # BudgetAllocator: premium budget split across underlyings  [F5 ✅]
│   ├── depth_allocator.py   # DepthAllocator: premium overlay per underlying, hysteresis  [F5 ✅]
│   ├── subscription_state.py   # SubscriptionState + plan/action types; snapshot-derived observability  [F6 ✅]
│   ├── subscription_manager.py # SubscriptionManager.reconcile: pure desired/current -> plan  [F6 ✅]
│   ├── broker_adapter.py    # BrokerAdapter: wire rendering, release-before-claim retier, delivery-derived snapshot  [F7.5 ✅]
│   ├── config.py           # framework schema + fail-fast validation  [F1 ✅]
│   └── config.example.yaml # reference §17 block, FYERS capability filled in (copy source)  [F2 ✅]
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

## Built state (F1) — market_depth_framework, contracts only

First phase of **Plan_002** (`plans/Plan_002_market_depth_framework_implementation.md`), the generic
market-depth allocation framework that will drive the hybrid (near-ATM legs at premium depth within the
broker's budget, the rest at standard depth). F1 delivers **contracts, not behaviour**.

- **Package `market_depth_framework/`** — a sub-package of the recorder, with a **one-way dependency**:
  it imports nothing from the recorder, so it stays independently testable and reusable across brokers.
  Per-module reference: `Documents/market_depth_framework.md`.
- **`models.py` — `Instrument`, `DepthType`.** `Instrument` is a frozen, hashable six-field leg identity
  (`underlying`, `exchange`, `symbol`, `expiry`, `strike`, `option_type`) with **no depth field**; depth
  is a value carried alongside, never part of the key (Plan_002 fork F10). This is the fix for §21 D-9:
  the recorder keys `_subscriptions` by *wire symbol*, whose `:50` suffix encodes depth, so a depth
  transition changes the key and one leg looks like two. `DepthType` names the tier
  (`STANDARD`/`PREMIUM`), not the level count — the numeric depth lives on the capability because it is a
  broker fact that varies by exchange.
- **`capabilities.py` — broker-declared facts.** `PremiumTier` / `StandardTier` / `BrokerCapability`,
  frozen and self-validating. `UNLIMITED_BUDGET` is an **`int`** sentinel (`2**31 - 1`), never
  `float('inf')`, so downstream `-> int` contracts and `min()` stay honest. `max_channels` is carried as
  **bookkeeping only and is never multiplied into a budget** — the FROZEN finding is 5 per *connection*
  × 3 connections = 15, not 5 per *channel* × 50 = 250.
- **`config.py` — schema + fail-fast validation.** Mirrors the recorder's `config.py` conventions: frozen
  typed config, a validator that **collects every error in one pass**, and an error type whose
  `report()` renders them all. Unknown keys are rejected (a typo'd key that validation ignores is a
  silent default by another name). The whole section is optional — absent means the framework is off,
  which is the current runtime state; present-but-malformed still fails hard.
- **`__main__.py` — separate entrypoint.** `python -m market_depth_recorder.market_depth_framework
  --config <path>` exits 0 / 1 / 2 per the recorder's convention. Deliberately separate from the
  recorder's `__main__.py` so F1 changes no recorder behaviour.

**Scope boundary at the time of F1, enforced by tests rather than by review.** No `effective_budget()`,
no `supports_premium()`, no §13.2 feasibility check — all three landed in F2 below. No
`window_manager` / `priority_policy` / `budget_allocator` / `depth_allocator` / `subscription_manager`
/ `broker_adapter` module (F3–F7.5); each has since landed in its own phase, and
`test_framework_package.py` keeps the same exact-equality guard over what is still ahead (F8's
`orchestrator`), shortened by one entry per phase rather than relaxed.
`BrokerCapability` itself still carries no budget arithmetic and no eligibility resolution — that guard
is unchanged and now reads as a data/behaviour separation guard, since F2 put the behaviour in a
separate module rather than on the dataclass.

**The framework is inert.** Not imported by any recorder module, not present in the shipped
`config.yaml`, not reachable from the live pipeline. The recorder's subscribe-everything-at-`:50` path
is unchanged and remains the active path.

**Threads added by F1:** none — the four-thread architecture (FEED, RAW WRITER, PROCESSOR, DB WRITER) is
preserved exactly; Plan_002 fork F1 settles that the framework is synchronous and threadless.
A subprocess import test with `socket.socket` / `sqlite3.connect` nulled asserts the thread count is
unchanged and nothing is printed, so inertness is verified rather than claimed.

**FDs added by F1:** one, transiently — the config file handle in `load_framework_config`, opened under
`with` and closed on every path including the YAML-error unwind. No socket, subprocess, DB handle, queue,
or executor anywhere in the package.

**Tests:** +187 (`test_framework_models.py` 36, `test_framework_capabilities.py` 50,
`test_framework_config.py` 91, `test_framework_package.py` 10). The pre-existing suite is unchanged at
**267**; full suite **454**.

## Built state (F2) — Broker Capabilities layer

Second phase of **Plan_002**. The first *behavioural* layer: it turns broker-declared facts into the two
answers the rest of the framework will consume — **one logical `effective_budget`** and **per-exchange
premium eligibility** — and nothing else. Still inert from the recorder's perspective.

- **`capability_layer.py` — `BrokerCapabilityLayer`.** Wraps one frozen `BrokerCapability`. No mutable
  state (`__slots__`, no setters), no I/O, safe to call from any thread. Per-module reference:
  `Documents/market_depth_framework.md`.
- **The budget is one number, computed once.**
  `effective_budget = min(total_symbol_budget, max_connections * symbols_per_connection)`, evaluated at
  construction from frozen inputs so it cannot drift mid-session. For the shipped FYERS configuration
  that is `min(UNLIMITED, 3 x 5) = 15`.
- **Connection and channel mechanics stay behind the boundary.** Allocators will see `effective_budget`
  and never `symbols_per_connection`, `max_connections`, or `max_channels`. That is what keeps the engine
  broker-agnostic: a broker exposing `1 x 20`, `5 x 10`, or a full 50-leg chain changes only its
  capability block, never allocator code.
- **15 is derived, never written down.** No framework source file contains a literal budget constant, and
  two AST scans over the package source enforce it: one rejects any multiplication mentioning
  `max_channels` (the disproven `5 x 50 = 250` model, roughly 16x too large), the other rejects a literal
  `15` assignment. The FROZEN evidence remains
  `Documents/patches/tbt_concurrency_reconciliation_20260714.md`.
- **Per-exchange premium eligibility (fork F13, §13.1).** `supports_premium(exchange)` is exact,
  case-sensitive membership in `premium_exchanges` — no silent normalization, and a malformed exchange
  raises rather than returning a plausible-looking `False`. An ineligible exchange (BFO) yields
  `premium_capacity() == 0`, so zero premium budget and no `min_per_underlying` floor, while its
  standard-depth baseline coverage is untouched: eligibility governs the overlay only.
  `depth_for(exchange, tier)` reports what the broker will *actually* serve, which is what makes a
  self-describing `depth_levels` and `NULL` deep-book metrics correct rather than optimistic.
- **§13.2 startup feasibility.** `eligible_underlyings()` and `check_premium_floor_feasible()` are
  module-level functions taking the underlying-to-exchange mapping as an argument, so the layer itself
  stays ignorant of underlyings. The floor is scoped to **eligible** underlyings only; scoring it over all
  configured underlyings would demand premium slots for an underlying whose exchange has no deep book,
  contradicting §13.1. Satisfying it at startup is what makes the mid-session failure unreachable — which
  is why the Budget Allocator (F5) will have no raising path able to kill the PROCESSOR thread.
  **Not yet called from a live startup path**: the mapping comes from the recorder's config, and that
  wiring is F8.
- **`config.example.yaml` — the FYERS capability, in configuration.** A version-controlled reference §17
  block (`symbols_per_connection: 5`, `max_connections: 3`, `max_channels: 50` as bookkeeping, premium
  depth 50, standard depth 5, `premium_exchanges: [NSE, NFO]`, `total_symbol_budget` omitted = the
  `UNLIMITED_BUDGET` sentinel). A **copy source, not a live config** (`enabled: false`); a test loads it
  end to end and asserts budget 15 with NFO eligible and BFO not, so the FYERS facts are proven to reach a
  budget through configuration alone. Wiring the block into `config.yaml` is F8.

**What the capability layer does not know:** underlyings, strikes, ranking, priority scores, windows,
subscription state, allocation policy. Asserted over its public method names and over its annotations (no
parameter typed `Instrument`) — eligibility is per-exchange, so two legs on the same exchange must get
identical answers regardless of strike or expiry. No `BudgetAllocator` or `DepthAllocator` behaviour
exists.

**Threads added by F2:** none. **FDs added by F2:** none — `capability_layer.py` imports only
`typing.Mapping` and three sibling modules; the package's only `open()` is still F1's config read under
`with`. No socket, subprocess, DB handle, queue, or executor.

**The framework remains inert.** Not imported by any recorder module, not present in the shipped
`config.yaml`, not reachable from the live pipeline. The recorder's subscribe-everything-at-`:50` path is
unchanged and remains the active path.

**Tests:** +132 (`test_framework_capability_layer.py`). One existing test widened —
`test_framework_package.py`'s exact-equality `__all__` assertion now expects the five new exports; it
stays an exact-equality check and the file's test count is unchanged. Full suite **586**.

## Built state (F3) — Window Manager

Third phase of **Plan_002**. The first layer that reasons about *legs*: given a spot price and a supplied
instrument universe it answers **which option legs are eligible candidates** — and stops there. It does
not rank them (F4), does not allocate budget or depth (F5), and does not decide what is subscribed (F6).
Still inert from the recorder's perspective.

- **`window_manager.py` — `WindowManager`.** A pure synchronous function of
  `(spot, universe, configured window)`. No mutable state (`__slots__`, frozen results), no I/O, no
  window state carried between passes, safe to call from any thread. Per-module reference:
  `Documents/market_depth_framework.md`.
- **One window, one density (F3 Decision 1).** Eligibility is a **single symmetric points-from-spot
  window** resolved from `underlyings[]` — `lower = spot - window_points`,
  `upper = spot + window_points` — with membership **inclusive at both bounds**, compared exactly with
  no epsilon. There is no ATM/expansion density split and no decimation: the strike step describes the
  instrument grid, not a second window density. Plan_002 §15 now states this explicitly.
- **The window semantics are the recorder's, not new ones.** That reproduces `websocket_client.py`'s DSM seeding rule
  (`st.b_lower <= k <= st.b_upper`) rather than inventing a parallel definition. The aggregate `_in_window`
  helper in `metrics/aggregate.py` uses an EPS because it is a different thing — an aggregate radius — and
  is deliberately not reused here.
- **ATM is nearest strike to spot; on an exact tie the LOWER strike wins (F3 Decision 2).** A decided,
  deterministic framework rule — it must not depend on list order, dictionary order, or input ordering.
  Implemented by sorting distinct strikes ascending and keeping only a strict improvement, so a shuffled
  universe cannot change the answer, and carrying a direct regression test plus a shuffled-input variant.
  It is the same answer `processor._resolve_atm` gives over its ascending `active_strikes_list`, with
  what was incidental list order in the recorder made explicit here.
- **The candidate set is not the subscription set (§15).** Boundary expansion, hysteresis, and the
  never-shrink subscription rule stay FEED-owned in the recorder and, in the framework, belong to F6.
  `WindowManager` recomputes from scratch on every call and remembers nothing.
- **Identity ordering, explicitly not priority ordering.** Candidates are returned sorted by
  `(strike, option_type, symbol)` so replay and tests are stable. A test asserts this is *not* a
  distance-from-ATM ordering, so nothing downstream can mistake it for a ranking F4 has not yet computed.
- **Identity is supplied, never constructed.** The universe arrives as `Instrument` values from the
  instrument master; the framework parses no symbol and builds no symbol. Option side is resolved through
  a registered `SymbolCodec` rule (`TagSymbolCodec(call_tags, put_tags)`), and expiry selection through a
  registered `ExpiryCalendar` rule (`FixedExpiryCalendar`). Both seams are registered **per rule name, not
  per index name** (§10.2), so a new exchange vocabulary needs a new registration, never an `if`.
  An unrecognised option-type tag raises on the pass that saw it — it is never guessed at.
- **Degenerate inputs get a named status, not an exception.** `WindowResult.status` is one of `RESOLVED`,
  `NO_SPOT` (missing / zero / negative / NaN / infinite spot, and `bool` rejected as not a price),
  `NO_EXPIRY`, `NO_UNIVERSE`. A caller-side bug — an unknown underlying, or a leg claiming this underlying
  on a contradicting exchange — still raises.
- **No second config system (F3 Decision 3).** The framework's `window_manager` config section stays
  deliberately **keyless**; there is one source of truth for these window facts and no duplicate
  framework window settings. Zones are read from the recorder's existing `underlyings[]` through
  `window_specs_from_underlyings()`, which takes plain mappings and consumes only `name`,
  `option_exchange`, and `initial_window`. Duplicating the zones into a second place is how a config and
  its source drift apart.

**What the Window Manager does not know:** `tbt_budget`, `effective_budget`, premium slots, connection
counts, `max_channels`, ranking scores, hysteresis, cooldown, subscription state, broker adapters. Asserted
on the *source* by AST scans in the same style as F1/F2: no capability-layer or recorder import; no budget,
ranking, or allocation token; no `'CE'` / `'PE'` / index / exchange literal in executable code; no
`open` / `connect` / `Thread` / `Popen` / `Queue` / `socket` call; no `time` / `random` / `socket` / `os` /
`threading` / `queue` / `asyncio` import; no ranking or allocation method on the class.

**Threads added by F3:** none. **FDs added by F3:** none — `window_manager.py` imports only `math`,
`dataclasses`, `enum`, and `typing` plus two sibling modules. No socket, subprocess, DB handle, queue, or
executor. F3 is a pure synchronous computation layer.

**The framework remains inert.** Not imported by any recorder module, not present in the shipped
`config.yaml`, not reachable from the live pipeline. The recorder's subscribe-everything-at-`:50` path is
unchanged and remains the active path.

**Tests:** +125 (`test_framework_window_manager.py`), on synthetic underlyings `ALPHAIDX` / `BETAIDX` on
exchanges `XFO` / `YFO` with strike steps 50 / 100 and windows 200 / 500, so no test can pass by accident
on a NIFTY-shaped universe. All five boundary positions (below, on lower, ATM, on upper, above) and both
option sides are verified **separately**, never inferred from one another. Two existing phase-boundary
guards widened by exactly one module each (`test_framework_package.py`, `test_framework_capability_layer.py`);
both remain exact-equality checks and still fail on any F4+ module. Full suite **711**.

---

## Built state (F4) — Priority Policy

F4 answers the **second** of the four questions the framework asks each pass. F3 said *which legs are in
play*; F4 says *in what order they matter*. It does not say how many may be premium (Budget Allocator,
F5), which ones get the premium overlay (Depth Allocator, F5), or what is actually subscribed
(Subscription Manager, F6). The ranking is an **input to F5**, nothing more.

- **`priority_policy.py` — `AtmDistancePolicy`.** `compute_priorities(candidates, ctx)` scores each
  candidate `-abs(strike - ctx.atm_strike)` and returns `rank_scores(...)`. Nearer the ATM outranks
  further; the ATM leg scores exactly `0.0`. Distance is measured from the **ATM the Window Manager
  already resolved**, never re-derived here — §15 states the ATM rule (including the lower-strike tie)
  exactly once.
- **`rank_scores(scored)` is the single ordering site (Plan_002 §10.3).** Every policy returns through
  it, so the total order — **score descending, then symbol ascending** — is defined in one place and an
  unchanged market yields an unchanged ranking. Equal-distance ties are the common case (the CE/PE pair
  at one strike; mirrored strikes either side of the ATM), and the symbol tie-break is what makes them
  deterministic rather than input-order-dependent.
- **`PriorityScore.rank` is 1-based and is the only rank basis in the system (§14.2, fork F4).** The
  drafted 0-based positional index was deleted rather than reconciled, so there is no second basis to
  keep in step. The 1-based floor is enforced by `PriorityScore.__post_init__`, not merely produced by
  the ranker, and `rank_scores` is the only place a rank is ever constructed.
- **`MarketContext` is a frozen per-pass snapshot** — `underlying`, `spot`, `atm_strike` and nothing
  else. It is rebuilt each pass and never mutated in place, which is what makes a ranking replayable.
  `market_context_from_window(result)` builds it from an F3 `WindowResult` and **refuses any
  non-`RESOLVED` status**: ranking a window that never resolved a spot would be ranking nothing while
  looking like it succeeded.
- **`policy_for(name)` selects the policy; `atm_distance` is the default (§14.6, fork F12).** Selecting
  `blended` raises `FrameworkConfigError` rather than falling back — a policy that silently degrades to
  another when its inputs are missing is exactly the silent default the fail-fast contract forbids.
- **`rank_candidates(policy, results)` ranks per underlying**, each starting at rank 1. Underlyings do
  not share a rank pool; how budget is split across them is F5's question, and ranking them together
  would pre-empt it. A non-`RESOLVED` window contributes an empty tuple rather than disappearing.
- **Candidate identity is preserved.** Each `PriorityScore` carries the exact `Instrument` object it
  scored (asserted by `id()`), the scored set equals the candidate set, and the input sequence is not
  mutated. F5 receives what F3 produced, not a re-derived lookup that could drift.

**Deliberately absent from F4**, and asserted absent by source-level AST scans rather than left to
review: budget or `tbt_budget` awareness, `max_channels`, the capability layer (not imported), premium
overlay selection, `DepthType` or any depth tier, hysteresis (§14.1), cooldown (§14.3), subscription
state, reconciliation, and broker I/O.

**Threads added by F4:** none. **FDs added by F4:** none — `priority_policy.py` imports only `math`,
`dataclasses`, `typing` plus three sibling modules. An AST scan asserts it imports no `time`, `random`,
`socket`, `os`, `threading`, `queue`, `asyncio`, `sqlite3`, `subprocess`, or HTTP client, and calls no
`open()`, `connect()`, `Thread()`, `Popen()`, `Queue()`, or `Session()`. F4 is a pure synchronous
computation layer.

**The framework remains inert.** Still not imported by any recorder module, still absent from the
shipped `config.yaml`. The recorder's subscribe-everything-at-`:50` path is unchanged.

**Tests:** +81 (`test_framework_priority_policy.py`), on the same synthetic `ALPHAIDX` / `BETAIDX`
underlyings, so nothing can pass by accident on a NIFTY-shaped chain. Three existing phase-boundary
guards shortened by exactly one module each (`priority_policy`) in `test_framework_package.py`,
`test_framework_capability_layer.py`, and `test_framework_window_manager.py`; all remain
exact-equality checks and still fail on any F5+ module arriving early. Framework suite **490**, full
suite **792**.


---

## Built state (F5) — Budget Allocator + Depth Allocator

F5 answers the **third and fourth** of the four questions the framework asks each pass. F3 said *which
legs are in play*, F4 said *in what order they matter*; F5 says *how many premium slots each underlying
gets* and *which of its legs hold them*. It does not decide what is actually subscribed
(`SubscriptionState` / `SubscriptionManager`, F6) and performs no broker I/O (F7).

Keeping the two allocators apart is deliberate. The split across underlyings is a **capacity** question
answered from candidate counts and configured weights; the overlay within one underlying is a
**ranking** question answered from `PriorityScore.rank`. Collapsing them would make the inter-underlying
split depend on individual leg priority, which is exactly the §10.4/§10.3 separation Plan_002 protects.

### `budget_allocator.py` — one logical budget split across underlyings (§10.4, §13)

`BudgetAllocator.allocate_budget(total_budget, candidate_counts) -> Dict[str, int]`.

- **The budget arrives as a plain integer.** The allocator does **not** compute broker capability: no
  `max_channels`, `symbols_per_connection`, `max_connections`, no `effective_budget` derivation, and no
  hardcoded `15`. `tbt_budget` is a broker *capability* exposed by the F2 capability layer, never an
  architectural constant, so another broker changes config and nothing else.
- **Largest-remainder split on exact rationals.** Shares are computed with `fractions.Fraction`, not
  floats: independent per-underlying rounding can sum *above* the budget and blow a hard broker limit,
  and float division can truncate an exact `13` to `12`. Integer arithmetic throughout.
- **Floors apply to premium-eligible underlyings only** (§13.2). An ineligible underlying reports
  `candidate_count = 0`, takes no floor, and receives `0`. A floor is itself capped by that underlying's
  candidate count, so a floor never invents capacity. An infeasible floor degrades deterministically and
  **never raises at runtime** — that check belongs to startup (F7), and a runtime raise here would kill
  PROCESSOR mid-session.
- **Redistribution is capacity-driven, not priority-driven** (§13.3). Unspent slots go out one at a
  time, round-robin in descending weight order with ties broken by name, to eligible underlyings that
  still have headroom. It reads counts and weights only — never a `PriorityScore`. Termination is
  structural: every step decrements `leftover`, and the loop exits when no underlying has headroom.
  `redistribute_unspent: false` is honoured, leaving a genuine surplus unspent.
- **Unimplemented policies fail fast.** `equal` and `proportional_to_candidates` are names the F1 schema
  accepts and no phase has implemented; `budget_allocator_for()` refuses them rather than silently
  serving `weighted`, mirroring F4's `policy_for("blended")`. An operator who configured one split and
  received another has no way to discover it.

Invariants asserted in code, not assumed: `sum(result.values()) <= total_budget`;
`result[u] <= candidate_counts[u]`; **every** configured underlying is answered, `0` being a valid
answer and a missing key not.

### `depth_allocator.py` — the premium overlay within one underlying (§10.5, §14)

`DepthAllocator.allocate(ranked, budget) -> DepthAllocation`. **One instance per underlying** — a shared
instance would let a busy chain's reallocation reset a quiet chain's cooldown, so churn control would
silently stop applying to the underlying that needed it least often.

- **Hysteresis is effective-rank stickiness inside a bounded band** (§14.1, fork F3, resolved §20.3). An
  incumbent competes at `rank - hysteresis_buffer` while `rank <= budget + hysteresis_buffer`, and at
  its true `rank` outside that band; a challenger always competes at its true `rank`; selection takes
  the `budget` lowest effective ranks; **an effective-rank tie is won by the challenger**. Each clause
  earns its place — the subtraction stops a leg oscillating around `rank == budget` from flapping, the
  band stops protection accumulating, and the tie rule is the anti-lockout that guarantees a rank-1 leg
  (the ATM) can never be shut out. `hysteresis_buffer = 0` collapses all of it to ordinary top-N.
  **No `hysteresis_buffer < smallest premium budget` startup guard exists** — the anti-lockout is a
  property of the selection rule, not of config (§20.3).
- **The cooldown gates premium reshuffles only** (§14.3, fork F5). A baseline addition is immediate:
  gating it would leave a newly-relevant strike entirely unsubscribed for the cooldown, a hole in the
  very book being recorded. The first allocation of the session is never gated either. A leg that has
  left the candidate window loses its slot regardless of the cooldown — that is disappearance, not
  churn — and a shrinking budget still truncates, because the budget is a hard broker limit.
- **Budget is passed per call and never stored** (§10.5): the split changes whenever another
  underlying's candidate count moves, so a remembered budget would go stale unnoticed.
- **Rank basis is `PriorityScore.rank`, 1-based and the only basis** (§14.2). List position is never a
  second rank — a shuffled input produces an identical allocation, asserted on the result *and* on the
  source.
- **The clock is injected and has no default.** No business logic here reads a wall clock, so tests
  advance time without sleeping and a replay reproduces a live pass exactly.
- **Diff semantics** (§14.4): `added_new` and `promoted_to_premium` are disjoint by construction, so a
  leg allocated straight to premium is subscribed once rather than as an add plus a promotion that
  burns a scarce slot on the round trip. `removed` is **observability only** and produces no
  unsubscribe anywhere in F5 — baseline coverage is monotone within a session (F6's invariant).
- State owned: current premium set, last-premium-change timestamp, and a `deque(maxlen=history_limit)`
  debug ring — **bounded by construction**, since an unbounded list is a slow leak in an all-session
  process.

**Deliberately absent from F5**, asserted absent by source-level AST scans rather than left to review:
`SubscriptionState`, `SubscriptionManager`, `reconcile()`, any subscription plan, the Broker Adapter and
its depth-transition probe, recorder integration, and — in the Budget Allocator specifically —
`PriorityScore` and every form of broker-capability arithmetic.

**Threads added by F5:** none. **FDs added by F5:** none. `budget_allocator.py` imports only
`fractions`, `types`, `typing` plus its `config` sibling; `depth_allocator.py` only `collections`,
`dataclasses`, `typing` plus `config`, `models`, `priority_policy`. An AST audit over both modules
confirms no `open()`, socket, thread, subprocess, queue, executor, DB handle, network call, wall-clock
read, `global`, or module-level side effect. Both are pure and synchronous, and the framework remains
**inert** — importing it starts no thread, and no recorder module references it.

**Tests:** +155 (`test_framework_budget_allocator.py` 71, `test_framework_depth_allocator.py` 84), on
synthetic `ALPHAIDX` / `BETAIDX` / `GAMMAIDX` underlyings so nothing can pass by accident on a
NIFTY-shaped chain. The five §20.3 hysteresis cases are carried as named mandatory regressions. Four
existing phase-boundary guards shortened by exactly the two F5 modules — `test_framework_package.py`,
`test_framework_capability_layer.py`, `test_framework_window_manager.py`, and
`test_framework_priority_policy.py` — all still exact-equality checks that fail on any F6+ module
arriving early. Framework suite **680**, full suite **947**.

---

## Built state (F6) — Subscription layer (state + pure reconciliation)

F6 answers the **fifth** question the framework asks each pass — *what should be subscribed, and how does
the desired state converge on the live one* — and stops exactly there. F5 produced each underlying's
desired premium/standard tuples; F6 turns those into a desired leg -> depth map, reconciles it against a
live snapshot, and tracks which dispatched actions the feed has and has not yet reflected. It performs
**no broker I/O**: the actual subscribe/upgrade/downgrade execution and the evidence for what a depth
transition costs on the wire are owned by the Broker Adapter (F7).

**The F6 design fork was resolved to Option A — snapshot-derived `pending` / `failed`** (Plan_002 §20.4,
decided 2026-08-25, a new F6 decision, not a reopening of F1-F5/F9). `pending` and `failed` are
**broker-neutral observability**, not a per-leg broker acknowledgement ledger. F6 assumes no per-leg ack
API, no FEED per-leg confirmation, and nothing about whether an unsubscribe exists or whether a bare
re-subscribe changes depth — all of those remain F7's to measure. The acknowledgement *is* the next live
snapshot: a dispatched action is confirmed when a later `current` shows the leg at its desired depth.

Splitting the layer into two modules keeps the data model free of the reconciliation algorithm, so the
dependency runs one way — `subscription_manager.py` imports the plan types from `subscription_state.py`,
never the reverse.

### `subscription_state.py` — desired coverage plus snapshot-derived observability (§9, §12, §20.4)

`SubscriptionState(effective_budget, *, clock)`. PROCESSOR-owned and single-writer (§7), so it carries no
lock of its own.

- **State keyed by leg identity; depth is a value** (F10, §9). Every set is keyed by `Instrument`; a
  leg's depth is membership in `premium_overlay`, never part of the key and never a `:50` wire suffix.
  This is what makes "the same leg at a different depth" expressible.
- **`baseline` grows monotonically; `premium_overlay` is replaced each pass.** `set_desired(desired)`
  unions every key into `baseline` and never removes one, so a leg that leaves the candidate window
  keeps its standard subscription; the premium set is *replaced* by the keys mapped to premium, so a leg
  dropped from the premium selection demotes to standard while remaining baseline. `reset()` is the only
  operation that may shrink `baseline`.
- **`effective_budget` is a plain integer** — a broker capability resolved by the F2 layer, never
  reconstructed here from `max_connections` / `symbols_per_connection`, and never a hardcoded `15`.
  `set_desired` enforces `len(premium_overlay) <= effective_budget`, so the §9 budget invariant holds
  before any action is dispatched. Invariants asserted, not assumed: `premium_overlay ⊆ baseline`;
  `pending ∩ failed = ∅`.
- **`pending` / `failed` are the snapshot lifecycle.** `record_dispatch(plan)` marks a plan's actioned
  legs (every group except `removed`) `pending` — awaiting confirmation, **not** broker success — and
  clears them from `failed` (a retry is now in flight). `apply_live(current)` clears any `pending` **or**
  `failed` leg the live snapshot now shows at its desired depth; the live snapshot is the authoritative
  observation boundary (§5), so it overrides a stale failure record, but it **never manufactures** a
  failure from a wrong-depth or missing leg (§4). `record_failed(legs)` is the minimal, no-taxonomy
  path moving legs `pending -> failed`. None of these perform I/O or know how `current` was produced.
- **The clock is injected and has no default.** `last_updated` is stamped from it on construction and on
  every mutator, so a replay reproduces a live pass exactly.

### `subscription_manager.py` — pure desired/current reconciliation (§10.6, §14.4)

`SubscriptionManager.reconcile(desired, current) -> SubscriptionPlan`. Stateless (`__slots__ = ()`),
clockless, and **pure**: same inputs -> same plan, no mutation of either argument, no I/O, no broker
assumption.

- **The eight §6 F2 transition rows, realised by comparing two maps.** `absent -> standard|premium`
  becomes `added_new` at the target depth (a leg premium on first sight is `added_new` **alone**, never
  also `promoted_to_premium` — §14.4 disjointness); `standard -> premium` is `promoted_to_premium`
  (UPGRADE); `premium -> standard` is `demoted_to_standard` (DOWNGRADE); the two same-depth rows are
  no-ops; `reset`/shutdown is `SubscriptionState.reset`, not a reconcile concern.
- **`removed` is observability only and never an unsubscribe** (§6 F2 row 7, §14.4). Legs the live book
  carries but the desired state no longer names are reported so drift is visible, but they produce **no**
  executable action — baseline coverage is monotone within a session.
- **`reconcile` never inspects `pending` / `failed`** (§10.6, frozen). The live `current` snapshot is the
  sole authority on the book, so a still-pending action that has not yet landed is simply re-emitted, and
  that re-emission *is* the retry. The observability annotations are folded in by `SubscriptionState`,
  deliberately outside this function — asserted absent on the source.
- **Release-before-claim ordering.** `SubscriptionPlan.ordered_actions()` emits all demotions before any
  additions or promotions, so a promotion never precedes the demotion that frees its slot against a hard
  premium budget. Every group is sorted by `str(instrument)`, so the plan is deterministic regardless of
  input-map iteration order. No numeric priority field, no priority-policy coupling.

**Deliberately absent from F6**, asserted absent by source-level AST scans: the Broker Adapter, any live
subscribe/unsubscribe execution, the depth-transition probe, per-leg acknowledgement APIs, recorder/FEED
integration, reconnect execution, and every form of broker-capability arithmetic. The F7 boundary
questions — whether a bare re-subscribe changes depth, whether an explicit unsubscribe exists or is
required, what a transition costs, behaviour at the 15-symbol ceiling, and reconnect depth restoration —
remain **unresolved** and untouched by F6 (§20.1).

**Threads added by F6:** none — `SubscriptionManager` is not a thread and F1's four recorder threads are
untouched. **FDs added by F6:** none. `subscription_state.py` imports only `dataclasses`, `enum`,
`typing` plus its `models` sibling; `subscription_manager.py` only `typing` plus `models` and
`subscription_state`. An AST audit over both modules confirms no `open()`, socket, thread, subprocess,
queue, executor, DB handle, network call, wall-clock read, or module-level side effect. The framework
remains **inert** — importing it starts no thread, and no recorder module references it.

**Tests:** +86 (`test_framework_subscription_state.py` 51, `test_framework_subscription_manager.py` 35),
on synthetic `ALPHAIDX` underlyings so nothing can pass by accident on a real-index-shaped chain. All
eight transition rows are covered individually, plus the full snapshot lifecycle, budget/monotonicity
invariants, ordering, idempotence, and the resource/scope AST guards. Four existing phase-boundary guards
shortened by exactly the two F6 modules — `test_framework_package.py`,
`test_framework_capability_layer.py`, `test_framework_window_manager.py`, and
`test_framework_priority_policy.py` — all still exact-equality checks that fail on any F7+ module
arriving early, and the exact-equality `__all__` set widened with the F6 group. `__init__.py` version
`0.5.0 -> 0.6.0`. Framework suite **766**, full suite **1033**. Recorder `--validate-config` still
`CONFIG OK`, config hash `sha256:8a48bcdd...1a468b` unchanged — no recorder behaviour changed.


## Built state (F7) — depth-transition probe harness (F7A) and live measurement (F7B)

**Nothing in `market_depth_framework/` changed.** F7 adds no framework module, no framework thread,
no recorder change, and no fifth recorder thread. It adds a **developer tool** under
`tools/fyers/` and its offline tests (F7A), and the live evidence that tool then captured (F7B,
2026-08-26). The Broker Adapter is deliberately **not** part of F7: F7 measures what the broker
does, and turning that evidence into broker-specific execution code is a separate phase.

**Why F7 is split.** Plan_002 §20.1 makes a live depth-transition probe the gate on the Broker
Adapter, and §22 fixes the order — F7 measures, the adapter contract is written from the
measurement, then F8 integrates. On 2026-08-26 no live probe was possible (market closed, OpenAlgo
not running, the stored FYERS session ~23 days stale and past the daily ~03:00 IST token rollover,
no `feed_token`). The measurement cannot be substituted, but the machinery around it — request
construction, acknowledgement parsing, transition classification, evidence capture — is
deterministic and is where the reasoning errors live. That is F7A. The measurement is F7B, which
ran on **2026-08-26, 09:34-09:52 IST** against a live NSE session — six invocations on one NFO
option, one case per process so no case could contaminate the next.

**The question F7 exists to answer.** When the framework retiers a leg between the standard (5) and
premium (50) depth tiers, what actually happens on the wire? Nothing in the codebase established
whether that changes an existing subscription, creates a second one, costs an extra premium slot, or
drops ticks in between.

**The measured answer.** Depth is a property of the **wire symbol**, not a mutable property of a
subscription. `SYMBOL` and `SYMBOL:50` are two independent subscriptions that stream simultaneously.
The `depth` request parameter does not change delivered depth. There is **no in-place transition**:
promotion adds a leg and demotion must remove one, so every retier is two operations, not one. The
full record is `Documents/patches/depth_transition_probe_20260826.md` with six evidence JSONs
alongside it.

**Two spellings, not assumed equivalent.** The recorder encodes depth **twice** — a `:50` symbol
suffix (`websocket_client.py:198-200`) *and* a `depth` field (`:558-563`, `:662-666`) — while the
proxy keys a subscription by `(symbol, exchange, mode)`, which excludes depth
(`websocket_proxy/server.py:74,1244`). So "move this leg to 50" has two candidate spellings:
**CASE A** `SYMBOL` + `depth: 50` (same subscription key) and **CASE B** `SYMBOL:50` + `depth: 50`
(a different key). The probe ran both, separately, and they are **not** equivalent: CASE A was
acknowledged `success` with `depth: 50` and delivered **5 levels**; CASE B delivered **50**. The
cheap in-place transition does not exist, so the adapter must use the suffixed spelling and manage
two legs across a retier.

- **`tools/fyers/_depth_probe_model.py`** — the broker-neutral data model. Pure: no network, no file
  I/O, no broker import, no recorder or framework import. Operations, symbol forms, mechanisms,
  confidence and outcome are explicit enums.
- **`tools/fyers/depth_transition_probe.py`** — the runner. Unlike the two TBT probes it does **not**
  bypass OpenAlgo: it speaks the proxy's own WebSocket protocol, because that is the path the Broker
  Adapter will sit on. One synchronous blocking connection — no callback client, therefore no
  background thread. Dry-run by default; `--live` opt-in; refused outside 09:15-15:30 IST unless
  forced; hard cap of 2 instruments; no retries and no loops; cleanup unsubscribes every wire symbol
  it subscribed and closes the socket in a `finally`.

**The invariant that makes the eventual evidence trustworthy.** Three depths are kept apart and never
merged: **requested** (what we asked), **reported** (what the acknowledgement said), **observed**
(levels counted in delivered market-data packets). The proxy echoes the requested depth back when the
adapter reports nothing (`server.py:1254`), so a reply of `depth: 50` may mean nothing at all.
`DepthEvidence.effective_depth` returns `None` unless the depth was observed, and
`classify_transition` returns `UNKNOWN` unless **both** sides were observed. An accepted request can
therefore never be recorded as a depth change — that guard is structural, not a matter of discipline.
Likewise an unattempted operation reports UNKNOWN, never "unsupported", and an accepted-but-unobserved
operation stays undecided.

**Secret hygiene.** The API key is read from `OPENALGO_API_KEY`, never a CLI argument (it would land
in shell history). Any parameter whose key looks like a secret is redacted, and `ProbeRequest` refuses
to be constructed with an unredacted one, so no credential can reach an evidence file.

**Threads added by F7A:** none. **FDs added by F7A:** none at rest — the probe's single socket exists
only during a `--live` run and is closed on every path. The framework remains inert; the recorder's
four-thread / three-queue contract is untouched; `market_depth_framework/broker_adapter.py` still does
not exist, and a test asserts it.

**Tests:** +103 (`tests/test_f7_depth_probe_harness.py`), all offline with no broker, WebSocket, or
market feed. They cover request construction, case sequencing, acknowledgement parsing, depth counting,
the confidence lattice, transition classification, support evidence, redaction, evidence determinism,
the CLI's safety limits, the unsubscribe-effect instrument, and import/dry-run inertness. **None of
them asserts anything about broker behaviour** — the broker's answers live in the evidence document,
never in an assertion. The count moved 83 -> 93 in the pre-market wire-format review and 93 -> 103
when the unsubscribe-effect instrument was added mid-run and then covered offline.

**Unsubscribe was measured with a control, not inferred.** Acceptance and effect are two
questions, and the committed harness could originally answer only the first.
`_measure_unsubscribe_effect` was added during the live run: observe -> unsubscribe -> observe ->
**re-subscribe** -> observe. Silence after an unsubscribe means nothing on its own; silence followed by a successful
resumption is evidence. Measured: 20 packets, then 0, then 21. Silence with no resumption would have
stayed UNKNOWN.

**What stayed UNKNOWN, deliberately.** Reconnect depth restoration (the proxy was shared with a live
client holding 180 symbols, so forcing a reconnect would have disrupted a running system) and premium
slot accounting (it needs the broker ceiling approached, which the safety rules forbid). Both are
**untested, not "no"** — the adapter keeps its conservative posture on those grounds: release before
claim, and re-observe after a reconnect rather than assume depth survived it.

**F7 is complete as the evidence phase.** F7A prepared the instrument; F7B measured. The Broker
Adapter is **not part of F7** — `market_depth_framework/broker_adapter.py` still does not exist and a
test asserts it. Its contract is derived from the measured evidence (§19 of the evidence document) and
its implementation is a separate, separately approved phase. This is architectural sequencing, not an
unfinished F7. The operator procedure is
`Documents/patches/depth_transition_probe_runbook_20260826.md`. F8 has not started.


---

## Built state (F7.5) — Broker Adapter

The layer F6 stopped short of and F7 measured for. `market_depth_framework/broker_adapter.py`
(~700 lines, 126 tests) turns a `SubscriptionPlan` into wire frames and turns delivered packets back
into the live `leg -> depth` snapshot that `SubscriptionState.apply_live()` consumes. Version
`0.6.0 -> 0.7.0`. Per-module reference: `Documents/market_depth_framework.md`.

**It is written from the F7B evidence, not ahead of it.** Every design choice below traces to a
measured fact or to a deliberately conservative reading of an unmeasured one; nothing in the module
asserts broker behaviour that was not observed on the wire.

### Where it sits

```
PROCESSOR thread                                    FEED thread
  DepthAllocator -> desired {leg: depth}
  SubscriptionState.set_desired()
  SubscriptionManager.reconcile(desired, live) ------> BrokerAdapter.apply(plan)
                                                          -> DepthTransport.send(frame)   [caller's WS]
  SubscriptionState.apply_live(snapshot) <------------ BrokerAdapter.live_snapshot()
                                                       BrokerAdapter.observe(packet|ack)
```

`reconcile()` stays pure, synchronous, and broker-free; the adapter is the only module in the package
that knows a wire format exists.

### Wire identity — the suffix never enters the framework

The framework's identity is `Instrument`, always. The adapter renders it per tier:

| Tier | Wire symbol | Evidence |
| --- | --- | --- |
| `DepthType.STANDARD` | `SYMBOL` | CASE A: bare symbol delivered 5 levels |
| `DepthType.PREMIUM` | `SYMBOL:50` | CASE B: suffixed symbol delivered 50 levels |

The `:50` suffix is built from `capability.premium.depth` through `WireDialect.premium_suffix()`, so a
broker with a 20-level deep tier renders `:20` with no code change. `live_snapshot()` is keyed by
`Instrument` and a test asserts no returned key carries a suffix.

### Release before claim

F7B measured that `SYMBOL` and `SYMBOL:50` are **independent concurrent subscriptions**, so a retier is
not an edit — it is a remove plus an add. The adapter always emits the release first:

- promotion: `unsubscribe SYMBOL` -> `subscribe SYMBOL:50`
- demotion: `unsubscribe SYMBOL:50` -> `subscribe SYMBOL`

The opposite ordering (claim then release) transiently holds both legs and is the one sequence that can
overshoot a premium ceiling nobody has measured. If the release fails at the transport, the claim is
**abandoned for that pass** and the leg reappears in the next reconciliation — never claimed on the
strength of a release that may not have taken effect.

Plan-wide ordering is preserved from `SubscriptionPlan.ordered_actions()`: demotions, then additions,
then promotions. `removed` produces no wire traffic at all (F2 row 7 — baseline coverage is monotone).

### Acknowledgements are transport news, not depth evidence

This is the finding F7A's anti-fabrication design existed to protect. CASE A was acknowledged
`status: success, depth: 50` and delivered five levels; no later frame corrected it.

- An accepted ack sets `accepted = True` and leaves the leg `REQUESTED`. It never enters
  `live_snapshot()`.
- An explicit rejection marks the leg `FAILED`, frees any premium slot it held, and surfaces through
  `take_rejections()`.
- An unacknowledged request stays `REQUESTED` — ambiguous, not failed.
- Only a **delivered packet** on a leg's own wire symbol moves it to `DELIVERING`.

A leg's tier is fixed when its wire symbol is rendered, so an illiquid strike delivering six levels on
`SYMBOL:50` is a live premium leg, not a broken one. The observed level count is recorded as
observability and never invalidates a leg — a threshold there would churn forever on a thin book.

**A released leg that keeps delivering stays visible.** `RELEASING` counts as live only when
`last_packet_at > released_at`, the same discrimination `_measure_unsubscribe_effect` used in F7B:
silence alone proves nothing, continued delivery proves the release did not take.

### Premium capacity and connection packing

The adapter consumes one logical `effective_budget` from `BrokerCapabilityLayer` and packs premium legs
into `(connection_id, channel_id)` slots itself, filling a connection before opening the next. Channel
ids are **strings** (`"1"`, `"2"`, ...) per the frozen finding. Standard legs consume no premium slot
and carry no connection assignment — the capability model describes premium connection arithmetic and
nothing else, and inventing standard-tier arithmetic would be an unmeasured assumption.

No allocator learns that connections exist; a test scans `budget_allocator.py`,
`depth_allocator.py`, `subscription_manager.py`, and `subscription_state.py` for `max_connections`,
`symbols_per_connection`, and `channel_id` and fails on any of them. A second test scans the adapter's
own AST for the integer literals `15`, `50`, and `250`.

A claim beyond the budget, or a premium claim on an exchange the capability does not cover, is
**refused** (reported in `DispatchResult.refused`) rather than dropped silently.

### Reconnect — conservative, and still UNKNOWN

Reconnect depth restoration was **not measured** (§21), and the module asserts nothing in either
direction — a test greps the source for both "preserves premium depth" and "loses premium depth".
`handle_reconnect(desired)` treats every live subscription as unknown: bookkeeping is cleared, the
desired coverage is reissued baseline-first, and **nothing is confirmed** until packets arrive again.
The repeated plan that follows is absorbed at the adapter (`_claim` skips legs already `REQUESTED` or
`DELIVERING`), so re-planning after a reconnect produces no wire storm.

### Threads, FDs, retries

**Threads added: none. Sockets added: none. FDs added: none.** The four-thread / three-queue contract
is untouched. The adapter runs synchronously on the caller's thread — FEED-owned in F8 — and writes
through the `DepthTransport` protocol the caller supplies; it never creates the transport and never
closes it. `close()` drops the adapter's own bookkeeping and nothing else, and is idempotent.

AST tests enforce this rather than trusting review: no `Thread` / `Process` / `Popen` / executor /
`Queue` / `Lock` construction, no `socket()` / `open()` / `connect()` / `sqlite3` / `duckdb` call, no
real clock read (the clock is injected), no statement executed at import time, and imports limited to
`__future__` / `dataclasses` / `enum` / `typing` plus three sibling modules.

There is **no retry loop** — a test fails the module on any `while` statement. Retry means the next
reconciliation pass observes `desired != live`; a failed leg is simply absent from `live_snapshot()`,
so `reconcile()` re-plans it. Bookkeeping is pruned at the start of each `apply()` (released legs that
have gone silent, and failed legs), so a session of retiering does not accumulate records.

### Deliberately absent from F7.5

No recorder integration. `processor.py`, `websocket_client.py`, `main.py`, and every other recorder
module are untouched, and the framework still imports nothing from the recorder. No acknowledgement-based
depth ledger, no `BrokerAckState` / `SubscriptionAckLedger` — the F6 state model
(`baseline` / `premium_overlay` / `pending` / `failed`) remains the only subscription state model. No
FYERS-specific failure taxonomy beyond the three shapes the evidence supports: accepted, rejected,
unacknowledged-ambiguous.

Framework suite **895**, full suite **1263**. Recorder `--validate-config` unchanged
(`sha256:8a48bcdd...a1468b`). F8 has not started.

## Built state (F8) — recorder integration (forks F15, F16)

The phase that connects the framework to the live recorder. Nothing in the framework's decision layers
changed; what landed is the **seam** (`framework_bridge.py`), the **pass driver**
(`market_depth_framework/orchestrator.py`), and the FEED-side **execution** of a plan through the
existing WebSocket connection. Framework version `0.7.0 -> 0.8.0`. Per-module references:
`Documents/framework_bridge.md`, `Documents/market_depth_framework.md`,
`Documents/websocket_client.md`, `Documents/processor.md`.

**Still four threads and three queues.** F8 adds no thread, no lock, no queue, no socket, and no file
descriptor — asserted by diffing every thread/lock/FD construct in the touched modules against `HEAD`,
and by a 25-cycle construct-and-teardown loop whose OS handle count and thread count do not move.

### Where the work happens

```
PROCESSOR thread                                     FEED thread
  run() loop
    framework_pass()                                   _on_open()
      bridge.maybe_rebalance(spot cache)                 authenticate -> subscribe spots
        FrameworkOrchestrator.rebalance()                -> _restore_framework_coverage()   [F16]
          WindowManager -> PriorityPolicy                -> _drain_framework_plan()         [F15]
          -> BudgetAllocator -> DepthAllocator
          -> SubscriptionState.set_desired()           _on_message()
          -> SubscriptionManager.reconcile()             classify -> _tee(packet)   [audit first]
      plans.publish(PlanEnvelope) -----------------> -> _observe_framework(packet)
                                                       -> _drain_framework_plan()  [F15]
                                                            BrokerAdapter.apply(plan)
                                                              AdapterTransport.send(frame)
      observations.take() <------------------------- bridge.publish_observation(
                                                            adapter.live_snapshot(),
                                                            adapter.take_rejections())
```

The rebalance runs in `TickProcessor.run()`, **never** inside `emit_second()` — the 1 s grid is not
allowed to inherit framework latency. The call has its own exception guard, so a framework fault
cannot reach the loop's outer handler in a way that ends PROCESSOR.

### Fork F15 — where FEED drains the plan mailbox

FEED does not poll: while connected it is blocked inside `transport.run_session()`. Its real execution
points are the callbacks, so the mailbox is drained at exactly two places:

- **tail of `_on_message`, strictly after `_tee(packet)`** — the lossless audit path is never delayed
  by framework work (a test watches the tee queue and the transport to assert the ordering);
- **end of `_on_open`** — the reconnect path, for a plan published while the socket was down.

Accepted residual, documented and tested rather than engineered away: **if the feed is connected but
completely silent, a pending plan waits for the next packet.** With no ticks there is no new metric or
window movement, so the pending plan is a re-issue of unchanged state. That is a latency
characteristic, not a correctness failure, and no timer was added to remove it.

### Fork F16 — with the flag ON the framework owns every option leg

| Concern | Flag OFF (default) | Flag ON |
| --- | --- | --- |
| Spot subscriptions | DSM | DSM (unchanged) |
| Spot state, boundaries, health, `current_spot_prices` | DSM | DSM (unchanged) |
| Option-leg subscriptions | DSM `_subscribe_strikes()` | **Framework only**, via `BrokerAdapter` |
| Resubscribe on reconnect | `_resubscribe_all()` | `_restore_framework_coverage()` for options; spots still via `_subscribe_spots()` |

Exactly one mechanism restores option coverage after a reconnect. In framework mode the DSM
never-shrink map holds **no** option leg, so `_resubscribe_all()` is deliberately not called and no leg
can be subscribed twice — tested directly (`DSM option-subscription calls == 0` with the flag on,
`> 0` with it off; reconnect produces no duplicate option subscription).

Boundaries still advance under the flag: they feed the window manager and the health file. Only the
*subscription* moved.

**`active_subscriptions` keeps meaning what it says.** In framework mode it is the union of the DSM map
(spots) and the adapter's claimed wire symbols (`REQUESTED` / `DELIVERING`, `:50` where premium), so the
health file reports actual live coverage rather than an empty option book. `_live_wire` is replaced
whole and never mutated, so the read needs no lock — the same lone-attribute rule as `last_recv_ts`.

### The transport seam

`AdapterTransport` in `websocket_client.py` is a deliberate **sibling** of `_send_frame`, never a reuse
of it. `_send_frame` swallows send failures, which is right for a DSM frame recorded in the never-shrink
map (the next resubscribe flushes it) and wrong for an adapter frame, whose leg must be marked failed
and re-planned. So `AdapterTransport.send` **raises**, translating everything — including
`TransportNotConnected` — into the framework's `TransportError`. It borrows the existing connection and
the existing `_client_lock`; it never creates a socket, a thread, or a connection lifecycle.

### Lock discipline

Unchanged: `_spot_lock` -> `_sub_lock`, with `_client_lock` a leaf. **No fourth lock was added.** An AST
audit asserts that no adapter or framework call appears inside a `_spot_lock` or `_sub_lock` block, so
no framework I/O ever runs under a state lock.

### Non-market-data messages

The adapter observes subscribe acknowledgements and errors on the control branch, before the existing
early return — the existing handling is untouched. An acknowledgement is **never** read as depth
confirmation; only a delivered packet on a leg's own wire symbol moves it to `DELIVERING`
(`accepted is True` with `is_delivering is False` is an explicit test).

### Reconnect — still UNKNOWN, still not claimed

`_restore_framework_coverage()` calls `handle_reconnect(desired)`, which forgets everything, reissues
baseline-before-premium, and confirms nothing until packets arrive. The log line says depth is
unconfirmed. **F7's UNKNOWN on reconnect depth restoration remains UNKNOWN**, as does the premium-slot
ceiling; F8 investigated neither.

### Health file

Two new sections appear **only** while the flag is on, so a flag-off health file is byte-for-byte what
it was before F8:

- `framework` — PROCESSOR's planning view (`bridge.stats()`);
- `framework_feed` — FEED's execution view (`plans_executed`, `plan_failures`, `desired_legs`,
  `premium_legs`, `effective_budget`, `delivering_legs`, `claimed_wire_symbols`).

They are separate keys because they are separate threads' facts.

### Flag-off regression

`framework_bridge_for()` returns `None` when the block is absent or disabled, and every F8 path in
PROCESSOR, FEED, and `main.py` is then inert: no adapter is constructed, no `framework` key appears in
processor stats, `feed.framework_stats()` is `None`, and the DSM owns option subscriptions exactly as
before. The old path was **not** replaced unconditionally. The recorder `config_hash` is unchanged
(`sha256:8a48bcdd...a1468b`) — a config with the framework block hashes identically to one without it.

Framework suite **1057**, full suite **1425** (run twice, identical, no flakes). F9 (replay/determinism) and F10
(true-scale live validation) have not started.


## Built state (F7.6) — adapter-side release derivation (fork F17)

F8 made the framework the only option-subscription owner, which exercises one interval on every session
start and every reconnect: a leg has been **dispatched** but has not yet **delivered** its first packet.
`SubscriptionManager.reconcile(desired, live)` compares against the delivery-derived snapshot (§20.4), so
during that interval it cannot see the leg and plans a re-tier as a plain `SUBSCRIBE`. The adapter used
to derive its release from the action's kind, so no release went out — it claimed the new wire spelling
while still holding the old one, and a stale premium record kept its pool slot until pruned.

The fix keeps that boundary intact and moves the decision to the layer that has the information:

```
SubscriptionManager :  desired state          vs  observed live state
BrokerAdapter       :  desired transition     vs  its own broker-leg state
```

`BrokerAdapter._obsolete_tiers(action)` returns the tiers of the wire legs the adapter holds for the same
`Instrument` at a tier other than the target — `REQUESTED` or `DELIVERING` only — and `_execute` releases
each of them before it claims. Release-before-claim is unchanged and absolute; F7.6 only makes the adapter
better at identifying what must be released.

**Invariant.** For a given `Instrument`, the adapter never claims a new wire tier while an obsolete wire
tier is still adapter-owned, even when neither leg has delivered a packet.

**Owned, dispatched, observed.** `desired` is what PROCESSOR wants, `owned` is what the adapter has
dispatched and not released, `observed` is what delivered packets prove. F7.6 uses the middle one for
release derivation and for nothing else: `live_snapshot()` is still delivery-derived, an owned leg is
still absent from it, and an acknowledgement is still not depth confirmation.

**Nothing else moved.** `SubscriptionManager`, `SubscriptionState`, `Instrument`, `desired vs live`,
the latest-wins mailbox, F15, F16, FEED/PROCESSOR ownership, the four threads, the three queues, the lock
model, reconnect semantics, the capacity model and the premium-slot value are all unchanged, and no
recorder integration file was touched. Both UNKNOWNs (reconnect depth restoration, the real premium
ceiling) remain UNKNOWN.

Adapter suite **137** (11 new), framework suite **1068**, full suite **1436** (run twice, identical, no
flakes). F9 and F10 have not started.

## Built state (F9) — the framework determinism harness (forks F18-F21)

F9 adds an **offline driver** for the framework, not a change to any live path. `replay.replay_file`
rebuilds Tier 2 by calling `TickProcessor.ingest()` / `emit_second()` directly and never calls `run()`,
so a Tier-2 rebuild is framework-free and stays that way (F8 asserts it:
`test_replay_emits_seconds_without_ever_rebalancing`). That is correct — the metric catalogue must not
depend on which legs happened to be subscribed when the log was recorded. So F9 adds a **second
driver** (fork F18 = A) rather than a flag on the first, and `replay.py` is untouched.

```
market_depth_recorder/framework_replay.py          # the driver + --verify (F18=A, F19=A)
market_depth_recorder/tools/validation/framework_soak.py   # N-replay soak + markdown report (F20=A)
market_depth_recorder/tests/test_framework_replay.py       # 32 tests, bounded synthetic session (F21=C)
```

### Where it sits

```
raw .jsonl.gz -> HEADER -> InstrumentManager.from_header (no REST)
                        -> build_universe (framework_bridge)
                        -> orchestrator_for(config.framework, clock=virtual)
                        -> BrokerAdapter(orchestrator.capability, RecordingTransport)

per packet: vclock["t"] = recv_ts; adapter.observe(packet); spot map updated;
            orchestrator.due(spots) -> rebalance -> adapter.apply(plan)
            -> invariant check -> one canonical JSON line
```

The clock is `lambda: vclock["t"]`, the same pattern `replay.py` uses. The module imports no `time`, no
`random`, no `uuid`; a source-level test asserts it.

### Real vs simulated

The orchestrator, every allocation layer, the adapter, wire rendering, the connection pool, the budget,
release-before-claim ordering, the spot prices, and the option depth packets are **real**. The broker is
a list (`RecordingTransport`). A leg the recording does not carry never delivers, so
`--confirm-after-passes N` (default 1) **synthesizes** a delivery for legs still `REQUESTED` after N
passes; that count is reported per record and again in the run digest. Nothing produced here is broker
evidence: **reconnect depth restoration and the real premium ceiling remain UNKNOWN**, settled only by a
live run (F10).

### Invariants enforced every pass

Checked against the adapter's own state, not the requested plan: premium occupancy never exceeds the
effective budget; no `Instrument` owned at two tiers at once; a symbol both released and claimed in one
pass releases first (the F7.6 invariant, now over a whole session). Each violation counts, logs at
ERROR, and makes the CLI exit non-zero; the driver does not abort, so a soak reports all of them.

### Threads, locks, FDs

None, none, and two. A framework replay is a single synchronous pass on the calling thread; the only
descriptors are the gzip reader and the allocation-log writer, both under `with`. No socket, subprocess,
SQLite, or DuckDB. A test asserts `threading.active_count()` is unchanged and that no store file appears.

### Nothing else moved

`replay.py`, `processor.py`, `websocket_client.py`, `main.py`, `framework_bridge.py`,
`broker_adapter.py`, and the Tier-2 output are untouched. The recorder `config_hash` is byte-identical
to the previous commit's. Full suite **1468** (run twice, identical, no flakes). F10 has not started.

Detail: `Documents/framework_replay.md`; measured session: `Documents/framework_soak_report.md`;
scope, forks, checklist, and gate: Plan_002 §22.12.

## Built state (F10A) — the live-validation watcher (forks F22-F26)

### Why there is a tool here at all

F10 closes Plan_001 **D18**, which needs one live session at true scale. The instrumentation audit that
opened F10A asked whether anything had to be built for that, and the answer was almost no: `health.json`
already carries every figure D18 wants — three queue depths, three drop counters, `degraded_level`,
`cycle_ms_p50` / `cycle_ms_max`, `rss_mb`, `active_contracts`, `actual_depth`, `restart_count`, and the
two framework views (PROCESSOR planning at `processor.py:618`, FEED execution at
`websocket_client.py:780-793`). What did not exist was a *record over time*: a snapshot answers "is it
healthy now", and D18 asks "what did a whole session look like". So `tools/validation/f10_live_monitor.py`
samples that same file on a cadence, appends a timeline, classifies each sample against the F25 rules,
and renders the F26 evidence skeleton. **No second monitoring system was introduced.**

### Where it sits

```
recorder process                          watcher process (separate terminal)
  PROCESSOR -> health.json  ---- read ---->  sample -> classify -> f10_timeline.jsonl
                                                          |
                                                          +-> evidence skeleton (--render)
```

One direction only. The watcher reads `health.json` and writes its own timeline, nothing else. It lives
under `tools/`, outside the recorder package, and imports no recorder module — the same placement rule
the F9 harness follows.

### Threads, locks, FDs

None, none, and one. It is a synchronous sample loop on the calling thread; the single descriptor is the
timeline file, opened per append under `with`. No socket, no subprocess, no SQLite, no DuckDB.

### The one thing it deliberately cannot do

It has **no kill path**. `os.kill`, `SIGTERM`, `SIGINT`, `terminate(` and `taskkill` are asserted absent
from its source by a test. When an abort criterion trips it prints `ABORT` and exits non-zero; a human
decides. That is not timidity — the thing being protected is the lossless raw path, and the correct
response is framework-first (`enabled: false`, graceful stop, restart), not process-first. The raw writer
reopens the same day's file in append mode, so a mid-session restart continues the audit trail rather
than forking it.

### Nothing else moved

No recorder runtime file was touched in F10A, and the framework remains disabled in the committed
config. Detail: `Documents/F10_LIVE_VALIDATION.md` (the F10B runbook); scope, forks, thresholds and
checklists: Plan_002 §22.13.
