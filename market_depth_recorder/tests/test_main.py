"""RecorderOrchestrator tests (spec §3.1 / §6.4 / §8.6). All run offline.

A virtual :class:`Clock` drives every milestone/guard/supervisor branch; the four workers are replaced
by lightweight fakes (via an injected ``pipeline_factory``) so a worker "crash" is just an
``is_alive()`` flip and teardown order is observable. No live broker / WS / market / subprocess.
"""

from __future__ import annotations

import json
import queue
import threading
from datetime import datetime

import pytest

from market_depth_recorder.config import load_config
from market_depth_recorder.main import (
    EXIT_FAILFAST,
    EXIT_OK,
    Milestone,
    RecorderOrchestrator,
    _Pipeline,
    read_status,
)
from market_depth_recorder.utils import IST


# --------------------------------------------------------------------------------------------------
# Virtual clock + fakes
# --------------------------------------------------------------------------------------------------
def ist_epoch(y, mo, d, h, mi, s=0) -> float:
    return datetime(y, mo, d, h, mi, s, tzinfo=IST).timestamp()


# 2026-07-06 is a Monday (trading day); 2026-07-04 is a Saturday.
MONDAY = (2026, 7, 6)
SATURDAY = (2026, 7, 4)


class Clock:
    """Deterministic clock: ``time()`` reads the cursor, ``sleep(dt)`` advances it (the design's
    inject-the-clock rule). Every orchestrator time branch is a pure function of this cursor."""

    def __init__(self, start: float):
        self.t = float(start)

    def time(self) -> float:
        return self.t

    def sleep(self, dt: float) -> None:
        self.t += float(dt)


class RecordingEvent(threading.Event):
    """A ``threading.Event`` that logs each ``set()`` so teardown ordering is observable."""

    def __init__(self, log: list, tag: str):
        super().__init__()
        self._log = log
        self._tag = tag

    def set(self) -> None:
        self._log.append(("set", self._tag))
        super().set()


class FakeWorker:
    """Thread-like stand-in: records start/join, ``is_alive`` optionally driven by a control callable."""

    def __init__(self, name: str, log: list, kind: str, alive_ctl=None):
        self.name = name
        self._log = log
        self._kind = kind
        self._alive = False
        self._alive_ctl = alive_ctl
        self.started = False

    def start(self):
        self.started = True
        self._alive = True

    def is_alive(self) -> bool:
        if self._alive_ctl is not None and self._alive:
            self._alive = self._alive_ctl()
        return self._alive

    def join(self, timeout=None):
        self._log.append(("join", self._kind))
        self._alive = False


class FakeFeed(FakeWorker):
    def __init__(self, name, log, alive_ctl=None):
        super().__init__(name, log, "feed", alive_ctl)
        self.connection_status = "connected"
        self.last_recv_ts = 1000.0
        self.active_subscriptions = {"NIFTY_A:50", "NIFTY_B:50"}
        self.raw_dropped_total = 0
        self.proc_dropped_total = 0
        self.actual_depth = {"NIFTY": 50, "SENSEX": 5}
        self.seeded: list = []
        self.frozen = False

    def stop(self):
        self._log.append(("stop", "feed"))
        self._alive = False

    def seed_spot(self, name, price):
        self.seeded.append((name, price))

    def freeze_dsm(self):
        self.frozen = True


class FakeProcessor(FakeWorker):
    def __init__(self, name, log, alive_ctl=None):
        super().__init__(name, log, "processor", alive_ctl)

    def stats(self):
        return {"degraded_level": 0, "stale_rows_total": 3, "db_rows_dropped_total": 0}


class FakeDbWriter(FakeWorker):
    def __init__(self, name, log, alive_ctl=None):
        super().__init__(name, log, "db", alive_ctl)
        self.rows_written = 42
        self.rows_ignored_total = 0
        self.commit_error_count = 0
        self.corruption_recoveries = 0
        self.boundary: int | None = None

    def mark_restart_boundary(self, ts):
        self.boundary = int(ts)


class FakeRawWriter(FakeWorker):
    def __init__(self, name, log, alive_ctl=None, eof_written=True):
        super().__init__(name, log, "raw", alive_ctl)
        self.records_written = 7
        self.eof_written = eof_written


