# `metrics/` — Metric registry, snapshot & compute bodies (P4a + P4b)

Reference for the implemented metric layer. Cites the design spec `§`. The declarative registry is
`registry.py` (metadata, §3.4.0); the compute bodies bind to it in `per_strike.py` (P4a, §3.4.2),
`rolling.py` (P4b, §3.4.3) and `aggregate.py` (P4b, §3.4.4). Shared inputs live in `snapshot.py`.

## `registry.py` — declarative registry + binding
- **Metadata** (`MetricSpec`, from P0): every metric declares `name`, `family`, `inputs`, `min_depth`,
  `output_columns`, `table`, `spec_section`, thin/fat eligibility. `REGISTRY` holds all M1–M29 + §3.4.3
  rolling + §3.4.4 aggregate/regime specs; the metadata is **frozen** and single-source.
- **`bind(name)`** (P4a) — decorator that attaches a compute body to an **already-registered** spec,
  storing it in `METRIC_FUNCS[name]`. Unlike `register()` (which *creates* a spec and fast-fails on a
  duplicate), `bind` fast-fails on an **unknown** name — so a typo can never leave a metric bodiless and
  the P0 metadata stays untouched.
- **`resolve_active(live_metrics)`** — resolves the `recorder.live_metrics` value (`"all"` or a token
  list) to the ordered active spec set, in **registry-declaration order** (per-strike → rolling →
  aggregate), so a caller computes them in dependency order (decision 37). `active_columns(specs)` is the
  union of their persisted `output_columns`; every other §4.1 column is `NULL` on the thin path.

## `snapshot.py` — shared inputs
- **`BookSnapshot`** (`__slots__`, decision 35) — built once per (symbol, second) from a packet's
  `depth.buy/sell`. Parses each side into best-first NumPy `price/qty/orders` arrays, keeping only
  **populated** levels (`price>0 & qty>0`) and sorting best-first (bids desc, asks asc) so index 0 is the
  touch and cumulative walks (M25) march outward. Exposes `best_bid/ask_px/qty`, `mid`, `spread`,
  `micro`, `L_bid/L_ask`, `depth()` = `min(L_bid, L_ask)`, and `enough(min_depth)` — the deep-book NULL
  gate. Carries the packet's self-describing `depth_levels`/`is_50_depth` for the row columns.
- **`MetricContext`** — config constants (`decay_k` + precomputed decay `weights`, `effective_depth_pct`,
  `round_number_multiples`, `book_pressure_levels`, `wall_sigma_mult`, `fill_probe_qty`,
  `stability_window`, `eps=1e-8`) plus per-symbol/per-packet scalars rebound each second (`tick_size`,
  `ltp`, `feed_time`, `now_local`, `history`). `w(n)` slices the decay array.
- **`StrikeHistory`** — per-symbol deques (touch key, Top-5 OBI, relative spread, freshness) that M22/M24
  read; `maxlen = max(time_windows_sec)`. The engine `push`es the current second before the bodies run.
- **P4b inputs** (§3.4.3/§3.4.4): **`WindowSample`** (`__slots__`) — one second of a strike's rolling
  inputs (`ltp`, `spread`, `wobi`, `book_pressure`, `micro_price`, price-aligned `dq_plus/dq_minus`,
  instantaneous `ofi`, `wall_price`); `None` fields mark a stale/shallow second the window bodies skip
  (decision 47). **`StrikeFeatures`** — one second of a strike's aggregate inputs (`option_type`,
  `strike`, `book_pressure`, `spread`, `relative_spread`, pooled-weighted `q_bid_w/q_ask_w`, `total_qty`,
  `wall_size`, `quote_stability`). **`TouchBook`** + `touch_book(snap, n)` — the compact prior-second
  top-`n` `price→qty` maps + touch scalars kept for price-aligned ΔQ (§3.4.3-B) and touch OFI (§3.4.3-E).
  `MetricContext` also gains `regime` (the `regime.*` thresholds the regime body reads).

## `per_strike.py` — M1–M29 bodies (spec §3.4.2)
Each is `fn(snap, ctx) -> {output_column: value | None}`, bound via `@bind(name)`; importing the module
(via `metrics/__init__`) populates `METRIC_FUNCS`. Implements the spec's corrections and guards:

| Metric | Notes / guard |
| --- | --- |
| M1 spread | logs CRITICAL on a crossed/`≤0` book, still records the value |
| M2–M4 rel-spread/mid/micro | `ε`-guarded ratios |
| M5–M8 raw/top5/top10/weighted OBI | Top-N → NULL when `depth() < N`; M8 per-side decay weights |
| M9–M11 stack ratios / book pressure | M11 **mid-centered** top-10, `book_pressure_levels`; NULL if `depth()<10` |
| M12 best bid/ask qty | touch quantities |
| M13/M14 avg order size / OCI | top-10; **`orders==0` → NULL** (no divide-by-zero) |
| M15–M19 effective depth / LCI / touch-dom / round-number / cumulative | M19 persists no §4.1 column (computed-only) |
| M20/M21 wall / wall score | M21 median over **non-zero non-wall** levels; NULL if `<2` such |
| M22 quote stability | fraction of the (shortest) window where the touch was unchanged; warm-up → NULL |
| M23/M24 freshness / confidence | latency from **`feed_time`** (absent/0 → freshness term 0); OBI-std clamped to `[0,1]`; result clamped |
| M25 cost-to-fill / Kyle-λ | walks the book for `fill_probe_qty`; per-side NULL if it can't absorb the probe |
| M26 queue imbalance | touch (L1) OBI |
| M27 VAMP | weighted multi-level micro-price; reduces to M4 at `L=1` |
| M28 micro/LTP divergence | NULL when `ltp` absent/`≤0` |
| M29 spread in ticks | NULL when `tick_size` unknown |

