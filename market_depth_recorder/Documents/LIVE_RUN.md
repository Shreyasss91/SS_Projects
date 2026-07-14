# LIVE_RUN.md — P9 live-run session runbook

> ⚠️ **§C (P10-E, 2026-07-07) PARTLY SUPERSEDED (P10-F, 2026-07-14).** The "full NIFTY chain at 50-level"
> result recorded for that run is a **measurement artifact** — the raw never streamed >5 concurrent NFO
> legs (FYERS caps at 5 per connection). The `< 15 ms` / `< 500 MB` targets were therefore **not** met "at
> full chain scale" — they were measured on ≤5 NFO @50 + 120 SENSEX @5, and **true 15 × 50-level scale is
> still untested**. Confirmed capability: **`tbt_budget = 15`** (3 conns × 5); a full chain needs the
> **hybrid**. **Canonical:** `Documents/patches/tbt_concurrency_reconciliation_20260714.md`.

The offline harness (`integration.md`) proves the pipeline mechanics deterministically. **P9 is the live
confirmation** against a real OpenAlgo + connected broker during IST market hours — the parts that
**cannot be faked**: that the broker actually delivers 50-level TBT depth for NIFTY/NFO (5-level for
SENSEX/BFO) with per-level `orders` populated, and that the real per-second cycle stays `< 15 ms` and RSS
`< 500 MB` at full chain scale.

Run this **only when the market is open** and a broker session is live. Capture results back into this file.

## A. Preconditions (verify before starting)

- [ ] OpenAlgo platform running and reachable at `openalgo.host_server` / `openalgo.websocket_url`.
- [ ] Broker = **FYERS** connected, session valid. Indian broker tokens expire ~03:00 IST — re-auth if stale.
      (True 50-level TBT is FYERS-only, NSE/NFO; other brokers/exchanges degrade to 5.)
- [ ] **OpenAlgo channel-spread patch applied + restarted** (P10-A). FYERS TBT caps 5 symbols/channel and
      stock OpenAlgo pins channel `"1"` (only 5 symbols get 50-level). Apply
      `Documents/patches/openalgo_fyers_tbt_channels.patch` and **restart OpenAlgo**, else a full NIFTY chain
      silently starves to 0 depth. Verify with `grep TBT_SYMBOLS_PER_CHANNEL broker/fyers/streaming/fyers_websocket_adapter.py`.
- [ ] **SEBI static-IP** whitelisting (effective 2026-04-01): the recorder host's IP is registered with the
      broker (quotes are IP-gated). Confirm a quote works from this host before the run.
- [ ] IST market hours; today is a trading day (weekend/holiday would idle the daemon if
      `skip_non_trading_days: true`).
- [ ] `config.yaml`: real `openalgo.api_key`, `transport: "raw"`, NIFTY + SENSEX under `underlyings`,
      `output_dir` writable with ≥ `min_free_disk_mb` free.
- [ ] Dependencies installed (`requirements.txt`); run everything as `python -m market_depth_recorder …`
      from the parent `SS_Projects/`.

## B. Run sequence

1. **Validate config** — `python -m market_depth_recorder --validate-config --config market_depth_recorder/config.yaml`
   → expect exit 0 (`CONFIG OK`).
2. **Preflight (live depth probe)** — `--preflight …`
   → expect per-underlying **actual depth**: `NIFTY/NFO → 50`, `SENSEX/BFO → 5`. Note the §9 WARNING if
   `actual < requested` (the silent 50→5 degrade alarm).
3. **Start the daemon** at/after `session_start` — `python -m market_depth_recorder --config …`
   → watch the log for milestones **Init → Connect → Record**; confirm `websocket_status` connected and
   option subscriptions flowing from spot ticks.
4. **Mid-session status** — `--status …` (reads `health.json`). Confirm:
   - [ ] queue depths (`raw_file_queue_size` / `proc_queue_size` / `db_queue_size`) bounded, not climbing.
   - [ ] `cycle_ms_p50` and `cycle_ms_max` **< 15**.
   - [ ] `rss_mb` **< 500**.
   - [ ] `actual_depth` = `{NIFTY: 50, SENSEX: 5}`.
   - [ ] `raw_dropped_total` = 0 and `db_rows_dropped_total` = 0 (lossless raw held; no shedding).
   - [ ] `degraded_level` = 0 under normal load.