class FakeIM:
    """Pre-resolved instrument manager stub — the orchestrator sees ``resolved=True`` and skips REST."""

    resolved = True


class NullRest:
    """A REST client whose ``get_quote`` returns instantly — the default so no test ever touches the
    network even if a cycle happens to start inside the record window (the mid-day-restart seed path)."""

    def get_quote(self, symbol, exchange):
        return 1.0


def make_factory(log, *, alive_ctls=None, eof_written=True):
    """Build a ``pipeline_factory`` yielding a fresh fake ``_Pipeline`` each call. ``alive_ctls`` maps a
    worker kind → a callable returning its next ``is_alive()`` value (for crash simulation)."""
    alive_ctls = alive_ctls or {}
    calls = {"n": 0}

    def factory(_orch):
        calls["n"] += 1
        shutdown = RecordingEvent(log, "shutdown")
        db_shutdown = RecordingEvent(log, "db_shutdown")
        err: queue.Queue = queue.Queue()
        raw_q: queue.Queue = queue.Queue()
        proc_q: queue.Queue = queue.Queue()
        db_q: queue.Queue = queue.Queue()
        feed = FakeFeed("Feed", log, alive_ctls.get("feed"))
        proc = FakeProcessor("TickProcessor", log, alive_ctls.get("processor"))
        dbw = FakeDbWriter("SQLiteLiveWriter", log, alive_ctls.get("db"))
        raw = FakeRawWriter("RawFileWriter", log, alive_ctls.get("raw"), eof_written=eof_written)
        return _Pipeline(shutdown, db_shutdown, err, raw_q, proc_q, db_q, raw, dbw, proc, feed)

    factory.calls = calls
    return factory


@pytest.fixture
def cfg(base_config, write_config):
    return load_config(write_config(base_config))


def _orch(cfg, clock, factory, **kw):
    return RecorderOrchestrator(
        cfg, FakeIM(),
        time_fn=clock.time, sleep_fn=clock.sleep,
        pipeline_factory=factory,
        rest_client=kw.pop("rest_client", NullRest()),
        loop_interval_sec=kw.pop("loop", 1.0),
        **kw,
    )


# --------------------------------------------------------------------------------------------------
# Milestone state machine (pure) — §3.1.1
# --------------------------------------------------------------------------------------------------
def test_current_milestone_transitions(cfg):
    clock = Clock(ist_epoch(*MONDAY, 9, 0))
    log: list = []
    o = _orch(cfg, clock, make_factory(log))
    o._session_date = datetime.fromtimestamp(clock.time(), tz=IST).date()
    o._compute_session_epochs()
    assert o._current_milestone(ist_epoch(*MONDAY, 9, 0)) == Milestone.CONNECT.value
    assert o._current_milestone(ist_epoch(*MONDAY, 9, 15)) == Milestone.RECORD.value
    assert o._current_milestone(ist_epoch(*MONDAY, 12, 0)) == Milestone.RECORD.value
    assert o._current_milestone(ist_epoch(*MONDAY, 15, 30)) == Milestone.CLOSE.value
    assert o._current_milestone(ist_epoch(*MONDAY, 15, 35)) == Milestone.TEARDOWN.value
    # record-gate window
    assert not o._in_record_window(ist_epoch(*MONDAY, 9, 0))
    assert o._in_record_window(ist_epoch(*MONDAY, 10, 0))
    assert not o._in_record_window(ist_epoch(*MONDAY, 15, 30))


# --------------------------------------------------------------------------------------------------
# Full session cycle: pre-open launch → record → freeze → teardown (clean) → reprocess gated
# --------------------------------------------------------------------------------------------------
def _tiny_session(base_config, end_min=16, grace=1):
    base_config["recorder"]["session_start"] = "09:15"
    base_config["recorder"]["session_end"] = f"09:{end_min:02d}"
    base_config["recorder"]["teardown_grace_min"] = grace
    return base_config


