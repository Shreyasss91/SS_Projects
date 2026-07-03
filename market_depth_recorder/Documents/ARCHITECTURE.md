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
├── instrument_manager.py  # REST instruments/expiry, strike-step detect, depth preflight (§3.2)  [P1]
├── file_writer.py         # Tier-0 gzip JSONL writer thread (§3.5)  [P2]
├── websocket_client.py    # raw-WS (primary) + SDK feed wrapper, DSM, reconnect (§3.3)  [P3]
├── processor.py           # 1s resampler + NumPy metric engine, thin/fat modes (§3.4)  [P4]
├── database_writer.py     # SQLiteLiveWriter (Tier 1) + DuckDBAnalyticalWriter (Tier 2) (§3.6)  [P5/P7]
├── main.py                # orchestrator daemon, milestones, supervisor, teardown (§3.1)  [P6]
├── replay.py              # offline raw → DuckDB rebuild, --catchup/--verify (§8)  [P7]
├── Documents/             # this living doc set
├── tests/                 # pytest suites — no live feed needed
└── data/                  # runtime artifacts (gitignored)
```

Modules past P0 are listed for the roadmap but not yet created.

## Threading & queue topology (§5.1) — *target*, not yet built (P3–P6)

**4 threads / 3 bounded queues.** The feed receiver **tees** each packet with two independent `put`s.

```
 WebSocket receiver (raw thread / SDK callback)
        │ tee
        ├── put(timeout) ─► raw_file_queue ─► RawTickFileWriter ─► .jsonl.gz   (Tier 0, audit, protected)
        └── put_nowait ───► proc_queue ─────► TickProcessor (1s) ─► db_queue ─► SQLiteLiveWriter ─► .db (Tier 1)
```

Backpressure shed order under overload: `proc_queue` (analytics) first → `db_queue` → `raw_file_queue`
last; a raw drop happens **only** on genuine disk saturation and is counted + logged ERROR (§1.4/§5.1).

## Transport (locked decision, §3.3.1)

Default transport is **raw WebSocket** (primary). The OpenAlgo SDK depth callback strips
`feed_time`/`depth_levels`/`is_50_depth`/`total_*_qty` (SDK `feed.py:456-467`) that the proxy sends on
the wire (`server.py:1821-1827`), so only raw preserves the recorder's self-describing,
exchange-timestamped audit. SDK remains selectable (`websocket.transport: sdk`) for LTP/degraded use.
SDK client is constructed with `auto_reconnect=False` — the recorder owns reconnect/resubscribe.

## Cross-cutting features layered on the spec (all additive)

- **Metric registry** (`metrics/registry.py`, §3.4.0) — declarative; `live_metrics` validated against it.
- **Provenance + versioning** — `SCHEMA_VERSION` + `config_hash` in the raw HEADER line (§3.5.4) and both
  stores' `recorder_meta` (§4.1b). `config_hash` is implemented in P0; the stamps land with the writers.
- **Operational CLI** — `--validate-config` (P0), `--preflight` (P1), `--status` (P6).
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
