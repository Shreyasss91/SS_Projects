"""Offline replay + DuckDB rebuild tests (spec §8). All run offline — a hand-built raw ``.jsonl.gz``
fixture with an enriched HEADER, the same ``TickProcessor``, and a local DuckDB/SQLite. No live feed.

Covers: `from_header` reconstruction (no REST); replay determinism (`--verify` clean on a re-replay);
a perturbed metric → drift reported; `--catchup` self-heal; corrupt-trailing-line / missing-EOF /
multi-HEADER tolerance; `--verify-against-live` (live-subset columns match a real SQLite live store);
rolling-window warm-up (early seconds NULL); the `--underlying` filter; and the CLI exit codes.
"""

from __future__ import annotations

import gzip
import json
import os
import queue
import threading
from datetime import date, datetime

import duckdb
import pytest

from market_depth_recorder.__main__ import main
from market_depth_recorder.config import load_config
from market_depth_recorder.database_writer import DuckDBAnalyticalWriter, SQLiteLiveWriter
from market_depth_recorder.instrument_manager import InstrumentManager
from market_depth_recorder.processor import TickProcessor
from market_depth_recorder import replay as R
from market_depth_recorder.utils import IST

SESSION_DATE = date(2026, 7, 6)
T0 = 1_781_060_400  # a fixed integer epoch; packets land at T0 + sec + 0.5 so each 1s boundary is clean
STRIKES = [23400, 23500, 23600]
STEP = 100
EXPIRY = "09-JUL-26"


# --------------------------------------------------------------------------------------------------
# Fixture builders
# --------------------------------------------------------------------------------------------------
def _instruments_block() -> dict:
    return {
        "NIFTY": {
            "option_exchange": "NFO", "expiry": EXPIRY, "strike_step": STEP,
            "contracts": [[k, f"N{k}CE", f"N{k}PE", 0.05] for k in STRIKES],
        }
    }


def _header() -> dict:
    return {
        "meta_type": "HEADER", "session_date": SESSION_DATE.isoformat(), "schema_version": 1,
        "config_hash": "sha256:test", "underlyings": ["NIFTY"], "open_timestamp": T0,
        "instruments": _instruments_block(),
    }


def _depth(bid: float, ask: float, qty: int) -> dict:
    return {
        "buy": [{"price": bid - i, "quantity": qty + 10 * i, "orders": 3} for i in range(5)],
        "sell": [{"price": ask + i, "quantity": qty + 10 * i, "orders": 3} for i in range(5)],
    }


def _spot_pkt(recv: float, ltp: float) -> dict:
    return {"symbol": "NIFTY", "exchange": "NSE_INDEX", "mode": 1, "ltp": ltp,
            "timestamp": int(recv), "recv_ts": recv}


def _depth_pkt(recv: float, strike: int, ot: str, qty: int) -> dict:
    return {
        "symbol": f"N{strike}{ot}:50", "exchange": "NFO", "mode": 3, "ltp": 1.5,
        "timestamp": int(recv), "feed_time": int(recv), "depth_levels": 50, "is_50_depth": True,
        "total_buy_qty": qty * 5, "total_sell_qty": qty * 5,
        "depth": _depth(1.4, 1.6, qty), "recv_ts": recv,
    }


def _packets(nsec: int = 35, *, perturb_sec: int | None = None) -> list[dict]:
    """One spot + six option (3 strikes × CE/PE) packets per second, all at ``T0+sec+0.5``."""
    out: list[dict] = []
    for sec in range(nsec):
        recv = T0 + sec + 0.5
        out.append(_spot_pkt(recv, 23500.0))
        qty = 100 if perturb_sec is None or sec != perturb_sec else 777  # perturbation → metric drift
        for k in STRIKES:
            for ot in ("CE", "PE"):
                out.append(_depth_pkt(recv, k, ot, qty))
    return out


