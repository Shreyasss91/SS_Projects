"""Tier-0 gzip flat-file writer (spec §3.5).

Records the raw incoming WebSocket tick stream into a compressed JSON Lines file
(``market_depth_raw_YYYYMMDD.jsonl.gz``) — the **lossless source of truth** (§1.4) from which both
derived stores (thin SQLite, fat DuckDB) are reconstructable by replay (§8). By isolating file I/O to
this dedicated thread, it shields the network receiver from disk-write latency.

FD ownership (single-owner, no lock): the gzip handle is created, written, flushed, fsynced, and
closed **only** by this thread's :meth:`run`. No other thread touches it, so no writing lock is
required — exclusive ownership is stronger than the spec's conservative "under its writing lock".
Thread owner · state owner · handle owner are all this one thread. The only file descriptor is the
gzip handle, closed on every path (clean drain, exception, rollover, shutdown).

Lossless-raw invariant (§1.4/§5.3): the single sanctioned raw-loss boundary is a genuine disk-write
failure — caught, counted (``write_error_count``), logged at ERROR, and the thread keeps draining.
Backpressure drops happen upstream at the tee (P3), never here.

Genericization: no index/exchange/strike literal appears here; the HEADER's ``underlyings`` list and
every threshold come from ``config``.
"""

from __future__ import annotations

import gzip
import json
import os
import queue
import threading
import time
from datetime import date, datetime

from . import SCHEMA_VERSION
from .config import Config
from .utils import IST, get_logger

logger = get_logger(__name__)

_RAW_FILENAME_FMT = "market_depth_raw_%Y%m%d.jsonl.gz"


