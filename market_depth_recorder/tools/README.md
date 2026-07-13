# `tools/` — maintained developer utilities

Standalone, parameterized command-line utilities for validating and benchmarking the Market Depth
Recorder. These are **maintained tools**, not investigation scratch — each takes CLI arguments (no
hard-coded paths), has `--help`, returns meaningful exit codes, and documents its purpose, workflow,
and example usage in its module docstring. They are dev-only and not on any runtime path.

Run any tool directly (it puts the project root on `sys.path` itself, so no `PYTHONPATH` needed):

```
python market_depth_recorder/tools/<area>/<tool>.py --help
```

## `validation/`

| Tool | Purpose |
| --- | --- |
| `duckdb_table_diff.py` | Memory-safe DuckDB-side diff of two analytics `.duckdb` stores — `exact` (bit-exact symmetric `EXCEPT`, a determinism gate) or `tolerance` (`atol + rtol` float compare). The scalable stand-in for the OOM-prone built-in `verify()` at full-day scale. |
| `highprec_slope.py` | Adjudicate the closed-form OLS `_slope` against exact `fractions.Fraction` ground truth — the discipline for validating a numerical change against a higher-precision reference rather than an assumption. |

## `performance/`

| Tool | Purpose |
| --- | --- |
| `bench_chunk.py` | Rebuild a raw log at a given streaming batch size and report wall time, replay/finalize split, **peak RSS**, and batches written — the gate for keeping writer memory bounded on the 8 GB target. Run one batch size per process for a clean peak. |

## Related

- `market_depth_recorder/benchmark.py` — the reusable replay benchmark harness (`run_benchmark`).
- `Documents/PERFORMANCE.md` — the performance engineering record these tools helped produce.
- `Documents/archive/validation-artifacts/` — the frozen, investigation-specific predecessors.
