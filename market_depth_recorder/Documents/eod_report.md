# `eod_report.py` — EOD health & sanity-check report (P10-C)

## Responsibility
Offline, post-session verification of **one trading day's** captured artifacts, producing a
PASS/WARN/FAIL report (markdown + JSON) into `<dated-dir>/reports/`. It is the operator's "did the day
capture cleanly?" gate — it would have caught the P9 NIFTY-no-depth failure automatically. **No live feed
required**; the raw reader tolerates a crash-truncated tail (missing EOF).

## Public API
- `run_eod_report(config, session_date, *, now=None, write=True) -> (exit_code, report_dict)` — the entry
  point. Builds the report, optionally writes the md+JSON, returns `0` unless any check **FAIL**ed (then `1`).
- `build_report(config, session_date, *, now=None) -> dict` — run all checks, aggregate, no I/O side effects
  beyond reading artifacts.
- `check_raw / check_live_db / check_duckdb / check_ops` — per-tier check lists (unit-testable in isolation).
- `render_markdown(report) -> str`, `write_report(report, session_date) -> (md_path, json_path)`.

## CLI
```
python -m market_depth_recorder --eod-report [--date YYYY-MM-DD] --config <cfg>
```
`--date` defaults to **today** (IST). Exit `0` clean / `1` on any FAIL. `--date` is only valid with
`--eod-report` (usage error otherwise).

## Checks (status = worst-wins overall)
**Tier 0 — raw `.jsonl.gz`:** `present` · `header` · `instruments` block · `config_hash` vs current ·
`eof` (clean vs missing→WARN) · `records` · `timespan` · **`depth_coverage.<U>`** (0 depth packets → FAIL —
the P9 catch) · **`depth_level.<U>`** (actual vs `requested_depth`; degraded → WARN, the §9 alarm) ·
`audit_fields` (feed_time coverage **among 50-level/TBT packets only** — 5-level books legitimately omit it,
so an all-5-level day is N/A→PASS) · `orders_populated` (M13/M14) · `book_integrity` (crossed/locked %).
**Tier 1 — live SQLite:** `present` (missing→WARN, rebuildable) · `tables` (4 present) ·
**`option_rows.<U>`** (per-underlying coverage; 0 → FAIL). **Tier 2 — DuckDB:** `present` (absent→SKIP —
reprocess may be pending) · `tables` populated · `meta` (`recorder_meta` schema_version/config_hash/built_by).
**Ops — `health.json`:** `drops` (raw/db dropped → FAIL if any) · `cycle_ms` (<30 ms, re-tuned post-P10-E) · `rss_mb` (<500) ·
`degraded`.

## Config keys consumed
`recorder.{output_dir, date_partitioned, health_file_path}`, each `underlyings[].{name, spot_symbol,
requested_depth}`, and `config_hash` (for the provenance cross-checks). Report-only thresholds (30 ms /
500 MB / 15% crossed) are fixed spec (§5.1) targets held as module constants — not engine tunables, so not
config keys.

## Paths & FDs
Reads the dated dir via `utils.session_output_dir` and the writers' `resolve_filename` staticmethods
(no format drift). Opens the raw gzip, the live SQLite (read-only URI), and — lazily, only if the file
exists — the DuckDB (read-only), each closed in a `finally`. `health.json` read via `with`. Reports written
via `utils.atomic_write` (temp + `os.replace`). No threads, no sockets, no subprocess.

## Tests
`tests/test_eod_report.py` (15): `_classify`; `check_raw` (clean / no-EOF / NIFTY-no-depth→FAIL / missing /
config-hash mismatch); `check_live_db` (clean / NIFTY-missing→FAIL / absent); `check_duckdb` (absent→SKIP /
populated+meta); `check_ops` (clean / drops-FAIL+perf-WARN); `run_eod_report` end-to-end (clean→0, NIFTY
gap→1, writes md+JSON).

## First real run (2026-07-06)
Run against the P9 capture: **overall FAIL** — correctly flagged `raw.depth_coverage.NIFTY` and
`live.option_rows.NIFTY` (the TBT-cap finding), plus WARNs on the missing EOF (force-kill),
SENSEX 5-level degrade, and `cycle_ms_max=25.96 > 15` at session end. Report at
`<data>/reports/eod_healthcheck_20260706.md`.
