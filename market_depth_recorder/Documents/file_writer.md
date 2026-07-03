# `file_writer.py` — Tier-0 gzip audit writer (§3.5)

## Responsibility

Records the raw incoming WebSocket tick stream into a compressed JSON Lines file
(`market_depth_raw_YYYYMMDD.jsonl.gz`) — the **lossless source of truth** (§1.4) from which both
derived stores are reconstructable by replay (§8). Isolating file I/O to this one background thread
shields the network receiver from disk-write latency. It is a pure queue consumer — **no sockets, DB,
or subprocess**.

## Public API

### `RawTickFileWriter(config, raw_file_queue, shutdown_event, session_date, *, schema_version=SCHEMA_VERSION, time_fn=time.time, error_queue=None, name="RawFileWriter")`
`threading.Thread` subclass (daemon). Constructor reads from `config`: `recorder.output_dir`,
`file_writer.{gzip_compresslevel, flush_max_records, fsync_interval_sec}`, `config_hash`, and the
underlying **names** (for the HEADER). `raw_file_queue` + `shutdown_event` are owned by the P6
orchestrator and injected. `session_date` (a `datetime.date`, from `now_ist().date()`) resolves the
filename once. `time_fn` is the injected clock — the single source of epoch timestamps, the fsync
cadence, and the rollover date — so every time branch is deterministic under test.

- `run()` — open file (+HEADER) → drain `raw_file_queue` until `shutdown_event` is set **and** the
  queue is empty → write EOF on clean drain → flush+fsync+close on **every** path.
- `RawTickFileWriter.resolve_filename(output_dir, d) -> str` — staticmethod; the daily raw-log path.
  Reused by replay/orchestrator.
- Counters (read by P6 health / tests): `records_written` (cumulative data packets),
  `write_error_count` (sanctioned raw-loss count), `_filename` (active file).

## File format (self-describing — §3.5.4)

- **HEADER** (first line): `{"meta_type":"HEADER","session_date":…,"schema_version":…,
  "config_hash":"sha256:…","underlyings":[…],"open_timestamp":…}` — flushed to the OS immediately so a
  reader always sees a described file. Ties every log to the exact formula/config that produced it
  (matches both stores' `recorder_meta`, §4.1b). Append mode means a same-day restart writes a *second*
  HEADER, recording the restart rather than truncating prior audit data.
- **Data lines**: each WS packet, compact `json.dumps(separators=(",",":")) + "\n"`.
- **EOF** (last line, clean shutdown only): `{"meta_type":"EOF","record_count":<data packets>,
  "close_timestamp":…}`. A crash skips EOF → a reader/replay treats the file as incomplete (the intended
  signal); prior lines up to the last durable flush remain readable.

## Two-tier flush (§3.5.3)

`fsync` is the expensive syscall; at multi-kHz rates a per-tick fsync would re-introduce the disk
stalls this thread exists to avoid. So:
- **Cheap `flush()`** (buffer → OS page cache) when `unflushed_count >= flush_max_records` (default 500).
- **Durable `os.fsync()`** on a bounded time cadence only, every `fsync_interval_sec` (default 2.0 s).

Crash-window tradeoff: at most `fsync_interval_sec` of the newest raw ticks can be lost to a hard power
failure — an explicit, bounded exception, acceptable because both derived stores rebuild from raw (§8).

## Daily rollover (§3.5.4, defensive)

The filename is resolved once from `session_date`; there is **no** midnight branch in a normal
~09:00→15:35 session. As a safety net, each write compares the current **IST** date
(`datetime.fromtimestamp(time_fn(), tz=IST)`, matching `session_date`'s basis so it never fires
spuriously on a non-IST host) against the open file's date; on a change it writes EOF, closes, and
reopens the new-dated file with a fresh HEADER.

## Threads / locks / FDs owned

- **Thread:** one — `run()`. **Lock:** none — the gzip handle is single-owner (only this thread ever
  touches it), which is stronger than a lock. **FD:** exactly one gzip handle, closed on every path
  (clean drain, exception, rollover, shutdown) via a guarded, idempotent `_close_file` in a `finally`.
- **Lossless-raw boundary (§1.4):** the one sanctioned drop is a serialization or disk-**write** failure
  — caught, `write_error_count`++, logged at ERROR, thread continues. Backpressure drops happen upstream
  at the tee (P3), never here. A fatal `run` crash is `logger.exception`-logged (and reported to
  `error_queue` when P6 wires one); the handle is still closed.

## Config keys consumed

`recorder.output_dir` · `file_writer.gzip_compresslevel` · `file_writer.flush_max_records` ·
`file_writer.fsync_interval_sec` · (`config.config_hash`, underlying names, `SCHEMA_VERSION` → HEADER).

## Tests (`tests/test_file_writer.py`, offline)

Round-trip (HEADER/data/EOF, exact packet equality, `record_count`); provenance stamping; cheap-flush
cadence; bounded fsync cadence (spied `os.fsync` + controllable clock); missing-EOF + byte-truncated
tail tolerance (clean prefix recovery); defensive IST rollover; write-error accounting (thread
survives); graceful drain through the real thread; optional `pandas.read_json` compatibility.
