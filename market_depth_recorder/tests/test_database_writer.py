"""SQLiteLiveWriter (Tier-1 thin live store) tests — spec §3.6/§4/§6.3. All offline: a real temp DB
via ``tmp_path``, an injected clock, and an in-memory ``db_queue`` — no feed/socket/broker.

Covers: DDL (4 tables + indexes) + ``recorder_meta`` provenance; round-trip of all four envelope
tables with ``None`` → NULL; batch flush by size and by time; PK-collision ``INSERT OR IGNORE`` count;
``mark_restart_boundary`` → ``INSERT OR REPLACE``; PASSIVE checkpoint cadence; teardown TRUNCATE +
optimize; corruption archive + rebuild (§6.3); graceful drain via the real thread; unknown-table skip;
and the deferred DuckDB stub.
"""

from __future__ import annotations

import os
import queue
import sqlite3
import threading
from datetime import date, datetime

import pytest

from market_depth_recorder import SCHEMA_VERSION
from market_depth_recorder.config import load_config
from market_depth_recorder.database_writer import (
    DuckDBAnalyticalWriter,
    SQLiteLiveWriter,
)
from market_depth_recorder.processor import (
    AGG_COLUMNS,
    OPTION_COLUMNS,
    SPOT_COLUMNS,
    STRIKE_WINDOW_COLUMNS,
)
from market_depth_recorder.utils import IST

SESSION_DATE = date(2026, 7, 3)
# The defensive rollover guard compares the injected clock's IST date to session_date, so the test
# clock is anchored to noon-IST on SESSION_DATE (matches now_ist().date()) — keeps every test
# deterministic on any host timezone and never spuriously rolls over.
SESSION_EPOCH = datetime(2026, 7, 3, 12, 0, 0, tzinfo=IST).timestamp()
T0 = 1_781_060_400  # a fixed epoch second used only for row `timestamp` columns (clock-independent)


# --------------------------------------------------------------------------------------------------
# Fixtures / helpers
# --------------------------------------------------------------------------------------------------
@pytest.fixture
def cfg(base_config, write_config):
    """A loaded, validated Config whose output_dir points at the per-test tmp data dir."""
    return load_config(write_config(base_config))


class Clock:
    """Deterministic injected clock (epoch seconds) — drives commit/checkpoint cadence + rollover."""

    def __init__(self, t: float = SESSION_EPOCH):
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, d: float) -> None:
        self.t += d


class ConnSpy:
    """Transparent proxy over a sqlite3.Connection that records every SQL string passed to execute()."""

    def __init__(self, real: sqlite3.Connection):
        self._real = real
        self.calls: list[str] = []

    def execute(self, sql, *args):
        self.calls.append(sql)
        return self._real.execute(sql, *args)

    def __getattr__(self, name):
        return getattr(self._real, name)


def row(columns: tuple[str, ...], **vals) -> tuple:
    """Build a full-width row tuple in ``columns`` order; unspecified columns default to None."""
    return tuple(vals.get(c) for c in columns)


def make_writer(cfg, *, clock=None, q=None, shutdown=None) -> SQLiteLiveWriter:
    return SQLiteLiveWriter(
        cfg,
        q if q is not None else queue.Queue(),
        shutdown if shutdown is not None else threading.Event(),
        SESSION_DATE,
        time_fn=clock or Clock(),
    )


def read_rows(path: str, table: str) -> list[tuple]:
    conn = sqlite3.connect(path)
    try:
        return conn.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
    finally:
        conn.close()


def query(path: str, sql: str) -> list[tuple]:
    conn = sqlite3.connect(path)
    try:
        return conn.execute(sql).fetchall()
    finally:
        conn.close()


