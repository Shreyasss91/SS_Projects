"""Declarative metric registry (spec §3.4.0) — the extension point for M1..M29 and beyond.

Every metric is a :class:`MetricSpec` entry rather than an inline hardcoded list. Each entry
declares its **name** (the token usable in ``recorder.live_metrics``), the **inputs** it consumes,
its **minimum depth** requirement (so deep-book-only metrics auto-``NULL`` when the populated level
count ``L`` is shallower — §3.4.2), the **output column(s)** it writes, the **table** it targets,
and its **thin/fat eligibility**.

This makes three things config-only rather than code changes (§3.4.0):
  1. ``recorder.live_metrics`` is *validated against the registry* at startup — an unknown name
     fast-fails (§7.3).
  2. the thin (live) vs fat (offline) split is simply *which registry entries fire* — the same
     ``TickProcessor`` runs both.
  3. adding a future metric (M30+) is a pure additive registration, with no edits to the resampler,
     the writers, or the validation.

**P0 registers metadata only** — no function bodies. The per-metric NumPy computations (§3.4.2–§3.4.4)
are bound to their specs in P4 (thin/live) and reused by P7 (fat/replay). ``register()`` supports the
decorator form ``@register(spec)`` so a compute function can be attached later without touching the
metadata declared here.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

# --------------------------------------------------------------------------------------------------
# Table names (spec §4.1). Kept as constants so specs reference a single source of truth.
# --------------------------------------------------------------------------------------------------
T_STRIKE = "option_strike_metrics"      # per-strike, per-second snapshot metrics (§3.4.2)
T_WINDOW = "strike_window_metrics"      # per-strike rolling-window metrics (§3.4.3)
T_AGG = "aggregated_window_metrics"     # multi-strike aggregates + regime (§3.4.4)

# Metric families (used for thin/fat cost reasoning and docs).
FAM_PER_STRIKE = "per_strike"
FAM_ROLLING = "rolling_window"
FAM_AGGREGATE = "aggregate"

# Canonical input tokens a metric may consume (documentation-grade vocabulary, §3.4.0).
#   touch          — L1 best bid/ask price+qty
#   full_book      — all L populated bid/ask levels
#   orders         — per-level order counts (nord); 0 treated as NULL (§3.4.2 M13/M14)
#   spot           — underlying spot LTP
#   ltp            — option last traded price
#   tick_size      — instrument tick size from the master contract (§3.4.2 M29)
#   feed_time      — broker exchange clock, for latency/staleness (§3.4.2 M23)
#   rolling_deque  — the per-strike 1s history deque (§3.4.3)
#   prev_snapshot  — the previous second's book, price-aligned (§3.4.3-B/E)
#   per_strike     — depends on already-computed per-strike metrics (aggregates, §3.4.4)


@dataclass(frozen=True)
class MetricSpec:
    """Declarative metadata for one metric (spec §3.4.0). Immutable; function bodies are stored
    separately in :data:`METRIC_FUNCS` (bound in P4/P7), so the metadata stays frozen."""

    name: str                               # registry key + token usable in recorder.live_metrics
    family: str                             # FAM_PER_STRIKE | FAM_ROLLING | FAM_AGGREGATE
    inputs: tuple[str, ...]                 # input tokens consumed (see vocabulary above)
    min_depth: int                          # min populated levels L; below this the metric emits NULL (§3.4.2)
    output_columns: tuple[str, ...]         # DB column(s) this metric writes (§4.1); () = computed but not persisted
    table: str                              # target table (T_STRIKE | T_WINDOW | T_AGG)
    spec_section: str                       # authoritative spec section reference
    description: str                        # one-line human description
    m_number: int | None = None             # 1..29 for the per-strike M-series; None otherwise
    thin_eligible: bool = True              # may run on the live (thin) path; the actual subset is recorder.live_metrics
    fat_eligible: bool = True               # runs in the offline (fat) full-catalog replay (§8)


# --------------------------------------------------------------------------------------------------
# Registry storage + registration API
# --------------------------------------------------------------------------------------------------
REGISTRY: dict[str, MetricSpec] = {}
"""name → MetricSpec. Populated at import time by the ``register(...)`` calls below."""

METRIC_FUNCS: dict[str, Callable] = {}
"""name → compute function. Empty in P0; bound in P4/P7 via ``@register(spec)`` decorator usage."""

# Named aggregate groups (§3.4.0 / §3.4.4): operator-facing tokens that expand to a set of metric
# names. ``atm_aggregates`` is the §3.4.4-B multi-strike matrix; ``regime`` is registered as its own
# metric (below) so it is usable directly. Kept as a dict so adding a group is a pure data edit.
GROUPS: dict[str, tuple[str, ...]] = {
    "atm_aggregates": (
        "depth_pcr",
        "consolidated_pressures",
        "bnet",
        "spread_diff",
        "net_options_pressure",
        "pinning_score",
    ),
}


def register(spec: MetricSpec) -> Callable[[Callable], Callable]:
    """Register ``spec`` in the module registry (duplicate-name fast-fail) and return a decorator
    that binds a compute function to it.

    Usable two ways:
      * ``register(MetricSpec(...))`` — metadata-only registration (P0). The returned decorator is
        simply discarded.
      * ``@register(MetricSpec(...))`` above a ``def`` — also stores the function in
        :data:`METRIC_FUNCS` (P4/P7), without altering the frozen metadata.
    """
    if spec.name in REGISTRY:
        raise ValueError(f"duplicate metric id {spec.name!r} in registry")
    REGISTRY[spec.name] = spec

    def _bind(fn: Callable) -> Callable:
        METRIC_FUNCS[spec.name] = fn
        return fn

    return _bind


def known_names() -> set[str]:
    """The full set of tokens accepted in ``recorder.live_metrics``: every metric ``name``, every
    output column, every named group, plus the literal ``"all"`` (§7.3 live_metrics membership)."""
    names: set[str] = set(REGISTRY)
    for spec in REGISTRY.values():
        names.update(spec.output_columns)
    names.update(GROUPS)
    names.add("all")
    return names


def resolve(token: str) -> list[MetricSpec]:
    """Resolve a ``live_metrics`` token to the metric spec(s) it selects.

    ``"all"`` → every registered metric; a group token → its member specs; a metric ``name`` → that
    spec; otherwise a token matching one or more metrics' output columns → those specs. Raises
    :class:`KeyError` for an unknown token (drives the §7.3 fast-fail).
    """
    if token == "all":
        return list(REGISTRY.values())
    if token in GROUPS:
        return [REGISTRY[n] for n in GROUPS[token]]
    if token in REGISTRY:
        return [REGISTRY[token]]
    hits = [s for s in REGISTRY.values() if token in s.output_columns]
    if hits:
        return hits
    raise KeyError(token)


def known_aggregates() -> tuple[str, ...]:
    """The named aggregate group tokens (e.g. ``atm_aggregates``) — convenience for docs/validation."""
    return tuple(GROUPS)


# ==================================================================================================
# §3.4.2 — Exhaustive per-strike metrics (M1–M29). Written to option_strike_metrics.
# min_depth encodes the deep-book guard: the metric emits NULL when the populated level count L is
# below it (§3.4.2). L1/touch metrics use 1; Top-N metrics use N.
# ==================================================================================================

# A. Spread Dynamics
register(MetricSpec("spread", FAM_PER_STRIKE, ("touch",), 1, ("spread",), T_STRIKE,
                    "§3.4.2-A", "M1 Bid-Ask spread P_ask1 - P_bid1", m_number=1))
register(MetricSpec("relative_spread", FAM_PER_STRIKE, ("touch",), 1, ("relative_spread",), T_STRIKE,
                    "§3.4.2-A", "M2 Relative spread = spread / mid", m_number=2))
register(MetricSpec("mid_price", FAM_PER_STRIKE, ("touch",), 1, ("mid_price",), T_STRIKE,
                    "§3.4.2-A", "M3 Mid price (P_bid1 + P_ask1)/2", m_number=3))
register(MetricSpec("micro_price", FAM_PER_STRIKE, ("touch",), 1, ("micro_price",), T_STRIKE,
                    "§3.4.2-A", "M4 Volume-weighted micro price", m_number=4))

# B. Order Book Imbalances
register(MetricSpec("raw_obi", FAM_PER_STRIKE, ("full_book",), 1, ("raw_obi",), T_STRIKE,
                    "§3.4.2-B", "M5 Raw OBI across all L levels", m_number=5))
register(MetricSpec("top5_obi", FAM_PER_STRIKE, ("full_book",), 5, ("top5_obi",), T_STRIKE,
                    "§3.4.2-B", "M6 Top-5 OBI", m_number=6))
register(MetricSpec("top10_obi", FAM_PER_STRIKE, ("full_book",), 10, ("top10_obi",), T_STRIKE,
                    "§3.4.2-B", "M7 Top-10 OBI", m_number=7))
register(MetricSpec("weighted_obi", FAM_PER_STRIKE, ("full_book",), 1, ("weighted_obi",), T_STRIKE,
                    "§3.4.2-B", "M8 Exponentially decay-weighted OBI (core pressure indicator)", m_number=8))

# C. Volumetric & Pressure Ratios
register(MetricSpec("bid_stack_ratio", FAM_PER_STRIKE, ("full_book",), 1, ("bid_stack_ratio",), T_STRIKE,
                    "§3.4.2-C", "M9 Bid stack ratio = Σq_bid / Σ(q_bid+q_ask)", m_number=9))
register(MetricSpec("ask_stack_ratio", FAM_PER_STRIKE, ("full_book",), 1, ("ask_stack_ratio",), T_STRIKE,
                    "§3.4.2-C", "M10 Ask stack ratio = 1 - bid stack ratio", m_number=10))
register(MetricSpec("book_pressure", FAM_PER_STRIKE, ("full_book",), 10, ("book_pressure",), T_STRIKE,
                    "§3.4.2-C", "M11 Mid-centered top-10 monetary-depth imbalance (+ve = bid-heavy)", m_number=11))
register(MetricSpec("best_bid_ask_qty", FAM_PER_STRIKE, ("touch",), 1,
                    ("best_bid_qty", "best_ask_qty"), T_STRIKE,
                    "§3.4.2-C", "M12 Raw quantities resting at touch (best bid/ask)", m_number=12))
register(MetricSpec("avg_order_size", FAM_PER_STRIKE, ("full_book", "orders"), 10,
                    ("avg_order_size_bid", "avg_order_size_ask"), T_STRIKE,
                    "§3.4.2-C", "M13 Avg order size = Σq / Σn over top-10 (orders==0 → NULL)", m_number=13))
register(MetricSpec("oci", FAM_PER_STRIKE, ("full_book", "orders"), 10, ("oci",), T_STRIKE,
                    "§3.4.2-C", "M14 Order Count Imbalance over top-10 (orders==0 → NULL)", m_number=14))

# D. Liquidity Concentration & Structure
register(MetricSpec("effective_depth", FAM_PER_STRIKE, ("full_book",), 1, ("effective_depth",), T_STRIKE,
                    "§3.4.2-D", "M15 Resting volume within ±effective_depth_pct of mid", m_number=15))
register(MetricSpec("lci", FAM_PER_STRIKE, ("full_book",), 5, ("lci_bid", "lci_ask"), T_STRIKE,
                    "§3.4.2-D", "M16 Liquidity Concentration Index (top-5 / total)", m_number=16))
register(MetricSpec("touch_dominance", FAM_PER_STRIKE, ("full_book",), 5,
                    ("touch_dominance_bid", "touch_dominance_ask"), T_STRIKE,
                    "§3.4.2-D", "M17 Touch dominance = q1 / top-5", m_number=17))
register(MetricSpec("round_number_depth", FAM_PER_STRIKE, ("full_book",), 1,
                    ("round_number_depth_bid", "round_number_depth_ask"), T_STRIKE,
                    "§3.4.2-D", "M18 Volume at round-number prices (low-priority for option premiums)", m_number=18))
register(MetricSpec("cumulative_depth_vector", FAM_PER_STRIKE, ("full_book",), 5, (), T_STRIKE,
                    "§3.4.2-D", "M19 4-dim cumulative depth [5,10,20,50] per side (20/50 NULL when L shallower; "
                                "not persisted as discrete columns in §4.1)", m_number=19))

# E. Wall Analytics & Book Stability
register(MetricSpec("wall", FAM_PER_STRIKE, ("full_book",), 1,
                    ("bid_wall_price", "bid_wall_qty", "ask_wall_price", "ask_wall_qty"), T_STRIKE,
                    "§3.4.2-E", "M20 Largest bid/ask wall price & size", m_number=20))
register(MetricSpec("wall_score", FAM_PER_STRIKE, ("full_book",), 1,
                    ("wall_score_bid", "wall_score_ask"), T_STRIKE,
                    "§3.4.2-E", "M21 Wall size / median non-zero non-wall size (NULL if <2 such levels)", m_number=21))
register(MetricSpec("quote_stability", FAM_PER_STRIKE, ("touch", "rolling_deque"), 1, ("quote_stability",), T_STRIKE,
                    "§3.4.2-E", "M22 Fraction of window seconds the touch price was unchanged", m_number=22))
register(MetricSpec("anomaly_freshness", FAM_PER_STRIKE, ("feed_time",), 1, (), T_STRIKE,
                    "§3.4.2-E", "M23 Latency = T_local - feed_time; >2s → stale (feeds M24; NULL if feed_time absent)",
                    m_number=23))
register(MetricSpec("confidence", FAM_PER_STRIKE, ("touch", "rolling_deque", "feed_time"), 1, ("confidence",), T_STRIKE,
                    "§3.4.2-E", "M24 Normalized [0,1] confidence (spread tightness + OBI stability + freshness)",
                    m_number=24))

# F. Extended Execution & Fair-Value Metrics
register(MetricSpec("cost_to_fill", FAM_PER_STRIKE, ("full_book",), 1,
                    ("fill_slippage_buy", "fill_slippage_sell", "book_slope_bid", "book_slope_ask"), T_STRIKE,
                    "§3.4.2-F", "M25 Cost-to-fill slippage + Kyle-λ book slope (NULL if book cannot absorb probe qty)",
                    m_number=25))
register(MetricSpec("queue_imbalance", FAM_PER_STRIKE, ("touch",), 1, ("queue_imbalance",), T_STRIKE,
                    "§3.4.2-F", "M26 Touch (L1) OBI = (q_bid1 - q_ask1)/(q_bid1 + q_ask1)", m_number=26))
register(MetricSpec("vamp", FAM_PER_STRIKE, ("full_book",), 1, ("vamp",), T_STRIKE,
                    "§3.4.2-F", "M27 Volume-Adjusted Mid Price (multi-level micro-price generalization)", m_number=27))
register(MetricSpec("microprice_ltp_div", FAM_PER_STRIKE, ("touch", "ltp"), 1, ("microprice_ltp_div",), T_STRIKE,
                    "§3.4.2-F", "M28 Fair-value gap = (micro_price - ltp)/ltp", m_number=28))
register(MetricSpec("spread_ticks", FAM_PER_STRIKE, ("touch", "tick_size"), 1, ("spread_ticks",), T_STRIKE,
                    "§3.4.2-F", "M29 Spread / tick_size (NULL if tick size unknown)", m_number=29))

# ==================================================================================================
# §3.4.3 — Per-strike rolling time-window metrics. Written to strike_window_metrics
# (one row per (symbol, time_window ∈ {5,10,30}s)). min_depth inherits the underlying snapshot metric.
# ==================================================================================================

# A. Window Stat Trends
register(MetricSpec("price_return", FAM_ROLLING, ("rolling_deque", "ltp"), 1, ("price_return",), T_WINDOW,
                    "§3.4.3-A", "LTP % return over the window"))
register(MetricSpec("spread_stats", FAM_ROLLING, ("rolling_deque",), 1,
                    ("spread_mean", "spread_min", "spread_max", "spread_std"), T_WINDOW,
                    "§3.4.3-A", "Rolling mean/min/max/std of absolute spread"))
register(MetricSpec("wobi_stats", FAM_ROLLING, ("rolling_deque",), 1, ("wobi_mean", "wobi_std"), T_WINDOW,
                    "§3.4.3-A", "Rolling mean/std of Weighted OBI"))
register(MetricSpec("regression_slopes", FAM_ROLLING, ("rolling_deque",), 10,
                    ("wobi_slope", "book_pressure_slope"), T_WINDOW,
                    "§3.4.3-A", "Linear-regression slopes of Weighted OBI and Book Pressure over the window"))
register(MetricSpec("micro_price_rv", FAM_ROLLING, ("rolling_deque",), 1, ("micro_price_rv",), T_WINDOW,
                    "§3.4.3-A", "Realized volatility sqrt(Σ r²) of 1s micro-price log returns (NULL if <2 valid)"))

# B. Liquidity Flow Dynamics (price-aligned across consecutive snapshots)
register(MetricSpec("liquidity_flow", FAM_ROLLING, ("full_book", "prev_snapshot"), 10,
                    ("liquidity_added", "liquidity_removed"), T_WINDOW,
                    "§3.4.3-B", "ΔQ± price-aligned adds/removes across top-10"))
register(MetricSpec("book_churn", FAM_ROLLING, ("rolling_deque",), 10, ("book_churn",), T_WINDOW,
                    "§3.4.3-B", "Cumulative added + removed over the window"))
register(MetricSpec("flow_intensity", FAM_ROLLING, ("rolling_deque",), 10, ("flow_intensity",), T_WINDOW,
                    "§3.4.3-B", "Count of active seconds in window with ΔQ+ or ΔQ-"))

# C. Options Book Momentum
register(MetricSpec("pressure_velocity", FAM_ROLLING, ("rolling_deque",), 10, ("pressure_velocity",), T_WINDOW,
                    "§3.4.3-C", "1st-order rate of change of Book Pressure"))
register(MetricSpec("pressure_acceleration", FAM_ROLLING, ("rolling_deque",), 10, ("pressure_acceleration",), T_WINDOW,
                    "§3.4.3-C", "2nd-order rate of change of Book Pressure"))

# D. Wall Persistence & Lifetime Analytics
register(MetricSpec("wall_persistence", FAM_ROLLING, ("rolling_deque",), 1, ("wall_persistence",), T_WINDOW,
                    "§3.4.3-D", "Consecutive seconds a wall held at one price"))
register(MetricSpec("wall_events", FAM_ROLLING, ("rolling_deque",), 1, ("walls_created", "walls_destroyed"), T_WINDOW,
                    "§3.4.3-D", "Count of walls created/destroyed over the window"))

# E. Order Flow Imbalance (touch-level; no deep-book guard — §3.4.3-E)
register(MetricSpec("ofi_sum", FAM_ROLLING, ("rolling_deque", "prev_snapshot"), 1, ("ofi_sum",), T_WINDOW,
                    "§3.4.3-E", "Cumulative best-level Order Flow Imbalance over the window"))

# ==================================================================================================
# §3.4.4 — Multi-strike aggregate matrix + regime. Written to aggregated_window_metrics
# (one row per (underlying, strike_window ∈ {SMALL,MEDIUM,LARGE})). Grouped under the
# "atm_aggregates" named group; "regime" is a standalone metric.
# ==================================================================================================
register(MetricSpec("depth_pcr", FAM_AGGREGATE, ("per_strike",), 1, ("depth_pcr",), T_AGG,
                    "§3.4.4-B", "Depth Put-Call Ratio (both-sides resting liquidity, not OI/volume PCR)"))
register(MetricSpec("consolidated_pressures", FAM_AGGREGATE, ("per_strike",), 10,
                    ("ce_pressure", "pe_pressure"), T_AGG,
                    "§3.4.4-B", "Consolidated CE/PE book pressures over the window"))
register(MetricSpec("bnet", FAM_AGGREGATE, ("per_strike",), 1, ("bnet",), T_AGG,
                    "§3.4.4-B", "Net Imbalance Bias: pooled PE - CE Weighted OBI, ∈[-2,2]"))
register(MetricSpec("spread_diff", FAM_AGGREGATE, ("per_strike",), 1, ("spread_diff",), T_AGG,
                    "§3.4.4-B", "Mean PE spread - mean CE spread"))
register(MetricSpec("net_options_pressure", FAM_AGGREGATE, ("per_strike",), 10, ("net_options_pressure",), T_AGG,
                    "§3.4.4-B", "NOP = PE Book Pressure - CE Book Pressure"))
register(MetricSpec("pinning_score", FAM_AGGREGATE, ("per_strike",), 1, ("pinning_score",), T_AGG,
                    "§3.4.4-B", "Pinning Score: max SMALL-window wall / mean LARGE-window wall"))
register(MetricSpec("regime", FAM_AGGREGATE, ("per_strike", "spot"), 1, ("regime",), T_AGG,
                    "§3.4.4-C", "Regime classification: Trending PE/CE, Pinning, Volatile, Balanced"))
