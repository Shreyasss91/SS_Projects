"""P8 — whole-pipeline integration & soak harness (the real four-thread pipeline end-to-end).

This is the automated recorded-feed harness the plan's P8 calls for: it drives the **real**
``_build_default_pipeline`` (real ``RawTickFileWriter`` + ``SQLiteLiveWriter`` + ``TickProcessor`` +
``DepthWebSocketClient``, three real bounded queues, both shutdown events, a real ``InstrumentManager``
reconstructed from a HEADER block) with a scripted, self-paced recorded feed injected through a
``RecordedTransport`` (a real ``FeedTransport``). It then exercises the **real** end-of-session reprocess
**subprocess** (``python -m market_depth_recorder --replay --catchup``) against the produced lossless raw
log, rebuilding the fat DuckDB store, and proves determinism via ``replay.verify``.

Everything runs offline — no live broker / WS / market. The feed shape mirrors production: NIFTY/NFO
50-level TBT depth (``:50`` topic, ``is_50_depth`` true, per-level ``orders`` populated) and SENSEX/BFO
5-level depth. The full FD audit is assertion-backed here (clean thread joins, HEADER..EOF-framed raw log,
populated live store, no ``.tmp``/``.building_*``/lock residue, reaped subprocess).
"""

from __future__ import annotations

import gzip
import json
import os
import sqlite3
import subprocess
import sys
import threading
import time

import pytest

from market_depth_recorder import replay
from market_depth_recorder.config import load_config
from market_depth_recorder.database_writer import SQLiteLiveWriter
from market_depth_recorder.file_writer import RawTickFileWriter
from market_depth_recorder.instrument_manager import InstrumentManager
from market_depth_recorder.main import RecorderOrchestrator
from market_depth_recorder.utils import now_ist

from .conftest import PACKAGE_ROOT

# Must be TODAY's IST date, not a hardcoded past date: the file/db writers' IST date-rollover guard
# fires when session_date != the wall-clock IST day, moving all data to a new dated file and leaving
# the session_date file empty (which this test inspects). now_ist().date() matches the writers' basis.
SESSION_DATE = now_ist().date()
_TICK = 0.05


# --------------------------------------------------------------------------------------------------
# Recorded-feed transport — a real FeedTransport that plays a scripted, self-paced feed.
# --------------------------------------------------------------------------------------------------
class RecordedTransport:
    """Plays a list of ``(delay_sec, market_data_msg)`` through the real feed callbacks, then blocks like
    a live socket until :meth:`close`. Adapts ``test_websocket_client.FakeTransport`` with recv-time
    pacing so the processor's 1-second grid actually ticks across the run."""

    def __init__(self, script):
        self._script = list(script)
        self.sent: list = []
        self._closed = threading.Event()
        self.on_open = self.on_message = self.on_close = None

    def bind(self, *, on_open, on_message, on_close):
        self.on_open, self.on_message, self.on_close = on_open, on_message, on_close

    def run_session(self):
        if self.on_open:
            self.on_open()
        for delay, msg in self._script:
            if self._closed.is_set():
                return
            if delay and self._closed.wait(delay):  # interruptible real sleep
                return
            if self.on_message:
                self.on_message(msg)
        self._closed.wait()  # block until the orchestrator's feed.stop() closes us

    def send(self, frame):
        self.sent.append(frame)

    def close(self):
        self._closed.set()


# --------------------------------------------------------------------------------------------------
# Scenario — chains + a scripted NIFTY(50-level)/SENSEX(5-level) feed.
# --------------------------------------------------------------------------------------------------
def _sym(name: str, strike: int, opt: str) -> str:
    return f"{name}24JUL25{strike}{opt}"


def _chain_block(name: str, exch: str, strikes: list[int]) -> dict:
    contracts = [[float(k), _sym(name, k, "CE"), _sym(name, k, "PE"), _TICK] for k in strikes]
    return {"option_exchange": exch, "expiry": "24-JUL-25", "strike_step": 100.0,
            "contracts": contracts}


def _depth_msg(symbol, exchange, *, levels, is50, ltp, feed_time, n_populated, shift=0.0):
    """A ``market_data`` depth envelope with per-level ``orders`` populated (M13/M14 computable)."""
    buy = [{"price": round(ltp - _TICK * (i + 1), 2), "quantity": 100 - i * 3 + int(shift),
            "orders": 3 + i} for i in range(n_populated)]
    sell = [{"price": round(ltp + _TICK * (i + 1), 2), "quantity": 90 - i * 3 + int(shift),
             "orders": 2 + i} for i in range(n_populated)]
    return {"type": "market_data", "symbol": symbol, "exchange": exchange, "mode": 3, "data": {
        "ltp": ltp, "timestamp": int(feed_time), "feed_time": int(feed_time),
        "depth_levels": levels, "is_50_depth": is50,
        "total_buy_qty": sum(b["quantity"] for b in buy),
        "total_sell_qty": sum(s["quantity"] for s in sell),
        "depth": {"buy": buy, "sell": sell}}}


