# Offline Replay Optimization — Engineering Journal

*Historical narrative of the market-depth-recorder offline analytics-replay optimization,
distilled from the implementation session (2026-07-12 → 2026-07-13). This is a **journal** — the
reasoning, dead-ends, and decision forks behind the work — not the reference. For the canonical
account with full benchmark tables and current-state description, read **`Documents/PERFORMANCE.md`**;
for the historical task plan, read **`Documents/archive/offline-replay-optimization-implementation-plan-COMPLETE.md`**.
Milestone commit: **`1641f22`**.*

---

## Background

Offline analytics generation — replaying the lossless Tier-0 raw log through the *full* metric
catalog to rebuild the Tier-2 DuckDB store — took **~3 h 52 m** for the representative capture
(671,481 packets → 5,951,233 rows; `data/reprocess.log`). That extrapolated to roughly a full day of
compute per trading session: unusable for the Stage-1 offline-research loop.

Two facts made aggressive optimization safe:
- The heavy full-catalog + rolling-window path is **offline-replay-only**; live capture uses only the
  thin `live_metrics` subset (p50 ≈ 1.12 ms). So optimizing it carried **zero live-latency risk**.
- A **determinism gate already existed** (`--verify` rebuild-and-diff against a reference DuckDB), so
  every change could be proven output-preserving.

Constraint that shaped the endgame: the normal execution environment is an **8 GB office PC**, so peak
RSS — not just wall time — was a first-class success criterion.

---

## Investigation timeline

1. **Phase 0 — baseline + harness.** Built `benchmark.py` (wall/CPU/RSS/pkt-s/rows-s, child-aggregating,
   psutil-optional) and a fixed 2.5-min slice (14:00:00–14:02:30 → 15,692 packets / 73,952 rows).
   Baseline: wall 204.3 s, CPU 148.3 s (72.6 % of one core), peak RSS 198.5 MB; `--verify` clean.
   **cProfile ranked metric compute as the cost** (rolling windows ~40 %, `round_number_depth` ~20 %,
   small-array NumPy reduces, `BookSnapshot` ~4.5 %). The plan's optimization order was built on that.

2. **Phase 1b — pure-Python hotspot conversions (one per commit).** Converted the hottest metric bodies
   from NumPy to plain Python on tiny arrays, each gated by an isolated microbenchmark + `--verify`:
   - H1 `_round_depth` (M18): `np.isclose`/`remainder` → modulo — **5×–34×** (n=5 → 33.7×, n=50 → 5.0×).
   - H2 rolling reduces: `_slope` (closed-form integer `sx`/`sxx` + sequential y-sums), `_spread_stats`,
     `_wobi_stats` (shared `_mean_std_minmax`) — **5×–22×**, max abs diff vs NumPy at machine epsilon.
   - H3 `_side_wall_score` + per-strike reduces — 3×–16×; `_confidence` std 22×–25×.
   - H4 `processor._wall` pure-Python — 1.8×–8.9×, bit-identical.
   - H5 `_parse_side` — lowest priority, marginal.
   Cumulative cProfile compute: **28.33 s → ~14.6 s (≈ −46 %, ~1.9×)**; slice wall ~204 → ~178 s.

3. **⚠ The turning point (2026-07-13).** Taking phase-boundary numbers, an **un-profiled phase
   breakdown** of the slice exposed that cProfile had lied (see Major findings). The write path, not
   compute, was ~98 % of the run. The roadmap pivoted to the DuckDB write.

4. **Arrow write backend.** Replaced row-by-row `executemany` with a columnar `pa.table` + `INSERT …
   SELECT`. Slice A/B (exact row parity, both `--verify`-clean): finalize **206.9 s → 0.77 s (≈ 270×)**,
   total wall **211.4 s → 6.96 s (≈ 30×)**, +66 MB RSS. Shipped behind `analytics_db.write_backend`
   (`executemany` default), pyarrow pinned + fast-fail, A/B parity test. ~100-min rebuild: 416 s (≈ 33×),
   but peak RSS **3.6 GB**.

5. **The `_slope` / reference detour.** A tolerance-aware diff of the ~100-min Arrow rebuild vs the old
   store flagged 45 rows — resolved into a numerical-accuracy question, not an Arrow defect (see below).
   Reference regenerated; old store archived.

6. **Phase P-C — chunked-Arrow streaming writer.** Root-caused RSS to the long-lived per-table buffers
   (5.95 M tuples), not the pivot; fixed by flushing fixed-size batches **during `write()`**. Peak RSS
   **3190 → 800 MB (4×)**, wall **300.8 → 244.8 s** (finalize collapsed 86 → 1.2 s as the write overlaps
   replay), determinism bit-exact, 267 tests pass.

7. **Default flip + report.** Both gating conditions met → `write_backend` default flipped to `arrow`,
   `executemany` deprecated (one release cycle), `PERFORMANCE.md` written. Milestone commit `1641f22`.

---

## Major findings

