"""Recorder orchestrator — the conductor (spec §3.1, §6.4, §8.6).

P0–P5 built every worker as a standalone, tested thread; nothing yet constructs, wires, supervises, or
tears the pipeline down. :class:`RecorderOrchestrator` is that missing conductor: it owns the milestone
state machine + 1-second loop, the three queues / two shutdown events / error queue, the
construction·start·supervision·teardown of all four worker threads, mid-day-restart recovery, the health
file, the session guards (disk + trading calendar), and the end-of-session reprocess subprocess launcher.
It is driven by the ``default`` (no-mode) CLI entry (``__main__.py``) and implements ``--status`` output.

**Milestone model (plan decision 56 — act-at-launch, record-gate at ``session_start``).** On process
start the orchestrator resolves the chains (Init) and immediately builds + starts the pipeline (Connect),
regardless of wall time; the feed connects and subscribes spot LTPs right away. **Record** begins when
``now ≥ session_start`` (DSM option subscriptions then flow naturally from spot ticks). At ``session_end``
the DSM is **frozen** (Close, never-shrink holds — no unsubscribe). At ``session_end + teardown_grace``
the pipeline is drained + joined (Teardown). After a **clean EOF** the fat-store **Reprocess** subprocess
is launched. A launch that lands inside the record window *is* the §3.1.2 mid-day-restart path (REST-quote
ATM seed + ``mark_restart_boundary``), so there is no separate skip.

**Concurrency / FD ownership.** The main thread constructs, starts, supervises, and joins all four
workers; each worker owns its own state single-threaded (this module adds no worker locks). The only
cross-thread hand-offs introduced here are the thread-safe queues, the two ``threading.Event``s, the
``error_queue``, and the atomic single-word ``mark_restart_boundary(ts)`` write (P5-documented). The only
new persistent FDs are the health file (a transient temp fd the ``atomic_write`` helper closes) and the
reprocess child's log file + lock file — both explicitly closed / ``.wait()``-reaped / released. A
supervisor restart joins + drops the old threads/queues before building new ones (no leak across a
restart).

**Genericization.** No index/exchange/strike literal appears here — every underlying comes from
``config.underlyings`` and all per-underlying work is keyed by ``name``.
"""

from __future__ import annotations

import enum
import json
import os
import queue
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import date, datetime, time as dt_time

from .config import Config
from .database_writer import SQLiteLiveWriter
from .file_writer import RawTickFileWriter
from .instrument_manager import InstrumentManager, RestClient
from .processor import TickProcessor
from .utils import (
    IST, atomic_write, free_disk_mb, get_logger, now_ist, parse_ist_hhmm, process_rss_mb,
)
from .websocket_client import DepthWebSocketClient

logger = get_logger(__name__)

# Exit codes returned by run() (the CLI default entry propagates them to the shell).
EXIT_OK = 0
EXIT_FAILFAST = 1

_LOOP_INTERVAL_SEC = 1.0        # §3.1.1: the milestone loop sleeps ~1 s per cycle (injectable for tests).
_NON_TRADING_POLL_SEC = 3600.0  # trading-calendar idle poll cadence (§3.1.5; injectable for tests).
_JOIN_TIMEOUT_SEC = 10.0        # per-worker join budget on teardown (§3.1.4 thread.join(timeout=10)).
_LOCK_STALE_SEC = 6 * 3600.0    # reprocess lock older than this is treated as stale and stolen (§8.6).


class Milestone(str, enum.Enum):
    """The §3.1.1 milestone the orchestrator is currently in (surfaced as health ``state``)."""

    INIT = "init"
    CONNECT = "connect"
    RECORD = "record"
    CLOSE = "close"
    TEARDOWN = "teardown"
    REPROCESS = "reprocess"
    DONE = "done"


