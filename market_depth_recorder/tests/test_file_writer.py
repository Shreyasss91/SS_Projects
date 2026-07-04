"""RawTickFileWriter (Tier-0 gzip audit log) tests — spec §3.5. All run offline (no feed/socket/DB).

Covers: HEADER/data/EOF round-trip, provenance stamping, the two-tier flush cadence (cheap flush vs
bounded fsync), tolerant reading of a torn/truncated trailing write, the defensive daily rollover, the
sanctioned write-error accounting (lossless-raw boundary, §1.4), graceful drain via the real thread,
and stdlib/pandas tooling compatibility (§3.5.1).
"""

from __future__ import annotations

import gzip
import json
import logging
import queue
import threading
from datetime import date, datetime
from pathlib import Path

import pytest

from market_depth_recorder import SCHEMA_VERSION
from market_depth_recorder.config import load_config
from market_depth_recorder.file_writer import RawTickFileWriter
from market_depth_recorder.utils import IST


# --------------------------------------------------------------------------------------------------
# Fixtures / helpers
# --------------------------------------------------------------------------------------------------
# The rollover guard compares dates in IST (matches session_date from now_ist()), so test epochs are
# built in IST too — keeps every test deterministic regardless of the host machine's timezone.
SESSION_DATE = date(2026, 7, 3)
SESSION_EPOCH = datetime(2026, 7, 3, 12, 0, 0, tzinfo=IST).timestamp()


@pytest.fixture
def cfg(base_config, write_config):
    """A loaded, validated Config whose output_dir points at the per-test tmp data dir."""
    return load_config(write_config(base_config))


class Clock:
    """Deterministic injected clock (epoch seconds) — drives timestamps, fsync cadence, rollover."""

    def __init__(self, t: float = SESSION_EPOCH):
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, d: float) -> None:
        self.t += d


def read_gz_lines(path: str) -> list[dict]:
    """Parse every JSONL record from a complete gzip log (stdlib only — no pandas dependency)."""
    out: list[dict] = []
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def read_gz_lines_tolerant(path: str) -> list[dict]:
    """Parse records from a possibly-torn gzip log, stopping cleanly at the first damaged/partial line
    (models reading an audit file after a crash — everything up to the last durable flush survives)."""
    out: list[dict] = []
    try:
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    break
    except (EOFError, OSError):
        pass  # missing gzip trailer on a truncated stream — prior lines already yielded
    return out


def _epoch_for(y: int, m: int, d: int, hh: int = 12) -> float:
    """IST epoch for a given date at noon (matches datetime.fromtimestamp(..., tz=IST).date())."""
    return datetime(y, m, d, hh, 0, 0, tzinfo=IST).timestamp()


# --------------------------------------------------------------------------------------------------
# Round-trip + provenance
# --------------------------------------------------------------------------------------------------
def test_round_trip_header_data_eof(cfg):
    packets = [{"ltp": 100.5 + i, "timestamp": 1000 + i, "depth": {"buy": [], "sell": []}}
               for i in range(5)]
    q: queue.Queue = queue.Queue()
    for p in packets:
        q.put(p)
    ev = threading.Event()
    ev.set()  # already signaled → run() drains the queued packets then exits
    clock = Clock()

    w = RawTickFileWriter(cfg, q, ev, session_date=date(2026, 7, 3), time_fn=clock)
    w.run()

    lines = read_gz_lines(w._filename)
    assert lines[0]["meta_type"] == "HEADER"
    assert lines[-1]["meta_type"] == "EOF"
    assert lines[-1]["record_count"] == len(packets)
    assert lines[-1]["close_timestamp"] == int(clock())
    assert lines[1:-1] == packets                 # exact data round-trip, order preserved
    assert w.records_written == len(packets)
    assert w.write_error_count == 0


def test_header_provenance(cfg):
    q: queue.Queue = queue.Queue()
    ev = threading.Event()
    ev.set()
    clock = Clock()
    w = RawTickFileWriter(cfg, q, ev, session_date=date(2026, 7, 3), time_fn=clock)
    w.run()

    header = read_gz_lines(w._filename)[0]
    assert header["meta_type"] == "HEADER"
    assert header["schema_version"] == SCHEMA_VERSION
    assert header["config_hash"] == cfg.config_hash
    assert header["underlyings"] == ["NIFTY", "SENSEX"]
    assert header["session_date"] == "2026-07-03"
    assert header["open_timestamp"] == int(clock())