**Genericization:** no index/exchange/strike/CE/PE literal — a body sees only book arrays + config
constants.

## `rolling.py` — rolling-window bodies (spec §3.4.3)
Signature `fn(hist, n, ctx) -> {col: value | None}` where `hist` is a strike's `list[WindowSample]`
(oldest→newest, the engine's deque) and `n ∈ time_windows_sec`. Bodies reduce over the **last `n`**
samples; deep-book guards are **inherited** — a shallow/stale second contributes `None` and is skipped, so
a body NULLs when too few valid points remain (decision 47).

- **Instantaneous helpers** (the engine builds a `WindowSample` from these each second): `ofi_instant(cur,
  prev)` — best-level Cont–Kukanov–Stoikov OFI (§3.4.3-E); `None` on the boundary second (no prior touch)
  — never a spurious 0. `liquidity_delta_instant(prev, bid_map, ask_map)` — price-aligned ΔQ+/ΔQ- across
  the top-N price union, both sides (§3.4.3-B); `(None, None)` with no prior second.
- **Window bodies:** `price_return`, `spread_stats` (mean/min/max/std), `wobi_stats` (mean/std),
  `regression_slopes` (`wobi_slope`, `book_pressure_slope` — least-squares closed form), `micro_price_rv`
  (log-return realized vol, skips missing/≤0), `liquidity_flow`/`book_churn`/`flow_intensity` (windowed
  ΔQ **sums**, decision 45), `pressure_velocity`/`pressure_acceleration` (BP finite differences reaching
  `BP_{t-2N}`), `wall_persistence`/`wall_events` (created/destroyed), `ofi_sum` (windowed).
- **`HEAVY_METRICS`** — the CPU-heavy reductions the engine NULLs under degraded mode (slopes, RV,
  liquidity flow/churn/intensity, velocity/accel, wall persistence/events) while keeping the 1s cadence.

## `aggregate.py` — multi-strike aggregates + regime (spec §3.4.4)
Per-window bodies are `fn(ce_feats, pe_feats, ctx)` over one strike window's CE/PE `StrikeFeatures`;
`pinning_score`/`regime` are per-underlying scalars (`fn(view, ctx)`).

- **Per-window:** `depth_pcr` (both-sides ΣPE/ΣCE), `consolidated_pressures` (`ce_pressure`/`pe_pressure`),
  `bnet` (§3.4.4-B — **pooled** weighted OBI difference, so window-count invariant, stays in `[-2,2]`),
  `spread_diff` (mean PE − mean CE), `net_options_pressure` (ΣPE−ΣCE book pressure).
- **Per-underlying scalars:** `pinning_score` (max SMALL wall / mean LARGE wall) and `regime` (§3.4.4-C:
  LARGE-window NOP/B_net → Trending PE/CE; SMALL pinning near ATM → Pinning; wide LARGE spread + low
  stability → Volatile; else Balanced). Thresholds from `regime.*`.
- **`compute_underlying(features, spot, atm, step, radii, ctx)`** — the orchestrator the engine calls once
  per underlying per second: slices the ATM-centred SMALL/MEDIUM/LARGE windows, runs the bound bodies, and
  writes the two per-underlying scalars **identically** into all three window rows (decision 46).

**Genericization (P4b):** CE/PE come from each feature's `option_type` (the InstrumentManager map),
windows from config radii, thresholds from `regime.*` — no literal in either module.

## Tests
- `tests/test_metrics_per_strike.py` — hand-computed values (spread/mid/micro/OBI/walls/effective-depth/
  M25/…) + every guard (shallow-book NULLs, `orders==0`, thin-book M25, absent tick/ltp/feed_time, crossed
  market, empty book).
- `tests/test_metrics_rolling.py` — window trends, slopes on a perfect line, RV skipping an invalid
  second, windowed liquidity sums, velocity/accel, wall persistence/events, `ofi_sum`, and the
  instantaneous OFI-sign/boundary + price-aligned ΔQ helpers.
- `tests/test_metrics_aggregate.py` — both-sides PCR, consolidated pressures/NOP, pooled `bnet`
  window-invariance, `spread_diff`, `pinning_score`, all five regime labels, and the `compute_underlying`
  window-slicing + per-underlying-scalar broadcast.
- `tests/test_processor.py` covers the engine end-to-end (four tables, `ofi` back-fill, dependency
  closure, degraded heavy-skip keeps cadence, full `emit_second` determinism).