def _write_raw(path: str, packets: list[dict], *, header: dict | None = None,
               eof: bool = True, extra_headers: int = 0, corrupt_tail: bool = False) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        fh.write(json.dumps(header or _header()) + "\n")
        for _ in range(extra_headers):  # simulate a same-day restart appending a second HEADER
            fh.write(json.dumps(_header()) + "\n")
        for p in packets:
            fh.write(json.dumps(p) + "\n")
        if corrupt_tail:
            fh.write('{"symbol": "N23500CE", "recv_ts": 12, tru')  # truncated JSON, no newline
        if eof:
            fh.write(json.dumps({"meta_type": "EOF", "record_count": len(packets),
                                 "close_timestamp": T0 + 999}) + "\n")


@pytest.fixture
def cfg(base_config, write_config):
    # single-underlying config keeps the fixture small; SENSEX is simply absent from the log.
    base_config["underlyings"] = [base_config["underlyings"][0]]
    return load_config(write_config(base_config))


def _raw(tmp_path, **kw) -> str:
    path = str(tmp_path / R._RAW_FILENAME_FMT.replace("%Y%m%d", SESSION_DATE.strftime("%Y%m%d")))
    _write_raw(path, kw.pop("packets", None) or _packets(), **kw)
    return path


# --------------------------------------------------------------------------------------------------
# from_header reconstruction (no REST)
# --------------------------------------------------------------------------------------------------
def test_from_header_rebuilds_maps(cfg):
    im = InstrumentManager.from_header(cfg, _instruments_block())
    assert im.resolved
    assert im.active_strikes_list["NIFTY"] == STRIKES
    assert im.strike_to_symbol_map["NIFTY"][23500] == {"CE": "N23500CE", "PE": "N23500PE"}
    assert im.symbol_to_strike_map["N23500CE"] == {"underlying": "NIFTY", "strike": 23500, "option_type": "CE"}
    assert im.tick_size_map["N23500CE"] == 0.05
    assert im.chains["NIFTY"].strike_step == STEP and im.chains["NIFTY"].expiry == EXPIRY


def test_from_header_missing_block_raises(cfg):
    from market_depth_recorder.instrument_manager import RestError

    with pytest.raises(RestError, match="instruments"):
        InstrumentManager.from_header(cfg, None)


def test_to_header_round_trips(cfg):
    im = InstrumentManager.from_header(cfg, _instruments_block())
    assert im.to_header_dict()["NIFTY"]["contracts"] == _instruments_block()["NIFTY"]["contracts"]


# --------------------------------------------------------------------------------------------------
# Replay → DuckDB + determinism / drift (§8.4)
# --------------------------------------------------------------------------------------------------
def test_replay_builds_four_tables_and_provenance(cfg, tmp_path):
    raw = _raw(tmp_path)
    out = str(tmp_path / "a.duckdb")
    stats = R.replay_file(cfg, raw, out)
    assert stats.packets > 0 and stats.rows > 0
    con = duckdb.connect(out, read_only=True)
    try:
        assert con.execute("SELECT count(*) FROM spot_states").fetchone()[0] > 0
        assert con.execute("SELECT count(*) FROM option_strike_metrics").fetchone()[0] > 0
        assert con.execute("SELECT count(*) FROM aggregated_window_metrics").fetchone()[0] > 0
        assert con.execute("SELECT built_by, source_raw FROM recorder_meta").fetchone()[0] == "replay"
    finally:
        con.close()


def test_replay_is_deterministic_verify_clean(cfg, tmp_path):
    raw = _raw(tmp_path)
    a = str(tmp_path / "a.duckdb")
    b = str(tmp_path / "b.duckdb")
    R.replay_file(cfg, raw, a)
    R.replay_file(cfg, raw, b)
    ok, report = R.verify(cfg, b, a)
    assert ok, "\n".join(report)


