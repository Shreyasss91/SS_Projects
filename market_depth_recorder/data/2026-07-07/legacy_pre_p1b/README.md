# Legacy pre-Phase-1b analytics reference (obsolete, retained for provenance)

**File:** `market_depth_analytics_20260707.pre-p1b.legacy.duckdb`
**Built:** 2026-07-07 19:27 IST · `built_by=replay` · `config_hash=sha256:fb97f393…`
**Source raw:** `../market_depth_raw_20260707.jsonl.gz` (~100-min session slice, 671,481 pkts → 5,951,233 rows)

## Why this reference was retired (not "wrong" — obsolete)

This store was the original golden reference for the 2026-07-07 dataset. It was replaced on 2026-07-13
by a fresh canonical rebuild from current code. It is **numerically superseded**, for three independent
and fully-understood reasons — none of which is a correctness defect in this file:

1. **Phase-1b introduced a numerically *superior* `_slope`.** The pure-Python closed-form `_slope`
   (`metrics/rolling.py`) that replaced the original NumPy version is both faster **and** more accurate.
   High-precision adjudication against an exact `fractions.Fraction` reference on the 45 rows that differed
   (`strike_window_metrics.book_pressure_slope`, |value| up to ~1.15e6): pure-Python is closer to the exact
   value in **41/45** rows, mean abs error **2.5e-10 vs 1.07e-9** (~4× better), max **relative** error
   **8.9e-14 vs 9.2e-13** (~10× better). The 45 rows over the verify `atol=1e-9` gate are this file (numpy)
   being *less* accurate, not the new build being wrong. Both agree to ~1e-12 relative.

2. **The provenance `config_hash` changed for a capture-only reason.** This file's hash `fb97f393`
   corresponds to config commit `3b6ceb5`; the current hash `8a48bcdd` (commit `212fb90`, 2026-07-07 15:51)
   differs only by NIFTY DSM **subscription-window** knobs (`initial_window` 1000→500,
   `expansion_threshold` 200→100, `expansion_step` 300→100). Those govern *which strikes get subscribed
   during live capture* — they have **zero** effect on any replayed metric value (the raw log already holds
   the ticks). `compute_config_hash` hashes `underlyings` wholesale, so these live-only knobs flipped the
   provenance stamp even though they change nothing in replay. This is why `--verify` aborted on config_hash
   against this file — a provenance flag, not data drift.

3. **The Arrow write backend is value-preserving.** The new build uses the Arrow columnar `finalize()`
   (write path only). Arrow was proven **bit-identical** to the legacy `executemany` path (slice A/B: exact
   73,952-row parity). It changes throughput, never a produced value.

## Do not use for verification

Future `--verify` must diff against the fresh canonical store beside the raw log
(`../market_depth_analytics_20260707.duckdb`, `config_hash=sha256:8a48bcdd…`). This legacy file is kept
only as a historical artifact of the pre-Phase-1b pipeline.
