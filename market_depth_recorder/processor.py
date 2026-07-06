"""Metric processor — resample loop + per-strike compute (spec §3.4, plan P4a).

``TickProcessor`` is the single compute thread: it drains ``proc_queue`` into an in-memory ``latest_ticks``
cache and, on each clock-aligned 1-second boundary, calls the pure :meth:`TickProcessor.emit_second`
which builds a :class:`BookSnapshot` per active option strike, runs the bound §3.4.2 metric bodies, and
pushes ``spot_states`` + ``option_strike_metrics`` row envelopes to ``db_queue``. It preserves a **uniform
1-second grid** (§6.2): forward-fill from the last packet, staleness → NULL/NaN rows (``confidence=0.0``),
degraded mode never varies the cadence.

**Concurrency (decision 33):** this one thread owns every piece of mutable state (``latest_ticks``, spot
cache, per-symbol history, counters) — there is **no lock**. The only cross-thread objects are the
thread-safe ``proc_queue`` (in) and ``db_queue`` (out). **FDs:** none — the processor holds no files,
sockets, DBs, or subprocesses.

**Genericization:** no index/exchange/strike/CE/PE literal appears — CE/PE and strikes come from the
InstrumentManager maps, windows/thresholds from config, and all per-underlying state is keyed by ``name``.

P4b adds the §3.4.3 rolling metrics (+ the ``ofi`` column) and the §3.4.4 aggregates/regime; in P4a those
columns are ``NULL`` and only two of the four tables are emitted.
"""

from __future__ import annotations

import math
import queue
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable

import numpy as np

from .config import Config
from .instrument_manager import InstrumentManager
from .metrics import registry
from .metrics.aggregate import compute_underlying
from .metrics.per_strike import relative_spread_value, topn_obi_value
from .metrics.registry import FAM_AGGREGATE, FAM_PER_STRIKE, FAM_ROLLING
from .metrics.rolling import HEAVY_METRICS, liquidity_delta_instant, ofi_instant
from .metrics.snapshot import (
    BookSnapshot, MetricContext, StrikeFeatures, StrikeHistory, TouchBook, WindowSample, touch_book,
)
from .utils import get_logger

logger = get_logger(__name__)

_TBT_SUFFIX = ":50"  # transport depth-topic suffix; stripped to the DB symbol (§4.1). Not an index literal.
_RAW_PUT_TIMEOUT_SEC = 0.5  # db_queue back-pressure: brief block before shedding (analytics sheds 2nd).
_DB_PUT_TIMEOUT_SEC = 0.5

# §4.1 column order — the db_queue row tuples follow these exactly (decision 38).
SPOT_COLUMNS: tuple[str, ...] = ("timestamp", "symbol", "spot_price", "atm_strike")

OPTION_COLUMNS: tuple[str, ...] = (
    "timestamp", "symbol", "strike_price", "option_type", "depth_levels", "is_50_depth", "ltp",
    "spread", "relative_spread", "mid_price", "micro_price", "weighted_obi", "raw_obi", "top5_obi",
    "top10_obi", "bid_stack_ratio", "ask_stack_ratio", "book_pressure", "best_bid_qty", "best_ask_qty",
    "avg_order_size_bid", "avg_order_size_ask", "oci", "effective_depth", "lci_bid", "lci_ask",
    "touch_dominance_bid", "touch_dominance_ask", "round_number_depth_bid", "round_number_depth_ask",
    "bid_wall_price", "bid_wall_qty", "ask_wall_price", "ask_wall_qty", "wall_score_bid",
    "wall_score_ask", "quote_stability", "confidence", "ofi", "fill_slippage_buy", "fill_slippage_sell",
    "book_slope_bid", "book_slope_ask", "queue_imbalance", "vamp", "microprice_ltp_div", "spread_ticks",
)

