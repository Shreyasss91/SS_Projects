<!--
================================================================================
ARCHIVED — HISTORICAL IMPLEMENTATION PLAN (not an active working plan)
================================================================================
Objective ......... Market Depth Recorder — offline analytics-replay performance
                    optimization (Tier-0 raw .jsonl.gz → Tier-2 DuckDB rebuild).
Status ............ IMPLEMENTATION COMPLETE — offline replay optimization done.
Milestone commit .. 1641f22  "perf(mdr): Arrow default write backend + chunked
                    streaming — ~57× replay on representative ~100-min dataset"
Archived .......... 2026-07-13 (moved out of ~/.claude/plans/, working filename
                    was performance-investigation-and-lazy-harbor.md).

Permanent engineering record .. Documents/PERFORMANCE.md  (the living, canonical
                    account: benchmark tables, per-optimization contribution,
                    lessons learned, deferred work).
Concise engineering journal ... Documents/archive/offline-replay-optimization-engineering-journal.md
                    (narrative history distilled from the implementation chat).

This document is the historical working plan that drove the effort
(Phase 0 baseline → Phase 1b pure-Python hotspots → the write-path pivot →
Arrow columnar backend → chunked-Arrow streaming writer → default flip). Every
phase relevant to the offline objective is complete and its checklist ticked.
Items still marked "deferred" here (DuckDB-side verify() rewrite, atol+rtol
tolerance, Phase 2 multi-process replay, future real-time incremental engine)
are intentionally out of scope — framework evolution, not open tasks.

Preserved for provenance and decision-history only. For the current state of the
system, read PERFORMANCE.md and the per-module docs — not this plan.
================================================================================
-->

# Market Depth Recorder — Analytics Replay Performance Optimization

## Context

Running `market_depth_recorder` over ~100 min of a session (~16% of a trading day) captured fine,
but **offline analytics generation took ~3h52m** (`data/reprocess.log`: full-day run 15:35→19:27,
`671,481 packets → 5,951,233 rows`). Extrapolated, a full session ≈ **~1 day** of analytics — far too
slow for the Stage-1 offline-research workflow.

Root cause (confirmed by reading the code + the run data): the offline **replay is a single synchronous
pass** (`replay.py:124`, `active_metrics="all"`) and the cost is entirely in **per-strike-per-second
Python/NumPy metric compute**, not the DuckDB write (that write is a single bulk `executemany` per table
at `finalize()` — `database_writer.py`). Throughput was ~48 packets/sec, ~425 rows/sec.

**Two structural enablers make this safe to fix aggressively:**
- **Live capture uses only the thin metric subset** (`live_metrics` in `config.yaml` — no rolling-window
  family; live cycle p50 ≈ 1.12 ms). The heavy full-catalog + rolling path is **offline-replay-only**, so
  optimizing it carries **zero live-latency risk**.
- A **determinism gate already exists**: `--verify` diffs a rebuild vs a reference DuckDB at `atol=1e-9`
  (`replay.py:59,278`). Every optimization is validated by rebuild-and-diff → **bit-identical (within
  tolerance) output is enforced**.

**Scope (user-confirmed):** offline speed only. Real-time / incremental-streaming engine = **future
phase** (see §Future Phase). We may introduce *seams/abstractions* that ease a later real-time swap, but
must not expand scope. Parallel replay must be **configurable** (single- or multi-process), default
`auto`. Chunking/merge must be **isolated from analytics logic** — metrics stay unaware of worker count,
and output must be identical regardless of worker count.

## ⚠ CRITICAL FINDING (2026-07-13) — the real bottleneck is the DuckDB WRITE, not metric compute

**Phase 0 mis-diagnosed the bottleneck because it trusted cProfile.** cProfile only times Python-level
calls on the calling thread and inflates a hot Python loop by its per-call overhead — so the metric bodies
*looked* dominant (`_compute_option` cumtime 26.8 s under cProfile) while the single GIL-released
`executemany` C-call was under-weighted. An **un-profiled phase-breakdown** of the fixed slice (201 s wall)
tells the true story:

| Phase | Time | Share |
|---|---|---|
| gzip read + `json.loads` + `ingest` | ~0.3 s | ~0 % |
| **`emit_second` — ALL metric compute (M1–M29 + rolling + agg)** | **4.3 s** | **~2 %** |
| **`DuckDBAnalyticalWriter.finalize()` — `executemany` INSERT + CHECKPOINT** | **196.8 s** | **~98 %** |

**Root cause:** `finalize()` (`database_writer.py:729`) does
`con.executemany("INSERT INTO t (...) VALUES (?, …)", rows)` — **row-by-row parameterized INSERT**, a
pathological anti-pattern for DuckDB (a vectorized columnar engine): ~74 k executes × ~100 param binds.
It scales linearly, which **explains the user's original 3h52m full-day run**: 196.8 s × (5.95 M rows /
74 k) ≈ 4.4 h. So the "~4-hour analytics" problem is ~98 % this one call.

