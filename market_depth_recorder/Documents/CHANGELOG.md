# Changelog — Market Depth Recorder

Dated running log; one entry per phase/iteration (what changed, why, affected files, deferred work).

## 2026-07-03 — P3: WebSocket client + DSM (`websocket_client.py`)

**What / why.** The first **networked** module and the tick producer: a `DepthWebSocketClient` FEED
thread that owns the feed transport, the Dynamic Strike Manager (DSM), the tee into
`raw_file_queue`/`proc_queue`, the recorder-owned reconnect state machine, and the live
depth-capability preflight (§3.3/§6.1/§3.2.5/§9). It closes the loop from "resolved chains" (P1) to
"packets flowing into the audit + analytics queues" (P2 writer downstream).

**Decisions (recorded in the plan doc, decisions 20–30).**
- **Transport seam (20)** — `FeedTransport` protocol; `RawWSTransport` built (default), `SdkTransport`
  a deferred fail-fast stub. The SDK depth callback strips the audit fields, so raw stays default.
- **Canonical packet = wire message, lightly normalized (21)** — `symbol` kept **as received** (keeps
  `:50` on depth topics, §3.3.3); the same dict is teed to both queues; DB-symbol stripping is downstream.
- **Native heartbeat (22)** — `run_forever(ping_interval, ping_timeout)`, no hand-rolled monitor thread.
- **One FEED thread + three locks (23/24)** — `_spot_lock → _sub_lock` order, `_client_lock` independent;
  `connect/disconnect` off `_client_lock`; no I/O under any lock; the tee is lock-free.
- **Lazy DSM seeding (25)** — boundaries seed from the first valid spot tick; P6's REST one-shot feeds the
  same `on_spot` entry, so P3 needs no REST/quotes.
- **Never-shrink (26)** — subscriptions only grow intra-session; `active_subscriptions` holds wire symbols.
- **Tee backpressure (28)** — proc sheds first (WARNING+count), raw sheds last (ERROR+count, the single
  sanctioned raw-loss boundary).
- **`--preflight` graceful-degrade (30)** — offline resolve is a prerequisite (exit 1 on REST failure);
  the live depth probe is best-effort (unreachable WS → `actual_depth=<unreachable>`, exit 0).

**Added files.**
- `websocket_client.py` — `FeedTransport`/`RawWSTransport`/`SdkTransport(stub)`/`make_transport`;
  `DepthWebSocketClient(threading.Thread)` (tee, DSM `_on_spot`/`_check_boundaries`, subscription flow +
  never-shrink, reconnect loop with injected `sleep_fn`, `on_open` auth+resubscribe); module helpers
  `wire_symbol`/`normalize_market_data`; `run_depth_preflight` + `DepthProbeResult` (§3.2.5/§9). One FD
  (WS socket), closed on every path; close-before-reconnect.
- `tests/test_websocket_client.py` (19 tests) — tee both-queues + shed order + raw-drop accounting;
  spot routing; DSM seed/upper-breach/lower-breach (gradual ramps within the 2% spike guard)/spike +
  non-positive rejection; never-shrink on pullback; reconnect auth+spot+resubscribe; disconnected-
  subscribe flushed on reconnect; deterministic backoff sequence; wire-symbol + normalize helpers;
  live preflight reads `depth_levels`/`is_50_depth`/`orders` + WARNs on `actual<requested`; unreachable
  probe degrades fast. All offline (fake transport + injected clock/sleep).
- `Documents/websocket_client.md` (new per-module doc).

**Changed files.**
- `__main__.py` — `_cmd_preflight` re-pointed from P1's offline `<pending>` to the live probe
  (graceful-degrade to `<unreachable>` + exit 0).
- `tests/test_instrument_manager.py` — the two `--preflight` tests updated for the live-probe output
  (`actual_depth=50` / `<unreachable`); added a WS-unreachable-exit-0 CLI test.
- `Documents/ARCHITECTURE.md` (P3 built state; topology now shows the FEED thread + tee + locks;
  transport + CLI notes updated), `Documents/instrument_manager.md` (`--preflight` now live).
- Live plan doc P3 section expanded with decisions 20–30 + subtask checklist.

