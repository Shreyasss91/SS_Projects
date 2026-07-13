# Performance — Offline Analytics Replay Optimization

*Permanent engineering record. Dataset throughout is the representative capture from 2026-07-07:*
***671,481 raw packets → 5,951,233 analytics rows*** *(spot 11,433 · option_strike 1,480,195 ·
strike_window 4,440,585 · aggregate 19,020). All wall/RSS figures are on the 8 GB office-PC target unless
noted. Cross-references are to the plan doc `performance-investigation-and-lazy-harbor.md` and the design
spec `market_depth_recorder_design.md`.*

---

## 1. Executive summary

The offline analytics rebuild (Tier 0 raw `.jsonl.gz` → Tier 2 DuckDB) originally took **~3 h 52 m** for
the representative dataset — extrapolating to roughly a full day of compute for a full trading session,
unusable for the Stage-1 offline-research workflow.

After the optimization, **the representative ~100-minute dataset rebuilds in 244.8 s (~4 min) vs the
original ~3 h 52 m — a ~57× speedup on that dataset** — with **peak RSS bounded to ~800 MB** (down 4× from
the intermediate Arrow implementation's ~3.2 GB). That is validated on the ~100-min dataset and makes the
writer suitable for the 8 GB target for current workloads; a true full-session replay has **not** yet been
measured on this hardware (projected, not verified). Output is **bit-exact** against the canonical
reference; the full test suite (267 tests) passes.

The decisive lesson: **the original profiling was wrong.** A cProfile run pointed at metric compute as the
bottleneck; an un-profiled phase-breakdown proved **~98 % of the time was a single row-by-row DuckDB
`INSERT`**. The winning optimization (columnar Arrow bulk load) was not even on the original priority list.

*(representative ~100-minute dataset; a true full-session replay is not yet measured on this hardware)*

| | Original | Final (shipped) | Improvement |
|---|---|---|---|
| Wall time | ~3 h 52 m (~13,920 s) | **244.8 s** | **~57×** (this dataset) |
| Peak RSS | (n/a — small under executemany) | **800 MB** | bounded; suitable for 8 GB target, current workloads |
| Write backend | `executemany` (row-by-row) | **`arrow`** (columnar, chunked) | new default |
| Determinism | reference | **bit-exact vs canonical** | preserved |

---

## 2. Original problem statement

`market_depth_recorder` captures option market depth live into a lossless Tier-0 raw log, then **offline**
replays that log through the *full* metric catalog (M1–M29 + rolling windows + aggregates) to build the
Tier-2 DuckDB analytics store. The replay is a single synchronous pass (`replay.py`, `active_metrics="all"`).

Measured reality (`data/reprocess.log`): rebuilding the representative dataset ran **15:35 → 19:27 =
~3 h 52 m**, ≈ 48 packets/s, ≈ 425 rows/s. That made the offline research loop impractical.

**Two structural facts made aggressive optimization safe:**
- **Live capture uses only the thin `live_metrics` subset** (no rolling-window family; live cycle p50 ≈
  1.12 ms). The heavy full-catalog + rolling path is **offline-replay-only** → optimizing it carries **zero
  live-latency risk**.
- **A determinism gate already existed**: a rebuild-and-diff (`--verify`) against a reference DuckDB. Every
  change is validated by comparing output to a known-good store, so "faster" never silently means "different".

---

## 3. Investigation timeline

| Date | Step | Outcome |
|---|---|---|
| — | **Phase 0** — build benchmark harness + fixed slice + reference | Baseline established (below) |
| — | **Phase 0 cProfile** ranks hotspots | *Mis-diagnosis:* metric compute (rolling windows, `round_number_depth`) looked dominant |
| — | **Phase 1b** — NumPy→pure-Python hotspot conversions (one per commit) | Correct + `--verify`-clean, but small real-world offline contribution |
| **2026-07-13** | **⚠ Turning point** — un-profiled phase-breakdown | **~98 % of wall is the `finalize()` `executemany` INSERT**, not compute |
| 2026-07-13 | **Arrow** columnar bulk-insert backend | finalize ~270× faster; ~33–46× end-to-end; behind a config switch |
| 2026-07-13 | **`_slope` investigation** (45 over-atol rows) | Pure-Python `_slope` proven *more* accurate; reference was stale → regenerated |
| 2026-07-13 | **Phase P-C** — chunked-Arrow streaming writer | Peak RSS 3190→800 MB (4×), wall 300.8→244.8 s, bit-exact |
| 2026-07-13 | **Default flip** → `arrow`; `executemany` deprecated | Offline optimization complete |

**Phase 0 baseline (fixed slice 14:00:00–14:02:30, 15,692 packets → 73,952 rows):** wall **204.3 s**, CPU
148.3 s (72.6 % of one core → ~27 % of wall is gzip/DuckDB I/O), peak RSS 198.5 MB, 76.8 pkt/s, 361.9 rows/s;
re-replay `--verify` → *no drift*. The slice was chosen small enough to iterate in minutes and directly
comparable across phases (row count is fixed by seconds × strikes; optimizations shrink wall, not rows).

---

## 4. The key turning point — measurement disproved the profile

Phase 0's cProfile ranked **metric compute** as the cost: `_window_rows` rolling windows ≈ 40 %,
`round_number_depth` (via `np.isclose`) ≈ 20 %, pervasive small-array NumPy reduces, `BookSnapshot` ≈ 4.5 %.
The plan's optimization order was built on that ranking (pure-Python hotspots first, then rolling-series
precompute, then optional multi-process).

