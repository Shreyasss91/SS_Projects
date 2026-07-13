# Engineering History — Market Depth Recorder

A lightweight, chronological index of **major engineering milestones**. It exists so a future
contributor has **one place to discover** the project's significant efforts and jump to the detailed
records — it links, it does not duplicate.

How the records are organized:
- **Living docs** (current state): `ARCHITECTURE.md`, per-module `*.md`, `PERFORMANCE.md`.
- **`CHANGELOG.md`**: the granular, dated running log (one entry per phase/iteration).
- **`archive/`**: completed, frozen historical artifacts (finished plans, engineering journals,
  investigation evidence) — preserved for provenance, not maintained.
- **`HISTORY.md`** (this file): the milestone-level table of contents over those records.

> Appending a milestone: add a new dated section at the **bottom** (chronological order), with a
> one-line status/summary and links to its living record, its archived plan/journal, and any tools
> or artifacts it produced. Keep entries short — depth belongs in the linked documents.

---

## 2026-07 — Offline Replay Optimization

**Status:** ✅ Complete — milestone commit `1641f22`.

**Summary:** Cut the offline analytics-replay rebuild from ~3 h 52 m to 244.8 s (~57× on the
representative ~100-min dataset) and bounded writer peak RSS to ~800 MB (4× lower), by discovering
through measurement that the DuckDB **write path** — not metric compute — was ~98 % of the cost,
then redesigning it around a chunked-streaming Arrow columnar backend. Determinism preserved
(bit-exact); the canonical reference was regenerated after an exact-`Fraction` adjudication proved the
pure-Python `_slope` more accurate than the stale numpy reference.

**Records:**
- Canonical performance report — [`PERFORMANCE.md`](PERFORMANCE.md)
- Historical implementation plan — [`archive/offline-replay-optimization-implementation-plan-COMPLETE.md`](archive/offline-replay-optimization-implementation-plan-COMPLETE.md)
- Engineering journal (narrative/decisions/dead-ends) — [`archive/offline-replay-optimization-engineering-journal.md`](archive/offline-replay-optimization-engineering-journal.md)
- Frozen validation evidence + method — [`archive/validation-artifacts/`](archive/validation-artifacts/)
- Detailed change entries — [`CHANGELOG.md`](CHANGELOG.md) (Phase P-C and the default-flip entries)

**Reusable tools produced:**
- [`tools/validation/duckdb_table_diff.py`](../tools/validation/duckdb_table_diff.py) — memory-safe DuckDB-side determinism / value-parity diff.
- [`tools/validation/highprec_slope.py`](../tools/validation/highprec_slope.py) — exact-`Fraction` numerical-accuracy harness.
- [`tools/performance/bench_chunk.py`](../tools/performance/bench_chunk.py) — writer peak-RSS + throughput benchmark.

**Deferred (framework evolution, not blockers):** DuckDB-side `verify()` rewrite; `atol + rtol` verify
semantics; Phase 2 multi-process replay; future real-time incremental rolling engine. See
[`PERFORMANCE.md` §11](PERFORMANCE.md).

<!-- Append the next milestone section below this line. -->