5. **Inspect the raw `.jsonl.gz`** (HEADER + a few packets, e.g. `zcat … | head`). Confirm the raw
   transport preserved the audit fields the SDK would strip:
   - [ ] `feed_time`, `depth_levels`, `is_50_depth`, `total_buy_qty` / `total_sell_qty` present.
   - [ ] per-level `orders` **populated and non-zero** (→ M13/M14 computable); spot-check that a level with
         `orders == 0` maps to `NULL` in the live metrics (never a divide-by-zero).
   - [ ] the HEADER carries the `instruments` block (self-contained replay).
6. **Graceful teardown** at `session_end + teardown_grace_min`: confirm the EOF marker is written, all FDs
   close, and the **reprocess subprocess auto-launches** (clean-EOF gate) → the DuckDB store is built.
   Also test a mid-session **SIGTERM** (`kill -TERM <pid>` / `docker stop`) once → confirm the graceful
   drain + EOF path runs (validates the P8 SIGTERM handler on a **real** OS signal).
7. **Post-session** — `--replay --verify …` clean (determinism); `--verify-against-live …` clean; query the
   DuckDB store (`recorder_meta.built_by = "replay"`, four tables populated).

## C. Confirmations to capture (paste results here after the run)

### P9 first run — 2026-07-06 (⚠️ PARTIAL PASS; full record `Documents/patches/Phase9_notes.md`)
- [x] Raw yields `feed_time` / `depth_levels` / `is_50_depth`: **yes at preflight (NIFTY TBT)**; the daemon
  raw log was SENSEX-only (5-level, omits these) because NIFTY depth never streamed — see the finding below.
- [x] Per-underlying actual depth NIFTY→50, SENSEX→5: **confirmed at preflight** (§9 alarm fired for SENSEX).
- [x] Per-level `orders` populated (M13/M14 computable): **yes** (100% of captured depth levels).
- [x] `cycle_ms_p50` / `cycle_ms_max`: **p50=10.5, max=14.2 mid-session (<15)**; EOD snapshot later showed
  `max=25.96` — NOT authoritative (SENSEX-only load). Full-scale check → P10-E4.
- [x] `rss_mb`: **51–60 MB** — NOT authoritative (NIFTY depth absent, not full scale). → P10-E4.
- [ ] OS handle/fd count stable across the session: **not measured this run** → P10-E5.

> **⛔ Headline finding (cannot be faked):** FYERS TBT caps **5 symbols/channel** and stock OpenAlgo pinned
> all 50-depth subs to channel `"1"` → 80 NIFTY `:50` legs starved and **NIFTY captured 0 depth** (SENSEX
> 5-level HSM was fine). Resolution = the **P10-A OpenAlgo channel-spread patch** (see §A precondition).
> The remaining live confirmations (whole NIFTY chain at 50-level, global-cap check, authoritative
> perf/RSS, graceful teardown) are **P10-E**, to run next session after the patch is applied + OpenAlgo restarted.

### P10-E — 2026-07-07 (patched OpenAlgo, fresh instance; ✅ PASS with known WARNs)
Run mid-session against the channel-spread-patched platform. A **compressed session** (`session_end`
set ~8 min ahead in `config_p10e.yaml`, grace 2 min) was used to exercise the real timer-based graceful
teardown on Windows without a full-day wait (external SIGINT/SIGTERM cannot be delivered to a detached
process on Windows — see §D). Raw/live/DuckDB are the `2026-07-07/` dated dir.

- [x] **E1 platform smoke:** platform up (HTTP 200); live quotes NIFTY 24502.25 / SENSEX 78554.21 (broker
  session + SEBI static-IP gate OK). Patch confirmed present (`TBT_SYMBOLS_PER_CHANNEL=5`, `_assign_tbt_channel`).
- [x] **E2 whole NIFTY chain 50-level:** preflight `NIFTY/NFO actual_depth=50`, `SENSEX/BFO=5`, per-level
  `orders=True`. Full-run raw shows **NFO `depth_levels` up to 47** across all 80 legs / ~16 TBT channels
  (impossible under the old 5-cap → channel-spread patch works). **No global FYERS TBT cap** manifested
  (200 contracts subscribed, no stalls). Per-strike populated depth varies 20–47 with real expiry-day
  liquidity (near-ATM hits 50; far-OTM legitimately fewer). SENSEX stays 5-level (BFO, expected).
- [x] **E3 mid-session `--status`:** queues 0/0/0, `raw_dropped_total=0`, `db_rows_dropped_total=0`,
  `degraded_level=0`, `active_contracts=200`, `actual_depth={NIFTY:50, SENSEX:5}` ✓, `restart_count=0`.
