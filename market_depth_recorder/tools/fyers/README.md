# `tools/fyers/` — FYERS streaming diagnostics

Broker-specific diagnostics for the FYERS feed the recorder consumes through OpenAlgo.

**Scope note:** unlike the rest of the recorder (which is broker-agnostic and talks to
OpenAlgo only over HTTP/WS), these tools **import OpenAlgo platform code** to drive the
FYERS streaming client directly. That is a deliberate, documented diagnostics scope
exception — the tools are **read-only w.r.t. platform code** (they drive the client,
never edit it), in the same spirit as `Documents/patches/OPENALGO_PATCH.md`. Run them
from OpenAlgo's environment (`uv run …` from the openalgo repo root) so the platform
deps and the token store are available.

| Tool | Purpose |
| --- | --- |
| `tbt_channel_probe.py` | Determine whether FYERS TBT (50-level depth) can stream on channels other than 1 — i.e. whether the 5-symbol ceiling is an upstream FYERS limit or a client-side channel-protocol bug. Drives `FyersTbtWebSocket` directly with full control over channel value + type, and records subscribe requests, FYERS ACKs/errors, and per-symbol packet counts. |
| `tbt_multiconn_probe.py` | Measure the effective concurrent 50-level budget across FYERS' 3 allowed connections. Opens N independent `FyersTbtWebSocket` connections, each a distinct 5-symbol group, observed concurrently; records per-connection + per-symbol connect / first-snapshot / first-incremental timing, sustained packet counts, drops, and ACKs/errors. |
| `_tbt_common.py` | Shared internals for both probes (token load, instrumented client subclass, subscribe/resume frame helpers, thread-safe `Recorder`). Imported, not run. |

## `tbt_channel_probe.py`

Runs a configurable test matrix, each on a fresh connection:

| Test | Setup | Question |
| --- | --- | --- |
| `T1` | 5 syms, channel `"1"` | baseline — must stream |
| `T2` | 5 syms, channel `"2"` (string) | can a non-1 channel stream on its own? |
| `T2p` | 5 syms, channel `2` (int) | is it a string-vs-int channel-type bug? |
| `T3` | 5 on ch1 **+** 5 on ch2 (strings) | are two channels concurrently independent? |

**Read T2 vs T3.** If a non-1 channel streams alone (T2) but is rejected the moment a
second channel is added (T3 → *"symbol count exceeds limit: 5"*), the 5-symbol cap is
**global per connection**, not per channel — channel spreading cannot raise it.

### Usage

```bash
# From the openalgo repo root, with OpenAlgo's own feed STOPPED (avoid a concurrent
# FYERS session / 429 confound — the token is read from the persisted DB, so token
# auto-load still works while OpenAlgo is down). Run during market hours.
uv run python market_depth_recorder/tools/fyers/tbt_channel_probe.py --out /tmp/tbt_probe.json

# One arm only, custom timing / current-expiry tickers:
uv run python market_depth_recorder/tools/fyers/tbt_channel_probe.py \
    --tests T3 \
    --group-a "NSE:NIFTY...CE,NSE:NIFTY...PE,..." \
    --group-b "NSE:NIFTY...CE,NSE:NIFTY...PE,..." \
    --observe-secs 45 --sub-resume-delay 0.3
```

Configurable via CLI: `--group-a/--group-b` (FYERS tickers), `--channel-a/--channel-b`,
`--observe-secs`, `--sub-resume-delay`, `--inter-test-delay`, `--resume-first`,
`--tests`, `--token`/`--user-id`, `--out`. See `--help` for defaults.

**Cautions**
- The default tickers are a specific weekly expiry — pass `--group-a/--group-b` with
  **current-expiry** tickers on any other day, or `T1` will stream 0 (the tool flags
  that rather than misreporting).
- Opens a **real FYERS TBT session**. Stop OpenAlgo's feed first; relaunch it after.
- Exit codes: `0` ran (see report), `2` setup/usage error.

## `tbt_multiconn_probe.py`

Answers the follow-on question the channel probe left open: given 5 symbols/connection, do FYERS'
**3 allowed connections combine to 15** concurrent 50-level symbols? Opens N genuinely independent
connections, each subscribing a **distinct** 5-symbol group on channel `"1"`, observed concurrently.

| Phase | Setup | Question |
| --- | --- | --- |
| `C1` | 1 conn, 5 syms | baseline — must stream 5/5 |
| `C3` | 3 concurrent conns, 5 distinct syms each | do 15 distinct legs stream at once? |
| `C4` | attempt a 4th conn while 3 are up | is the documented 3-connection cap enforced? |

**Result (2026-07-14, evidence `Documents/patches/tbt_multiconn_20260714.json`):** C1 5/5, **C3
15/15 distinct concurrent** (each conn 5/5, sustained increments, 0 drops), C4 4th **refused**
(`429`). ⇒ **`tbt_budget = 15`**. Full reconciliation (incl. the Jul-07/Jul-14 raw re-read):
`Documents/patches/tbt_concurrency_reconciliation_20260714.md`.

### Usage

```bash
# From the openalgo repo root, OpenAlgo's own feed STOPPED (its adapter holds a TBT connection;
# with the 3-conn cap that would confound C3/C4). Run during market hours, current-expiry tickers.
uv run python market_depth_recorder/tools/fyers/tbt_multiconn_probe.py \
    --observe-secs 60 --out /tmp/tbt_multiconn.json
```

Configurable via CLI: `--groups` (';'-separated groups of ','-separated tickers), `--connections/-n`,
`--observe-secs`, `--baseline-secs`, `--c4-secs`, `--connect-stagger`, `--sub-resume-delay`,
`--inter-phase-delay`, `--phases`, `--token`/`--user-id`, `--out`.

**Cautions**
- Same current-expiry ticker caveat as the channel probe — pass `--groups` on any other day (needs
  ≥ N × 5 distinct legs); C1 flags a stale-ticker 0-stream rather than misreporting.
- Opens **real FYERS TBT sessions**; stop OpenAlgo's feed first, relaunch after. A refused connection
  fires a single clean handshake (reconnect disabled up-front) — do **not** re-enable reconnect here,
  or a handshake failure storms FYERS and self-inflicts a Cloudflare `429` (see the reconnect issue
  note in `Documents/patches/openalgo_tbt_reconnect_storm_issue.md`).
- Exit codes: `0` ran (see report), `2` setup/usage error.

## Related
- `Documents/patches/tbt_concurrency_reconciliation_20260714.md` — **canonical** protocol reconciliation.
- `Documents/patches/OPENALGO_PATCH.md` §8 — the channel-spread patch + the authoritative correction.
- `Documents/patches/Phase9_notes.md` §3 — the original (superseded) 5-per-channel finding.
- `Documents/patches/openalgo_tbt_reconnect_storm_issue.md` — the `_run_websocket` retry-on-return issue.