# Columns the engine always fills itself (identity + capability + forward-filled ltp); the rest come
# from metric bodies and default to NULL on the thin path.
_BASE_OPTION_COLUMNS = frozenset({
    "timestamp", "symbol", "strike_price", "option_type", "depth_levels", "is_50_depth", "ltp", "ofi",
})

STRIKE_WINDOW_COLUMNS: tuple[str, ...] = (
    "timestamp", "symbol", "time_window", "price_return", "spread_mean", "spread_min", "spread_max",
    "spread_std", "wobi_mean", "wobi_std", "wobi_slope", "book_pressure_slope", "liquidity_added",
    "liquidity_removed", "book_churn", "flow_intensity", "pressure_velocity", "pressure_acceleration",
    "ofi_sum", "micro_price_rv", "wall_persistence", "walls_created", "walls_destroyed",
)

AGG_COLUMNS: tuple[str, ...] = (
    "timestamp", "underlying", "strike_window", "depth_pcr", "ce_pressure", "pe_pressure", "bnet",
    "spread_diff", "net_options_pressure", "pinning_score", "regime",
)


def strip_suffix(symbol: str | None) -> str:
    """Drop the transport ``:50`` depth suffix to get the DB/lookup symbol (§4.1, decision 36)."""
    if symbol and symbol.endswith(_TBT_SUFFIX):
        return symbol[: -len(_TBT_SUFFIX)]
    return symbol or ""


class _Cell:
    """The latest packet cached for one option symbol + its receive time (staleness basis)."""

    __slots__ = ("packet", "recv_ts")

    def __init__(self, packet: dict, recv_ts: float):
        self.packet = packet
        self.recv_ts = recv_ts


