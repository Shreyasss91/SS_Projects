# Market Depth Recorder — Implementation Plan

## Context

We are building the **Market Depth Recorder**, a standalone, high-throughput Python microservice
that captures real-time option market depth for configured weekly chains (initially NIFTY + SENSEX)
off OpenAlgo and persists it through a three-tier pipeline: **Tier 0** raw `.jsonl.gz` (lossless
source of truth) → **Tier 1** thin live SQLite/WAL (`live_metrics` subset, market hours) → **Tier 2**
fat DuckDB analytics (full catalog, rebuilt offline by replaying Tier 0). It is config-driven and
broker/exchange/symbol-agnostic.

The authoritative design is `market_depth_recorder_design.md` (~1452 lines, the spec). This plan
sequences that spec into independently testable phases, reconciles it with **three verified
integration findings**, and folds in four approved future-adaptability scope additions. Nothing here
changes the spec's architecture — it makes its extension points first-class and corrects one
load-bearing assumption the spec itself flagged for confirmation (§3.3.5 ⚠️, P8).

### Verified integration findings (drive several decisions below)
- **REST (startup):** `GET /api/v1/instruments/?apikey=…&exchange=NFO&format=json` returns rows with
  `symbol, brsymbol, name, exchange, brexchange, token, expiry, strike, lotsize, instrumenttype,
  tick_size`. **Expiry is `DD-MMM-YY` uppercase** (`09-JUL-26`) — parse with `%d-%b-%y`, fallback
  `%d-%b-%Y`. `POST /api/v1/expiry {apikey, symbol, exchange:"NFO"/"BFO", instrumenttype:"options"}`
  returns a sorted future-only expiry list; `exchange` must be the **option** exchange, not
  `NSE_INDEX`. `POST /api/v1/quotes {apikey, symbol, exchange:"NSE_INDEX"}` → `data.ltp`, and
  **requires a live broker session** (the others are DB-backed). Default rate limit 10 req/s.
- **FYERS depth:** `symbol.endswith(":50")` + `TBT_SUPPORTED_EXCHANGES={"NSE","NFO"}` route to TBT
  50-level; **BFO/SENSEX silently degrades to 5-level**. Depth is **mode 3**. Per-level dicts are
  `{price, quantity, orders}`; **`orders` (count) is populated** on TBT → M13/M14 computable, but
  it is cumulative/carried-forward on diff updates, so **`orders==0` must be treated as NULL**
  (avoid M13 divide-by-zero). `timestamp` is proxy-local `int(time.time())`; `feed_time` is the
  broker exchange clock and is present only on the TBT depth packet.
- **SDK strips audit fields (load-bearing):** the installed SDK `openalgo==2.0.2`
  (`feed.py:456-467`) delivers only `{ltp, timestamp, depth:{buy,sell}}` to the depth callback and
  **drops `feed_time`, `depth_levels`, `is_50_depth`, `total_buy/sell_qty`**. The proxy sends these
  over the wire (`server.py:1821-1827`); only the SDK convenience layer discards them. The SDK also
  defaults `auto_reconnect=True`. The `:50` suffix passes through the SDK unaltered. → Raw WS is the
  only transport that preserves the recorder's core value (self-describing, exchange-timestamped
  audit).

### Locked decisions
1. **Transport default = raw WebSocket (primary).** SDK selectable via `websocket.transport: sdk`
   (LTP/degraded use). Reconnect/resubscribe/DSM/tee stay transport-agnostic — only the default flips.
2. **Folder rename** `MarketDepth_Recorder/` → `market_depth_recorder/`; the folder **is** the Python
   package (`__init__.py` + `__main__.py` + modules), with `config.yaml`, `requirements.txt`,
   `Documents/`, `tests/`, `data/`, and the docs alongside. Run `python -m market_depth_recorder …`
   from the parent `SS_Projects/`.
3. **Standalone `requirements.txt` + venv** (`openalgo`, `numpy`, `duckdb`, `pyyaml`,
   `websocket-client`). No coupling to the platform's uv env.
4. **`auto_reconnect=False`** when constructing the SDK client (recorder owns reconnect/resubscribe).
5. **Depth capture over raw WS** yields `feed_time`/`depth_levels`/`is_50_depth` directly; the §3.2.5
   preflight subscribes one near-ATM strike per underlying and reads them to log actual depth.
6. **Four scope additions** (all additive): metric registry · provenance+versioning · operational CLI
   · session guards. Detailed under each phase.