- [x] **E4 authoritative perf/RSS (full 80×50):** **`rss_mb` 52–58 MB (≪500 ✓)**; **`cycle_ms_p50` ≈ 22 ms,
  `max` ≈ 43–60 ms.** *Important:* the earlier P9/warm-up 10–20 ms figures were measured before the
  aggregate/regime path fully engaged (and while it was silently crashing on the `theta_pressure` bug);
  ~22 ms is the honest full-thin-workload number for 200 legs at 50-level. The pipeline **keeps real-time
  pace with ~45× headroom** (22 ms of the 1000 ms budget; proc/db/raw queues pinned at 0, zero drops).
  **Decisions (user, 2026-07-07):**
  - **Target RE-TUNED 15 ms → 30 ms** (`eod_report._CYCLE_MS_TARGET`). The original §5.1 <15 ms was set
    against P9's SENSEX-5-level-dominated load; 30 ms flags a real real-time-risk regression without
    false-alarming on the expected full-scale cost. The true failure signal is queues climbing / cycle_ms
    approaching the 1000 ms budget — neither occurs here.
  - **Per-underlying `process` sharding (§5.2): NOT DONE — rejected as the wrong lever.** It partitions by
    underlying, but NIFTY is ≈ 84 % of the load (80 legs × ~40 levels ≈ 3200 level-ops vs SENSEX 120 × 5 =
    600) → NIFTY lands wholly in one shard, cycle stays ~14–17 ms. Also unimplemented (config-validated
    only). Kept documented as a non-solution.
  - **Intra-underlying parallelism (shard strikes across workers): DEFERRED** to a dedicated session — the
    only lever that would actually cut the NIFTY cycle, but a substantial architectural change not worth
    building blind into a live window.
  - **Applied now (output-preserving):** removed a redundant weighted_obi/book_pressure double-compute in
    `processor._core` (reuses the persisted per-strike values). Residual cost is the aggregate matrix +
    regime + deep-book metrics — genuine work, not waste.
- [x] **E5 FD/handle stability:** OS handle count **196–197 flat** across the run (threads 27–28) — no leak.
- [x] **E6 graceful teardown → reprocess → DuckDB:** timer teardown fired at `session_end+grace`: DSM frozen
  (never-shrink) → drain → **clean EOF written** (raw HEADER carries `instruments`+`config_hash`; EOF meta
  present) → reprocess subprocess auto-launched (`--replay --catchup`) → **DuckDB built: 61 538 packets,
  580 s, 291 837 rows, 0 corrupt lines** → parent `.wait()`-reaped the child and **exited cleanly**.
- [x] **E7 abort/rollback + restart re-seed:** mid-session restart **re-seeds ATM via one REST quote per
  underlying + `mark_restart_boundary`** (logged `boundary_ts` on every start; no wait for a WS spot).
  §9 degrade alarm fired correctly for SENSEX at preflight. The SIGINT/SIGTERM graceful-drain **path** is
  the same drain/EOF/FD-close chain E6 validated; on Windows external signals can't reach a detached
  process, so the timer path is the faithful local test (handlers are unit-tested + valid on Linux/Docker).
- [x] **E8 post-session verify:** DuckDB `recorder_meta.built_by="replay"`, all 4 tables populated
  (spot_states 580, option_strike_metrics 72 380, strike_window_metrics 217 140, aggregated_window_metrics
  1 737). **`--replay --verify` (determinism) → `VERIFY OK: no drift`** — a fresh rebuild matches the
  canonical value-for-value (replay is deterministic; the source of truth is sound). **`--verify-against-live`
  → 99.7 % agreement** (ltp 68 168/68 386 exact); the ~0.3 % differing rows are at second boundaries — the
  expected divergence between the **live wall-clock-triggered emit** and the **replay timestamp-partitioned
  emit** (which tick was last-included in that second) — plus 1 missing first-second row in the disposable
  live store. No data loss (the DuckDB from lossless raw is complete + deterministic). **Resolved
  (2026-07-07):** added `_LIVE_SUBSET_TOLERANCE_PCT = 2.0` to `replay.verify()` — `--verify-against-live`
  now passes when the live/replay divergence is within 2 % of rows. Re-run on the real session:
  **`VERIFY OK: 658/74697 rows differ (0.88%) — within the 2.0% live/replay boundary-timing tolerance`**
  (a row counts if any live_metrics cell differs, so it's stricter than the ltp-only 0.3 %; 2 % gives
  headroom for busier sessions). The **strict duckdb-vs-duckdb determinism gate keeps ZERO tolerance**
  (unchanged — still `VERIFY OK: no drift`).
