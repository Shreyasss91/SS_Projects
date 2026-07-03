"""TickProcessor engine (spec §3.4.1, §5.1, §6.2) — ingest/classify, resample emit, staleness,
forward-fill, ATM, thin selection, degraded mode, and emit_second determinism (the P7 replay seam).

All offline: injected clock + plain queues + a lightweight InstrumentManager stub (the processor reads
only ``symbol_to_strike_map`` / ``active_strikes_list`` / ``tick_size_map``).
"""

from __future__ import annotations

import queue
import threading
import time

import pytest

from market_depth_recorder.config import load_config
from market_depth_recorder.processor import OPTION_COLUMNS, TickProcessor, strip_suffix

CE = "NIFTY26JUN2423400CE"
PE = "NIFTY26JUN2423400PE"
CE2 = "NIFTY26JUN2423500CE"


class FakeIM:
    """Minimal stand-in for the resolved InstrumentManager (only the maps the processor reads)."""

    def __init__(self):
        self.symbol_to_strike_map = {
            CE: {"underlying": "NIFTY", "strike": 23400.0, "option_type": "CE"},
            PE: {"underlying": "NIFTY", "strike": 23400.0, "option_type": "PE"},
            CE2: {"underlying": "NIFTY", "strike": 23500.0, "option_type": "CE"},
        }
        self.active_strikes_list = {"NIFTY": [23300.0, 23400.0, 23500.0],
                                    "SENSEX": [80000.0, 80100.0]}
        self.tick_size_map = {CE: 0.05, PE: 0.05, CE2: 0.05}


def depth_packet(symbol, *, recv_ts, ltp=100.0, feed_time=None):
    bids = [(100.0, 10, 2), (99.5, 20, 3), (99.0, 5, 1)]
    asks = [(100.5, 8, 2), (101.0, 12, 4), (101.5, 6, 1)]
    return {
        "symbol": symbol, "exchange": "NFO", "mode": 3, "ltp": ltp, "recv_ts": recv_ts,
        "feed_time": feed_time, "depth_levels": 3, "is_50_depth": 0,
        "depth": {"buy": [{"price": p, "quantity": q, "orders": o} for p, q, o in bids],
                  "sell": [{"price": p, "quantity": q, "orders": o} for p, q, o in asks]},
    }


def spot_packet(symbol, *, recv_ts, ltp):
    return {"symbol": symbol, "exchange": "NSE_INDEX", "mode": 1, "ltp": ltp, "recv_ts": recv_ts}


@pytest.fixture
def cfg(base_config, write_config):
    return load_config(write_config(base_config))


def make_proc(cfg, *, active="all", proc_q=None, db_q=None):
    proc_q = proc_q or queue.Queue(maxsize=cfg.queues["max_queue_size"])
    db_q = db_q or queue.Queue(maxsize=cfg.queues["max_queue_size"])
    p = TickProcessor(cfg, FakeIM(), proc_q, db_q, threading.Event(),
                      time_fn=lambda: 0.0, active_metrics=active)
    return p, proc_q, db_q


def row_dict(table_env, symbol):
    for r in table_env["rows"]:
        d = dict(zip(OPTION_COLUMNS, r))
        if d["symbol"] == symbol:
            return d
    raise AssertionError(f"{symbol} not in rows")


def envelopes_by_table(envs):
    return {e["table"]: e for e in envs}


# --------------------------------------------------------------------------------------------------
# Ingest / classification
# --------------------------------------------------------------------------------------------------
def test_strip_suffix():
    assert strip_suffix("FOO:50") == "FOO"
    assert strip_suffix("FOO") == "FOO"
    assert strip_suffix(None) == ""


def test_ingest_classifies_option_spot_unknown(cfg):
    p, _, _ = make_proc(cfg)
    p._ingest(depth_packet(CE + ":50", recv_ts=1.0))     # option with transport suffix
    p._ingest(spot_packet("NIFTY", recv_ts=1.0, ltp=23412.0))
    p._ingest(depth_packet("WHO_DIS", recv_ts=1.0))       # unknown → counted, dropped
    assert CE in p._known and CE in p._latest              # suffix stripped for the DB key
    assert p._spot["NIFTY"][0] == pytest.approx(23412.0)
    assert p.unknown_symbol_total == 1


