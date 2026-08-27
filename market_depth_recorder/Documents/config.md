# Module: `config.py`

Loads and validates `config.yaml`, then hands the rest of the engine a frozen, typed object. Implements
spec §7.1–§7.3.

## Responsibilities

- Parse `config.yaml` (safe-load) and fast-fail on malformed YAML (§7.3 rule 1).
- Run **all** §7.3 validation rules, **collecting every failure** into one report (rule 3) rather than
  stopping at the first.
- Compute `config_hash` — the provenance stamp (§3.5.4 / §4.1b).
- Return a frozen, typed `Config` (rule E8) — never a raw dict.

## Public API

- `load_config(path) -> Config` — the single entry point. Raises `ConfigError` (carrying `.errors: list[str]`
  and `.report()`) on any failure; otherwise returns a `Config`.
- `compute_config_hash(raw: dict) -> str` — `"sha256:<hex>"` over the canonicalized (sorted-key)
  `metrics` + `regime` + `underlyings` subset — the parts that determine produced column values. An
  unchanged config hashes identically; changing a formula constant, threshold, or underlying flips it.
  Non-formula sections (queues, websocket, …) deliberately do **not** affect it.
- `Config` — frozen dataclass: one read-only mapping per top-level section, `underlyings: tuple[Underlying, …]`,
  `config_hash`, `source_path`.
- `Underlying` — frozen dataclass: `name, spot_symbol, spot_exchange, option_exchange, requested_depth,
  expected_strike_step, strike_step_fallback, initial_window, expansion_threshold, expansion_step,
  atm_max_strike_range`.
- `ConfigError` — exception with `.errors` and `.report()`.

## Validation rules (§7.3) implemented

1. Well-formed YAML; root is a mapping.
2. `output_dir` writable (temp create+delete; mkdir if missing).
3. Boundary/enum checks, **all collected**:
   - per-underlying `expansion_threshold < initial_window`; unique `name`; required keys present &
     non-empty; `strike_step_fallback ∈ expected_strike_step`; `expected_strike_step` a non-empty
     positive-int list.
   - `database.batch_write_interval_ms ∈ [500, 5000]`.
   - `analytics_db.memory_limit_mb ≥ 256`, `1 ≤ threads ≤ 64`.
   - `live_metrics` membership against the registry (or literal `"all"`).
   - enums: `websocket.transport ∈ {sdk, raw}`, `processor.mode ∈ {thread, process}` (+`shards ≥ 1`
     when process).
   - watermarks `0 < warn < critical ≤ 100`; `raw_file_queue_max ≥ max_queue_size`.
   - `session_start < session_end` (IST `HH:MM`).
   - non-empty positive-int lists: `metrics.time_windows_sec`, `metrics.round_number_multiples`.
   - session guards: `min_free_disk_mb ≥ 0`, `disk_check_interval_sec ≥ 5`, `skip_non_trading_days` bool,
     `trading_holidays` parse as `YYYY-MM-DD` (enforced only when `skip_non_trading_days = true`).
4. `health_file_path` parent dir writable/creatable (no `/tmp` assumption).
5. Fast-fail: any failure → stderr report + **exit 1** (via the CLI). No silent defaults.
6. `host_server` (http/https) and `websocket_url` (ws/wss) parse as valid URIs.

## Config keys consumed

All of them — this module is the single validator for the whole `config.yaml` (§7.1).

## Threads / locks / FDs owned

None persistent. The rule-2/rule-4 write-probes create and immediately remove a temp file, closing the
descriptor on every path.

## Tests

`tests/test_config.py` — happy path, one negative per rule, `--validate-config` exit codes, `config_hash`
determinism (incl. non-formula-section insensitivity), `live_metrics` membership (all M1–M29 + `"all"`).

## `market_depth_framework` block (F8, Plan_002 §17)

The recorder config carries the framework block, validated on every start by
`market_depth_framework/config.py` (fail-fast, exit 1) whether or not it is enabled — a
misconfiguration is found before the morning it is switched on. `enabled: false` is the default and
means today's recorder, unchanged.

The block is **excluded from `config_hash`**: a config with it hashes identically to the same config
without it (`sha256:8a48bcdd...a1468b`), so adopting the framework does not look like a new session to
the DB or to the EOD report.
