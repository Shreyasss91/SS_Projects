# `replay.py` — Offline replay + DuckDB rebuild (P7)

The **offline path**: replay the lossless Tier-0 raw `.jsonl.gz` through the **same**
`TickProcessor` with the **full** metric catalog and bulk-load the fat Tier-2 DuckDB analytics store
(`market_depth_analytics_YYYYMMDD.duckdb`). This is the normal way Tier 2 exists (the P6 end-of-session
reprocess shells out to `--replay --catchup`); it is also the **determinism harness** (`--verify`).

Authoritative spec: **§8** (§8.1 guarantees, §8.2 invocation, §8.3 simulated clock, §8.4 verify, §8.5
idempotency, §8.6 trigger modes), **§3.6.5** (DuckDB bulk load), **§4.1a** (DuckDB DDL), **§6.2** (warm-up).

## How it works

- **Same processor, only the clock + sink swap (§8.1).** `replay_file` constructs the same
  `TickProcessor` (`active_metrics="all"`), an empty `proc_queue`, and an unbounded `db_queue`; it drives
  the resample **synchronously** (no thread): per data packet `processor.ingest(pkt)` then
  `while recv_ts ≥ next_b: emit_second(int(next_b)); drain db_queue → DuckDBAnalyticalWriter; next_b += 1`.
- **`recv_ts` virtual clock (decision 66).** The 1-second grid is driven by each packet's `recv_ts` — the
  recorder clock the **live** resampler boundary AND staleness keyed off — so the rebuild matches the live
  store second-for-second (buckets *and* timestamps). `next_b` is seeded exactly as the live `run()` loop:
  `(floor(t0/interval)+1)*interval`.
- **Self-contained instruments (decision 65).** The instrument context (symbol↔strike/type + `tick_size`)
  is reconstructed from the raw HEADER's `instruments` block via `InstrumentManager.from_header()` — **no
  REST** — so a log of any age replays correctly even after the live chain has rolled.
- **Robust reader (§8.5, decision 71).** `_load_header` reads the first HEADER; the packet loop skips
  HEADER/EOF meta (multiple HEADERs from same-day restarts tolerated), skips a corrupt/truncated trailing
  JSON line with a counted WARNING, and tolerates a missing EOF.

## Public API

| Symbol | Purpose |
| --- | --- |
| `replay_file(config, raw_path, output_path, *, underlying, from_t, to_t, time_fn) -> _ReplayStats` | Replay one raw log into a fresh DuckDB store (full catalog). Returns `{packets, corrupt_lines, rows, seconds, output}`. |
| `catchup(config, *, time_fn) -> int` | Rebuild, oldest-first, every raw log whose canonical `.duckdb` is missing/older; per-file failure isolated. Returns #rebuilt (§8.6 mode 2). |
| `verify(config, built_path, reference_path, *, live_subset) -> (ok, report)` | Diff a build vs a reference: prior DuckDB build (full) or the SQLite live store (`live_subset`, live_metrics columns only). Aborts on schema/config_hash mismatch (§8.4). |
| `canonical_output` / `replay_side_output` / `live_store_path` | Path resolution: canonical `market_depth_analytics_*.duckdb` vs an ad-hoc `.replay.duckdb` side file vs the SQLite live store. |

## CLI (`__main__.py`, §8.2)

```
python -m market_depth_recorder --replay <raw.jsonl.gz> --output <db>        # canonical build
python -m market_depth_recorder --replay <raw.jsonl.gz> --verify             # → side file, diff vs prior build
python -m market_depth_recorder --replay <raw.jsonl.gz> --verify-against-live # diff live_metrics vs SQLite live store
python -m market_depth_recorder --replay --catchup                           # self-heal every stale day
    [--underlying NIFTY] [--from 09:20 --to 10:30]                           # optional filters
```
Ad-hoc/`--verify` runs default to a `.replay.duckdb` side file so the canonical store is never clobbered.
Exit `0` on success / clean verify, `1` on failure / drift, `2` on a usage error.

## Filters (decision 72) — warm-up caveat

`--underlying` replays a single underlying (its options + spot). `--from/--to` (IST HH:MM) slice against
`recv_ts`. **A mid-session slice restarts rolling warm-up** (the first ≤ largest-window seconds are NULL,
§6.2), so a sliced build is *not* second-for-second comparable to a full-day build — run `--verify` only
on an unsliced build.

## `--verify` semantics (§8.4)

1. Compare `recorder_meta.schema_version`/`config_hash` first; **abort** on a schema-version mismatch (a
   deliberate column-set change is not drift) or a config_hash mismatch.
2. Per table: row counts, then per-`(timestamp, symbol[, window])` tolerance diff (`abs(a−b) ≤ 1e-9`,
   NULL==NULL, bool↔int normalized). Report up to 50 mismatches; exit 1 on any.
3. `--verify-against-live`: compare only the `recorder.live_metrics` output columns (+ base identity
   columns) against the SQLite live store; a table with no live-populated columns (e.g.
   `strike_window_metrics` when no rolling metric is live) is **skipped** (the live store never wrote it).

## Threads · locks · FDs owned

- **No threads, no subprocess, no locks** — replay is a single synchronous pass. The P6 M6 launcher
  already runs it as a reaped subprocess, so nothing here leaks into the daemon.
- **FDs:** the gzip reader (`with`-closed) and the DuckDB build connection (`with`-closed + CHECKPOINT,
  temp-file-then-`os.replace`). `verify`/`catchup` open read-only DuckDB/SQLite connections closed in
  `finally`.

## Config keys consumed

`recorder.{output_dir, resample_interval_sec, live_metrics}`, `analytics_db.{memory_limit_mb, threads}`
(via `DuckDBAnalyticalWriter`), and the underlying spot symbols/exchanges for the `--underlying` filter.

## Genericization

No index/exchange/strike literal — underlyings come from the HEADER/config, all state keyed by `name`;
table/column names are the §4 schema constants imported from `processor`.

## Tests (`tests/test_replay.py`, offline)

`from_header` reconstruction (+ missing-block error + round-trip); replay builds the four tables +
`recorder_meta(built_by="replay")`; **determinism** (`--verify` clean on a re-replay); perturbed metric →
drift reported; corrupt-trailing-line / missing-EOF / multi-HEADER tolerated; rolling warm-up NULLs;
`--catchup` self-heal (rebuild missing, skip up-to-date); `--verify-against-live` (live-subset matches a
real SQLite live store built by the same driver); `--underlying` filter; CLI exit codes. A subprocess
end-to-end runs the exact M6 `--replay --catchup` command against an enriched raw log.
