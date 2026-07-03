"""Per-second option-book snapshot + metric context (spec §3.4.2, plan decision 35).

A :class:`BookSnapshot` is built **once** per (symbol, second) from a normalized depth packet's
``depth: {"buy": [...], "sell": [...]}`` — turning the list-of-dicts book into per-side NumPy arrays
so every M1–M29 body consumes vectors without re-parsing (``__slots__`` per §5.1). A
:class:`MetricContext` carries the config-derived constants + per-symbol/per-packet scalars the bodies
need (decay weights, tick size, ltp, feed_time, the M22/M24 history). Both live in ``metrics/`` (not
``processor.py``) so the compute modules import them without a circular dependency back to the engine.

**Genericization:** nothing here names an index/exchange/strike/CE/PE — a snapshot is pure book data;
per-underlying identity is carried by the caller.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np

from ..utils import decay_weights

# Numerical floor used throughout §3.4.2 to keep ratios finite (the spec's ε = 1e-8).
EPS = 1e-8

# Max book depth we ever precompute decay weights for (TBT tops out at 50; a little headroom).
_MAX_LEVELS = 64


def _parse_side(levels: Sequence[dict] | None, *, descending: bool) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Turn one side's list-of-level-dicts into ``(price, qty, orders)`` float64 arrays.

    Only **populated** levels (``price > 0`` and ``quantity > 0``) are kept — zero-padding rows a feed
    appends beyond the real book are dropped so ``L`` reflects true depth (§3.4.2). Levels are sorted
    **best-first** (bids descending, asks ascending) so index 0 is always the touch and cumulative
    book-walks (M25) march away from the touch, regardless of feed ordering quirks.
    """
    px: list[float] = []
    qty: list[float] = []
    ordc: list[float] = []
    for lvl in levels or ():
        if not isinstance(lvl, dict):
            continue
        p = float(lvl.get("price") or 0.0)
        q = float(lvl.get("quantity") or 0.0)
        o = float(lvl.get("orders") or 0.0)
        if p > 0.0 and q > 0.0:
            px.append(p)
            qty.append(q)
            ordc.append(o)
    if not px:
        empty = np.empty(0, dtype=np.float64)
        return empty, empty.copy(), empty.copy()
    order = np.argsort(px)
    if descending:
        order = order[::-1]
    p_arr = np.asarray(px, dtype=np.float64)[order]
    q_arr = np.asarray(qty, dtype=np.float64)[order]
    o_arr = np.asarray(ordc, dtype=np.float64)[order]
    return p_arr, q_arr, o_arr


class BookSnapshot:
    """One second's bid/ask book for a single option strike, as best-first NumPy arrays."""

    __slots__ = (
        "bid_px", "bid_qty", "bid_ord", "ask_px", "ask_qty", "ask_ord",
        "depth_levels", "is_50_depth", "L_bid", "L_ask", "_mid", "_spread",
    )

    def __init__(self, depth: dict | None, *, depth_levels: object = None, is_50_depth: object = None):
        buy = (depth or {}).get("buy")
        sell = (depth or {}).get("sell")
        self.bid_px, self.bid_qty, self.bid_ord = _parse_side(buy, descending=True)
        self.ask_px, self.ask_qty, self.ask_ord = _parse_side(sell, descending=False)
        self.L_bid = int(self.bid_px.size)
        self.L_ask = int(self.ask_px.size)
        # Self-describing capability from the packet (row columns, §4.1), independent of populated L.
        self.depth_levels = depth_levels
        self.is_50_depth = is_50_depth
        self._mid: float | None = None
        self._spread: float | None = None

    # -- touch scalars ------------------------------------------------------------------------------
    @property
    def has_touch(self) -> bool:
        """True when both sides have at least the best level (needed for any touch metric)."""
        return self.L_bid >= 1 and self.L_ask >= 1

    @property
    def best_bid_px(self) -> float:
        return float(self.bid_px[0]) if self.L_bid else float("nan")

    @property
    def best_ask_px(self) -> float:
        return float(self.ask_px[0]) if self.L_ask else float("nan")

    @property
    def best_bid_qty(self) -> float:
        return float(self.bid_qty[0]) if self.L_bid else float("nan")

    @property
    def best_ask_qty(self) -> float:
        return float(self.ask_qty[0]) if self.L_ask else float("nan")

    @property
    def spread(self) -> float:
        """M3 pre-req: ``P_ask1 - P_bid1`` (may be ≤ 0 on a crossed book — caller logs M1 CRITICAL)."""
        if self._spread is None:
            self._spread = self.best_ask_px - self.best_bid_px if self.has_touch else float("nan")
        return self._spread

    @property
    def mid(self) -> float:
        """M3 mid price ``(P_bid1 + P_ask1)/2``."""
        if self._mid is None:
            self._mid = (self.best_bid_px + self.best_ask_px) / 2.0 if self.has_touch else float("nan")
        return self._mid

    def depth(self) -> int:
        """Populated levels available on **both** sides — the basis for the ``min_depth`` NULL guard
        (a Top-N metric needs N levels each side to be meaningful, §3.4.2)."""
        return min(self.L_bid, self.L_ask)

    def enough(self, min_depth: int) -> bool:
        return self.depth() >= min_depth