def test_resolve_filename(cfg):
    path = RawTickFileWriter.resolve_filename(cfg.recorder["output_dir"], date(2026, 7, 3))
    assert path.endswith("market_depth_raw_20260703.jsonl.gz")


# --------------------------------------------------------------------------------------------------
# Two-tier flush (§3.5.3)
# --------------------------------------------------------------------------------------------------
def test_cheap_flush_fires_at_flush_max_records(cfg, base_config, write_config):
    # flush_max_records=3, fsync effectively disabled → only the count-based flush branch fires.
    base_config["file_writer"]["flush_max_records"] = 3
    base_config["file_writer"]["fsync_interval_sec"] = 1e9
    cfg = load_config(write_config(base_config))
    clock = Clock()
    w = RawTickFileWriter(cfg, queue.Queue(), threading.Event(), date(2026, 7, 3), time_fn=clock)
    w._open_file()
    try:
        w._write_packet({"n": 1})
        w._write_packet({"n": 2})
        assert w.unflushed_count == 2               # below threshold → not yet flushed
        w._write_packet({"n": 3})
        assert w.unflushed_count == 0               # threshold hit → cheap flush reset the counter
    finally:
        w._close_file()


def test_durable_fsync_is_time_bounded(cfg, base_config, write_config, monkeypatch):
    import market_depth_recorder.file_writer as fw_mod

    calls = {"n": 0}
    monkeypatch.setattr(fw_mod.os, "fsync", lambda fd: calls.__setitem__("n", calls["n"] + 1))

    base_config["file_writer"]["flush_max_records"] = 10_000  # never trip the count branch
    base_config["file_writer"]["fsync_interval_sec"] = 2.0
    cfg = load_config(write_config(base_config))
    clock = Clock()
    w = RawTickFileWriter(cfg, queue.Queue(), threading.Event(), date(2026, 7, 3), time_fn=clock)
    w._open_file()  # sets last_fsync = clock()
    try:
        w._write_packet({"n": 1})                   # 0s elapsed → no fsync
        assert calls["n"] == 0
        clock.advance(2.5)                           # > interval → fsync once
        w._write_packet({"n": 2})
        assert calls["n"] == 1
        clock.advance(0.5)                           # < interval → still no new fsync
        w._write_packet({"n": 3})
        assert calls["n"] == 1
    finally:
        w._close_file()


# --------------------------------------------------------------------------------------------------
# Crash tolerance
# --------------------------------------------------------------------------------------------------
def test_missing_eof_and_truncated_tail_tolerated(cfg, base_config, write_config):
    # flush each line so every record sits at a gzip sync-flush boundary (independently decodable).
    base_config["file_writer"]["flush_max_records"] = 1
    cfg = load_config(write_config(base_config))
    data = [{"n": i} for i in range(6)]

    # Simulate a crash: open + write, close WITHOUT the EOF marker.
    w = RawTickFileWriter(cfg, queue.Queue(), threading.Event(), date(2026, 7, 3), time_fn=Clock())
    w._open_file()
    for p in data:
        w._write_packet(p)
    w._close_file()
    path = w._filename

    # Missing-EOF file is still fully readable: HEADER + all data, no EOF line.
    lines = read_gz_lines(path)
    assert lines[0]["meta_type"] == "HEADER"
    assert all(l.get("meta_type") != "EOF" for l in lines)
    assert lines[1:] == data

    # Now tear the trailing bytes (gzip trailer + into the last block) and re-read tolerantly.
    raw = Path(path).read_bytes()
    torn = Path(path + ".torn")
    torn.write_bytes(raw[:-12])
    recovered = read_gz_lines_tolerant(str(torn))
    assert recovered and recovered[0]["meta_type"] == "HEADER"
    recovered_data = [l for l in recovered if l.get("meta_type") != "HEADER"]
    assert recovered_data == data[: len(recovered_data)]   # a clean prefix — never corrupted mid-stream


