# Validation Artifacts — Offline Replay Optimization

**These are historical validation artifacts, not maintained tooling.** They are preserved so the
key correctness investigations behind the offline-replay optimization (milestone commit `1641f22`)
remain reproducible and auditable. They are frozen snapshots tied to the 2026-07-07 representative
dataset and the state of the code at the time — they are *not* kept up to date and are not on any
runtime path.

For the maintained, generalized equivalents, see instead:
- `market_depth_recorder/tools/validation/highprec_slope.py` — the generalized exact-`Fraction`
  slope-accuracy harness (accepts any captured-series file via CLI).
- `market_depth_recorder/tools/validation/duckdb_table_diff.py` — the generalized memory-safe
  DuckDB-side determinism / value-parity diff.

Narrative context: `Documents/PERFORMANCE.md` (§6) and
`Documents/archive/offline-replay-optimization-engineering-journal.md`.

---

## What each artifact is

| Artifact | What it is |
| --- | --- |
| `capture_series.py` | One-off replay harness that wraps `TickProcessor._window_rows` and captures the **exact `book_pressure` input series** feeding `_slope` for a fixed set of target `(symbol, ts, time_window)` keys, plus `ctx.eps`. Writes `captured.json`. No DB output — inputs only. |
| `dump_targets.py` | One-off that queries the arrow rebuild vs the legacy store and dumps the **45 `book_pressure_slope` rows over `atol=1e-9`** (their keys + stored `built`/`ref` values) to `targets.json`. |
| `captured.json` | The captured input series (`{"eps": <float>, "series": [{symbol, ts, n, y:[...]}, ...]}`) for the 45 rows — the exact evidence fed to the high-precision adjudication. |
| `targets.json` | The 45 target keys with their stored `built` (pure-Python) and `ref` (numpy) slope values, used to cross-check that the captured inputs faithfully reproduce what was written. |
| `arrow_ab.py` | Historical A/B harness: `executemany` vs `arrow` finalize backend on the fixed slice — wall, finalize time, rows, peak RSS, and `--verify` drift. The evidence for the ~270× finalize / ~30× wall Arrow result. |
| `arrow_fullrun.py` | Historical one-off: full ~100-min Arrow rebuild with `--verify` against the then-existing store — wall, replay/finalize split, peak RSS (~3.6 GB), DB size, per-table row counts. The run that first surfaced the RSS problem and the 45-row `_slope` finding. |

## Why they were created

During Arrow write-path validation, a tolerance-aware diff of the ~100-min Arrow rebuild against the
pre-existing analytics store flagged **45 rows** — all in `strike_window_metrics.book_pressure_slope`
— as exceeding the `--verify` gate (`atol = 1e-9`). The question was whether this was an Arrow defect,
a `_slope` regression, or a stale reference. Settling it required capturing the *exact* inputs for
those 45 rows and adjudicating the two `_slope` implementations against a higher-precision reference.

## How the `_slope` adjudication was performed

1. **`dump_targets.py`** identified the 45 over-`atol` `book_pressure_slope` rows and their stored
   `built`/`ref` values → `targets.json`.
2. **`capture_series.py`** replayed the full ~100-min raw log, wrapping `_window_rows`, and recorded
   the exact `book_pressure` series (and `eps`) that `_slope` consumed for each target key →
   `captured.json`.
3. The series were recomputed **three ways with the identical formula and `eps`**: numpy pairwise
   sums (the historical/reference impl), pure-Python sequential sums (the current impl), and exact
   `fractions.Fraction` arithmetic (ground truth). `sx`/`sxx` are exact integers in every path, so the
   only divergence is the summation order of `sy`/`sxy`.
4. A DB cross-check confirmed recomputed-pure == stored `built` and recomputed-numpy == stored `ref`
   (0 mismatches → captured inputs faithful).

**Verdict:** the pure-Python closed form was closer to exact in **41/45** rows (mean abs error
~4× smaller, max relative error ~10× smaller). The 45 "over-atol" rows were the **stale numpy
reference being less accurate**, not a defect — so `_slope` was kept and the canonical reference was
regenerated from current code. (The mis-scaled pure-absolute `atol` that surfaced the rows is tracked
separately as the deferred `atol + rtol` verify-semantics fix.)

The maintained `tools/validation/highprec_slope.py` reproduces step 3–4 against these frozen JSON
files:

```
python market_depth_recorder/tools/validation/highprec_slope.py \
    Documents/archive/validation-artifacts/captured.json \
    --targets Documents/archive/validation-artifacts/targets.json
```

## Reproducibility note

The two `.py` scripts here are **as originally written** — they contain hard-coded paths and
assumptions specific to this investigation (they expect the 2026-07-07 dataset and the scratch layout
of the time). They are retained as evidence of method, not as runnable utilities. To re-run an
equivalent analysis on new data, use the generalized tools under `market_depth_recorder/tools/`.
