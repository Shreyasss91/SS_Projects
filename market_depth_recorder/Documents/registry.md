# Module: `metrics/registry.py`

The declarative metric registry (spec §3.4.0) — the extension point for M1..M29 and beyond. **P0
registers metadata only; no function bodies.** The NumPy computations (§3.4.2–§3.4.4) are bound to
their specs in P4 (thin/live) and reused by P7 (fat/replay).

## Why a registry

Making the metric set declarative turns three things into config/data edits instead of code changes
(§3.4.0):
1. `recorder.live_metrics` is **validated against the registry** at startup (unknown name → fast-fail, §7.3).
2. the **thin (live) vs fat (offline)** split is simply *which registry entries fire* — one `TickProcessor`.
3. **adding a future metric (M30+)** is a pure additive `register(...)` — no edits to the resampler,
   writers, or validation.

## Public API

- `MetricSpec` — frozen dataclass: `name` (registry key + `live_metrics` token), `family`
  (`per_strike` / `rolling_window` / `aggregate`), `inputs` (tuple of input tokens), `min_depth`
  (populated-levels guard — metric emits NULL when `L < min_depth`, §3.4.2), `output_columns` (the §4.1
  DB columns it writes; `()` = computed but not persisted as discrete columns), `table`, `spec_section`,
  `description`, `m_number` (1..29 for the per-strike M-series, else `None`), `thin_eligible`,
  `fat_eligible`.
- `REGISTRY: dict[str, MetricSpec]` — populated at import by the `register(...)` calls.
- `METRIC_FUNCS: dict[str, Callable]` — name → compute function; empty in P0, bound in P4/P7.
- `GROUPS: dict[str, tuple[str, …]]` — named aggregate groups; `atm_aggregates` expands to the §3.4.4-B
  multi-strike matrix. (`regime` is registered as its own metric, so it is a token directly.)
- `register(spec) -> decorator` — inserts `spec` (duplicate-name fast-fail) and returns a decorator that
  binds a compute function later (`@register(spec)` on a `def`), without mutating the frozen metadata.
- `known_names() -> set[str]` — every metric `name`, every output column, every group token, plus
  `"all"`; the acceptance set for `recorder.live_metrics` (§7.3).
- `resolve(token) -> list[MetricSpec]` — `"all"` → all; a group → its members; a `name` → that spec;
  else a token matching output columns → those specs; `KeyError` on unknown (drives §7.3 fast-fail).
- `known_aggregates() -> tuple[str, …]` — the group tokens.

## What is registered (metadata only)

- **§3.4.2 per-strike M1–M29** → `option_strike_metrics`. `min_depth` encodes the deep-book guard:
  touch/L1 metrics = 1, Top-5 = 5, Top-10 = 10. M19 (cumulative depth vector) and M23 (anomaly/freshness)
  are computed-but-not-persisted-as-columns → `output_columns=()`; resolvable by `name`.
- **§3.4.3 rolling-window** → `strike_window_metrics` (price return, spread/wobi stats, regression slopes,
  micro-price RV, liquidity flow, churn, flow intensity, pressure velocity/acceleration, wall persistence
  & events, OFI sum).
- **§3.4.4 multi-strike aggregates + regime** → `aggregated_window_metrics` (depth PCR, consolidated
  CE/PE pressures, B_net, spread diff, NOP, pinning score, regime), grouped under `atm_aggregates`
  (+ standalone `regime`).

## Notes / caveats

- `thin_eligible`/`fat_eligible` default to `True` for all metrics — every metric *may* run live; the
  actual live subset is chosen via `recorder.live_metrics`, not these flags. A future metric can set
  `thin_eligible=False` to forbid live use.
- `orders`-dependent metrics (M13 avg order size, M14 OCI) carry the `orders` input; the P4 bodies must
  treat `orders == 0` at a populated level as NULL (§3.4.2, `fyers_tbt_websocket.py:476-490`).

## Threads / locks / FDs owned

None. Pure in-memory declarative data, populated once at import.

## Tests

Exercised via `tests/test_config.py::test_live_metrics_full_m_series_pass` (all 29 M-names accepted) and
the `live_metrics` membership negative case; direct registry unit tests arrive with the P4 function bodies.
