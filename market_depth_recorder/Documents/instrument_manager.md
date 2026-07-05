# `instrument_manager.py` — Instrument & Expiry Manager (§3.2)

## Responsibility

Runs once at startup. Over the OpenAlgo REST API, resolves each configured underlying's **current
weekly option chain**, auto-detects the **strike step**, and compiles the **O(1) lookup structures**
the DSM (P3) and processor (P4) consume. Pure resolution logic — **no sockets, threads, or DB**; the
only file descriptor is a transient HTTP connection closed on every path.

The §3.2.5 **live** depth probe (reading `depth_levels`/`is_50_depth` off a raw packet) is **deferred
to P3** (plan decision 10): the SDK strips those fields, so the probe needs the raw-WS client that
lands in P3. `--preflight` here resolves the chain **offline** and reports `actual_depth` as pending.

## Public API

### `RestClient(host_server, api_key, *, timeout=10, max_retries=3, backoff_sec=0.5, opener=None)`
Thin `urllib` wrapper (no third-party HTTP dep — standalone-venv promise). Injectable `opener` for
tests.
- `get_instruments(exchange) -> list[dict]` — `GET /api/v1/instruments/?apikey=…&exchange=<x>&format=json`; auth via **query param**.
- `get_expiry(symbol, exchange) -> list[str]` — `POST /api/v1/expiry/` body `{apikey, symbol, exchange, instrumenttype:"options"}`; auth in **body**. Returns the API's sorted, future-only expiry list.
- `get_quote(symbol, exchange) -> float` — `POST /api/v1/quotes/` body `{apikey, symbol, exchange}` → `data.ltp` (P6 mid-day-restart ATM seed, §3.1.2). **Needs a live broker session** (unlike the DB-backed instruments/expiry); a missing/non-numeric `ltp` raises `RestError`. The orchestrator falls back to the lazy WS spot seed on any failure.
- Retries up to `max_retries` on network error / **5xx** with linear backoff; **4xx is terminal**
  (a bad key/request never benefits from a retry). Non-`success` envelopes and malformed bodies raise
  `RestError`.

### `InstrumentManager(config, rest_client=None)`
- `resolve()` — loop `config.underlyings` (never branching on a name); per underlying: one expiry POST
  + one instruments GET, filter, detect step, build maps. Raises `RestError` on any REST failure or an
  empty/absent chain (fast-fail — no chain means nothing to record).
- `preflight_report() -> list[dict]` — one summary row per resolved underlying for `--preflight`.
- `resolved` (property) — `True` once `resolve()` has run; the P6 orchestrator resolves exactly once at
  Milestone 1 and skips a redundant re-fetch on a supervised restart.
- `to_header_dict() -> dict` (P7) — serialize the resolved chain for the raw-log HEADER: per underlying
  `{option_exchange, expiry, strike_step, contracts:[[strike, ce_sym, pe_sym, tick_size], …]}`. The P6
  orchestrator passes this to `RawTickFileWriter` so replay is self-contained.
- `from_header(config, header) -> InstrumentManager` (P7, classmethod) — reconstruct a fully-resolved
  manager from a HEADER's `instruments` block with **no REST** (offline replay for a log of any age).
  Raises `RestError` if the block is absent (a pre-enrichment log).

**Exposed state** (all keyed by underlying `name` / OpenAlgo `symbol`):
| Attribute | Shape | Consumer |
| --- | --- | --- |
| `strike_to_symbol_map` | `{name: {strike: {"CE": sym, "PE": sym}}}` | DSM subscription math (P3) |
| `symbol_to_strike_map` | `{sym: {"underlying","strike","option_type"}}` | reverse lookup (P3/P4) |
| `active_strikes_list` | `{name: [sorted strikes]}` | DSM boundary/ATM search (P3) |
| `tick_size_map` | `{sym: tick_size}` | M29 spread-in-ticks (P4) |
| `chains` | `{name: ResolvedChain}` | preflight / orchestrator summary |

`ResolvedChain` (frozen): `name, option_exchange, expiry, expiry_date, strike_step, strikes,
requested_depth, probe_strike, n_contracts`. `probe_strike` is the **median strike** placeholder
(no live spot yet — the DSM refines the true near-ATM with the live spot tick in P3).

## Resolution rules

- **`E_weekly`** = `get_expiry(...)[0]`. The OpenAlgo expiry service already drops past expiries, sorts,
  and includes the expiry day itself (`expiry_service.py:224-228`) — so `data[0]` satisfies the §3.2.2
  rollover gate directly. The instrument master is used only for the strike grid / symbols / tick_size.
- **Underlying match:** exact `name` column (unambiguous — we query per option-exchange); blank `name`
  falls back to **longest-prefix** over the configured names on the `symbol` string (NIFTYNXT50 not
  shadowed by NIFTY; cf. `qty_freeze_db.py:211-219`).
- **Option filter:** `instrumenttype ∈ {OPTIDX, OPTSTK, CE, PE}`, a resolvable CE/PE (tag or symbol
  suffix), a positive `strike`, and `expiry == E_weekly`.
- **Strike step (§3.2.3):** mode of adjacent sorted-strike differences (`Counter`, so ties never
  raise and wide far-OTM gaps don't distort). Validated against `expected_strike_step`; on a miss (or
  < 2 strikes / no positive gaps) → **WARNING** + `strike_step_fallback`.
- **Maps built from the master `symbol` directly** — never string-constructed (avoids
  expiry/strike-format bugs). Integral float strikes are normalized to `int` keys.

## Config keys consumed
`openalgo.host_server`, `openalgo.api_key`; per underlying: `name`, `option_exchange`,
`requested_depth`, `expected_strike_step`, `strike_step_fallback`. (REST timeout/retries are
transport constants, not engine config — they never touch `config_hash`.)

## Threads / locks / FDs
None persistent. No thread, no lock, no DB. Each REST call opens one HTTP connection under `with`
(or explicitly closes the `HTTPError` body) — closed on success, retry, and error. `InstrumentManager`
holds no long-lived descriptor after `resolve()`.

## CLI
`python -m market_depth_recorder --preflight --config config.yaml` → per-underlying line
`name option_exchange expiry step strikes requested_depth probe_strike actual_depth=<n>`. **As of P3**,
`--preflight` resolves the chain (this module) **and** runs the live raw-WS depth probe
(`websocket_client.run_depth_preflight`) to fill `actual_depth`. REST resolution is a prerequisite
(exit **1** on config/REST failure); the depth probe is best-effort — an unreachable WS/session prints
`actual_depth=<unreachable: no WS/session>` and still exits **0** (plan decision 30). Instruments/expiry
are DB-backed (no live broker session), but the depth probe needs the WS proxy + a live feed.

## Deferred to later phases
- DSM boundary math / true ATM from live spot is now built in **P3** (`websocket_client.py`); this
  module's `chains[name].probe_strike` (median strike) seeds the preflight, and the DSM refines the true
  near-ATM from the live spot tick.
