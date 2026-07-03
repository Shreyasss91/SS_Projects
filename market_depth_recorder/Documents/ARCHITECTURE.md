# Architecture — Market Depth Recorder

Living architecture doc. Tracks **what is actually built**, not the aspiration. Cites the design spec
`market_depth_recorder_design.md` (§) as the authority.

## What this service is

A standalone, config-driven microservice that captures real-time option market depth for the
configured weekly chains (initially NIFTY + SENSEX) off OpenAlgo and persists it through a
**three-tier pipeline** (§2.1):

- **Tier 0 — raw `.jsonl.gz`** (lossless source of truth; every packet, exchange-timestamped).
- **Tier 1 — thin live SQLite/WAL** (`recorder.live_metrics` subset, written during market hours).
- **Tier 2 — fat DuckDB analytics** (full §4 catalog, rebuilt offline by replaying Tier 0).

Both derived stores are reconstructable from Tier 0 (§2.1), so neither is a single point of loss.

## Package layout (§2.1)

The folder **is** the Python package; run it from the parent `SS_Projects/` with
`python -m market_depth_recorder …`.

```
market_depth_recorder/
├── __init__.py            # package marker; __version__, SCHEMA_VERSION=1  [P0 ✅]
├── __main__.py            # CLI surface (§8.2); --validate-config wired, rest stubbed  [P0 ✅]
├── config.py              # loader + full §7.3 validation, config_hash, frozen Config  [P0 ✅]
├── utils.py               # logging, IST/time, decay weights, atomic write, disk free  [P0 ✅]
├── config.yaml            # §7.1 template, materialized verbatim  [P0 ✅]
├── requirements.txt       # standalone pins (openalgo exact; rest ~=)  [P0 ✅]
├── metrics/
│   ├── __init__.py        # metric layer marker  [P0 ✅]
│   └── registry.py        # declarative M1–M29 + rolling + aggregate/regime metadata (§3.4.0)  [P0 ✅]
├── instrument_manager.py  # REST instruments/expiry, weekly-expiry, strike-step, O(1) maps (§3.2)  [P1 ✅]
├── file_writer.py         # Tier-0 gzip JSONL writer thread (§3.5)  [P2 ✅]
├── websocket_client.py    # raw-WS transport (primary), DSM, tee, reconnect, depth preflight (§3.3)  [P3 ✅]
├── processor.py           # 1s resampler + NumPy metric engine, thin/fat modes (§3.4)  [P4]
├── database_writer.py     # SQLiteLiveWriter (Tier 1) + DuckDBAnalyticalWriter (Tier 2) (§3.6)  [P5/P7]
├── main.py                # orchestrator daemon, milestones, supervisor, teardown (§3.1)  [P6]
├── replay.py              # offline raw → DuckDB rebuild, --catchup/--verify (§8)  [P7]
├── Documents/             # this living doc set
├── tests/                 # pytest suites — no live feed needed
└── data/                  # runtime artifacts (gitignored)
```

Modules past P0 are listed for the roadmap but not yet created.

## Threading & queue topology (§5.1) — feed receiver + tee now built (P3)

**4 threads / 3 bounded queues.** The feed receiver **tees** each packet with two independent `put`s.

```
 FEED thread — RawWSTransport.run_forever receive loop + DSM + reconnect   [P3 ✅]
        │ tee (no lock, returns immediately)
        ├── put(timeout) ─► raw_file_queue ─► RawTickFileWriter ─► .jsonl.gz   (Tier 0, audit, protected)  [P2 ✅]
        └── put_nowait ───► proc_queue ─────► TickProcessor (1s) ─► db_queue ─► SQLiteLiveWriter ─► .db (Tier 1)  [P4/P5]
```

`RawTickFileWriter` (P2) drains `raw_file_queue` and owns the Tier-0 gzip handle exclusively. The
**FEED thread** (P3) is the producer: `DepthWebSocketClient` runs the transport receive loop, drives
the DSM (boundary math + strike selection), and tees each normalized packet to both queues. The
`proc_queue → TickProcessor → db_queue → SQLiteLiveWriter` analytics stages land P4/P5; until then the
client is exercised by its tests (injected fake transport + queues + clock + `sleep_fn`), and the two
queues are supplied by the orchestrator (P6).

**Locks (P3, §3.3.3):** `_spot_lock` (spot cache + 10-tick median deque + boundaries), `_sub_lock`
(RLock, the never-shrink `_subscriptions` map), `_client_lock` (serializes sends into the transport).
Lock order `_spot_lock → _sub_lock` (never held together — subscription I/O happens after the spot
lock is released); `connect`/`disconnect` are FEED-thread-only and not under `_client_lock`; the tee
takes no lock; no I/O under any lock.

Backpressure shed order under overload: `proc_queue` (analytics) first → `db_queue` → `raw_file_queue`
last; a raw drop happens **only** on genuine disk saturation and is counted + logged ERROR (§1.4/§5.1).
On the write side, `RawTickFileWriter` treats a serialization/disk-write failure as that single
sanctioned boundary — counted (`write_error_count`) + logged ERROR, thread survives.

## Transport (locked decision, §3.3.1)

Default transport is **raw WebSocket** (primary), built in P3 as `RawWSTransport` on `websocket-client`
(`run_forever(ping_interval, ping_timeout)` for native heartbeat). The OpenAlgo SDK depth callback
strips `feed_time`/`depth_levels`/`is_50_depth`/`total_*_qty` (SDK `feed.py:456-467`) that the proxy
sends on the wire (`server.py:1821-1827`), so only raw preserves the recorder's self-describing,
exchange-timestamped audit. The transports sit behind a `FeedTransport` seam selected by
`websocket.transport`; **`SdkTransport` is a deferred stub** (P3, plan decision 20) that fails fast with
a clear message if selected — it will be built against the same seam later (with `auto_reconnect=False`,
the recorder owns reconnect/resubscribe).

