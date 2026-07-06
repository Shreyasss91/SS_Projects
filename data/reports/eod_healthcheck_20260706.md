# EOD Health & Sanity Report — 2026-07-06

**Overall: ❌ FAIL**  ·  PASS 17 · WARN 3 · FAIL 2 · SKIP 1

- Generated: 2026-07-06T15:13:11.672290+05:30
- Config hash: `sha256:480fc4c4f5aebb99cc3bb1d8be4a4d79bc4d849592de5ea64c6839f423483a65`
- Data dir: `./data`

## Tier 0 — Raw audit log

| Check | Status | Detail |
| --- | --- | --- |
| `raw.present` | ✅ PASS | market_depth_raw_20260706.jsonl.gz |
| `raw.header` | ✅ PASS | session_date=2026-07-06 |
| `raw.instruments` | ✅ PASS | HEADER carries the instruments block (self-contained replay) |
| `raw.config_hash` | ✅ PASS | matches current config |
| `raw.eof` | ⚠️ WARN | no EOF marker — incomplete/crash capture (replay-tolerant) |
| `raw.records` | ✅ PASS | 36710 data packets |
| `raw.timespan` | ✅ PASS | 13:45:53–13:54:41 IST (9 min) |
| `raw.depth_coverage.NIFTY` | ❌ FAIL | NO depth packets captured (feed/subscription failure) |
| `raw.depth_coverage.SENSEX` | ✅ PASS | 35975 depth packets |
| `raw.depth_level.SENSEX` | ⚠️ WARN | DEGRADED: actual 5 < requested 50 (§9 — TBT unsupported / capped?) |
| `raw.audit_fields` | ✅ PASS | no 50-level (TBT) packets this session — audit fields N/A (5-level books omit feed_time/depth_levels/is_50_depth) |
| `raw.orders_populated` | ✅ PASS | 100.0% of depth levels have orders>0 (M13/M14 computable) |
| `raw.book_integrity` | ✅ PASS | 95.1% books ordered (crossed 1277, locked 471 of 35584) |

## Tier 1 — Live SQLite

| Check | Status | Detail |
| --- | --- | --- |
| `live.present` | ✅ PASS | market_depth_live_20260706.db |
| `live.tables` | ✅ PASS | 4 tables present |
| `live.option_rows.NIFTY` | ❌ FAIL | 0 option_strike_metrics rows |
| `live.option_rows.SENSEX` | ✅ PASS | 47867 option_strike_metrics rows |

## Tier 2 — DuckDB analytics

| Check | Status | Detail |
| --- | --- | --- |
| `duckdb.present` | ➖ SKIP | market_depth_analytics_20260706.duckdb not built yet (run --catchup / auto reprocess) |

## Ops — health.json

| Check | Status | Detail |
| --- | --- | --- |
| `ops.health` | ✅ PASS | state=record as of 13:54:33 |
| `ops.drops` | ✅ PASS | raw_dropped=0, db_dropped=0 |
| `ops.cycle_ms` | ⚠️ WARN | p50=10.0 max=25.96219995757565 (target <15 ms) |
| `ops.rss_mb` | ✅ PASS | 60 MB (target <500) |
| `ops.degraded` | ✅ PASS | degraded_level=0 |
