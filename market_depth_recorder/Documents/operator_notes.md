# Operator Notes — Market Depth Recorder

Day-to-day operating guide: how to run it, what to do at EOD, how to verify a capture, precautions, and
configuration guidance. For setup/bootstrap see `SETUP.md`; for architecture see `ARCHITECTURE.md`; for the
live-validation record see `LIVE_RUN.md` + `phase_10E_notes.md`.

> **Golden rules**
> 1. Run everything as a module **from the parent `SS_Projects/`** (so `python -m market_depth_recorder`
>    resolves): `python -m market_depth_recorder <flags> --config market_depth_recorder/config.yaml`.
> 2. **Apply the FYERS TBT channel-spread patch and restart OpenAlgo** before any 50-level run, else the
>    NIFTY chain silently starves to 0 depth (see Precautions).
> 3. **Never hard-kill the daemon** (`kill -9` / Task-Manager End Task) — it truncates the raw gzip (no EOF)
>    and skips the reprocess. Stop with in-console **Ctrl-C**, a Linux **SIGTERM**, or let the
>    `session_end + teardown_grace` timer stop it.

---

## 1. Daily run

### 1.1 Before the open (one-time per day / per deploy)
| Step | Command / action | Expect |
| --- | --- | --- |
| Broker session | Log into OpenAlgo, connect **FYERS**; tokens expire ~03:00 IST → re-auth if stale | a quote returns |
| Patch present | `grep TBT_SYMBOLS_PER_CHANNEL broker/fyers/streaming/fyers_websocket_adapter.py` | prints the const |
| Patch live | **restart OpenAlgo** after applying the patch | — |
| Validate config | `python -m market_depth_recorder --validate-config --config market_depth_recorder/config.yaml` | `CONFIG OK` (exit 0) |
| Preflight depth | `python -m market_depth_recorder --preflight --config market_depth_recorder/config.yaml` | `NIFTY … actual_depth=50`, `SENSEX … actual_depth=5` (exit 0) |

If preflight shows `NIFTY actual_depth=5` → the patch is **not** applied / OpenAlgo not restarted, or the
FYERS TBT session is down. Fix before starting the daemon.

### 1.2 Start the daemon
```bash
python -m market_depth_recorder --config market_depth_recorder/config.yaml
```
- Start any time; a launch inside the record window is treated as a **mid-day restart** (it seeds ATM via a
  one-shot REST quote per underlying + `mark_restart_boundary`, no need to wait for a WS spot tick).
- Watch the log for the milestones: **Init → orchestrator start → pipeline started (4 workers) → feed
  connected → `[NIFTY] subscribed N legs` / `[SENSEX] subscribed N legs`**.
- Leave it running. It records `session_start..session_end`, freezes the DSM at `session_end`, then drains +
  builds the DuckDB at `session_end + teardown_grace_min`.

### 1.3 Mid-session health (any time)
```bash
python -m market_depth_recorder --status --config market_depth_recorder/config.yaml
```
**Healthy looks like:** `state=record`, `websocket_status=connected`, all three queue sizes bounded (near 0),
`raw_dropped_total=0`, `db_rows_dropped_total=0`, `degraded_level=0`, `actual_depth={NIFTY:50, SENSEX:5}`,
`rss_mb` well under 500, `cycle_ms_p50` under ~30 (see the re-tuned target below), `restart_count` stable.

---

## 2. End of day (EOD)

The daemon tears down **automatically** at `session_end + teardown_grace_min` (default 15:30 + 5 = 15:35):
DSM frozen → queues drained → **raw EOF written** → **reprocess subprocess auto-launched** (`--replay
--catchup`) → the fat **DuckDB** is built beside the raw → parent reaps the child and exits. You normally do
nothing. To stop early, use **Ctrl-C** in the daemon's console (Linux: `kill -TERM <pid>` / `docker stop`).

**After teardown, confirm the build (see the verification checklist §3):**
```bash
python -m market_depth_recorder --eod-report --config market_depth_recorder/config.yaml   # today, IST
# or a specific day:
python -m market_depth_recorder --eod-report --date 2026-07-07 --config market_depth_recorder/config.yaml
```
Exit **0 = clean** (no FAIL), **1 = at least one FAIL**. Report written to
`data/<date>/reports/eod_healthcheck_<date>.{md,json}`.

**If the daemon died uncleanly** (no EOF → reprocess skipped) or you were offline for a day, self-heal:
```bash
python -m market_depth_recorder --catchup --config market_depth_recorder/config.yaml
```
`--catchup` rebuilds every raw log that lacks an up-to-date DuckDB (oldest-first), across the base dir and
all `data/<date>/` sub-folders. (`reprocess.catchup_on_start: true` also runs this automatically on boot.)

