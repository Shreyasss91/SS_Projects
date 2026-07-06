# LIVE_RUN.md — P9 live-run session runbook

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

- [ ] Raw yields `feed_time` / `depth_levels` / `is_50_depth`: __
- [ ] Per-underlying actual depth NIFTY→50, SENSEX→5: __
- [ ] Per-level `orders` populated (M13/M14 computable): __
- [ ] `cycle_ms_p50` / `cycle_ms_max` (target < 15 ms thin): __
- [ ] `rss_mb` at full NIFTY+SENSEX scale (target < 500 MB — **authoritative** memory check): __
- [ ] OS handle/fd count for the process stable across the session (no slow leak): __

## D. Abort / rollback

- Stop = `Ctrl-C` (SIGINT) or `SIGTERM` → both run the graceful drain / EOF / FD-close path.
- A mid-session restart re-seeds ATM via one REST `get_quote` per underlying + `mark_restart_boundary`
  (the overlap second commits `INSERT OR REPLACE`), then subscribes — no need to wait for a WS spot tick.
- If NIFTY depth degrades to 5 (the §9 alarm fires), check the FYERS TBT session / the `:50` topic routing.
- The live SQLite store is disposable — the fat DuckDB is always rebuilt from the untouched raw log.