def _spot_msg(name, exchange, ltp):
    return {"type": "market_data", "symbol": name, "exchange": exchange, "mode": 1,
            "data": {"ltp": ltp, "timestamp": int(time.time())}}


NIFTY_STRIKES = [23300, 23400, 23500]
SENSEX_STRIKES = [79900, 80000, 80100]


def _header_instruments() -> dict:
    return {
        "NIFTY": _chain_block("NIFTY", "NFO", NIFTY_STRIKES),
        "SENSEX": _chain_block("SENSEX", "BFO", SENSEX_STRIKES),
    }


def _script():
    """~2.5 s of feed across three 1-second buckets (a prior second exists for rolling ΔQ/OFI)."""
    ft = time.time()

    def nifty_depth(strike, ltp, shift=0.0):
        return _depth_msg(_sym("NIFTY", strike, "CE") + ":50", "NFO", levels=50, is50=1, ltp=ltp,
                          feed_time=ft, n_populated=10, shift=shift)

    def nifty_pe(strike, ltp):
        return _depth_msg(_sym("NIFTY", strike, "PE") + ":50", "NFO", levels=50, is50=1, ltp=ltp,
                          feed_time=ft, n_populated=10)

    def sensex_depth(strike, opt, ltp):
        return _depth_msg(_sym("SENSEX", strike, opt), "BFO", levels=5, is50=0, ltp=ltp,
                          feed_time=ft, n_populated=5)

    return [
        # -- second 1 --
        (0.0, _spot_msg("NIFTY", "NSE_INDEX", 23412.0)),
        (0.0, _spot_msg("SENSEX", "BSE_INDEX", 80050.0)),
        (0.0, nifty_depth(23400, 120.0)),
        (0.0, nifty_pe(23400, 118.0)),
        (0.0, nifty_depth(23500, 70.0)),
        (0.0, sensex_depth(80000, "CE", 250.0)),
        (0.0, sensex_depth(80000, "PE", 240.0)),
        # -- second 2 (prior second now exists → rolling deltas are computable) --
        (1.2, _spot_msg("NIFTY", "NSE_INDEX", 23430.0)),
        (0.0, nifty_depth(23400, 121.0, shift=5)),
        (0.0, nifty_pe(23400, 119.0)),
        (0.0, nifty_depth(23500, 71.0)),
        (0.0, sensex_depth(80000, "CE", 251.0)),
        # -- second 3 --
        (1.2, _spot_msg("NIFTY", "NSE_INDEX", 23445.0)),
        (0.0, nifty_depth(23400, 122.0, shift=8)),
    ]


# --------------------------------------------------------------------------------------------------
def _wait_until(pred, timeout: float, interval: float = 0.05):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if pred():
            return True
        time.sleep(interval)
    return pred()


@pytest.fixture
def cfg(base_config, write_config):
    # Short WAL checkpoint + batch cadence so a ~3 s run crosses real flush/checkpoint paths.
    base_config["database"]["wal_checkpoint_interval_sec"] = 30
    base_config["database"]["batch_write_interval_ms"] = 500
    path = write_config(base_config)
    return load_config(path), path