def test_full_clean_session_freezes_and_tears_down(base_config, write_config):
    cfg = load_config(write_config(_tiny_session(base_config)))
    clock = Clock(ist_epoch(*MONDAY, 9, 14, 50))
    log: list = []
    factory = make_factory(log)
    launches: list = []
    o = _orch(cfg, clock, factory, loop=20.0,
              reprocess_launcher=lambda cmd, logp: launches.append((cmd, logp)) or 0)
    rc = o.run()
    assert rc == EXIT_OK
    # feed was frozen at session_end (Close) and pipeline torn down cleanly.
    assert o._pipeline.feed.frozen is True
    assert factory.calls["n"] == 1  # no restart
    # Clean EOF + auto_on_session_end → reprocess launched once with the replay/catchup command.
    assert len(launches) == 1
    cmd, _ = launches[0]
    assert "--replay" in cmd and "--catchup" in cmd


def test_teardown_join_order(base_config, write_config):
    cfg = load_config(write_config(_tiny_session(base_config, end_min=16, grace=1)))
    # start in the Close window so the loop reaches teardown in a couple of steps
    clock = Clock(ist_epoch(*MONDAY, 9, 16, 50))
    log: list = []
    o = _orch(cfg, clock, make_factory(log), loop=20.0,
              reprocess_launcher=lambda *a: 0)
    o.run()
    # §3.1.4: shared shutdown set → feed stopped → feed & processor joined → THEN db_shutdown set →
    # db joined → raw joined. The db writer must not be signaled before the processor has drained.
    seq = [e for e in log if e in (
        ("set", "shutdown"), ("stop", "feed"), ("join", "feed"), ("join", "processor"),
        ("set", "db_shutdown"), ("join", "db"), ("join", "raw"))]
    assert seq == [
        ("set", "shutdown"), ("stop", "feed"), ("join", "feed"), ("join", "processor"),
        ("set", "db_shutdown"), ("join", "db"), ("join", "raw"),
    ]


# --------------------------------------------------------------------------------------------------
# Supervisor restart (§3.1.3)
# --------------------------------------------------------------------------------------------------
def _fast_supervise(base_config):
    base_config["recorder"]["supervisor_interval_sec"] = 1
    return base_config


def test_supervisor_restarts_then_resumes(base_config, write_config):
    cfg = load_config(write_config(_tiny_session(_fast_supervise(base_config), end_min=16, grace=0)))
    clock = Clock(ist_epoch(*MONDAY, 9, 14, 50))  # pre-open launch
    log: list = []
    # First build: feed is dead from the start; later builds: healthy.
    build = {"n": 0}

    def factory_wrapper(o):
        build["n"] += 1
        ctl = {"feed": (lambda: False)} if build["n"] == 1 else {}
        return make_factory(log, alive_ctls=ctl)(o)

    o = _orch(cfg, clock, factory_wrapper, loop=1.0, reprocess_launcher=lambda *a: 0)
    rc = o.run()
    assert rc == EXIT_OK
    assert o._restart_count == 1          # exactly one supervised rebuild
    assert build["n"] == 2                # crashed pipeline + healthy rebuild


def test_supervisor_fail_fast_after_max_attempts(base_config, write_config):
    cfg = load_config(write_config(_tiny_session(_fast_supervise(base_config), end_min=30, grace=1)))
    clock = Clock(ist_epoch(*MONDAY, 9, 14, 50))  # pre-open launch, wide window
    log: list = []
    # Every feed is dead → every cycle crashes → bounded by max_restart_attempts (default 3).
    factory = make_factory(log, alive_ctls={"feed": (lambda: False)})
    o = _orch(cfg, clock, factory, loop=1.0, reprocess_launcher=lambda *a: 0)
    rc = o.run()
    assert rc == EXIT_FAILFAST
    assert o._restart_count == 4          # 3 permitted + the 4th that trips fail-fast


# --------------------------------------------------------------------------------------------------
# Mid-day-restart ATM seed (§3.1.2)
# --------------------------------------------------------------------------------------------------
class FakeRest:
    def __init__(self, quotes: dict, fail: set | None = None):
        self._quotes = quotes
        self._fail = fail or set()
        self.calls: list = []

    def get_quote(self, symbol, exchange):
        self.calls.append((symbol, exchange))
        if symbol in self._fail:
            raise RuntimeError("no broker session")
        return self._quotes[symbol]


