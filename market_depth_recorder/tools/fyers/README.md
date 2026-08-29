# `tools/fyers/` — FYERS streaming diagnostics

Broker-specific diagnostics for the FYERS feed the recorder consumes through OpenAlgo.

**Scope note:** unlike the rest of the recorder (which is broker-agnostic and talks to
OpenAlgo only over HTTP/WS), the two TBT probes **import OpenAlgo platform code** to drive the
FYERS streaming client directly. (`depth_transition_probe.py` is the exception — it speaks the
proxy's own WebSocket protocol and imports nothing from the platform, because the path it measures
is the path the Broker Adapter will sit on.) That is a deliberate, documented diagnostics scope
exception — the tools are **read-only w.r.t. platform code** (they drive the client,
never edit it), in the same spirit as `Documents/evidence/openalgo_platform/OPENALGO_PATCH.md`. Run them
from OpenAlgo's environment (`uv run …` from the openalgo repo root) so the platform
deps and the token store are available.

| Tool | Purpose |
| --- | --- |
| `tbt_channel_probe.py` | Determine whether FYERS TBT (50-level depth) can stream on channels other than 1 — i.e. whether the 5-symbol ceiling is an upstream FYERS limit or a client-side channel-protocol bug. Drives `FyersTbtWebSocket` directly with full control over channel value + type, and records subscribe requests, FYERS ACKs/errors, and per-symbol packet counts. |
| `tbt_multiconn_probe.py` | Measure the effective concurrent 50-level budget across FYERS' 3 allowed connections. Opens N independent `FyersTbtWebSocket` connections, each a distinct 5-symbol group, observed concurrently; records per-connection + per-symbol connect / first-snapshot / first-incremental timing, sustained packet counts, drops, and ACKs/errors. |
| `depth_transition_probe.py` | Measure what a 5 <-> 50 depth change actually does on the OpenAlgo proxy path — the F7 gate on the Broker Adapter (Plan_002 §20.1). Drives `ws://host:8765` with the recorder's own `subscribe`/`unsubscribe` frames, running the four transitions in both symbol spellings (`SYMBOL` vs `SYMBOL:50`) and both mechanisms (bare re-subscribe vs unsubscribe-then-subscribe). Dry-run by default. |
| `_depth_probe_model.py` | Broker-neutral model behind the depth probe (operations, symbol forms, the OBSERVED/INFERRED/UNKNOWN lattice, transition classification, evidence serialisation). Pure — no network, no broker import, fully unit-tested offline. Imported, not run. |
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

**Result (2026-07-14, evidence `Documents/evidence/fyers_tbt_concurrency_20260714/tbt_multiconn_20260714.json`):** C1 5/5, **C3
15/15 distinct concurrent** (each conn 5/5, sustained increments, 0 drops), C4 4th **refused**
(`429`). ⇒ **`tbt_budget = 15`**. Full reconciliation (incl. the Jul-07/Jul-14 raw re-read):
`Documents/evidence/fyers_tbt_concurrency_20260714/tbt_concurrency_reconciliation_20260714.md`.

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
  note in `Documents/evidence/openalgo_platform/openalgo_tbt_reconnect_storm_issue.md`).
- Exit codes: `0` ran (see report), `2` setup/usage error.

## `depth_transition_probe.py`

Answers the question Plan_002 §20.1 forbids guessing: **when the framework retiers a leg between the
standard (5) and premium (50) depth tiers, what actually happens on the wire?** Nothing in the
codebase establishes whether that changes an existing subscription, creates a second one, costs an
extra premium slot, or drops ticks in between — and every phase above F7 would inherit the guess.

Unlike the TBT probes above, this one deliberately does **not** bypass OpenAlgo. The Broker Adapter
will sit on the proxy path, so the proxy path is what must be measured.

### The two spellings

The recorder encodes depth twice — a `:50` symbol suffix **and** a `depth` field — while the proxy
keys a subscription by `(symbol, exchange, mode)`, which excludes depth. So "move this leg to 50"
has two candidate spellings that may not be the same operation at all:

| | Wire symbol | `depth` | Proxy subscription key |
| --- | --- | --- | --- |
| **CASE A** logical | `SYMBOL` | 50 | same key as the depth-5 subscription |
| **CASE B** recorder-style | `SYMBOL:50` | 50 | a *different* key |