@dataclass
class MetricContext:
    """Config constants + per-symbol/per-packet scalars a metric body consumes (spec §3.4.2/§7.1).

    Built once per processor and lightly rebound per (symbol, second) for the scalar fields
    (``tick_size``/``ltp``/``feed_time``/``now_local``/``history``). ``weights`` is precomputed to
    ``_MAX_LEVELS`` and sliced per side, so no metric recomputes the decay array.
    """

    decay_k: float
    effective_depth_pct: float
    round_number_multiples: tuple[int, ...]
    book_pressure_levels: int
    wall_sigma_mult: float
    fill_probe_qty: float
    stability_window: int
    eps: float = EPS
    weights: np.ndarray = field(default=None, repr=False)  # type: ignore[assignment]
    # Per-symbol / per-packet, rebound each second:
    tick_size: float | None = None
    ltp: float | None = None
    feed_time: float | None = None
    now_local: float | None = None
    history: "StrikeHistory | None" = None

    def __post_init__(self) -> None:
        if self.weights is None:
            self.weights = decay_weights(_MAX_LEVELS, self.decay_k)

    def w(self, n: int) -> np.ndarray:
        """Decay weights ``w_1..w_n`` (§3.4.2 M8), sliced from the precomputed array."""
        if n <= self.weights.size:
            return self.weights[:n]
        return decay_weights(n, self.decay_k)


class StrikeHistory:
    """Per-symbol rolling history that M22 (quote stability) and M24 (confidence) read (decision 41).

    The engine ``push``es the current second's touch key, Top-5 OBI, relative spread and freshness flag
    **before** M22/M24 run, so the deques already include the current second. ``maxlen`` = the largest
    configured window; the metric slices the last N. Reused by P4b's §3.4.3 window table.
    """

    __slots__ = ("touch", "top5obi", "rel_spread", "fresh")

    def __init__(self, maxlen: int):
        self.touch: deque = deque(maxlen=maxlen)
        self.top5obi: deque = deque(maxlen=maxlen)
        self.rel_spread: deque = deque(maxlen=maxlen)
        self.fresh: deque = deque(maxlen=maxlen)

    def push(self, touch_key: object, top5obi: float | None, rel_spread: float | None,
             fresh: bool | None) -> None:
        self.touch.append(touch_key)
        self.top5obi.append(top5obi)
        self.rel_spread.append(rel_spread)
        self.fresh.append(fresh)

    def recent(self, seq: deque, window: int) -> list:
        """The last ``window`` entries of one deque (fewer during warm-up)."""
        n = len(seq)
        if n == 0:
            return []
        return list(seq)[max(0, n - window):]