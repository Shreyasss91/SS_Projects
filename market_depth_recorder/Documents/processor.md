# `processor.py` — Metric Processor (P4a + P4b)

Reference for the implemented state. Cites the design spec `§`; when code and spec diverge, fix the code
or update `PROJECT_NOTES.md` — never let this doc drift.

## Responsibility
`TickProcessor` is the single **compute thread** (spec §3.4.1, §5.1). It drains `proc_queue` into an
in-memory `latest_ticks` cache and, on each clock-aligned 1-second boundary, emits one second's rows for
every tracked symbol across **all four §4.1 tables**: `spot_states`, `option_strike_metrics` (§3.4.2
per-strike M1–M29 + the instantaneous `ofi`), `strike_window_metrics` (§3.4.3 rolling windows, one row per
`(symbol, w∈time_windows_sec)`), and `aggregated_window_metrics` (§3.4.4 multi-strike aggregates + regime,
one row per `(underlying, strike_window∈{SMALL,MEDIUM,LARGE})`). It guarantees a **uniform 1-second grid**
(§6.2): forward-fill from the last packet, staleness → NULL/NaN rows (`confidence=0.0`), degraded mode
never varies the cadence.

**Compute order per second (decision 37):** spot → per-strike (+ rolling windows, back-filling `ofi`) →
multi-strike aggregates → regime. The *same* `TickProcessor` runs live (thin subset → SQLite) and offline
(full catalog → DuckDB, P7); thin-vs-fat is purely which registry entries fire.

## Public API
- `TickProcessor(config, instrument_manager, proc_queue, db_queue, shutdown_event, *, time_fn=time.time,
  active_metrics=None, name="TickProcessor")` — `active_metrics` defaults to `recorder.live_metrics`;
  pass `"all"` for the full catalog (fat/replay, P7).
- `run()` — thread body: drain + classify + cache, fire `emit_second` on each aligned boundary, graceful
  drain on `shutdown_event`.
- `emit_second(now_epoch) -> list[envelope]` — the **pure per-second seam** (drain-independent). P7's
  simulated-clock replay calls it directly with virtual timestamps. Returns the same envelopes it
  enqueues on `db_queue`.
- `stats() -> dict` — counters for the P6 health file (`records_written`, `spot_rows_written`,
  `unknown_symbol_total`, `stale_rows_total`, `ticks_shed_total`, `db_rows_dropped_total`,
  `tracked_symbols`, `degraded_level`).
- `strip_suffix(symbol)` — drop the transport `:50` suffix to the DB symbol; `SPOT_COLUMNS` /
  `OPTION_COLUMNS` / `STRIKE_WINDOW_COLUMNS` / `AGG_COLUMNS` — the §4.1 column order each table's row
  tuples follow.

## db_queue contract (P4 defines; P5/P7 consume) — decision 38
Per second, one envelope per table: `{"table": <name>, "rows": [tuple, …]}` with tuples in **exact §4.1
column order** (`SPOT_COLUMNS` / `OPTION_COLUMNS` / `STRIKE_WINDOW_COLUMNS` / `AGG_COLUMNS`); guarded/
inactive metrics are `None`. `spot_states` one row per underlying with a known spot; `option_strike_metrics`
one row per tracked option symbol; `strike_window_metrics` one row per `(symbol, w)`;
`aggregated_window_metrics` one row per `(underlying, strike_window)` for underlyings with a known spot +
resolvable ATM/step. `recorder_meta` provenance is the writer's job (P5), not the processor's.

## Threads / locks / FDs
- **Thread owner:** the one `TickProcessor` thread (`run()`); P7 replay calls `emit_second()`
  synchronously (no thread).
- **State owner:** that same thread owns *all* mutable state (`latest_ticks`, `_known`, `_spot`,
  `_history`, and the P4b `_window` deques + `_prev` touch-books, counters) → **no lock** (single owner,
  decision 33). Cross-thread edges are only the thread-safe `proc_queue` (in) / `db_queue` (out).
- **FDs:** **none.** The processor holds no files, sockets, DBs, or subprocesses — only in-memory queues,
  NumPy arrays, and `deque`s. Adds zero FD surface.

## Behaviour details
- **Classification (decision 36):** a packet's `symbol` is stripped of `:50`; if the clean symbol is in
  `symbol_to_strike_map` → option (cached in `latest_ticks`, added to `_known`); else if it matches a
  configured `spot_symbol` → spot (updates `_spot[name]`, rejecting `ltp ≤ 0`); else counted in
  `unknown_symbol_total` and dropped (never crashes the loop).