def test_replay_arrow_backend_matches_executemany(cfg, base_config, write_config, tmp_path):
    """The Arrow columnar write backend must produce bit-identical tables to the legacy executemany
    path (verify-clean) — the correctness gate for the ~30× replay speedup (write-path pivot)."""
    pytest.importorskip("pyarrow")
    raw = _raw(tmp_path)
    a = str(tmp_path / "exec.duckdb")
    R.replay_file(cfg, raw, a)  # cfg fixture defaults to write_backend='executemany'
    base_config["analytics_db"]["write_backend"] = "arrow"
    cfg_arrow = load_config(write_config(base_config))
    b = str(tmp_path / "arrow.duckdb")
    R.replay_file(cfg_arrow, raw, b)
    ok, report = R.verify(cfg, b, a)  # arrow build diffed against the executemany build
    assert ok, "\n".join(report)


def test_replay_chunked_arrow_matches_unchunked(cfg, base_config, write_config, tmp_path):
    """A tiny write_batch_rows (streaming flushes mid-replay) must produce a build identical to a large
    single-batch build — chunking bounds peak RSS without changing output (§P-C), verify-clean."""
    pytest.importorskip("pyarrow")
    raw = _raw(tmp_path)
    base_config["analytics_db"]["write_backend"] = "arrow"
    base_config["analytics_db"]["write_batch_rows"] = 100000
    big = str(tmp_path / "big.duckdb")
    R.replay_file(load_config(write_config(base_config)), raw, big)
    base_config["analytics_db"]["write_batch_rows"] = 3   # force many small flushes
    small = str(tmp_path / "small.duckdb")
    R.replay_file(load_config(write_config(base_config)), raw, small)
    ok, report = R.verify(cfg, small, big)
    assert ok, "\n".join(report)


def test_replay_file_write_backend_param_overrides_config(cfg, tmp_path):
    """The ``write_backend`` param on replay_file overrides the config default for one run (the seam the
    ``--backend`` CLI flag uses): cfg defaults to executemany, the override forces arrow, output is
    value-identical (verify-clean). Lets a canonical rebuild pick arrow without editing the config default."""
    pytest.importorskip("pyarrow")
    raw = _raw(tmp_path)
    a = str(tmp_path / "default_exec.duckdb")
    b = str(tmp_path / "override_arrow.duckdb")
    R.replay_file(cfg, raw, a)                                # config default: executemany
    R.replay_file(cfg, raw, b, write_backend="arrow")        # same cfg, param override -> arrow
    ok, report = R.verify(cfg, b, a)
    assert ok, "\n".join(report)


def test_perturbed_replay_reports_drift(cfg, tmp_path):
    clean_raw = _raw(tmp_path, packets=_packets())
    a = str(tmp_path / "a.duckdb")
    R.replay_file(cfg, clean_raw, a)
    perturbed_raw = str(tmp_path / "perturbed.jsonl.gz")
    _write_raw(perturbed_raw, _packets(perturb_sec=20))
    b = str(tmp_path / "b.duckdb")
    R.replay_file(cfg, perturbed_raw, b)
    ok, report = R.verify(cfg, b, a)
    assert not ok
    assert any("option_strike_metrics" in line for line in report)


# --------------------------------------------------------------------------------------------------
# Robust reader (§8.5)
# --------------------------------------------------------------------------------------------------
def test_corrupt_trailing_line_skipped(cfg, tmp_path):
    raw = _raw(tmp_path, corrupt_tail=True, eof=False)  # truncated last line, no EOF
    out = str(tmp_path / "a.duckdb")
    stats = R.replay_file(cfg, raw, out)
    assert stats.corrupt_lines == 1
    assert stats.rows > 0  # everything before the bad line still built


def test_multi_header_tolerated(cfg, tmp_path):
    raw = _raw(tmp_path, extra_headers=1)  # a same-day restart appended a second HEADER
    out = str(tmp_path / "a.duckdb")
    stats = R.replay_file(cfg, raw, out)
    assert stats.rows > 0