**Measured fix (proven, row-count-parity exact):** replace `executemany` with a **columnar Arrow bulk
insert** — `pa.table({col: column_values})` then `INSERT INTO t SELECT * FROM arrow_tbl`:

| finalize approach | 73,952 rows | speedup |
|---|---|---|
| `executemany` (current) | 77.2 s in-mem / 196.8 s on-disk+CHECKPOINT | — |
| Arrow columnar bulk load | **1.06 s** | **72.6×** |

**Reprioritization (measured, overrides the compute-first order below for the OFFLINE goal):**
- **NEW P-W (DuckDB write path) is now the #1 lever — do it first.** ~72× on ~98 % of the run ⇒ full-day
  rebuild ~3h52m → single-digit minutes. Needs: `pyarrow` as a declared dep (already importable in the
  venv); careful type/NULL/`is_50_depth`-bool mapping through Arrow; a `--verify` zero-drift gate; FD-safe
  (Arrow tables are in-memory, connection already `with`-closed).
- **Phase 1b (done) stays** — it is correct, `--verify`-clean, low-risk, and it is the *right* work for the
  **future real-time path** (Part B: no giant batch write; per-tick compute latency is what matters). But
  for the **offline** goal its real-world contribution is ~1–2 s of ~200 s (<1 %).
- **Phase 1c / 1a / 1d → DEFER (likely drop for offline).** They optimize the 4.3 s (2 %) compute slice;
  not worth it for offline once the write is fixed. Keep 1c's reducer *seam* idea only as a Part-B item.
- **Phase 2 (multi-process) → DEFERRED, pending evaluation after chunked Arrow.** Based on current
  measurements (write ~1 s, compute ~4 s → a single-process replay finishes a full day in minutes) it is
  **unlikely to be required for today's workloads**, but the design **remains available** if future datasets
  or workflows justify additional parallelism. Reassess after chunked Arrow lands.

**Status: VALIDATED + IMPLEMENTED behind a config switch (2026-07-13).** A/B on the fixed slice (full
metric set, both `--verify` clean, exact 73,952-row parity): `executemany` wall 211.4 s / finalize 206.9 s /
peak RSS 192.5 MB vs **`arrow` wall 6.96 s / finalize 0.77 s / peak RSS 258.1 MB → finalize 269.8×, total
wall 30.4×** (the ~6 s loop is now the floor). Shipped as `analytics_db.write_backend` (`executemany`|`arrow`),
default `executemany`, pyarrow pinned + fast-fail, arrow-vs-executemany parity test added (suite 257 pass).
**Next:** full-day `arrow` rebuild + `--verify` vs a full-day reference (+ peak-RSS check) → then flip the
config default to `arrow` → later remove the legacy path. The compute-path order table below is retained for
the **future real-time** work but is superseded by P-W for the offline objective; **Phase 1c/1a/1d deferred;
Phase 2 deferred pending evaluation after chunked Arrow (unlikely required for today's workloads on current
measurements, but the design remains available if future datasets/workflows justify parallelism).**

### ⚠ FINDING (2026-07-13) — ~100-min arrow rebuild is faithful, but the `--verify` gate is mis-scaled

**Arrow performance/faithfulness: PASS.** ~100-min (671,481 pkts → 5,951,233 rows) arrow rebuild: **wall
416.1 s (6.9 min) vs original ~3h52m ≈ 33×**; replay 352.9 s / finalize 63.2 s; peak RSS **3618.5 MB**;
DB **606.8 MB** vs 651.8 MB ref; **exact per-table row parity** (spot 11,433 · option 1,480,195 · window
4,440,585 · agg 19,020). Arrow itself is **bit-exact** vs `executemany` (slice A/B: 0 divergent of 73,952).

**But a tolerance-aware DuckDB-side diff of the full run vs the 652 MB store surfaced 45 over-atol rows**
(of 4,440,585), **all in `strike_window_metrics.book_pressure_slope`**, max **abs 1.419e-9** / **rel
1.01e-12**, on values of magnitude **1.14e3–1.15e6**. Every other column of every table is ≤1e-12 or 0.

**Root cause — NOT arrow.** The 652 MB store was built by the **pre-Phase-1b numpy** `_slope`; this run
uses the **Phase-1b pure-Python closed-form** `_slope`. On large-magnitude book_pressure the two agree to
~1e-12 **relative**, but `replay._values_equal` uses a **pure ABSOLUTE** `_VERIFY_ATOL=1e-9` that does not
scale with magnitude, so |value|·rel ≈ 1e6·1e-12 ≈ 1.4e-9 trips the gate. `wobi_slope` (same `_slope`) is
clean only because its magnitudes are small. The fixed slice (14:00–14:02) never exercised book_pressure
large enough to expose this, so Phase-1b passed slice `--verify`.

