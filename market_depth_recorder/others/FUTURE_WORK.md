# Future Work — Market Depth Recorder

**Engineering backlog and idea repository.** This is *not* a living architecture document
(`Documents/ARCHITECTURE.md`) nor an active implementation plan (those live in `~/.claude/plans/`
while in progress, and land in `Documents/archive/` when complete). It is a lightweight place to
record deferred items, future milestones, and raw ideas so they are not lost and do not clutter active
plans.

Each item below follows a fixed template: **Title · Priority · Status · Background · Why it matters ·
Current state · Possible implementation approach · Dependencies · Success criteria · Notes.** When an
item is picked up, it graduates into its own scoped implementation plan; when finished, its plan and
journal are archived and it is struck from (or marked done in) this backlog.

Priority = High / Medium / Low. Status = Deferred (consciously postponed from a completed effort) /
Future (planned but not yet started) / Research (needs investigation before it can be scoped).

---

# High Priority

## 1. DuckDB-side `verify()` rewrite

- **Priority:** High
- **Status:** Deferred (from the Offline Replay Optimization milestone)
- **Background:** `replay.verify()` → `_read_table` materializes **both** the built and reference
  tables into nested Python dicts (rows × ~30 cols × 2). During the ~100-min canonical rebuild this
  OOM'd, and every determinism gate in the milestone had to fall back to an ad-hoc DuckDB-side diff.
  The generalized replacement already exists as a tool (`tools/validation/duckdb_table_diff.py`) but is
  not yet wired into the product's `verify()` path.
- **Why it matters:** The built-in determinism gate is currently **unusable at scale** — it cannot run
  on the representative dataset, let alone a full session on the 8 GB target machine. Determinism is the
  recorder's correctness guarantee (both derived stores are reconstructable from Tier 0), so its gate
  must scale to the largest datasets it protects.
- **Current state:** `verify()` and `_read_table` unchanged (O(rows) memory). A working, validated
  DuckDB-side diff exists in `tools/validation/duckdb_table_diff.py` (exact symmetric `EXCEPT` and
  tolerance modes) — it just isn't the code path `--verify` calls.
- **Possible implementation approach:**
  - Reimplement the per-table comparison DuckDB-side: `ATTACH` both stores, compare with symmetric
    `EXCEPT` (exact) or a PK-join predicate (tolerance) — the logic already prototyped in the tool.
  - Stream/aggregate results inside DuckDB so Python only ever holds counts and a bounded sample of
    diverging rows, never whole tables.
  - Fold `tools/validation/duckdb_table_diff.py` and `replay.verify()` onto one shared implementation
    so there is a single comparison definition.
  - Preserve the existing report shape (per-table verdict + first-N divergences) and the `config_hash`
    provenance gate.
- **Dependencies:** Naturally implemented **together with item #2** (the tolerance semantics live in the
  same comparison). Uses the existing `_TABLE_SPEC` (columns/PK).
- **Success criteria:**
  - `--verify` runs to completion on the full representative dataset (and projects safely to full-day)
    with bounded, roughly constant memory.
  - Bit-identical verdicts to the current implementation on datasets small enough for both to run.
  - Existing determinism guarantees and provenance gating preserved; test suite green.
- **Notes:** The tool already reproduces the known results (legacy-vs-canonical exact diff, and the
  45-cell tolerance finding). This is largely a "promote the tool into the product path" effort. See
  `Documents/PERFORMANCE.md` §11 and the engineering journal.

## 2. Relative tolerance verification (`atol + rtol`)

- **Priority:** High
- **Status:** Deferred (from the Offline Replay Optimization milestone)
- **Background:** `replay._values_equal` compares floats with a **pure absolute** tolerance
  (`_VERIFY_ATOL = 1e-9`). During Arrow validation, 45 `book_pressure_slope` cells tripped the gate at
  `abs ≈ 1.4e-9` while agreeing to `~1e-12` **relative** — because on values of magnitude ~1e6, an
  absolute 1e-9 gate is far tighter than intended. Exact-`Fraction` adjudication proved neither
  implementation wrong (the current `_slope` was in fact *more* accurate); the gate was mis-scaled.
- **Why it matters:** A pure-absolute tolerance silently mis-judges any unbounded quantity (slopes,
  large sums). It produces false "drift" on correct code and could equally mask real drift on
  small-magnitude columns. Correct verification semantics are foundational to trusting every future
  rebuild.