def test_spot_rejects_non_positive_ltp(cfg):
    p, _, _ = make_proc(cfg)
    p._ingest(spot_packet("NIFTY", recv_ts=1.0, ltp=0.0))
    assert "NIFTY" not in p._spot


# --------------------------------------------------------------------------------------------------
# emit_second: rows, ATM, envelopes on db_queue
# --------------------------------------------------------------------------------------------------
def test_emit_produces_spot_and_option_envelopes(cfg):
    p, _, db_q = make_proc(cfg)
    p._ingest(spot_packet("NIFTY", recv_ts=1.0, ltp=23412.0))
    p._ingest(depth_packet(CE, recv_ts=1.0))
    envs = p.emit_second(2)
    tables = envelopes_by_table(envs)
    assert set(tables) == {"spot_states", "option_strike_metrics"}
    # ATM: spot 23412 → closest active strike 23400.
    assert tables["spot_states"]["rows"][0] == (2, "NIFTY", pytest.approx(23412.0), 23400)
    ce = row_dict(tables["option_strike_metrics"], CE)
    assert ce["timestamp"] == 2 and ce["strike_price"] == 23400.0 and ce["option_type"] == "CE"
    assert ce["spread"] == pytest.approx(0.5)
    assert ce["ofi"] is None  # rolling column deferred to P4b
    # Envelopes were also enqueued for the DB writer.
    assert db_q.qsize() == 2


def test_no_spot_row_before_spot_known(cfg):
    p, _, _ = make_proc(cfg)
    p._ingest(depth_packet(CE, recv_ts=1.0))
    tables = envelopes_by_table(p.emit_second(2))
    assert "spot_states" not in tables            # spot_price is NOT NULL — skip until known
    assert "option_strike_metrics" in tables


# --------------------------------------------------------------------------------------------------
# Thin selection vs full catalog
# --------------------------------------------------------------------------------------------------
def test_thin_selection_only_fills_active_columns(cfg):
    thin = ["spread", "weighted_obi", "best_bid_qty", "best_ask_qty"]
    p, _, _ = make_proc(cfg, active=thin)
    p._ingest(depth_packet(CE, recv_ts=1.0))
    ce = row_dict(envelopes_by_table(p.emit_second(2))["option_strike_metrics"], CE)
    assert ce["spread"] is not None and ce["weighted_obi"] is not None
    assert ce["best_bid_qty"] == pytest.approx(10.0)
    # Not selected → NULL on the thin path (fixed-width row, §5.1).
    assert ce["raw_obi"] is None and ce["micro_price"] is None and ce["vamp"] is None


def test_full_catalog_fills_many_columns(cfg):
    p, _, _ = make_proc(cfg, active="all")
    p._ingest(depth_packet(CE, recv_ts=1.0, feed_time=1.5))
    ce = row_dict(envelopes_by_table(p.emit_second(2))["option_strike_metrics"], CE)
    for col in ("spread", "mid_price", "micro_price", "raw_obi", "weighted_obi", "queue_imbalance",
                "vamp", "spread_ticks", "confidence"):
        assert ce[col] is not None, col
    assert ce["spread_ticks"] == pytest.approx(10.0)  # 0.5 / tick 0.05


# --------------------------------------------------------------------------------------------------
# Staleness / forward-fill / grid
# --------------------------------------------------------------------------------------------------
def test_forward_fill_repeats_last_snapshot(cfg):
    p, _, _ = make_proc(cfg, active="all")
    p._ingest(depth_packet(CE, recv_ts=1.0))
    a = row_dict(envelopes_by_table(p.emit_second(2))["option_strike_metrics"], CE)
    b = row_dict(envelopes_by_table(p.emit_second(3))["option_strike_metrics"], CE)  # no new tick
    assert a["spread"] == b["spread"] == pytest.approx(0.5)     # forward-filled, grid intact