# --------------------------------------------------------------------------------------------------
# The whole-pipeline harness.
# --------------------------------------------------------------------------------------------------
@pytest.mark.integration
def test_real_four_thread_pipeline_end_to_end(cfg):
    config, config_path = cfg
    im = InstrumentManager.from_header(config, _header_instruments())
    transport = RecordedTransport(_script())

    orch = RecorderOrchestrator(
        config, im, time_fn=time.time, transport=transport,
        reprocess_launcher=lambda *a: 0,  # unused; teardown is driven manually
    )
    orch._session_date = SESSION_DATE
    pipeline = orch._build_default_pipeline()
    orch._pipeline = pipeline

    orch._start_pipeline()
    try:
        # Wait until the processor has emitted at least one option second, then let a second bucket form.
        assert _wait_until(lambda: pipeline.processor.records_written > 0, timeout=15.0), \
            "processor never emitted an option row"
        time.sleep(1.4)
    finally:
        # Real §3.1.4 teardown drain (feed → processor → db → raw), each join(timeout=10).
        health = orch.build_health(time.time())
        orch._teardown_pipeline()

    # --- FD / thread audit: every worker joined, nothing left alive -------------------------------
    for w in (pipeline.feed, pipeline.processor, pipeline.db_writer, pipeline.raw_writer):
        assert not w.is_alive(), f"{w.name} still alive after teardown"

    # --- Tier-0 raw log: HEADER (with instruments) .. data .. EOF ---------------------------------
    raw_path = RawTickFileWriter.resolve_filename(config.recorder["output_dir"], SESSION_DATE)
    assert os.path.exists(raw_path)
    header, data_lines, eof = None, 0, None
    with gzip.open(raw_path, "rt", encoding="utf-8") as fh:
        for line in fh:
            obj = json.loads(line)
            mt = obj.get("meta_type")
            if mt == "HEADER":
                header = obj
            elif mt == "EOF":
                eof = obj
            else:
                data_lines += 1
    assert header is not None and "instruments" in header  # self-contained for replay (§8, decision 65)
    assert "NIFTY" in header["instruments"] and "SENSEX" in header["instruments"]
    assert eof is not None, "raw log has no EOF marker (clean-drain gate for reprocess)"
    assert data_lines > 0
    assert pipeline.raw_writer.eof_written is True

    # Depth audit fields survived the raw transport (the load-bearing finding: SDK would strip them).
    with gzip.open(raw_path, "rt", encoding="utf-8") as fh:
        objs = [json.loads(x) for x in fh]
    depth_pkts = [o for o in objs if o.get("meta_type") is None and o.get("mode") == 3]
    nifty_pkt = next(p for p in depth_pkts if str(p.get("symbol", "")).startswith("NIFTY"))
    assert nifty_pkt["depth_levels"] == 50 and nifty_pkt["is_50_depth"] == 1
    assert nifty_pkt["feed_time"] and nifty_pkt["symbol"].endswith(":50")
    assert nifty_pkt["depth"]["buy"][0]["orders"] > 0  # per-level orders populated → M13/M14 computable
    sensex_pkt = next(p for p in depth_pkts if str(p.get("symbol", "")).startswith("SENSEX"))
    assert sensex_pkt["depth_levels"] == 5 and sensex_pkt["is_50_depth"] == 0

    # --- Tier-1 live SQLite store: populated ------------------------------------------------------
    live_path = SQLiteLiveWriter.resolve_filename(config.recorder["output_dir"], SESSION_DATE)
    assert os.path.exists(live_path)
    con = sqlite3.connect(live_path)
    try:
        opt_rows = con.execute("SELECT COUNT(*) FROM option_strike_metrics").fetchone()[0]
        spot_rows = con.execute("SELECT COUNT(*) FROM spot_states").fetchone()[0]
        built_by = con.execute("SELECT built_by FROM recorder_meta").fetchone()[0]
    finally:
        con.close()
    assert opt_rows > 0 and spot_rows > 0
    assert built_by == "live"

    # --- Health snapshot carried the P8 perf fields -----------------------------------------------
    assert set(health) >= {"cycle_ms_p50", "cycle_ms_max", "rss_mb",
                           "raw_file_queue_size", "proc_queue_size", "db_queue_size"}
    assert health["rss_mb"] > 0.0  # a running process always has a resident set
    assert health["cycle_ms_max"] < 15.0  # tiny book → far under the thin budget (sanity, not a gate)
    assert health["actual_depth"].get("NIFTY") == 50 and health["actual_depth"].get("SENSEX") == 5

    # --- FD residue: no stray temp / build / lock files in the data dir ----------------------------
    leftovers = [f for f in os.listdir(config.recorder["output_dir"])
                 if f.startswith(".tmp_") or ".building_" in f or f.endswith(".lock")]
    assert leftovers == [], f"unexpected FD residue: {leftovers}"

    # ==============================================================================================
    # Part 2 — the REAL end-of-session reprocess subprocess rebuilds the fat DuckDB store.
    # ==============================================================================================
    repro_log = os.path.join(config.recorder["output_dir"], "reprocess_subproc.log")
    with open(repro_log, "w", encoding="utf-8") as log_fh:
        proc = subprocess.run(
            [sys.executable, "-m", "market_depth_recorder", "--replay", "--catchup",
             "--config", config_path],
            cwd=str(PACKAGE_ROOT.parent), stdout=log_fh, stderr=subprocess.STDOUT, timeout=120,
        )
    assert proc.returncode == 0, open(repro_log, encoding="utf-8").read()

    duck_path = replay.canonical_output(config, raw_path)
    assert os.path.exists(duck_path), "reprocess did not produce the analytics DuckDB store"

    import duckdb
    dcon = duckdb.connect(duck_path, read_only=True)
    try:
        d_built_by = dcon.execute("SELECT built_by FROM recorder_meta").fetchone()[0]
        d_opt = dcon.execute("SELECT COUNT(*) FROM option_strike_metrics").fetchone()[0]
        d_spot = dcon.execute("SELECT COUNT(*) FROM spot_states").fetchone()[0]
    finally:
        dcon.close()
    assert d_built_by == "replay"
    assert d_opt > 0 and d_spot > 0

    # --- Determinism: a second replay of the same lossless raw log must match the reprocess build --
    reverify = os.path.join(config.recorder["output_dir"], "reverify.duckdb")
    replay.replay_file(config, raw_path, reverify)
    ok, report = replay.verify(config, reverify, duck_path)
    assert ok, "replay is non-deterministic:\n" + "\n".join(report)
