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

## Related
- `Documents/patches/OPENALGO_PATCH.md` — the channel-spread patch this probes.
- `Documents/patches/Phase9_notes.md` §3 — the original 5-per-channel finding.
