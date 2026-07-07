"""Offline replay — rebuild the fat Tier-2 DuckDB analytical store from a raw log (spec §8).

Replay drives the **same** :class:`~market_depth_recorder.processor.TickProcessor` and metric bodies as
live capture — there is no second implementation to drift (§8.1). The only substitutions are the **clock
source** (a virtual clock advanced from each packet's ``recv_ts`` — the recorder clock the live resampler
boundary AND staleness keyed off, so the rebuild matches the live store second-for-second; plan decision
66) and the **sink** (`DuckDBAnalyticalWriter` bulk load instead of the live SQLite writer). The network,
raw, and live-SQLite writers are all absent — a file iterator stands in for the socket.

Self-containment (plan decision 65): the instrument context (symbol↔strike/type + ``tick_size``) is
reconstructed from the raw log's HEADER ``instruments`` block via
:meth:`InstrumentManager.from_header` — **no REST**, correct for a log of any age.

Concurrency / FDs: replay is a **single synchronous pass** — no threads, no subprocess. The processor is
driven directly (``ingest`` + ``emit_second``); the only FDs are the gzip reader (``with``-closed) and the
DuckDB build connection (``with``-closed + CHECKPOINT). The end-of-session M6 launcher (P6) already runs
this as a reaped subprocess, so nothing here leaks into the daemon.

Genericization: no index/exchange/strike literal — underlyings come from the HEADER/config, keyed by ``name``.
"""

from __future__ import annotations

import gzip
import json
import math
import os
import queue
import threading
import time
from datetime import date, datetime
from glob import glob

from .config import Config
from .database_writer import DuckDBAnalyticalWriter
from .instrument_manager import InstrumentManager
from .processor import (
    AGG_COLUMNS, OPTION_COLUMNS, SPOT_COLUMNS, STRIKE_WINDOW_COLUMNS, TickProcessor, strip_suffix,
)
from .utils import IST, get_logger

logger = get_logger(__name__)

_RAW_GLOB = "market_depth_raw_*.jsonl.gz"
_RAW_FILENAME_FMT = "market_depth_raw_%Y%m%d.jsonl.gz"
_LIVE_FILENAME_FMT = "market_depth_live_%Y%m%d.db"
_REPLAY_SUFFIX = ".replay.duckdb"

# Per-table (column tuple, primary-key columns) — used by the writer INSERTs (via processor) and verify.
_TABLE_SPEC: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "spot_states": (SPOT_COLUMNS, ("timestamp", "symbol")),
    "option_strike_metrics": (OPTION_COLUMNS, ("timestamp", "symbol")),
    "strike_window_metrics": (STRIKE_WINDOW_COLUMNS, ("timestamp", "symbol", "time_window")),
    "aggregated_window_metrics": (AGG_COLUMNS, ("timestamp", "underlying", "strike_window")),
}

# Verify float tolerance (§8.4). Replay of the same log is bit-deterministic, so the default is tight;
# it exists to absorb only DOUBLE↔REAL round-trip noise on the against-live path.
_VERIFY_ATOL = 1e-9


# --------------------------------------------------------------------------------------------------
# Raw reader (§8.5) — skip HEADER/EOF meta, tolerate a corrupt trailing line, count drops.
# --------------------------------------------------------------------------------------------------
def _load_header(fh) -> dict | None:
    """Read up to the first ``HEADER`` meta line and return it (``fh`` is left positioned just after).
    Returns ``None`` for a pre-enrichment log whose first non-empty line is not a HEADER."""
    for raw in fh:
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            return None
        if obj.get("meta_type") == "HEADER":
            return obj
        return None
    return None


class _ReplayStats:
    __slots__ = ("packets", "corrupt_lines", "rows", "output", "seconds")

    def __init__(self):
        self.packets = 0
        self.corrupt_lines = 0
        self.rows = 0
        self.output = None
        self.seconds = 0


# --------------------------------------------------------------------------------------------------
# Filters (§8.2, plan decision 72)
# --------------------------------------------------------------------------------------------------
def _ist_hhmm(recv_ts: float) -> tuple[int, int]:
    dt = datetime.fromtimestamp(recv_ts, tz=IST)
    return dt.hour, dt.minute


