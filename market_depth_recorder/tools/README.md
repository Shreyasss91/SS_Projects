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

## `fyers/`

Broker-specific FYERS streaming diagnostics. **Scope exception:** the two TBT probes import
OpenAlgo platform code to drive the FYERS client directly (read-only w.r.t. platform code) — run
them from OpenAlgo's environment. `depth_transition_probe.py` does not: it speaks the proxy's
WebSocket protocol and imports nothing from the platform. See `fyers/README.md`.

| Tool | Purpose |
| --- | --- |
| `tbt_channel_probe.py` | Probe whether FYERS TBT (50-level depth) can stream on channels other than 1 — settles whether the 5-symbol ceiling is an upstream FYERS limit or a client-side channel-protocol bug. Fresh-connection test matrix (T1/T2/T2p/T3) capturing subscribe requests, FYERS ACKs/errors, and per-symbol packet counts. |
| `tbt_multiconn_probe.py` | Measure the effective concurrent 50-level budget across FYERS' 3 allowed connections. Opens N independent connections, each a distinct 5-symbol group, observed concurrently (C1 baseline / C3 core / C4 4th-connection ceiling), capturing per-connection + per-symbol connect/snapshot/incremental timing, sustained packet counts, drops, and ACKs/errors. Established **`tbt_budget = 15`** (3 × 5). |
| `depth_transition_probe.py` | Measure what a 5 <-> 50 depth change actually does on the OpenAlgo proxy path the recorder uses — the F7 gate on the Broker Adapter (Plan_002 §20.1). Runs the four transitions in both symbol spellings and both mechanisms, separating *requested* / *reported* / **observed** depth so an accepted request can never be recorded as a depth change. Dry-run by default; `--live` opt-in, capped at 2 instruments. |
| `_depth_probe_model.py` | Broker-neutral data model behind the depth probe (operations, symbol forms, the OBSERVED/INFERRED/UNKNOWN lattice, evidence serialisation). Pure — no network, no broker import. Not a standalone tool. |
| `_tbt_common.py` | Shared building blocks for both FYERS TBT probes (token load, instrumented client subclass, frame helpers, `Recorder`) — one implementation, imported by both. Not a standalone tool. |

## Related

- `market_depth_recorder/benchmark.py` — the reusable replay benchmark harness (`run_benchmark`).
- `Documents/PERFORMANCE.md` — the performance engineering record these tools helped produce.
- `Documents/archive/validation-artifacts/` — the frozen, investigation-specific predecessors.
