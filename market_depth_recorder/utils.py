"""Shared primitives for the Market Depth Recorder (spec §2.1 ``utils.py``).

Math helpers (decay arrays), logging configuration, IST/time helpers, an atomic-file-write helper,
and a disk-space helper. No engine constants live here — every magic number resolves from config.
"""

from __future__ import annotations

import logging
import math
import os
import shutil
import tempfile
from datetime import datetime, time as dt_time, timedelta, timezone

import numpy as np

# Indian Standard Time is a fixed +05:30 offset with no DST, so a fixed-offset tzinfo is exact and
# avoids a third-party tz dependency (spec keeps the recorder standalone, §1.3).
IST = timezone(timedelta(hours=5, minutes=30), name="IST")

# --------------------------------------------------------------------------------------------------
# F1 — Logging
# --------------------------------------------------------------------------------------------------
_LOG_FORMAT = "%(asctime)s %(levelname)-8s [%(threadName)s] %(name)s: %(message)s"
_LOG_CONFIGURED = False


def setup_logging(level: str = "INFO") -> None:
    """Configure the root logger with a single console handler (idempotent).

    Thread name is included in every line — the recorder is multi-threaded (§5.1) and the owning
    thread is load-bearing context. Level comes from ``recorder.log_level``. Calling this more than
    once only updates the level; it never stacks duplicate handlers (which would double every line
    and leak handler FDs).
    """
    global _LOG_CONFIGURED
    root = logging.getLogger()
    resolved = getattr(logging, str(level).upper(), logging.INFO)
    if not _LOG_CONFIGURED:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_LOG_FORMAT))
        root.addHandler(handler)
        _LOG_CONFIGURED = True
    root.setLevel(resolved)
    for handler in root.handlers:
        handler.setLevel(resolved)


def get_logger(name: str) -> logging.Logger:
    """Return a module logger. Mirrors the platform convention ``logger = get_logger(__name__)``."""
    return logging.getLogger(name)


# --------------------------------------------------------------------------------------------------
# F2 — IST / time helpers
# --------------------------------------------------------------------------------------------------
def parse_ist_hhmm(value: str) -> dt_time:
    """Parse an ``"HH:MM"`` string as an IST wall-clock time.

    Raises :class:`ValueError` with a clear message on a malformed value (drives §7.3 fast-fail for
    ``session_start``/``session_end`` and the ``--from``/``--to`` CLI args).
    """
    parts = str(value).strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"expected IST time as 'HH:MM', got {value!r}")
    try:
        hh, mm = int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise ValueError(f"non-numeric IST time {value!r}") from exc
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        raise ValueError(f"IST time out of range {value!r}")
    return dt_time(hour=hh, minute=mm, tzinfo=IST)


def now_ist() -> datetime:
    """Current wall-clock time in IST (the recorder's session timezone, §3.1)."""
    return datetime.now(IST)


def to_epoch_seconds(dt: datetime | None = None) -> int:
    """UTC epoch seconds for storage timestamps (§4.1 stores UNIX seconds, UTC). Naive datetimes are
    assumed to already be UTC; ``None`` means now."""
    if dt is None:
        return int(datetime.now(timezone.utc).timestamp())
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


# --------------------------------------------------------------------------------------------------
# F3 — Decay-weight array factory (Weighted OBI, spec §3.4.2 M8)
# --------------------------------------------------------------------------------------------------
def decay_weights(n_levels: int, decay_k: float) -> np.ndarray:
    """Exponential decay weights ``w_i = exp(-decay_k * (i - 1))`` for ``i in [1, n_levels]``.

    With the spec default ``decay_k = 0.2`` this yields ``w_1 = 1.0``, ``w_5 ≈ 0.45``, ``w_10 ≈ 0.16``,
    ``w_20 ≈ 0.02`` (§3.4.2 M8), prioritizing near-touch levels over far-OTM spoofing walls.
    """
    if n_levels < 1:
        raise ValueError(f"n_levels must be >= 1, got {n_levels}")
    if decay_k < 0:
        raise ValueError(f"decay_k must be >= 0, got {decay_k}")
    i = np.arange(n_levels, dtype=np.float64)  # 0..n-1 == (i-1) for i in 1..n
    return np.exp(-decay_k * i)


# --------------------------------------------------------------------------------------------------
# F4 — Atomic file write (health file, provenance — §6.4)
# --------------------------------------------------------------------------------------------------
def atomic_write(path: str, data: str, encoding: str = "utf-8") -> None:
    """Write ``data`` to ``path`` atomically (temp file in the same directory + ``os.replace``).

    A reader never observes a half-written file (matters for ``health.json``, §6.4). The temp file is
    fsynced before the rename and cleaned up on any failure so no descriptor or stray temp leaks.
    """
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp_", dir=directory)
    # Adopt the raw fd into a file object first; if that fails we still own the bare fd and must
    # close it explicitly (fd hygiene — the with-block below only closes it once adoption succeeds).
    try:
        fh = os.fdopen(fd, "w", encoding=encoding)
    except BaseException:
        os.close(fd)
        _silent_unlink(tmp)
        raise
    try:
        with fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)  # atomic on POSIX and Windows for same-volume paths
    except BaseException:
        _silent_unlink(tmp)
        raise


def _silent_unlink(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        pass


# --------------------------------------------------------------------------------------------------
# F5 — Disk-space helper (session guard, §3.1.5)
# --------------------------------------------------------------------------------------------------
def free_disk_mb(path: str) -> float:
    """Free space in MiB on the filesystem containing ``path`` (the disk-space guard reads this to
    surface the one condition — genuine disk saturation — under which raw capture may shed, §3.1.5)."""
    return shutil.disk_usage(path).free / (1024 * 1024)