def test_staleness_nulls_row_but_keeps_grid(cfg):
    p, _, _ = make_proc(cfg, active="all")
    p._ingest(depth_packet(CE, recv_ts=1.0))
    # staleness_timeout = 5.0 → at t=10 the last tick (t=1) is stale.
    ce = row_dict(envelopes_by_table(p.emit_second(10))["option_strike_metrics"], CE)
    assert ce["symbol"] == CE and ce["timestamp"] == 10        # still emitted (grid preserved)
    assert ce["spread"] is None and ce["ltp"] is None
    assert ce["confidence"] == 0.0                             # §6.2 outage second
    assert p.stale_rows_total == 1


def test_quote_stability_warmup(cfg):
    p, _, _ = make_proc(cfg, active="all")
    p._ingest(depth_packet(CE, recv_ts=1.0))
    first = row_dict(envelopes_by_table(p.emit_second(2))["option_strike_metrics"], CE)
    assert first["quote_stability"] is None                    # <2 samples → warm-up NULL
    p._ingest(depth_packet(CE, recv_ts=2.0))                   # same touch price
    second = row_dict(envelopes_by_table(p.emit_second(3))["option_strike_metrics"], CE)
    assert second["quote_stability"] == pytest.approx(1.0)     # touch unchanged across the window


# --------------------------------------------------------------------------------------------------
# Determinism (P7 seam) + degraded mode
# --------------------------------------------------------------------------------------------------
def test_emit_second_deterministic(cfg):
    # Two independent runs with identical inputs + clock must produce identical rows (the P7 seam):
    # each emit_second advances per-symbol history, so determinism is run-to-run, not call-idempotence.
    def run():
        p, _, _ = make_proc(cfg, active="all")
        out = []
        p._ingest(depth_packet(CE, recv_ts=1.0, feed_time=1.4))
        out.append(envelopes_by_table(p.emit_second(2))["option_strike_metrics"]["rows"])
        p._ingest(depth_packet(CE, recv_ts=2.0, feed_time=2.4))
        out.append(envelopes_by_table(p.emit_second(3))["option_strike_metrics"]["rows"])
        return out

    assert run() == run()


def test_degraded_level_and_shed(base_config, write_config):
    # Watermarks are a fraction of queues.max_queue_size — shrink it so the test can cross them.
    base_config["queues"]["max_queue_size"] = 100
    cfg = load_config(write_config(base_config))
    proc_q = queue.Queue(maxsize=100)
    p, _, _ = make_proc(cfg, active="all", proc_q=proc_q)
    p._ingest(depth_packet(CE, recv_ts=1.0))
    for _ in range(95):        # past the 90% critical watermark
        proc_q.put(None)
    assert p._degraded_level() == 2
    # At a much later second the cached CE tick is stale → critical shed evicts it (counted).
    p.emit_second(100)
    assert p.ticks_shed_total >= 1
    assert CE in p._known      # still tracked → grid continues as NULL rows


def test_run_thread_drains_and_emits(cfg):
    # Exercise the real run() loop: ingest from proc_queue, cross a 1s boundary, emit, drain on shutdown.
    proc_q = queue.Queue(maxsize=cfg.queues["max_queue_size"])
    db_q = queue.Queue(maxsize=cfg.queues["max_queue_size"])
    shutdown = threading.Event()
    p = TickProcessor(cfg, FakeIM(), proc_q, db_q, shutdown, active_metrics="all")  # real clock
    proc_q.put(spot_packet("NIFTY", recv_ts=time.time(), ltp=23412.0))
    proc_q.put(depth_packet(CE, recv_ts=time.time()))
    p.start()
    try:
        time.sleep(1.3)          # let at least one aligned second fire
    finally:
        shutdown.set()
        p.join(timeout=5)
    assert not p.is_alive()       # thread reaped (FD hygiene)
    assert p.records_written > 0
    tables = set()
    while not db_q.empty():
        tables.add(db_q.get()["table"])
    assert "option_strike_metrics" in tables


def test_db_queue_drop_counter_on_full(cfg):
    db_q = queue.Queue(maxsize=1)
    db_q.put("occupied")  # leave no room
    p, _, _ = make_proc(cfg, active="all", db_q=db_q)
    p._ingest(depth_packet(CE, recv_ts=1.0))
    p.emit_second(2)      # both envelopes fail to enqueue
    assert p.db_rows_dropped_total >= 1