# integration.md — whole-pipeline harness + FD audit (P8)

`tests/test_integration.py` is the automated, offline **integration & soak** harness: it runs the **real**
four-thread pipeline end-to-end and then the **real** end-of-session reprocess subprocess. It is the
committed replacement for the P6 "manual e2e smoke". Marked `@pytest.mark.integration` (deselect with
`-m "not integration"`); it runs by default in `pytest market_depth_recorder/tests/ -q`.

## What it exercises

1. **Real pipeline** — builds via `RecorderOrchestrator._build_default_pipeline()` (real
   `RawTickFileWriter` + `SQLiteLiveWriter` + `TickProcessor` + `DepthWebSocketClient`, three real bounded
   `queue.Queue`s, `shutdown_event` + `db_shutdown_event`, a real `InstrumentManager` reconstructed from a
   HEADER `instruments` block via `from_header`). No live broker/WS/market.
2. **Recorded feed** — `RecordedTransport` is a real `FeedTransport` (adapts `FakeTransport`) that plays a
   scripted, self-paced `market_data` sequence through the real feed callbacks → the real tee → both
   queues. The feed shape mirrors production: **NIFTY/NFO 50-level TBT** (`:50` topic, `is_50_depth=1`,
   per-level `orders` populated) and **SENSEX/BFO 5-level**. Three 1-second buckets (a prior second exists
   so rolling ΔQ/OFI are computable).
3. **Real teardown** — the genuine §3.1.4 drain (`_teardown_pipeline`): `shutdown` → `feed.stop()` → join
   `feed → processor` → set `db_shutdown` → join `db → raw`.
4. **Real reprocess subprocess** — `python -m market_depth_recorder --replay --catchup` (via
   `subprocess.run`, stdout/stderr → a log file, reaped) rebuilds the fat DuckDB store from the produced
   raw log; determinism is proven by a second in-process `replay_file` + `replay.verify`.

## Assertions (the whole-pipeline FD audit is assertion-backed)

- **Threads:** no worker `is_alive()` after teardown (clean joins on every path).
- **Tier-0 raw `.jsonl.gz`:** `HEADER` (with the `instruments` block for NIFTY+SENSEX) .. ≥1 data line ..
  `EOF`; `raw_writer.eof_written is True` (the clean-EOF reprocess gate). Depth audit fields survived the
  raw transport — `feed_time`, `depth_levels` (50 for NIFTY, 5 for SENSEX), `is_50_depth`, the `:50`
  suffix, and **per-level `orders > 0`** (the load-bearing finding: the SDK path would strip these).
- **Tier-1 live SQLite:** `spot_states` + `option_strike_metrics` populated; `recorder_meta.built_by="live"`.
- **Tier-2 DuckDB (from the real subprocess):** exists at `replay.canonical_output(...)`;
  `recorder_meta.built_by="replay"`; spot/option rows > 0; a re-replay `verify`s clean (determinism).
- **Health:** `build_health()` carries `cycle_ms_p50`/`cycle_ms_max`/`rss_mb` + queue depths;
  `actual_depth` = `{NIFTY: 50, SENSEX: 5}`; `cycle_ms_max < 15 ms` (sanity on a tiny book, not a hard gate).
- **FD residue:** no `.tmp_*` / `.building_*` / `*.lock` left in the data dir; the subprocess is reaped.

## FD-holding resources covered (open → close, every path)

| Resource | Owner | Closed |
|---|---|---|
| gzip raw handle | `RawTickFileWriter` | `run()` `finally` (flush→fsync→close), EOF on clean drain |
| SQLite conn (+`-wal`/`-shm`) | `SQLiteLiveWriter` | `run()` `finally`; TRUNCATE+optimize on teardown |
| DuckDB conn (+`.wal`/`.building_*`) | `DuckDBAnalyticalWriter` (subprocess) | `with`/`__exit__`; temp→`os.replace` |
| WS socket | `RawWSTransport`/`RecordedTransport` | feed `run()` `finally` + `stop()` |
| reprocess subprocess + log fd | harness / orchestrator | `subprocess.run` reaps; log via `with` |
| 4 worker threads | orchestrator | `_teardown_pipeline` joins (timeout 10 s each) |

`process_rss_mb()` (ctypes/`getrusage`) and the SIGTERM handler add **no** FD.

## Notes

- Clock basis is the **real** wall clock (`time_fn=time.time`) so the processor's 1 s grid actually ticks
  across the run; assertions are on structure/content, not exact timestamps. Determinism of the *rebuild*
  is proven separately (recv_ts-driven replay + `verify`).
- The live-store-vs-DuckDB `--verify-against-live` equivalence is covered by `test_replay.py` (synchronous,
  recv_ts-paced) — not asserted here, since the live thread buckets on the real clock while replay buckets
  on `recv_ts`.
- Live-broker confirmations (bullet 2 of the P8 spec) are **P9** — see `LIVE_RUN.md`.