# --------------------------------------------------------------------------------------------------
# Rolling-window warm-up (§6.2)
# --------------------------------------------------------------------------------------------------
def test_warmup_first_second_rolling_null(cfg, tmp_path):
    raw = _raw(tmp_path)
    out = str(tmp_path / "a.duckdb")
    R.replay_file(cfg, raw, out)
    con = duckdb.connect(out, read_only=True)
    try:
        first_ts = con.execute("SELECT min(timestamp) FROM strike_window_metrics").fetchone()[0]
        # price_return needs ≥2 samples in the window → NULL at the first emitted second.
        vals = con.execute("SELECT price_return FROM strike_window_metrics WHERE timestamp = ?",
                           [first_ts]).fetchall()
        assert all(v[0] is None for v in vals)
    finally:
        con.close()


# --------------------------------------------------------------------------------------------------
# --catchup self-heal (§8.6 mode 2)
# --------------------------------------------------------------------------------------------------
def test_catchup_rebuilds_missing_and_skips_current(cfg, tmp_path, monkeypatch):
    out_dir = cfg.recorder["output_dir"]
    raw = _raw(tmp_path)  # writes into out_dir (tmp_path/data via base_config? no — tmp_path)
    # move the raw into the configured output_dir so catchup's glob finds it
    dst = os.path.join(out_dir, os.path.basename(raw))
    os.replace(raw, dst)
    built = R.catchup(cfg)
    assert built == 1
    duck = DuckDBAnalyticalWriter.resolve_filename(out_dir, SESSION_DATE)
    assert os.path.exists(duck)
    # second run: the store is now up-to-date → nothing rebuilt.
    assert R.catchup(cfg) == 0


# --------------------------------------------------------------------------------------------------
# --verify-against-live (§8.4) — live-subset columns match a real SQLite live store
# --------------------------------------------------------------------------------------------------
def _drive(proc: TickProcessor, packets: list[dict], interval: float = 1.0) -> None:
    import math

    next_b = None
    for pkt in packets:
        recv = pkt["recv_ts"]
        proc.ingest(pkt)
        if next_b is None:
            next_b = (math.floor(recv / interval) + 1) * interval
        while recv >= next_b:
            proc.emit_second(int(next_b))
            next_b += interval


def _build_live_store(cfg, packets) -> str:
    db_q: queue.Queue = queue.Queue()
    shutdown = threading.Event()
    writer = SQLiteLiveWriter(cfg, db_q, shutdown, SESSION_DATE,
                              time_fn=lambda: datetime(2026, 7, 6, 12, tzinfo=IST).timestamp())
    writer.start()
    im = InstrumentManager.from_header(cfg, _instruments_block())
    vclock = {"t": 0.0}
    proc = TickProcessor(cfg, im, queue.Queue(), db_q, threading.Event(),
                         time_fn=lambda: vclock["t"], active_metrics=cfg.recorder["live_metrics"])
    # reuse the same per-second driver, but this processor pushes to the live writer's queue
    orig_ingest = proc.ingest
    def ingest(p):
        vclock["t"] = p["recv_ts"]
        orig_ingest(p)
    proc.ingest = ingest
    _drive(proc, packets)
    shutdown.set()
    writer.join(timeout=5)
    return SQLiteLiveWriter.resolve_filename(cfg.recorder["output_dir"], SESSION_DATE)


def test_verify_against_live_subset_matches(cfg, tmp_path):
    packets = _packets()
    raw = _raw(tmp_path, packets=packets)
    duck = str(tmp_path / "a.duckdb")
    R.replay_file(cfg, raw, duck)
    live = _build_live_store(cfg, packets)
    ok, report = R.verify(cfg, duck, live, live_subset=True)
    assert ok, "\n".join(report)
    assert any("no drift" in line for line in report)


def _perturb_one_live_ltp(live_path: str) -> None:
    """Diverge exactly one live_metrics cell from the replay (simulates a second-boundary difference)."""
    import sqlite3
    con = sqlite3.connect(live_path)
    key = con.execute("select timestamp, symbol from option_strike_metrics "
                      "where ltp is not null limit 1").fetchone()
    con.execute("update option_strike_metrics set ltp = ltp + 999 where timestamp=? and symbol=?", key)
    con.commit()
    con.close()