- **Current state:** `_values_equal` unchanged (pure absolute). `tools/validation/duckdb_table_diff.py`
  already implements `abs(a-b) <= atol + rtol*abs(ref)` in its tolerance mode and demonstrates that
  `rtol=1e-9` clears the 45-cell finding.
- **Possible implementation approach:**
  - Adopt numpy-`isclose`-style semantics `abs(a-b) <= atol + rtol*abs(b)` in the shared comparison.
  - Choose defaults deliberately (e.g. `atol=1e-9`, `rtol=1e-9`) and make them configurable; document
    the rationale.
  - Consider per-column overrides if any column legitimately needs exact matching.
- **Dependencies:** Should be implemented **with item #1** — same comparison code, one change.
- **Success criteria:**
  - Large-magnitude columns no longer produce false drift at ~1e-12 relative agreement.
  - Small-magnitude columns are not made *looser* than today (no masking of real drift).
  - Decision and defaults documented; a regression test covers the large-magnitude slope case.
- **Notes:** Kept deliberately **separate** from the Arrow work (a like-for-like rebuild is already
  bit-exact, so it wasn't needed to unblock the milestone). It is a framework-correctness improvement
  on its own merits. See `Documents/PERFORMANCE.md` §6 for the full `_slope` investigation.

---

# Medium Priority

## 3. Phase 2 — Parallel replay

- **Priority:** Medium
- **Status:** Deferred (design complete, not implemented)
- **Background:** The original optimization plan included a multi-process, time-chunked replay driver
  (`replay_mode: single|multi`, `replay_workers: auto|N`) to get ~Ncore× throughput. After the write
  path was fixed and chunked-Arrow landed, a single-process replay rebuilds the representative dataset
  in ~4 minutes, so parallelism was not required — but the design was preserved, not discarded.
- **Why it matters:** Larger datasets (true full sessions, multi-day backfills, or a much wider chain)
  could reintroduce a throughput ceiling that single-process replay can't meet. Having a validated
  design ready avoids a from-scratch effort if that day comes.
- **Current state:** Not implemented. Full design retained in
  `Documents/archive/offline-replay-optimization-implementation-plan-COMPLETE.md` (§Phase 2): contiguous
  time-chunks per worker, a config-derived pre-roll warmup window
  `W = 2·max(time_windows) + 1 + staleness_timeout + margin` so rolling history is warm at each chunk
  boundary, per-worker temp partitions, and an order-independent merge — output **bit-identical
  regardless of worker count**.
- **Possible implementation approach:**
  - Isolate all chunking/worker/merge logic in the replay driver; `TickProcessor` and metrics stay
    parallelism-unaware.
  - `ProcessPoolExecutor` (or `Popen`) workers, each writing a temp partition; a final merge unions in
    timestamp order into the canonical store via the existing `DuckDBAnalyticalWriter` DDL/meta.
  - Fail-clean: any worker failure aborts the whole replay and sweeps all temp partitions (context-
    managed + `finally`).
- **Dependencies:** Benefits from item #1 (a scalable `verify()`) for the worker-count-invariance gate.
  Reuses the chunked-Arrow writer.
- **Success criteria (for revisiting):** A single-process replay of the target dataset exceeds an
  acceptable wall-clock budget **and** profiling shows compute (not I/O) is the ceiling. Then:
  `multi/workers=auto` and `multi/workers=1` both `--verify` clean against the single-process reference
  (output independent of worker count), with a measured near-linear speedup and no FD/temp leaks.
- **Notes:** Wording is intentionally "deferred pending future workloads," not "dropped" — the
  architecture stays available. Revisit only when measured evidence justifies it.

## 4. Incremental real-time rolling engine

- **Priority:** Medium
- **Status:** Future
- **Background:** Rolling-window metrics currently **recompute over the whole window** each second
  (offline replay tolerates this). For a Stage-2 real-time path, the same reductions should be
  incremental so per-tick cost is O(1) rather than O(window).
- **Why it matters:** It makes the validated rolling metrics usable **online** (live trading) with
  bounded per-tick latency, and would also speed offline replay. Replay and live already share one
  `TickProcessor` + metric registry, so doing this once benefits both without a second implementation to
  drift.
- **Current state:** Recompute-over-window bodies. Phase 1c intentionally left a thin **reducer seam**
  (a pre-extracted series + window length) as the entry point for swapping individual metrics to
  incremental implementations without an engine refactor. Live capture already computes only the thin
  validated `live_metrics` subset, so the online path is not otherwise blocked.
- **Possible implementation approach:**
  - Replace window recomputation with ring-buffer running sums (and Welford-style running variance) per
    strike, updated on each new second and decremented as samples age out.
  - Swap metrics one at a time behind the reducer seam, each gated by `--verify` bit-exactness (within
    tolerance) against the recompute implementation on replay.
  - Keep the columnar row-tuple contract (`OPTION_COLUMNS` etc.) as the stable compute↔sink interface.
- **Dependencies:** The reducer seam (already present). Benefits from items #1/#2 (verification) for the
  equivalence gate.
- **Success criteria:** Per-tick rolling cost is O(1) in window length; incremental output matches the
  recompute output within verification tolerance across a full replay; live per-cycle latency stays
  within budget.
- **Notes:** This is the main bridge from "validated offline metrics" to "real-time feature bus." See
  `Documents/PERFORMANCE.md` §11 and the plan's "Part B — Real-time suitability."

## 5. Benchmark & validation framework improvements

- **Priority:** Medium
- **Status:** Future
- **Background:** The milestone produced good ad-hoc tooling (`benchmark.py`, `tools/performance/
  bench_chunk.py`, `tools/validation/*`) but performance/correctness measurement is still manual and
  point-in-time. There is no automated suite or historical tracking.
- **Why it matters:** Without continuous measurement, a future change could silently regress throughput
  or peak RSS (the 8 GB constraint) or introduce numerical drift, and it would only be caught by chance.
  The whole milestone was evidence-driven; institutionalizing that evidence protects the gains.
- **Current state:** Manual invocation of the harness/tools on a chosen slice or dataset; results
  recorded by hand into docs. No regression thresholds, no history.
- **Possible implementation approach:**
  - A small automated benchmark suite over a committed fixed slice (wall, CPU, peak RSS, rows/s) that
    emits a machine-readable record.
  - Optional CI/local regression check that fails when wall or peak RSS regresses beyond a threshold vs a
    stored baseline.
  - Append benchmark records to a history file for trend visibility; automate the RSS-per-batch report.
  - Fold the reusable validation tools into a documented, one-command "validate a rebuild" flow.
- **Dependencies:** `benchmark.py`, the `tools/` utilities. A stable committed benchmark fixture.
- **Success criteria:** A single command produces a comparable benchmark record; a regression in
  throughput or peak RSS is detected automatically; a determinism check is one command away.
- **Notes:** Keep fixtures small and committed so runs are fast and comparable. Don't let benchmark
  artifacts (DBs) leak into git — they are already gitignored.

---

# Low Priority / Research

## 6. Future storage / backend ideas

- **Priority:** Low
- **Status:** Research
- **Background:** The write path is now a chunked-Arrow columnar bulk load behind a backend-agnostic
  `_flush(table)` seam, with `executemany` retained as a deprecated fallback. Other loading/storage
  strategies were never explored because Arrow already met the goal.
- **Why it matters:** Future scale, portability, or interoperability needs (sharing analytics with other
  tools, incremental/streaming consumers) might favor a different storage or loading strategy. Worth
  keeping on the radar, not worth acting on now.
- **Current state:** Single canonical DuckDB store per session, rebuilt offline; chunked-Arrow default.
- **Possible implementation approach (candidates to investigate):**
  - Alternative DuckDB loading strategies (e.g. `COPY`, appender API, native Parquet scan).
  - A Parquet intermediate pipeline (per-table Parquet → DuckDB view/import) for interoperability and
    partial/parallel writes.
  - True streaming writers (write as replay proceeds, no separate finalize) building on the `_flush`
    seam.
  - Other analytical storage backends if a concrete need arises.
- **Dependencies:** None hard; the `_flush(table)` seam is the natural insertion point.
- **Success criteria:** Any candidate must preserve determinism (bit-exact within tolerance), atomic
  all-or-nothing output, bounded peak RSS, and throughput at least comparable to chunked-Arrow — or
  offer a clear interoperability/scale win that justifies a trade-off.
- **Notes:** Research only. Do not pursue without a concrete driving requirement; chunked-Arrow is
  sufficient for current workloads.

## 7. Engineering tooling

- **Priority:** Low
- **Status:** Research
- **Background:** The `tools/` directory now holds a few maintained utilities. There is room for more
  developer-experience tooling around validation, benchmarking, profiling, and docs.
- **Why it matters:** Better tooling lowers the cost of the evidence-driven discipline that made this
  milestone succeed, and makes future investigations faster and more repeatable.
- **Current state:** `tools/validation/` (diff, slope harness) and `tools/performance/` (RSS bench)
  exist; everything else is manual.
- **Possible implementation approach (candidates):**
  - Additional reusable validation tools (schema/row-count diff, provenance/`config_hash` inspector).
  - Benchmark visualization (plot wall/RSS trends from the history file).
  - Profiling automation (one-command cProfile + phase-breakdown on a fixed slice, with the
    profiler-vs-reality caveat baked in).
  - Documentation automation (e.g. keeping module docs / this backlog cross-referenced).
- **Dependencies:** None hard.
- **Success criteria:** Each tool is parameterized, self-documenting (`--help`, docstring), returns
  meaningful exit codes, and earns its place by being reused — not one-off investigation code.
- **Notes:** Hold the same bar set in this milestone: maintained tools go in `tools/`; one-off
  investigation scripts stay ephemeral or are archived as evidence, never committed as tooling.

---

# Future Strategy Ideas

Larger, strategic directions that may eventually become **projects** in their own right (each spanning
multiple milestones). These are intentionally **not backlog items yet** — no template, no commitment —
just directions worth remembering so they inform longer-term thinking. Any of these, once concrete and
prioritized, would be broken down into its own set of `FUTURE_WORK` items and implementation plans.

- **Online feature store** — serve the validated metric catalogue as a low-latency, live feature bus for
  strategies (the natural destination of the incremental real-time rolling engine, item #4).
- **Distributed replay** — scale replay across machines (not just cores) for large backfills or many
  sessions in parallel; a superset of Phase 2 (item #3).
- **Cross-day analytics** — analytics that span sessions (multi-day rolling features, regime tracking,
  session-over-session comparisons) rather than the current single-session rebuild.
- **ML feature engineering pipeline** — turn the metric outputs into curated, versioned ML feature sets
  (labeling, alignment, train/serve parity with the live feature store).
- **Multi-underlying replay** — replay and analyze many underlyings/chains together at scale, beyond the
  current configured set, with shared infrastructure.
- **Strategy research infrastructure** — a repeatable harness for backtesting/researching strategies on
  the recorded depth data (dataset management, experiment tracking, reproducibility).
- **Visualization / dashboard improvements** — interactive exploration of depth analytics, benchmark
  trends, and validation results (ties into the tooling ideas, item #7).

---

# Promotion Criteria

An item should normally move from `FUTURE_WORK.md` into its **own implementation plan** when all of the
following hold:

- there is a **clearly defined problem statement**,
- **success criteria are measurable**,
- **dependencies are understood**,
- the **scope is bounded**,
- and it has become an **active engineering priority**.

Until then it stays here as an idea or a deferred backlog item. This reinforces the distinction between
*ideas* and *planned work*: implementation plans should describe what is actually being built, with a
concrete, bounded, measurable objective — not aspirations.

---

# Future Ideas / Parking Lot

A holding area for raw engineering ideas that are **not yet planned work**. Capture the idea and enough
context to revisit it; do not turn it into a plan until it is prioritized.

> **For future contributors:** add new ideas here rather than embedding them in active implementation
> plans or living architecture docs. Keeping speculative ideas out of active plans keeps those plans
> honest about what is actually being built. An idea graduates out of the parking lot only when it is
> picked up and given its own scoped plan.

- _(empty — add ideas as they arise, e.g. "one-line idea — why it might matter — any pointer")_

---

## Intended workflow

This document is one stage of a deliberate lifecycle. Keep each kind of content in its home:

- **Active work → implementation plans.** In-progress plans live in `~/.claude/plans/` and track live
  progress; nothing speculative goes here.
- **Completed work → `Documents/archive/`.** Finished plans, engineering journals, and investigation
  evidence are frozen there for provenance (see `Documents/HISTORY.md` for the milestone index).
- **Permanent results → `Documents/`.** The living architecture, per-module references, `CHANGELOG.md`,
  and the `PERFORMANCE.md` engineering record describe the system as actually built.
- **Future ideas → `others/FUTURE_WORK.md`** (this file). The backlog and parking lot for what is *not*
  yet being built.

When an item here is prioritized, it graduates into its own scoped implementation plan; when that work
completes, it is archived and this backlog is updated. That keeps active plans focused, the living docs
current, and future ideas captured without clutter.

---

## Maintenance note

> During milestone close-out, review this document:
>
> - remove items that have been completed,
> - update priorities if needed,
> - move active items into implementation plans,
> - and archive completed plans under `Documents/archive/`.

Revisiting it each close-out keeps the roadmap useful over the years instead of drifting stale.
