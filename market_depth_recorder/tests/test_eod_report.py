"""P10-C — EOD health & sanity-check report.

Exercises the per-tier check functions against synthetic artifacts (clean day, crashed/no-EOF day,
NIFTY-no-depth day, degraded-depth day, empty day) plus the end-to-end `run_eod_report` (writes the
dated markdown+JSON, returns exit 0/1). Offline — no live feed.
"""

from __future__ import annotations

import gzip
import json
import os
import sqlite3
from datetime import date, datetime

import pytest

from market_depth_recorder import eod_report as eod
from market_depth_recorder.config import load_config
from market_depth_recorder.eod_report import FAIL, PASS, SKIP, WARN
from market_depth_recorder.utils import IST

SESSION = date(2026, 7, 6)


@pytest.fixture
def cfg(base_config, write_config):
    # Flat layout so the synthetic artifacts sit directly under output_dir for these tests.
    base_config["recorder"]["date_partitioned"] = False
    return load_config(write_config(base_config))


# ---- builders ---------------------------------------------------------------------------------
def _depth_pkt(sym, levels, *, feed_time=True, orders=3, bid=100.0, ask=100.5, recv=1000.0):
    p = {
        "symbol": sym, "mode": 3, "recv_ts": recv,
        "is_50_depth": levels >= 50, "depth_levels": levels,
        "total_buy_qty": 10, "total_sell_qty": 10,
        "depth": {"buy": [{"price": bid, "quantity": 10, "orders": orders}],
                  "sell": [{"price": ask, "quantity": 10, "orders": orders}]},
    }
    if feed_time:
        p["feed_time"] = 999
    return p


def _write_raw(path, config, packets, *, header=True, instruments=True, eof=True):
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        if header:
            h = {"meta_type": "HEADER", "session_date": SESSION.isoformat(), "schema_version": 1,
                 "config_hash": config.config_hash, "underlyings": ["NIFTY", "SENSEX"], "open_timestamp": 0}
            if instruments:
                h["instruments"] = {"NIFTY": {}}
            fh.write(json.dumps(h) + "\n")
        for p in packets:
            fh.write(json.dumps(p) + "\n")
        if eof:
            fh.write(json.dumps({"meta_type": "EOF", "record_count": len(packets),
                                 "close_timestamp": 0}) + "\n")


def _make_live_db(path, *, nifty=True, sensex=True):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE spot_states (timestamp INT)")
    con.execute("CREATE TABLE option_strike_metrics (timestamp INT, symbol TEXT)")
    con.execute("CREATE TABLE strike_window_metrics (timestamp INT)")
    con.execute("CREATE TABLE aggregated_window_metrics (timestamp INT)")
    con.execute("INSERT INTO spot_states VALUES (1)")
    if nifty:
        con.execute("INSERT INTO option_strike_metrics VALUES (1, 'NIFTY07JUL2624000CE')")
    if sensex:
        con.execute("INSERT INTO option_strike_metrics VALUES (1, 'SENSEX09JUL2675700CE')")
    con.commit()
    con.close()


def _write_health(path, **over):
    h = {"timestamp": int(datetime.now(IST).timestamp()), "state": "record",
         "raw_dropped_total": 0, "db_rows_dropped_total": 0,
         "cycle_ms_p50": 10.0, "cycle_ms_max": 12.0, "rss_mb": 60.0, "degraded_level": 0}
    h.update(over)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(h, fh)


def _status(checks, name):
    return next(c.status for c in checks if c.name == name)


# ---- helpers ----------------------------------------------------------------------------------
def test_classify_spot_and_option(cfg):
    unders = [(u.name, u.spot_symbol) for u in cfg.underlyings]
    assert eod._classify("NIFTY", unders) == ("NIFTY", "spot")
    assert eod._classify("NIFTY07JUL2624000CE:50", unders) == ("NIFTY", "option")
    assert eod._classify("SENSEX09JUL2675700PE", unders) == ("SENSEX", "option")
    # NIFTYNXT50 is not configured and the digit-guard stops it matching NIFTY.
    assert eod._classify("NIFTYNXT5028JUL26FUT", unders) == (None, None)


# ---- check_raw --------------------------------------------------------------------------------
def test_raw_clean_day(cfg, tmp_path):
    raw = str(tmp_path / "raw.jsonl.gz")
    _write_raw(raw, cfg, [_depth_pkt("NIFTY07JUL2624000CE:50", 50),
                          _depth_pkt("SENSEX09JUL2675700CE:50", 50)])
    checks = eod.check_raw(cfg, raw)
    assert _status(checks, "raw.header") == PASS
    assert _status(checks, "raw.eof") == PASS
    assert _status(checks, "raw.depth_coverage.NIFTY") == PASS
    assert _status(checks, "raw.depth_coverage.SENSEX") == PASS
    assert _status(checks, "raw.depth_level.NIFTY") == PASS
    assert _status(checks, "raw.audit_fields") == PASS  # TBT packets carry feed_time


def test_raw_no_eof_warns(cfg, tmp_path):
    raw = str(tmp_path / "raw.jsonl.gz")
    _write_raw(raw, cfg, [_depth_pkt("NIFTY07JUL2624000CE:50", 50),
                          _depth_pkt("SENSEX09JUL2675700CE:50", 50)], eof=False)
    assert _status(eod.check_raw(cfg, raw), "raw.eof") == WARN