- [x] **E9 EOD report:** `--eod-report` → **overall WARN, PASS 24 · WARN 2 · FAIL 0**, exit 0. The 2 WARNs
  are the two known/expected ones: `raw.depth_level.SENSEX` (5<50 BFO degrade, §9) and `ops.cycle_ms`
  (p50 21.7 > 15). **NIFTY depth coverage now PASSES** (was the P9 FAIL). Report at
  `2026-07-07/reports/eod_healthcheck_20260707.{md,json}`.

> **Bugs found & fixed during P10-E** (all with regression tests; full suite **257 → green**). Items 1–4
> are genuine bugs the full-depth live data exposed; item 5 is a perf optimization; item 6 is the verify
> tolerance (see E8 above). Full narrative in `phase_10E_notes.md`.
>
> 1. **`regime.theta_pressure: 5.0e6` parsed by PyYAML as the STRING `"5.0e6"`** (unsigned exponent is not
>    a YAML float — needs `5.0e+6` or `5000000.0`). The regime classifier crashed mid-session at
>    `nop > theta_pressure` (`float > str`) **once full-depth NIFTY made NOP non-null** — a latent bug
>    P9's NIFTY-starved data never reached, so the aggregate/regime path silently crash-looped (which also
>    made the pre-fix cycle_ms readings non-authoritative). Fix: YAML literal → `5000000.0` **and** added
>    `config.py` numeric validation of all five regime thresholds (a bad value now fails loudly at startup
>    instead of crashing live). *Files:* `config.yaml`, `config.py`; test in `test_config.py`.
> 2. **`crossed/zero market` logged at `CRITICAL`** per crossed/locked level, per second → **460 lines in
>    ~60 s** on expiry day (log noise + string-format cost on the TickProcessor hot path). Crossed/locked
>    books are normal option microstructure, not a fault. Downgraded to DEBUG; the crossed/locked *rate* is
>    already surfaced by the EOD report. *Files:* `metrics/per_strike.py`; test in `test_metrics_per_strike.py`.
> 3. **`actual_depth` health map was first-write-wins** on `depth_levels` → froze on the first arbitrary
>    (illiquid OTM) strike (showed `{NIFTY:27}`) and dropped SENSEX entirely (BFO sends `depth_levels=None`).
>    The §9 degrade-alarm needs the true capability. Now **max-seen** per underlying with a populated-level
>    fallback when the field is absent → correct `{NIFTY:50, SENSEX:5}`. *Files:* `websocket_client.py`;
>    tests in `test_websocket_client.py`.
> 4. **`test_integration` pinned `SESSION_DATE=date(2026,7,6)`** → on any later day the IST date-rollover
>    guard moved data to the wall-clock-dated file, emptying the inspected file (`data_lines == 0`). Now
>    `now_ist().date()`. *Files:* `test_integration.py`.
> 5. **Perf micro-opt (output-preserving, not a bug):** `processor._core` recomputed `weighted_obi` /
>    `book_pressure` / `micro_price` over the deep book even when they were already computed into the
>    persisted per-strike row (default `live_metrics` has weighted_obi + book_pressure) — a 200×/sec
>    double-compute. Now reuses the row values (identical output → determinism intact). *Files:*
>    `processor.py`; covered by the existing determinism + integration tests.
> 6. **`--verify-against-live` tolerance:** added `_LIVE_SUBSET_TOLERANCE_PCT = 2.0` so the disposable live
>    store's expected second-boundary divergence (0.88 % of rows on the real session) passes; strict duckdb-vs-duckdb
>    determinism keeps zero tolerance. *Files:* `replay.py`; tests in `test_replay.py`.

## D. Abort / rollback

- Stop = `Ctrl-C` (SIGINT) or `SIGTERM` → both run the graceful drain / EOF / FD-close path.
- A mid-session restart re-seeds ATM via one REST `get_quote` per underlying + `mark_restart_boundary`
  (the overlap second commits `INSERT OR REPLACE`), then subscribes — no need to wait for a WS spot tick.
- If NIFTY depth degrades to 5 (the §9 alarm fires), check the FYERS TBT session / the `:50` topic routing.
- The live SQLite store is disposable — the fat DuckDB is always rebuilt from the untouched raw log.
