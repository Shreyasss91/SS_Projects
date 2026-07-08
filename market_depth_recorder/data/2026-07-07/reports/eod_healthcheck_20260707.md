# EOD Health & Sanity Report — 2026-07-07

**Overall: ⚠️ WARN**  ·  PASS 22 · WARN 4 · FAIL 0 · SKIP 0

- Generated: 2026-07-07T19:47:43.596472+05:30
- Config hash: `sha256:8a48bcdd4fca933d1dbc85bd9a5c1dc055403392da0afeb22e629af550a1468b`
- Data dir: `./market_depth_recorder/data\2026-07-07`

## Tier 0 — Raw audit log

| Check | Status | Detail |
| --- | --- | --- |
| `raw.present` | ✅ PASS | market_depth_raw_20260707.jsonl.gz |
| `raw.header` | ✅ PASS | session_date=2026-07-07 |
| `raw.instruments` | ✅ PASS | HEADER carries the instruments block (self-contained replay) |
| `raw.config_hash` | ⚠️ WARN | HEADER config_hash sha256:fb97f393dc30a9fdfc8b91438ed7afefc742f9782fce1891e4c509ae033bae5e != current sha256:8a48bcdd4fca933d1dbc85bd9a5c1dc055403392da0afeb22e629af550a1468b (config changed since capture) |
| `raw.eof` | ⚠️ WARN | EOF record_count=609943 != observed 671481 |
| `raw.records` | ✅ PASS | 671481 data packets |
| `raw.timespan` | ✅ PASS | 12:16:20–15:26:53 IST (191 min) |
| `raw.depth_coverage.NIFTY` | ✅ PASS | 56754 depth packets |
| `raw.depth_coverage.SENSEX` | ✅ PASS | 608888 depth packets |
| `raw.depth_level.NIFTY` | ✅ PASS | actual 50 = requested 50 |
| `raw.depth_level.SENSEX` | ⚠️ WARN | DEGRADED: actual 5 < requested 50 (§9 — TBT unsupported / capped?) |
| `raw.audit_fields` | ✅ PASS | 100.0% of 56754 TBT packets carry feed_time (exchange clock the SDK strips) |
| `raw.orders_populated` | ✅ PASS | 99.9% of depth levels have orders>0 (M13/M14 computable) |
| `raw.book_integrity` | ✅ PASS | 92.6% books ordered (crossed 32794, locked 14836 of 645038) |

## Tier 1 — Live SQLite

| Check | Status | Detail |
| --- | --- | --- |
| `live.present` | ✅ PASS | market_depth_live_20260707.db |
| `live.tables` | ✅ PASS | 4 tables present |
| `live.option_rows.NIFTY` | ✅ PASS | 34155 option_strike_metrics rows |
| `live.option_rows.SENSEX` | ✅ PASS | 819481 option_strike_metrics rows |

## Tier 2 — DuckDB analytics

| Check | Status | Detail |
| --- | --- | --- |
| `duckdb.present` | ✅ PASS | market_depth_analytics_20260707.duckdb |
| `duckdb.tables` | ✅ PASS | 4 tables populated |
| `duckdb.meta` | ⚠️ WARN | built_by=replay schema_version=1 config_hash MISMATCH |

## Ops — health.json

| Check | Status | Detail |
| --- | --- | --- |
| `ops.health` | ✅ PASS | state=close as of 15:34:57 |
| `ops.drops` | ✅ PASS | raw_dropped=0, db_dropped=0 |
| `ops.cycle_ms` | ✅ PASS | p50=1.1 max=4.73230000352487 (target <30 ms) |
| `ops.rss_mb` | ✅ PASS | 78 MB (target <500) |
| `ops.degraded` | ✅ PASS | degraded_level=0 |
