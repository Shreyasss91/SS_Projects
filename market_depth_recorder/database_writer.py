"""Store writers (spec §3.6). Two writers, one logical schema (§4), different backends.

**P5 builds ``SQLiteLiveWriter``** — the live-path batching consumer (§3.6.1–§3.6.4). It is the fourth
and final live thread: it drains ``db_queue`` (the per-second row envelopes emitted by
:class:`~market_depth_recorder.processor.TickProcessor`) and commits the ``recorder.live_metrics``
subset to the thin Tier-1 SQLite/WAL store ``market_depth_live_YYYYMMDD.db`` (§4.1). Small, frequent
WAL commits are exactly SQLite's strength, so the live path never blocks the pipeline.

``DuckDBAnalyticalWriter`` (§3.6.5) is the offline fat-store writer; it is **deferred to P7** and left
here as a construction-time stub (mirrors the P3 ``SdkTransport`` stub).

FD ownership (single-owner, no lock, decision 48): the ``sqlite3.Connection`` is created, PRAGMA-tuned,
DDL-initialized, written, checkpointed, and closed **only** by this thread's :meth:`run`. No other
thread touches it, so no DB lock is required — exclusive ownership is stronger than a lock. The only
file descriptor is the connection (plus its ``-wal``/``-shm`` sidecars), closed on every path (clean
drain, corruption rebuild, exception, shutdown, defensive date rollover). ``mark_restart_boundary`` is
the one deliberate cross-thread field (written by the P6 orchestrator, read here) — a single attribute
assignment is atomic under the GIL, so it too needs no lock.

Column order is imported from :mod:`~market_depth_recorder.processor` (single source of truth,
decision 49) so the ``INSERT`` statements can never drift from the tuple order the processor emits.

Genericization: no index/exchange/strike/CE-PE literal appears here — table and column names are the
§4 schema constants; symbols and underlyings flow through from the envelopes.

Lossless-raw invariant: this writer never touches the raw audit path. Live-store corruption is
**non-fatal** to the catalog (§6.3) — the fat DuckDB store is rebuilt from the untouched raw log at
end-of-session regardless — so on corruption the writer archives the bad file and rebuilds a fresh one.
"""

from __future__ import annotations

import os
import queue
import sqlite3
import threading
import time
from datetime import date, datetime

from . import SCHEMA_VERSION
from .config import Config
from .processor import AGG_COLUMNS, OPTION_COLUMNS, SPOT_COLUMNS, STRIKE_WINDOW_COLUMNS
from .utils import IST, get_logger

logger = get_logger(__name__)

_LIVE_FILENAME_FMT = "market_depth_live_%Y%m%d.db"

# Table → §4.1 column order (imported from processor — the authoritative emitted-tuple order).
_TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
    "spot_states": SPOT_COLUMNS,
    "option_strike_metrics": OPTION_COLUMNS,
    "strike_window_metrics": STRIKE_WINDOW_COLUMNS,
    "aggregated_window_metrics": AGG_COLUMNS,
}

_RECORDER_META_COLUMNS = ("schema_version", "config_hash", "built_by", "build_time", "source_raw")