**cProfile lied by construction.** It times Python-level calls on the calling thread and inflates a hot
Python loop by its per-call overhead — so the many small metric-body calls *looked* dominant, while the
single, GIL-released, C-level `executemany` call was under-weighted. An **un-profiled phase-breakdown** of
the same fixed slice (201 s wall) told the truth:

| Phase | Time | Share |
|---|---|---|
| gzip read + `json.loads` + ingest | ~0.3 s | ~0 % |
| `emit_second` — **all** metric compute (M1–M29 + rolling + agg) | 4.3 s | **~2 %** |
| `finalize()` — `executemany` INSERT + CHECKPOINT | **196.8 s** | **~98 %** |

**Root cause:** `finalize()` did `con.executemany("INSERT INTO t (...) VALUES (?, …)", rows)` — **row-by-row
parameterized INSERT**, a pathological anti-pattern for DuckDB (a vectorized *columnar* engine): ~74 k
executes × ~100 param binds on the slice. It scales linearly with rows, which **exactly explains the
original 3 h 52 m**: `196.8 s × (5.95 M / 74 k) ≈ 4.4 h`.

The entire ~4-hour problem was one wrong write call. The metric-compute optimizations the profile prioritized
addressed the 2 % slice.

---

## 5. Every optimization — what, why, measured contribution

### 5.1 Phase 1b — NumPy → pure-Python on tiny arrays *(kept; small offline impact)*