def _in_time_slice(recv_ts: float, from_t, to_t) -> bool:
    if from_t is None and to_t is None:
        return True
    hh, mm = _ist_hhmm(recv_ts)
    minutes = hh * 60 + mm
    if from_t is not None and minutes < from_t.hour * 60 + from_t.minute:
        return False
    if to_t is not None and minutes > to_t.hour * 60 + to_t.minute:
        return False
    return True


def _packet_underlying(pkt: dict, im: InstrumentManager, spot_to_name: dict) -> str | None:
    clean = strip_suffix(pkt.get("symbol"))
    meta = im.symbol_to_strike_map.get(clean)
    if meta is not None:
        return meta["underlying"]
    return spot_to_name.get(clean)


# --------------------------------------------------------------------------------------------------
# Core replay of one raw log → one DuckDB store
# --------------------------------------------------------------------------------------------------
def replay_file(
    config: Config,
    raw_path: str,
    output_path: str,
    *,
    underlying: str | None = None,
    from_t=None,
    to_t=None,
    time_fn=time.time,
) -> _ReplayStats:
    """Replay ``raw_path`` into a fresh DuckDB store at ``output_path`` with the **full** metric catalog.

    Drives the processor synchronously off packet ``recv_ts`` (decision 66/67), draining each emitted
    second into the DuckDB writer. ``--underlying`` / ``--from`` / ``--to`` are optional filters (a
    time-slice restarts rolling warm-up, so a sliced build is not comparable to a full-day build)."""
    stats = _ReplayStats()
    stats.output = output_path
    interval = float(config.recorder["resample_interval_sec"])
    spot_to_name = {u.spot_symbol: u.name for u in config.underlyings}

    with gzip.open(raw_path, "rt", encoding="utf-8") as fh:
        header = _load_header(fh)
        im = InstrumentManager.from_header(config, (header or {}).get("instruments"))
        # A holder so the processor's rare fallback clock (self._time()) reads the virtual time.
        vclock = {"t": 0.0}
        db_q: queue.Queue = queue.Queue()
        processor = TickProcessor(
            config, im, queue.Queue(), db_q, threading.Event(),
            time_fn=lambda: vclock["t"], active_metrics="all",
        )
        source_raw = os.path.basename(raw_path)
        session_date = _date_from_header_or_name(header, raw_path)

        with DuckDBAnalyticalWriter(
            config, output_path, session_date=session_date, source_raw=source_raw, time_fn=time_fn,
        ) as duck:
            next_b: float | None = None
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    stats.corrupt_lines += 1
                    logger.warning("replay: skipping corrupt line in %s (%d total)",
                                   source_raw, stats.corrupt_lines)
                    continue
                if obj.get("meta_type") in ("HEADER", "EOF"):
                    continue  # multi-HEADER (restart) / EOF tolerated
                recv = obj.get("recv_ts")
                if recv is None:
                    continue
                if not _in_time_slice(recv, from_t, to_t):
                    continue
                if underlying is not None and _packet_underlying(obj, im, spot_to_name) != underlying:
                    continue

                vclock["t"] = recv
                processor.ingest(obj)
                stats.packets += 1
                if next_b is None:
                    next_b = (math.floor(recv / interval) + 1) * interval  # first boundary after t0 (live parity)
                while recv >= next_b:
                    processor.emit_second(int(next_b))  # pushes envelopes to db_q
                    _drain(db_q, duck)
                    stats.seconds += 1
                    next_b += interval
            _drain(db_q, duck)  # any straggler envelopes
        stats.rows = duck.rows_written
    logger.info("replay: %s → %s (%d packets, %d seconds, %d rows, %d corrupt lines)",
                source_raw, os.path.basename(output_path), stats.packets, stats.seconds,
                stats.rows, stats.corrupt_lines)
    return stats


def _drain(db_q: queue.Queue, duck: DuckDBAnalyticalWriter) -> None:
    while True:
        try:
            env = db_q.get_nowait()
        except queue.Empty:
            return
        duck.write(env)