def test_midday_restart_seeds_and_marks_boundary(base_config, write_config):
    cfg = load_config(write_config(_tiny_session(base_config, end_min=30, grace=1)))
    clock = Clock(ist_epoch(*MONDAY, 9, 20))  # inside the record window → mid-day restart path
    log: list = []
    factory = make_factory(log)
    rest = FakeRest({"NIFTY": 23500.0, "SENSEX": 80000.0})
    o = _orch(cfg, clock, factory, loop=600.0, rest_client=rest,
              reprocess_launcher=lambda *a: 0)
    o.run()
    p = o._pipeline
    assert p.feed.seeded == [("NIFTY", 23500.0), ("SENSEX", 80000.0)]  # ATM seeded from REST quotes
    assert p.db_writer.boundary is not None                            # overlap second flagged
    assert rest.calls == [("NIFTY", "NSE_INDEX"), ("SENSEX", "BSE_INDEX")]


def test_midday_restart_quote_failure_falls_back(base_config, write_config):
    cfg = load_config(write_config(_tiny_session(base_config, end_min=30, grace=1)))
    clock = Clock(ist_epoch(*MONDAY, 9, 20))  # inside the record window
    log: list = []
    rest = FakeRest({"SENSEX": 80000.0}, fail={"NIFTY"})  # NIFTY quote fails
    o = _orch(cfg, clock, make_factory(log), loop=600.0, rest_client=rest,
              reprocess_launcher=lambda *a: 0)
    o.run()
    # NIFTY seed skipped (WS fallback), SENSEX still seeded — one failure never aborts the seed.
    assert o._pipeline.feed.seeded == [("SENSEX", 80000.0)]


# --------------------------------------------------------------------------------------------------
# Session guards (§3.1.5)
# --------------------------------------------------------------------------------------------------
def test_low_disk_logs_error(base_config, write_config, caplog, monkeypatch):
    cfg = load_config(write_config(_tiny_session(base_config, end_min=16, grace=0)))
    clock = Clock(ist_epoch(*MONDAY, 9, 16, 50))  # past teardown → startup disk check then drain
    monkeypatch.setattr("market_depth_recorder.main.free_disk_mb", lambda _p: 1.0)  # far below 2048
    o = _orch(cfg, clock, make_factory([]), loop=20.0, reprocess_launcher=lambda *a: 0)
    with caplog.at_level("ERROR"):
        o.run()
    assert any("LOW DISK" in r.message for r in caplog.records)


def test_holiday_idle_skips_session(base_config, write_config, caplog):
    base_config["recorder"]["skip_non_trading_days"] = True
    cfg = load_config(write_config(base_config))
    clock = Clock(ist_epoch(*SATURDAY, 9, 0))  # a weekend
    log: list = []
    factory = make_factory(log)
    o = _orch(cfg, clock, factory, loop=1.0)
    # Stop the idle loop after the first poll so the test does not spin.
    orig_sleep = clock.sleep

    def stop_after_first(dt):
        orig_sleep(dt)
        o._external_stop.set()

    o._sleep = stop_after_first
    with caplog.at_level("INFO"):
        rc = o.run()
    assert rc == EXIT_OK
    assert factory.calls["n"] == 0  # never built the pipeline on a non-trading day
    assert any("non-trading day" in r.message for r in caplog.records)


# --------------------------------------------------------------------------------------------------
# Health file (§6.4)
# --------------------------------------------------------------------------------------------------
def test_build_health_schema(cfg):
    clock = Clock(ist_epoch(*MONDAY, 10, 0))
    log: list = []
    o = _orch(cfg, clock, make_factory(log))
    o._session_date = datetime.fromtimestamp(clock.time(), tz=IST).date()
    o._pipeline = o._pipeline_factory(o)
    o._state = Milestone.RECORD.value
    health = o.build_health(clock.time())
    assert health["state"] == "record"
    assert health["websocket_status"] == "connected"
    assert health["active_contracts"] == 2
    assert health["actual_depth"] == {"NIFTY": 50, "SENSEX": 5}
    assert health["rows_written"] == 42
    assert health["stale_rows_total"] == 3
    assert health["config_hash"] == cfg.config_hash
    # every documented key present
    for key in ("timestamp", "raw_file_queue_size", "proc_queue_size", "db_queue_size",
                "last_raw_tick_time", "raw_dropped_total", "db_rows_dropped_total",
                "degraded_level", "restart_count"):
        assert key in health