**What / why.** The metric bodies used NumPy reduces on ≤64-element (often ≤61-sample rolling) arrays,
where NumPy's fixed per-call overhead dominates its vectorization benefit. Converted the hottest bodies to
plain Python, **one hotspot per commit**, each gated by an isolated microbenchmark (primary signal — full
slice wall has ±10 % run-to-run noise that swamps a single body's ~2–5 s) and `--verify` zero-drift.

| Hotspot | Change | Microbench | Verify |
|---|---|---|---|
| `_round_depth` (M18) | `np.isclose`/`remainder` → modulo | 5×–34× (n=5→33.7×, n=50→5.0×) | clean |
| `metrics/rolling.py` reduces | `_slope`, `_spread_stats`, `_wobi_stats`, `_micro_price_rv` → pure-Python | faster on ≤61-sample windows | clean |
| `_side_wall_score` + per-strike reduces | `np.median`/`np.delete`/sums → Python | faster | clean |
| `processor._wall` | `np.concatenate`/`argmax`/`mean`/`std` → single Python pass | 1.8×–8.9× | bit-identical |
| `snapshot._parse_side` | (lowest priority) convert only if positive | — | — |

**Measured contribution to the offline goal: <1 %** of wall (it optimizes the 4.3 s / 2 % compute slice).
**Kept anyway** because it is correct, low-risk, and it is the *right* work for a future **real-time** path
(per-tick latency, no giant batch write). `_slope`'s pure-Python form later proved not just faster but
**numerically more accurate** (§6).

### 5.2 P-W — Arrow columnar write backend *(the decisive lever)* — §7

### 5.3 Phase P-C — chunked-Arrow streaming writer *(bounds peak RSS)* — §8

### 5.4 Deferred / dropped for the offline goal

- **Phase 1c** (precompute rolling series once) / **1a** (forward-fill memoization) / **1d** (per-second
  constant caching): all target the 2 % compute slice — **not worth it for offline** once the write was
  fixed. 1c's reducer *seam* idea is retained as a future real-time item.
- **Phase 2** (multi-process time-chunked replay): **deferred pending future workloads.** With write ~1 s
  and compute ~4 s on the slice, a single-process replay is projected to finish a full day in minutes — parallelism is
  **unlikely to be required for today's workloads**, but the design remains documented and available if
  future datasets or workflows justify it.

---

## 6. The `_slope` investigation — why the canonical reference changed

When the ~100-min Arrow rebuild was diffed (tolerance-aware) against the pre-existing 652 MB analytics store,
**45 rows** (of 4,440,585) exceeded the gate — **all** in `strike_window_metrics.book_pressure_slope`, max
**abs 1.419e-9 / rel 1.01e-12**, on values of magnitude **1.14e3–1.15e6**. Every other column of every table
was ≤ 1e-12 or 0.

**Root cause — not Arrow.** The 652 MB store was built by the **pre-Phase-1b NumPy** `_slope`; this rebuild
used the **Phase-1b pure-Python closed-form** `_slope`. They agree to ~1e-12 **relative**, but the verify
gate `_values_equal` uses a **pure absolute** `atol = 1e-9` that does not scale with magnitude — so
`|value| · rel ≈ 1e6 · 1e-12 ≈ 1.4e-9` trips it. (`wobi_slope` uses the same `_slope` but stays clean only
because its magnitudes are small.) The fixed slice never exercised `book_pressure` large enough to expose
this, so Phase 1b passed its slice `--verify`.

**High-precision adjudication.** Captured the exact `book_pressure` input series for all 45 rows via a
wrapped-`_window_rows` replay, then recomputed each slope three ways with the identical formula/`eps`:
NumPy pairwise, pure-Python sequential, and **exact `fractions.Fraction`** ground truth. DB cross-check
confirmed pure == stored `built` and numpy == stored `ref` (captured inputs faithful).

| | NumPy (old reference) | Pure-Python (current) |
|---|---|---|
| closer-to-exact wins | 4 / 45 | **41 / 45** |
| mean absolute error | 1.066e-9 | **2.514e-10** (~4× better) |
| max **relative** error | 9.24e-13 | **8.90e-14** (~10× better) |

**The pure-Python `_slope` is decisively as-or-more accurate.** The 45 "over-atol" rows were the *stale
NumPy reference being less accurate*, not a current-code defect.

**Resolution.**
1. **Regenerated the canonical reference from current code** — the 652 MB store predates all of Phase 1b and
   is the less-accurate artifact. Since Arrow == executemany is bit-exact, it was rebuilt via Arrow →
   **607.3 MB, `config_hash 8a48bcdd`**, exact row counts. The old store was **archived** (not deleted) to
   `data/2026-07-07/legacy_pre_p1b/` with a provenance README — it is obsolete, *not* "incorrect".
2. **`_slope` NOT reverted** — pure-Python stays (faster *and* more accurate).
3. **The `_values_equal` absolute→(atol + rtol) fix is a SEPARATE framework decision** (§10 deferred). It is
   a real mis-scaling for unbounded quantities, but a like-for-like rebuild from current code is already
   bit-exact, so it is not needed to unblock this work — it is decided on its own merits.

---

## 7. Arrow writer redesign

**Change.** Replace the per-table row-by-row `executemany` INSERT with a **columnar bulk load**: pivot the
buffered row tuples into a `pyarrow.Table` (one array per column, correct type/NULL mapping, `is_50_depth`
0/1 → native `BOOLEAN`), register it, and `INSERT INTO t SELECT * FROM arrow_tbl`. DuckDB ingests the whole
column vector at once instead of binding ~100 params per row.

**Measured (fixed slice A/B, 73,952 rows, both `--verify`-clean, exact row parity):**

| finalize backend | wall | finalize | peak RSS |
|---|---|---|---|
| `executemany` | 211.4 s | 206.9 s | 192.5 MB |
| **`arrow`** | **6.96 s** | **0.77 s** | 258.1 MB |

→ **finalize 269.8×, total wall 30.4×.** On the full ~100-min dataset an early Arrow rebuild measured
**416.1 s (≈ 33×)**; the later P-C benchmark's unchunked control measured **300.8 s (≈ 46×)** (run-to-run
variance + machine state). Arrow is **bit-exact** vs `executemany` (slice A/B: 0 divergent of 73,952).