def _date_from_header_or_name(header: dict | None, raw_path: str) -> date | None:
    if header and header.get("session_date"):
        try:
            return date.fromisoformat(str(header["session_date"]))
        except ValueError:
            pass
    return _date_from_raw(raw_path)


def _date_from_raw(raw_path: str) -> date | None:
    try:
        return datetime.strptime(os.path.basename(raw_path), _RAW_FILENAME_FMT).date()
    except ValueError:
        return None


# --------------------------------------------------------------------------------------------------
# --catchup (§8.6 mode 2, plan decision 69) — rebuild any raw log lacking an up-to-date DuckDB store.
# --------------------------------------------------------------------------------------------------
def catchup(config: Config, *, time_fn=time.time) -> int:
    """Rebuild, oldest-first, every raw log whose canonical analytics store is missing or stale. A
    per-file failure is logged + skipped so one bad day never blocks the rest. Returns #rebuilt."""
    out_dir = config.recorder["output_dir"]
    partitioned = config.recorder.get("date_partitioned", False)
    # Raw logs live either flat under out_dir or in dated sub-folders (P10-B). Scan both so a mix of
    # legacy-flat and dated days both rebuild. Sort by filename (embeds YYYYMMDD) = chronological.
    patterns = [os.path.join(out_dir, _RAW_GLOB)]
    if partitioned:
        patterns.append(os.path.join(out_dir, "*", _RAW_GLOB))
    raws = sorted({p for pat in patterns for p in glob(pat)}, key=os.path.basename)
    built = 0
    for raw in raws:
        d = _date_from_raw(raw)
        if d is None:
            continue
        # Canonical store sits beside its raw log (same dated sub-folder in partitioned mode).
        duck_path = DuckDBAnalyticalWriter.resolve_filename(os.path.dirname(raw), d)
        if _is_up_to_date(duck_path, raw):
            logger.info("catchup: %s up-to-date — skipping", os.path.basename(duck_path))
            continue
        try:
            replay_file(config, raw, duck_path, time_fn=time_fn)
            built += 1
        except Exception:  # noqa: BLE001 — one bad day must not block the catchup
            logger.exception("catchup: failed to rebuild %s — skipping", os.path.basename(raw))
    logger.info("catchup: rebuilt %d store(s)", built)
    return built


def _is_up_to_date(duck_path: str, raw_path: str) -> bool:
    return os.path.exists(duck_path) and os.path.getmtime(duck_path) >= os.path.getmtime(raw_path)


# --------------------------------------------------------------------------------------------------
# --verify (§8.4, plan decision 70) — diff a fresh rebuild vs a reference (prior build / live store).
# --------------------------------------------------------------------------------------------------
# --verify-against-live tolerance. The live SQLite store is emitted on a WALL-CLOCK grid (emit fires as
# the second boundary passes, seeing whatever ticks have arrived); replay rebuilds on a TIMESTAMP grid
# (every tick of second T is assigned to T). At second boundaries these disagree on which tick was
# "last-in-second", so a small fraction of live rows legitimately differ from the replay — and the live
# store may miss its very first second. This is NOT drift: the canonical DuckDB is verified byte-identical
# by the strict (duckdb-vs-duckdb) determinism pass, and the live store is disposable. Empirically **0.88 %**
# of rows at full 50-level scale (P10-E, 2026-07-07: 658/74 697 — a row counts if ANY live_metrics cell
# differs). 2 % leaves headroom for busier sessions without masking a real regression. The strict
# duckdb-vs-duckdb determinism path keeps ZERO tolerance.
_LIVE_SUBSET_TOLERANCE_PCT = 2.0
_REPORT_MAX_LINES = 50