Both are probed. CASE A is not expressible by the recorder today, but if it works it is the cheaper
transition and the adapter should prefer it.

### Cases

| Case | Transition | Spelling | Mechanism |
| --- | --- | --- | --- |
| `C1_5_5_logical` | 5 -> 5 | logical | bare re-subscribe (idempotence control) |
| `C2_5_50_logical` | 5 -> 50 | logical | bare re-subscribe (CASE A) |
| `C3_5_50_suffixed` | 5 -> 50 | `:50` | bare re-subscribe (CASE B) |
| `C4_50_50_logical` | 50 -> 50 | logical | bare re-subscribe (does a repeat cost a slot?) |
| `C5_50_5_logical` | 50 -> 5 | logical | bare re-subscribe (does demotion free a slot?) |
| `C6_5_50_logical_unsub` | 5 -> 50 | logical | unsubscribe, then subscribe |
| `C7_50_5_logical_unsub` | 50 -> 5 | logical | unsubscribe, then subscribe |

### Three depths, never conflated

**Requested** (what we asked for) / **reported** (what the acknowledgement said) / **observed**
(levels counted in delivered market-data packets). Only the third is evidence of delivered depth —
the proxy echoes the requested depth back when the adapter reports nothing
(`websocket_proxy/server.py:1254`), so a reply of `depth: 50` may mean nothing at all.

Every result carries a confidence: **OBSERVED** (counted in packets), **INFERRED** (acknowledgement
only), or **UNKNOWN**. A transition is classified `depth_changed` only when *both* sides were
observed; anything less is `unknown`, never "no". This is enforced in the model, not by discipline,
and is covered by `tests/test_f7_depth_probe_harness.py`.

### Usage

```bash
# From SS_Projects/market_depth_recorder. Dry-run first — sends nothing, touches no network.
python tools/fyers/depth_transition_probe.py     --symbols NIFTY<EXPIRY><STRIKE>CE --out /tmp/probe_dryrun.json

# Live, in session, current-expiry NFO leg. The key comes from the environment, never the
# command line (it would land in shell history).
export OPENALGO_API_KEY="…"
python tools/fyers/depth_transition_probe.py --live     --symbols NIFTY<EXPIRY><STRIKE>CE     --out Documents/evidence/depth_transition_<YYYYMMDD>/depth_transition_probe_<YYYYMMDD>.json
```

Configurable via CLI: `--symbols`, `--exchange`, `--mode`, `--url`, `--cases`, `--observe-secs`,
`--settle-secs`, `--out`, `--no-cleanup`, `--allow-outside-session`. See `--help` for defaults.

**Cautions**
- **NFO only.** 50-level TBT is NSE/NFO-restricted; a SENSEX/BFO leg cannot answer this question.
- **Do not run before market data is available.** Outside 09:15-15:30 IST no depth packets flow, so
  every case returns UNKNOWN. `--live` refuses outside the session unless `--allow-outside-session`
  is passed explicitly.
- Maximum **2** instruments, enforced in code. Do not raise it, and do not probe the broker's
  capacity ceiling by exceeding it.
- Stop the recorder first — it holds premium slots, and contention reads as a capacity failure.
- Pass a **current-expiry** symbol; do not reuse one from an older document.
- Exit codes: `0` ran (see report), `2` setup/usage error.

Operator procedure: `Documents/evidence/depth_transition_20260826/depth_transition_probe_runbook_20260826.md`.
Evidence document: `Documents/evidence/depth_transition_20260826/depth_transition_probe_20260826.md`.

## Related
- `Documents/evidence/fyers_tbt_concurrency_20260714/tbt_concurrency_reconciliation_20260714.md` — **canonical** protocol reconciliation.
- `Documents/evidence/openalgo_platform/OPENALGO_PATCH.md` §8 — the channel-spread patch + the authoritative correction.
- `plans/Plan_001_evidence/Phase9_notes.md` §3 — the original (superseded) 5-per-channel finding.
- `Documents/evidence/openalgo_platform/openalgo_tbt_reconnect_storm_issue.md` — the `_run_websocket` retry-on-return issue.
- `Documents/evidence/depth_transition_20260826/depth_transition_probe_20260826.md` — the F7 depth-transition evidence document
  (template prepared; **live results pending**).
- `Documents/evidence/depth_transition_20260826/depth_transition_probe_runbook_20260826.md` — operator procedure for the live run.