**Shipped** as `analytics_db.write_backend` (`arrow` | `executemany`), pyarrow pinned + fast-fail if
missing, with a per-run `--backend` CLI override. **Cost:** Arrow buffered the *whole session* then pivoted
the largest table ~3× at once → **~3.2–3.6 GB peak RSS** on ~100-min data, projecting to ~20 GB full-day —
over the 8 GB target. That is what §8 fixes.

---

## 8. Chunked-Arrow redesign (Phase P-C)

**Root cause of the RSS (measured).** The long-lived per-table buffers (`self._buffers`, 5.95 M row tuples
for the whole session) dominate RSS; the Arrow pivot only adds a transient peak on top of them.

**Change.** Stream **fixed-size batches during `write()`** instead of buffering the whole session. The write
path becomes a single seam — **`write(row) → buffer → _flush(table) → backend insert`**: `write()` flushes a
table once its buffer reaches `analytics_db.write_batch_rows` (new config key, default **100_000**, validated
positive int ≤ 5_000_000, fast-fail). **All batching policy lives in `_flush(table)`** (boolify option rows,
dispatch to the arrow/executemany insert per batch, advance counters, clear buffer). The replay engine and
metrics are **completely unaware** of batching — the seam a future streaming/parallel writer reuses. Atomic
build (`.building_<pid>` temp → `os.replace`) is preserved, and `close()` was **hardened** so a
mid-`finalize()` failure discards the partial temp in the `finally` (previously it orphaned a `.building`).

**Benchmark (~100-min dataset, backend=arrow, one process per run for clean peak RSS):**

| batch | wall | finalize | peak RSS | batches |
|---|---|---|---|---|
| 5_000_000 (unchunked control) | 300.8 s | 86.4 s | **3190 MB** | 4 |
| 250_000 | 247.1 s | 4.1 s | 1278 MB | 26 |
| **100_000 (default)** | **244.8 s** | 1.2 s | **800 MB** | 62 |
| 50_000 | 249.8 s | 0.6 s | 932 MB | 121 |