def verify(
    config: Config,
    built_path: str,
    reference_path: str,
    *,
    live_subset: bool = False,
) -> tuple[bool, list[str]]:
    """Diff the DuckDB build at ``built_path`` against ``reference_path``. Default reference is a prior
    DuckDB build (full column-for-column, **zero tolerance** — the determinism gate); ``live_subset``
    compares only the ``recorder.live_metrics`` columns against the SQLite live store (the rest are
    deliberately NULL there, §3.4.1) and **tolerates up to ``_LIVE_SUBSET_TOLERANCE_PCT`` of rows
    diverging** at second boundaries (see the constant above — expected, not drift). Returns
    ``(ok, report_lines)``; aborts on a ``recorder_meta`` schema_version/config_hash mismatch (a
    deliberate column-set change is not drift)."""
    ref_kind = "sqlite" if live_subset else "duckdb"
    report: list[str] = []

    ok, meta_report = _compare_meta(built_path, reference_path, ref_kind)
    report.extend(meta_report)
    if not ok:
        return False, report

    live_cols = _live_column_set(config) if live_subset else None
    tolerance_pct = _LIVE_SUBSET_TOLERANCE_PCT if live_subset else 0.0
    total_rows = 0        # union of comparable keys across all comparable tables
    divergent_rows = 0    # rows differing in any compared cell, or present on only one side
    shown = 0
    for table, (columns, pk) in _TABLE_SPEC.items():
        cmp_cols = _columns_to_compare(columns, pk, live_cols)
        if live_cols is not None and not cmp_cols:
            # No live_metrics column lands in this table (e.g. no rolling metric selected → the live
            # store never writes strike_window_metrics) — it is not comparable against the live store.
            continue
        built = _read_table("duckdb", built_path, table, columns, pk)
        ref = _read_table(ref_kind, reference_path, table, columns, pk)
        total_rows += len(built.keys() | ref.keys())
        if len(built) != len(ref):
            report.append(f"[{table}] row count differs: built={len(built)} ref={len(ref)}")
        for key in sorted(built.keys() & ref.keys(), key=lambda k: tuple(str(x) for x in k)):
            row_diff = False
            for col in cmp_cols:
                if not _values_equal(built[key].get(col), ref[key].get(col)):
                    row_diff = True
                    if shown < _REPORT_MAX_LINES:
                        report.append(f"[{table}] {key} {col}: built={built[key].get(col)!r} "
                                      f"ref={ref[key].get(col)!r}")
                        shown += 1
            if row_diff:
                divergent_rows += 1
        only_built = built.keys() - ref.keys()
        only_ref = ref.keys() - built.keys()
        divergent_rows += len(only_built) + len(only_ref)
        if only_built:
            report.append(f"[{table}] {len(only_built)} row(s) only in built (e.g. {next(iter(only_built))})")
        if only_ref:
            report.append(f"[{table}] {len(only_ref)} row(s) only in ref (e.g. {next(iter(only_ref))})")
    if shown >= _REPORT_MAX_LINES:
        report.append(f"… (cell mismatches truncated at {_REPORT_MAX_LINES} lines)")

    pct = (divergent_rows / total_rows * 100.0) if total_rows else 0.0
    ok = pct <= tolerance_pct
    if divergent_rows == 0:
        report.append("VERIFY OK: no drift")
    elif ok:  # live_subset within tolerance
        report.append(f"VERIFY OK: {divergent_rows}/{total_rows} rows differ ({pct:.2f}%) — within the "
                      f"{tolerance_pct:.1f}% live/replay boundary-timing tolerance (live store is "
                      f"disposable; canonical DuckDB verified separately)")
    else:
        report.append(f"VERIFY FAILED: {divergent_rows}/{total_rows} rows differ ({pct:.2f}%) — exceeds "
                      f"the {tolerance_pct:.1f}% tolerance")
    return ok, report


def _compare_meta(built_path: str, reference_path: str, ref_kind: str) -> tuple[bool, list[str]]:
    b = _read_meta("duckdb", built_path)
    r = _read_meta(ref_kind, reference_path)
    if b is None or r is None:
        return False, [f"recorder_meta missing (built={b is not None}, ref={r is not None})"]
    if b["schema_version"] != r["schema_version"]:
        return False, [f"schema_version mismatch: built={b['schema_version']} ref={r['schema_version']} "
                       "— aborting (deliberate column-set change is not drift)"]
    if b["config_hash"] != r["config_hash"]:
        return False, [f"config_hash mismatch: built={b['config_hash']} ref={r['config_hash']} "
                       "— aborting (formula/config differs)"]
    return True, []