**Deferred.** `SdkTransport` body (post-P3, additive against the seam); `--status`/orchestration/
teardown/REST-quote mid-day seeding (P6); the resampler/metrics that consume `proc_queue` (P4).

**Verification.** `python -m pytest market_depth_recorder/tests/ -q` → **98 passed** (79 prior + 19
new), no live feed. `--validate-config` → exit 0; `--preflight` without a server → exit 1 at REST
resolution (the documented prerequisite). Genericization grep on `websocket_client.py` → only a
doc-comment `NIFTY/SENSEX` mention; `:50`/`5` are cited transport constants (`_TBT_SUFFIX`/
`_TBT_MIN_DEPTH`). A **real bug the tests caught:** the initial breach tests jumped spot >2% in one
tick and were (correctly) rejected by the DSM's own spike guard — fixed the tests to ramp gradually,
confirming the guard behaves as specified.

## 2026-07-03 — P2: Tier-0 gzip file writer (`file_writer.py`)

**What / why.** The first background writer thread and the first stage of the pipeline: drains
`raw_file_queue` and appends every WS packet to the daily gzip JSON Lines log — the **lossless source
of truth** (§1.4) both derived stores rebuild from. Isolating file I/O to this thread shields the feed
receiver from disk latency (§3.5).

**Decisions (recorded in the plan doc, decisions 15–19).**
- **Single-owner FD, no lock** — the gzip handle is touched only by `run()`; exclusive ownership is
  stronger than a lock.
- **Injected clock (`time_fn`)** — sole source of epoch timestamps, the fsync cadence, and the rollover
  date, so every time branch is deterministic under test.
- **Append mode (`gzip.open("at")`)** — a same-day restart appends a second HEADER (records the restart)
  rather than truncating prior audit data.
- **Write-failure = the one sanctioned raw-loss boundary** — caught, `write_error_count`++, ERROR-logged,
  thread continues (§1.4). Sentinel-error-queue wiring deferred to P6 (optional `error_queue` hook left).