### Decisions taken during P0 planning (2026-07-03)
7. **Canonical spec = the in-folder `market_depth_recorder_design.md`** (inside the package folder). The
   copy under `..\trading_engine\...\LLM_Spec_Chat\` is stale and ignored. CLAUDE.md/PROJECT_NOTES updated.
8. **Dependency pinning:** `openalgo==2.0.2` pinned **exactly** (load-bearing — the audit-field-stripping
   behavior in `feed.py:456-467` is version-specific); `numpy`/`duckdb`/`pyyaml`/`websocket-client`/`pytest`
   pinned with compatible-release `~=` against the versions actually installed at build time (read them,
   don't guess). Reproducible without freezing out patch updates.
9. **Metric registry (P0-G) pre-registers the full M1–M29 metadata skeleton now** (metadata only — id,
   inputs, min_depth, output columns, thin/fat eligibility; **no function bodies**, deferred to P4/P7).
   `live_metrics` validation (§7.3) resolves against the complete set from day one.

### Decisions taken during P1 planning (2026-07-03)
10. **Preflight live depth probe DEFERRED to P3** (user-confirmed fork). Reading `depth_levels`/
    `is_50_depth` needs a **raw-WS subscription** (the SDK strips them, §3.3.1), and the reconnect/DSM/tee
    client is P3 — pulling a throwaway socket into P1 would add an FD surface P3 immediately supersedes.
    So **P1 delivers the full InstrumentManager + an OFFLINE `--preflight`** (resolve each chain, print the
    planned near-ATM probe strike + `requested_depth` per underlying, mark `actual_depth` as *"pending P3
    raw-WS probe"*), and **P3 owns the live depth probe** + the §9 `actual < requested` WARNING. P1 stays
    socket/thread-free and deterministic.
11. **`E_weekly` via the `/api/v1/expiry` endpoint** (spec §3.2.1 "preferred"), NOT re-derived from the
    master. The expiry service already **drops past expiries, sorts, and includes the expiry day**
    (`expiry_service.py:224-228`) — so `data[0]` **is** `E_weekly` with the §3.2.2 rollover gate already
    satisfied. Body `instrumenttype:"options"` (lowercase); `exchange` = the **option** exchange (NFO/BFO),
    never `NSE_INDEX`. The master (GET instruments) is used only for the **strike grid + symbol + tick_size**.
12. **Underlying↔instrument match on the `name` column** (exact, unambiguous since we query per option-
    exchange), with a **longest-prefix `symbol` guard** as the documented fallback for masters with an
    inconsistent `name` (cf. `qty_freeze_db.py:211-219` — NIFTYNXT50 must not be shadowed by NIFTY).
13. **Maps built directly from master `symbol` rows** — never string-construct option symbols (the master
    `symbol` is authoritative; avoids expiry-format/strike-format bugs). Float `strike` → `int` key when
    integral (index strikes are).
14. **REST via stdlib `urllib`** (no new dependency — keeps the standalone venv promise): one opener,
    10 s timeout, ≤3 retries w/ backoff, `apikey` as query (instruments) / body (expiry); injectable
    `RestClient` so all tests run against canned dicts with no live server.

### Progress-tracking convention (this doc is live)
- Phase subtask checklists are embedded here as `- [ ]` / `- [x]` items; tick them as work completes.
- Per PROJECT_NOTES workflow step 9 + CLAUDE.md, update this doc when a fork is decided, before a phase
  starts (embed its checklist), and as each subtask/phase completes. `Documents/` tracks implemented
  state; this plan tracks progress.

---

## P0.0 — Doc sync (execute FIRST, right after exiting plan mode) — ✅ DONE (2026-07-03, commit 29eb68a)

Keep `market_depth_recorder_design.md` and `PROJECT_NOTES.md` in sync with the decisions above **before**
writing code. Edits to the spec (cite the finding for each):

- **Transport default (fork 1):**
  - §1.3(1) and §3.3.1/§3.3.1a: reframe **raw WebSocket as the primary transport** and the SDK as the
    alternate; state *why* (SDK `feed.py:456-467` strips `feed_time`/`depth_levels`/`is_50_depth`/
    `total_*_qty`; proxy sends them at `server.py:1821-1827`).
  - §3.3.5 ⚠️ note: mark **resolved** — SDK passes `:50` through unaltered, but drops the audit fields,
    so raw is default. Keep the SDK path documented.
  - §7 template + §7.2 table: change `websocket.transport` default from `"sdk"` to `"raw"`; update the
    inline comment.
- **Package layout (fork 2):** §2.1 directory schema — rename the root to `market_depth_recorder/`, add
  `requirements.txt`, `Documents/`, `tests/`. §8.2 invocation already uses `market_depth_recorder`.
- **Env (fork 3):** §1.3(1)/§2.1 — note the standalone `requirements.txt` + venv explicitly.
- **`auto_reconnect=False` (decision 4):** §3.3.1 client construction — add the argument and one line of
  rationale (avoid double reconnect/replay).
- **SDK-strips-fields + preflight (decision 5):** §3.2.5 and §9 — record that the preflight reads
  `feed_time`/`depth_levels`/`is_50_depth` from the **raw** packet; over SDK these are unavailable and
  level count would be inferred from `len(depth["buy"])`. Confirm per-level `orders` present (M13/M14)
  with the `orders==0 → NULL` caveat (`fyers_tbt_websocket.py:476-490`).
- **Scope adds:**
  - *Metric registry:* new short subsection under §3.4 (e.g. §3.4.0) — declarative registry; each metric
    declares inputs, min depth, output column(s); `recorder.live_metrics` validated against the registry;
    thin vs fat = which registry entries fire.
  - *Provenance + versioning:* §3.5.4 — add a **HEADER** meta line at file open (session date, underlyings,
    config hash, schema_version) complementing the EOF line; §4 — a small `recorder_meta` table (or DuckDB
    equivalent) stamping `schema_version` + config/formula hash into both stores; note in §8.4 that
    `--verify` compares stamps.
  - *Operational CLI:* extend §8.2 with `--validate-config`, `--preflight`, `--status` (dry-run, exit
    0/1; no live market needed).
  - *Session guards:* §3.1/§6 — pre-session disk-space check + periodic low-space ERROR alarm (ties to the
    lossless-raw invariant), and optional trading-holiday/non-trading-day skip; add config keys in §7
    (`recorder.min_free_disk_mb`, `recorder.disk_check_interval_sec`, `recorder.skip_non_trading_days`,
    `recorder.trading_holidays: []`).
- **`PROJECT_NOTES.md`:** update the module map / invariants / roadmap to record fork 1 (raw default),
  the rename, and the four scope adds so the working rulebook matches the spec.

*Deliverable check:* spec + notes reflect all six locked decisions; no silent drift.

---

## P0 — Scaffolding, config, utils, registry skeleton

**Expanded subtask checklist** (embedded 2026-07-03; tick as completed). Reconciled against spec
§2.1 (layout), §7.1 (config template), §7.3 (validation), §3.4.0 (registry), §4.1b + §3.5.4 (provenance),
§8.2 (CLI).

### P0-A · Git-aware folder rename `MarketDepth_Recorder/` → `market_depth_recorder/`
- [x] A1. Confirm git repo root — it is `SS_Projects/` (its own `.git`, user *Shreyas S S*, branch `main`),
  **not** the openalgo repo. Rename runs from there.
- [x] A2. **RESOLVED (2026-07-03):** session now anchored at parent `SS_Projects/`. Directory-level `git mv`
  still failed **Permission denied** (a stale process holds the old dir as its cwd), so used **per-file** git mv
  instead — all 3 files moved cleanly into `market_depth_recorder/`. The now-empty, **untracked** `MarketDepth_Recorder/`
  remnant is "Device or resource busy" on rmdir; git ignores empty dirs so it won't be committed — delete once the
  holding process closes.
- [x] A3. The 3 docs (`CLAUDE.md`, `market_depth_recorder_design.md`, `PROJECT_NOTES.md`) moved with the rename
  (staged as `RM`/`R`, working-tree doc-sync edits preserved).
- [x] A4. (done in planning) source-of-truth switched to in-folder spec in CLAUDE.md + PROJECT_NOTES.
- [x] A5. `.gitignore` inside package: `data/**`, `*.jsonl.gz`, `*.db*`, `*.duckdb`, `*.log`,
  `health.json`, `reprocess.lock`, `__pycache__/`, `.venv/`, `.pytest_cache/`.
- [x] A6. Session already anchored at parent `SS_Projects/`; all P0 files created under
  `market_depth_recorder/`. Subsequent phases run from there.

### P0-B · Package skeleton + CLI surface — ✅
- [x] B1. `__init__.py` — `__version__ = "0.1.0"` + `SCHEMA_VERSION = 1`.
- [x] B2. `__main__.py` — full `argparse` surface (all §8.2 flags).
- [x] B2a. `--validate-config` wired end-to-end (load+validate → report → exit 0/1); `--preflight`/`--status`/
  `--replay`/`--catchup` parsed + stubbed with clean (exit 0) "not implemented until P<n>".
- [x] B2b. Arg-dependency guards (`--output`/`--verify` only with `--replay/--catchup`; `--from/--to`
  parse as IST `HH:MM`) → usage error exit 2. Verified via CLI.

### P0-C · `requirements.txt` + venv bootstrap — ✅
- [x] C1. `requirements.txt` — `openalgo==2.0.2` (exact) + `numpy~=2.4.4`, `duckdb~=1.5.2`, `PyYAML~=6.0.3`,
  `websocket-client~=1.9.0`, `pytest~=9.0.3` (compatible-release against installed versions). Standalone.
- [x] C2. `Documents/SETUP.md` — venv bootstrap + module-run instructions.

### P0-D · `config.yaml` (materialize §7.1 template) — ✅
- [x] D1. `config.yaml` written verbatim from §7.1 (all sections + NIFTY/SENSEX), annotated comments,
  `transport: "raw"` default, `api_key` placeholder.
- [x] D2. Single tracked `config.yaml` template (no separate example file).

### P0-E · `config.py` — load + full §7.3 validation (fast-fail, exit 1) — ✅
- [x] E1. Rule 1 — safe-load YAML, catch `YAMLError`/`FileNotFoundError` → report.
- [x] E2. Rule 2 — I/O verify `recorder.output_dir` (temp create+delete; mkdir if missing).
- [x] E3. Rule 3 — all boundary checks, **collect ALL failures** (not first): per-underlying
  `expansion_threshold < initial_window`; unique `name` + required non-empty keys +
  `strike_step_fallback ∈ expected_strike_step`; `database.batch_write_interval_ms ∈ [500,5000]`;
  `analytics_db.memory_limit_mb ≥ 256` & `1 ≤ threads ≤ 64`; `live_metrics` membership (registry or `"all"`);
  enums `transport ∈ {sdk,raw}` / `processor.mode ∈ {thread,process}` (+`shards ≥ 1` if process); watermarks
  `0 < warn < critical ≤ 100` & `raw_file_queue_max ≥ max_queue_size`; `session_start < session_end`;
  non-empty positive-int lists (`time_windows_sec`, `round_number_multiples`, each `expected_strike_step`);
  session guards (`min_free_disk_mb ≥ 0`, `disk_check_interval_sec ≥ 5`, `skip_non_trading_days` bool,
  `trading_holidays` parse `YYYY-MM-DD` when skip=true).
- [x] E4. Rule 4 — `recorder.health_file_path` parent dir writable/creatable (no `/tmp` assumption).
- [x] E5. Rule 5 — fast-fail: collect → `ConfigError.report()` to stderr → **exit 1**; no silent defaults.
- [x] E6. Rule 6 — `host_server` (http/https) & `websocket_url` (ws/wss) parse as valid URIs.
- [x] E7. `config_hash` — `sha256:` over canonicalized `metrics`+`regime`+`underlyings`; determinism +
  non-formula-section insensitivity tested.
- [x] E8. Returns frozen `Config` dataclass (typed `Underlying` tuple + read-only section maps).

### P0-F · `utils.py` — shared primitives — ✅
- [x] F1. Idempotent logging setup (single console handler, level, thread name) + `get_logger`.
- [x] F2. IST/time helpers: `parse_ist_hhmm`, `now_ist()`, `to_epoch_seconds` (UTC).
- [x] F3. Decay-weight array factory `w_i = exp(-decay_k·(i-1))` (w1=1.0, w5≈0.45, w10≈0.16 tested).
- [x] F4. Atomic-file-write helper (temp + `fsync` + `os.replace`; fd closed + temp cleaned on all paths).
- [x] F5. Disk-space helper (`shutil.disk_usage` → free MiB).

### P0-G · `metrics/registry.py` — declarative skeleton (§3.4.0), **full M1–M29 metadata** — ✅
- [x] G1. `metrics/__init__.py` package marker.
- [x] G2. Frozen `MetricSpec` dataclass: name, family, inputs, min_depth, output_columns, table,
  spec_section, description, m_number, thin/fat eligibility.
- [x] G3. `register(...)` (decorator-capable; binds body later via `METRIC_FUNCS`) + `REGISTRY`;
  duplicate-name fast-fail.
- [x] G4. Lookup API: `resolve(token)`, `known_names()`, `known_aggregates()`, `GROUPS` (`atm_aggregates`),
  `regime` as a metric, `"all"`.
- [x] G5. Full M1–M29 + §3.4.3 rolling-window + §3.4.4 aggregate/regime metadata registered against
  actual §4.1 column names — metadata only, **no function bodies** (deferred P4/P7).

### P0-H · `Documents/` skeleton — ✅
- [x] H1. `ARCHITECTURE.md` — layout (§2.1), tiers, target thread/queue topology, invariants, P0 built state.
- [x] H2. `CHANGELOG.md` — dated P0 entry (what/why/files/verification/FD audit/deferred).
- [x] H3. Per-module docs: `config.md`, `utils.md`, `registry.md`, `SETUP.md`.

### P0-I · Tests — `tests/test_config.py` (+ `test_utils.py`) — ✅ (48 passed)
- [x] I1. `tests/__init__.py` + `conftest.py` good-config fixture + `write_config` helper.
- [x] I2. Happy path (fixture + shipped `config.yaml`) loads+validates clean.
- [x] I3. One negative test per §7.3 rule (16 parametrized + dedicated per-underlying/YAML/IO cases).
- [x] I4. `--validate-config` exit codes (good→0, bad→1, report to stderr).
- [x] I5. `config_hash` determinism (same→same, constant→different, non-formula section→same).
- [x] I6. `live_metrics` membership (unknown fails; `all` passes; all 29 M-names pass).
- [x] I7. utils tests (decay values+monotonic, IST parse ok/bad, atomic round-trip+no-stray-temp, disk free).

### P0-J · Completion Audit — ✅
- [x] J1. `--validate-config` → 0 good / 1 seeded-bad (verified).
- [x] J2. `pytest tests/ -q` green (48 passed), no live feed.
- [x] J3. FD audit of P0 surface — write-probe fd closed+unlinked all paths; `atomic_write` hardened
  (adopt-fd-or-close); single guarded log handler; no sockets/DB/subprocess/threads yet. Clean.
- [x] J4. Docs current (ARCHITECTURE + CHANGELOG + per-module) citing spec §s.
- [x] J5. Genericization check — no index/exchange/strike-step literal in engine code (only config.yaml +
  test fixtures; `utils`/`log_level` hits are `"INFO"` false positives).
- [ ] J6. Stop for approval before P1. ← **awaiting approval**

*Critical files:* `market_depth_recorder/{__init__.py,__main__.py,config.py,utils.py,metrics/registry.py,
metrics/__init__.py}`, `requirements.txt`, `config.yaml`, `.gitignore`,
`Documents/{ARCHITECTURE,CHANGELOG,SETUP,config,utils,registry}.md`, `tests/{__init__,conftest,test_config,test_utils}.py`.

## P1 — InstrumentManager (`instrument_manager.py`)

**Scope:** the first live module — runs once at startup to resolve each configured underlying's current
weekly option chain over OpenAlgo REST, auto-detect the strike step, and compile the O(1) lookup maps +
per-symbol `tick_size` that P3 (DSM) and P4 (processor) consume. **Pure resolution logic — no sockets,
threads, or DB** — fully testable against mocked REST (decisions 10–14 above). Standalone project: talks
to OpenAlgo only over HTTP; imports no platform module.

**Verified REST contract (read from OpenAlgo source 2026-07-03):**
- **Instruments** `GET {host_server}/api/v1/instruments/?apikey=<k>&exchange=<NFO|BFO>&format=json` →
  `{"status":"success","data":[{symbol,brsymbol,name,exchange,brexchange,token,expiry,strike,lotsize,
  instrumenttype,tick_size},…]}`. `strike`/`tick_size` **float**; `expiry` **string `DD-MMM-YY`
  uppercase**; `name` = base underlying; option `instrumenttype ∈ {OPTIDX,OPTSTK,CE,PE}`. Auth = query
  param. Errors 401/403/500 `{"status":"error",…}`.
- **Expiry** `POST {host_server}/api/v1/expiry/` body `{apikey,symbol,exchange:<NFO|BFO>,
  instrumenttype:"options"}` → `{"status":"success","data":[<sorted future-only expiry strings>]}`;
  `data[0]` = `E_weekly` (rollover gate pre-satisfied, decision 11).
- **Quotes** (needs live broker session) is **NOT** used in P1 — it's the P6 mid-day-restart ATM path.

### P1 subtask checklist (embedded 2026-07-03; ✅ complete 2026-07-03)
- [x] **A · `RestClient`** — stdlib `urllib` opener, 10 s timeout, ≤3 retries w/ backoff, `apikey` as
  query (instruments) / body (expiry), typed `RestError`; response used under `with`/closed on **every**
  path incl. retry/error (no leaked HTTP conn); injectable for tests.
- [x] **B · Expiry resolution** — POST expiry, `E_weekly=data[0]`, empty list → fast-fail (clear error);
  parse `E_weekly` with `%d-%b-%y` (fallback `%d-%b-%Y`) to a `date` for logs.
- [x] **C · Instruments fetch + filter** — GET per `option_exchange`; keep rows where `name ==
  underlying.name` (blank-name → longest-prefix `symbol` fallback **with a digit-after-base guard** so
  NIFTYNXT50 isn't matched to NIFTY), `instrumenttype` is an option type w/ non-null `strike`, and
  `expiry == E_weekly`.
- [x] **D · Strike-step detect + validate (§3.2.3)** — mode of adjacent sorted-strike diffs; ∈
  `expected_strike_step` else **WARNING** + `strike_step_fallback`; robust to single-strike / tie edges.
- [x] **E · O(1) maps + tick_size (§3.2.4)** — `strike_to_symbol_map[name][strike][CE|PE]`,
  `symbol_to_strike_map[symbol]`, `active_strikes_list[name]`, `tick_size_map[symbol]` (M29); frozen
  `ResolvedChain` per underlying; near-ATM probe strike = median strike placeholder (DSM refines in P3).
  Keyed by `name` throughout — no index literal.
- [x] **F · `--preflight` (offline)** wired end-to-end in `__main__.py` (replaced the P1 stub): load+
  validate → build `InstrumentManager` (REST only) → per underlying print `name, option_exchange,
  E_weekly, strike_step, #strikes, requested_depth, planned_probe_strike, actual_depth=<pending P3
  raw-WS probe>`; exit 0 clean / 1 on REST/resolution failure. No socket, no market.
- [x] **G · Tests** `tests/test_instrument_manager.py` (21 tests) — mocked REST dicts: happy path (maps/
  step/E_weekly), strike-step mode (wide-gap, single→fallback+WARN, unexpected→fallback+WARN),
  name/longest-prefix (NIFTYNXT50 not shadowed, blank-name fallback), expiry parse + empty-expiry/no-
  contracts fail, REST success/retry/timeout/5xx/4xx→`RestError`, `--preflight` exit codes. No live feed.
- [x] **H · Docs** — `Documents/instrument_manager.md` (responsibilities, public API, config keys, REST
  contract, FDs held = none persistent); updated `ARCHITECTURE.md` (P1 built state) + dated
  `CHANGELOG.md`; cite §3.2.*.
- [x] **I · Completion audit** — `pytest tests/ -q` **69 passed** (P0 48 + 21 new); `--validate-config`
  →0, `--preflight` (no server) →1 clean `RestError`; FD audit (RestClient closed on every path incl.
  HTTPError; no threads/DB/sockets); genericization check (no NIFTY/SENSEX/NFO/step **functional**
  literal in `instrument_manager.py` — only doc/comment mentions). Docs current. **← awaiting approval
  before P2.**

*Test caught a real bug (fixed):* blank-`name` longest-prefix matched `NIFTYNXT50…`→`NIFTY` (NIFTYNXT50
not a configured underlying); fixed with the digit-after-base guard (F&O symbol = `BASE + DDMMMYY…`).

*Critical files:* **new** `instrument_manager.py`, `tests/test_instrument_manager.py`,
`Documents/instrument_manager.md`; **edit** `__main__.py` (wire `--preflight`),
`Documents/{ARCHITECTURE,CHANGELOG}.md`; **reuse** `config.py`, `utils.py`, `metrics/registry.py`.

## P2 — Tier-0 gzip file writer (`file_writer.py`)

**Scope:** the first background **writer thread** — owns the Tier-0 raw `.jsonl.gz` audit log, the
**lossless source of truth** from which both derived stores are reconstructable. Drains
`raw_file_queue`, JSONL-serializes each packet, writes to a gzip handle, and shields the WS receiver
from disk latency. Pure queue consumer — **no sockets, DB, or subprocess** — fully testable offline by
injecting the queue, clock, and session date. Authoritative: **spec §3.5** (§3.5.1 loop, §3.5.2 gzip,
§3.5.3 two-tier flush, §3.5.4 naming + HEADER/EOF provenance) + the lossless-raw invariant (§1.4/§5.3).

### Decisions taken during P2 planning (2026-07-03)
15. **Single-owner FD, no lock.** The gzip handle is created/written/flushed/fsynced/closed **only** by
    the writer thread's `run()`; no other thread touches it, so **no writing lock is needed** (the spec's
    "under its writing lock" is conservative — exclusive ownership is stronger). Thread owner · state
    owner · handle owner are all this one thread.
16. **Injected clock (`time_fn=time.time`).** Sole source of epoch timestamps (`open_/close_timestamp`),
    the fsync cadence, **and** the date-rollover comparison — every time-dependent branch is deterministic
    under test. `session_date` is also injected (orchestrator passes `now_ist().date()`).
17. **Append mode kept (`gzip.open(mode="at")`).** A same-day restart appends a *second* HEADER to the
    day's file (replay tolerates it; it records the restart) rather than truncating prior audit data.
18. **Write-failure = the one sanctioned raw-loss boundary.** A per-packet `.write` exception (disk
    saturation) is caught, increments `write_error_count`, logged at **ERROR**, and the thread continues
    (one bad write must not kill the audit path — §1.4/§5.3). Full sentinel-error-queue wiring is P6;
    P2 leaves an optional `error_queue=None` hook but stays robust standalone.
19. **Tests round-trip via stdlib `gzip`+`json`, not pandas.** pandas 2.3.1 is present transitively but
    **not pinned** in `requirements.txt` (standalone-venv promise), so the mandatory tests use stdlib; a
    single `pytest.importorskip("pandas")` compat check honors the §3.5.1 tooling claim without a new pin.

### FD structure (close on EVERY path)
```
run():
  try:
    self._open_file()                 # writes HEADER line
    try:
      self._consume_loop()            # drain until shutdown_event AND queue empty
      self._write_eof()               # only on clean drain
    finally:
      self._close_file()              # flush → fsync(guarded) → close; idempotent
  except Exception:
    logger.exception("RawTickFileWriter crashed")   # (+ error_queue.put in P6)
```
A mid-loop crash skips EOF (no EOF marker → replay treats the file as incomplete, the intended signal)
but still closes the handle. `_close_file` guards `None`/already-closed and tolerates a closed fileno.

### P2 subtask checklist (embedded 2026-07-03; ✅ complete 2026-07-03)
- [x] **A · Module skeleton** — `file_writer.py` with `class RawTickFileWriter(threading.Thread)`;
  docstring citing §3.5 + FD-ownership + genericization notes; constructor
  `(config, raw_file_queue, shutdown_event, session_date, *, schema_version, time_fn, error_queue, name)`
  reading `output_dir`/`gzip_compresslevel`/`flush_max_records`/`fsync_interval_sec`/`config_hash`/
  underlying names from `config`.
- [x] **B · `resolve_filename` (staticmethod) + `_open_file`** — `market_depth_raw_YYYYMMDD.jsonl.gz`
  from `session_date`; `gzip.open("at", …)`; HEADER line; init `last_fsync`/`unflushed_count`/
  `_current_date`; HEADER flushed to OS immediately.
- [x] **C · `_write_packet` + `_maybe_flush`** — compact JSONL; counter bumps; two-tier flush (§3.5.3):
  cheap `flush()` at `flush_max_records`; bounded `flush()`+`os.fsync(fileno())` every `fsync_interval_sec`.
- [x] **D · `_maybe_rollover`** — defensive **IST** date-change guard (`datetime.fromtimestamp(time_fn(),
  tz=IST)`, matches `session_date` basis) → EOF+close old, reopen new-dated file. Never fires normally.
- [x] **E · `run` + `_consume_loop` + `_write_eof` + `_close_file`** — drain until shutdown AND empty;
  `get(timeout=1.0)`/`task_done()`; per-packet write-error catch (count + ERROR); EOF on clean drain;
  guarded flush→fsync→close on every path; `records_written`/`write_error_count`/`_filename` exposed.
- [x] **F · Tests** `tests/test_file_writer.py` (10, offline): round-trip; provenance; cheap-flush
  cadence; bounded-fsync cadence (spied `os.fsync` + clock); missing-EOF + byte-truncated-tail
  tolerance; defensive IST rollover; write-error accounting; graceful drain via real thread; optional
  pandas `read_json` compat.
- [x] **G · Docs** — new `Documents/file_writer.md`; updated `Documents/ARCHITECTURE.md` (P2 built state
  + topology) + dated `Documents/CHANGELOG.md`; cite §3.5.
- [x] **H · Completion audit** — full `pytest market_depth_recorder/tests/ -q` **79 passed** (69 + 10);
  FD audit (one gzip handle, guarded `finally` close on drain/exception/rollover/shutdown; `fsync` guards
  closed fileno; no other FDs; fakes hold no real FD); genericization check (no index/exchange/strike
  functional literal in `file_writer.py` — only a doc mention). Docs current. **← awaiting approval before P3.**

*Robustness fix caught by tests:* the rollover guard originally compared the **machine-local** date to
`session_date` (from `now_ist()`), which would spuriously roll over on a non-IST host at the first
write; fixed to compare in **IST**, matching `session_date`'s basis.

*Critical files:* **new** `file_writer.py`, `tests/test_file_writer.py`, `Documents/file_writer.md`;
**edit** `Documents/{ARCHITECTURE,CHANGELOG}.md`; **reuse** `config.py`, `utils.py`, `__init__.py`,
`tests/conftest.py`.

*Tests (spec §3.5.1) confirm the log is standard-tooling compatible (`pd.read_json(lines=True,
compression="gzip")`) while the mandatory suite stays stdlib-only.*

## P3 — WebSocket client + DSM (`websocket_client.py`)

**Scope:** the first **networked** module and the piece that actually produces ticks. It owns the feed
transport to the OpenAlgo WS proxy, the **Dynamic Strike Manager (DSM)**, the **tee** into
`raw_file_queue`/`proc_queue`, the recorder-owned reconnect state machine, and the **live
depth-capability preflight** (§3.2.5/§9, moved here from P1 per decision 10). It emits normalized
packets into the two (injected) queues and manages subscriptions — **no resampler/metrics/DB/gzip**
(P4/P5) and **no orchestration/REST-quote seeding** (P6). Authoritative: **spec §3.3** (§3.3.1a raw
transport, §3.3.2 DSM/boundary math, §3.3.3 subscription flow + `:50`, §3.3.4 never-shrink), **§6.1**
(reconnect), **§3.2.5/§9** (preflight/observability), **§5.1** (per-queue backpressure).

**Verified WS proxy protocol (`websocket_proxy/server.py`, read 2026-07-03):** authenticate
`{"action":"authenticate","api_key":<cfg>}` (also accepts `apikey`); subscribe
`{"action":"subscribe","symbol":<s>,"exchange":<e>,"mode":<1|3>,"depth":<n>}` (`server.py:1151,1171,
1201`), ack echoes `depth: actual_depth`; market-data envelope `{"type":"market_data","symbol",
"exchange","mode","data":{…}}` (`server.py:1821-1827`) whose `data` carries `feed_time`/`depth_levels`/
`is_50_depth`/`total_*_qty`/`depth:{buy,sell}`/`ltp`/`timestamp`; `:50` routes to FYERS TBT
(`fyers_websocket_adapter.py:349`, `TBT_SUPPORTED_EXCHANGES={"NSE","NFO"}`, BFO→5), re-published under
the same suffixed topic (§3.3.3).

### Decisions taken during P3 planning (2026-07-03)
20. **Transport seam.** A `FeedTransport` protocol (`connect→bool`, `disconnect`, `authenticate`,
    `subscribe`, delivery callback). `RawWSTransport` built fully (default); **`SdkTransport` deferred**
    — a stub raising a clear `NotImplementedError` at construction. DSM/tee/reconnect/never-shrink live
    in transport-agnostic `DepthWebSocketClient`; only auth/subscribe/heartbeat framing differ; config
    `transport` selects the impl. *(User away on the "SDK now vs deferred" fork; deferring is the
    recommended default — filling `SdkTransport` later is purely additive.)*
21. **Canonical packet = wire message, lightly normalized.** One flat dict: `symbol` **as received
    (keeps `:50`, honoring §3.3.3 "raw preserves exactly as received")**, `exchange`, `mode`, payload
    fields (`ltp/timestamp/feed_time/depth_levels/is_50_depth/total_*_qty/depth:{buy,sell}`), plus a
    recorder-added `recv_ts` (injected clock). **Teed to both queues** (single item, two puts).
    Stripping `:50` to the DB symbol is the **consumer's** job (P4/P5) — audit stays verbatim.
22. **Heartbeat = `websocket-client` native `run_forever(ping_interval=heartbeat_interval_sec,
    ping_timeout=heartbeat_timeout_sec)`** — no hand-rolled monitor thread (fewer FDs/threads,
    FD-hygiene). A missed pong → `on_close` → recorder-owned reconnect.
23. **One FEED thread** owns `connect/disconnect` + reconnect loop + (raw) `run_forever` receive loop.
    Callbacks run on it; they do **only** the cheap tee (+ DSM handoff for spot) and never block (§5.1).
24. **Three locks, order `spot_lock → RLock`; `client_lock` independent.** `spot_lock` guards
    `current_spot_prices` + per-underlying 10-tick median deque + `B_lower/upper`; `RLock` guards
    `active_subscriptions`; `client_lock` serializes `subscribe/unsubscribe` into the transport.
    `connect/disconnect` are FEED-thread-only and **not** under `client_lock`. **No I/O under any
    lock**; the tee takes no lock.
25. **DSM seeds lazily from the first valid spot tick** (`S_0`, `B_lower/upper`, `K_initial` from
    `active_strikes_list`). P6's mid-day REST one-shot feeds the same `on_spot(name, price)` entry —
    so P3 has **no** REST/quotes code. Spot validation: drop `≤0` and `>2%` single-tick spikes vs the
    10-tick median.
26. **Never-shrink.** Diff target strikes against `active_subscriptions`; subscribe only the
    difference; never unsubscribe intra-session (reset only at 15:35, a P6 concern).
    `active_subscriptions` stores the **wire** symbol (with `:50`) so resubscribe re-sends it exactly.
27. **`:50` + frame depth.** Depth frame `mode=3, depth=<requested_depth>`, symbol suffixed `:50` when
    `requested_depth > 5`. `:50` is the adapter's TBT trigger token (a transport constant with a citing
    comment — not an index/exchange literal), so the genericization contract holds.
28. **Tee backpressure (§5.1).** `proc_queue.put_nowait` (Full → `proc_dropped_total` + WARNING, sheds
    **first**); `raw_file_queue.put(timeout=_RAW_PUT_TIMEOUT_SEC)` (Full → `raw_dropped_total` + ERROR,
    the **single** sanctioned raw-loss boundary, sheds **last**).
29. **Reconnect (recorder-owned, §6.1).** `T = min(backoff_max_sec, backoff_base^attempts·backoff_mult)`
    with injected `sleep_fn`; on (re)connect authenticate → resubscribe **every** symbol in
    `active_subscriptions` (batched) → resume. A subscribe issued while disconnected updates the set
    only and is flushed by the next resubscribe.
30. **`--preflight` re-pointed, graceful-degrade.** Keep the offline resolve (P1) **and** attempt the
    live probe (one `:50` depth per `chains[name].probe_strike`, read `depth_levels`/`is_50_depth`/
    per-level `orders`, log the §9 line + WARNING on `actual<requested`). **WS unreachable → print
    `actual_depth=<unreachable: no WS/session>` and exit 0** (preserves P1's CI-friendly smoke
    contract; the P6 in-session orchestrator preflight treats unreachable as a hard startup error
    separately). *(User away on the exit-code fork; graceful exit-0 is the recommended default.)*

### P3 subtask checklist (embedded 2026-07-03; tick as completed)
- [x] **A · Module skeleton + transport seam** — `websocket_client.py` docstring (§3.3/§6.1 + FD/lock
  table + genericization note); `FeedTransport` protocol; `RawWSTransport` + deferred `SdkTransport`
  stub; `make_transport(config)` (selects by transport; sends/callbacks via `bind`).
  `DepthWebSocketClient(config, instrument_manager, raw_file_queue, proc_queue, shutdown_event, *,
  time_fn, sleep_fn, transport, name)` initializing the three locks, `active_subscriptions`,
  per-underlying spot/boundary state keyed by `name`, drop counters.
- [x] **B · Raw transport** — `run_forever(ping_interval/ping_timeout)`; `on_open` authenticate frame;
  `on_message` parse → filter `market_data` → normalize (decision 21) → `_on_message`;
  `on_close/on_error` → reconnect; idempotent `close()` on every path.
- [x] **C · Tee** — `_tee(packet)`: `proc_queue.put_nowait` (WARNING+count) then
  `raw_file_queue.put(timeout=_RAW_PUT_TIMEOUT_SEC)` (ERROR+`raw_dropped_total`). Two puts, no lock.
- [x] **D · DSM** — `_on_spot` (spot_lock: median deque, drop ≤0/>2% spikes, seed `S_0`/boundaries/
  `K_initial`); `_check_boundaries` (breach → expand by `E`, `K_new` from `active_strikes_list`, update
  boundary). Params per-underlying from config, state keyed by `name`.
- [x] **E · Subscription flow + never-shrink** — `_subscribe_strikes(name, strikes)` (RLock: map via
  `strike_to_symbol_map`, wire symbol w/`:50`, diff vs set, add difference; sends after lock release
  under `client_lock`); spot LTP `mode=1` per underlying on connect; no unsubscribe intra-session.
- [x] **F · Reconnect state machine** — FEED-thread loop: backoff (`sleep_fn`) → `run_session` (open →
  `on_open` authenticate + `_subscribe_spots` + `_resubscribe_all`) → resume; `shutdown_event` breaks +
  `close()`.
- [x] **G · Live preflight (§3.2.5/§9) + `--preflight` re-point** — `run_depth_preflight()` (one `:50`
  per `probe_strike`, bounded-timeout first packet, reads `depth_levels`/`is_50_depth`/`orders`, closes
  cleanly, fast-degrades when unreachable); §9 INFO line + WARNING on `actual<requested`; re-pointed
  `_cmd_preflight` (offline resolve prerequisite + live probe; unreachable → `<unreachable>` + exit 0;
  removed P1's `<pending>` literal).
- [x] **H · Tests** `tests/test_websocket_client.py` (18, offline, fake transport + injected
  clock/sleep): tee both-queues + shed order + raw-drop accounting; DSM `K_initial`/breach-expand
  (gradual ramps within the 2% spike guard)/spike+non-positive-ignore/never-shrink; reconnect
  resubscribes full set + disconnected-subscribe flush + deterministic backoff; `:50` on depth / absent
  on spot; wire-symbol + normalize helpers; preflight reads `depth_levels`/`is_50_depth`/`orders` + WARN
  on actual<requested; unreachable degrades fast. Plus the two updated `--preflight` CLI tests +
  WS-unreachable-exit-0 in `test_instrument_manager.py`.
- [x] **I · Docs** — new `Documents/websocket_client.md` (API, threads/locks/FDs, config keys,
  transport table, preflight); updated `ARCHITECTURE.md` (P3 built state + topology/locks) + dated
  `CHANGELOG.md` (incl. deferred SDK transport) + `instrument_manager.md` (`--preflight` now live);
  cite §3.3/§6.1/§9.
- [x] **J · Completion audit** — full `pytest` **98 passed** (79 prior + 19 new), no live feed;
  `--validate-config`→0, `--preflight`(no server)→exit 1 at REST resolution (documented prerequisite;
  the WS graceful-degrade only applies after resolve succeeds); **FD audit** (one FEED thread + one
  daemon preflight-probe thread joined in `finally`, socket `close()`d on every path incl. drop/
  reconnect/shutdown/probe, close-before-reconnect, SDK stub holds nothing); **concurrency audit**
  (owners named, order `spot_lock→sub_lock` never nested, no I/O under locks, tee lock-free,
  connect/close off `client_lock`, counters FEED-thread-only); genericization (only a doc-comment
  NIFTY/SENSEX mention; `:50`/`5` = cited `_TBT_SUFFIX`/`_TBT_MIN_DEPTH` transport constants).
  **← stop for approval before P4.**

*Test caught a real behavior (fixed in the tests):* the initial breach tests jumped spot >2% in one
tick and were **correctly** rejected by the DSM's own spike guard (§3.3.2) — the tests were changed to
ramp gradually, confirming the guard works as specified rather than papering over it.

*Critical files:* **new** `websocket_client.py`, `tests/test_websocket_client.py`,
`Documents/websocket_client.md`; **edit** `__main__.py` (re-point `--preflight`),
`Documents/{ARCHITECTURE,CHANGELOG,instrument_manager}.md`; **reuse** `config.py`,
`instrument_manager.py`, `utils.py`, `tests/conftest.py`. Dependency `websocket-client~=1.9.0` already
pinned (P0).

## P4 — Processor thin/live (`processor.py`), split P4a / P4b

**Scope:** the **compute core** — the `TickProcessor` thread that drains `proc_queue`, keeps a
clock-aligned **uniform 1-second grid**, and turns each second's option-book snapshots into the four
§4.1 row families, pushing them to `db_queue`. It binds the actual **NumPy metric bodies** to the
registry specs P0 declared metadata-only (`METRIC_FUNCS` was empty). The *same* `TickProcessor` runs
live (thin subset → SQLite, P5) and offline (full catalog → DuckDB, P7); thin-vs-fat is purely which
registry entries fire. Authoritative: **spec §3.4** (§3.4.0 registry, §3.4.1 resample/thin-fat, §3.4.2
M1–M29, §3.4.3 rolling, §3.4.4 aggregates + regime), **§5.1** (degraded mode / watermarks / `__slots__`),
**§6.2** (timeline continuity / NaN padding / warm-up), **§4.1** (row schema). Pure compute + queues —
**no files/sockets/DB/subprocess** — fully testable offline (injected clock + queues; the `emit_second`
seam is the P7 replay entry).

**Split (user fork, 2026-07-03):**
- **P4a** — engine (thread, resample loop, cache, staleness/forward-fill, degraded-mode skeleton,
  db_queue contract) **+ single-snapshot per-strike M1–M29** → `spot_states` + `option_strike_metrics`
  (all columns except `ofi`, which is rolling machinery).
- **P4b** — **rolling-window** metrics (§3.4.3 → `strike_window_metrics` + the instantaneous `ofi`
  column) and **multi-strike aggregates + regime** (§3.4.4 → `aggregated_window_metrics`), completing
  the full catalog. P7 reuses **all** these bodies verbatim (adds only replay + DuckDB, no new math).

**Verified data contract (read from built P1/P3 code + config, 2026-07-03):**
- *Input packet* (`proc_queue`, from `normalize_market_data`, decision 21): flat dict — `symbol` as
  received (keeps `:50` on depth), `exchange`, `mode` (1 spot / 3 depth), `ltp`, `timestamp` (proxy),
  `feed_time` (broker clock; depth only), `depth_levels`, `is_50_depth`, `total_buy/sell_qty`,
  `depth:{buy,sell}` with per-level `{price,quantity,orders}`, recorder-added `recv_ts`.
- *InstrumentManager maps* (all keyed by `name`): `symbol_to_strike_map[sym]→{underlying,strike,
  option_type}` (also the option-vs-spot classifier), `strike_to_symbol_map[name][strike][CE|PE]`,
  `active_strikes_list[name]`, `tick_size_map[sym]` (M29), `chains[name]`.
- *Config keys* (present + P0-validated): `recorder.{resample_interval_sec,staleness_timeout_sec,
  live_metrics}`, `metrics.{decay_k,effective_depth_pct,round_number_multiples,book_pressure_levels,
  wall_sigma_mult,time_windows_sec,small_window_strikes,medium_window_divisor}`, per-underlying
  `atm_max_strike_range`, `regime.{theta_*,quote_stability_min}`, `queues.{max_queue_size,
  warn_watermark_pct,critical_watermark_pct}`, `processor.{mode,shards}` (mode=thread only). **`metrics.
  fill_probe_qty` for M25 is not yet in config/§7.3 → P4a adds it (A9).**
- *Output tables* (§4.1 exact column order): `spot_states`(4), `option_strike_metrics`(~40 incl `ofi`),
  `strike_window_metrics`(~21, per `(ts,symbol,w∈{5,10,30})`), `aggregated_window_metrics`(~10, per
  `(ts,underlying,strike_window∈{SMALL,MEDIUM,LARGE})`). DB `symbol` **has no `:50`**.

### Decisions taken during P4 planning (2026-07-03)
31. **P4 split P4a/P4b** (user fork). P4a = engine + single-snapshot M1–M29 (→ `spot_states`,
    `option_strike_metrics` minus `ofi`); P4b = §3.4.3 rolling (→ `strike_window_metrics` + `ofi`) and
    §3.4.4 aggregates + regime (→ `aggregated_window_metrics`). Thin-vs-fat stays a pure selection; P7
    adds only replay + DuckDB, no new metric math.
32. **Metric bodies in `metrics/` compute modules** (user fork): `metrics/per_strike.py` (P4a),
    `metrics/rolling.py` + `metrics/aggregate.py` (P4b), each bound to its registered spec via a **new
    `registry.bind(name)` decorator** — `register()` re-registration would duplicate-fail (raises on a
    known name), so `bind()` only sets `METRIC_FUNCS[name]` on an already-registered spec (fast-fail on
    unknown name). Metadata stays frozen in `registry.py`; `processor.py` stays orchestration-only
    (genericization preserved).
33. **Single-owner `TickProcessor` thread, no processor lock.** One thread owns the `proc_queue` drain,
    `latest_ticks`, per-underlying spot cache, per-symbol history deques, `prev_snapshot`/wall state,
    **and** the 1s emit. Exactly one thread touches all of it (like P2's writer FD) → **no lock**. Cross-
    thread edges are only the thread-safe `proc_queue` (in) / `db_queue` (out).
34. **Injected clock + pure `emit_second(now_epoch)` seam.** `time_fn` (default `time.time`) is the sole
    time source for the resample boundary and staleness; `emit_second(now_epoch)` is a pure, drain-
    independent per-second entry that P7's simulated-clock replay calls directly — same processor,
    deterministic. No wall-clock inside metric math.
35. **`BookSnapshot` (`__slots__`) built once per (symbol, second).** `depth.buy/sell` → per-side NumPy
    `price/qty/orders` arrays once; every metric consumes the arrays (no re-parse). `L` = populated
    levels per side (drives `min_depth` NULL guards). `__slots__` per §5.1.
36. **Symbol keying strips `:50`.** `latest_ticks` + DB rows key by the clean symbol (§4.1 has no
    suffix). Classify: clean symbol ∈ `symbol_to_strike_map` → option (mode 3); else matches a configured
    `spot_symbol` → spot (mode 1); else counted + logged + dropped (never crashes the loop).
37. **Dependency closure, fixed compute order.** Persisted columns come from `live_metrics`, but internal
    prerequisites are always computed when a dependent is active (P4b `atm_aggregates`/`regime` force per-
    strike `book_pressure`/wobi/spread/wall even if unpersisted). Order **per-strike → rolling → aggregate
    → regime**; active set resolved once at construction via `resolve_active()`.
38. **`db_queue` emission contract (P4 defines; P5/P7 consume).** Per second, one envelope per table:
    `{"table":<name>,"rows":[tuple,…]}`, tuples in exact §4.1 column order, guarded metrics = `None`.
    `spot_states` one/underlying; `option_strike_metrics` one/active option; (P4b) `strike_window_metrics`
    one per `(symbol,w)`; `aggregated_window_metrics` one per `(underlying,strike_window)`. `recorder_meta`
    provenance is the writer's job.
39. **Timeline continuity (§6.2) + degraded mode (§5.1) — the grid is sacred.** Per-symbol last-`recv_ts`;
    gap > `staleness_timeout_sec` → NULL/NaN row (`confidence=0.0`), keep the second; else forward-fill.
    History deques start empty each start/restart → dependent columns NULL until filled (documented warm-
    up). Degraded reads `proc_queue`/`db_queue` `qsize()` each second: ≥ warn → skip heavy rolling (P4b:
    slopes, wall-score median, quote stability, velocity/accel, churn/flow) → NULL, **1s cadence
    unchanged**; ≥ critical → shed oldest cached ticks for least-active symbols (counted+logged). Uniform
    1s grid **never** varies. `db_queue.put(timeout)` on Full → `db_rows_dropped_total` + WARNING (sheds
    second, after proc, before the protected raw path).
40. **NULL/guard matrix from registry `min_depth` + spec caveats.** NULL when `L<min_depth`; `orders==0`
    → NULL (M13/M14); `feed_time` absent/0 → M23 + its M24 freshness term NULL/0; `tick_size` unknown →
    M29 NULL; side can't absorb `fill_probe_qty` within `L` → M25's four values NULL; `<2` non-zero non-
    wall levels → M21 NULL; (P4b) `<2` valid micro-price returns → RV NULL; post-restart boundary second
    → OFI NULL (not 0); crossed/`spread≤0` → CRITICAL log (M1), value still recorded.
41. **M22/M24 touch-history deque is P4a engine infra.** M22 (quote stability)/M24 (confidence) are
    `option_strike_metrics` columns but need a short per-strike history (touch price + Top5-OBI); P4a
    builds that per-symbol deque (reused by P4b's §3.4.3 window table). The **`ofi` column** is §3.4.3-E
    rolling machinery (price-aligned `t-1` touch) → deferred to **P4b**; NULL in P4a rows.

**Concurrency ownership:** *thread owner* = the single `TickProcessor` thread (`run()`); P7 replay calls
`emit_second()` synchronously (no thread). *State owner* = that same thread (no lock — single owner).
*FD owner* = none (only in-memory queues/arrays/deques; P4 adds zero FD surface).

### P4a subtask checklist — engine + per-strike M1–M29 (embedded 2026-07-03; ✅ complete 2026-07-03)
- [x] **A1 · `registry.bind()` + `resolve_active()`** — `bind(name)` decorator (unknown-name fast-fail;
  sets `METRIC_FUNCS`) + `resolve_active(live_metrics|"all")` returning the ordered active spec set +
  persisted output columns. Frozen `MetricSpec` metadata unchanged.
- [x] **A2 · `BookSnapshot`** (`__slots__`, decision 35) — parse `depth.buy/sell` → per-side NumPy
  `price/qty/orders` once; `L_bid/L_ask`, touch scalars, decay `w_i` (reuse `utils` factory), mid/micro
  helpers; malformed/empty book → NULL-yielding snapshot (never raises).
- [x] **A3 · `metrics/per_strike.py` — M1–M29** bound to specs (decisions 31/32/40) — vectorized NumPy
  per §3.4.2 incl. corrections: mid-centered M11, non-zero-median M21, ±band M15, `orders==0→NULL`
  M13/M14, VAMP M27→M4 at L=1, M23 from `feed_time`, M25 depth-guard + Kyle-λ, M29 tick_size guard,
  M4/M26 touch. M22/M24 consume the A5 deque. Each returns column(s) or `None` under guard. (`ofi` NOT
  here — P4b.)
- [x] **A4 · `TickProcessor` thread + resample loop** (decisions 33/34/36/38/39) — `__init__(config,
  instrument_manager, proc_queue, db_queue, shutdown_event, *, time_fn, active_metrics, name)`; `run()`
  drains + classifies → updates `latest_ticks`/spot cache, and on each aligned 1s boundary calls pure
  `emit_second(now)` → build snapshots, run per-strike, forward-fill/staleness, emit `spot_states` +
  `option_strike_metrics` envelopes. Graceful drain on `shutdown_event`.
- [x] **A5 · Per-symbol history deque + spot/ATM cache** (decision 41) — per-strike deque
  (maxlen=`max(time_windows_sec)`) of touch price + Top5-OBI for M22/M24 (reused by P4b); per-underlying
  spot cache + `K_ATM` from `active_strikes_list` for `spot_states.atm_strike`.
- [x] **A6 · Degraded-mode + shedding skeleton** (decision 39) — `qsize()` watermarks; least-active shed
  at critical; counters (`ticks_shed_total`, `db_rows_dropped_total`, `unknown_symbol_total`) exposed for
  the P6 health file. (Heavy-skip set wired in P4b when those metrics exist.)
- [x] **A7 · Tests** `tests/test_processor.py` + `tests/test_metrics_per_strike.py` (offline, injected
  clock/queues) — hand-computed M1–M29 fixtures (+ each correction/guard); L=5 fallback NULLs; `orders==0`
  / `feed_time` absent / `tick_size` unknown / M25 thin-book → NULL; staleness → NULL row +
  `confidence=0.0`, grid preserved; forward-fill; M22/M24 warm-up NULLs; `spot_states` ATM; thin-subset
  vs `all`; degraded shed keeps cadence; `emit_second` determinism under a virtual clock (P7 seam).
- [x] **A8 · Docs** — new `Documents/processor.md` + `Documents/metrics.md` (P4a scope); update
  `ARCHITECTURE.md` (P4a built state + processor in topology) + dated `CHANGELOG.md`; cite
  §3.4.1/§3.4.2/§5.1/§6.2.
- [x] **A9 · Config add** — `metrics.fill_probe_qty` in `config.yaml` (annotated) + `config.py` §7.3
  validation (positive) + a test. Needed by M25.
- [x] **A10 · Completion audit** — full `pytest` green; `--validate-config`→0 incl. `fill_probe_qty`; FD
  audit (processor holds none); concurrency audit (single-owner, no lock, no I/O off queues);
  genericization (no index/exchange/step/CE-PE literal — CE/PE from maps, ranges from config, keyed by
  `name`); invariants (uniform-1s grid in degraded mode; never writes raw; db-shed counted). Docs
  current. **← stop for approval before P4b.**

*Critical files (P4a):* **new** `processor.py`, `metrics/per_strike.py`, `tests/test_processor.py`,
`tests/test_metrics_per_strike.py`, `Documents/processor.md`, `Documents/metrics.md`; **edit**
`metrics/registry.py` (`bind()`+`resolve_active()`), `metrics/__init__.py`, `config.yaml` + `config.py`
(`fill_probe_qty`), `Documents/{ARCHITECTURE,CHANGELOG}.md`; **reuse** `config.py`, `utils.py`,
`instrument_manager.py`, `metrics/registry.py`, `tests/conftest.py`. `numpy~=2.4.4` pinned (P0).

*P4a completion (2026-07-03):* full `pytest market_depth_recorder/tests/ -q` **130 passed** (98 prior +
32 new); `--validate-config`→0 good / →1 on seeded-bad `fill_probe_qty`; **FD audit** — processor holds
**no** files/sockets/DB/subprocess (only queues/arrays/deques), the one thread is joined by tests/P6;
**concurrency audit** — single-owner state, no lock, cross-thread edges are only the two thread-safe
queues; **genericization** grep clean (no NIFTY/SENSEX/NFO/BFO/NSE_INDEX/CE-PE functional literal in
`processor.py` or the metric modules — CE/PE from `symbol_to_strike_map`, steps/ranges from config, state
keyed by `name`; `:50` = cited `_TBT_SUFFIX`). Two minor refinements recorded as decision 42.
**← stopping for approval before P4b.**

42. **Two P4a implementation refinements** (2026-07-03): (a) `BookSnapshot`/`MetricContext`/`StrikeHistory`
    live in **`metrics/snapshot.py`** (not `processor.py`) to avoid a `processor`↔`metrics` circular
    import — the compute modules import them without importing the engine. (b) M22 (quote stability) /
    M24 (confidence) are per-second `option_strike_metrics` columns whose §3.4.2 "rolling window" is
    under-specified; P4a uses the **shortest** `time_windows_sec` (most responsive) as their window, via
    `MetricContext.stability_window` — documented in `metrics.md`/`processor.md`.

### Decisions taken during P4b planning (2026-07-03)
43. **Family-specific bound signatures.** Per-strike bodies stay `fn(snap, ctx)`. **Rolling** bodies are
    `fn(hist, n, ctx)` (`hist` = per-symbol `list[WindowSample]` oldest→newest; `n` = the window). **Aggregate**
    per-window bodies are `fn(ce_feats, pe_feats, ctx)`; `pinning_score`/`regime` are `fn(agg_view, ctx)`
    (cross-window). All bound via `bind()`; the engine dispatches by `spec.family`/name.
44. **P4b engine state (single-owner, no lock).** `self._window[clean]` = `deque[WindowSample]`
    (maxlen = `2·max(time_windows_sec)+1`, to reach `BP_{t-2N}` for acceleration at the largest window);
    `self._prev[clean]` = the prior second's compact top-10 price→qty per side + touch (price-aligned ΔQ +
    touch OFI); `self._features[clean]` = the current second's per-strike aggregate features. `WindowSample`
    lives in `metrics/snapshot.py`.
45. **Windowed liquidity split (spec §3.4.3-B ambiguity).** `liquidity_added`/`liquidity_removed` are the
    **window sums** of per-second ΔQ+/ΔQ- (not the last-second instantaneous value), so
    `book_churn = liquidity_added + liquidity_removed` with no per-window duplication. Per-second ΔQ± come
    from the price-aligned **union of top-10 prices** vs the prior second; a second with book <10 levels or
    no prior contributes `None` (skipped from the window sums / flow_intensity).
46. **Per-underlying regime + pinning repeated across window rows.** `pinning_score` (max SMALL wall / mean
    LARGE wall) and `regime` (§3.4.4-C: LARGE-window NOP/Bnet + SMALL pinning + spread/stability) are single
    per-underlying-per-second scalars, written **identically into all three** `aggregated_window_metrics`
    rows (SMALL/MEDIUM/LARGE); `depth_pcr`/pressures/`bnet`/`spread_diff`/NOP vary per window. `regime.theta_*`
    are read from config and still need operator re-tuning to the rescaled M11 book-pressure magnitude
    (§3.4.2 M11 note) — config tuning, not engine logic.
47. **Rolling `min_depth` inherited via `None` inputs.** Deep-book rolling metrics (slopes, liquidity flow,
    velocity/accel — registry min_depth 10) inherit the guard from their per-second inputs: a shallow/stale
    second yields `None` for `book_pressure`/ΔQ, and the window body NULLs when it has <2 valid points (or a
    required lag point is `None`). No separate depth check inside the window bodies.

### P4b subtask checklist — rolling windows + aggregates + regime (embedded 2026-07-03; ✅ complete 2026-07-04)
- [ ] **B1 · `metrics/rolling.py` — §3.4.3** — reuse/extend the A5 deque; per window `w∈{5,10,30}`:
  price_return, spread stats, wobi mean/std, regression slopes, micro-price RV, price-aligned liquidity
  added/removed + churn + flow_intensity (union-of-prices), pressure velocity/accel, wall persistence +
  created/destroyed, instantaneous OFI (→ `option_strike_metrics.ofi`) + windowed `ofi_sum`; warm-up +
  boundary OFI NULL. Emit `strike_window_metrics`; back-fill the `ofi` column.
- [ ] **B2 · `metrics/aggregate.py` — §3.4.4 + regime** — once/sec/underlying: `K_ATM`; SMALL/MEDIUM/LARGE
  windows from config + step; depth PCR (both-sides), CE/PE pressures, pooled `B_net∈[-2,2]`, spread_diff,
  NOP, pinning_score; regime (§3.4.4-C). Consumes per-strike outputs (decision 37); emit
  `aggregated_window_metrics`.
- [ ] **B3 · Processor wiring** — extend `emit_second` to per-strike → rolling → aggregate → regime;
  complete the degraded heavy-skip set; wire `ofi` back-fill + the two new envelopes.
- [x] **B4 · Tests** `tests/test_metrics_rolling.py` (rolling bodies + OFI/ΔQ helpers) +
  `tests/test_metrics_aggregate.py` (per-window bodies + regime labels + `compute_underlying`
  orchestrator) + P4b integration in `tests/test_processor.py` — price-aligned add/remove across a
  shifting book, slopes, RV with a skipped stale second, OFI sign + boundary NULL, wall persistence/
  events; ATM/window grouping, both-sides PCR, pooled `B_net` window-invariance, all five regime labels;
  dependency closure; degraded NULLs heavy + keeps cadence; full `emit_second` determinism under a virtual
  clock. **158 passed.** Also fixed two pre-existing tests exposed by this run: the P4a
  `test_emit_produces_spot_and_option_envelopes` now tolerates the two new P4b tables (subset + qsize ==
  table count); and the P2 `test_write_error_counted_and_thread_survives` was **date-dependent** — it used
  the real clock so the defensive IST rollover fired once the calendar rolled past its hardcoded
  `session_date` (2026-07-03 → -04), consuming the FakeHandle's one failing write on the EOF marker; fixed
  by injecting the existing fixed `Clock()` (the design's inject-the-clock rule).
- [x] **B5 · Docs** — extended `metrics.md` (rolling.py + aggregate.py sections + P4b snapshot dataclasses)
  + `processor.md` (four-table pipeline, rolling/aggregate wiring, dependency closure, heavy-skip degraded,
  new config keys) + `ARCHITECTURE.md` (P4a+P4b built state, all four tables emitted, topology-after-P4b)
  + dated `CHANGELOG.md` (2026-07-04 P4b entry); cite §3.4.3/§3.4.4.
- [x] **B6 · Completion audit** — full `pytest market_depth_recorder/tests/ -q` **158 passed** (no live
  feed); `--validate-config`→0 (config_hash stable); **FD audit** — processor + rolling + aggregate hold
  **no** files/sockets/DB/subprocess (only in-memory deques/dicts/NumPy arrays), zero new FD surface;
  **concurrency** — all P4b state (`_window` deques, `_prev` touch-books) owned by the single `run()`
  thread, no lock, cross-thread edges only the two thread-safe queues; **genericization** grep clean (no
  NIFTY/SENSEX/NFO/BFO/NSE_INDEX literal in rolling/aggregate/processor/snapshot — CE/PE from the
  InstrumentManager map's `option_type`, windows/radii/thresholds from config, all state keyed by `name`);
  **invariants** — uniform 1s grid preserved in degraded mode (heavy metrics NULL, row still emitted),
  boundary/warm-up NULLs (OFI/price_return), lossless-raw path untouched. Docs current. **← stop for
  approval before P5.**

*Critical files (P4b):* **new** `metrics/rolling.py`, `metrics/aggregate.py`,
`tests/test_metrics_rolling.py`, `tests/test_metrics_aggregate.py`; **edit** `processor.py`,
`metrics/__init__.py`, `Documents/{metrics,processor,ARCHITECTURE,CHANGELOG}.md`; **reuse** everything
P4a built.

- **Tests (both):** deterministic hand-computed metric fixtures; staleness/NULL padding; degraded mode
  keeps cadence; boundary-second OFI NULL after restart; `emit_second` determinism (P7 seam).

## P5 — SQLite live writer (`database_writer.py::SQLiteLiveWriter`)

**Scope:** the fourth and final **live thread** — the batching consumer that drains `db_queue` (the
envelopes P4 already emits, currently unread — `db_queue` has no reader yet) and commits the
`recorder.live_metrics` subset to the thin Tier-1 SQLite/WAL store (`market_depth_live_YYYYMMDD.db`).
Closes the live path end-to-end (feed → tee → processor → **DB**); the raw audit path (P2) already
terminates. After P5 the only unbuilt live piece is the P6 orchestrator. Pure `db_queue` consumer +
one SQLite connection — **no sockets, subprocess, or compute** — fully testable offline (temp DB via
`tmp_path`, injected clock, in-memory `db_queue`). Authoritative: **spec §3.6.1–§3.6.4**
(thread/batch/PRAGMA/DB-selection/teardown), **§4.1** (DDL), **§4.1b** (`recorder_meta`), **§4.2**
(indexes), **§4.3** (`WITHOUT ROWID` + insert semantics), **§4.4** (checkpoints/optimize/no-VACUUM),
**§6.3** (corruption recovery), **§5.1** (`db_queue` backpressure — producer side, built in P4).

**Verified data contract (read from built P4 code, 2026-07-04):**
- *Input* (`db_queue`, from `TickProcessor._push`): one envelope per table per second,
  `{"table":<name>,"rows":[tuple,…]}`; tuples in **exact §4.1 column order**, guarded metrics `None`.
  The four table names + column tuples are the authoritative order:
  `processor.SPOT_COLUMNS`(4)/`OPTION_COLUMNS`(47 incl. `ofi`)/`STRIKE_WINDOW_COLUMNS`(23)/
  `AGG_COLUMNS`(11). DB `symbol` has **no `:50`** (processor already stripped it).
- *Config keys* (present; `database` exposed as `config.database` MappingProxy like `file_writer`):
  `database.{batch_size=500,batch_write_interval_ms=1000,cache_size_mb=64,
  wal_checkpoint_interval_sec=600}`, `recorder.output_dir`, `config.config_hash`, `SCHEMA_VERSION`(=1).
  Only `batch_write_interval_ms` is range-validated → P5 adds the other three (fork B).
- *Threading template* = `file_writer.py::RawTickFileWriter`: `threading.Thread` subclass, FD opened
  **inside `run()`**, single-owner, no lock; `run()` = try→open→(try consume→final flush→finally
  close)→except report to `error_queue`. P5 mirrors this with a `sqlite3.Connection` as the FD.

### Forks resolved (2026-07-04)
- **A. Boundary-second `INSERT OR REPLACE` → DEFERRED to P6** (user-accepted). P5 ships steady-state
  `INSERT OR IGNORE` + count/log (§4.3 choice b) and exposes `mark_restart_boundary(ts)` that flips the
  next commit spanning `ts` to `INSERT OR REPLACE` (§4.3 choice a), then reverts. **P6 drives the hook**
  (see the amended P6 section). P5 unit-tests the hook directly — no orchestrator needed.
- **B. Add §7.3 validation NOW** for `batch_size`, `cache_size_mb`, `wal_checkpoint_interval_sec`
  (fast-fail contract, like P4a's `fill_probe_qty`).
- **C. Deferred `DuckDBAnalyticalWriter` stub NOW** in `database_writer.py` — raises
  `NotImplementedError("built in P7")` at construction (mirrors P3's `SdkTransport` stub).

### Decisions taken during P5 planning (2026-07-04)
48. **Single-owner connection, no lock, opened in `run()`.** The `sqlite3.Connection` is created,
    PRAGMA-tuned, DDL-initialized, written, checkpointed, and closed **only** by the writer thread's
    `run()` (thread affinity + single-owner, like P2's gzip handle). No DB lock; `check_same_thread=True`
    (default) is correct. Cross-thread edge = only the thread-safe `db_queue` (in). **FD owner = this one
    thread**; connection closed on every path (clean drain, corruption rebuild, exception, shutdown).
49. **Column order reused from `processor.py`** (single source of truth). `database_writer` imports
    `SPOT_COLUMNS`/`OPTION_COLUMNS`/`STRIKE_WINDOW_COLUMNS`/`AGG_COLUMNS` and derives each `INSERT` +
    `?`-count from them, so SQL can never drift from the emitted tuple order (no cycle — `processor`
    doesn't import `database_writer`). DDL strings (CREATE TABLE + indexes + `recorder_meta`) are module
    constants in `database_writer.py`, transcribed verbatim from §4.1/§4.1b/§4.2.
50. **Injected clock + session date** (`time_fn=time.time`, `session_date: date`) — sole source of the
    checkpoint/commit cadence, `recorder_meta.build_time`, and the §3.6.3 date-mismatch guard. Filename
    `market_depth_live_YYYYMMDD.db` resolved once from `session_date` into `recorder.output_dir` (mirrors
    `RawTickFileWriter.resolve_filename`).
51. **Batch flush = size OR time** (§3.6.1). Per-table buffers; commit when total buffered rows ≥
    `database.batch_size` OR `database.batch_write_interval_ms` elapsed since last commit. One
    `BEGIN`/`executemany`-per-nonempty-table/`commit`; on `sqlite3.Error` rollback + log, batch dropped-
    with-count (no poison-batch retry — the fat store rebuilds from raw). PK-collision drops counted via
    `total_changes` delta + WARNING.
52. **`recorder_meta` stamped once at DB creation** (§4.1b): one row `built_by="live"`, `source_raw=NULL`,
    `schema_version=SCHEMA_VERSION`, `config_hash=config.config_hash`, `build_time=int(time_fn())`. Written
    only when the DDL runs (fresh/rebuilt DB); not re-stamped on a same-day reopen.
53. **PASSIVE checkpoint on a time cadence** (§4.4): every `wal_checkpoint_interval_sec` (via `time_fn`)
    the loop runs `PRAGMA wal_checkpoint(PASSIVE)`. **Teardown reconciliation:** §4.4 (authoritative over
    §3.6.4's shorter list) — teardown runs `PRAGMA wal_checkpoint(TRUNCATE)` **then** `PRAGMA optimize`,
    **no VACUUM**.
54. **Corruption recovery on open** (§6.3): after connect run `PRAGMA quick_check`; on any failure or
    `sqlite3.DatabaseError` → close → archive `.db`(+`-wal`/`-shm`) to `.corrupt_<epoch>.bak` → fresh DB +
    DDL + indexes + `recorder_meta` → CRITICAL log. A brand-new daily file passes trivially. `shutil`
    only; no OS syslog. Live-store corruption is non-fatal (fat store rebuilds from raw).
55. **Counters for the P6 health file:** `rows_written`, `rows_ignored_total` (PK collisions),
    `commit_error_count`, `corruption_recoveries` (thread-local). `db_rows_dropped_total` stays
    producer-side (P4). P5 never touches the raw path and never blocks the tee.

### FD structure (close on EVERY path)
```
run():
  try:
    self._open_db()            # connect → quick_check → (recover if bad) → PRAGMA → DDL-if-new → recorder_meta
    try:
      self._consume_loop()     # drain db_queue: buffer → flush on size/time → periodic PASSIVE checkpoint
      self._final_flush()      # commit remaining buffered rows on clean drain
      self._teardown_pragmas() # wal_checkpoint(TRUNCATE) + optimize
    finally:
      self._close_db()         # commit-safe close; idempotent; guards None/closed conn
  except Exception:
    logger.exception("SQLiteLiveWriter crashed")   # + error_queue.put (P6 hook)
```
A mid-loop crash still closes the connection in `finally`; buffered-uncommitted rows are lost from the
live store only (raw intact → rebuildable). A mid-session `DatabaseError` triggers §6.3 archive+rebuild.

### P5 subtask checklist (embedded 2026-07-04; ✅ complete 2026-07-04)
- [x] **A · Module skeleton + DDL constants** — `database_writer.py` docstring (§3.6/§4 + FD ownership +
  genericization); `SQLiteLiveWriter(threading.Thread)` constructor (decision 48/50); DDL module
  constants (4 tables §4.1 + 4 indexes §4.2 + `recorder_meta` §4.1b) verbatim; import the four column
  tuples from `processor` (decision 49); precompute per-table `INSERT OR IGNORE`/`OR REPLACE` + counts.
- [x] **B · `resolve_filename` + `_open_db`** — `market_depth_live_YYYYMMDD.db` from `session_date`;
  `sqlite3.connect`; `PRAGMA quick_check` → §6.3 recover-if-bad; PRAGMA tuning (§3.6.2: WAL,
  `synchronous=NORMAL`, `temp_store=MEMORY`, `cache_size=-cache_size_mb*1000`); create
  tables+indexes+`recorder_meta` only if new/rebuilt (decision 52); init `last_checkpoint`/`last_commit`.
- [x] **C · `_recover_corrupt_db`** (§6.3, decision 54) — close → archive `.db`/`-wal`/`-shm` →
  `.corrupt_<epoch>.bak` → fresh connect + DDL + `recorder_meta` → CRITICAL log; bump `corruption_recoveries`.
- [x] **D · Buffer + flush engine** (§3.6.1, decision 51) — per-table buffers; `_buffer(env)` dispatch by
  `env["table"]`; `_maybe_flush()` on size/time; `_commit()` = one txn, `executemany` per nonempty table,
  count PK-collision ignores via `total_changes` delta (WARNING), rollback+log on `sqlite3.Error`.
  `mark_restart_boundary(ts)` hook (fork A) → next commit spanning `ts` uses `INSERT OR REPLACE`, reverts.
- [x] **E · Checkpoint + teardown** (§4.4, decision 53) — periodic `wal_checkpoint(PASSIVE)`;
  `_teardown_pragmas` = `wal_checkpoint(TRUNCATE)` + `optimize` (no VACUUM); `_close_db` idempotent/guarded.
- [x] **F · Thread loop** — `run()` per the FD structure; `_consume_loop` drains until `shutdown_event`
  set AND `db_queue.empty()` (mirrors P2); `get(timeout=1.0)` + `task_done()`; unknown-table envelope
  counted+logged, never crashes; defensive date-mismatch guard (§3.6.3) → final flush + reopen new DB.
- [x] **G · Deferred DuckDB stub** (fork C) — `class DuckDBAnalyticalWriter` raising
  `NotImplementedError("DuckDBAnalyticalWriter is built in P7")` at construction.
- [x] **H · Config validation** (fork B) — §7.3 rules in `config.py`: `batch_size` ∈ [1,5000];
  `cache_size_mb ≥ 1`; `wal_checkpoint_interval_sec ≥ 30` (per §7.2); annotate `config.yaml`; a negative
  test per rule.
- [x] **I · Tests** `tests/test_database_writer.py` (offline; `tmp_path` DB + injected clock + in-memory
  `db_queue`): DDL creates 4 tables+indexes+`recorder_meta`; provenance row correct; round-trip all four
  envelope tables → rows in §4.1 column order, `None`→NULL; batch flush by **size** and by **time** (spied
  clock); PK-collision `OR IGNORE` counts+logs, no dup; `mark_restart_boundary` → `OR REPLACE` overwrites
  boundary second; PASSIVE checkpoint cadence (spied); teardown TRUNCATE+optimize + clean close;
  **corruption recovery** (garbage bytes → `quick_check` fails → archive `.corrupt_*.bak` + rebuilt DB +
  `recorder_meta`); graceful drain via a real thread; unknown-table envelope ignored+counted. No live feed.
- [x] **J · Docs** — new `Documents/database_writer.md`; update `ARCHITECTURE.md` (P5 built state — all
  four live threads present, `db_queue` now consumed, topology-after-P5) + dated `CHANGELOG.md`; cite
  §3.6/§4/§6.3.
- [x] **K · Completion audit** — full `pytest` green (158 + new); `--validate-config` →0 (incl. three new
  keys) / →1 per seeded-bad key; **FD audit** (one `sqlite3.Connection` opened in `run()`, closed on every
  path incl. corruption-rebuild/exception/shutdown/date-rollover; archive closes old conn first; DuckDB
  stub holds nothing); **concurrency audit** (single-owner conn, no lock, only edge is `db_queue`, counters
  thread-local); **genericization** grep clean (table/column names are schema constants, symbols flow from
  envelopes — no index/exchange/strike/CE-PE literal); **invariants** (raw path untouched; live-store
  corruption non-fatal; no VACUUM). Docs current. **← stop for approval before P6.**

*Critical files:* **new** `database_writer.py`, `tests/test_database_writer.py`,
`Documents/database_writer.md`; **edit** `config.py` + `config.yaml` (three validation rules) +
`tests/test_config.py`, `Documents/{ARCHITECTURE,CHANGELOG}.md`; **reuse** `processor.py` (column
tuples), `config.py`, `utils.py`, `__init__.py` (`SCHEMA_VERSION`), `file_writer.py` (threading pattern),
`tests/conftest.py`. Dependency `sqlite3` (stdlib — no new pin).

*P5 completion (2026-07-04):* full `pytest market_depth_recorder/tests/ -q` **175 passed** (158 prior + 14
new writer + 3 new config); `--validate-config` →0 good / →1 with the exact message on each seeded-bad
`batch_size`/`cache_size_mb`/`wal_checkpoint_interval_sec`. **FD audit** — one `sqlite3.Connection` opened
in `run()` and closed in `run()`'s `finally` on every path (clean/exception/shutdown/corruption-rebuild/
date-rollover); `run()` was **hardened** so a *partial* `_open_db` (connect succeeds, PRAGMA/DDL raises)
still closes its FD — the one real issue the audit caught; corruption recovery closes the bad conn before
reconnecting; DuckDB stub holds nothing. **Concurrency audit** — single-owner connection + state, no lock;
cross-thread edges only the thread-safe `db_queue` and the atomic single-word `mark_restart_boundary`
hand-off (documented for P6). **Genericization** grep clean (no NIFTY/SENSEX/NFO/BFO/NSE_INDEX/CE-PE
functional literal in `database_writer.py` — only a doc-comment mention; table/column names are §4 schema
constants). **Invariants** — raw path untouched; live-store corruption non-fatal (rebuilds from raw); no
VACUUM; batch cadence honors size-or-time. Docs current. **← stopping for approval before P6.**

*Test-caught behavior (fixed in the test, not the code):* `test_graceful_drain_via_real_thread` initially
tripped the defensive IST rollover because the injected clock's epoch mapped to a different IST date than
`session_date` — anchored the test clock to noon-IST on `SESSION_DATE` per the design's inject-the-clock
rule (same class as the P2/P4b date-dependent fixes). No production code changed for it.

## P6 — Orchestrator (`main.py`)

**Scope:** the final live module — the conductor. P0–P5 built every worker as a standalone, tested
thread; **nothing yet constructs, wires, supervises, or tears the pipeline down.** P6 is that missing
piece: `main.py` → `RecorderOrchestrator`, the `default` (no-mode) CLI entrypoint (`__main__.py:166`
stub today), owning the milestone state machine + 1 s loop, the 3 queues / `shutdown_event` /
`error_queue`, construction+start+supervision+teardown of all four threads, mid-day-restart recovery,
the health-file writer, session guards (disk + trading calendar), and the M6 reprocess subprocess
launcher. It implements `--status`. After P6 the only unbuilt module is P7 (replay/DuckDB).
Authoritative: **§3.1** (§3.1.1 milestones, §3.1.2 restart, §3.1.3 supervisor, §3.1.4 teardown, §3.1.5
guards), **§6.4** (health + supervision), **§8.2/§8.6** (CLI + reprocess), **§3.5.4/§4.1b** (provenance
via clean EOF).

**Verified wiring contract (read from built P0–P5, 2026-07-04):**
- **Queues are caller-created + injected** (plain `queue.Queue`): `raw_file_queue` (cap
  `queues.raw_file_queue_max`, sheds **last**), `proc_queue` + `db_queue` (cap `queues.max_queue_size`).
  One shared `shutdown_event: threading.Event` in every constructor; loop = drain-then-exit.
- **Thread constructors:** `RawTickFileWriter(config, raw_file_queue, shutdown_event, session_date, *,
  time_fn, error_queue, …)`; `SQLiteLiveWriter(config, db_queue, shutdown_event, session_date, *,
  time_fn, error_queue, …)`; `TickProcessor(config, im, proc_queue, db_queue, shutdown_event, *, time_fn,
  active_metrics, …)`; `DepthWebSocketClient(config, im, raw_file_queue, proc_queue, shutdown_event, *,
  time_fn, sleep_fn, transport, …)`.
- **Shutdown:** setting `shutdown_event` drains the three consumers; the **feed** also needs
  `client.stop()` (sets event + force-closes transport) to break its blocking `run_session()`.
- **`error_queue` asymmetry:** raw + db writers report `(name, repr(exc))` on crash; **processor + feed
  do not** → supervision keys on `is_alive()` (catches any death); `error_queue` only enriches the log.
- **Counters for health:** feed `raw_dropped_total`/`proc_dropped_total`/`current_spot_prices`/
  `active_subscriptions`(prop); processor `stats()`; writer `rows_written`/`rows_ignored_total`/
  `commit_error_count`/`corruption_recoveries`; raw `records_written`/`write_error_count`. Static
  `resolve_filename(output_dir, d)` on both file/db writers.
- **InstrumentManager:** `resolve()` blocking-once, maps keyed by `name`. **`RestClient` has
  get_instruments/get_expiry but NO get_quote.**
- **Gaps P6 must fill in P1/P3 (small, additive):** no `RestClient.get_quote`; feed has **no** public
  spot-seed entry, no connection-status flag, no per-underlying `actual_depth`, no `last_recv_ts`.
- **Config keys all present** (P0-validated); **no milestone-time keys** (init/connect) exist.

### Forks resolved (2026-07-04, user)
- **Fork 1 — mid-day-restart ATM seed:** **add `RestClient.get_quote`** (spec-faithful §3.1.2), with
  WS-spot-tick lazy seed as the documented fallback.
- **Fork 2 — pre-open milestone timing:** **init+connect at launch, record-gate at `session_start`**
  (rec) — no new milestone-time config keys; this also *is* the §3.1.2 in-window restart path.
- **Fork 3 — worker crash policy:** **in-process supervisor restart** (§3.1.3), bounded → fail-fast.
- **Fork 4 — M6 reprocess launcher:** **build now**, tested against a stub command (P7 fills the replay).

### Decisions taken during P6 planning (2026-07-04)
56. **Milestone model = act-at-launch, record-gate at `session_start`** (fork 2). On process start:
    **Init** (resolve chains) → **Connect** (construct feed, `client.start()`, spot LTP `mode=1` subs)
    immediately, regardless of wall time. **Record** begins when `now_ist() ≥ session_start` (DSM enabled
    → option subs flow from spot ticks). **Close** at `session_end` (freeze DSM). **Teardown** at
    `session_end + teardown_grace_min`. **Reprocess** after a clean EOF. No new milestone-time keys; the
    spec's 09:00/09:10 fixtures become "as soon as the scheduler launches us," which also **is** the
    §3.1.2 in-window restart path (no separate M1/M2 skip).
57. **Mid-day-restart ATM seed via new `RestClient.get_quote`** (fork 1). If `session_start ≤ now <
    session_end`, POST `/api/v1/quotes {apikey,symbol,exchange}` per underlying (spot symbol+exchange) →
    `data.ltp` → `client.seed_spot(name, ltp)` so DSM resolves ATM + subscribes strikes immediately.
    **Needs a live broker session; on any quote failure → WARNING + fall back to the lazy WS spot-tick
    seed** (P3 decision 25). The overlap second is flagged with `db_writer.mark_restart_boundary(ts)`
    (P5 hook) → that one commit uses `INSERT OR REPLACE` (freshest recompute wins), then reverts.
58. **In-process supervisor restart** (fork 3). A tick every `recorder.supervisor_interval_sec`
    (default 5) scans all four `is_alive()` + drains `error_queue`. On any dead thread / error item **in
    the record window**: log ERROR (with error-queue detail if present), set `shutdown_event` +
    `client.stop()`, **join all (bounded 10 s each)**, then rebuild fresh queues+event+threads and
    re-enter the record-start path (= restart-recovery: REST-quote ATM seed + `mark_restart_boundary`).
    Bounded to `recorder.max_restart_attempts` (default 3) consecutive failures w/ backoff → **fail-fast**
    exit non-zero (OS supervisor takes over; never a tight crash-loop). Old thread/queue objects are
    joined+dropped before new ones are created (no thread/queue/FD leak across a restart).
59. **Build the M6 reprocess launcher now** (fork 4). `subprocess.Popen([sys.executable, "-m",
    "market_depth_recorder", "--replay", "--catchup", "--config", <path>])`, **detached**, stdout+stderr
    → `open(reprocess.log_file, "a")` (**a real file, never `PIPE`** — FD-hygiene), guarded by
    `reprocess.lock_file` (exclusive create; stale detection by pid/age), **`.wait()`-reaped**. Gated on
    `reprocess.auto_on_session_end` **AND** a **clean EOF** (raw drained + valid EOF marker). Tested
    against a stub command so P6 CI needs no P7 replay body. Unclean teardown → skip; OS-scheduled
    `--catchup` (§8.6 mode 2) covers it.
60. **Two-signal teardown, spec drain order** (§3.1.4). `session_end` → `client.freeze_dsm()` (stop
    boundary expansion; **no unsubscribe — never-shrink holds**, feed keeps delivering final ticks through
    the grace window). At `session_end + teardown_grace_min` → set `shutdown_event` + `client.stop()`;
    **join order `feed → processor → db_writer`, raw joined in parallel**; `join(timeout=10)` each. The
    processor fully drains `proc_queue` and flushes its final 1 s cycle into `db_queue` **before** the
    db_writer finishes — guaranteed by joining processor before db_writer. EOF/fsync/close happen inside
    each thread's own `run()` `finally` (already built P2/P5).
61. **Small additive touches to built modules** (kept minimal, each tested):
    - **P1 `instrument_manager.py`:** `RestClient.get_quote(symbol, exchange) -> float` (POST
      `/api/v1/quotes`, `apikey` in body, response closed on every path per the P1 pattern; `RestError`).
    - **P3 `websocket_client.py`:** public `seed_spot(name, price)` (thin wrapper over `_on_spot`),
      `freeze_dsm()` (flag checked in `_check_boundaries`), `connection_status` property (for health
      `websocket_status`), `last_recv_ts` attr (set in tee, for `last_raw_tick_time`), per-underlying
      `actual_depth` capture (first depth packet / preflight, for the §9 health map). Read-only exposure
      or one-line flags — no change to DSM/tee/reconnect; genericization unaffected (keyed by `name`).
62. **Health file** (§6.4 + §9). Main thread writes `recorder.health_file_path` every
    `health_write_interval_sec` via `utils.atomic_write`. Schema: `timestamp`, `state` (milestone),
    `session_date`, `config_hash`, `websocket_status`, `raw_file_queue_size`, `proc_queue_size`,
    `db_queue_size`, `last_raw_tick_time`, `active_contracts` (`len(active_subscriptions)`),
    `raw_dropped_total`, `proc_dropped_total`, `db_rows_dropped_total`, `degraded_level`, `actual_depth`
    (**per-underlying map**, §9 silent-50→5 alarm), plus writer/processor counters (`rows_written`,
    `rows_ignored_total`, `stale_rows_total`, `commit_error_count`, `corruption_recoveries`,
    `restart_count`). `--status` reads + pretty-prints this file (in `__main__.py`, replaces the stub;
    missing file → friendly "recorder not running" + exit 0).
63. **Session guards** (§3.1.5). Disk: at startup + every `disk_check_interval_sec`,
    `utils.free_disk_mb(output_dir) < min_free_disk_mb` → **ERROR** (non-blocking). Trading calendar: if
    `skip_non_trading_days` and today (IST) is a weekend or ∈ `trading_holidays` → one INFO line,
    idle-sleep the 1 s loop until the next day's session window (daemon is long-lived across days).
    Default `skip_non_trading_days: false` = always run.
64. **Config adds** (mirrors P4a `fill_probe_qty` / P5 batch keys — add validation now):
    `recorder.supervisor_interval_sec` (≥1, default 5) and `recorder.max_restart_attempts` (≥0, default
    3) in `config.yaml` (annotated) + §7.3 validation in `config.py` + a negative test each. `get_quote`
    reuses `openalgo.{host_server,api_key}` — no new key.

### Concurrency & FD ownership
- **Thread owner:** the main thread constructs, starts, supervises, and joins all four workers.
- **State owner:** each worker owns its state single-threaded (P6 adds no locks). The only cross-thread
  hand-offs P6 introduces are the thread-safe queues, `shutdown_event`, `error_queue`, and the atomic
  single-word `mark_restart_boundary(ts)` write (P5-documented).
- **FD structure (close/join on EVERY path):**
```
run_forever():
  while not stop:
    build queues + shutdown_event + error_queue + 4 threads
    start writers + processor, then feed; (restart path) REST-quote seed + mark_restart_boundary
    try:
      milestone loop (1s): record-gate → health write → disk guard → supervisor tick
    finally:
      shutdown_event.set(); client.stop()
      join feed → processor → db_writer (raw parallel), each join(timeout=10)   # threads close own FDs
    if crash and attempts < max: continue (rebuild)  else: break / fail-fast
  if clean EOF and auto_on_session_end: launch reprocess subprocess (log file, lock, wait-reap)
```
Health `atomic_write` uses a transient temp fd closed by the helper. The reprocess child's log file and
lock file are the only new persistent FDs — both explicitly closed/`.wait()`-reaped/lock-released. A
supervisor restart joins + drops old threads/queues before creating new ones (no leak).

### P6 subtask checklist (embedded 2026-07-04; ✅ complete 2026-07-05)
- [x] **A · `main.py` skeleton + `RecorderOrchestrator`** — docstring (§3.1/§6.4 + FD/concurrency +
  genericization); `Milestone` enum; injected `time_fn`/`sleep_fn` (+ `transport`/`rest_client`/
  `pipeline_factory`/`reprocess_launcher`/`loop_interval_sec`/`non_trading_poll_sec` seams) so every
  milestone/guard/supervisor branch is deterministic under test.
- [x] **B · Milestone state machine + 1 s loop** (decision 56) — act-at-launch Init→Connect; record-gate
  at `session_start`; freeze at `session_end`; teardown at `+teardown_grace_min`; reprocess after clean
  EOF; epochs from config via `parse_ist_hhmm` + `datetime.combine(session_date, …, tzinfo=IST)`.
- [x] **C · Queue/event/thread construction + start ordering** — `_build_default_pipeline` builds 3 sized
  queues + `shutdown_event` + **`db_shutdown_event`** + `error_queue`; constructs raw/db writers +
  processor + feed; starts consumers **then** feed. Reused by the supervisor restart via `pipeline_factory`.
- [x] **D · Mid-day-restart recovery** (decision 57) — in-window detection; `get_quote` per underlying →
  `feed.seed_spot`; `db_writer.mark_restart_boundary(overlap_ts)`; WARNING + WS-fallback on quote fail.
- [x] **E · P1/P3/P2 additive touches** (decision 61) — `RestClient.get_quote` + `IM.resolved`; feed
  `seed_spot`/`freeze_dsm`/`connection_status`/`last_recv_ts`/`actual_depth`; `RawTickFileWriter.eof_written`.
  Unit-tested in the existing P1/P3 test files (4 + 6 tests).
- [x] **F · Thread supervisor** (decision 58) — `supervisor_interval_sec` tick: `is_alive()` + drain
  `error_queue`; crash → teardown + rebuild + re-seed + resume; bounded `max_restart_attempts` w/ backoff
  → fail-fast non-zero; `restart_count` exposed for health.
- [x] **G · Teardown drain** (decision 60) — `freeze_dsm()` at `session_end`; **two-event** drain:
  `shutdown_event`+`stop()` → join `feed → processor` → set `db_shutdown_event` → join `db_writer` → join
  `raw`; `join(timeout=10)`. The separate db event guarantees the processor's final rows reach the writer.
- [x] **H · Health file writer + `--status`** (decision 62) — `build_health()` dict + `atomic_write` every
  interval; `read_status` reader/pretty-printer wired into `__main__.py` (`--status`; missing file → exit 0).
- [x] **I · Session guards** (decision 63) — startup + periodic disk check (ERROR); trading-calendar
  idle-until-next-trading-day (poll loop, interruptible via `stop()`).
- [x] **J · M6 reprocess launcher** (decision 59) — `Popen` (log file, not PIPE) + exclusive run lock
  (age-based stale-steal) + `.wait()`-reap; gated on `auto_on_session_end` + clean EOF; tested against a stub.
- [x] **K · Config adds + CLI wire** (decision 64) — `supervisor_interval_sec` (≥1) / `max_restart_attempts`
  (≥0) in `config.yaml` + `config.py` §7.3 + `conftest` + `test_config`; default (no-mode) CLI entry →
  `RecorderOrchestrator.run()`.
- [x] **L · Tests** `tests/test_main.py` (16, offline; virtual clock + fake workers via `pipeline_factory`
  + `RecordingEvent`) — milestone transitions + record-gate; full clean session (freeze + teardown +
  reprocess); teardown join order; supervisor restart-and-resume + bounded fail-fast; mid-day seed via
  mocked `get_quote` + boundary mark + WS fallback; low-disk ERROR; holiday idle; health schema + atomicity;
  `--status` present/missing; reprocess gating on clean EOF + lock acquire/release + disabled. Plus a
  scratch end-to-end smoke driving the **real** four-thread pipeline (no-op transport). No live feed/broker.
- [x] **M · Docs** — new `Documents/main.md`; updated `ARCHITECTURE.md` (P6 built state + two-event topology)
  + dated `CHANGELOG.md` + `instrument_manager.md` (`get_quote`/`resolved`) + `websocket_client.md`
  (`seed_spot`/`freeze_dsm`/status/`actual_depth`); cite §3.1/§6.4/§8.
- [x] **N · Completion audit** — full `pytest market_depth_recorder/tests/ -q` **203 passed** (175 prior +
  16 main + 4 `get_quote` + 6 WS + 2 config); `--validate-config`→0 incl. two new keys / →1 seeded-bad;
  `--status` prints; **FD/thread audit** — all four workers joined on every path (clean teardown,
  crash-restart, KeyboardInterrupt), no thread/queue leak across restart (old joined+dropped before
  rebuild), reprocess child → log file + `.wait()`-reap + lock release, `get_quote` response closed (shared
  `_request`), health temp fd closed by `atomic_write`; end-to-end smoke confirms **zero** threads left alive
  after a clean run; **concurrency audit** — main = supervisor, workers single-owner, two-event drain,
  `mark_restart_boundary` atomic hand-off, no I/O under any lock; **genericization** grep of `main.py`
  clean (underlyings from config, keyed by `name`); **invariants** — clean EOF gates M6, lossless raw
  untouched, drain order enforced, never-shrink until teardown (`freeze_dsm` no unsubscribe), uniform 1 s
  grid. Docs current. **← stop for approval before P7.**

*Two P6 refinements worth recording:* (a) **two shutdown events** (`shutdown_event` for feed·processor·raw,
`db_shutdown_event` for the db writer) instead of one — the spec's single-event drain has a race where the
db writer can observe the shared event set with `db_queue` momentarily empty (before the processor's final
push) and exit early; signaling the db writer only after the processor joins closes it, with no change to
any worker's code. (b) **Trading-calendar idle** is a poll loop that idles on a non-trading day and proceeds
on the next trading day (interruptible via `stop()`); one `run()` = one session, relying on the OS scheduler
to relaunch daily — documented in `main.md` (multi-day continuous looping is not a P6 goal).

*Critical files:* **new** `main.py`, `tests/test_main.py`, `Documents/main.md`; **edit** `__main__.py`
(default entry → orchestrator, implement `--status`), `instrument_manager.py` (`get_quote`) +
`tests/test_instrument_manager.py`, `websocket_client.py` (`seed_spot`/`freeze_dsm`/`connection_status`/
`last_recv_ts`/`actual_depth`) + `tests/test_websocket_client.py`, `config.py` + `config.yaml` +
`tests/test_config.py` (two keys), `Documents/{ARCHITECTURE,CHANGELOG,instrument_manager,websocket_client}.md`;
**reuse** all P0–P5 (`config`, `utils.{atomic_write,free_disk_mb,now_ist,parse_ist_hhmm,get_logger}`,
`instrument_manager`, `file_writer`, `websocket_client`, `processor`, `database_writer`, `tests/conftest`).
Deps: `subprocess`/`sys`/`json` (stdlib — no new pin).

*Verification:* full `pytest market_depth_recorder/tests/ -q` (no live broker/WS/market — simulated
clock drives all milestones; injected crash proves supervisor restart; mocked `get_quote` proves restart
seeding + boundary mark; stub cmd proves the reprocess launcher); `--validate-config`→0 incl. new keys;
`--status` pretty-prints `health.json` (degrades cleanly when absent); FD/concurrency/genericization/
invariant audit per subtask N. Live end-to-end + whole-pipeline FD audit is **P8**, not P6.

## P7 — Replay + DuckDB writer (`replay.py`, `database_writer.py::DuckDBAnalyticalWriter`)

**Scope:** the **offline** path — replay the lossless Tier-0 raw `.jsonl.gz` through the **same**
`TickProcessor` with the **full** metric catalog and bulk-load the fat Tier-2 **DuckDB** analytics store
(`market_depth_analytics_YYYYMMDD.duckdb`). Not a recovery tool — it is the normal way Tier 2 exists (the
P6 end-of-session reprocess already shells out to `--replay --catchup`; today that hits the P7 stub).
Replay is also the **determinism harness**: `--verify` re-runs the same processor and diffs the rebuild to
catch wall-clock/dict-order nondeterminism. Authoritative: **§8** (§8.1 guarantees, §8.2 invocation, §8.3
simulated clock, §8.4 verify, §8.5 idempotency, §8.6 trigger modes), **§3.6.5** (DuckDB bulk load), **§4.1a**
(DuckDB DDL), **§4.1b** (`recorder_meta`), **§6.2** (warm-up), **§3.4.1** (thin/fat).

### Forks resolved (2026-07-05, user)
- **Fork 1 — instrument context in replay → ENRICH THE RAW HEADER.** The processor needs each option's
  strike/option_type/`tick_size`; the raw HEADER today stores only underlying names, so a past-day replay
  can't rebuild them (REST returns today's rolled chain; reverse-parsing symbols is fragile — P1 never
  string-parses). Persist the resolved chain in the HEADER so replay is **self-contained and correct for
  any-age log** (upholds the §1.4 "raw is the reconstructable source of truth" invariant).
- **Fork 2 — replay clock basis → `recv_ts`.** Drive the 1s grid from each packet's `recv_ts` (the recorder
  clock the live resampler boundary AND staleness keyed off), reproducing live buckets/timestamps exactly.
  Spec §8.3 (which says feed_time/timestamp) gets a clarifying edit.
- **Fork 3 — DuckDB bulk load → `con.executemany`, no new dep.** Zero new dependency (standalone-venv
  promise); fine for a day's volume. (pandas is only transitively present/unpinned — not used.)
- **Fork 4 — verify scope → BOTH modes.** `--verify` (vs a prior DuckDB build) and `--verify-against-live`
  (live_metrics columns vs the SQLite live store).

### Decisions taken during P7 planning (2026-07-05)
65. **HEADER enrichment (fork 1).** `InstrumentManager.to_header_dict()` serializes the resolved chain (per
    underlying: `option_exchange, expiry, strike_step, contracts=[[strike, ce_sym, pe_sym, tick_size],…]`);
    the orchestrator passes that dict to `RawTickFileWriter`, which embeds it in the HEADER's `instruments`
    key. `InstrumentManager.from_header(config, header)` rebuilds all maps (`symbol_to_strike_map`,
    `strike_to_symbol_map`, `active_strikes_list`, `tick_size_map`, `chains`) with **no REST**. `file_writer`
    stays IM-agnostic (embeds a plain dict). Backward-compat: replay tolerates a HEADER without `instruments`
    (clear error for an old-day log; same-day may fall back to REST).
66. **recv_ts virtual clock (fork 2).** Replay advances a virtual clock from data-packet `recv_ts`, mirroring
    the live `run()` loop with `recv_ts` in place of `self._time()`. `emit_second(now_epoch)` is already pure
    w.r.t. the passed boundary (staleness = `ts − cell.recv_ts`), so buckets/timestamps match live. §8.3 clarified.
67. **Synchronous processor reuse, no thread, no processor change.** `replay.py` constructs the SAME
    `TickProcessor` with `active_metrics="all"`, an empty `proc_queue`, and an unbounded `db_queue`; per
    packet it calls `ingest(pkt)` then `while recv_ts ≥ next_b: emit_second(int(next_b)); drain db_queue →
    DuckDB writer; next_b += 1`. Draining each second bounds memory and keeps `_degraded_level`==0 (full
    catalog, no shedding). Add a thin public `TickProcessor.ingest(pkt)` over `_ingest` (additive; no logic change).
68. **`DuckDBAnalyticalWriter` = plain object (not a thread), `executemany` bulk (fork 3).** `with`-managed:
    open fresh `.duckdb` → `PRAGMA memory_limit`/`threads` from `analytics_db` → `_DUCKDB_DDL` (4 tables §4.1a
    + `recorder_meta`; DuckDB dialect BIGINT/DOUBLE/VARCHAR/BOOLEAN, no WITHOUT ROWID / WAL PRAGMA) →
    `write(envelope)` buffers per table → `finalize()` bulk `executemany` per table + stamp
    `recorder_meta(built_by="replay", source_raw=<raw filename>)` + `CHECKPOINT`; `__exit__` closes in
    `finally`. Column tuples imported from `processor` (single source of truth). `is_50_depth` 0/1 → BOOLEAN
    at insert. Idempotency by fresh file (§8.5): build to a temp path, then atomic-rename to `--output` so a
    crashed build never leaves a half store.
69. **`--catchup` self-heal (§8.6 mode 2).** Scan `output_dir` for `market_depth_raw_*.jsonl.gz`; replay a
    date when `market_depth_analytics_<date>.duckdb` is missing OR older than the raw log; **oldest-first**;
    a per-file failure is logged + skipped (one bad day never blocks the rest). Idempotent.
70. **`--verify` both modes (fork 4, §8.4).** Replay into a temp `.duckdb`, then diff vs a reference: default
    = the canonical prior build for that day; `--verify-against-live` = the SQLite live store, restricted to
    `recorder.live_metrics` columns. Compare `recorder_meta.schema_version`/`config_hash` first and **abort on
    schema mismatch** (a deliberate column-set change is not drift). Then per-table row counts + per-`(table,
    timestamp, symbol)` tolerance diff (`abs(a−b) ≤ atol`, NULL==NULL). Report mismatches; exit 0 clean / 1 drift.
71. **Robust reader (§8.5).** Iterate gz lines; skip HEADER/EOF meta (multiple HEADERs from same-day restarts
    tolerated — the **first** carries the `instruments` block; later data still flows); skip a corrupt/truncated
    trailing JSON line with a **counted WARNING** rather than aborting; a missing EOF is tolerated (crash before close).
72. **Filters (§8.2).** `--underlying <name>` replays one underlying (its options + spot). `--from/--to` (IST
    HH:MM) slice against `recv_ts`, **documented caveat**: a mid-session slice restarts rolling warm-up, so a
    sliced build is not second-for-second comparable to a full-day build (`--verify` is meaningful only on an
    unsliced build).

### P7 subtask checklist (embedded 2026-07-05; ✅ complete 2026-07-06)
- [x] **A · `DuckDBAnalyticalWriter`** (decision 68) — replaced the P5 stub in `database_writer.py`: DuckDB
  DDL constant (`_DUCKDB_DDL`, §4.1a), open/PRAGMA/DDL, `write(envelope)` per-table buffer, `finalize()` bulk
  `executemany` + `recorder_meta(built_by="replay")` + `CHECKPOINT`, `with`/`__exit__` close-in-`finally`;
  column tuples imported from `processor`; `is_50_depth`→BOOLEAN; temp-file-then-`os.replace` idempotency.
- [x] **B · HEADER enrichment** (decision 65) — `InstrumentManager.to_header_dict()` + `from_header()`;
  `file_writer.py` HEADER gains an `instruments` dict (optional `instruments=None` arg — P2 tests still pass);
  `main.py` orchestrator passes `im.to_header_dict()` (guarded for fakes).
- [x] **C · `replay.py`** (decisions 66/67/71) — `_load_header` + robust packet loop (skip meta, skip corrupt
  trailing, count); `replay_file(config, raw_path, output_path, *, underlying, from_t, to_t)` reconstructs the
  IM via `from_header`, drives the processor synchronously off `recv_ts` (`ingest` + boundary `emit_second`),
  drains `db_queue` → DuckDB writer. Added thin public `TickProcessor.ingest`.
- [x] **D · `--catchup`** (decision 69) — `catchup()` scan + oldest-first + missing/stale staleness; per-file isolation.
- [x] **E · `--verify` both modes** (decision 70) — `verify(config, built, reference, *, live_subset)`:
  schema/config_hash gate → row-count + tolerance diff → report; `--verify-against-live` reads the SQLite live
  store (live_metrics columns only; a table with no live columns is skipped).
- [x] **F · Filters** (decision 72) — `--underlying`, `--from/--to` applied in `replay_file` + warm-up caveat.
- [x] **G · CLI wire** (`__main__.py`) — replaced the stub with `_cmd_replay`: output resolution (canonical vs
  `.replay.duckdb` side file; `--catchup` iterates), dispatch `--output/--verify/--verify-against-live/
  --underlying/--from/--to`; exit 0/1/2.
- [x] **H · Spec/notes sync** — §8.3 recv_ts clarification; §3.5.4 HEADER `instruments` block; `PROJECT_NOTES.md`.
- [x] **I · Tests** — `tests/test_replay.py` (15) + 4 DuckDB cases in `tests/test_database_writer.py` (all
  offline): writer DDL/round-trip/None→NULL/`is_50_depth`→BOOLEAN/idempotent/discard-on-error; `from_header`
  maps + round-trip + missing-block error; **replay determinism** (`--verify` clean on re-replay); perturbed →
  drift; catchup self-heal; corrupt-line/missing-EOF/multi-HEADER tolerated; `--verify-against-live` (real
  SQLite live store, live-subset match); warm-up NULLs; `--underlying` filter; CLI exit codes.
- [x] **J · Docs** — new `Documents/replay.md`; updated `database_writer.md` (DuckDB writer built),
  `ARCHITECTURE.md` (P7 built + both tiers complete), `file_writer.md` (HEADER `instruments`),
  `instrument_manager.md` (`to_header_dict`/`from_header`), dated `CHANGELOG.md`; cite §8/§3.6.5/§4.1a.
- [x] **K · Completion audit** — full `pytest market_depth_recorder/tests/ -q` **221 passed** (203 prior − 1
  removed stub + 4 DuckDB + 15 replay); `--validate-config`→0; the exact M6 `--replay --catchup` **subprocess**
  rebuilds a DuckDB store from an enriched raw log (5 spot / 30 option / 15 agg rows, `built_by="replay"`);
  `--verify` clean on re-replay + perturbed→drift; `--catchup` self-heals. **FD audit** — DuckDB build conn
  `with`/`finally` close + CHECKPOINT + temp→rename on every path (finalize/exception/discard); gz reader
  `with`-closed; verify/catchup read-only conns closed in `finally`; replay adds **no** thread/subprocess/lock
  (the M6 child is already reaped by P6). **Genericization** grep clean (replay/writer keyed by `name`;
  table/column names are §4 schema constants imported from `processor`). **Invariants** — idempotent fresh
  file (§8.5); determinism proven by `--verify`; warm-up reproduced; recv_ts live-parity; lossless raw
  untouched (read-only). Docs current. **← stopping for approval before P8.**

*Two P7 notes worth recording:* (a) **`--verify-against-live` skips tables with no live columns** — when
`recorder.live_metrics` selects no rolling metric, the live store never writes `strike_window_metrics`, so
that table is excluded from the comparison rather than flagged as a row-count mismatch. (b) A
**pre-enrichment log** (HEADER without an `instruments` block) is *not* self-contained → `from_header` raises
a clear `RestError`; there are no such production logs (all P7+ logs carry the block), and the same-day M6
path always has it.

*Critical files:* **new** `replay.py`, `tests/test_replay.py`, `Documents/replay.md`; **edit**
`database_writer.py` (`DuckDBAnalyticalWriter` body + `_DUCKDB_DDL`), `__main__.py` (replace the replay stub),
`file_writer.py` (HEADER `instruments`), `main.py` (pass chain to the writer), `instrument_manager.py`
(`to_header_dict`/`from_header`), `processor.py` (thin public `ingest`), `tests/test_database_writer.py`
(DuckDB cases), `Documents/{database_writer,ARCHITECTURE,file_writer,instrument_manager,CHANGELOG}.md`,
`PROJECT_NOTES.md` + spec §8.3/§3.5.4; **reuse** `processor.py` (`TickProcessor`, column tuples,
`emit_second`), `config.py` (`analytics_db.*`), `utils.py`, `__init__.py` (`SCHEMA_VERSION`). `duckdb~=1.5.2`
already pinned (P0).

*Verification:* full `pytest market_depth_recorder/tests/ -q` green (no live feed/broker; DuckDB is local);
`--replay <fixture>.jsonl.gz --output tmp.duckdb` → DuckDB with the four §4.1a tables + `recorder_meta`;
`--verify` clean diff on a re-replay (determinism); `--catchup` rebuilds a missing/stale day; end-to-end —
the P6 e2e smoke records a tiny raw log → `--replay` it → the DuckDB store is queryable with `built_by="replay"`.

## P8 — Offline Integration & Soak (automated, committed)

**Scope:** the first whole-pipeline run — the real four-thread pipeline driven end-to-end by a scripted,
`recv_ts`-paced recorded feed + the real reprocess subprocess, all under a virtual clock (no live
broker/WS/market), plus the small instrumentation/hardening it needs. **No new engine math.** Authoritative:
existing spec §3.1 (orchestrator), §5.1/§6.2 (processor), §6.4 (health), §8 (replay) + the cross-cutting
invariants. The original P8 spec bullets (whole-pipeline FD audit; live depth confirmations; perf targets)
split into **P8 (offline: FD audit + perf/memory instrument, deterministic)** and the new **P9 (live
confirmations)** below.

### Two exploration findings that reshape P8 (verified 2026-07-06)
- **The claimed real four-thread e2e smoke does not exist as code.** `Documents/main.md:120-122` and
  `Documents/CHANGELOG.md:106-107` assert an "end-to-end smoke [that] drives the real four-thread pipeline
  (no-op transport)," but **no test constructs `_build_default_pipeline` + the real workers together** —
  `test_main.py` runs entirely on injected fakes (`pipeline_factory`); `test_replay.py` glues only
  processor→SQLite→DuckDB. P6's e2e was a **manual** check. P8 builds the real harness (making the claim
  true) and corrects the two docs.
- **No perf/memory instrumentation exists, and there is no SIGTERM handler.** `emit_second` is untimed;
  nothing measures process RSS; only SIGINT/`stop()` teardown gracefully. With `daemon=True` workers an OS
  `SIGTERM` (systemd/`docker stop`) hard-kills mid-write, skipping the raw EOF marker + FD close — a real
  gap in the lossless-raw invariant on managed shutdown.

### Forks resolved (2026-07-06, user)
- **Fork 1 — E2E approach → BUILD BOTH, split P8 (offline) + new P9 (live).** P8 = the automated
  recorded-feed harness (satisfies FD audit + perf/memory instrument, CI-runnable). **P9 = the live-run
  session**; its full checklist + run-sequence are **written now**, executed **later** ("when market opens I
  will ask you to run P9"). Market closed today (2026-07-06) → P9 authored, not run, this cycle.
- **Fork 2 — RSS measurement → stdlib platform-adaptive.** `utils.process_rss_mb()`: `ctypes` +
  `GetProcessMemoryInfo` (`WorkingSetSize`) on Windows; `resource.getrusage(RUSAGE_SELF).ru_maxrss`
  normalized to MiB (Linux KiB / macOS bytes) on Unix. **No new pinned dependency** (standalone-venv promise).
- **Fork 3 — SIGTERM → add a graceful-teardown handler** (main thread, live daemon entry only) → `stop()` →
  the existing drain/EOF/FD-close path. Upholds lossless-raw under production supervisors.
- **Fork 4 — cycle timing → permanent, in health.** `perf_counter` around `emit_second`;
  `cycle_ms_p50`/`cycle_ms_max` in `TickProcessor.stats()`; surface (+`rss_mb`) in `health.json` + `--status`.

### P8.0 — Doc sync (execute FIRST) — ✅ (this doc + spec §6.4/§3.1.4 + PROJECT_NOTES + the main.md/CHANGELOG e2e-claim correction)

### P8 subtask checklist (embedded 2026-07-06; ✅ complete 2026-07-06)
- [x] **A · RSS instrument (`utils.py`)** — `process_rss_mb()` (Windows `ctypes`/`K32GetProcessMemoryInfo`
  `WorkingSetSize` with explicit `restype`/`argtypes` — default int marshalling truncates handle/pointer on
  64-bit; Unix `getrusage` `ru_maxrss` → MiB); best-effort (failure → `0.0` + DEBUG). 3 tests in
  `test_utils.py`: positive+finite, grows after a big alloc, never raises.
- [x] **B · Cycle-time instrument (`processor.py`)** — `perf_counter` around the `emit_second` body in a
  `try/finally` (processor-thread-only, **no lock**); bounded `deque(maxlen=300)`; `stats()` adds
  `cycle_ms_p50`/`cycle_ms_max` (empty → `0.0`). Test in `test_processor.py`.
- [x] **C · Health surface (`main.py`/`__main__.py`)** — `build_health()` adds `cycle_ms_p50`/`cycle_ms_max`
  (from `stats()`) + `rss_mb` (sampled each write); `read_status` prints them; extended `test_main.py`
  schema + `--status` tests.
- [x] **D · SIGTERM handler (`__main__.py`)** — `_install_sigterm_handler`/`_make_sigterm_handler` in
  `_cmd_run` only (main thread, guarded); `h` → `orchestrator.stop()` (idempotent). 2 tests (handler
  invoked directly; install returns True on main thread); real OS delivery → P9.
- [x] **E · Real four-thread harness (`tests/test_integration.py`, new)** — `RecordedTransport` (a real
  `FeedTransport` playing a self-paced `market_data` script) drives the **real** `_build_default_pipeline`
  (real raw/db writers + processor + feed, 3 real bounded queues, both events, real `InstrumentManager` via
  `from_header`), all paths under `tmp_path`; shrunk checkpoint/batch cadence. Script: spot→DSM seed→option
  subscribe→**50-level NIFTY/NFO + 5-level SENSEX/BFO, per-level `orders` populated**→tee→emit→SQLite commit
  across 3 buckets. Real §3.1.4 teardown; asserts no worker `is_alive()`; raw `.gz` HEADER…EOF with the
  `instruments` block + preserved `feed_time`/`depth_levels`/`is_50_depth`/`orders`; live `.db` populated;
  `health.json` perf fields. **Real reprocess subprocess** (`--replay --catchup`) → DuckDB
  `built_by="replay"` → determinism via `replay.verify`; reaped + no `.building_*`/lock/`.tmp` residue.
  `@pytest.mark.integration` (registered in `conftest`). *(Real-clock drive; live-vs-replay `--verify` stays
  in `test_replay`. Rolling-window 30 s warm-up + a DSM boundary breach are beyond a ~3 s bucketed run, so
  those remain covered by their unit tests — noted in `integration.md`.)*
- [x] **F · Whole-pipeline FD audit** — every FD resource audited on clean/SIGINT/**SIGTERM** paths (gzip;
  SQLite+`-wal`/`-shm`; DuckDB+`.wal`/`.building_*`; WS socket; reprocess subprocess+log fd; run-lock;
  health temp fd; 4 threads; queues) — open→close sites match the runtime map; assertion-backed in E (clean
  joins, no residue, reaped subprocess). Written up in `Documents/integration.md` + dated `CHANGELOG.md` +
  `ARCHITECTURE.md` P8-built state.
- [x] **G · Docs + completion audit** — corrected the false e2e-smoke claim in `main.md`/`CHANGELOG.md`;
  updated `ARCHITECTURE.md`/`CHANGELOG.md`/`utils.md`/`processor.md`/`main.md` + spec §6.4/§3.1.4 +
  `PROJECT_NOTES.md`; new `integration.md` + `LIVE_RUN.md`. Full `pytest market_depth_recorder/tests/ -q`
  **228 passed** (221 + 7); `--validate-config`→0; `--status` shows the new fields; genericization grep of
  `utils/processor/main/__main__.py` clean. **← P8 complete; P9 runbook authored, awaiting a live market
  session to execute.**

*Critical files (P8):* **new** `tests/test_integration.py`, `Documents/integration.md`; **edit** `utils.py`
(`process_rss_mb`), `processor.py` (cycle timing), `main.py` (`build_health`+SIGTERM), `__main__.py`
(`--status` fields + SIGTERM in `_cmd_run`), `tests/{test_utils,test_processor,test_main}.py`,
`Documents/{ARCHITECTURE,CHANGELOG,main,utils,processor}.md`, `PROJECT_NOTES.md`, spec §6.4/§3.1.4, and the
two doc-claim corrections; **reuse** `RecorderOrchestrator._build_default_pipeline`, all four real workers,
`replay.{replay_file,verify,catchup}`, `FakeTransport`/`_md`, `test_replay._packets/_write_raw`,
`InstrumentManager.from_header`, `utils.atomic_write`, `tests/conftest.py`. No new pinned dependency
(stdlib `ctypes`/`resource`/`signal`).

---

## P9 — Live-run session (runbook authored now, executed when market opens)

**Scope:** operator-driven live confirmation of the whole pipeline against a real OpenAlgo + connected broker
(**FYERS**, for the 50-level TBT depth), during IST market hours. Bullet-2 confirmations **cannot be faked**.
**Deliverable now = the complete runbook `Documents/LIVE_RUN.md` + this checklist.** Execution is a later,
explicitly-requested session (I drive it interactively and capture results into `LIVE_RUN.md`).

### P9-A · Preconditions checklist
- [x] OpenAlgo running; broker = **FYERS** connected, session valid (tokens expire ~03:00 IST — re-auth if stale).
- [x] **SEBI static-IP** whitelisting (effective 2026-04-01): recorder host IP registered with the broker
  (quotes/orders IP-gated); confirm quotes work from this host. *(quotes/depth returned live → IP + session OK)*
- [x] IST market hours; today is a trading day (not weekend/holiday). *(Mon 2026-07-06 13:36 IST)*
- [x] `config.yaml`: real `openalgo.api_key`/`host_server`/`websocket_url`, `transport: raw`, NIFTY+SENSEX;
  `output_dir` writable, ≥ `min_free_disk_mb` free; venv installed. *(deps global; api_key set by user)*

### P9-B · Run sequence
- [x] 1. `--validate-config` → exit 0. *(2026-07-06)*
- [x] 2. `--preflight` → per-underlying **actual depth**: NIFTY/NFO → **50**, SENSEX/BFO → **5**; note the §9
  WARNING on `actual < requested` (silent 50→5 alarm). *(all confirmed; §9 alarm fired for SENSEX)*
- [x] 3. Start the daemon at/after `session_start`; watch logs for **Init → Connect → Record**; confirm
  `websocket_status` connected + option subs flowing from spot ticks. *(milestones + mid-day REST ATM seed OK)*
- [x] 5. Inspect raw `.jsonl.gz`: **`feed_time`/`depth_levels`/`is_50_depth`/`total_buy/sell_qty` present**
  (load-bearing raw-transport finding — SDK strips them) + **per-level `orders` populated & non-zero**;
  spot-check `orders==0 → NULL` in live metrics. *(fields + per-level `orders` + HEADER `instruments` confirmed)*
- ➜ 4. Mid-session `--status`. *(PARTIAL this session: queues/cycle=10.5/rss=51/drops=0 ✓ via health.json;
  `actual_depth` empty & NIFTY depth absent — TBT-cap finding.)* **MOVED → P10-E3.**
- ➜ 6. Graceful teardown + mid-session SIGTERM. *(NOT run: external SIGTERM unreliable on Windows; force-kill
  only → no EOF/DuckDB.)* **MOVED → P10-E6.**
- ➜ 7. Post-session `--verify`/`--verify-against-live` + DuckDB query. *(NOT run: no teardown → no DuckDB.)*
  **MOVED → P10-E8.**

### P9-C · Confirmations to capture (the P8 spec bullets, live)
- [x] Raw yields `feed_time`/`depth_levels`/`is_50_depth` ✓; NIFTY→50 / SENSEX→5 ✓; per-level `orders`
  populated → M13/M14 computable ✓; §9 silent-50→5 alarm behaves. *(all confirmed at preflight)*
- ➜ Performance / RSS at full scale. *(PARTIAL: cycle 10.5/14.2 ms < 15 ✓; rss=51MB NOT authoritative —
  SENSEX-only load, NIFTY depth absent.)* **MOVED → P10-E4.**
- ➜ FD audit under real load (OS handle/fd count stable across the session). *(NOT run this session.)*
  **MOVED → P10-E5.**

### P9-D · Abort / rollback (in the runbook)
- Stop = Ctrl-C (SIGINT) or SIGTERM → graceful drain. Mid-session restart re-seeds ATM via REST `get_quote` +
  `mark_restart_boundary` (INSERT-OR-REPLACE overlap second). NIFTY depth degrading to 5 → check FYERS TBT
  session / `:50` routing per the §9 alarm.
- ➜ *Live abort/rollback drill (SIGINT/SIGTERM drain + mid-session restart re-seed + degrade path)* **MOVED → P10-E7.**

*Critical files (P9):* **new** `Documents/LIVE_RUN.md` (authored now); execution captures results into it.
No code changes (P9 is operational).

### P9 EXECUTION LOG (2026-07-06) — partial pass + one design-breaking finding
Executed live (IST Mon 2026-07-06 ~13:36–14:19, OpenAlgo + FYERS). Full detail in `Documents/patches/Phase9_notes.md`.
- **Confirmed live:** chain resolution on the real master; preflight actual depth **NIFTY/NFO→50, SENSEX/BFO→5**
  with per-level `orders` populated; §9 silent-degrade alarm fires; Init→Connect→Record + mid-day REST ATM
  seed; raw audit fields (`feed_time`/`depth_levels`/`is_50_depth`/`total_*_qty`) + HEADER `instruments`;
  `cycle_ms_p50=10.5`/`max=14.2` (<15ms), `rss_mb=51` (≪500), `raw_dropped=db_dropped=0`; 95.1% books
  correctly ordered (no bid/ask parse bug); 36,711 raw records captured.
- **3 bugs found & fixed (228 tests green):** (1) `instrument_manager._matches_underlying` — live master
  `name` col is the full contract label not the base underlying → broadened the symbol-prefix fallback to
  fire whenever exact-name fails; (2) invalid `heartbeat_timeout(12) > interval(10)` crashed `run_forever`
  → config `8` + new `config.py` validation rule `0<timeout<interval`; (3) preflight now infers depth level
  count from `len(depth["buy"])` when `depth_levels` absent (5-level BFO packets omit it).
- **HEADLINE FINDING (cannot be faked):** **FYERS TBT caps at 5 symbols per channel**, and OpenAlgo
  **hardcodes `channel="1"`** (`broker/fyers/streaming/fyers_websocket_adapter.py:682,686`) for all depth-50
  subs → effective ceiling the recorder can reach = **5 symbols total**. 80 NIFTY `:50` legs → FYERS rejected
  the whole channel → **NIFTY captured 0 depth** (spot only); SENSEX (non-TBT BFO 5-level HSM) streamed fine.
  Proxy protocol has no channel field, so the recorder cannot fix this alone. Also saw FYERS 429s under load.
- **Windows caveat:** external graceful SIGTERM unreliable (daemon needed `taskkill /F`); force-kill left the
  gz without EOF (crash path, replay-tolerant). Graceful teardown must be tested via in-console Ctrl-C / the
  15:35 auto-teardown next session.

---

## P10 — Full-chain 50-level via OpenAlgo channel patch + dated storage + EOD health report

**Origin:** the P9 headline finding. **Locked decisions (user, 2026-07-06):**
- **D1. Option A — patch OpenAlgo** to spread depth-50 subscriptions across FYERS TBT channels 1–50 (5 per
  channel, ceiling 5×50=250). **Reject** direct-FYERS-connection (would break the broker-agnostic contract,
  duplicate token/session mgmt, risk concurrent-session conflicts).
- **D2. No hybrid** — with the cap lifted, subscribe the **whole NIFTY chain at 50-level** (recorder already
  sends `:50` for all legs → no recorder subscription-code change). Hybrid kept only as a documented fallback(Docuement clearly when does the need for hybrid arises and possible ways to approach hybrid model).
- **D3. Data + reports live inside `market_depth_recorder/`, in dated sub-folders** (`data/<YYYY-MM-DD>/…`).
- **D4. EOD health & sanity-check** produces a **separate dated report** (markdown + json) from the day's data.
- **D5. Live full-50 validation deferred to the next session** (only 71 min of market left when decided; a
  live platform patch + OpenAlgo restart + re-run was too rushed). Build everything now; validate next open.

**Sequencing:** P10-A (platform patch, isolated) → P10-B (dated storage) → P10-C (EOD tool) → P10-D (docs) →
P10-E (live validation, next session). Each phase stops for approval per the workflow.

**⚠️ Risks the patch does NOT remove — MUST verify live before P10 is "done" (blocking):**
1. **Global FYERS TBT cap?** We only ever observed the *per-channel* limit (5). FYERS may **also** cap the
   **total** TBT symbols **per app** across all channels. Spreading NIFTY's ~80 legs over ~16 channels is the
   test — if a global cap exists, some channels will still stall/reject. → validated in **P10-E2**. *(If a
   global cap turns out to exist, the "whole chain at 50-level, no hybrid" decision (D2) reopens and the
   hybrid fallback is back on the table.)*
2. **Perf/storage at 80 × 50-level.** The clean P9 numbers (`cycle 10.5 ms`, `rss 51 MB`) were **SENSEX
   5-level-dominated**. Full NIFTY 50-level (10× the levels × ~80 symbols) is the real load the `< 15 ms`
   cycle / `< 500 MB` RSS targets — and the raw/live/duckdb storage growth — must hold against. → the
   **authoritative** measurement is **P10-E4** (+ E5 FD stability). *(If targets are missed at full scale,
   revisit `processor.mode: process` sharding (§5.2) and/or the hybrid to bound volume.)*

### P10-A · OpenAlgo channel-spread patch (PLATFORM code — scope-exception, user-authorized)
- [x] A1. Edit `broker/fyers/streaming/fyers_websocket_adapter.py::_subscribe_tbt_depth` — replaced the
  hardcoded `channel="1"` with a **stable bucketed assignment** via new `_assign_tbt_channel()` (5/channel
  across 1–50, class consts `TBT_SYMBOLS_PER_CHANNEL`/`TBT_MAX_CHANNELS`). Reuses an existing symbol's channel
  (no renumber on reconnect — caller holds `self.lock`, so race-free); 250 ceiling → clear ERROR + `False`.
  `py_compile` OK.
- [x] A2. Verified the TBT client resumes each newly-used channel (`_flush_subscribe_batch` →
  `switch_channel(resume_channels=[…])`, `fyers_tbt_websocket.py:633-634`) + resubscribes per channel on
  reconnect → multi-channel subs stream; no client change needed.
- [x] A3. Reference **patch file** `Documents/patches/openalgo_fyers_tbt_channels.patch` generated (88-line
  `git diff`).
- [x] A4. `Documents/patches/OPENALGO_PATCH.md` — detailed **pro/cons analysis** (patch vs direct-FYERS vs stay-≤5),
  **operator notes** (apply/revert/`git apply`; **upgrade-drift** warning + re-check grep; upstream candidate),
  **re-test checklist** (Option Chain/GEX 50-depth; recorder preflight >5 NIFTY), and the P10-E risk cross-refs.
- ➜ A5. **Live smoke (needs OpenAlgo restart):** restart OpenAlgo, `--preflight` a NIFTY window >5 symbols,
  confirm depth streams across channels + Option Chain unaffected. **MOVED → P10-E1/E2** (a restart disrupts
  the live feed → validation window).

### P10-B · Dated storage inside the package (recorder code) — ✅ (2026-07-06, 237 tests)
**Decision (2026-07-06):** the dated sub-folder holds the **DATA + reports** (raw/live/duckdb/`reports/`);
**operational singletons stay at the BASE `output_dir`** (`health.json`, `reprocess.log/.lock`) so
`--status`, the run-lock, and the launcher stay date-agnostic (revises the earlier "health/reprocess follow
the dated dir" wording).
- [x] B1. `config.yaml` — `output_dir` → `./market_depth_recorder/data` (inside package); added
  `date_partitioned: true` (+ `config.py` Rule-3 bool validation, optional→defaults flat). `health_file_path`
  / `reprocess.{log,lock}_file` → the **base** dir (un-dated, per the decision above). `config_hash` unchanged
  (paths aren't in the formula).
- [x] B2. Path resolution via new `utils.session_output_dir(output_dir, session_date, date_partitioned)`
  → `<output_dir>/<YYYY-MM-DD>/` when partitioned, else flat; wired into `RawTickFileWriter` +
  `SQLiteLiveWriter` (each `makedirs` its dated dir). Date stays in filenames too (self-description).
- [x] B3. Replay/reprocess place the canonical duckdb + derived live-store **beside the raw log**
  (`os.path.dirname(raw)`) — flat/partitioned-agnostic; `catchup` globs both base and `*/` dated sub-folders
  (union, sorted by filename). `canonical_output`/`live_store_path`/`catchup` updated; `auto_on_session_end`
  reprocess finds the day's raw in its dated dir.
- [x] B4. Verified `market_depth_recorder/.gitignore` `data/**` covers `data/<date>/…` + `reports/`
  (`git check-ignore`).
- [x] B5. Tests `tests/test_paths.py` (9): `session_output_dir` (partitioned/flat/None-date); writers land in
  dated dir + flat when off + absent-key→flat; replay canonical/live paths beside raw; catchup discovers
  dated **and** legacy-flat raws with duckdb beside each. Full suite **237 passed**.

### P10-C · EOD health & sanity-check + dated report (new module + CLI) — ✅ (2026-07-06, 252 tests)
- [x] C1. New `eod_report.py` + CLI `--eod-report [--date YYYY-MM-DD]` (defaults to today IST; resolves the
  dated dir; `--date` guarded to `--eod-report` only). Wired in `__main__.py`.
- [x] C2. **Checks** implemented — *Raw:* HEADER/`instruments`/`config_hash`; EOF clean-vs-missing; record
  count; timespan; **per-underlying depth coverage → FAIL on 0** (the P9 catch); **actual-vs-requested depth**
  (§9 degrade → WARN); `feed_time` coverage **among TBT/50-level packets only** (5-level books legitimately
  omit it → all-5-level day is N/A→PASS, no daily false WARN); per-level `orders`; crossed/locked %.
  *Live DB:* table presence + **per-underlying option-row coverage → FAIL on 0**. *DuckDB:* absent→SKIP,
  tables populated, `recorder_meta` stamps. *Ops:* drops→FAIL, `cycle_ms<15`, `rss<500`, degraded.
  *(Deferred as not worth the complexity now: the 1s-grid-gap scan and live-DB NULL-rate spot-check — the
  depth-coverage + timespan checks already surface the failure modes those targeted; can add later.)*
- [x] C3. **Report** → `<dated-dir>/reports/eod_healthcheck_<date>.{md,json}` (atomic write); worst-wins
  overall verdict; **exit 0 clean / 1 on any FAIL**. Markdown badge tables + machine JSON.
- [x] C4. Pure/offline — no live feed; tolerant EOF-safe raw reader; sqlite/duckdb opened read-only + closed
  in `finally`; injected `now`.
- [x] C5. Tests `tests/test_eod_report.py` (15): `_classify`; `check_raw` clean/no-EOF/NIFTY-no-depth→FAIL/
  missing/hash-mismatch; `check_live_db` clean/NIFTY-missing→FAIL/absent; `check_duckdb` skip/populated+meta;
  `check_ops` clean/drops-FAIL+perf-WARN; `run_eod_report` end-to-end (clean→0, gap→1, writes md+json).
  **First real run** on the P9 `2026-07-06` capture: overall **FAIL** — correctly flagged
  `raw.depth_coverage.NIFTY` + `live.option_rows.NIFTY`, WARNs on missing EOF / SENSEX 5-level / `cycle_ms_max
  25.96>15`. Full suite **252 passed**.

### P10-D · Docs — ✅ (2026-07-06)
- [x] D1. `Documents/patches/Phase9_notes.md` — done (session understanding + all tests).
- [x] D2. `Documents/patches/OPENALGO_PATCH.md` (P10-A), `Documents/eod_report.md` (module ref), `SETUP.md`
  (dated storage layout + `--eod-report`/`--catchup` usage + FYERS TBT patch precondition).
- [x] D3. Updated `ARCHITECTURE.md` (module map + `eod_report.py` + P8/P9/P10 built-state; storage topology
  already added in P10-B), dated `CHANGELOG.md` (P10-A/B/C/D entries), `LIVE_RUN.md` (P9 results filled +
  channel-patch precondition in §A). **Reconciled the 5-per-channel TBT reality** into the authoritative
  design spec §1 depth-reality note, `CLAUDE.md` "Depth Reality", and `PROJECT_NOTES.md` roadmap (P9 partial
  pass + P10-A..E) — spec is the source of truth, all citing `Documents/patches/{OPENALGO_PATCH,Phase9_notes}.md`.

### P10-E · Live validation — ✅ DONE (2026-07-07; PASS with known WARNs; full record `Documents/{LIVE_RUN,phase_10E_notes}.md`)
*Absorbed all incomplete/partial P9 items — P9 is now a closed partial-pass record. Run mid-session against
the channel-spread-patched OpenAlgo (fresh instance) using a **compressed session** (`session_end` +8 min)
to exercise the real timer-based graceful teardown on Windows without a full-day wait. Suite **257 green**.*
- [x] E1. Platform up (HTTP 200); live quotes NIFTY 24502 / SENSEX 78554 (broker + SEBI static-IP OK); patch
  present (`TBT_SYMBOLS_PER_CHANNEL`, `_assign_tbt_channel`). *(Browser-driven Option Chain/GEX UI smoke not
  run headless — the same WS-proxy + FYERS TBT depth path is exercised by E2's live preflight.)*
- [x] E2. Preflight `NIFTY/NFO=50`, `SENSEX/BFO=5`; full-run raw shows **NFO `depth_levels` up to 47** across
  all 80 legs / ~16 TBT channels (impossible under the old 5-cap → patch works); **no global FYERS cap**
  (200 contracts, no stalls). Per-strike populated depth varies 20–47 with real expiry-day liquidity.
- [x] E3. `--status`: queues 0/0/0, drops 0, `degraded_level=0`, `active_contracts=200`, **`actual_depth=
  {NIFTY:50, SENSEX:5}`** (after the max-seen fix), `restart_count=0`.
- [x] E4. **rss 52–58 MB (≪500 ✓)**; **`cycle_ms_p50` ≈ 22 ms, `max` ≈ 43–60 ms** — exceeds the old <15 ms.
  Keeps real-time pace (~45× headroom; queues 0). **Decisions (user):** target **RE-TUNED 15→30 ms**;
  per-underlying `process` sharding **REJECTED** (wrong lever — NIFTY ≈ 84 % of load lands in one shard);
  intra-underlying parallelism **DEFERRED**; a redundant `_core` double-compute removed (output-preserving).
- [x] E5. OS handle count **196–197 flat**, threads 27–28 — no leak across the run.
- [x] E6. Timer teardown at `session_end+grace`: DSM frozen → drain → **clean EOF** → reprocess subprocess
  auto-launched → **DuckDB built (61 538 packets, 580 s, 291 837 rows, 0 corrupt)** → parent `.wait()`-reaped
  the child and exited cleanly. *(External SIGINT/SIGTERM can't reach a detached process on Windows — the
  timer path is the faithful local test of the identical drain/EOF/FD-close chain; handlers unit-tested +
  valid on Linux/Docker.)*
- [x] E7. Mid-session restart **re-seeds ATM via one REST quote per underlying + `mark_restart_boundary`**
  (`boundary_ts` logged every start); §9 degrade alarm fired for SENSEX at preflight. Graceful-drain path =
  the one E6 validated.
- [x] E8. `--replay --verify` → **`VERIFY OK: no drift`** (determinism, zero tolerance). DuckDB
  `recorder_meta.built_by="replay"` + all 4 tables populated. `--verify-against-live` → **99.7 % match**;
  the boundary-timing divergence (live wall-clock emit vs replay timestamp emit; 0.88 % of rows on the real
  session) is now tolerated by a new `_LIVE_SUBSET_TOLERANCE_PCT = 2.0` in `replay.verify()` (strict duckdb
  path stays zero-tolerance).
- [x] E9. `--eod-report` → **PASS 24 · WARN 2 · FAIL 0**, exit 0. WARNs = known SENSEX 5-level degrade (§9)
  + `cycle_ms` (pre-retune threshold). **NIFTY depth coverage now PASSES** (was the P9 FAIL). Captured in
  `LIVE_RUN.md` §C.

**P10-E outcomes / open items** (detail in `Documents/phase_10E_notes.md`):
- Patch validated end-to-end — full NIFTY chain streams true 50-level TBT; no global cap. **D2 (whole chain
  at 50-level, no hybrid) holds** — hybrid remains a documented fallback only.
- **Open (deferred):** intra-underlying parallelism to bring `cycle_ms` further down (not needed for
  real-time pace today). Per-underlying sharding is documented as a non-solution.
- **Windows signal limitation (documented):** external SIGINT/SIGTERM don't gracefully stop a detached
  daemon on Windows; use in-console Ctrl-C or the `session_end+grace` timer. On Linux/Docker the handlers
  deliver normally (`docker stop`/systemd SIGTERM → graceful drain).
- **D2 holds:** whole chain at 50-level with no hybrid. Hybrid stays a documented fallback only (would
  re-open only if a global FYERS cap appeared — it did not).

*Critical files (P10):* **platform** `broker/fyers/streaming/fyers_websocket_adapter.py` (patch); **new**
`market_depth_recorder/eod_report.py`, `Documents/patches/openalgo_fyers_tbt_channels.patch`,
`Documents/patches/OPENALGO_PATCH.md`, `Documents/eod_report.md`, `tests/test_eod_report.py`, `tests/test_paths.py`;
**edit** `config.yaml`, `config.py`, `main.py`, `replay.py`, `__main__.py` (CLI), `Documents/{ARCHITECTURE,
CHANGELOG,LIVE_RUN,SETUP}.md`, `PROJECT_NOTES.md`.

---

## Cross-cutting invariants (guard every phase)
- **Lossless raw:** raw drop only on disk saturation, counted + logged ERROR.
- **Tee correctness:** two independent `put`s, never a shared queue; backpressure order proc → db → raw.
- **Genericization:** no index/exchange/strike-step literal in engine code; state keyed by `name`.
- **Uniform 1s grid:** never varied at runtime (degraded mode skips work, keeps cadence).
- **Never-shrink** subscriptions until graceful 15:35 shutdown.
- **FD hygiene:** shared singletons, `with`/close on every path; subprocess logs to file, `wait()`-reaped.
- **Docs updated per phase** (ARCHITECTURE + dated CHANGELOG + per-module doc) as part of the Completion
  Audit — a phase is not done until its docs are current.

## Verification (how each phase is proven)
- Unit tests per phase (pytest), all runnable **without** a live broker/WS/market (inject clock, feed,
  writers) per the CLAUDE.md testing rule.
- `--validate-config` (P0), `--preflight` (P1/P3), `--status` (P6) as dry-run smoke checks.
- **Replay is the determinism harness:** `--verify` re-runs the same `TickProcessor` against a fixture
  raw `.jsonl.gz` and diffs the rebuild (catches wall-clock/dict-order nondeterminism).
- Final: end-to-end run + FD audit (P8).

## Sequencing notes
- P0.0 (doc sync) and P0 (rename) run first; the rename invalidates this session's CWD — continue against
  the new `market_depth_recorder/` path.
- Each phase stops for approval per the PROJECT_NOTES workflow; expand each into an exhaustive subtask
  checklist before implementing it.