def test_health_file_written_atomically(base_config, write_config, tmp_path):
    cfg = load_config(write_config(_tiny_session(base_config, end_min=16, grace=0)))
    clock = Clock(ist_epoch(*MONDAY, 9, 15, 30))  # in Record → the loop writes health before teardown
    o = _orch(cfg, clock, make_factory([]), loop=20.0, reprocess_launcher=lambda *a: 0)
    o.run()
    health_path = cfg.recorder["health_file_path"]
    with open(health_path, encoding="utf-8") as fh:
        payload = json.load(fh)   # valid JSON → never observed half-written
    assert "state" in payload and "config_hash" in payload
    # No stray temp files left behind by atomic_write.
    import os
    leftovers = [f for f in os.listdir(os.path.dirname(health_path)) if f.startswith(".tmp_")]
    assert leftovers == []


# --------------------------------------------------------------------------------------------------
# --status reader (§8.2)
# --------------------------------------------------------------------------------------------------
def test_read_status_missing_file(tmp_path):
    code, text = read_status(str(tmp_path / "nope.json"))
    assert code == EXIT_OK
    assert "not running" in text


def test_read_status_pretty_prints(tmp_path):
    path = tmp_path / "health.json"
    path.write_text(json.dumps({
        "timestamp": int(ist_epoch(*MONDAY, 10, 0)), "state": "record",
        "session_date": "2026-07-06", "websocket_status": "connected", "active_contracts": 164,
        "raw_dropped_total": 0, "actual_depth": {"NIFTY": 50},
    }), encoding="utf-8")
    code, text = read_status(str(path))
    assert code == EXIT_OK
    assert "RECORDER STATUS" in text
    assert "record" in text and "actual_depth" in text


# --------------------------------------------------------------------------------------------------
# Reprocess launcher (§3.1.1 M6 / §8.6)
# --------------------------------------------------------------------------------------------------
def test_reprocess_gated_on_clean_eof(base_config, write_config):
    cfg = load_config(write_config(_tiny_session(base_config, end_min=16, grace=0)))
    clock = Clock(ist_epoch(*MONDAY, 9, 16, 50))
    log: list = []
    launches: list = []
    # Raw writer reports NO clean EOF → reprocess must be skipped.
    factory = make_factory(log, eof_written=False)
    o = _orch(cfg, clock, factory, loop=20.0,
              reprocess_launcher=lambda cmd, logp: launches.append(cmd) or 0)
    o.run()
    assert launches == []


def test_reprocess_lock_acquired_and_released(base_config, write_config, tmp_path):
    cfg = load_config(write_config(_tiny_session(base_config, end_min=16, grace=0)))
    clock = Clock(ist_epoch(*MONDAY, 9, 16, 50))
    lock_path = cfg.reprocess["lock_file"]
    seen = {}

    def launcher(cmd, logp):
        # While the child "runs", the run lock exists.
        import os
        seen["lock_present"] = os.path.exists(lock_path)
        seen["cmd"] = cmd
        return 0

    o = _orch(cfg, clock, make_factory([]), loop=20.0, reprocess_launcher=launcher)
    o.run()
    import os
    assert seen["lock_present"] is True          # lock held during the launch
    assert not os.path.exists(lock_path)         # released afterwards
    assert "--replay" in seen["cmd"]


def test_reprocess_skipped_when_disabled(base_config, write_config):
    base_config["reprocess"]["auto_on_session_end"] = False
    cfg = load_config(write_config(_tiny_session(base_config, end_min=16, grace=0)))
    clock = Clock(ist_epoch(*MONDAY, 9, 16, 50))
    launches: list = []
    o = _orch(cfg, clock, make_factory([]), loop=20.0,
              reprocess_launcher=lambda cmd, logp: launches.append(cmd) or 0)
    o.run()
    assert launches == []