## Cross-cutting features layered on the spec (all additive)

- **Metric registry** (`metrics/registry.py`, §3.4.0) — declarative; `live_metrics` validated against it.
- **Provenance + versioning** — `SCHEMA_VERSION` + `config_hash` in the raw HEADER line (§3.5.4) and both
  stores' `recorder_meta` (§4.1b). `config_hash` implemented in P0; the **raw HEADER/EOF stamp lands in
  P2** (`file_writer.py`); the stores' `recorder_meta` stamps land with the DB writers (P5/P7).
- **Operational CLI** — `--validate-config` (P0), `--preflight` (P3, offline chain resolution **plus**
  the live raw-WS depth probe; unreachable WS degrades gracefully to exit 0), `--status` (P6).
- **Session guards** — disk-space check + optional trading-holiday skip (§3.1.5); config keys validated in P0.

## Invariants (guard every phase)

- **Lossless raw** — Tier 0 is 100% of the feed; only permitted loss is disk saturation (counted + ERROR).
- **Genericization** — no index/exchange/strike-step literal in engine code; state keyed by `name`.
- **Uniform 1s grid** — never varied at runtime (degraded mode skips work, keeps cadence).
- **Never-shrink subscriptions** — until graceful 15:35 shutdown.
- **FD hygiene** — shared singletons, `with`/close on every path; subprocess logs to file, `wait()`-reaped.

## Built state (P0)

Scaffolding, config (loader + full §7.3 validation, fast-fail exit 1, `config_hash`), utils, the
declarative metric-registry skeleton (M1–M29 + rolling + aggregates + regime, **metadata only**), the
CLI surface (`--validate-config` wired end-to-end, rest stubbed with clean exits), standalone
`requirements.txt`, and this doc set. No live feed, no threads, no I/O pipeline yet — those start at P1.

## Built state (P1)

`instrument_manager.py` — the first live module (REST, still no threads/DB/sockets). `RestClient`
(stdlib `urllib`; instruments GET + expiry POST; 10 s timeout, ≤3 retries on network/5xx, 4xx
terminal) and `InstrumentManager` (weekly-expiry via the authoritative expiry endpoint, per-underlying
instrument filter with `name`/longest-prefix disambiguation, mode-based strike-step detection with a
warned config fallback, and the O(1) `strike_to_symbol_map` / `symbol_to_strike_map` /
`active_strikes_list` / `tick_size_map`). `--preflight` is wired to resolve every chain offline and
report the planned near-ATM probe strike per underlying (`actual_depth` pending the P3 raw-WS probe).
The only FD is a transient HTTP connection, closed on every path. See `instrument_manager.md`.

## Built state (P2)

`file_writer.py` — `RawTickFileWriter(threading.Thread)`, the first background writer and the first
thread in the pipeline. Drains `raw_file_queue`, serializes each packet to a JSONL line, and appends it
to the daily gzip log with a self-describing HEADER (open) + EOF (clean drain) provenance line stamping
`SCHEMA_VERSION`/`config_hash`/underlyings (§3.5.4). Two-tier flush (cheap `flush()` at
`flush_max_records`; bounded `os.fsync()` every `fsync_interval_sec`, §3.5.3). Single-owner gzip handle
(no lock), closed on every path via a guarded `finally`. Lossless-raw boundary: a serialization/disk
write failure is counted + ERROR-logged and the thread survives (§1.4). A defensive IST-based daily
rollover guard exists but never fires in a normal session. Still no sockets/DB/subprocess; the queue,
tee, and clock are injected by tests. See `file_writer.md`.

## Built state (P3)

`websocket_client.py` — `DepthWebSocketClient(threading.Thread)`, the first **networked** module and the
tick producer. Owns: (1) the **transport seam** — `RawWSTransport` on `websocket-client` (default,
native ping heartbeat) behind a `FeedTransport` protocol, with a deferred `SdkTransport` stub; (2) the
**DSM** (§3.3.2) — spot LTP validation (drop ≤0 and >2%-vs-10-tick-median spikes), lazy boundary
seeding, breach expansion, and strike selection via the P1 `strike_to_symbol_map`; (3) the **tee**
(§5.1) — `proc_queue.put_nowait` (sheds first, WARNING+count) then
`raw_file_queue.put(timeout)` (sheds last, ERROR+`raw_dropped_total`, the single sanctioned raw-loss
boundary); (4) the recorder-owned **reconnect** state machine (§6.1) — exponential backoff + resubscribe
every symbol in the **never-shrink** `active_subscriptions`; (5) the live **depth preflight**
(§3.2.5/§9) — `run_depth_preflight()` subscribes one `:50` depth per underlying's near-ATM probe strike,
reads actual `depth_levels`/`is_50_depth`/per-level `orders`, logs the consolidated line + a WARNING on
`actual < requested`. The only FD is the WS socket, closed on every path (drop, reconnect, shutdown,
preflight probe); close-before-reconnect holds. `--preflight` re-pointed from P1's offline-only resolve
to include this live probe (graceful-degrade to exit 0 when the WS is unreachable, plan decision 30).
Tests inject a fake transport + queues + clock + `sleep_fn` — no live feed. See `websocket_client.md`.