# --------------------------------------------------------------------------------------------------
# Defensive daily rollover (§3.5.4)
# --------------------------------------------------------------------------------------------------
def test_defensive_date_rollover(cfg):
    clock = Clock(t=_epoch_for(2026, 7, 3))
    w = RawTickFileWriter(cfg, queue.Queue(), threading.Event(),
                          session_date=date(2026, 7, 3), time_fn=clock)
    w._open_file()
    w._write_packet({"n": 1})              # same date → day-1 file
    clock.t = _epoch_for(2026, 7, 4)       # local date advances
    w._write_packet({"n": 2})              # triggers rollover → day-2 file
    w._write_eof()
    w._close_file()

    out_dir = cfg.recorder["output_dir"]
    f1 = read_gz_lines(RawTickFileWriter.resolve_filename(out_dir, date(2026, 7, 3)))
    f2 = read_gz_lines(RawTickFileWriter.resolve_filename(out_dir, date(2026, 7, 4)))

    assert f1[0]["session_date"] == "2026-07-03" and f1[-1]["meta_type"] == "EOF"
    assert f1[-1]["record_count"] == 1 and f1[1:-1] == [{"n": 1}]
    assert f2[0]["session_date"] == "2026-07-04" and f2[-1]["meta_type"] == "EOF"
    assert f2[-1]["record_count"] == 1 and f2[1:-1] == [{"n": 2}]


# --------------------------------------------------------------------------------------------------
# Lossless-raw boundary: write failure counted + logged, thread survives (§1.4)
# --------------------------------------------------------------------------------------------------
class _FakeHandle:
    """Stand-in gzip handle whose first N writes raise OSError (models disk saturation)."""

    def __init__(self, fail_times: int):
        self.fail = fail_times
        self.writes: list[str] = []

    def write(self, s: str) -> None:
        if self.fail > 0:
            self.fail -= 1
            raise OSError("disk full")
        self.writes.append(s)

    def flush(self) -> None:
        pass

    def fileno(self) -> int:
        raise ValueError("no real fd")   # exercises the guarded fsync path

    def close(self) -> None:
        pass


def test_write_error_counted_and_thread_survives(cfg, caplog):
    # Inject the fixed clock so the defensive rollover (which compares today vs session_date) never
    # fires on the real calendar date — otherwise the FakeHandle's one failing write is consumed by the
    # rollover EOF marker instead of the packet write it is meant to exercise.
    w = RawTickFileWriter(cfg, queue.Queue(), threading.Event(), SESSION_DATE, time_fn=Clock())
    w._fh = _FakeHandle(fail_times=1)     # no real file/FD; skip HEADER
    with caplog.at_level(logging.ERROR):
        w._write_packet({"a": 1})         # first write raises → counted, dropped
        w._write_packet({"a": 2})         # recovers
    assert w.write_error_count == 1
    assert w.records_written == 1
    assert w._fh.writes == ['{"a":2}\n']
    assert any("write failed" in r.message.lower() or "disk" in r.message.lower()
               for r in caplog.records)


# --------------------------------------------------------------------------------------------------
# Graceful drain through the real thread
# --------------------------------------------------------------------------------------------------
def test_graceful_drain_via_thread(cfg):
    q: queue.Queue = queue.Queue()
    ev = threading.Event()
    packets = [{"i": i} for i in range(50)]
    for p in packets:
        q.put(p)

    w = RawTickFileWriter(cfg, q, ev, session_date=date(2026, 7, 3))
    w.start()
    q.join()          # every enqueued packet processed (task_done)
    ev.set()          # then signal shutdown
    w.join(timeout=10)
    assert not w.is_alive()

    lines = read_gz_lines(w._filename)
    assert lines[-1]["meta_type"] == "EOF"
    assert lines[-1]["record_count"] == len(packets)
    assert lines[1:-1] == packets


# --------------------------------------------------------------------------------------------------
# Tooling compatibility (§3.5.1) — optional, pandas not a pinned dependency
# --------------------------------------------------------------------------------------------------
def test_pandas_read_json_compat(cfg):
    pd = pytest.importorskip("pandas")
    q: queue.Queue = queue.Queue()
    for p in [{"ltp": 1.0}, {"ltp": 2.0}]:
        q.put(p)
    ev = threading.Event()
    ev.set()
    w = RawTickFileWriter(cfg, q, ev, session_date=date(2026, 7, 3))
    w.run()

    df = pd.read_json(w._filename, lines=True, compression="gzip")
    assert len(df) == len(read_gz_lines(w._filename))   # HEADER + 2 data + EOF, parsed cleanly