def _live_column_set(config: Config) -> set[str]:
    """Columns the live store actually populates: the resolved live_metrics output columns + the base
    identity/capability columns the engine always fills (mirrors processor._BASE_OPTION_COLUMNS)."""
    from .metrics import registry

    active = registry.resolve_active(config.recorder["live_metrics"])
    cols = set(registry.active_columns(active))
    cols |= {"timestamp", "symbol", "strike_price", "option_type", "depth_levels", "is_50_depth",
             "ltp", "spot_price", "atm_strike", "underlying", "strike_window", "time_window"}
    return cols


def _columns_to_compare(columns: tuple[str, ...], pk: tuple[str, ...], live_cols: set | None) -> list[str]:
    non_pk = [c for c in columns if c not in pk]
    if live_cols is None:
        return non_pk
    return [c for c in non_pk if c in live_cols]


def _read_table(kind: str, path: str, table: str, columns: tuple[str, ...], pk: tuple[str, ...]) -> dict:
    col_list = ", ".join(columns)
    if kind == "duckdb":
        import duckdb

        con = duckdb.connect(path, read_only=True)
    else:
        import sqlite3

        con = sqlite3.connect(path)
    try:
        rows = con.execute(f"SELECT {col_list} FROM {table}").fetchall()
    finally:
        con.close()
    pk_idx = [columns.index(c) for c in pk]
    out = {}
    for r in rows:
        key = tuple(r[i] for i in pk_idx)
        out[key] = dict(zip(columns, r))
    return out


def _read_meta(kind: str, path: str) -> dict | None:
    if kind == "duckdb":
        import duckdb

        con = duckdb.connect(path, read_only=True)
    else:
        import sqlite3

        con = sqlite3.connect(path)
    try:
        row = con.execute("SELECT schema_version, config_hash FROM recorder_meta LIMIT 1").fetchone()
    except Exception:  # noqa: BLE001 — a missing table means no meta
        return None
    finally:
        con.close()
    if not row:
        return None
    return {"schema_version": row[0], "config_hash": row[1]}


def _values_equal(a, b) -> bool:
    """Tolerance-aware equality with NULL==NULL and bool↔int normalization (§8.4)."""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) == bool(b)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if isinstance(a, float) and math.isnan(a) and isinstance(b, float) and math.isnan(b):
            return True
        return abs(a - b) <= _VERIFY_ATOL
    return a == b


# --------------------------------------------------------------------------------------------------
# Output-path resolution (§8.1/§8.2) — canonical vs ad-hoc side file.
# --------------------------------------------------------------------------------------------------
def canonical_output(config: Config, raw_path: str) -> str:
    """The canonical ``market_depth_analytics_YYYYMMDD.duckdb`` for a raw log's date, placed **beside the
    raw log** so it lands in the same (possibly dated, P10-B) sub-folder — flat/partitioned agnostic.
    ``config`` is retained for signature stability."""
    d = _date_from_raw(raw_path)
    out_dir = os.path.dirname(raw_path)
    if d is None:
        base = os.path.basename(raw_path).replace(".jsonl.gz", "")
        return os.path.join(out_dir, f"{base}.duckdb")
    return DuckDBAnalyticalWriter.resolve_filename(out_dir, d)


def replay_side_output(raw_path: str) -> str:
    """An ad-hoc ``.replay.duckdb`` side file next to the raw log (never clobbers the canonical store)."""
    base = raw_path[:-len(".jsonl.gz")] if raw_path.endswith(".jsonl.gz") else raw_path
    return base + _REPLAY_SUFFIX


def live_store_path(config: Config, raw_path: str) -> str:
    """The SQLite live store for a raw log's date, **beside the raw log** (same dated sub-folder in
    partitioned mode). ``config`` retained for signature stability."""
    d = _date_from_raw(raw_path)
    out_dir = os.path.dirname(raw_path)
    if d is None:
        raise ValueError(f"cannot derive a date from {raw_path!r} for the live store")
    return os.path.join(out_dir, d.strftime(_LIVE_FILENAME_FMT))
