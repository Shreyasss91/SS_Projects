# `main.py` — Recorder Orchestrator (P6)

The conductor. P0–P5 built every worker as a standalone, tested thread; `main.py`'s
`RecorderOrchestrator` is the piece that **constructs, wires, supervises, and tears down** the live
pipeline. It is the `default` (no-mode) CLI entry and also implements `--status`.

Authoritative spec: **§3.1** (§3.1.1 milestones, §3.1.2 mid-day restart, §3.1.3 supervisor, §3.1.4
teardown drain, §3.1.5 guards), **§6.4** (health + supervision), **§8.2/§8.6** (CLI + reprocess).

## Responsibilities

1. **Milestone state machine + 1-second loop (§3.1.1, decision 56 — act-at-launch).**
   `Init` (resolve chains once) → `Connect` (build + start the pipeline immediately; the feed connects
   and subscribes spot LTPs regardless of wall time) → `Record` when `now ≥ session_start` (DSM option
   subscriptions flow from spot ticks) → `Close` at `session_end` (freeze the DSM) → `Teardown` at
   `session_end + teardown_grace_min` → `Reprocess` after a clean EOF. The spec's fixed 09:00/09:10
   fixtures collapse to "as soon as the scheduler launches us," which also *is* the §3.1.2 in-window
   restart path — no separate skip.
2. **Pipeline construction + start ordering (§5.1).** Builds the three bounded queues
   (`raw_file_queue` sized `queues.raw_file_queue_max`; `proc_queue`/`db_queue` sized
   `queues.max_queue_size`), the two shutdown events, and the `error_queue`; constructs the four workers;
   **starts consumers (raw · db · processor) before the producer (feed).** Encapsulated in
   `_build_default_pipeline`; a `pipeline_factory` seam lets tests inject fakes.
3. **Mid-day-restart recovery (§3.1.2, decision 57).** A launch/restart inside the record window calls
   `RestClient.get_quote` once per underlying → `feed.seed_spot(name, ltp)` (instant ATM resolution) and
   flags the overlap second via `db_writer.mark_restart_boundary(ts)` (P5 hook → `INSERT OR REPLACE`).
   Any quote failure (the endpoint needs a live broker session) → WARNING + fall back to the lazy WS
   spot-tick seed; one failure never aborts the seed of the other underlyings.
4. **Thread supervisor (§3.1.3, decision 58).** Every `supervisor_interval_sec`, scan `is_alive()` on all
   four workers and drain `error_queue`. A dead worker / error → ERROR log → teardown → **rebuild** fresh
   queues·events·threads → re-enter the record-start path (= restart recovery). Bounded by
   `max_restart_attempts` consecutive failures with backoff → **fail-fast** (exit non-zero) so an OS
   supervisor relaunches — never a tight crash-loop. Old threads/queues are joined + dropped before new
   ones are built.
5. **Teardown drain (§3.1.4, decision 60).** `shutdown_event.set()` + `feed.stop()`; join **feed →
   processor** (so the processor fully drains `proc_queue` and flushes its final 1-second rows into
   `db_queue`); *then* `db_shutdown_event.set()` + join **db_writer**; then join **raw_writer**. Each
   `join(timeout=10)`.
6. **Health file (§6.4, decision 62).** Every `health_write_interval_sec`, `utils.atomic_write` the
   payload (schema below). `--status` reads + pretty-prints it.
7. **Session guards (§3.1.5, decision 63).** Startup + periodic disk check (ERROR below
   `min_free_disk_mb`, non-blocking); optional trading-calendar idle (`skip_non_trading_days`).
8. **Reprocess launcher (§3.1.1 M6 / §8.6, decision 59).** After a clean EOF, launch `--replay --catchup`
   as a subprocess.

## Two shutdown events (why)

`shutdown_event` stops **feed · processor · raw writer**; `db_shutdown_event` stops the **db writer
separately**. If all four shared one event, at teardown the db writer could observe the event set with
`db_queue` momentarily empty (before the processor pushes its final second) and exit early, losing those
rows. Signaling the db writer only *after* the processor has joined closes that race race-free — no
change to any worker's code (each just takes the event it was handed).

## Public API

| Symbol | Purpose |
| --- | --- |
| `RecorderOrchestrator(config, instrument_manager, *, time_fn, sleep_fn, transport, rest_client, pipeline_factory, reprocess_launcher, loop_interval_sec, non_trading_poll_sec, name)` | Construct. Everything after `*` is injectable for deterministic offline tests. |
| `.run() -> int` | Run one session end-to-end (idle if a non-trading day → resolve → supervise → teardown → reprocess). Returns a shell exit code (`0` clean / `1` fail-fast). |
| `.stop()` | Request graceful shutdown from another thread / signal handler. |
| `.build_health(now) -> dict` | The §6.4 payload (also used by tests). |
| `Milestone` | Enum of milestone `state` strings. |
| `read_status(health_path) -> (code, text)` | The `--status` reader; missing file → exit 0 + friendly message. |

## Health schema (`health.json`, §6.4 + §9)