---

## 3. Verification checklist (per capture)

Run these after a session; each is offline (no live market needed).

| Check | Command | PASS criterion |
| --- | --- | --- |
| **EOD health** | `--eod-report --date <d>` | exit 0; no `FAIL`. Known/acceptable WARNs: `raw.depth_level.SENSEX` (BFO 5<50, §9) and `ops.cycle_ms` if > target. |
| **Determinism** | `--replay <raw.gz> --verify --config …` | `VERIFY OK: no drift` (a fresh rebuild matches the canonical value-for-value). |
| **Live vs replay** | `--replay <raw.gz> --verify-against-live --config …` | `VERIFY OK … within the 2.0% live/replay boundary-timing tolerance` (or `no drift`). |
| **DuckDB sane** | query `recorder_meta` + the 4 tables | `built_by='replay'`, `config_hash` present; `spot_states / option_strike_metrics / strike_window_metrics / aggregated_window_metrics` all non-empty. |
| **Raw self-contained** | `zcat raw.gz | head -1` and `| tail -1` | HEADER has `instruments` + `config_hash` + `schema_version`; last line is the EOF meta (`close_timestamp`, `record_count`). |

**Reading verify output:**
- `VERIFY OK: no drift` — perfect match (determinism gate is zero-tolerance).
- `VERIFY OK: N/M rows differ (…%) — within the 2.0% … tolerance` — expected for `--verify-against-live`;
  the disposable live store diverges slightly from the replay at second boundaries (wall-clock vs timestamp
  emit). Not drift; the DuckDB from the lossless raw is the source of truth.
- `VERIFY FAILED: … exceeds the …% tolerance` or `config_hash mismatch` / `schema_version mismatch` — real
  problem: investigate (a config/formula change, a corrupted store, or a genuine regression).

---

## 4. Operator precautions

- **FYERS TBT patch is mandatory for 50-level — but it does not buy a full chain.** Without
  `Documents/evidence/openalgo_platform/openalgo_fyers_tbt_channels.patch` applied to OpenAlgo (and OpenAlgo restarted),
  every 50-depth sub is pinned to channel `"1"` → the NIFTY chain starves to **0 depth** (silent).
  Re-check after every OpenAlgo upgrade (upstream may overwrite it). **With** the patch, expect only
  **~15 legs at 50-level**: FYERS caps Market-Depth at **5 symbols per _connection_** (3 connections per
  app → `tbt_budget = 15`), and channels carry no capacity. The rest of the chain streams at 5-level or
  not at all until the hybrid allocator lands. Corrected 2026-08-25 — the earlier "5 symbols/channel,
  ceiling 250" wording is disproven; see `Documents/evidence/fyers_tbt_concurrency_20260714/tbt_concurrency_reconciliation_20260714.md`.
- **Never hard-kill.** `kill -9` / End-Task truncates the gzip (no EOF) → replay treats the file as
  incomplete and the auto-reprocess is skipped. Use Ctrl-C, Linux SIGTERM, or the timer. On **Windows** an
  external SIGINT/SIGTERM to a *detached* daemon does **not** deliver gracefully — run it in a foreground
  console and press Ctrl-C, or rely on the `session_end+grace` timer. (Linux/Docker: `docker stop` = SIGTERM
  = graceful drain.)
- **Broker tokens expire ~03:00 IST.** Re-auth FYERS in OpenAlgo before the open, or the feed won't connect.
- **SEBI static-IP (from 2026-04-01):** the recorder host's IP must be broker-whitelisted (quotes are
  IP-gated). Confirm a quote works from the host before a run.
- **Disk space:** the raw log is the lossless source of truth; low disk is the one sanctioned raw-loss
  boundary. Keep ≥ `recorder.min_free_disk_mb` free; the daemon ERRORs when below it. A full trading day of
  NIFTY 50-level ≈ tens of MB gzip raw + a larger DuckDB.
- **Single instance per deployment.** `health.json` and `reprocess.log/.lock` are un-dated singletons at the
  base `output_dir`; running two daemons against the same dir corrupts them.
- **Expiry day is noisy but fine:** crossed/locked books are pervasive (logged at DEBUG, not an error); the
  EOD report surfaces the crossed/locked *rate* as a data-quality note.

---

## 5. Runtime files — what's what (all under `data/`, all gitignored)