# --------------------------------------------------------------------------------------------------
# DDL + provenance
# --------------------------------------------------------------------------------------------------
def test_ddl_creates_all_tables_indexes_and_recorder_meta(cfg):
    w = make_writer(cfg)
    w._open_db()
    path = w._path
    w._close_db()

    names = {r[0] for r in query(path, "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"spot_states", "option_strike_metrics", "strike_window_metrics",
            "aggregated_window_metrics", "recorder_meta"} <= names

    indexes = {r[0] for r in query(path, "SELECT name FROM sqlite_master WHERE type='index'")}
    assert {"idx_osm_strike", "idx_osm_ts", "idx_swm_symbol", "idx_spot_ts"} <= indexes


def test_recorder_meta_stamp_is_correct(cfg):
    w = make_writer(cfg)
    w._open_db()
    path = w._path
    w._close_db()

    rows = query(path, "SELECT schema_version, config_hash, built_by, build_time, source_raw "
                       "FROM recorder_meta")
    assert len(rows) == 1
    schema_version, config_hash, built_by, build_time, source_raw = rows[0]
    assert schema_version == SCHEMA_VERSION
    assert config_hash == cfg.config_hash
    assert built_by == "live"
    assert build_time == int(SESSION_EPOCH)
    assert source_raw is None


def test_reopen_same_day_does_not_duplicate_provenance(cfg):
    """A same-day reopen (file already exists) must not re-stamp recorder_meta (decision 52)."""
    w = make_writer(cfg)
    w._open_db()
    w._close_db()
    w2 = make_writer(cfg)
    w2._open_db()
    path = w2._path
    w2._close_db()
    assert query(path, "SELECT COUNT(*) FROM recorder_meta")[0][0] == 1


# --------------------------------------------------------------------------------------------------
# Round-trip of all four tables (None → NULL)
# --------------------------------------------------------------------------------------------------
def test_round_trip_all_four_tables_with_nulls(cfg):
    q = queue.Queue()
    w = make_writer(cfg, q=q)
    w._open_db()

    spot = row(SPOT_COLUMNS, timestamp=T0, symbol="NIFTY", spot_price=23412.5, atm_strike=23400)
    opt = row(OPTION_COLUMNS, timestamp=T0, symbol="NIFTY26JUN23400CE",
              strike_price=23400.0, option_type="CE", ltp=120.5, spread=1.5, depth_levels=50,
              is_50_depth=1)  # every other metric stays None → NULL
    win = row(STRIKE_WINDOW_COLUMNS, timestamp=T0, symbol="NIFTY26JUN23400CE", time_window=5,
              price_return=0.01)
    agg = row(AGG_COLUMNS, timestamp=T0, underlying="NIFTY", strike_window="SMALL", regime="Balanced")

    for table, rows in [("spot_states", [spot]), ("option_strike_metrics", [opt]),
                        ("strike_window_metrics", [win]), ("aggregated_window_metrics", [agg])]:
        w._buffer({"table": table, "rows": rows})
    w._final_flush()
    path = w._path
    w._close_db()

    assert read_rows(path, "spot_states") == [spot]
    got_opt = read_rows(path, "option_strike_metrics")[0]
    assert got_opt == opt  # includes the trailing None metrics stored as NULL
    assert got_opt[OPTION_COLUMNS.index("micro_price")] is None
    assert read_rows(path, "strike_window_metrics") == [win]
    assert read_rows(path, "aggregated_window_metrics") == [agg]


# --------------------------------------------------------------------------------------------------
# Batch flush triggers
# --------------------------------------------------------------------------------------------------
def test_flush_by_size(base_config, write_config):
    base_config["database"]["batch_size"] = 2
    base_config["database"]["batch_write_interval_ms"] = 5000
    cfg = load_config(write_config(base_config))
    clock = Clock()
    w = make_writer(cfg, clock=clock)
    w._open_db()
    path = w._path

    w._buffer({"table": "spot_states",
               "rows": [row(SPOT_COLUMNS, timestamp=T0, symbol="A", spot_price=1.0, atm_strike=1)]})
    w._maybe_flush()
    assert query(path, "SELECT COUNT(*) FROM spot_states")[0][0] == 0  # below batch_size, no time

    w._buffer({"table": "spot_states",
               "rows": [row(SPOT_COLUMNS, timestamp=T0 + 1, symbol="A", spot_price=2.0, atm_strike=1)]})
    w._maybe_flush()  # now 2 buffered ≥ batch_size → commit
    assert query(path, "SELECT COUNT(*) FROM spot_states")[0][0] == 2
    w._close_db()


def test_flush_by_time(base_config, write_config):
    base_config["database"]["batch_size"] = 500
    base_config["database"]["batch_write_interval_ms"] = 1000
    cfg = load_config(write_config(base_config))
    clock = Clock()
    w = make_writer(cfg, clock=clock)
    w._open_db()
    path = w._path

    w._buffer({"table": "spot_states",
               "rows": [row(SPOT_COLUMNS, timestamp=T0, symbol="A", spot_price=1.0, atm_strike=1)]})
    w._maybe_flush()
    assert query(path, "SELECT COUNT(*) FROM spot_states")[0][0] == 0  # < batch_size, < interval

    clock.advance(1.0)  # 1000 ms elapsed since last commit
    w._maybe_flush()
    assert query(path, "SELECT COUNT(*) FROM spot_states")[0][0] == 1
    w._close_db()


# --------------------------------------------------------------------------------------------------
# Collision semantics: IGNORE (steady state) vs REPLACE (restart boundary)
# --------------------------------------------------------------------------------------------------
def test_pk_collision_ignored_and_counted(cfg):
    w = make_writer(cfg)
    w._open_db()
    path = w._path

    w._buffer({"table": "spot_states",
               "rows": [row(SPOT_COLUMNS, timestamp=T0, symbol="A", spot_price=1.0, atm_strike=100)]})
    w._commit()
    w._buffer({"table": "spot_states",  # same PK, different price
               "rows": [row(SPOT_COLUMNS, timestamp=T0, symbol="A", spot_price=9.0, atm_strike=999)]})
    w._commit()

    assert query(path, "SELECT spot_price FROM spot_states")[0][0] == 1.0  # original kept (IGNORE)
    assert w.rows_ignored_total == 1
    w._close_db()


def test_mark_restart_boundary_uses_replace(cfg):
    w = make_writer(cfg)
    w._open_db()
    path = w._path

    w._buffer({"table": "spot_states",
               "rows": [row(SPOT_COLUMNS, timestamp=T0, symbol="A", spot_price=1.0, atm_strike=100)]})
    w._commit()

    w.mark_restart_boundary(T0)  # the P6 orchestrator flags the overlap second
    w._buffer({"table": "spot_states",  # same PK — freshest recompute must win
               "rows": [row(SPOT_COLUMNS, timestamp=T0, symbol="A", spot_price=9.0, atm_strike=999)]})
    w._commit()

    assert query(path, "SELECT spot_price, atm_strike FROM spot_states")[0] == (9.0, 999)
    assert w.rows_ignored_total == 0
    assert w._boundary_ts is None  # reverted after flushing at/past the boundary second
    w._close_db()


# --------------------------------------------------------------------------------------------------
# Checkpoint cadence + teardown PRAGMAs
# --------------------------------------------------------------------------------------------------
def test_passive_checkpoint_cadence(cfg):
    clock = Clock()
    w = make_writer(cfg, clock=clock)
    w._open_db()
    w.wal_checkpoint_interval_sec = 30  # config-min; drive the clock past it
    spy = ConnSpy(w._conn)
    w._conn = spy

    w._maybe_checkpoint()  # no time elapsed → no PASSIVE checkpoint
    assert not any("wal_checkpoint(PASSIVE)" in c for c in spy.calls)

    clock.advance(31)
    w._maybe_checkpoint()
    assert any("wal_checkpoint(PASSIVE)" in c for c in spy.calls)
    w._close_db()


def test_teardown_truncate_and_optimize(cfg):
    w = make_writer(cfg)
    w._open_db()
    spy = ConnSpy(w._conn)
    w._conn = spy
    w._teardown_pragmas()
    assert any("wal_checkpoint(TRUNCATE)" in c for c in spy.calls)
    assert any("optimize" in c for c in spy.calls)
    assert not any("VACUUM" in c.upper() for c in spy.calls)  # §4.4: no VACUUM
    w._close_db()


# --------------------------------------------------------------------------------------------------
# Corruption recovery (§6.3)
# --------------------------------------------------------------------------------------------------
def test_corruption_archive_and_rebuild(cfg, tmp_path):
    path = SQLiteLiveWriter.resolve_filename(cfg.recorder["output_dir"], SESSION_DATE)
    with open(path, "wb") as fh:  # garbage bytes — not a valid SQLite header
        fh.write(b"this is definitely not a sqlite database " * 8)

    w = make_writer(cfg)
    w._open_db()  # must detect corruption, archive, rebuild
    live_path = w._path
    w._close_db()

    assert w.corruption_recoveries == 1
    import glob
    backups = glob.glob(path + ".corrupt_*.bak")
    assert backups, "expected an archived .corrupt_*.bak file"
    # The rebuilt DB is healthy and re-stamped.
    assert query(live_path, "PRAGMA quick_check")[0][0] == "ok"
    assert query(live_path, "SELECT built_by FROM recorder_meta")[0][0] == "live"


# --------------------------------------------------------------------------------------------------
# Thread lifecycle + robustness
# --------------------------------------------------------------------------------------------------
def test_graceful_drain_via_real_thread(cfg):
    q = queue.Queue()
    shutdown = threading.Event()
    w = make_writer(cfg, q=q, shutdown=shutdown)

    for i in range(3):
        q.put({"table": "spot_states",
               "rows": [row(SPOT_COLUMNS, timestamp=T0 + i, symbol="A", spot_price=float(i),
                            atm_strike=100)]})
    w.start()
    q.join()            # all envelopes consumed
    shutdown.set()      # signal graceful teardown
    w.join(timeout=5)
    assert not w.is_alive()

    path = SQLiteLiveWriter.resolve_filename(cfg.recorder["output_dir"], SESSION_DATE)
    assert query(path, "SELECT COUNT(*) FROM spot_states")[0][0] == 3
    assert w.rows_written == 3


def test_unknown_table_envelope_ignored(cfg):
    w = make_writer(cfg)
    w._open_db()
    w._buffer({"table": "bogus_table", "rows": [(1, 2, 3)]})
    assert w.unknown_table_total == 1
    assert w._buffered_rows == 0  # nothing routed
    w._close_db()


# --------------------------------------------------------------------------------------------------
# DuckDBAnalyticalWriter (P7, §3.6.5 / §4.1a) — offline fat-store bulk writer
# --------------------------------------------------------------------------------------------------
def _duck_query(path: str, sql: str):
    import duckdb

    con = duckdb.connect(path, read_only=True)
    try:
        return con.execute(sql).fetchall()
    finally:
        con.close()


def test_duckdb_ddl_and_provenance(cfg, tmp_path):
    out = str(tmp_path / "a.duckdb")
    with DuckDBAnalyticalWriter(cfg, out, session_date=SESSION_DATE, source_raw="raw.jsonl.gz",
                               time_fn=Clock()) as w:
        w.write({"table": "spot_states", "rows": [row(SPOT_COLUMNS, timestamp=T0, symbol="NIFTY",
                                                      spot_price=23500.0, atm_strike=23500)]})
    tables = {r[0] for r in _duck_query(out, "SELECT table_name FROM information_schema.tables")}
    assert {"spot_states", "option_strike_metrics", "strike_window_metrics",
            "aggregated_window_metrics", "recorder_meta"} <= tables
    meta = _duck_query(out, "SELECT schema_version, config_hash, built_by, build_time, source_raw "
                            "FROM recorder_meta")
    assert meta == [(SCHEMA_VERSION, cfg.config_hash, "replay", int(SESSION_EPOCH), "raw.jsonl.gz")]


def test_duckdb_round_trip_all_tables_and_nulls(cfg, tmp_path):
    out = str(tmp_path / "a.duckdb")
    opt = row(OPTION_COLUMNS, timestamp=T0, symbol="N23500CE", strike_price=23500.0, option_type="CE",
              depth_levels=50, is_50_depth=1, ltp=1.5, spread=0.05)  # rest default None → NULL
    with DuckDBAnalyticalWriter(cfg, out, session_date=SESSION_DATE, source_raw="r") as w:
        w.write({"table": "option_strike_metrics", "rows": [opt]})
        w.write({"table": "strike_window_metrics",
                 "rows": [row(STRIKE_WINDOW_COLUMNS, timestamp=T0, symbol="N23500CE", time_window=5)]})
        w.write({"table": "aggregated_window_metrics",
                 "rows": [row(AGG_COLUMNS, timestamp=T0, underlying="NIFTY", strike_window="SMALL",
                              regime="Balanced")]})
    # is_50_depth stored as a native BOOLEAN (§4.1a); NULLs preserved; regime VARCHAR round-trips.
    assert _duck_query(out, "SELECT typeof(is_50_depth), is_50_depth, ltp, mid_price "
                            "FROM option_strike_metrics") == [("BOOLEAN", True, 1.5, None)]
    assert _duck_query(out, "SELECT time_window, price_return FROM strike_window_metrics") == [(5, None)]
    assert _duck_query(out, "SELECT regime, depth_pcr FROM aggregated_window_metrics") == [("Balanced", None)]


def test_duckdb_idempotent_fresh_file(cfg, tmp_path):
    out = str(tmp_path / "a.duckdb")
    for _ in range(2):  # a re-run overwrites with an identical, single-copy build (§8.5)
        with DuckDBAnalyticalWriter(cfg, out, session_date=SESSION_DATE, source_raw="r") as w:
            w.write({"table": "spot_states",
                     "rows": [row(SPOT_COLUMNS, timestamp=T0, symbol="NIFTY", spot_price=1.0, atm_strike=1)]})
    assert _duck_query(out, "SELECT count(*) FROM spot_states") == [(1,)]
    assert not any(f.name.endswith(".building") or ".building_" in f.name
                   for f in tmp_path.iterdir())  # no temp build left behind


def test_duckdb_discards_build_on_error(cfg, tmp_path):
    out = str(tmp_path / "a.duckdb")
    with pytest.raises(RuntimeError):
        with DuckDBAnalyticalWriter(cfg, out, session_date=SESSION_DATE, source_raw="r") as w:
            w.write({"table": "spot_states",
                     "rows": [row(SPOT_COLUMNS, timestamp=T0, symbol="NIFTY", spot_price=1.0, atm_strike=1)]})
            raise RuntimeError("boom")  # exit with an exception → discard the partial build
    assert not os.path.exists(out)  # canonical store never created
    assert list(tmp_path.iterdir()) == [] or all("building" not in f.name for f in tmp_path.iterdir())


# --------------------------------------------------------------------------------------------------
# §P-C — streaming/chunked writer: peak-RSS bound via write_batch_rows (batching seam is _flush)
# --------------------------------------------------------------------------------------------------
def _cfg_batch(base_config, write_config, n: int):
    base_config["analytics_db"]["write_batch_rows"] = n
    return load_config(write_config(base_config))


def _spot_env(ts: int):
    return {"table": "spot_states",
            "rows": [row(SPOT_COLUMNS, timestamp=ts, symbol="NIFTY", spot_price=float(ts), atm_strike=ts)]}


def test_duckdb_chunked_matches_single_shot(base_config, write_config, tmp_path):
    """A tiny batch size (many flushes) yields identical content to one big batch (single flush) —
    batching changes only *when* rows are inserted, never the stored data (§P-C)."""
    envs = [_spot_env(T0 + i) for i in range(7)]
    results = {}
    for label, n in (("chunked", 2), ("single", 100000)):
        out = str(tmp_path / f"{label}.duckdb")
        with DuckDBAnalyticalWriter(_cfg_batch(base_config, write_config, n), out,
                                    session_date=SESSION_DATE, source_raw="r") as w:
            for e in envs:
                w.write(e)
        results[label] = _duck_query(out, "SELECT * FROM spot_states ORDER BY timestamp")
    assert results["chunked"] == results["single"]
    assert len(results["chunked"]) == 7


def test_duckdb_partial_final_batch_flushes(base_config, write_config, tmp_path):
    """Row count not a multiple of the batch size: the trailing partial batch must flush at finalize."""
    out = str(tmp_path / "a.duckdb")
    with DuckDBAnalyticalWriter(_cfg_batch(base_config, write_config, 3), out,
                                session_date=SESSION_DATE, source_raw="r") as w:
        for i in range(5):  # 5 rows, batch 3 → one full batch (3) + one partial (2) at finalize
            w.write(_spot_env(T0 + i))
    assert _duck_query(out, "SELECT count(*) FROM spot_states") == [(5,)]


def test_duckdb_batches_written_count(base_config, write_config, tmp_path):
    """batches_written is deterministic: a flush fires when a buffer reaches the threshold, plus one
    trailing flush per non-empty table at finalize."""
    out = str(tmp_path / "a.duckdb")
    with DuckDBAnalyticalWriter(_cfg_batch(base_config, write_config, 2), out,
                                session_date=SESSION_DATE, source_raw="r") as w:
        w.write(_spot_env(T0 + 0))      # buf=1, no flush
        w.write(_spot_env(T0 + 1))      # buf=2 ≥ 2 → flush #1
        w.write(_spot_env(T0 + 2))      # buf=1, no flush → flushed as #2 at finalize
        assert w.batches_written == 1   # only the threshold flush so far
    # after finalize: the trailing partial flushed
    assert _duck_query(out, "SELECT count(*) FROM spot_states") == [(3,)]


def _boom_insert(*_a, **_k):
    raise RuntimeError("insert boom")


def test_duckdb_failure_mid_batch_no_canonical(base_config, write_config, tmp_path, monkeypatch):
    """Failure while inserting a batch (during a write() threshold flush) → no canonical store, temp swept."""
    out = str(tmp_path / "a.duckdb")
    monkeypatch.setattr(DuckDBAnalyticalWriter, "_insert_executemany", staticmethod(_boom_insert))
    with pytest.raises(RuntimeError):
        with DuckDBAnalyticalWriter(_cfg_batch(base_config, write_config, 2), out,
                                    session_date=SESSION_DATE, source_raw="r") as w:
            w.write(_spot_env(T0 + 0))
            w.write(_spot_env(T0 + 1))  # buf=2 → flush → boom
    assert not os.path.exists(out)
    assert all("building" not in f.name for f in tmp_path.iterdir())


def test_duckdb_failure_between_batches_no_canonical(base_config, write_config, tmp_path):
    """Failure after one batch has flushed but before the next (an exception between batches) → the
    already-inserted batch lives only in the temp build, which is discarded → no canonical store."""
    out = str(tmp_path / "a.duckdb")
    with pytest.raises(RuntimeError):
        with DuckDBAnalyticalWriter(_cfg_batch(base_config, write_config, 2), out,
                                    session_date=SESSION_DATE, source_raw="r") as w:
            w.write(_spot_env(T0 + 0))
            w.write(_spot_env(T0 + 1))     # flush batch #1 (succeeds)
            assert w.batches_written == 1
            raise RuntimeError("between-batches boom")
    assert not os.path.exists(out)
    assert all("building" not in f.name for f in tmp_path.iterdir())


def test_duckdb_failure_final_partial_batch_no_canonical(base_config, write_config, tmp_path, monkeypatch):
    """Failure while flushing the trailing partial batch at finalize → no canonical store, temp swept."""
    out = str(tmp_path / "a.duckdb")
    monkeypatch.setattr(DuckDBAnalyticalWriter, "_insert_executemany", staticmethod(_boom_insert))
    with pytest.raises(RuntimeError):
        with DuckDBAnalyticalWriter(_cfg_batch(base_config, write_config, 100), out,
                                    session_date=SESSION_DATE, source_raw="r") as w:
            w.write(_spot_env(T0))  # < batch → no mid flush; the only flush is at finalize → boom
    assert not os.path.exists(out)
    assert all("building" not in f.name for f in tmp_path.iterdir())


def test_duckdb_failure_after_checkpoint_before_rename_no_canonical(base_config, write_config, tmp_path,
                                                                    monkeypatch):
    """Failure after CHECKPOINT but before the atomic rename → canonical store is all-or-nothing: it must
    be ABSENT (the completed build lived only in the temp, which the rename never promoted)."""
    import market_depth_recorder.database_writer as dw
    out = str(tmp_path / "a.duckdb")

    def boom_replace(_src, _dst):
        raise OSError("rename boom")

    monkeypatch.setattr(dw.os, "replace", boom_replace)
    with pytest.raises(OSError):
        with DuckDBAnalyticalWriter(_cfg_batch(base_config, write_config, 100), out,
                                    session_date=SESSION_DATE, source_raw="r") as w:
            w.write(_spot_env(T0))
    assert not os.path.exists(out)  # canonical never appears (either complete or absent)