**High-precision adjudication (2026-07-13) — `_slope` VALIDATED; pure-Python is the MORE accurate one.**
Captured the exact `book_pressure` input series for all 45 rows via a wrapped-`_window_rows` replay
(45/45, `eps=1e-8`), then recomputed each slope 4 ways with the identical formula/eps: numpy pairwise,
pure-Python sequential, and **exact `fractions.Fraction`** ground truth. DB cross-check: pure==stored
`built`, numpy==stored `ref` (0 mismatches → captured inputs faithful). Result vs the exact reference:

| | numpy (orig/ref) | pure-Python (current) |
|---|---|---|
| closer-to-exact wins | 4 / 45 | **41 / 45** |
| mean abs error | 1.066e-9 | **2.514e-10** (~4× better) |
| max **relative** error | 9.24e-13 | **8.90e-14** (~10× better) |

Both agree to ~1e-12 **relative**; the pure-Python closed form is decisively **as-or-more accurate**. So
the 45 "over-atol" rows are the **stale numpy reference being *less* accurate**, not a current-code defect.

**Resolution (per user's decision tree — `_slope` validated ⇒ proceed):**
1. **Regenerate the golden reference from current code** (the 652 MB store predates all of Phase-1b and is
   the less-accurate artifact). arrow==executemany is bit-exact (slice A/B), so build it via arrow.
2. **`_values_equal` abs→(atol+rtol) is a SEPARATE framework decision** — the pure-absolute `_VERIFY_ATOL`
   mis-scales for unbounded quantities (a ~1e-12 relative diff on a ~1e6 slope trips a 1e-9 abs gate). Worth
   adopting numpy-`isclose` semantics `abs(a-b) <= atol + rtol*|b|`, but decided on its own merits, not
   driven by this arrow work. (Not required once the reference is regenerated from current code — a
   like-for-like rebuild is bit-exact.)
3. **`_slope` NOT reverted** — pure-Python stays (it is both faster *and* more accurate here).

Arrow remains fully validated (bit-exact vs executemany; the sole reference delta was the numpy `_slope`).
The config-default flip to `arrow` is now unblocked *after* the reference is regenerated from current code.

**DONE (2026-07-13).** Old 652 MB store archived → `data/2026-07-07/legacy_pre_p1b/` (+README). Added a
per-run **`--backend {executemany,arrow}`** CLI override (writer `write_backend` seam threaded through
`replay_file`/`catchup`) so the canonical rebuild uses Arrow without editing the committed default.
Regenerated the canonical reference via the canonical path (`--replay … --backend arrow`, ~6m14s): 607.3 MB,
`config_hash 8a48bcdd`, exact row counts. Determinism re-verified **bit-exact (0 drift)** via a memory-safe
DuckDB-side `EXCEPT` (the built-in `--verify` OOM'd — see below). **Default kept at `executemany`** — Arrow
is correctness/perf-validated but the default flip is **gated on chunked-Arrow bounding peak RSS** first
(~3.6 GB on ~100-min won't scale to full-day on the 8 GB machine); Arrow selectable now via config/`--backend`.
Suite **259 passed**.

**⚠ NEW framework finding — `verify()` OOMs at scale (deferred, separate proposal).** `replay.verify` →
`_read_table` materializes **both** built + ref tables into nested Python dicts (4.44M × 2 × ~30 cols) →
`MemoryError` on the ~100-min dataset; unusable on the 8 GB target / full-day. Fix: reimplement the per-table
diff **DuckDB-side** (ATTACH + SQL), which also lets the tolerance become `atol + rtol*|b|` (fixes the
mis-scaled pure-absolute `_VERIFY_ATOL` behind the 45-row finding). Not bundled with the Arrow work per user.

**NEXT — chunked-Arrow finalize (peak-RSS).** Arrow buffers all rows then pivots → ~3.6 GB RSS on ~100-min
(~1/6 session) → ~20 GB projected full-day, over the 8 GB machine. Stream fixed-size Arrow batches into
DuckDB instead of buffering the whole dataset; keep throughput, bound peak RSS. Gate with the same
determinism diff. This is the last item before the offline pipeline is production-ready. See
[[mdr-8gb-ram-constraint]].

## Authoritative Optimization Order

Single-process optimizations first (each independently measured on the fixed slice + `--verify`-gated),
then layer multi-process replay on top. **This order is set by the Phase 0 profile (measured), not by the
original estimates** — the earlier guess of "memoization first" was overturned by the data (see Phase 0
Results below). This is the one order used everywhere in this document:

| Step | Change | Measured basis |
|---|---|---|
| **1b** | NumPy→pure-Python on tiny (≤64-elem) arrays — **implemented one hotspot per commit** (lead: `round_number_depth` isclose→modulo) | ~20% single body + pervasive small-array reduces (profile #2/#3) |
| **1c** | Precompute rolling series once; reduce per-window by slice; kill per-metric dict/getattr churn | rolling windows ~40% (profile #1) |
| **1a** | Forward-fill memoization — **reassess after 1b/1c; likely defer** | BookSnapshot only ~4.5% (profile #4) + M22/M24 correctness risk |
| **1d** | Cache per-second constants (`sorted(_known)`, `_strike_step`) | trivial cleanup, last |
| **2** | Multi-process time-chunked replay (`auto` workers) | ~Ncore× on top; **reassess if Phase 1 already fast enough** |

Per-step gains are recorded by measurement (the Phase 0 harness), never estimated up front.

---

## Phase 0 RESULTS (measured) — reprioritizes Phase 1

**Harness:** `market_depth_recorder/benchmark.py` (dev tool, not in the runtime path) — records
wall/CPU/RAM/packets-per-sec/rows-per-sec, aggregates child processes for Phase 2, degrades gracefully
without psutil.

**Fixed slice:** a standalone trimmed raw file `…/scratchpad/slice/market_depth_raw_20260707.jsonl.gz`
covering 14:00:00–14:02:30 IST (normal steady activity) — **15,692 packets → 73,952 rows, 149 grid
seconds**. Chosen so a run finishes in a few minutes and is directly comparable across phases (row count
is fixed by seconds×strikes; optimizations shrink wall, not rows).

**Baseline (pristine code, uncontended):** wall **204.3 s**, CPU 148.3 s (**72.6 %** of one core → ~27 % of
wall is gzip/DuckDB I/O, not compute), peak RSS **198.5 MB**, **76.8 packets/s, 361.9 rows/s**.
**Determinism gate:** a re-replay `--verify` vs the reference reports **`VERIFY OK: no drift`**.

**cProfile hotspot ranking (guides priority):**
1. `_window_rows` rolling windows ≈ **40 %** of compute (cum 10.2 s within `_compute_option`'s 25.5 s) —
   per-body series re-extraction (`_valued`/`getattr`, 7.4 M getattr calls) + numpy std/mean/slope on
   ≤61-element windows.
2. `round_number_depth` (M18) via **`np.isclose`** ≈ **20 %** (cum 5.2 s) — one per-strike body,
   replaceable with cheap modulo math.
3. Pervasive numpy small-array reduces (sum/mean/std/var/median/argmax/delete) across per-strike + rolling.
4. `BookSnapshot`/`_parse_side` ≈ **only 1.15 s (~4.5 %)**.

**Reprioritization (measured impact first) — this is the authoritative Phase-1 order; full detail in
Phase 1 below:**
- **P1-b NumPy→pure-Python (FIRST, biggest lever):** lead with `_round_depth` (isclose→modulo), then
  small-array reduces in per-strike (`_side_wall_score` median/delete, sums/means) and rolling
  (`_slope`, `_spread_stats`, `_wobi_stats`, `_micro_price_rv`). Profile-confirm each; keep numerical
  equivalence within `--verify` `atol=1e-9`.
- **P1-c precompute rolling series once:** extract each `WindowSample` attribute series a single time per
  strike-second and reduce the 5/10/30 s windows from slices — kills the `_valued`/getattr churn and the
  triple re-scan.
- **P1-a forward-fill memoization → REASSESS/likely DEFER:** BookSnapshot is only ~4.5 %, and the
  per-strike bodies it could skip must still recompute history-dependent M22/M24 — smaller benefit + the
  most correctness risk. Decide after 1b/1c land, based on whether per-strike bodies still dominate.
- **P1-d constant caching:** `sorted(self._known)`, `_strike_step` memoize — trivial cleanup, last.

---

## Phase 0 — Reference + benchmark harness (prep) — DONE (see results above)

- **Harness** `market_depth_recorder/benchmark.py` records wall/CPU/RAM/packets-per-sec/rows-per-sec via
  psutil (child-aggregating for Phase 2), degrades gracefully without it, and is not on the runtime path.
- **Reference + baseline established on the fixed slice** (not a per-phase full-day rebuild — the full-day
  run is the milestone gate). Slice reference: `…/scratchpad/bench/slice_reference.duckdb`; baseline +
  per-phase samples appended to `…/scratchpad/bench/results.jsonl`.
- **Determinism confirmed:** a re-replay of the slice `--verify`s `no drift` before any change.
- A stale orphan `market_depth_raw_20260707.replay.duckdb.building_16516` (245 MB) still sits under
  `data/2026-07-07/` — confirm with user before deleting (not touched).

## Phase 1 — Single-process optimizations (shared `TickProcessor`; benchmark + verify each)

Order = the Authoritative Optimization Order above: **1b → 1c → reassess 1a → 1d.** Each step: implement →
benchmark on the fixed slice → zero-drift `--verify` against the slice reference → summarize deltas →
commit. **Stop-and-discuss if a step under-delivers.** One authoritative full-day rebuild + benchmark +
verify at the Phase-1 milestone.

**1b. NumPy→pure-Python on tiny arrays (FIRST — highest measured impact).** Profile-confirm each body, then
convert *only* where it measurably helps while `--verify` stays within `atol=1e-9` (keep formula and
summation order identical). If any body drifts >1e-9, keep NumPy for that one.

**1b is NOT one implementation unit — it is a sequence of independent, individually-measured hotspot
conversions.** Do **one hotspot per iteration**, in this order (measured-impact first), and treat each as
its own micro-phase with its own commit:

1. `metrics/per_strike.py:_round_depth` (M18) — `np.isclose`/`np.remainder` → plain modulo test (profile
   #2, ~20%, cum 5.2 s). **Biggest single lever — do first.**
2. `metrics/rolling.py` window reduces — `_slope` (closed-form running sums), `_spread_stats`
   (min/max/mean/Welford std), `_wobi_stats`, `_micro_price_rv` — pure-Python over the ≤61-sample window.
   *(May be taken as one or split further if any single one under/over-delivers.)*
3. `metrics/per_strike.py:_side_wall_score` (`np.median`/`np.delete`) → Python; plus other per-strike
   small-array reduces (`.sum()`/`.mean()`) on a handful of levels.
4. `processor.py:_wall` (`np.concatenate`/`argmax`/`mean`/`std`) → single Python pass.
5. `metrics/snapshot.py:_parse_side` — `np.argsort`+fancy-index → Python `sorted()` on the small level list
   (profiled at only ~1.15 s → **lowest priority; convert only if measurably positive**).

**Per-hotspot loop (mandatory for each of the above):** select the one hotspot → implement only that
change → **microbenchmark old-vs-new in isolation** (see Measurement note below) → `--verify` zero-drift
against the slice reference → full-slice benchmark to confirm **no regression** → report the delta for
*that change alone* → commit + document it (its own commit; no bundling) → **re-profile if the ranking may
have shifted** before picking the next hotspot. A hotspot that shows no meaningful gain (or would drift) is
reverted/kept-as-NumPy and recorded as such — never bundled into another change's benchmark. Continue until
all worthwhile 1b hotspots are done, **then** move to 1c.

**Measurement note (measured 2026-07-12 — evidence overrode the original method).** The plan originally
treated the fixed-slice **wall-clock** as the per-hotspot arbiter. First micro-phase (`_round_depth`)
showed this is unworkable: full-slice wall has **~±10% run-to-run variance (~±20 s on a ~200 s slice)**,
which **swamps a single hotspot's true contribution (~2–5 s)**. So slice wall cannot resolve one function's
gain. **Revised method, per hotspot:** (1) an **isolated microbenchmark** (old vs new function on
representative array sizes — for NIFTY 50-level and SENSEX 5-level books) is the *primary* gain signal;
(2) `--verify` zero-drift is the correctness gate; (3) the full-slice benchmark is used only to confirm
**no regression** and to measure the **cumulative** gain of all 1b changes together (and at each phase
boundary). `_round_depth` result: **verify clean**; microbench **5×–34× faster** (n=5 →33.7×, n=20 →11.5×,
n=50 →5.0×); full-slice wall within noise (204 s → 227 s = run variance, not a regression).

**Profiler is the tie-breaker (source of truth on real workload).** The microbenchmark must stay
representative of the actual replay mix. After optimizing a hotspot, **periodically re-run cProfile on the
slice** and confirm that hotspot has actually moved **down** the ranking. If the profiler disagrees with
the microbenchmark (e.g. a body the microbench says is faster is *not* dropping in the profile — wrong
array-size assumption, unrepresentative inputs, or a shifted bottleneck), **trust the profiler**, fix the
microbench to match the real distribution, and reprioritize the remaining hotspots by the fresh profile.

**Confirmed methodology (user-approved 2026-07-12):** (1) microbenchmark = primary per-hotspot gain signal;
(2) `--verify` = correctness gate; (3) full-slice replay = regression check + **cumulative** gain at each
major-phase boundary (1b, 1c, …), not per-hotspot; (4) periodic full-replay re-profile keeps the microbench
honest — profiler wins any disagreement.

**1c. Precompute rolling series once; slice per window; drop dict/getattr churn (SECOND — attacks the ~40%
rolling cost).** In `_window_rows` (`processor.py:471`): extract each `WindowSample` attribute series
(`spread`, `wobi`, `ofi`, `dq_plus`, `book_pressure`, `micro_price`, `wall_price`…) **once** from the deque,
then reduce the 5/10/30 s windows from *slices* of the shared series instead of every body re-running
`_valued(_lastn(...))` (the 7.4 M-getattr churn, profile #1). Replace `dict.fromkeys(...)`+per-metric-merge
(`:475,:480`) with direct positional writes; same for the per-strike merge (`:372-374`) and aggregates
(`:500-504`). Output-identical.
  - *Future-proofing seam (no scope creep):* a thin internal "reducer" signature taking a pre-extracted
    series + window length, so a later incremental/streaming reducer can replace one metric without
    touching the engine.

**1a. Forward-fill memoization — REASSESS after 1b/1c; likely DEFER.** Rationale (from the profile):
`BookSnapshot` is only ~4.5% of compute, and the per-strike bodies a cache could skip must still recompute
the history-dependent M22 (`quote_stability`) / M24 (`confidence`). Decide with post-1b/1c numbers: if
per-strike bodies still dominate and the forward-fill rate is high, implement; otherwise defer to the
Future Phase and document. **If implemented:** in `_compute_option` (`processor.py:324`), cache the
packet-pure per-strike outputs + `BookSnapshot` keyed on packet identity + staleness edge, recompute
M22/M24 every second, and add explicit regression tests — unchanged packet (cache hit), changed packet,
stale→fresh, fresh→stale, first-seen strike, missing packet, session boundary — asserting cache-hit output
== recompute output via the injected clock/feed harness.

**1d. Cache per-second constants (LAST — trivial).** `sorted(self._known)` (`:276`) → cached sorted list
invalidated only on `_known` membership change; `_strike_step` (`:508`) → memoize per underlying
(session-constant). `MetricContext` reuse is already in place.

## Phase P-C — Chunked-Arrow streaming writer (peak-RSS bound) — APPROVED 2026-07-13, in progress

**Goal (primary = memory, not throughput).** Bound `DuckDBAnalyticalWriter` peak RSS so it is
**~independent of replay duration** (full-day-safe on the 8 GB machine), while keeping throughput close to
the current unchunked Arrow. Root cause (measured): the long-lived per-table buffers (`self._buffers`,
5.95M tuples for the whole session) dominate RSS; the Arrow pivot only adds a transient peak on top. Fix:
**stream fixed-size batches during `write()`** so no table's buffer exceeds one batch.

**Locked decisions (user, 2026-07-13):**
- Config key is neutral: **`analytics_db.write_batch_rows`** (batching is a writer property, not Arrow's).
  Default **100_000**; validate present + positive int in **[1, 5_000_000]**, else fast-fail exit 1 (floor
  relaxed from 1_000 → 1 during impl: any positive size is *correct*, and small sizes must be testable at the
  replay level; < a few thousand is merely inefficient, not invalid).
- **All batching policy lives in `_flush(table)`.** The write path boundary is
  **`write(row) → buffer → _flush(table) → backend insert`** — the single seam future streaming/parallel
  writers evolve. Replay engine, metrics, and higher-level replay flow stay **completely unaware** of batching.
- Backend-agnostic: `_flush` dispatches to the existing `_insert_arrow`/`_insert_executemany` per batch
  (also bounds the deprecated executemany path — bonus).
- **Primary success criterion = bounded peak RSS ~independent of duration.** Throughput must stay close to
  current Arrow but is now the secondary goal.
- Benchmark **50k / 100k / 250k** on the ~100-min dataset, reporting **peak RSS, wall, batches written**;
  revisit the default from measured data (e.g. if 250k gives ~same RSS with far fewer inserts).

**Implementation checklist:**
- [x] `config.yaml`: add `write_batch_rows: 100000` under `analytics_db` with a comment.
- [x] `config.py`: validate `write_batch_rows` present, int (bool rejected), `1 ≤ n ≤ 5_000_000`; fast-fail.
- [x] `tests/conftest.py`: add `write_batch_rows` to `base_config.analytics_db`.
- [x] `database_writer.py` `__init__`: `self._batch_rows`; `self.batches_written = 0`.
- [x] `database_writer.py` `_flush(table)`: **the only batching seam** — boolify option rows, dispatch to
      arrow/executemany insert, advance `rows_written`/`batches_written`, clear buffer.
- [x] `database_writer.py` `write()`: `if len(buf) >= self._batch_rows: self._flush(table)`.
- [x] `database_writer.py` `finalize()`: flush remaining partials via `_flush` → `recorder_meta` → `CHECKPOINT`.
- [x] `close()`: log `batches_written`; **hardened** to discard the temp on mid-`finalize()` failure (finally).
- [x] Tests (`test_database_writer.py`): chunked==single-shot; partial final batch; `batches_written` count.
- [x] **Failure-injection tests**: mid-batch, between batches, final partial, after `CHECKPOINT` before rename
      → canonical strictly all-or-nothing (all 4 pass).
- [x] `test_replay.py`: chunked-arrow == unchunked (verify-clean).
- [x] Benchmark script: {5M control, 250k, 100k, 50k} → peak RSS, wall, batches.
- [x] Determinism gate: DuckDB-side **bit-exact** diff chunked-100k vs the canonical reference → **0 drift**
      across all 4 tables (5,951,233 rows).
- [x] FD audit of the write path (FD-neutral; cleanup strictly better); full suite **267 pass**.
- [x] Docs: `ARCHITECTURE.md` + `Documents/database_writer.md` + CHANGELOG P-C entry all updated.

**P-C COMPLETE (2026-07-13).** All gates green. Peak RSS 3190→800 MB (4×), wall 300.8→244.8 s, 0 drift,
267 tests pass.

**Benchmark result (2026-07-13, ~100-min dataset, backend=arrow, separate process per run for clean RSS):**

| batch | wall | finalize | peak RSS | batches |
|---|---|---|---|---|
| 5_000_000 (unchunked control) | 300.8 s | 86.4 s | **3190 MB** | 4 |
| 250_000 | 247.1 s | 4.1 s | 1278 MB | 26 |
| **100_000 (default)** | **244.8 s** | 1.2 s | **800 MB** | 62 |
| 50_000 | 249.8 s | 0.6 s | 932 MB | 121 |

→ **100k is empirically optimal: lowest peak RSS (800 MB, 4× below unchunked) AND fastest wall** (finalize
collapses 86→1.2 s as the write overlaps replay). RSS floor is now DuckDB's own working set (`memory_limit`
PRAGMA), not the Python buffer → **writer memory bounded by the batch size, not replay duration**. **Default
kept at 100_000** (data-backed). Progress checklist ticked: config.yaml/config.py/conftest/writer/`_flush`/
tests (267 pass)/benchmark all done; `close()` hardened to discard the temp on mid-`finalize()` failure
(fixes the pre-existing `.building` orphan).

**MILESTONE COMPLETE — default flipped to `arrow` (2026-07-13).** All 5 review items delivered:
(1) throughput ~3h52m → 300.8 s (unchunked) → **244.8 s chunked = ~57×**; (2) peak RSS 3190→**800 MB (4×)**;
(3) determinism **bit-exact, 0 drift**; (4) **default flipped `executemany`→`arrow`** (both gating conditions
met: throughput preserved+improved, RSS bounded), `executemany` **DEPRECATED** (retained one release cycle as
`--backend`/config fallback); (5) **`Documents/PERFORMANCE.md`** written (full journey, per-optimization
measured contribution, `_slope`/reference story, lessons, deferred work). Wording precisioned across docs +
code ("bounded by batch size, not replay duration"). Suite **267 pass** with `arrow` default.

**OFFLINE REPLAY OPTIMIZATION COMPLETE.** Remaining is framework evolution only, not a blocker:
DuckDB-side `verify()` rewrite (fixes O(rows) OOM) + `atol+rtol` tolerance; Phase 2 (deferred, unlikely
needed); future incremental real-time rolling engine. See `Documents/PERFORMANCE.md` §11.

## Phase 2 — Multi-process time-chunked replay (configurable)

Add a **parallel driver** that is isolated from all metric/analytics code. Metrics/`TickProcessor` remain
completely unaware of parallelism.

- **Config (genericization contract, fast-fail):** add to `config.yaml` `reprocess:` →
  `replay_mode: single|multi` (default keeps current behavior configurable) and `replay_workers: auto|N`
  where `auto` = `max(1, cpu_count() - 1)`. Validate at startup (out-of-range → exit 1).
- **Chunking:** split the session `[t0, t_end]` into `N` contiguous time-chunks. Each worker replays the
  **same raw log** but:
  - starts *ingesting* at `chunk_start - W`, where **`W` is derived from config, never hard-coded**:
    `W = (2 * max(time_windows_sec) + 1) + staleness_timeout_sec + safety_margin`. It is computed from the
    live `config.yaml` values (`metrics.time_windows_sec`, `recorder.staleness_timeout_sec`) plus a small
    safety margin, so it auto-adapts if those settings change. So rolling deques / `StrikeHistory` /
    `_prev` (OFI) / `_known` are fully warm at `chunk_start`;
  - only `emit_second` for boundaries `>= chunk_start` and `< chunk_end` → rows outside the chunk's own
    range are discarded.
  Because each strike's rolling window depends only on its own last `2N+1` seconds and the pre-roll makes
  that history identical to the full-day build, chunk output is **bit-identical** (verify-clean).
  Aggregates are intact (a time-chunk contains all strikes for its seconds); spot resolves within-chunk.
- **Isolation + merge:** each worker writes its rows to a **temp partition** (per-table Parquet, or a temp
  DuckDB) under `.building_<pid>/`. A final **merge pass** unions partitions in timestamp order into the
  canonical DuckDB, writes `recorder_meta` once, `CHECKPOINT`, and atomically `os.replace`s — reusing the
  existing `DuckDBAnalyticalWriter` DDL/meta so the output schema is unchanged. Merge output is identical
  regardless of `N` (rows keyed by PK; union is order-independent for content).
- **Modes:** `replay_mode: single` runs today's exact synchronous path (debugging/profiling/deterministic
  baseline). `multi` runs the chunked pool. `catchup()`/`_cmd_replay` select via config; keep a CLI
  override flag (e.g. `--workers`) for ad-hoc runs.
- **Metrics stay replay-mode-unaware:** all chunking, worker/process management, and partition merging live
  **only in the replay driver**. `TickProcessor` and the metric bodies receive the same inputs and cannot
  tell whether they run in one process or many.
- **Robustness / determinism:** if **any** worker fails, the whole replay **fails cleanly** — surface the
  error, cancel/join remaining workers, and remove **all** temp partitions so no orphan `.building_*`
  directory/file is left behind (context-managed temp dir + `finally` cleanup; also sweep pre-existing
  stale `.building_*` on start). The canonical DuckDB is produced by the merge step only on full success
  (atomic `os.replace`), and its content is **identical regardless of worker count** (rows keyed by PK;
  union is order-independent) — enforced by the invariance verify below.
- **FD hygiene:** workers are a `ProcessPoolExecutor` (or `Popen`) reaped/joined on every path (success and
  failure); each worker `with`-closes its gzip reader + partition writer; the merge connection is
  `with`-closed. Runs inside the already-reaped end-of-session reprocess subprocess
  (`main._launch_reprocess`), stdout/stderr → log file, never PIPE. Run a focused FD audit after Phase 2.

Verify: `multi` build with `workers=auto` **and** with `workers=1` must both `--verify` clean against the
single-process `reference.duckdb` (proves output is worker-count-invariant).

---

## Stopping criterion (avoid over-optimizing)

Once the **high-impact** optimizations are done and replay is at an acceptable time, **stop** if further
changes offer only marginal improvement relative to their added complexity. Document any such
lower-value ideas as **deferred work** (in `CHANGELOG.md` / the plan) rather than implementing them. The
Phase-1 → Phase-2 reassessment above is the first application of this rule.

## Future Phase (deferred — not in this scope)

Incremental / streaming O(1)-per-tick rolling engine so Stage-2 real-time reuses the exact metric bodies
online. Phase 1c intentionally leaves a thin reducer seam (pre-extracted series + window) so individual
metrics can later be swapped to ring-buffer running-sum implementations **without another engine refactor**.
Real-time already computes only the thin validated subset via `live_metrics` + the registry toggle, so the
online path is not the bottleneck; the deferred work is about making validated rolling metrics incremental.

## Part B — Real-time suitability (assessment, documented not implemented)

- **Good:** replay and live already share one `TickProcessor` + metric registry (no dual implementation to
  drift), and the active metric set is config-toggleable (`live_metrics`) — so "compute only validated
  metrics in real time" is already the supported path.
- **Recommendation (future):** move rolling reductions from recompute-over-window to incremental running
  sums (ring buffers) — makes real-time rolling O(1)/tick and also speeds offline. Phase 1c's reducer seam
  is the entry point. Keep the columnar row-tuple contract (`OPTION_COLUMNS` etc.) as the stable interface
  between compute and any sink (SQLite live, DuckDB offline, or a future in-memory feature bus).

## Critical files

- `processor.py` — `_window_rows`/`_agg_rows` (1c), `_wall` (1b), `emit_second` loop constant caching (1d),
  `_compute_option` (1c reorder; 1a only if implemented).
- `metrics/per_strike.py` — `_round_depth`, `_side_wall_score`, small-array reduces (1b).
- `metrics/rolling.py` — `_slope`, `_spread_stats`, `_wobi_stats`, `_micro_price_rv` (1b); reducer seam (1c).
- `metrics/snapshot.py` — `_parse_side` argsort (1b).
- `replay.py` — timing log (P0); new parallel driver + chunking + merge (P2), kept separate from metric code.
- `config.py` / `config.yaml` — `reprocess.replay_mode` + `replay_workers` validation (P2).
- `database_writer.py` — reused as-is for DDL/meta/merge sink (P2).
- `__main__.py` (`_cmd_replay`) / `main.py` (`_launch_reprocess`) — mode/worker wiring (P2).
- Docs: `Documents/ARCHITECTURE.md`, `Documents/CHANGELOG.md`, per-module docs, and the in-repo
  **peppy-dolphin plan doc** (project convention — sync progress there as phases complete).

## Verification (end-to-end)

1. **Per-phase gate (fixed slice):** rebuild the fixed slice → `--verify` against the slice reference →
   must report `VERIFY OK: no drift` (zero-tolerance duckdb path). Any drift >1e-9 → **stop, investigate,
   fix before continuing** (never defer a correctness failure to the milestone). At the **Phase-1
   milestone**, one authoritative **full-day** rebuild + `--verify` against a full-day reference (built
   from the pristine baseline commit) before deciding on Phase 2.
2. **Benchmark (per phase):** record wall-clock, CPU utilization, peak RAM (RSS), packets/sec, and
   rows/sec for each slice rebuild via the harness, so every step's contribution is measured in isolation;
   full-day numbers at the milestone.
3. **Phase 2 invariance:** `multi/workers=auto` and `multi/workers=1` builds both `--verify` clean against
   the single-process reference (output independent of worker count).
4. **FD audit** after Phase 1 (touches DB/compute) and Phase 2 (subprocess/pool/gzip/DuckDB).
5. Confirm `single` mode still reproduces today's exact behavior for debugging/profiling.
