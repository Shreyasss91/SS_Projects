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
from collections.abc import Callable

from .config import Config
from .instrument_manager import InstrumentManager
from .metrics import registry
from .metrics.per_strike import relative_spread_value, topn_obi_value
from .metrics.registry import FAM_PER_STRIKE
from .metrics.snapshot import BookSnapshot, MetricContext, StrikeHistory
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

        # Active per-strike specs that actually have a bound body (P4a: the §3.4.2 family only).
        active = registry.resolve_active(live)
        self._active_per_strike = [
            s for s in active if s.family == FAM_PER_STRIKE and s.name in registry.METRIC_FUNCS
        ]

        # spot_symbol → underlying name (classifier + spot routing); all keyed by name (no literal).
        self._spot_symbol_to_name = {u.spot_symbol: u.name for u in config.underlyings}

        # Single-owner mutable state (no lock).
        self._latest: dict[str, _Cell] = {}          # clean option symbol → last packet cell
        self._known: set[str] = set()                 # every option symbol seen (grid membership)
        self._spot: dict[str, tuple[float, float]] = {}   # name → (spot_price, recv_ts)
        self._history: dict[str, StrikeHistory] = {}  # clean symbol → M22/M24 history

        m = config.metrics
        windows = list(m["time_windows_sec"])
        self._hist_maxlen = max(windows)
        self._ctx = MetricContext(
            decay_k=float(m["decay_k"]),
            effective_depth_pct=float(m["effective_depth_pct"]),
            round_number_multiples=tuple(m["round_number_multiples"]),
            book_pressure_levels=int(m["book_pressure_levels"]),
            wall_sigma_mult=float(m["wall_sigma_mult"]),
            fill_probe_qty=float(m["fill_probe_qty"]),
            stability_window=int(windows[0]),  # M22/M24 use the shortest (most responsive) window
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
        calls this directly with virtual timestamps. Returns the db_queue envelopes (also enqueued)."""
        level = self._degraded_level()
        self._log_degraded(level)
        envelopes: list[dict] = []

        spot_rows = self._spot_rows(now_epoch)
        if spot_rows:
            env = {"table": "spot_states", "rows": spot_rows}
            envelopes.append(env)
            self._emit(env)
            self.spot_rows_written += len(spot_rows)

        opt_rows = [self._option_row(now_epoch, clean) for clean in sorted(self._known)]
        if opt_rows:
            env = {"table": "option_strike_metrics", "rows": opt_rows}
            envelopes.append(env)
            self._emit(env)
            self.records_written += len(opt_rows)

        if level >= 2:
            self._shed(now_epoch)
        return envelopes

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

    def _option_row(self, ts: int, clean: str) -> tuple:
        meta = self._im.symbol_to_strike_map[clean]
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
            return tuple(row[c] for c in OPTION_COLUMNS)

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
            fn = registry.METRIC_FUNCS[spec.name]
            for col, val in fn(snap, ctx).items():
                row[col] = val
        return tuple(row[c] for c in OPTION_COLUMNS)

    def _history_for(self, clean: str) -> StrikeHistory:
        h = self._history.get(clean)
        if h is None:
            h = StrikeHistory(self._hist_maxlen)
            self._history[clean] = h
        return h

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
        }


def _as_int_bool(value: object) -> int | None:
    """Normalize the packet's ``is_50_depth`` to the live SQLite 0/1 convention (§4.1a)."""
    if value is None:
        return None
    return 1 if value else 0