class RawTickFileWriter(threading.Thread):
    """Background consumer of ``raw_file_queue`` that appends each packet to the daily gzip JSONL log.

    Args:
        config: Validated :class:`~market_depth_recorder.config.Config` (reads ``file_writer`` +
            ``recorder.output_dir`` + ``config_hash`` + underlying names).
        raw_file_queue: The audit queue (P6 orchestrator owns it; injected here / by tests).
        shutdown_event: Set by the orchestrator to signal graceful teardown; the loop drains fully
            before exiting (§3.5.1).
        session_date: The session's local date — resolves the filename once (§3.5.4).
        schema_version: Persisted-schema stamp for the HEADER (defaults to the package constant).
        time_fn: Injected clock (default :func:`time.time`) — sole source of epoch timestamps, the
            fsync cadence, and the date-rollover comparison, so every time branch is deterministic
            under test.
        error_queue: Optional sentinel-error register (P6 wires it); on a fatal ``run`` crash the
            thread reports here. ``None`` keeps P2 self-contained.
        name: Thread name (surfaced in every log line).
    """

    def __init__(
        self,
        config: Config,
        raw_file_queue: "queue.Queue",
        shutdown_event: threading.Event,
        session_date: date,
        *,
        schema_version: int = SCHEMA_VERSION,
        time_fn=time.time,
        error_queue: "queue.Queue | None" = None,
        name: str = "RawFileWriter",
    ):
        super().__init__(name=name, daemon=True)
        fw = config.file_writer
        self.queue = raw_file_queue
        self.shutdown_event = shutdown_event
        self.time_fn = time_fn
        self.error_queue = error_queue

        self.output_dir: str = config.recorder["output_dir"]
        self.gzip_compresslevel: int = fw["gzip_compresslevel"]
        self.flush_max_records: int = fw["flush_max_records"]
        self.fsync_interval_sec: float = fw["fsync_interval_sec"]

        self.schema_version = schema_version
        self.config_hash: str = config.config_hash
        self.underlyings: list[str] = [u.name for u in config.underlyings]

        # State owned exclusively by this thread once run() starts.
        self._current_date: date = session_date
        self._fh = None
        self._filename: str | None = None
        self.records_written = 0        # cumulative data packets (health)
        self._file_record_count = 0     # data packets in the current file (EOF record_count)
        self.write_error_count = 0      # sanctioned raw-loss counter (§1.4)
        self.unflushed_count = 0
        self.last_fsync = 0.0
        # True once run() wrote the final EOF marker on a clean drain — the P6 orchestrator gates the
        # end-of-session fat-store reprocess on this (§3.1.1 Milestone 6: reprocess only after a clean
        # EOF). A mid-loop crash skips EOF, leaving this False so reprocess is skipped for the day.
        self.eof_written = False

    # ---------------------------------------------------------------------------------------------
    # Filename / open / close
    # ---------------------------------------------------------------------------------------------
    @staticmethod
    def resolve_filename(output_dir: str, d: date) -> str:
        """Absolute path of the daily raw log for date ``d`` (§3.5.4). Reused by replay/orchestrator."""
        return os.path.join(output_dir, d.strftime(_RAW_FILENAME_FMT))

    def _open_file(self) -> None:
        """Open (append) the current-date gzip handle and write the provenance HEADER line (§3.5.4)."""
        os.makedirs(self.output_dir, exist_ok=True)
        self._filename = self.resolve_filename(self.output_dir, self._current_date)
        self._fh = gzip.open(
            self._filename, mode="at", compresslevel=self.gzip_compresslevel, encoding="utf-8"
        )
        self._file_record_count = 0
        self.unflushed_count = 0
        self.last_fsync = self.time_fn()
        header = {
            "meta_type": "HEADER",
            "session_date": self._current_date.isoformat(),
            "schema_version": self.schema_version,
            "config_hash": self.config_hash,
            "underlyings": self.underlyings,
            "open_timestamp": int(self.time_fn()),
        }
        self._fh.write(json.dumps(header, separators=(",", ":")) + "\n")
        self._fh.flush()  # make the HEADER durable to the OS early so a reader sees a described file
        logger.info("Opened raw audit log %s", self._filename)

    def _close_file(self) -> None:
        """Flush → fsync → close the handle (idempotent; guards a None/closed handle). No EOF here."""
        fh = self._fh
        if fh is None:
            return
        self._fh = None
        try:
            fh.flush()
            try:
                os.fsync(fh.fileno())
            except (OSError, ValueError):
                pass  # closed/invalid fileno — nothing durable to sync
            self.last_fsync = self.time_fn()
        finally:
            try:
                fh.close()
            except OSError as exc:
                logger.error("Error closing raw audit log %s: %s", self._filename, exc)

    # ---------------------------------------------------------------------------------------------
    # Write path
    # ---------------------------------------------------------------------------------------------
    def _write_packet(self, packet) -> None:
        """Serialize one packet to a JSONL line and append it, honoring rollover + two-tier flush.

        A serialization or disk-write failure is the single sanctioned raw-loss boundary (§1.4): it is
        counted and logged at ERROR, and the thread continues — one bad packet must not kill the audit
        path.
        """
        self._maybe_rollover()
        try:
            line = json.dumps(packet, separators=(",", ":"))
        except (TypeError, ValueError) as exc:
            self.write_error_count += 1
            logger.error(
                "Unserializable raw packet dropped: %s (%d write error(s) total)",
                exc, self.write_error_count,
            )
            return
        try:
            self._fh.write(line + "\n")
        except OSError as exc:
            self.write_error_count += 1
            logger.error(
                "Raw write failed (disk saturation?), packet dropped: %s (%d write error(s) total)",
                exc, self.write_error_count,
            )
            return
        self.records_written += 1
        self._file_record_count += 1
        self.unflushed_count += 1
        self._maybe_flush()

    def _maybe_flush(self) -> None:
        """Two-tier flush (§3.5.3): cheap ``flush()`` at ``flush_max_records``; bounded durable
        ``fsync`` every ``fsync_interval_sec`` (bounds the crash-loss window)."""
        now = self.time_fn()
        need_fsync = (now - self.last_fsync) >= self.fsync_interval_sec
        if self.unflushed_count >= self.flush_max_records or need_fsync:
            self._fh.flush()
            self.unflushed_count = 0
        if need_fsync:
            try:
                os.fsync(self._fh.fileno())
            except (OSError, ValueError):
                pass
            self.last_fsync = now

    def _maybe_rollover(self) -> None:
        """Defensive daily-file rollover (§3.5.4). Fires only if the IST date changes mid-run — a
        safety net for an unusually long-lived process, never the normal ~09:00→15:35 daily mechanism.

        Dates are compared in **IST** (the market timezone, matching ``session_date`` from ``now_ist()``)
        so the guard never fires spuriously on a non-IST host during a normal session."""
        today = datetime.fromtimestamp(self.time_fn(), tz=IST).date()
        if today != self._current_date:
            logger.warning(
                "Local date changed %s → %s; rolling over raw audit log",
                self._current_date, today,
            )
            self._write_eof()
            self._close_file()
            self._current_date = today
            self._open_file()

    def _write_eof(self) -> None:
        """Append the EOF provenance marker for the current file (§3.5.4): data ``record_count`` +
        ``close_timestamp``. Best-effort — a write failure here is logged, not fatal."""
        if self._fh is None:
            return
        eof = {
            "meta_type": "EOF",
            "record_count": self._file_record_count,
            "close_timestamp": int(self.time_fn()),
        }
        try:
            self._fh.write(json.dumps(eof, separators=(",", ":")) + "\n")
        except OSError as exc:
            logger.error("Failed to write EOF marker to %s: %s", self._filename, exc)

    # ---------------------------------------------------------------------------------------------
    # Thread loop
    # ---------------------------------------------------------------------------------------------
    def _consume_loop(self) -> None:
        """Drain ``raw_file_queue`` until shutdown is signaled AND the queue is empty (§3.5.1)."""
        q = self.queue
        while not self.shutdown_event.is_set() or not q.empty():
            try:
                packet = q.get(timeout=1.0)
            except queue.Empty:
                continue
            try:
                self._write_packet(packet)
            finally:
                q.task_done()

    def run(self) -> None:  # noqa: D102 (threading.Thread.run)
        try:
            self._open_file()
            try:
                self._consume_loop()
                self._write_eof()  # only reached on a clean drain
                self.eof_written = True  # clean EOF → the P6 reprocess gate (§3.1.1 M6) may fire
            finally:
                self._close_file()
        except Exception as exc:  # noqa: BLE001 — the audit thread must never die silently
            logger.exception("RawTickFileWriter crashed")
            if self.error_queue is not None:
                try:
                    self.error_queue.put((self.name, repr(exc)))
                except Exception:
                    logger.exception("Failed to report RawTickFileWriter crash to error_queue")