# --------------------------------------------------------------------------------------------------
# DDL — the live SQLite store (§4.1 tables + §4.2 indexes + §4.1b provenance). Column order matches
# the processor's emitted tuples (verified in tests); the INSERT statements below name columns
# explicitly so a DDL/tuple mismatch would surface immediately rather than silently mis-map.
# --------------------------------------------------------------------------------------------------
_DDL = """
CREATE TABLE IF NOT EXISTS spot_states (
    timestamp INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    spot_price REAL NOT NULL,
    atm_strike INTEGER NOT NULL,
    PRIMARY KEY (timestamp, symbol)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS option_strike_metrics (
    timestamp INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    strike_price REAL NOT NULL,
    option_type TEXT NOT NULL,
    depth_levels INTEGER,
    is_50_depth INTEGER,
    ltp REAL,
    spread REAL,
    relative_spread REAL,
    mid_price REAL,
    micro_price REAL,
    weighted_obi REAL,
    raw_obi REAL,
    top5_obi REAL,
    top10_obi REAL,
    bid_stack_ratio REAL,
    ask_stack_ratio REAL,
    book_pressure REAL,
    best_bid_qty REAL,
    best_ask_qty REAL,
    avg_order_size_bid REAL,
    avg_order_size_ask REAL,
    oci REAL,
    effective_depth REAL,
    lci_bid REAL,
    lci_ask REAL,
    touch_dominance_bid REAL,
    touch_dominance_ask REAL,
    round_number_depth_bid REAL,
    round_number_depth_ask REAL,
    bid_wall_price REAL,
    bid_wall_qty REAL,
    ask_wall_price REAL,
    ask_wall_qty REAL,
    wall_score_bid REAL,
    wall_score_ask REAL,
    quote_stability REAL,
    confidence REAL,
    ofi REAL,
    fill_slippage_buy REAL,
    fill_slippage_sell REAL,
    book_slope_bid REAL,
    book_slope_ask REAL,
    queue_imbalance REAL,
    vamp REAL,
    microprice_ltp_div REAL,
    spread_ticks REAL,
    PRIMARY KEY (timestamp, symbol)
);

CREATE TABLE IF NOT EXISTS strike_window_metrics (
    timestamp INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    time_window INTEGER NOT NULL,
    price_return REAL,
    spread_mean REAL,
    spread_min REAL,
    spread_max REAL,
    spread_std REAL,
    wobi_mean REAL,
    wobi_std REAL,
    wobi_slope REAL,
    book_pressure_slope REAL,
    liquidity_added REAL,
    liquidity_removed REAL,
    book_churn REAL,
    flow_intensity REAL,
    pressure_velocity REAL,
    pressure_acceleration REAL,
    ofi_sum REAL,
    micro_price_rv REAL,
    wall_persistence REAL,
    walls_created INTEGER,
    walls_destroyed INTEGER,
    PRIMARY KEY (timestamp, symbol, time_window)
);

CREATE TABLE IF NOT EXISTS aggregated_window_metrics (
    timestamp INTEGER NOT NULL,
    underlying TEXT NOT NULL,
    strike_window TEXT NOT NULL,
    depth_pcr REAL,
    ce_pressure REAL,
    pe_pressure REAL,
    bnet REAL,
    spread_diff REAL,
    net_options_pressure REAL,
    pinning_score REAL,
    regime TEXT,
    PRIMARY KEY (timestamp, underlying, strike_window)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS recorder_meta (
    schema_version INTEGER NOT NULL,
    config_hash    TEXT    NOT NULL,
    built_by       TEXT    NOT NULL,
    build_time     INTEGER NOT NULL,
    source_raw     TEXT
);

CREATE INDEX IF NOT EXISTS idx_osm_strike ON option_strike_metrics (strike_price, option_type);
CREATE INDEX IF NOT EXISTS idx_osm_ts     ON option_strike_metrics (timestamp);
CREATE INDEX IF NOT EXISTS idx_swm_symbol ON strike_window_metrics (symbol, time_window);
CREATE INDEX IF NOT EXISTS idx_spot_ts    ON spot_states (timestamp);
"""


def _build_insert(table: str, columns: tuple[str, ...], verb: str) -> str:
    """``INSERT OR <verb> INTO table (cols…) VALUES (?, …)`` — columns named for drift-safety (§4.3)."""
    cols = ", ".join(columns)
    placeholders = ", ".join("?" * len(columns))
    return f"INSERT OR {verb} INTO {table} ({cols}) VALUES ({placeholders})"


