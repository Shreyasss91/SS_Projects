# Phase 10-E — Live Validation Notes (2026-07-07)

Full narrative record of the P10-E live-validation session. Companion to `LIVE_RUN.md` §C (the checklist)
and `CHANGELOG.md` (the dated entry). Outcome: **PASS with two known WARNs; 6 code changes (4 bugs, 1 perf
opt, 1 verify tolerance); test suite 254 → 257 green.**

---

## 1. Purpose & setup

P10-E is the live confirmation of the P10-A **OpenAlgo FYERS-TBT channel-spread patch** — the parts that
cannot be faked offline: that the **whole NIFTY weekly chain streams true 50-level TBT depth** (not just 5
legs), that there is **no global FYERS cap** beyond the per-channel 5, and the **authoritative perf/RSS** at
full 80×50-level scale that P9 (NIFTY-starved) and the P8 harness could not measure.

**Preconditions verified:** patched OpenAlgo running (fresh instance) + FYERS session live (quotes returned
for NIFTY 24502.25 / SENSEX 78554.21 → broker + SEBI static-IP gate OK); patch present in
`broker/fyers/streaming/fyers_websocket_adapter.py` (`TBT_SYMBOLS_PER_CHANNEL=5`, `TBT_MAX_CHANNELS=50`,
`_assign_tbt_channel`); IST market hours (~11:10, mid-session); deps importable (`openalgo==2.0.2`).

**Run strategy — compressed session.** On Windows a detached daemon **cannot** be gracefully stopped by an
external SIGINT/SIGTERM (the first `kill -INT` hard-killed the process and truncated the gzip — no EOF). The
faithful graceful path is the **timer-based auto-teardown** at `session_end + teardown_grace`, which is also
the production path. To exercise it without a full-day wait, a throwaway `config_p10e.yaml` set
`session_end` ~8 min ahead (grace 2 min). `config_hash` excludes session times, so determinism/verify are
unaffected. Data landed in the `data/2026-07-07/` dated dir.

---

## 2. Checklist results (E1–E9)

| E | Result |
| --- | --- |
| E1 platform smoke | ✅ HTTP 200; live quotes both indices; patch present. |
| E2 whole NIFTY 50-level | ✅ preflight `NIFTY=50 / SENSEX=5`; raw NFO `depth_levels` **up to 47** across ~16 channels; **no global cap**; 200 contracts, no stalls. |
| E3 mid-session `--status` | ✅ queues 0, drops 0, degraded 0, `actual_depth={NIFTY:50,SENSEX:5}`, `restart_count=0`. |
| E4 perf/RSS | ⚠️ rss 52–58 MB (✓); **cycle_ms_p50 ≈ 22 ms, max ≈ 43–60 ms** — keeps pace, exceeds old 15 ms target. |
| E5 FD stability | ✅ handles **196–197 flat**, threads 27–28 — no leak. |
| E6 teardown → reprocess → DuckDB | ✅ clean EOF → auto-reprocess → **291 837 rows, 0 corrupt** → clean exit. |
| E7 restart re-seed / abort | ✅ REST re-seed + `mark_restart_boundary`; §9 degrade alarm fired; graceful drain = E6. |
| E8 post-session verify | ✅ determinism `VERIFY OK: no drift`; DuckDB 4 tables + `built_by=replay`; verify-against-live 99.7 % (within new 1 % tolerance). |
| E9 EOD report | ✅ PASS 24 · WARN 2 · FAIL 0, exit 0; NIFTY depth coverage now PASSES (was P9 FAIL). |

**Key measured facts:**
- Subscriptions: NIFTY 80 legs (ATM±1000 @ step 50 → 40 strikes × CE/PE) at 50-level; SENSEX 120 legs
  (ATM±3000 @ step 100 → 60 strikes × CE/PE) at 5-level. Total 200 contracts.
- Raw log: 61 538 packets, 580 s captured, 5.7 MB gzip. Live SQLite 13 MB. DuckDB (full catalog) 55.8 MB,
  291 837 rows across the 4 tables (spot_states 580, option_strike_metrics 72 380, strike_window_metrics
  217 140, aggregated_window_metrics 1 737).