`timestamp`, `state` (milestone), `session_date`, `config_hash`, `websocket_status`,
`raw_file_queue_size`, `proc_queue_size`, `db_queue_size`, `last_raw_tick_time`, `active_contracts`,
`raw_dropped_total`, `proc_dropped_total`, `db_rows_dropped_total`, `degraded_level`, **`actual_depth`
(per-underlying map** — alarms on a silent 50→5 degrade), `rows_written`, `rows_ignored_total`,
`stale_rows_total`, `commit_error_count`, `corruption_recoveries`, `restart_count`, `raw_records_written`,
and the **P8 perf fields** `cycle_ms_p50` / `cycle_ms_max` (from `processor.stats()`, target < 30 ms post-P10-E) +
`rss_mb` (sampled via `utils.process_rss_mb()` each write, target < 500 MB). `--status` prints all three.

## Signals (P8)

The live daemon entrypoint (`__main__._cmd_run`) registers a **SIGTERM** handler → `orchestrator.stop()`
so a managed shutdown (systemd / `docker stop`) runs the full drain / EOF / FD-close path instead of
hard-killing the `daemon=True` workers mid-write (upholds lossless-raw). SIGINT already maps to
`KeyboardInterrupt` → `stop()`. Registration is best-effort (main thread + SIGTERM support); the handler
factory is unit-tested by direct invocation, and real OS-signal delivery is exercised in P9.

## Config keys consumed

`recorder.{session_start, session_end, teardown_grace_min, output_dir, health_file_path,
health_write_interval_sec, min_free_disk_mb, disk_check_interval_sec, skip_non_trading_days,
trading_holidays, supervisor_interval_sec, max_restart_attempts, log_level}`;
`reprocess.{auto_on_session_end, lock_file, log_file}`; `queues.{raw_file_queue_max, max_queue_size}`;
`websocket.{backoff_base, backoff_mult, backoff_max_sec}`; `openalgo.{host_server, api_key}` (for the
quote seed). `supervisor_interval_sec` (≥1) and `max_restart_attempts` (≥0) are new in P6 (§7.3).

## Threads · locks · FDs owned

- **Thread owner:** the main thread constructs, starts, supervises, and joins all four workers. P6 adds
  no worker threads and no worker locks.
- **Cross-thread hand-offs:** the thread-safe queues, the two `threading.Event`s, the `error_queue`, and
  the atomic single-word `mark_restart_boundary(ts)` write (P5-documented).
- **FDs:** the health temp fd (closed by `atomic_write`), the reprocess child's log file + run lock
  (both closed / `.wait()`-reaped / released). Every worker thread is joined on every exit path (clean
  teardown, crash-restart, KeyboardInterrupt) — no thread/queue/FD leak across a supervised restart.

## Additive touches to earlier modules (all tested)

- **P1 `instrument_manager.py`:** `RestClient.get_quote(symbol, exchange) -> float` (POST
  `/api/v1/quotes/`, response closed on every path); `InstrumentManager.resolved` property.
- **P3 `websocket_client.py`:** `seed_spot(name, price)`, `freeze_dsm()`, `connection_status` property,
  `last_recv_ts` attr, per-underlying `actual_depth` capture (first depth packet).
- **P2 `file_writer.py`:** `eof_written` flag (True after a clean EOF) — the reprocess gate.

## Genericization

No index/exchange/strike/CE-PE literal appears — every underlying comes from `config.underlyings`, all
per-underlying work (quote seed, `actual_depth`) is keyed by `name`.

## Deviation note (trading-calendar idle)

Decision 63's "idle until the next trading day" is implemented as a poll loop
(`non_trading_poll_sec`, default 3600 s) that idles while today is a weekend/holiday and proceeds on the
next trading day; it is interruptible via `stop()`. In practice an OS scheduler relaunches the daemon
daily, so the idle simply avoids connecting to a closed feed. Multi-day continuous looping across many
sessions in a single long-lived process is not a P6 goal (one `run()` = one session).

## Tests (`tests/test_main.py`, offline)

Virtual clock + fake workers via an injected `pipeline_factory`; a "crash" is an `is_alive()` flip and
teardown ordering is observed through a `RecordingEvent`. Covers: milestone transitions + record-gate;
full clean session (freeze + teardown + reprocess); teardown join order; supervisor restart-and-resume
and bounded fail-fast; mid-day seed via mocked `get_quote` + boundary mark + WS fallback; low-disk ERROR;
holiday idle; health schema + atomicity; `--status` (present + missing); reprocess gating on clean EOF +
lock acquire/release + disabled skip; and the SIGTERM handler (P8) triggering a graceful stop. These are
all **fake-worker** tests (injected `pipeline_factory`) — they exercise the orchestration logic, not the
real threads.

The **real four-thread pipeline** (real `_build_default_pipeline` + a scripted recorded feed + the real
reprocess subprocess) is exercised end-to-end by `tests/test_integration.py` — see `integration.md`.
(P6 originally verified this manually; P8 turned it into the committed harness.)