class SQLiteLiveWriter(threading.Thread):
    """Background consumer of ``db_queue`` that batch-commits per-second rows to the thin live store.

    Args:
        config: Validated :class:`~market_depth_recorder.config.Config` (reads the ``database`` section
            + ``recorder.output_dir`` + ``config_hash``).
        db_queue: The metrics queue (P6 orchestrator owns it; injected here / by tests). Items are
            ``{"table": <name>, "rows": [tuple, …]}`` envelopes with tuples in exact §4.1 column order.
        shutdown_event: Set by the orchestrator to signal graceful teardown; the loop drains fully,
            commits the final batch, then runs the teardown PRAGMAs (§3.6.4).
        session_date: The session's local date — resolves the DB filename once (§3.6.3).
        schema_version: Persisted-schema stamp for ``recorder_meta`` (defaults to the package constant).
        time_fn: Injected clock (default :func:`time.time`) — sole source of the commit/checkpoint
            cadence, ``recorder_meta.build_time``, and the date-rollover comparison.
        error_queue: Optional sentinel-error register (P6 wires it); on a fatal ``run`` crash the thread
            reports here. ``None`` keeps P5 self-contained.
        name: Thread name (surfaced in every log line).
    """

    def __init__(
        self,
        config: Config,
        db_queue: "queue.Queue",
        shutdown_event: threading.Event,
        session_date: date,
        *,
        schema_version: int = SCHEMA_VERSION,
        time_fn=time.time,
        error_queue: "queue.Queue | None" = None,
        name: str = "SQLiteLiveWriter",
    ):
        super().__init__(name=name, daemon=True)
        db = config.database
        self._db_queue = db_queue
        self.shutdown_event = shutdown_event
        self.time_fn = time_fn
        self.error_queue = error_queue

        self.output_dir: str = config.recorder["output_dir"]
        self.batch_size: int = db["batch_size"]
        self.batch_write_interval_ms: int = db["batch_write_interval_ms"]
        self.cache_size_mb: int = db["cache_size_mb"]
        self.wal_checkpoint_interval_sec: float = db["wal_checkpoint_interval_sec"]

        self.schema_version = schema_version
        self.config_hash: str = config.config_hash

        # Precomputed per-table statements (decision 49) — named columns, both collision verbs.
        self._insert_ignore = {t: _build_insert(t, c, "IGNORE") for t, c in _TABLE_COLUMNS.items()}
        self._insert_replace = {t: _build_insert(t, c, "REPLACE") for t, c in _TABLE_COLUMNS.items()}

        # State owned exclusively by this thread once run() starts (except _boundary_ts, see below).
        self._current_date: date = session_date
        self._conn: sqlite3.Connection | None = None
        self._path: str | None = None
        self._buffers: dict[str, list[tuple]] = {t: [] for t in _TABLE_COLUMNS}
        self._buffered_rows = 0
        self._last_commit = 0.0
        self._last_checkpoint = 0.0

        # Cross-thread hand-off (fork A): set by the P6 orchestrator after a mid-day restart so the one
        # overlap second commits with INSERT OR REPLACE; read + reverted by this thread in _commit.
        self._boundary_ts: int | None = None

        # Health counters (read by the P6 health file; written only by this thread).
        self.rows_written = 0
        self.rows_ignored_total = 0
        self.commit_error_count = 0
        self.corruption_recoveries = 0
        self.unknown_table_total = 0

    # ---------------------------------------------------------------------------------------------
    # Public API (cross-thread)
    # ---------------------------------------------------------------------------------------------
    def mark_restart_boundary(self, boundary_ts: int) -> None:
        """Flag the single overlap second after a mid-day restart so its commit uses INSERT OR REPLACE
        (§4.3 / fork A). Called by the P6 orchestrator, **not** the writer thread — a lone attribute
        assignment is atomic under the GIL. The writer reverts to INSERT OR IGNORE once past the second.
        """
        self._boundary_ts = int(boundary_ts)

    @staticmethod
    def resolve_filename(output_dir: str, d: date) -> str:
        """Absolute path of the daily live DB for date ``d`` (§3.6.3). Reused by the orchestrator."""
        return os.path.join(output_dir, d.strftime(_LIVE_FILENAME_FMT))

    # ---------------------------------------------------------------------------------------------
    # Open / recover / schema / close
    # ---------------------------------------------------------------------------------------------
    def _open_db(self) -> None:
        """Open the current-date live DB: connect → integrity check (recover if corrupt) → PRAGMA →
        create schema + stamp provenance if the file is new/rebuilt (§3.6.2/§3.6.3/§4.1b/§6.3)."""
        os.makedirs(self.output_dir, exist_ok=True)
        self._path = self.resolve_filename(self.output_dir, self._current_date)
        need_schema = not os.path.exists(self._path)
        # isolation_level=None → autocommit; we manage BEGIN/COMMIT explicitly for batched writes.
        self._conn = sqlite3.connect(self._path, isolation_level=None)
        if not self._quick_check_ok():
            self._recover_corrupt_db()
            need_schema = True
        self._apply_pragmas()
        if need_schema:
            self._create_schema()
        now = self.time_fn()
        self._last_commit = now
        self._last_checkpoint = now
        logger.info("Opened live store %s", self._path)

    def _quick_check_ok(self) -> bool:
        """Fast corruption probe (§6.3). ``PRAGMA quick_check`` returns ``ok`` on a healthy DB; a fresh
        empty file passes trivially. A ``DatabaseError`` (header/format damage) counts as corrupt."""
        try:
            row = self._conn.execute("PRAGMA quick_check").fetchone()
        except sqlite3.DatabaseError:
            return False
        return bool(row) and row[0] == "ok"

    def _recover_corrupt_db(self) -> None:
        """Archive a corrupt live DB (+ its ``-wal``/``-shm``) and reconnect to a fresh file (§6.3).
        Non-fatal to the catalog — the fat store rebuilds from the untouched raw log."""
        logger.critical("Live store %s failed integrity check — archiving and rebuilding", self._path)
        try:
            if self._conn is not None:
                self._conn.close()
        except sqlite3.Error:
            pass
        self._conn = None
        ts = int(self.time_fn())
        for suffix in ("", "-wal", "-shm"):
            src = self._path + suffix
            if os.path.exists(src):
                dst = f"{self._path}.corrupt_{ts}.bak{suffix}"
                try:
                    os.replace(src, dst)
                except OSError as exc:
                    logger.error("Failed to archive %s → %s: %s", src, dst, exc)
        self._conn = sqlite3.connect(self._path, isolation_level=None)
        self.corruption_recoveries += 1

    def _apply_pragmas(self) -> None:
        """High-performance WAL tuning (§3.6.2). ``cache_size`` is negative → KiB (MiB × 1000)."""
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA temp_store=MEMORY")
        self._conn.execute(f"PRAGMA cache_size={-self.cache_size_mb * 1000}")

    def _create_schema(self) -> None:
        """Create the four tables + secondary indexes + ``recorder_meta``, then stamp one provenance
        row for this live build (§4.1/§4.2/§4.1b, decision 52)."""
        self._conn.executescript(_DDL)
        self._conn.execute(
            f"INSERT INTO recorder_meta ({', '.join(_RECORDER_META_COLUMNS)}) VALUES (?, ?, ?, ?, ?)",
            (self.schema_version, self.config_hash, "live", int(self.time_fn()), None),
        )

    def _close_db(self) -> None:
        """Close the connection (idempotent; guards a None/closed handle)."""
        conn = self._conn
        if conn is None:
            return
        self._conn = None
        try:
            conn.close()
        except sqlite3.Error as exc:
            logger.error("Error closing live store %s: %s", self._path, exc)

    # ---------------------------------------------------------------------------------------------
    # Buffer / commit / checkpoint
    # ---------------------------------------------------------------------------------------------
    def _buffer(self, envelope: dict) -> None:
        """Route one envelope's rows into its table buffer; an unknown table is counted + logged, never
        fatal (the loop must never crash on a malformed envelope)."""
        table = envelope.get("table")
        rows = envelope.get("rows") or []
        buf = self._buffers.get(table)
        if buf is None:
            self.unknown_table_total += 1
            logger.warning("db_writer: unknown table %r — %d row(s) ignored", table, len(rows))
            return
        buf.extend(rows)
        self._buffered_rows += len(rows)

    def _maybe_flush(self) -> None:
        """Commit when the buffer reaches ``batch_size`` rows OR ``batch_write_interval_ms`` has elapsed
        since the last commit (§3.6.1)."""
        if self._buffered_rows == 0:
            return
        elapsed_ms = (self.time_fn() - self._last_commit) * 1000.0
        if self._buffered_rows >= self.batch_size or elapsed_ms >= self.batch_write_interval_ms:
            self._commit()

    def _commit(self) -> None:
        """Commit all buffered rows in one transaction (§3.6.1). Uses INSERT OR REPLACE for the tables
        touching a marked restart-boundary second (fork A) and INSERT OR IGNORE otherwise, counting
        PK-collision drops. On error the transaction is rolled back and the batch dropped-with-count
        (no poison-batch retry — the fat store rebuilds from raw)."""
        conn = self._conn
        boundary = self._boundary_ts
        expected = 0
        max_ts: int | None = None
        try:
            conn.execute("BEGIN")
            before = conn.total_changes
            for table, buf in self._buffers.items():
                if not buf:
                    continue
                use_replace = boundary is not None and any(r[0] == boundary for r in buf)
                stmt = self._insert_replace[table] if use_replace else self._insert_ignore[table]
                conn.executemany(stmt, buf)
                expected += len(buf)
                batch_max = max(r[0] for r in buf)
                max_ts = batch_max if max_ts is None else max(max_ts, batch_max)
            conn.commit()
            applied = conn.total_changes - before
            self.rows_written += applied
            ignored = expected - applied
            if ignored > 0:
                self.rows_ignored_total += ignored
                logger.warning("db_writer: %d row(s) ignored on PK collision", ignored)
        except sqlite3.Error as exc:
            self.commit_error_count += 1
            logger.error("db_writer: commit failed, %d row(s) dropped: %s", expected, exc)
            try:
                conn.rollback()
            except sqlite3.Error:
                pass
        finally:
            for buf in self._buffers.values():
                buf.clear()
            self._buffered_rows = 0
            self._last_commit = self.time_fn()
        # Revert to INSERT OR IGNORE once we have flushed at/past the boundary second.
        if boundary is not None and max_ts is not None and max_ts >= boundary:
            self._boundary_ts = None

    def _maybe_checkpoint(self) -> None:
        """PASSIVE WAL checkpoint on a time cadence (§4.4) to keep the ``-wal`` bounded."""
        now = self.time_fn()
        if now - self._last_checkpoint >= self.wal_checkpoint_interval_sec:
            try:
                self._conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
            except sqlite3.Error as exc:
                logger.error("db_writer: PASSIVE checkpoint failed: %s", exc)
            self._last_checkpoint = now

    def _teardown_pragmas(self) -> None:
        """End-of-session maintenance (§4.4, authoritative over §3.6.4): fold + shrink the WAL and
        refresh index stats. **No VACUUM** (§4.4)."""
        try:
            self._conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            self._conn.execute("PRAGMA optimize")
        except sqlite3.Error as exc:
            logger.error("db_writer: teardown PRAGMAs failed: %s", exc)

    def _maybe_rollover(self) -> None:
        """Defensive daily-DB rollover (§3.6.3). Fires only if the IST date changes mid-run — a safety
        net for an unusually long-lived process, never the normal ~09:00→15:35 daily mechanism."""
        today = datetime.fromtimestamp(self.time_fn(), tz=IST).date()
        if today != self._current_date:
            logger.warning("Local date changed %s → %s; rolling over live store", self._current_date, today)
            self._final_flush()
            self._teardown_pragmas()
            self._close_db()
            self._current_date = today
            self._open_db()

    def _final_flush(self) -> None:
        """Commit any rows still buffered (clean drain / teardown / rollover)."""
        if self._buffered_rows > 0:
            self._commit()

    # ---------------------------------------------------------------------------------------------
    # Thread loop
    # ---------------------------------------------------------------------------------------------
    def _consume_loop(self) -> None:
        """Drain ``db_queue`` until shutdown is signaled AND the queue is empty (§3.6.4)."""
        q = self._db_queue
        while not self.shutdown_event.is_set() or not q.empty():
            self._maybe_rollover()
            try:
                envelope = q.get(timeout=1.0)
            except queue.Empty:
                self._maybe_flush()       # honor the time trigger while idle
                self._maybe_checkpoint()
                continue
            try:
                self._buffer(envelope)
                self._maybe_flush()
                self._maybe_checkpoint()
            finally:
                q.task_done()

    def run(self) -> None:  # noqa: D102 (threading.Thread.run)
        try:
            try:
                self._open_db()            # inside the finally so a partial open still closes its FD
                self._consume_loop()
                self._final_flush()        # only reached on a clean drain
                self._teardown_pragmas()
            finally:
                self._close_db()
        except Exception as exc:  # noqa: BLE001 — the writer thread must never die silently
            logger.exception("SQLiteLiveWriter crashed")
            if self.error_queue is not None:
                try:
                    self.error_queue.put((self.name, repr(exc)))
                except Exception:
                    logger.exception("Failed to report SQLiteLiveWriter crash to error_queue")


class DuckDBAnalyticalWriter:
    """Offline fat-store writer (§3.6.5) — **deferred to P7**.

    Runs inside the end-of-session replay subprocess, bulk-loading the full §4 catalog into the fat
    ``market_depth_analytics_YYYYMMDD.duckdb`` store in one pass. The body (fresh-file DDL, Appender/
    Arrow bulk load, ``CHECKPOINT``, ``with``-guarded close) lands in P7; construction fails loudly
    until then (mirrors the P3 ``SdkTransport`` stub).
    """

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("DuckDBAnalyticalWriter is built in P7 (offline DuckDB replay)")
