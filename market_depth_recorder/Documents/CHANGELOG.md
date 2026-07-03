# Changelog — Market Depth Recorder

Dated running log; one entry per phase/iteration (what changed, why, affected files, deferred work).

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