→ **100k is empirically optimal: lowest peak RSS (800 MB, 4× below unchunked) *and* fastest wall** — finalize
collapses 86 → 1.2 s because the write now overlaps replay. The RSS floor is now DuckDB's own working set
(`memory_limit` PRAGMA), not the Python buffer, so **writer memory is bounded by the configured batch size
rather than growing with replay duration** (DuckDB's own working set can still vary). **Failure-injection
tests** (mid-batch, between batches, final partial, after `CHECKPOINT` before rename) confirm the canonical
store is strictly all-or-nothing. **267 tests pass**; FD audit FD-neutral, cleanup strictly improved.

---

## 9. Final benchmark tables

**Throughput** (same 671,481-packet / 5,951,233-row dataset throughout):

| Implementation | Wall | vs original |
|---|---|---|
| Original — `executemany`, buffer-all | ~3 h 52 m (~13,920 s) | 1× |
| Arrow, unchunked (P-C control) | 300.8 s | ~46× |
| **Arrow, chunked 100k (shipped default)** | **244.8 s** | **~57×** |

**Peak RSS:**

| Implementation | Peak RSS |
|---|---|
| Arrow, unchunked | 3190 MB |
| **Arrow, chunked 100k (shipped default)** | **800 MB (4× lower)** |

**Determinism:** chunked-100k build (62 batches) vs the canonical reference (built pre-chunking, buffer-all)
→ **bit-exact, 0 divergent rows** across all 4 tables (5,951,233 rows), via a memory-safe DuckDB-side
symmetric `EXCEPT` (the built-in `--verify` OOMs at this scale — §10). Arrow is independently bit-exact vs
`executemany` (slice A/B). Chunking changes only *when* rows insert, never the data.

---

## 10. Lessons learned

- **Measure before optimizing.** cProfile's per-call model inflated a hot Python loop and hid a single
  GIL-released C call that was ~98 % of the time. An un-profiled phase-breakdown found the real bottleneck
  the profiler had ranked near-zero. Profilers have a model; validate it against wall-clock reality.
- **Re-profile after every major optimization.** The bottleneck moves. Once the write collapsed from ~197 s
  to ~1 s, the ~6 s compute loop became the new floor — a completely different regime that reprioritized all
  remaining work (and made Phase 2 parallelism unnecessary for current workloads).
- **Validate numerical changes against a higher-precision reference.** The 45-row discrepancy was resolved
  not by argument but by an exact `fractions.Fraction` ground truth, which proved the *current* code more
  accurate and the *reference* stale — the opposite of the initial assumption.
- **Separate correctness work from performance work.** Arrow (perf) was proven bit-exact independently; the
  `_slope` accuracy question (correctness) and the `_values_equal` tolerance mis-scaling (framework) were
  each adjudicated on their own merits and deliberately *not* bundled into the performance change.
- **Let measured evidence drive engineering decisions.** Every default (Arrow over executemany, 100k batch
  size, keeping pure-Python `_slope`, deferring Phase 2) is backed by a number in this document, not an
  estimate. When measurement contradicted the plan, the plan was updated before continuing.

---

## 11. Deferred work (framework evolution — not blockers)

- **DuckDB-side `verify()` rewrite.** `replay.verify` → `_read_table` materializes **both** built + ref
  tables into nested Python dicts (O(rows), unbounded) → `MemoryError` on the ~100-min dataset, unusable on
  the 8 GB target / full-day. Reimplement the per-table diff **DuckDB-side** (ATTACH + SQL `EXCEPT`/PK-join),
  as already used for the determinism gates here.
- **`atol + rtol` verification semantics.** `_values_equal` uses a pure **absolute** `atol = 1e-9` that
  mis-scales for unbounded quantities (a ~1e-12 *relative* diff on a ~1e6 slope trips a 1e-9 absolute gate —
  the §6 finding). Adopt NumPy-`isclose` semantics `|a-b| ≤ atol + rtol·|b|`. Naturally folds into the
  DuckDB-side rewrite above.
- **Phase 2 — multi-process time-chunked replay.** Deferred pending future workloads; design documented in
  the plan. Unlikely required for today's data volumes on current measurements, available if they grow.
- **Future incremental / real-time rolling engine.** Move rolling reductions from recompute-over-window to
  O(1)/tick running sums (ring buffers), reusing the exact validated metric bodies online. Phase 1c's
  reducer seam is the intended entry point; the columnar row-tuple contract stays the stable compute↔sink
  interface.

**Offline replay optimization is complete.** Everything above is framework evolution, not a blocker for
production use.