| File | Location | Stale? | Notes |
| --- | --- | --- | --- |
| `market_depth_raw_<date>.jsonl.gz` | `data/<date>/` | keep | **Lossless source of truth.** Everything rebuilds from this. |
| `market_depth_live_<date>.db` | `data/<date>/` | **disposable** | Thin real-time SQLite; not authoritative — the DuckDB is. Safe to delete. |
| `market_depth_analytics_<date>.duckdb` | `data/<date>/` | keep | Full analytical catalog; rebuilt from raw by replay/catchup. |
| `reports/eod_healthcheck_<date>.{md,json}` | `data/<date>/reports/` | keep | EOD health report. |
| `health.json` | `data/` (**base, un-dated**) | live | Liveness file for `--status`; **intentionally at the base** so `--status` is date-agnostic. Not stale while the daemon runs. |
| `reprocess.log` / `reprocess.lock` | `data/` (**base, un-dated**) | keep/live | Reprocess child's log + run-lock; **intentionally at the base** so the launcher/lock are date-agnostic. |

> **Do the base-dir singletons belong in a dated folder?** **No — by design (P10-B decision).** Only the
> day's *data* (raw/live/duckdb/reports) is date-partitioned; `health.json` and `reprocess.log/.lock` stay
> at the base so `--status`, the run-lock, and the launcher are date-agnostic. Any `run_*.log` /
> `verify_*.log` you create by redirecting daemon/verify stdout are **ad-hoc, not part of the design** —
> delete them freely (they are gitignored via `*.log`).

---

## 6. Configuration guidance (`config.yaml`, §7)

Everything is config-driven; a missing/out-of-range value fast-fails at startup (exit 1). Common knobs:

- **`openalgo.{host_server, websocket_url, api_key}`** — point at your OpenAlgo; set the **real** API key.
- **`websocket.transport: "raw"`** — keep RAW (default). The SDK path strips `feed_time`/`depth_levels`/
  `is_50_depth` (the recorder's core audit value); use `sdk` only for LTP/degraded cases.
- **`recorder.session_start/session_end` + `teardown_grace_min`** — the record window; teardown fires at
  `session_end + grace`. To test teardown quickly, set `session_end` a few minutes ahead (this is what the
  P10-E compressed run did) — `config_hash` excludes session times, so verification is unaffected.
- **`recorder.live_metrics`** — the thin subset written live to SQLite (the DuckDB always gets the full
  catalog). Must be registry names or `"all"`.
- **Per-underlying** — `requested_depth: 50` (records the actual level returned; BFO auto-degrades to 5);
  `initial_window` (ATM± points to subscribe); `expected_strike_step` + `strike_step_fallback`;
  `atm_max_strike_range` (aggregate matrix radius). Add any weekly-option underlying to the `underlyings`
  list — **no code change** (symbol/exchange/step are never hardcoded in the engine).
- **`recorder.date_partitioned: true`** — day's data in `data/<date>/`; base singletons stay flat.
- **`reprocess.auto_on_session_end: true`** — build the DuckDB automatically after a clean teardown.
  **`catchup_on_start: true`** — self-heal stale/missing DuckDBs on boot.
- **Session guards** — `min_free_disk_mb`, `disk_check_interval_sec`, `skip_non_trading_days`,
  `trading_holidays: [YYYY-MM-DD, …]`.
- **`regime.theta_pressure`** — write large numbers as `5000000.0` or `5.0e+6`, **never `5.0e6`** (unsigned
  exponent parses as a string in PyYAML; the loader now rejects it, but avoid the trap). All regime
  thresholds are validated numeric at startup.
- **Perf note:** `cycle_ms` target is a **report-only** threshold (`eod_report._CYCLE_MS_TARGET`, re-tuned to
  30 ms after P10-E) — not an engine tunable. `processor.mode`/`shards` are config-validated but the process
  path is not implemented; keep `mode: thread`.

---

## 7. Quick CLI reference

```bash
# from SS_Projects/ ; add --config market_depth_recorder/config.yaml to each
python -m market_depth_recorder --validate-config        # config OK?           exit 0/1
python -m market_depth_recorder --preflight              # live depth per udl   exit 0/1
python -m market_depth_recorder                          # RUN the daemon
python -m market_depth_recorder --status                 # read health.json
python -m market_depth_recorder --eod-report [--date D]  # health report        exit 0/1
python -m market_depth_recorder --replay [RAW] [--output D] [--from HH:MM --to HH:MM] [--underlying NAME]
python -m market_depth_recorder --catchup                # rebuild stale DuckDBs
python -m market_depth_recorder --replay RAW --verify              # determinism (zero-tolerance)
python -m market_depth_recorder --replay RAW --verify-against-live # vs live SQLite (1% tolerance)
```