- NIFTY was on **expiry day** (07-JUL-26) — deep ITM/ATM books; crossed/locked spreads pervasive (this is
  what exposed bug #2's log flood at scale).

---

## 3. Bugs found & fixed (the value of running live)

Every one of these was **latent until full-depth NIFTY data hit the pipeline** — none is reproducible from
P9's NIFTY-starved capture or from the Python-dict test fixtures. This is exactly why P10-E exists.

### Bug 1 — `theta_pressure` YAML exponent trap (processor crash-loop)
`regime.theta_pressure: 5.0e6` → **PyYAML parses an unsigned exponent as the STRING `"5.0e6"`** (only
`5.0e+6` / `5000000.0` parse as float). The regime classifier does `nop > theta_pressure`; once full-depth
NIFTY produced a non-null net order pressure, that became `float > str` → `TypeError` → `TickProcessor`
crash → supervisor rebuild loop. P9 never hit it (NIFTY 0-depth → NOP stayed null; the guard
short-circuited). **Side effect:** the pre-fix cycle_ms readings (10–20 ms) were **not authoritative** — the
aggregate/regime path was crashing before it finished, so it wasn't in the measured cycle.
**Fix:** literal → `5000000.0`; **and** `config.py` now validates all five regime thresholds numeric
(`v.num`), turning a latent live crash into a clear startup failure. Test: `test_config.py` negative case
`("regime","theta_pressure") "5.0e6" → "regime.theta_pressure"`.

### Bug 2 — `crossed/zero market` logged at CRITICAL (hot-path flood)
`metrics/per_strike.py::_spread` logged `logger.critical(...)` for every crossed (<0) or locked (==0) book.
On expiry day across 80 legs that was **460 lines in ~60 s** — log noise + per-level string formatting on
the single-owner `TickProcessor` thread. Crossed/locked books are **normal option microstructure**, not a
fault. **Fix:** downgraded to DEBUG; the crossed/locked *rate* is already a first-class EOD-report check.
Data return unchanged (spread stays lossless). Test: `test_metrics_per_strike.py` asserts DEBUG level.

### Bug 3 — `actual_depth` health map first-write-wins
`websocket_client.py::_capture_actual_depth` recorded the **first** `depth_levels` seen per underlying. The
first NIFTY packet was an illiquid OTM strike (27 levels) → the §9 health map froze at `{NIFTY:27}` forever;
and SENSEX/BFO packets carry `depth_levels=None` → SENSEX was **never recorded at all**. The §9 degrade
alarm needs the true 50-level capability. **Fix:** track **max-seen** per underlying, with a fallback to the
populated per-side level count when `depth_levels` is absent (so BFO registers 5) → correct
`{NIFTY:50, SENSEX:5}`. Tests: `test_websocket_client.py` (max-seen retained; thin-first updates upward;
BFO None-fallback).

### Bug 4 — `test_integration` hardcoded a past `SESSION_DATE`
`SESSION_DATE = date(2026,7,6)` → on any later day the file/db writers' **IST date-rollover guard** moved
all data to the wall-clock-dated file, leaving the inspected (session_date) file empty → `data_lines == 0`.
Surfaced because the run day (07-07) ≠ the pinned date. **Fix:** `SESSION_DATE = now_ist().date()`. (Also a
reminder that the tests use Python-dict configs, which is why bugs 1 & 3 slipped past the suite.)

### Change 5 — perf micro-opt (output-preserving, not a bug)
`processor._core` recomputed `weighted_obi` / `book_pressure` / `micro_price` over the deep book even when
they were already computed into the persisted per-strike row (default `live_metrics` includes weighted_obi +
book_pressure) — a 200×/sec double-compute. Now reuses the row values via `_reuse_*` flags (identical output
→ determinism intact). Covered by the determinism + integration tests.

### Change 6 — `--verify-against-live` tolerance (see §4)

---

## 4. E4 perf & E8 verify — the two nuanced findings

### E4 — cycle_ms 22 ms > 15 ms at full scale (decisions taken)
The honest full-thin-workload number for 200 legs at 50-level is **cycle_ms_p50 ≈ 22 ms** (max ≈ 43–60 ms, a
one-time warm-up spike). This is **not a real-time failure**: the processor uses ~22 ms of each 1000 ms
second and the proc/db/raw queues stay pinned at 0 with zero drops (~45× headroom). The real failure signal
would be queues climbing or cycle_ms approaching 1000 ms — neither occurs.

**Decisions (user, 2026-07-07):**
- **Re-tune the target 15 ms → 30 ms.** `eod_report._CYCLE_MS_TARGET = 30.0`. The original §5.1 <15 ms was
  set against P9's SENSEX-5-level-dominated load and is unrealistic at true 50-level NIFTY scale. 30 ms
  flags a genuine regression without false-alarming on the expected cost.
- **Do NOT do per-underlying `process` sharding (§5.2) — it is the wrong lever.** It partitions by
  underlying, but NIFTY is ≈ 84 % of the load (80 legs × ~40 levels ≈ 3200 level-ops vs SENSEX 120 × 5 =
  600). NIFTY lands wholly in one shard → its cycle stays ~14–17 ms. (It is also unimplemented — config
  validates `processor.mode: process` / `shards` but `main.py` always builds the single-thread processor.)
  Kept documented as a **non-solution**.
- **Defer intra-underlying parallelism** (sharding strikes across workers) — the only lever that would
  actually cut the NIFTY cycle — to a dedicated session. Substantial architectural change; not worth
  building blind into a live window, and not needed for real-time pace today.

### E8 — verify-against-live 99.7 %, tolerance added
`--replay --verify` (duckdb-vs-duckdb determinism) was **clean: `VERIFY OK: no drift`** — replay is fully
deterministic. `--verify-against-live` (duckdb-vs-live-SQLite) showed a **1-row-count diff + value diffs**.
Investigation (68 386 shared ltp cells): **99.7 % match exactly**; the ~0.3 % that differ are at second
boundaries. Root cause: the **live store is emitted on a WALL-CLOCK grid** (emit fires as the boundary
passes, seeing whatever ticks have arrived) while **replay rebuilds on a TIMESTAMP grid** (every tick of
second T → T). At boundaries they disagree on which tick was "last-in-second"; the live store may also miss
its very first second. This is **not drift** — the canonical DuckDB (from the lossless raw) is verified
byte-identical by the strict determinism pass, and the live SQLite store is explicitly disposable.
*(The apparent "1-second lag" in the first few mismatch samples was a red herring — cherry-picked from the
mismatch-only list; the T-1 hypothesis holds for only 37 % of rows = coincidental unchanged-ltp seconds.)*

**Resolution:** `replay.verify()` gained `_LIVE_SUBSET_TOLERANCE_PCT = 2.0` — `--verify-against-live` passes
when < 2 % of rows diverge and reports `VERIFY OK: N/M rows differ (…%) — within the 2.0% live/replay
boundary-timing tolerance`. Re-run on the real session: **`VERIFY OK: 658/74697 rows differ (0.88%)`** (the
row-level count is stricter than the ltp-only 0.3 %, since a row counts if ANY live_metrics cell differs; 2 %
gives headroom for busier sessions). The **strict duckdb-vs-duckdb determinism gate keeps ZERO tolerance**
(unchanged). Tests: `test_replay.py` (within-tolerance passes; zero-tolerance still fails).

---

## 5. Files touched

**Recorder code:** `metrics/per_strike.py` (bug 2), `websocket_client.py` (bug 3), `processor.py` (change
5), `config.py` (bug 1 validation), `config.yaml` (bug 1 literal), `eod_report.py` (E4 target),
`replay.py` (E8 tolerance).
**Tests:** `test_metrics_per_strike.py`, `test_websocket_client.py`, `test_config.py`, `test_integration.py`,
`test_replay.py`, `test_eod_report.py`. **Suite: 257 passed.**
**Docs:** `LIVE_RUN.md`, `CHANGELOG.md`, `phase_10E_notes.md` (this file), `operator_notes.md`, and the plan
`refer-market-depth-recorder-design-md-an-peppy-dolphin.md` (P10-E marked done).

---

## 6. Residual / follow-ups

- **Open (deferred):** intra-underlying parallelism for `cycle_ms` headroom (not needed for real-time pace).
- **Windows signal limitation (documented):** external SIGINT/SIGTERM don't gracefully stop a detached
  daemon on Windows; use in-console Ctrl-C or the `session_end+grace` timer. On Linux/Docker the handlers
  deliver normally (`docker stop`/systemd SIGTERM → graceful drain).
- **D2 holds:** whole chain at 50-level with no hybrid. Hybrid stays a documented fallback only (would
  re-open only if a global FYERS cap appeared — it did not).