- **cProfile mis-diagnosed the bottleneck.** cProfile times Python-level calls on the calling thread and
  inflates a hot Python loop by its per-call overhead, so the many small metric-body calls *looked*
  dominant while the single GIL-released C-level `executemany` was under-weighted. The un-profiled phase
  breakdown of a 201 s slice: gzip+json+ingest ~0.3 s (~0 %), **all metric compute 4.3 s (~2 %)**,
  **`finalize()` executemany INSERT + CHECKPOINT 196.8 s (~98 %)**. Root cause: row-by-row
  `con.executemany("INSERT … VALUES (?,…)", rows)` is a pathological anti-pattern for DuckDB's columnar
  engine; it scales linearly and reproduces the original 3 h 52 m (`196.8 s × 5.95 M / 74 k ≈ 4.4 h`).
  The winning optimization was **not even on the original priority list**.

- **The 45-row `book_pressure_slope` discrepancy was a stale reference, not a bug.** The old 652 MB store
  was built by the pre-Phase-1b NumPy `_slope`; the rebuild used the Phase-1b pure-Python closed form.
  They agree to ~1e-12 *relative*, but `_values_equal` uses a **pure absolute** `atol = 1e-9` that
  mis-scales — on slopes of magnitude ~1e6, `1e6 · 1e-12 ≈ 1.4e-9` trips it. Exact `fractions.Fraction`
  adjudication of all 45 rows proved the **pure-Python `_slope` more accurate** (closer to exact in
  41/45; mean abs error ~4× better, max rel error ~10× better) — sequential accumulation rounds tighter
  than NumPy's pairwise reduction at these short window lengths. So the reference was obsolete, not the
  code.

- **The Arrow pivot was never the main memory cost.** The `self._buffers` accumulation of the whole
  session (5.95 M tuples) dominated RSS; the finalize pivot only added a transient spike on top. This is
  why chunking *only* `finalize()` would have been insufficient — the fix had to flush during `write()`.

- **The built-in `--verify` is not memory-safe at scale.** `verify()` → `_read_table` materializes both
  full tables into nested Python dicts (4.44 M × 2 × ~30 cols) → `MemoryError`; it cannot run on the
  ~100-min dataset, let alone full-day on 8 GB. All determinism gates in this effort used a memory-safe
  DuckDB-side `EXCEPT`/PK-join instead. (Fix deferred as framework work.)

- **`_wall` is faster in NumPy — a recorded negative result.** Converting `processor._wall`'s
  `argmax`/`concatenate` to pure Python was ~2.5× *slower* on 50-level NIFTY books, so it was
  deliberately **kept as NumPy**. Not every hotspot wants converting.