- **Tests round-trip via stdlib `gzip`+`json`** (pandas isn't a pinned dep); one `importorskip("pandas")`
  compat check honors the §3.5.1 tooling claim.

**Added files.**
- `file_writer.py` — `RawTickFileWriter(threading.Thread)`: `resolve_filename` (staticmethod), HEADER at
  open + EOF on clean drain (`SCHEMA_VERSION`/`config_hash`/underlyings stamp, §3.5.4), two-tier flush
  (§3.5.3), defensive IST daily rollover, per-packet write-error accounting; `records_written` /
  `write_error_count` counters for P6 health. One gzip FD, closed on every path via a guarded `finally`.
- `tests/test_file_writer.py` (10 tests) — HEADER/data/EOF round-trip + exact packet equality;
  provenance stamping; cheap-flush cadence; bounded fsync cadence (spied `os.fsync` + controllable
  clock); missing-EOF + byte-truncated-tail tolerance (clean-prefix recovery); defensive rollover;
  write-error accounting (thread survives); graceful drain through the real thread; optional
  `pandas.read_json` compat.
- `Documents/file_writer.md` (new per-module doc).

**Changed files.** `Documents/ARCHITECTURE.md` (P2 built state; threading/queue topology now shows the
raw writer built; provenance bullet notes the HEADER/EOF stamp landed). Live plan doc P2 section
expanded with decisions 15–19 + subtask checklist, boxes ticked.

**Verification.** `python -m pytest market_depth_recorder/tests/ -q` → **79 passed** (69 prior + 10
new), no live feed. Tests run the writer synchronously (`run()` with a pre-set shutdown event) and via
a real started thread (`start()`/`q.join()`/`join()`), reading logs back with stdlib `gzip`+`json`.
The `-o addopts=""` flag is needed only to detach from the openalgo repo's root `pytest` addopts
(`--timeout`), unrelated to this package.

**Robustness fix caught while testing.** The rollover guard originally compared the **machine-local**
date against `session_date` (derived from `now_ist()`); on a non-IST host that mismatch would trigger a
spurious rollover on the first write. Changed to compare in **IST** (`datetime.fromtimestamp(...,
tz=IST)`), matching `session_date`'s basis — the guard now never fires spuriously in a normal session.

**FD audit (P2 surface).** Exactly one gzip handle per open, created in `_open_file` and released by a
guarded, idempotent `_close_file` (`flush` → `fsync` → `close`) inside a `finally`, so it closes on
clean drain, mid-loop exception, rollover, and shutdown alike. `fsync` guards a closed/invalid `fileno`
(`OSError`/`ValueError`). No sockets/DB/subprocess; the single thread is `join()`-reaped by the
orchestrator (P6) and is a daemon as a backstop. Tests leak no handles (fakes hold no real FD). Clean.

**Deferred.** Receiver + tee + the queues themselves → P3; sentinel `error_queue` wiring → P6; the
stores' `recorder_meta` provenance stamps → P5/P7.

## 2026-07-03 — P1: InstrumentManager (`instrument_manager.py`)

**What / why.** First live module: resolve each configured underlying's current weekly option chain
over the OpenAlgo REST API and compile the O(1) lookup structures the DSM (P3) and processor (P4)
consume. Pure resolution — no threads/DB/sockets; the only FD is a transient HTTP connection.

**Decisions (recorded in the plan doc, decisions 10–14).**
- **Live depth probe deferred to P3** (user-confirmed): reading `depth_levels`/`is_50_depth` needs a
  raw-WS subscription (the SDK strips them) and that client is P3. `--preflight` resolves the chain
  offline and reports `actual_depth=<pending P3 raw-WS probe>`.
- **`E_weekly` via `/api/v1/expiry`** (`data[0]`; the service already drops past expiries, sorts, and
  includes the expiry day → rollover gate satisfied). Master used only for the strike grid + tick_size.
- **Underlying match on the `name` column** (exact), longest-prefix `symbol` fallback for blank names
  (NIFTYNXT50 not shadowed by NIFTY).
- **Maps built from master `symbol` rows** (never string-constructed); integral strikes → `int` keys.
- **REST via stdlib `urllib`** (no new dependency).

**Added files.**
- `instrument_manager.py` — `RestClient` (urllib; instruments GET + expiry POST; 10 s timeout, ≤3
  retries on network/5xx, 4xx terminal; injectable opener), `InstrumentManager.resolve()` /
  `preflight_report()`, frozen `ResolvedChain`, and the maps (`strike_to_symbol_map`,
  `symbol_to_strike_map`, `active_strikes_list`, `tick_size_map`). Mode-based strike-step detection
  (§3.2.3) with a warned `strike_step_fallback`.
- `tests/test_instrument_manager.py` — RestClient (success/retry/timeout/5xx/4xx/bad-status/expiry
  body), resolution happy path + contaminant exclusion + blank-name prefix fallback, empty-expiry and
  no-contracts fast-fail, strike-step edge cases (wide-gap mode / single-strike / unexpected→fallback),
  expiry parse, `_option_type`/`_norm_strike`, and `--preflight` exit codes (ok/REST-fail/bad-config).

**Changed files.** `__main__.py` — `--preflight` wired to `_cmd_preflight` (offline resolve + report,
exit 0/1), replacing the P0 stub; imports `setup_logging`. `Documents/ARCHITECTURE.md` (P1 built
state), `Documents/instrument_manager.md` (new per-module doc). Live plan doc P1 boxes ticked.

**Verification.** `python -m pytest market_depth_recorder/tests/ -q` → **69 passed** (48 P0 + 21 new),
no live feed. `--validate-config` still exits 0; `--preflight` with no REST server up exits 1 with a
clean `RestError` (no traceback). All tests run against a scripted fake opener / injected `FakeRest`.
A test caught a real bug: the blank-`name` longest-prefix fallback matched `NIFTYNXT50…` to `NIFTY`
(NIFTYNXT50 isn't a configured underlying) — fixed by requiring the char after the base name to be a
digit (an F&O symbol is `BASE + DDMMMYY…`), so `…NXT50` is rejected.

**FD audit (P1 surface).** Every REST call opens one HTTP connection under `with` (response read then
closed); the `HTTPError` error-body path explicitly `.close()`s the error response before raising or
retrying. No thread/lock/DB/subprocess introduced; `InstrumentManager` holds no long-lived descriptor
after `resolve()`. Clean.

**Deferred.** Live §3.2.5 depth probe + §9 `actual < requested` WARNING → P3; DSM/true-ATM → P3.

## 2026-07-03 — P0: Scaffolding, config, utils, registry skeleton

**What / why.** Stood up the package skeleton so every later phase has a validated config, shared
primitives, and a declarative metric registry to build against. No live feed, threads, or I/O pipeline
yet — those begin at P1.

**Folder rename (P0-A).** `MarketDepth_Recorder/` → `market_depth_recorder/` (the folder *is* the
package, §2.1). The directory-level `git mv` failed (a stale process holds the old dir's handle), so
the three docs were moved **per-file** with `git mv` instead — content and working-tree doc-sync edits
preserved. The now-empty, untracked `MarketDepth_Recorder/` remnant is harmless (git ignores empty
dirs); delete once the holding process closes.

**Added files.**
- `__init__.py` — `__version__ = "0.1.0"`, `SCHEMA_VERSION = 1` (stamped into raw HEADER §3.5.4 and
  `recorder_meta` §4.1b).
- `config.yaml` — §7.1 template materialized verbatim, `transport: "raw"` default, NIFTY+SENSEX.
- `config.py` — YAML load + **all** §7.3 rules (collect-all-errors, fast-fail `ConfigError` → exit 1),
  `compute_config_hash` (sha256 of metrics+regime+underlyings, §3.5.4/§4.1b), frozen typed `Config`
  with typed `Underlying` entries.
- `utils.py` — logging setup (idempotent, single handler, thread name), IST/time helpers
  (`parse_ist_hhmm`, `now_ist`, `to_epoch_seconds`), decay-weight factory (`w_i = exp(-k·(i-1))`,
  §3.4.2 M8), atomic file write, disk-free helper (§3.1.5).
- `metrics/registry.py` — declarative `MetricSpec` + `register`/`resolve`/`known_names`/`GROUPS`;
  **full M1–M29 + §3.4.3 rolling-window + §3.4.4 aggregate/regime metadata**, no function bodies
  (deferred P4/P7). `live_metrics` validation resolves against the complete set from day one.
- `__main__.py` — §8.2 CLI surface; `--validate-config` wired end-to-end (0/1 exit), other subcommands
  parsed + stubbed with clean exits, arg-dependency guards (`--output` needs `--replay`; `--from/--to`
  parse as IST `HH:MM`).
- `requirements.txt` — standalone pins: `openalgo==2.0.2` exact (load-bearing), `numpy/duckdb/PyYAML/
  websocket-client/pytest` compatible-release `~=` against installed versions.
- `.gitignore` — runtime artifacts (`data/**`, `*.jsonl.gz`, `*.db*`, `*.duckdb`, `*.log`, venv, caches).
- `Documents/` — `ARCHITECTURE.md`, this `CHANGELOG.md`, `SETUP.md`, `config.md`, `utils.md`, `registry.md`.
- `tests/` — `conftest.py` (good-config fixture + writer), `test_config.py` (happy path, one negative
  per §7.3 rule, `--validate-config` exit codes, `config_hash` determinism, `live_metrics` membership),
  `test_utils.py` (decay values, IST parse, atomic round-trip, disk free).

**Verification.** `--validate-config` on the shipped config exits 0; **48 tests pass**, no live feed.
Arg guards return exit 2 on misuse; stubs exit 0.

**FD audit (P0 surface).** `config.py` write-probe closes its `mkstemp` fd and unlinks the temp on all
paths; `utils.atomic_write` adopts the raw fd into a file object (closing the bare fd if adoption
fails) and cleans the temp on error; logging adds a single guarded `StreamHandler` (no stacking). No
sockets/DB/subprocess/threads exist yet. Clean.

**Deferred.** Metric function bodies (P4/P7); `recorder_meta`/HEADER stamping (P2/P5/P7); `--preflight`
(P1), `--status` (P6), `--replay`/`--catchup`/`--verify` (P7). Empty `MarketDepth_Recorder/` dir removal
(pending stale handle release).
