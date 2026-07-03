# Changelog — Market Depth Recorder

Dated running log; one entry per phase/iteration (what changed, why, affected files, deferred work).

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