- **The `config_hash` mismatch was a red herring.** The ~100-min `--verify` initially aborted on a
  provenance hash mismatch — traced to a capture-only NIFTY DSM-window config change (commit `212fb90`),
  **not** `write_backend` (that section isn't hashed) and not data drift.

- **The "652 MB store" is ~100 min, not a full day.** User correction: it is ~1/6 of a session, a *large
  representative* dataset — so all "full-day" claims remain **projected, not measured**, until a true
  full-session capture exists.

---

## Key design decisions

- **Arrow behind a config switch, not a hard replacement.** `analytics_db.write_backend`
  (`arrow` | `executemany`) kept the legacy path available for A/B and rollback; `executemany` stayed the
  default until memory was bounded, then flipped to `arrow` with `executemany` **deprecated for one
  release cycle** (not deleted).

- **Per-run `--backend {executemany,arrow}` CLI override.** Let the canonical reference be rebuilt via
  Arrow *without* touching the committed default — honoring the "flip only after verification" ordering.

- **Reference regenerated by a fresh canonical replay (not promoted from a benchmark artifact).** Cleaner
  provenance. Old store **archived** to `data/2026-07-07/legacy_pre_p1b/` with a README (obsolete, *not*
  "incorrect"). `_slope` **kept** (faster *and* more accurate).

- **`_values_equal` tolerance change kept separate.** The absolute→`atol + rtol·|b|` fix is a genuine
  latent mis-scaling, but was explicitly **not bundled** with the Arrow work — a like-for-like rebuild is
  already bit-exact. It is a standalone framework proposal.

- **Chunked batching localized to one seam.** The boundary is `write(row) → buffer → _flush(table) →
  backend insert`; **all** batching policy lives in `_flush(table)`. Replay engine and metrics stay
  completely unaware of batching — the seam a future streaming/parallel writer reuses.

- **Neutral config name `write_batch_rows`** (not `arrow_batch_rows`) — batching is a property of the
  writer, not of Arrow, and applies to both backends. Default **100_000**, validated `[1, 5_000_000]`,
  fast-fail (floor relaxed from 1_000 → 1 so tiny batches are testable at the replay level).

- **Hardened `close()`.** A mid-`finalize()` failure now discards the partial `.building_<pid>` temp in
  the `finally` — fixing a pre-existing latent bug that had orphaned a 245 MB `.building_16516` on disk.

- **Phase 1c / 1a / 1d deferred; Phase 2 deferred (not "dropped").** Compute-slice optimizations aren't
  worth it once the write is fixed; multi-process replay is "unlikely required for today's workloads but
  the design remains available" — softened wording chosen deliberately to avoid prematurely retiring the
  architecture.

---

## Validation methodology

The measurement discipline evolved under evidence and became the backbone of the effort:

- **Per-hotspot microbenchmark = primary gain signal.** The first hotspot exposed that full-slice wall
  has ~±10 % run-to-run variance (~±20 s on a 200 s slice), which **swamps** a single function's ~2–5 s
  contribution. So an isolated old-vs-new microbenchmark (at representative array sizes — 50-level NIFTY
  and 5-level SENSEX) became the primary signal.
- **`--verify` zero-drift = correctness gate** on every change.
- **Full-slice replay = regression check + cumulative gain** at each phase boundary only, never per
  hotspot.
- **Periodic cProfile re-profile keeps the microbench honest; the profiler is the tie-breaker.** After
  optimizing a hotspot, re-profile to confirm it actually moved down the ranking; if profiler and
  microbench disagree, trust the profiler and fix the microbench's input distribution.
- **Numerical changes adjudicated against a higher-precision reference.** The `_slope` question was
  settled with exact `fractions.Fraction` ground truth on the captured real input series (cross-checked:
  recomputed pure == stored built, recomputed numpy == stored ref → captured inputs faithful), not by
  argument.
- **Determinism at scale via memory-safe DuckDB-side diff.** ATTACH both DBs + symmetric `EXCEPT`
  (bit-exact, NULL-correct set semantics) or a PK-join with tolerance predicates mirroring
  `_values_equal` — because the built-in `--verify` OOMs. This caught (and correctly *dismissed*) the
  45-row `_slope` noise and confirmed chunked-Arrow bit-exact.
- **RSS measured in a separate process per run** (Python doesn't return memory to the OS between runs),
  sweeping batch sizes 50k/100k/250k (+ a 5M unchunked control).

---

## Performance milestones

*(Representative ~100-min dataset: 671,481 packets → 5,951,233 rows. Full tables in `PERFORMANCE.md`
§7–§9; a true full-session replay is not yet measured — figures below are on this dataset.)*

| Milestone | Wall | Peak RSS | Note |
|---|---|---|---|
| Original `executemany` | ~3 h 52 m | (small) | row-by-row INSERT = ~98 % of the run |
| Phase 1b (compute) | ~178 s (slice-scaled) | — | correct + verified, but ~2 % slice → <1 % offline impact |
| Arrow, unchunked | 300.8 s (~46×) | 3190 MB | finalize ~270× on slice A/B; RSS too high for 8 GB full-day |
| **Chunked-Arrow 100k (shipped)** | **244.8 s (~57×)** | **800 MB (4×)** | finalize 86 → 1.2 s; determinism bit-exact; 62 batches |

100k was empirically optimal (lowest RSS *and* fastest wall of 50k/100k/250k). Writer memory is now
bounded by the batch size rather than growing with replay duration (DuckDB's own working set can still
vary).

---

## Lessons learned

- **Measure before optimizing.** A profiler has a model; validate it against wall-clock reality. cProfile
  ranked the true ~98 % bottleneck near zero.
- **Re-profile after every major optimization.** The bottleneck moves — once the write collapsed to ~1 s,
  the ~6 s compute loop became the new floor and remaining priorities changed (Phase 2 became unnecessary).
- **Validate numerical changes against a higher-precision reference.** Exact `Fraction` arithmetic settled
  the `_slope` accuracy question definitively and reversed the initial assumption (current code was the
  *more* accurate one).
- **Separate correctness work from performance work.** Arrow (perf) was proven bit-exact independently;
  the `_slope` accuracy and `_values_equal` tolerance questions were adjudicated on their own merits and
  not bundled in.
- **Let measured evidence drive decisions.** Every default (Arrow, 100k batch, keeping pure-Python
  `_slope`, deferring Phase 2) is backed by a number. When measurement contradicted the plan, the plan was
  updated *before* continuing.
- **Negative results are results.** Keeping `_wall` on NumPy after a measured 2.5× regression was as
  valuable as any conversion.

---

## Deferred work (framework evolution — not blockers)

- **DuckDB-side `verify()` rewrite** — replace the O(rows) Python-dict materialization (which OOMs) with
  an ATTACH + SQL diff, as already used for the determinism gates here.
- **`atol + rtol` verification semantics** — `_values_equal`'s pure-absolute tolerance mis-scales for
  unbounded quantities; adopt `|a-b| ≤ atol + rtol·|b|`. Folds naturally into the `verify()` rewrite.
- **Phase 2 — multi-process time-chunked replay** — deferred pending future workloads; design remains in
  the archived plan. Unlikely required at current data volumes.
- **Future incremental / real-time rolling engine** — O(1)/tick running sums reusing the validated metric
  bodies; Phase 1c's reducer seam is the intended entry point.
- **A true full-session capture + replay** — to convert the projected full-day claims into measured ones.

See `PERFORMANCE.md §11` for the current statement of these items.
