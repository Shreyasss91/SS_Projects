# EOD Health & Sanity Report — 2026-07-07

**Overall: ⚠️ WARN**  ·  PASS 24 · WARN 2 · FAIL 0 · SKIP 0

- Generated: 2026-07-07T12:42:58.665966+05:30
- Config hash: `sha256:fb97f393dc30a9fdfc8b91438ed7afefc742f9782fce1891e4c509ae033bae5e`
- Data dir: `./market_depth_recorder/data\2026-07-07`

## Tier 0 — Raw audit log

| Check | Status | Detail |
| --- | --- | --- |
| `raw.present` | ✅ PASS | market_depth_raw_20260707.jsonl.gz |
| `raw.header` | ✅ PASS | session_date=2026-07-07 |
| `raw.instruments` | ✅ PASS | HEADER carries the instruments block (self-contained replay) |
| `raw.config_hash` | ✅ PASS | matches current config |
| `raw.eof` | ✅ PASS | clean EOF; record_count=61538 |
| `raw.records` | ✅ PASS | 61538 data packets |
| `raw.timespan` | ✅ PASS | 12:16:20–12:26:00 IST (10 min) |
| `raw.depth_coverage.NIFTY` | ✅ PASS | 5502 depth packets |
| `raw.depth_coverage.SENSEX` | ✅ PASS | 55495 depth packets |
| `raw.depth_level.NIFTY` | ✅ PASS | actual 50 = requested 50 |
| `raw.depth_level.SENSEX` | ⚠️ WARN | DEGRADED: actual 5 < requested 50 (§9 — TBT unsupported / capped?) |
| `raw.audit_fields` | ✅ PASS | 100.0% of 5502 TBT packets carry feed_time (exchange clock the SDK strips) |
| `raw.orders_populated` | ✅ PASS | 99.9% of depth levels have orders>0 (M13/M14 computable) |
| `raw.book_integrity` | ✅ PASS | 93.8% books ordered (crossed 2726, locked 946 of 58778) |

## Tier 1 — Live SQLite

| Check | Status | Detail |
| --- | --- | --- |
| `live.present` | ✅ PASS | market_depth_live_20260707.db |
| `live.tables` | ✅ PASS | 4 tables present |
| `live.option_rows.NIFTY` | ✅ PASS | 2900 option_strike_metrics rows |
| `live.option_rows.SENSEX` | ✅ PASS | 69480 option_strike_metrics rows |

## Tier 2 — DuckDB analytics

| Check | Status | Detail |
| --- | --- | --- |
| `duckdb.present` | ✅ PASS | market_depth_analytics_20260707.duckdb |
| `duckdb.tables` | ✅ PASS | 4 tables populated |
| `duckdb.meta` | ✅ PASS | built_by=replay schema_version=1 config_hash matches |

## Ops — health.json

| Check | Status | Detail |
| --- | --- | --- |
| `ops.health` | ✅ PASS | state=close as of 12:25:50 |
| `ops.drops` | ✅ PASS | raw_dropped=0, db_dropped=0 |
| `ops.cycle_ms` | ⚠️ WARN | p50=21.7 max=43.239699996775016 (target <15 ms) |
| `ops.rss_mb` | ✅ PASS | 66 MB (target <500) |
| `ops.degraded` | ✅ PASS | degraded_level=0 |