def test_verify_against_live_within_tolerance_passes(cfg, tmp_path, monkeypatch):
    # A small live/replay divergence (boundary timing) is tolerated for the disposable live store.
    packets = _packets()
    raw = _raw(tmp_path, packets=packets)
    duck = str(tmp_path / "a.duckdb")
    R.replay_file(cfg, raw, duck)
    live = _build_live_store(cfg, packets)
    _perturb_one_live_ltp(live)
    monkeypatch.setattr(R, "_LIVE_SUBSET_TOLERANCE_PCT", 100.0)  # generous → within bounds
    ok, report = R.verify(cfg, duck, live, live_subset=True)
    assert ok, "\n".join(report)
    assert any("within the" in line and "tolerance" in line for line in report)


def test_verify_against_live_beyond_tolerance_fails(cfg, tmp_path, monkeypatch):
    # With zero tolerance the same single divergence fails — the strict determinism gate is unchanged.
    packets = _packets()
    raw = _raw(tmp_path, packets=packets)
    duck = str(tmp_path / "a.duckdb")
    R.replay_file(cfg, raw, duck)
    live = _build_live_store(cfg, packets)
    _perturb_one_live_ltp(live)
    monkeypatch.setattr(R, "_LIVE_SUBSET_TOLERANCE_PCT", 0.0)
    ok, report = R.verify(cfg, duck, live, live_subset=True)
    assert not ok
    assert any("exceeds" in line for line in report)


# --------------------------------------------------------------------------------------------------
# --underlying filter (§8.2)
# --------------------------------------------------------------------------------------------------
def test_underlying_filter_replays_subset(cfg, tmp_path):
    raw = _raw(tmp_path)
    out = str(tmp_path / "a.duckdb")
    R.replay_file(cfg, raw, out, underlying="NIFTY")  # the only underlying → same as full
    con = duckdb.connect(out, read_only=True)
    try:
        assert con.execute("SELECT count(*) FROM option_strike_metrics").fetchone()[0] > 0
    finally:
        con.close()
    # a non-matching filter → no option rows recorded (all packets skipped)
    out2 = str(tmp_path / "b.duckdb")
    R.replay_file(cfg, raw, out2, underlying="DOESNOTEXIST")
    con = duckdb.connect(out2, read_only=True)
    try:
        assert con.execute("SELECT count(*) FROM option_strike_metrics").fetchone()[0] == 0
    finally:
        con.close()


# --------------------------------------------------------------------------------------------------
# CLI exit codes (§8.2)
# --------------------------------------------------------------------------------------------------
def test_cli_replay_builds(cfg, tmp_path, write_config, base_config):
    base_config["underlyings"] = [base_config["underlyings"][0]]
    cfg_path = write_config(base_config)
    raw = _raw(tmp_path)
    out = str(tmp_path / "cli.duckdb")
    assert main(["--config", cfg_path, "--replay", raw, "--output", out]) == 0
    assert os.path.exists(out)


def test_cli_replay_missing_file(cfg, tmp_path, write_config, base_config):
    base_config["underlyings"] = [base_config["underlyings"][0]]
    cfg_path = write_config(base_config)
    assert main(["--config", cfg_path, "--replay", str(tmp_path / "nope.jsonl.gz")]) == 1


def test_cli_replay_verify_clean(cfg, tmp_path, write_config, base_config):
    base_config["underlyings"] = [base_config["underlyings"][0]]
    cfg_path = write_config(base_config)
    raw = _raw(tmp_path)
    canonical = R.canonical_output(cfg, raw)
    R.replay_file(cfg, raw, canonical)  # prior build to diff against
    assert main(["--config", cfg_path, "--replay", raw, "--verify"]) == 0