@dataclass
class _Pipeline:
    """One built-and-wired instance of the live pipeline (rebuilt fresh on every supervised restart).

    Two shutdown events, not one: ``shutdown_event`` stops the feed + processor + raw writer together;
    ``db_shutdown_event`` stops the **db writer separately** so teardown can join the processor first
    (draining ``proc_queue`` and flushing its final rows into ``db_queue``) and only then signal the db
    writer — otherwise both would see the shared event set with ``db_queue`` momentarily empty and the db
    writer could exit before the processor's final rows arrive (§3.1.4 ordered drain).
    """

    shutdown_event: threading.Event
    db_shutdown_event: threading.Event
    error_queue: "queue.Queue"
    raw_file_queue: "queue.Queue"
    proc_queue: "queue.Queue"
    db_queue: "queue.Queue"
    raw_writer: object
    db_writer: object
    processor: object
    feed: object

    def workers(self) -> list:
        return [self.feed, self.processor, self.db_writer, self.raw_writer]


def _default_reprocess_launcher(cmd: list[str], log_path: str) -> int:
    """Launch the reprocess child with stdout+stderr → a real log file (never a PIPE — FD hygiene) and
    ``.wait()``-reap it (§8.6 mode 1). Returns the child's exit code."""
    os.makedirs(os.path.dirname(os.path.abspath(log_path)), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as log_fh:
        log_fh.write(f"\n=== reprocess start {datetime.now(IST).isoformat()} ===\n")
        log_fh.flush()
        proc = subprocess.Popen(cmd, stdout=log_fh, stderr=subprocess.STDOUT)
        return proc.wait()


def _int_or_none(value) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


class RecorderOrchestrator:
    """Constructs, supervises, and tears down the four-thread live pipeline (see module docstring).

    Args:
        config: Validated :class:`~market_depth_recorder.config.Config`.
        instrument_manager: The (possibly not-yet-resolved) :class:`InstrumentManager`; the orchestrator
            resolves it exactly once at Init.
        time_fn / sleep_fn: Injected clock + sleep so every milestone/guard/supervisor branch is
            deterministic under test.
        transport: Optional feed transport (tests inject a fake); ``None`` → each feed selects by config.
        rest_client: Optional REST client for the mid-day-restart quote seed; ``None`` → built from config.
        pipeline_factory: ``factory(orchestrator) -> _Pipeline`` (tests inject fakes); ``None`` → the real
            four-thread build.
        reprocess_launcher: ``launcher(cmd, log_path) -> int`` (tests stub it); ``None`` → the real
            subprocess launcher.
        loop_interval_sec / non_trading_poll_sec: Loop + idle cadences (injectable to keep tests fast).
    """

    def __init__(
        self,
        config: Config,
        instrument_manager: InstrumentManager,
        *,
        time_fn=time.time,
        sleep_fn=time.sleep,
        transport=None,
        rest_client=None,
        pipeline_factory=None,
        reprocess_launcher=None,
        loop_interval_sec: float = _LOOP_INTERVAL_SEC,
        non_trading_poll_sec: float = _NON_TRADING_POLL_SEC,
        name: str = "Orchestrator",
    ):
        self._config = config
        self._im = instrument_manager
        self._time = time_fn
        self._sleep = sleep_fn
        self._transport = transport
        self._rest = rest_client or RestClient(
            config.openalgo["host_server"], config.openalgo["api_key"]
        )
        self._pipeline_factory = pipeline_factory or (lambda o: o._build_default_pipeline())
        self._reprocess_launcher = reprocess_launcher or _default_reprocess_launcher
        self._loop_interval = float(loop_interval_sec)
        self._non_trading_poll_sec = float(non_trading_poll_sec)
        self.name = name

        rec = config.recorder
        self._session_start_t = parse_ist_hhmm(rec["session_start"])
        self._session_end_t = parse_ist_hhmm(rec["session_end"])
        self._teardown_grace_min = int(rec["teardown_grace_min"])
        self.output_dir: str = rec["output_dir"]
        self._health_path: str = rec["health_file_path"]
        self._health_interval = float(rec["health_write_interval_sec"])
        self._min_free_disk_mb = float(rec["min_free_disk_mb"])
        self._disk_interval = float(rec["disk_check_interval_sec"])
        self._skip_non_trading = bool(rec["skip_non_trading_days"])
        self._supervisor_interval = float(rec["supervisor_interval_sec"])
        self._max_restart_attempts = int(rec["max_restart_attempts"])
        self._holidays = (
            self._parse_holidays(rec.get("trading_holidays", [])) if self._skip_non_trading else set()
        )

        ws = config.websocket
        self._backoff_base = float(ws["backoff_base"])
        self._backoff_mult = float(ws["backoff_mult"])
        self._backoff_max = float(ws["backoff_max_sec"])

        # Runtime state (main-thread-owned).
        self._pipeline: _Pipeline | None = None
        self._state: str = Milestone.INIT.value
        self._session_date: date | None = None
        self._session_start_epoch = 0.0
        self._session_end_epoch = 0.0
        self._teardown_epoch = 0.0
        self._frozen = False
        self._external_stop = threading.Event()
        self._restart_count = 0
        self._consecutive_failures = 0
        self._clean_teardown = False
        self._last_health = 0.0
        self._last_disk_check = 0.0
        self._last_supervisor = 0.0

    # ================================================================= public entry
    def run(self) -> int:
        """Run one session end-to-end: (idle if a non-trading day) → resolve → build/supervise the
        pipeline until teardown → launch the reprocess. Returns a shell exit code."""
        if not self._await_trading_day():
            return EXIT_OK
        self._session_date = self._now_ist().date()
        self._compute_session_epochs()
        try:
            self._resolve_instruments()
        except Exception:
            logger.exception("Init failed: could not resolve instrument chains — aborting")
            return EXIT_FAILFAST
        logger.info(
            "orchestrator start: session_date=%s window=[%s..%s] teardown=+%dmin loop=%.0fs",
            self._session_date, self._session_start_t.strftime("%H:%M"),
            self._session_end_t.strftime("%H:%M"), self._teardown_grace_min, self._loop_interval,
        )
        rc = self._run_forever()
        if self._clean_teardown:
            self._launch_reprocess()
        self._state = Milestone.DONE.value
        logger.info("orchestrator exit rc=%d restarts=%d", rc, self._restart_count)
        return rc

    def stop(self) -> None:
        """Request a graceful shutdown from another thread / signal handler (idempotent)."""
        self._external_stop.set()
        p = self._pipeline
        if p is not None:
            p.shutdown_event.set()
            p.db_shutdown_event.set()

    # ================================================================= session guards
    def _await_trading_day(self) -> bool:
        """Trading-calendar guard (§3.1.5): if ``skip_non_trading_days`` and today (IST) is a weekend or a
        configured holiday, idle until the next trading day. Returns ``False`` if stopped externally."""
        if not self._skip_non_trading:
            return True
        logged = False
        while self._is_non_trading_day(self._today()):
            if self._external_stop.is_set():
                return False
            if not logged:
                logger.info(
                    "non-trading day %s — idling until the next trading day (skip_non_trading_days)",
                    self._today(),
                )
                logged = True
            self._sleep(self._non_trading_poll_sec)
        return True

    def _is_non_trading_day(self, d: date) -> bool:
        return d.weekday() >= 5 or d in self._holidays

    @staticmethod
    def _parse_holidays(raw) -> set:
        out = set()
        for h in raw or ():
            try:
                out.add(date.fromisoformat(str(h)))
            except ValueError:
                logger.warning("ignoring unparseable trading_holidays entry %r", h)
        return out

    def _disk_check(self, now: float) -> None:
        """Disk-space guard (§3.1.5): ERROR (non-blocking) when free space on ``output_dir`` falls below
        ``min_free_disk_mb`` — the early warning for the single sanctioned raw-loss mode (disk saturation)."""
        self._last_disk_check = now
        try:
            free = free_disk_mb(self.output_dir)
        except OSError as exc:
            logger.error("disk guard: cannot stat %s (%s)", self.output_dir, exc)
            return
        if free < self._min_free_disk_mb:
            logger.error(
                "LOW DISK: %.0f MiB free on %s < min_free_disk_mb=%.0f — raw capture may shed on "
                "genuine saturation (§1.4/§3.1.5)", free, self.output_dir, self._min_free_disk_mb,
            )

    def _maybe_disk_check(self, now: float) -> None:
        if now - self._last_disk_check >= self._disk_interval:
            self._disk_check(now)

    # ================================================================= init
    def _resolve_instruments(self) -> None:
        """Milestone 1 — resolve every weekly chain over REST (once; a supervised restart reuses them)."""
        im = self._im
        if getattr(im, "resolved", True):
            return
        logger.info("Init: resolving weekly option chains via REST")
        im.resolve()

    def _compute_session_epochs(self) -> None:
        d = self._session_date

        def epoch(t: dt_time) -> float:
            return datetime.combine(d, dt_time(t.hour, t.minute), tzinfo=IST).timestamp()

        self._session_start_epoch = epoch(self._session_start_t)
        self._session_end_epoch = epoch(self._session_end_t)
        self._teardown_epoch = self._session_end_epoch + self._teardown_grace_min * 60

    # ================================================================= supervised session loop
    def _run_forever(self) -> int:
        """Supervisor-restart wrapper: run a session cycle; on a worker crash rebuild + retry, bounded by
        ``max_restart_attempts`` (then fail-fast so an OS supervisor takes over — never a tight loop)."""
        while not self._external_stop.is_set():
            outcome = self._run_session_cycle()
            if outcome == "clean":
                self._clean_teardown = True
                self._consecutive_failures = 0
                return EXIT_OK
            # crash
            self._restart_count += 1
            self._consecutive_failures += 1
            if self._consecutive_failures > self._max_restart_attempts:
                logger.critical(
                    "supervisor: %d consecutive worker failures exceed max_restart_attempts=%d — "
                    "fail-fast (OS supervisor should relaunch)",
                    self._consecutive_failures, self._max_restart_attempts,
                )
                return EXIT_FAILFAST
            backoff = min(
                self._backoff_max,
                self._backoff_base ** self._consecutive_failures * self._backoff_mult,
            )
            logger.warning(
                "supervisor: rebuilding pipeline after crash (attempt %d/%d) in %.1fs",
                self._consecutive_failures, self._max_restart_attempts, backoff,
            )
            self._sleep(backoff)
        return EXIT_OK

    def _run_session_cycle(self) -> str:
        """Build + start the pipeline, run the milestone loop until teardown or a detected crash, and
        always drain + join in ``finally``. Returns ``"clean"`` or ``"crash"``."""
        self._state = Milestone.INIT.value
        self._frozen = False
        self._pipeline = self._pipeline_factory(self)
        self._start_pipeline()
        self._state = Milestone.CONNECT.value
        self._disk_check(self._now())  # startup disk guard (§3.1.5)
        if self._in_record_window(self._now()):
            self._seed_restart()
        outcome = "clean"
        try:
            outcome = self._milestone_loop()
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt — graceful teardown")
            self._external_stop.set()
            outcome = "clean"
        finally:
            self._teardown_pipeline()
        return outcome

    def _start_pipeline(self) -> None:
        """Start consumers (writers + processor) **before** the producer (feed), so no tick is teed into
        a queue whose consumer has not started."""
        p = self._pipeline
        p.raw_writer.start()
        p.db_writer.start()
        p.processor.start()
        p.feed.start()
        logger.info("pipeline started: 4 workers (raw · db · processor · feed)")

    def _milestone_loop(self) -> str:
        """The §3.1.1 1-second loop: advance milestone → freeze at session_end → teardown at grace →
        supervisor tick → health write → disk guard. Returns ``"clean"`` at teardown / external stop,
        ``"crash"`` on a detected worker failure."""
        while True:
            now = self._now()
            self._state = self._current_milestone(now)
            if self._state == Milestone.CLOSE.value and not self._frozen:
                self._pipeline.feed.freeze_dsm()
                self._frozen = True
            if self._state == Milestone.TEARDOWN.value:
                logger.info("teardown time reached (session_end + grace) — draining pipeline")
                return "clean"
            if self._external_stop.is_set() or self._pipeline.shutdown_event.is_set():
                return "clean"
            if self._supervisor_tick(now):
                return "crash"
            self._maybe_write_health(now)
            self._maybe_disk_check(now)
            self._sleep(self._loop_interval)

    def _current_milestone(self, now: float) -> str:
        if now >= self._teardown_epoch:
            return Milestone.TEARDOWN.value
        if now >= self._session_end_epoch:
            return Milestone.CLOSE.value
        if now >= self._session_start_epoch:
            return Milestone.RECORD.value
        return Milestone.CONNECT.value

    def _in_record_window(self, now: float) -> bool:
        return self._session_start_epoch <= now < self._session_end_epoch

    # ================================================================= mid-day restart (§3.1.2)
    def _seed_restart(self) -> None:
        """A launch/restart inside the record window resolves each ATM instantly via one REST quote per
        underlying, seeds the DSM, and flags the overlap second for INSERT OR REPLACE (plan decision 57).
        Any quote failure (needs a live broker session) → WARNING + fall back to the lazy WS spot seed."""
        boundary_ts = int(self._now())
        self._pipeline.db_writer.mark_restart_boundary(boundary_ts)
        logger.info(
            "mid-day restart in record window — seeding ATM via REST quotes (boundary_ts=%d)",
            boundary_ts,
        )
        for u in self._config.underlyings:
            try:
                ltp = self._rest.get_quote(u.spot_symbol, u.spot_exchange)
            except Exception as exc:  # noqa: BLE001 — any quote failure degrades to the WS spot seed
                logger.warning(
                    "mid-day seed: get_quote(%s/%s) failed (%s) — falling back to WS spot tick",
                    u.name, u.spot_exchange, exc,
                )
                continue
            self._pipeline.feed.seed_spot(u.name, ltp)
            logger.info("mid-day seed: %s spot=%.2f", u.name, ltp)

    # ================================================================= supervisor (§3.1.3)
    def _supervisor_tick(self, now: float) -> bool:
        """Every ``supervisor_interval_sec`` scan ``is_alive()`` on all four workers and drain the error
        queue. Returns ``True`` if any worker died or reported an error (triggers a rebuild)."""
        if now - self._last_supervisor < self._supervisor_interval:
            return False
        self._last_supervisor = now
        errors = []
        eq = self._pipeline.error_queue
        while True:
            try:
                errors.append(eq.get_nowait())
            except queue.Empty:
                break
        dead = [w.name for w in self._pipeline.workers() if not w.is_alive()]
        if dead or errors:
            logger.error("supervisor detected failure: dead=%s errors=%s", dead, errors)
            return True
        return False

    # ================================================================= teardown (§3.1.4)
    def _teardown_pipeline(self) -> None:
        """Drain + join in the §3.1.4 order. Set the shared event (feed·processor·raw), stop the feed, and
        join **feed → processor** first; only then signal the db writer's own event and join it (so the
        processor's final ``db_queue`` rows are committed); the raw writer drains independently."""
        p = self._pipeline
        if p is None:
            return
        p.shutdown_event.set()
        try:
            p.feed.stop()
        except Exception:  # noqa: BLE001 — stop must never break teardown
            logger.exception("error stopping feed")
        p.feed.join(timeout=_JOIN_TIMEOUT_SEC)
        p.processor.join(timeout=_JOIN_TIMEOUT_SEC)
        # Processor has fully drained proc_queue + pushed its final rows; now let the db writer finish.
        p.db_shutdown_event.set()
        p.db_writer.join(timeout=_JOIN_TIMEOUT_SEC)
        p.raw_writer.join(timeout=_JOIN_TIMEOUT_SEC)
        for w in p.workers():
            if w.is_alive():
                logger.error("worker %s did not join within %.0fs", w.name, _JOIN_TIMEOUT_SEC)

    # ================================================================= health file (§6.4)
    def _maybe_write_health(self, now: float) -> None:
        if now - self._last_health >= self._health_interval:
            self._write_health(now)
            self._last_health = now

    def _write_health(self, now: float) -> None:
        try:
            atomic_write(self._health_path, json.dumps(self.build_health(now), indent=2))
        except Exception:  # noqa: BLE001 — a health-write failure must never crash the loop
            logger.exception("failed to write health file %s", self._health_path)

    def build_health(self, now: float) -> dict:
        """Assemble the §6.4 health payload from the live workers' counters. ``getattr`` defaults keep it
        robust to a partially-featured fake and guarantee it never raises inside the loop."""
        p = self._pipeline
        feed, proc, dbw, raw = p.feed, p.processor, p.db_writer, p.raw_writer
        pstats = proc.stats() if hasattr(proc, "stats") else {}
        return {
            "timestamp": int(now),
            "state": self._state,
            "session_date": self._session_date.isoformat() if self._session_date else None,
            "config_hash": self._config.config_hash,
            "websocket_status": getattr(feed, "connection_status", "unknown"),
            "raw_file_queue_size": p.raw_file_queue.qsize(),
            "proc_queue_size": p.proc_queue.qsize(),
            "db_queue_size": p.db_queue.qsize(),
            "last_raw_tick_time": _int_or_none(getattr(feed, "last_recv_ts", None)),
            "active_contracts": len(getattr(feed, "active_subscriptions", ()) or ()),
            "raw_dropped_total": getattr(feed, "raw_dropped_total", 0),
            "proc_dropped_total": getattr(feed, "proc_dropped_total", 0),
            "db_rows_dropped_total": pstats.get("db_rows_dropped_total", 0),
            "degraded_level": pstats.get("degraded_level", 0),
            "actual_depth": dict(getattr(feed, "actual_depth", {}) or {}),
            "rows_written": getattr(dbw, "rows_written", 0),
            "rows_ignored_total": getattr(dbw, "rows_ignored_total", 0),
            "stale_rows_total": pstats.get("stale_rows_total", 0),
            "commit_error_count": getattr(dbw, "commit_error_count", 0),
            "corruption_recoveries": getattr(dbw, "corruption_recoveries", 0),
            "restart_count": self._restart_count,
            "raw_records_written": getattr(raw, "records_written", 0),
            # P8 perf-target observability (§6.4): processor cycle time + process RSS.
            "cycle_ms_p50": pstats.get("cycle_ms_p50", 0.0),
            "cycle_ms_max": pstats.get("cycle_ms_max", 0.0),
            "rss_mb": round(process_rss_mb(), 1),
        }

    # ================================================================= reprocess (§3.1.1 M6 / §8.6)
    def _launch_reprocess(self) -> None:
        """Milestone 6 — after a clean EOF, launch the detached fat-store build (§8.6 mode 1), guarded by
        the run lock and gated on ``reprocess.auto_on_session_end``. Skipped (scheduled ``--catchup``
        covers it) when the teardown was unclean or the lock is held."""
        rp = self._config.reprocess
        if not rp.get("auto_on_session_end"):
            logger.info("reprocess: auto_on_session_end disabled — skipping")
            return
        if not self._clean_eof():
            logger.info("reprocess: no clean EOF on today's raw log — skipping (scheduled --catchup covers it)")
            return
        if not self._acquire_reprocess_lock():
            logger.warning("reprocess: run lock held (%s) — skipping", rp.get("lock_file"))
            return
        self._state = Milestone.REPROCESS.value
        try:
            cmd = [
                sys.executable, "-m", "market_depth_recorder",
                "--replay", "--catchup", "--config", self._config.source_path,
            ]
            logger.info("reprocess: launching %s", " ".join(cmd))
            rc = self._reprocess_launcher(cmd, rp["log_file"])
            logger.info("reprocess: child exited rc=%s (log → %s)", rc, rp["log_file"])
        except Exception:  # noqa: BLE001 — a launcher failure must not crash the daemon
            logger.exception("reprocess: launcher failed")
        finally:
            self._release_reprocess_lock()

    def _clean_eof(self) -> bool:
        """True when this session's raw writer flushed its final EOF marker on a clean drain (the P2
        ``eof_written`` flag) — the gate for the automatic reprocess (§3.1.1 M6)."""
        p = self._pipeline
        return bool(p is not None and getattr(p.raw_writer, "eof_written", False))

    def _acquire_reprocess_lock(self) -> bool:
        """Exclusive-create the run lock; steal it only if it is stale (age > ``_LOCK_STALE_SEC``). Uses
        real wall-clock file age (independent of the injected clock — it is a physical file property)."""
        path = self._config.reprocess["lock_file"]
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                age = time.time() - os.path.getmtime(path)
            except OSError:
                return False
            if age <= _LOCK_STALE_SEC:
                return False
            logger.warning("reprocess: stealing stale run lock %s (age %.0fs)", path, age)
            try:
                os.unlink(path)
                fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except OSError:
                return False
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(f"{os.getpid()} {int(time.time())}\n")
        return True

    def _release_reprocess_lock(self) -> None:
        path = self._config.reprocess["lock_file"]
        try:
            os.unlink(path)
        except OSError:
            pass

    # ================================================================= default pipeline build
    def _build_default_pipeline(self) -> _Pipeline:
        """Construct the real four-thread pipeline with its queues + events. The feed's transport is left
        ``None`` (unless one was injected) so each rebuilt feed selects its own by config."""
        cfg = self._config
        q = cfg.queues
        shutdown = threading.Event()
        db_shutdown = threading.Event()
        err: queue.Queue = queue.Queue()
        raw_q: queue.Queue = queue.Queue(maxsize=int(q["raw_file_queue_max"]))
        proc_q: queue.Queue = queue.Queue(maxsize=int(q["max_queue_size"]))
        db_q: queue.Queue = queue.Queue(maxsize=int(q["max_queue_size"]))
        # Embed the resolved chain in the raw HEADER so the offline replay is self-contained (§8,
        # decision 65). A fake IM in tests may lack to_header_dict → HEADER simply omits it.
        instruments = self._im.to_header_dict() if hasattr(self._im, "to_header_dict") else None
        raw_writer = RawTickFileWriter(
            cfg, raw_q, shutdown, self._session_date, time_fn=self._time, error_queue=err,
            instruments=instruments,
        )
        db_writer = SQLiteLiveWriter(
            cfg, db_q, db_shutdown, self._session_date, time_fn=self._time, error_queue=err,
        )
        processor = TickProcessor(
            cfg, self._im, proc_q, db_q, shutdown, time_fn=self._time,
        )
        feed = DepthWebSocketClient(
            cfg, self._im, raw_q, proc_q, shutdown,
            time_fn=self._time, sleep_fn=self._sleep, transport=self._transport,
        )
        return _Pipeline(
            shutdown, db_shutdown, err, raw_q, proc_q, db_q, raw_writer, db_writer, processor, feed,
        )

    # ================================================================= clock helpers
    def _now(self) -> float:
        return self._time()

    def _now_ist(self) -> datetime:
        return datetime.fromtimestamp(self._time(), tz=IST)

    def _today(self) -> date:
        return self._now_ist().date()


# --------------------------------------------------------------------------------------------------
# --status reader (§6.4 / §8.2) — pretty-print the current health file.
# --------------------------------------------------------------------------------------------------
def read_status(health_path: str) -> tuple[int, str]:
    """Read + pretty-print the health file for ``--status``. Returns ``(exit_code, text)``. A missing
    file is not an error (the recorder simply is not running) → exit 0 with a friendly message."""
    if not os.path.exists(health_path):
        return EXIT_OK, f"recorder not running (no health file at {health_path})"
    try:
        with open(health_path, encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, ValueError) as exc:
        return EXIT_FAILFAST, f"could not read health file {health_path}: {exc}"
    lines = [f"RECORDER STATUS ({health_path}):"]
    ts = payload.get("timestamp")
    if isinstance(ts, (int, float)):
        age = int(now_ist().timestamp() - ts)
        lines.append(f"  as of        : {datetime.fromtimestamp(ts, tz=IST):%Y-%m-%d %H:%M:%S %Z} ({age}s ago)")
    for key in ("state", "session_date", "websocket_status", "active_contracts",
                "raw_file_queue_size", "proc_queue_size", "db_queue_size",
                "last_raw_tick_time", "raw_dropped_total", "db_rows_dropped_total",
                "degraded_level", "cycle_ms_p50", "cycle_ms_max", "rss_mb",
                "rows_written", "restart_count", "actual_depth"):
        if key in payload:
            lines.append(f"  {key:<20}: {payload[key]}")
    return EXIT_OK, "\n".join(lines)