def test_raw_nifty_no_depth_fails(cfg, tmp_path):
    raw = str(tmp_path / "raw.jsonl.gz")
    # Only SENSEX depth (the P9 scenario) → NIFTY depth coverage FAILs.
    _write_raw(raw, cfg, [_depth_pkt("SENSEX09JUL2675700CE:50", 5)])
    checks = eod.check_raw(cfg, raw)
    assert _status(checks, "raw.depth_coverage.NIFTY") == FAIL
    assert _status(checks, "raw.depth_level.SENSEX") == WARN     # 5 < requested 50
    assert _status(checks, "raw.audit_fields") == PASS           # no TBT packets → N/A


def test_raw_missing_file_fails(cfg, tmp_path):
    checks = eod.check_raw(cfg, str(tmp_path / "nope.jsonl.gz"))
    assert checks[0].name == "raw.present" and checks[0].status == FAIL


def test_raw_config_hash_mismatch_warns(cfg, tmp_path):
    raw = str(tmp_path / "raw.jsonl.gz")
    with gzip.open(raw, "wt", encoding="utf-8") as fh:
        fh.write(json.dumps({"meta_type": "HEADER", "session_date": SESSION.isoformat(),
                             "config_hash": "sha256:deadbeef", "instruments": {"X": {}}}) + "\n")
        fh.write(json.dumps(_depth_pkt("NIFTY07JUL2624000CE:50", 50)) + "\n")
    assert _status(eod.check_raw(cfg, raw), "raw.config_hash") == WARN


# ---- check_live_db ----------------------------------------------------------------------------
def test_live_db_clean(cfg, tmp_path):
    db = str(tmp_path / "live.db")
    _make_live_db(db, nifty=True, sensex=True)
    checks = eod.check_live_db(cfg, db)
    assert _status(checks, "live.tables") == PASS
    assert _status(checks, "live.option_rows.NIFTY") == PASS
    assert _status(checks, "live.option_rows.SENSEX") == PASS


def test_live_db_nifty_missing_fails(cfg, tmp_path):
    db = str(tmp_path / "live.db")
    _make_live_db(db, nifty=False, sensex=True)
    assert _status(eod.check_live_db(cfg, db), "live.option_rows.NIFTY") == FAIL


def test_live_db_absent_warns(cfg, tmp_path):
    checks = eod.check_live_db(cfg, str(tmp_path / "nope.db"))
    assert checks[0].name == "live.present" and checks[0].status == WARN


# ---- check_duckdb -----------------------------------------------------------------------------
def test_duckdb_absent_skips(cfg, tmp_path):
    checks = eod.check_duckdb(cfg, str(tmp_path / "nope.duckdb"))
    assert checks[0].status == SKIP


def test_duckdb_populated_meta(cfg, tmp_path):
    duck = str(tmp_path / "a.duckdb")
    import duckdb
    con = duckdb.connect(duck)
    for t in eod._LIVE_TABLES:
        con.execute(f"CREATE TABLE {t} (ts INTEGER)")
        con.execute(f"INSERT INTO {t} VALUES (1)")
    con.execute("CREATE TABLE recorder_meta (schema_version INTEGER, config_hash VARCHAR, built_by VARCHAR)")
    con.execute("INSERT INTO recorder_meta VALUES (1, ?, 'replay')", [cfg.config_hash])
    con.close()
    checks = eod.check_duckdb(cfg, duck)
    assert _status(checks, "duckdb.tables") == PASS
    assert _status(checks, "duckdb.meta") == PASS


# ---- check_ops --------------------------------------------------------------------------------
def test_ops_clean(cfg, tmp_path):
    hp = str(tmp_path / "health.json")
    _write_health(hp)
    checks = eod.check_ops(hp)
    assert _status(checks, "ops.drops") == PASS
    assert _status(checks, "ops.cycle_ms") == PASS
    assert _status(checks, "ops.rss_mb") == PASS


def test_ops_drops_fail_and_perf_warn(cfg, tmp_path):
    hp = str(tmp_path / "health.json")
    # cycle_ms_max must exceed the re-tuned _CYCLE_MS_TARGET (30 ms, post-P10-E) to trip the WARN.
    _write_health(hp, raw_dropped_total=3, cycle_ms_max=35.0, rss_mb=700.0, degraded_level=2)
    checks = eod.check_ops(hp)
    assert _status(checks, "ops.drops") == FAIL
    assert _status(checks, "ops.cycle_ms") == WARN
    assert _status(checks, "ops.rss_mb") == WARN
    assert _status(checks, "ops.degraded") == WARN


# ---- run_eod_report end-to-end ----------------------------------------------------------------
def test_run_eod_report_clean_passes(cfg, tmp_path):
    d = tmp_path / "data"  # matches the base_config output_dir
    _write_raw(str(d / "market_depth_raw_20260706.jsonl.gz"), cfg,
               [_depth_pkt("NIFTY07JUL2624000CE:50", 50), _depth_pkt("SENSEX09JUL2675700CE:50", 50)])
    _make_live_db(str(d / "market_depth_live_20260706.db"))
    _write_health(str(d / "health.json"))
    code, report = eod.run_eod_report(cfg, SESSION)
    assert code == 0
    assert report["overall"] in (PASS, WARN)  # duckdb SKIP doesn't fail
    assert os.path.exists(report["report_md"]) and os.path.exists(report["report_json"])


def test_run_eod_report_fails_on_nifty_gap(cfg, tmp_path):
    d = tmp_path / "data"
    _write_raw(str(d / "market_depth_raw_20260706.jsonl.gz"), cfg,
               [_depth_pkt("SENSEX09JUL2675700CE:50", 5)])   # NIFTY absent
    _make_live_db(str(d / "market_depth_live_20260706.db"), nifty=False)
    _write_health(str(d / "health.json"))
    code, report = eod.run_eod_report(cfg, SESSION)
    assert code == 1 and report["overall"] == FAIL
