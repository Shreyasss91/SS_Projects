# `metrics/` — Metric registry, snapshot & per-strike bodies (P4a)

Reference for the implemented metric layer. Cites the design spec `§`. The declarative registry is
`registry.py` (metadata, §3.4.0); the compute bodies bind to it in `per_strike.py` (P4a) and — later —
`rolling.py` / `aggregate.py` (P4b). Shared inputs live in `snapshot.py`.

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
constants. **Deferred (P4b):** §3.4.3 rolling bodies (+ the `ofi` column) and §3.4.4 aggregates/regime.

## Tests
`tests/test_metrics_per_strike.py` — hand-computed values (spread/mid/micro/OBI/walls/effective-depth/
M25/…) + every guard (shallow-book NULLs, `orders==0`, thin-book M25, absent tick/ltp/feed_time, crossed
market, empty book). `tests/test_processor.py` covers the engine.