- **ATM:** `spot_states.atm_strike` = the closest `active_strikes_list[name]` element to the spot LTP.
- **Forward-fill / staleness (§6.2):** every second recomputes from the cached last packet (forward-fill
  is automatic). If `now − recv_ts > staleness_timeout_sec`, the row is NULL/NaN with `confidence=0.0`,
  and a placeholder is pushed to history to keep the M22/M24 window aligned. The row is **still emitted**
  so the grid never gaps.
- **M22/M24 history (decision 41):** a per-symbol `StrikeHistory` (touch key + Top-5 OBI + relative
  spread, `maxlen = max(time_windows_sec)`) is pushed **before** the bodies run, so quote-stability and
  confidence see the current second. The window used is the **shortest** `time_windows_sec` (most
  responsive) — a documented choice for these two §3.4.2 columns.
- **Rolling windows (§3.4.3, P4b):** per option strike the engine keeps a `_window[clean]` deque of
  `WindowSample` (`maxlen = 2·max(time_windows_sec)+1`, reaching `BP_{t-2N}` for acceleration) and a
  `_prev[clean]` `TouchBook` for price-aligned ΔQ/OFI. Each second it computes the instantaneous OFI +
  ΔQ (ΔQ only when `depth() ≥ 10`, decision 47), back-fills `option_strike_metrics.ofi`, appends the
  sample, then emits one `strike_window_metrics` row per `time_windows_sec` window. A stale/gap second
  appends an **invalid** sample and clears `_prev` (breaking ΔQ/OFI continuity — boundary OFI is NULL, not
  0).
- **Aggregates + regime (§3.4.4, P4b):** for each underlying with a known spot + resolvable ATM/step, the
  engine collects the per-strike `StrikeFeatures` into `compute_underlying(...)`, which slices the
  ATM-centred SMALL/MEDIUM/LARGE windows and returns the three rows; `pinning_score`/`regime` are computed
  once per underlying and written identically into all three (decision 46). Window radii come from
  `small_window_strikes`, `atm_max_strike_range // medium_window_divisor`, and `atm_max_strike_range`.
- **Dependency closure (decision 37):** when any rolling/aggregate metric is active, `_core()` computes the
  per-strike scalars it needs (book_pressure, wobi, micro, spread, pooled q_bid/ask_w, wall) **regardless**
  of whether those columns are persisted; thin nulling then drops unselected columns at row assembly.
- **Degraded mode (§5.1):** `_degraded_level()` compares `max(proc_qsize, db_qsize)` to
  `warn/critical_watermark_pct` of `queues.max_queue_size`; transitions log WARNING/INFO. At **level ≥ 1**
  the CPU-heavy rolling reductions (`rolling.HEAVY_METRICS`: slopes, RV, liquidity flow/churn/intensity,
  velocity/accel, wall persistence/events) are skipped → NULL, while the cheap trend columns and the row
  itself are still emitted. At **critical (level 2)**, `_shed` also evicts already-stale cached ticks for
  the least-active symbols (counted in `ticks_shed_total`); they still emit NULL rows via `_known` so the
  grid holds. **The 1-second cadence is never varied.**
- **db_queue back-pressure:** `put(timeout)`; on `Full`, rows are counted in `db_rows_dropped_total` and
  logged WARNING (analytics sheds second — after `proc_queue`, before the always-protected raw path).

## Config keys consumed
`recorder.{resample_interval_sec, staleness_timeout_sec, live_metrics}`;
`metrics.{decay_k, effective_depth_pct, round_number_multiples, book_pressure_levels, wall_sigma_mult,
fill_probe_qty, time_windows_sec, small_window_strikes, medium_window_divisor}`; `regime.*` (thresholds
for the §3.4.4-C classifier); `queues.{max_queue_size, warn_watermark_pct, critical_watermark_pct}`.
Per-underlying `spot_symbol` / `name` / `atm_max_strike_range` for classification, spot routing, and the
aggregate window radii. No index/exchange/strike/CE/PE literal appears — the genericization contract holds
(CE/PE from the InstrumentManager map, steps/ranges/thresholds from config, all state keyed by `name`).

## Deferred to P5+ / later
`proc_queue`-side shedding and the health-file wiring (P6); process-sharding (`processor.mode: process`,
§5.2 headroom). The row envelopes are consumed by the SQLite live writer (P5) and the DuckDB analytical
writer + replay (P7), which reuse these metric bodies verbatim.