class TickProcessor(threading.Thread):
    """Single-owner resample/compute thread (§3.4.1). See module docstring for ownership + invariants."""

    def __init__(
        self,
        config: Config,
        instrument_manager: InstrumentManager,
        proc_queue: "queue.Queue",
        db_queue: "queue.Queue",
        shutdown_event: threading.Event,
        *,
        time_fn: Callable[[], float] = time.time,
        active_metrics: object = None,
        name: str = "TickProcessor",
    ):
        super().__init__(name=name, daemon=True)
        self._config = config
        self._im = instrument_manager
        self._proc_queue = proc_queue
        self._db_queue = db_queue
        self._shutdown = shutdown_event
        self._time = time_fn

        rec = config.recorder
        self._interval = float(rec["resample_interval_sec"])
        self._staleness = float(rec["staleness_timeout_sec"])
        live = active_metrics if active_metrics is not None else rec["live_metrics"]

        # Active specs with a bound body, split by family (decision 37 dependency-closure order).
        active = registry.resolve_active(live)
        have_body = [s for s in active if s.name in registry.METRIC_FUNCS]
        self._active_per_strike = [s for s in have_body if s.family == FAM_PER_STRIKE]
        self._active_rolling = [s for s in have_body if s.family == FAM_ROLLING]
        self._active_agg = [s for s in have_body if s.family == FAM_AGGREGATE]
        self._need_rolling = bool(self._active_rolling)
        self._need_agg = bool(self._active_agg)
        # Persisted-column sets for thin nulling (columns not selected are written NULL).
        self._window_cols = registry.active_columns(self._active_rolling)
        self._agg_cols = registry.active_columns(self._active_agg)

        # spot_symbol → underlying name (classifier + spot routing); all keyed by name (no literal).
        self._spot_symbol_to_name = {u.spot_symbol: u.name for u in config.underlyings}

        # Single-owner mutable state (no lock).
        self._latest: dict[str, _Cell] = {}          # clean option symbol → last packet cell
        self._known: set[str] = set()                 # every option symbol seen (grid membership)
        self._spot: dict[str, tuple[float, float]] = {}   # name → (spot_price, recv_ts)
        self._history: dict[str, StrikeHistory] = {}  # clean symbol → M22/M24 history
        self._window: dict[str, deque] = {}           # clean symbol → deque[WindowSample] (§3.4.3)
        self._prev: dict[str, TouchBook] = {}         # clean symbol → prior second's book (ΔQ/OFI)

        m = config.metrics
        windows = list(m["time_windows_sec"])
        self._time_windows = tuple(int(w) for w in windows)
        self._hist_maxlen = max(windows)
        # Window history must reach BP_{t-2N} for acceleration at the largest window (decision 44).
        self._window_maxlen = 2 * max(windows) + 1
        # Per-underlying aggregate radii (in strikes): SMALL/MEDIUM/LARGE (§3.4.4-A). Keyed by name.
        self._agg_radii = {
            u.name: {
                "SMALL": int(m["small_window_strikes"]),
                "MEDIUM": int(u.atm_max_strike_range) // int(m["medium_window_divisor"]),
                "LARGE": int(u.atm_max_strike_range),
            }
            for u in config.underlyings
        }
        self._ctx = MetricContext(
            decay_k=float(m["decay_k"]),
            effective_depth_pct=float(m["effective_depth_pct"]),
            round_number_multiples=tuple(m["round_number_multiples"]),
            book_pressure_levels=int(m["book_pressure_levels"]),
            wall_sigma_mult=float(m["wall_sigma_mult"]),
            fill_probe_qty=float(m["fill_probe_qty"]),
            stability_window=int(windows[0]),  # M22/M24 use the shortest (most responsive) window
            regime=dict(config.regime),        # §3.4.4-C thresholds for the regime body
        )

        # Degraded-mode watermarks (§5.1) — reads live qsize vs a fraction of max_queue_size.
        q = config.queues
        self._max_q = int(q["max_queue_size"])
        self._warn_q = self._max_q * float(q["warn_watermark_pct"]) / 100.0
        self._crit_q = self._max_q * float(q["critical_watermark_pct"]) / 100.0
        self._degraded_prev = 0

        # Counters (exposed via stats() for the P6 health file).
        self.records_written = 0
        self.spot_rows_written = 0
        self.unknown_symbol_total = 0
        self.stale_rows_total = 0
        self.ticks_shed_total = 0
        self.db_rows_dropped_total = 0
        # P8: per-second cycle timing (§6.4 perf target < 15 ms thin). Bounded ring, processor-thread
        # only (single owner — no lock). Recorded on every emit_second call incl. replay.
        self._cycle_ms: deque = deque(maxlen=300)

    # ------------------------------------------------------------------ thread loop
    def run(self) -> None:  # pragma: no cover — exercised via the graceful-drain integration test
        interval = self._interval
        next_b = (math.floor(self._time() / interval) + 1) * interval
        try:
            while not self._shutdown.is_set() or not self._proc_queue.empty():
                try:
                    pkt = self._proc_queue.get(timeout=0.2)
                except queue.Empty:
                    pkt = None
                if pkt is not None:
                    try:
                        self._ingest(pkt)
                    finally:
                        self._proc_queue.task_done()
                now = self._time()
                while now >= next_b:
                    self.emit_second(int(next_b))
                    next_b += interval
        except Exception:
            logger.exception("TickProcessor crashed")

    # ------------------------------------------------------------------ ingest (cache update)
    def ingest(self, pkt: dict) -> None:
        """Public entry to feed one packet into the cache. The live thread uses the internal ``_ingest``
        from its ``run()`` loop; the offline replay driver (`replay.py`) calls this directly since it
        drives the resample synchronously off packet ``recv_ts`` instead of via the queue thread
        (plan decision 67). Thin wrapper — no behavior change."""
        self._ingest(pkt)

    def _ingest(self, pkt: dict) -> None:
        raw_symbol = pkt.get("symbol")
        clean = strip_suffix(raw_symbol)
        recv_ts = pkt.get("recv_ts")
        if recv_ts is None:
            recv_ts = self._time()

        if clean in self._im.symbol_to_strike_map:
            self._latest[clean] = _Cell(pkt, float(recv_ts))
            self._known.add(clean)
            return
        name = self._spot_symbol_to_name.get(clean)
        if name is not None:
            ltp = pkt.get("ltp")
            if ltp is not None and float(ltp) > 0:
                self._spot[name] = (float(ltp), float(recv_ts))
            return
        self.unknown_symbol_total += 1
        logger.debug("dropping tick for unknown symbol %r", raw_symbol)

    # ------------------------------------------------------------------ per-second emit (pure seam)
    def emit_second(self, now_epoch: int) -> list[dict]:
        """Emit one second's rows for every tracked symbol. Pure w.r.t. the injected clock — P7 replay
        calls this directly with virtual timestamps. Returns the db_queue envelopes (also enqueued).

        Order per §3.4 / decision 37: spot → per-strike (+ rolling windows) → multi-strike aggregates."""
        cycle_start = time.perf_counter()
        try:
            level = self._degraded_level()
            self._log_degraded(level)
            heavy_skip = level >= 1  # §5.1: skip CPU-heavy rolling work in degraded mode, keep cadence
            envelopes: list[dict] = []

            spot_rows = self._spot_rows(now_epoch)
            if spot_rows:
                self._push(envelopes, "spot_states", spot_rows)
                self.spot_rows_written += len(spot_rows)

            opt_rows: list[tuple] = []
            window_rows: list[tuple] = []
            feats_by_name: dict[str, list] = defaultdict(list)
            for clean in sorted(self._known):
                row, feat, name, w_rows = self._compute_option(now_epoch, clean, heavy_skip)
                opt_rows.append(row)
                if feat is not None:
                    feats_by_name[name].append(feat)
                window_rows.extend(w_rows)
            if opt_rows:
                self._push(envelopes, "option_strike_metrics", opt_rows)
                self.records_written += len(opt_rows)
            if window_rows:
                self._push(envelopes, "strike_window_metrics", window_rows)
            if self._need_agg:
                agg_rows = self._agg_rows(now_epoch, feats_by_name)
                if agg_rows:
                    self._push(envelopes, "aggregated_window_metrics", agg_rows)

            if level >= 2:
                self._shed(now_epoch)
            return envelopes
        finally:
            # Record on every path (§6.4 perf observability). perf_counter → wall ms; single owner.
            self._cycle_ms.append((time.perf_counter() - cycle_start) * 1000.0)

    def _push(self, envelopes: list, table: str, rows: list) -> None:
        env = {"table": table, "rows": rows}
        envelopes.append(env)
        self._emit(env)

    def _spot_rows(self, ts: int) -> list[tuple]:
        rows = []
        for u in self._config.underlyings:
            sp = self._spot.get(u.name)
            if sp is None:
                continue
            price, _ = sp
            atm = self._resolve_atm(u.name, price)
            if atm is None:
                continue
            rows.append((ts, u.spot_symbol, price, atm))
        return rows

    def _resolve_atm(self, name: str, spot: float) -> int | None:
        strikes = self._im.active_strikes_list.get(name)
        if not strikes:
            return None
        closest = min(strikes, key=lambda k: abs(k - spot))
        return int(closest)

    def _compute_option(self, ts: int, clean: str, heavy_skip: bool) -> tuple:
        """Build one option strike's row (+ its rolling-window rows + aggregate feature) for this second.

        Returns ``(option_row_tuple, StrikeFeatures|None, underlying_name, window_row_tuples)``."""
        meta = self._im.symbol_to_strike_map[clean]
        name = meta["underlying"]
        cell = self._latest.get(clean)
        row = dict.fromkeys(OPTION_COLUMNS)
        row["timestamp"] = ts
        row["symbol"] = clean
        row["strike_price"] = meta["strike"]
        row["option_type"] = meta["option_type"]

        stale = cell is None or (ts - cell.recv_ts) > self._staleness
        if stale:
            self.stale_rows_total += 1
            if cell is not None:  # keep self-describing capability even on a stale row
                row["depth_levels"] = cell.packet.get("depth_levels")
                row["is_50_depth"] = _as_int_bool(cell.packet.get("is_50_depth"))
            row["confidence"] = 0.0  # §6.2 outage second
            self._history_for(clean).push(None, None, None, False)
            w_rows: list[tuple] = []
            if self._need_rolling:
                self._prev[clean] = None  # a gap breaks price-alignment / OFI continuity
                self._append_sample(clean, WindowSample(ts=ts, valid=False))
                w_rows = self._window_rows(ts, clean, heavy_skip)
            return tuple(row[c] for c in OPTION_COLUMNS), None, name, w_rows

        pkt = cell.packet
        row["depth_levels"] = pkt.get("depth_levels")
        row["is_50_depth"] = _as_int_bool(pkt.get("is_50_depth"))
        row["ltp"] = pkt.get("ltp")

        snap = BookSnapshot(pkt.get("depth"),
                            depth_levels=pkt.get("depth_levels"), is_50_depth=pkt.get("is_50_depth"))
        # Rebind the shared context for this symbol/second (single-threaded — safe to mutate).
        ctx = self._ctx
        ctx.tick_size = self._im.tick_size_map.get(clean)
        ctx.ltp = pkt.get("ltp")
        ctx.feed_time = pkt.get("feed_time")
        ctx.now_local = cell.recv_ts
        # Populate M22/M24 history with this second BEFORE the bodies run (decision 41).
        hist = self._history_for(clean)
        touch_key = (snap.best_bid_px, snap.best_ask_px) if snap.has_touch else None
        hist.push(touch_key, topn_obi_value(snap, 5, ctx.eps), relative_spread_value(snap, ctx.eps),
                  ctx.feed_time not in (None, 0))
        ctx.history = hist

        for spec in self._active_per_strike:
            for col, val in registry.METRIC_FUNCS[spec.name](snap, ctx).items():
                row[col] = val

        feat = None
        w_rows = []
        if self._need_rolling or self._need_agg:
            core = self._core(snap, ctx)
            if self._need_rolling:
                ofi, dq_plus, dq_minus = self._instantaneous(clean, snap)
                row["ofi"] = ofi  # instantaneous touch OFI back-filled (§3.4.3-E)
                self._append_sample(clean, WindowSample(
                    ts=ts, valid=True, ltp=pkt.get("ltp"), spread=core["spread"], wobi=core["wobi"],
                    book_pressure=core["book_pressure"], micro_price=core["micro"],
                    dq_plus=dq_plus, dq_minus=dq_minus, ofi=ofi, wall_price=core["wall_price"]))
                w_rows = self._window_rows(ts, clean, heavy_skip)
            if self._need_agg:
                feat = StrikeFeatures(
                    option_type=meta["option_type"], strike=float(meta["strike"]), valid=True,
                    book_pressure=core["book_pressure"], spread=core["spread"],
                    relative_spread=core["rel_spread"], q_bid_w=core["q_bid_w"], q_ask_w=core["q_ask_w"],
                    total_qty=core["total_qty"], wall_size=core["wall_size"],
                    quote_stability=core["quote_stability"])
        return tuple(row[c] for c in OPTION_COLUMNS), feat, name, w_rows

    def _history_for(self, clean: str) -> StrikeHistory:
        h = self._history.get(clean)
        if h is None:
            h = StrikeHistory(self._hist_maxlen)
            self._history[clean] = h
        return h

    # ------------------------------------------------------------------ P4b: core features + windows
    def _core(self, snap: BookSnapshot, ctx: MetricContext) -> dict:
        """Compute the per-strike scalars the rolling + aggregate metrics need (always, when a rolling/
        aggregate metric is active — dependency closure, decision 37), independent of the persisted set."""
        F = registry.METRIC_FUNCS
        if snap.has_touch:
            wb, wa = ctx.w(snap.L_bid), ctx.w(snap.L_ask)
            q_bid_w = float((snap.bid_qty * wb).sum())
            q_ask_w = float((snap.ask_qty * wa).sum())
            total_qty = float(snap.bid_qty.sum() + snap.ask_qty.sum())
        else:
            q_bid_w = q_ask_w = total_qty = 0.0
        wall_size, wall_price = self._wall(snap, ctx)
        return {
            "spread": snap.spread if snap.has_touch else None,
            "wobi": F["weighted_obi"](snap, ctx)["weighted_obi"],
            "book_pressure": F["book_pressure"](snap, ctx)["book_pressure"],
            "micro": F["micro_price"](snap, ctx)["micro_price"],
            "rel_spread": relative_spread_value(snap, ctx.eps),
            "quote_stability": F["quote_stability"](snap, ctx)["quote_stability"],
            "q_bid_w": q_bid_w, "q_ask_w": q_ask_w, "total_qty": total_qty,
            "wall_size": wall_size, "wall_price": wall_price,
        }

    @staticmethod
    def _wall(snap: BookSnapshot, ctx: MetricContext) -> tuple:
        """Dominant wall size (max resting qty, for pinning) + its price when it qualifies as a wall
        (≥ mean + wall_sigma_mult·σ over populated levels, for persistence/events; else None)."""
        if not (snap.L_bid or snap.L_ask):
            return None, None
        sizes = np.concatenate([snap.bid_qty, snap.ask_qty])
        prices = np.concatenate([snap.bid_px, snap.ask_px])
        j = int(np.argmax(sizes))
        wall_size = float(sizes[j])
        thresh = sizes.mean() + ctx.wall_sigma_mult * sizes.std() if sizes.size >= 2 else sizes.mean()
        wall_price = float(prices[j]) if wall_size >= thresh else None
        return wall_size, wall_price

    def _instantaneous(self, clean: str, snap: BookSnapshot) -> tuple:
        """Instantaneous touch OFI + price-aligned ΔQ vs the prior second; rolls the prev-book (§3.4.3)."""
        cur = touch_book(snap, 10)
        prev = self._prev.get(clean)
        ofi = ofi_instant(cur, prev)
        if snap.depth() >= 10:  # ΔQ is a top-10 deep-book metric (min_depth 10, decision 47)
            dq_plus, dq_minus = liquidity_delta_instant(prev, cur.bid, cur.ask)
        else:
            dq_plus, dq_minus = None, None
        self._prev[clean] = cur
        return ofi, dq_plus, dq_minus

    def _append_sample(self, clean: str, sample: WindowSample) -> None:
        dq = self._window.get(clean)
        if dq is None:
            dq = deque(maxlen=self._window_maxlen)
            self._window[clean] = dq
        dq.append(sample)

    def _window_rows(self, ts: int, clean: str, heavy_skip: bool) -> list[tuple]:
        hist = list(self._window[clean])
        rows = []
        for n in self._time_windows:
            row = dict.fromkeys(STRIKE_WINDOW_COLUMNS)
            row["timestamp"], row["symbol"], row["time_window"] = ts, clean, n
            for spec in self._active_rolling:
                if heavy_skip and spec.name in HEAVY_METRICS:
                    continue  # NULL heavy columns in degraded mode; the 1s grid still emits a row
                for col, val in registry.METRIC_FUNCS[spec.name](hist, n, self._ctx).items():
                    row[col] = val
            rows.append(tuple(row[c] for c in STRIKE_WINDOW_COLUMNS))
        return rows

    # ------------------------------------------------------------------ P4b: multi-strike aggregates
    def _agg_rows(self, ts: int, feats_by_name: dict) -> list[tuple]:
        rows = []
        for u in self._config.underlyings:
            feats = feats_by_name.get(u.name)
            sp = self._spot.get(u.name)
            if not feats or sp is None:
                continue
            spot = sp[0]
            atm = self._resolve_atm(u.name, spot)
            step = self._strike_step(u.name)
            if atm is None or step is None:
                continue
            for label, cols in compute_underlying(feats, spot, float(atm), float(step),
                                                  self._agg_radii[u.name], self._ctx):
                row = dict.fromkeys(AGG_COLUMNS)
                row["timestamp"], row["underlying"], row["strike_window"] = ts, u.name, label
                for col, val in cols.items():
                    if col in self._agg_cols:  # thin nulling: only persist selected aggregate columns
                        row[col] = val
                rows.append(tuple(row[c] for c in AGG_COLUMNS))
        return rows

    def _strike_step(self, name: str) -> int | None:
        """The strike step for an underlying, derived from the resolved chain's sorted strikes (the
        smallest adjacent gap on the contiguous grid). Keyed by ``name`` — no literal."""
        strikes = self._im.active_strikes_list.get(name)
        if not strikes or len(strikes) < 2:
            return None
        diffs = {round(strikes[i + 1] - strikes[i]) for i in range(len(strikes) - 1)}
        diffs.discard(0)
        return min(diffs) if diffs else None

    # ------------------------------------------------------------------ degraded mode (skeleton)
    def _degraded_level(self) -> int:
        load = max(self._proc_queue.qsize(), self._db_queue.qsize())
        if load >= self._crit_q:
            return 2
        if load >= self._warn_q:
            return 1
        return 0

    def _log_degraded(self, level: int) -> None:
        if level != self._degraded_prev:
            if level == 0:
                logger.info("processor left degraded mode")
            else:
                logger.warning("processor degraded mode level %d (queue watermark reached)", level)
            self._degraded_prev = level

    def _shed(self, now_epoch: int) -> None:
        """Critical-pressure relief: evict already-stale cached ticks for the least-active symbols.
        They still emit a NULL row via ``_known`` (grid preserved). P6 adds proc_queue-side shedding."""
        dead = [c for c, cell in self._latest.items() if (now_epoch - cell.recv_ts) > self._staleness]
        for clean in dead:
            del self._latest[clean]
            self.ticks_shed_total += 1

    # ------------------------------------------------------------------ db_queue emission
    def _emit(self, envelope: dict) -> None:
        try:
            self._db_queue.put(envelope, timeout=_DB_PUT_TIMEOUT_SEC)
        except queue.Full:
            self.db_rows_dropped_total += len(envelope.get("rows", ()))
            logger.warning("db_queue full — dropped %s rows for %s (analytics sheds; raw is protected)",
                           len(envelope.get("rows", ())), envelope.get("table"))

    # ------------------------------------------------------------------ observability
    def stats(self) -> dict:
        return {
            "records_written": self.records_written,
            "spot_rows_written": self.spot_rows_written,
            "unknown_symbol_total": self.unknown_symbol_total,
            "stale_rows_total": self.stale_rows_total,
            "ticks_shed_total": self.ticks_shed_total,
            "db_rows_dropped_total": self.db_rows_dropped_total,
            "tracked_symbols": len(self._known),
            "degraded_level": self._degraded_prev,
            "cycle_ms_p50": self._cycle_percentile(50.0),
            "cycle_ms_max": max(self._cycle_ms) if self._cycle_ms else 0.0,
        }

    def _cycle_percentile(self, pct: float) -> float:
        """Nearest-rank percentile of the recent per-second cycle times (ms); 0.0 before any cycle."""
        if not self._cycle_ms:
            return 0.0
        ordered = sorted(self._cycle_ms)
        idx = int(round((pct / 100.0) * (len(ordered) - 1)))
        return ordered[min(idx, len(ordered) - 1)]


def _as_int_bool(value: object) -> int | None:
    """Normalize the packet's ``is_50_depth`` to the live SQLite 0/1 convention (§4.1a)."""
    if value is None:
        return None
    return 1 if value else 0