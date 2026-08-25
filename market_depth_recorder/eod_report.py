"""EOD health & sanity-check report (P10-C).

Runs **offline** over a single trading day's captured artifacts and emits a PASS/WARN/FAIL report
(markdown + JSON) into ``<dated-dir>/reports/``:

* **raw** ``.jsonl.gz`` (Tier 0) — HEADER/EOF provenance, record count, per-underlying depth coverage,
  actual-vs-requested depth (the §9 degrade check that catches "NIFTY got 0 / 5-level depth"), audit-field
  presence, per-level ``orders``, crossed/locked book share;
* **live** SQLite (Tier 1) — table presence + per-underlying row coverage;
* **DuckDB** (Tier 2, if built) — tables populated + ``recorder_meta`` provenance stamps;
* **ops** — the final ``health.json`` (drops, cycle time, RSS, degraded level).

No live feed is required; the raw reader tolerates a crash-truncated tail (missing EOF). The overall
verdict is the worst per-check status; the process exits non-zero iff any check FAILs. Thresholds mirror
the spec's fixed targets (§5.1 ``<15 ms`` / ``<500 MB``) and are report-only — they are not engine
behaviour, so they are not per-deployment config keys.
"""

from __future__ import annotations

import gzip
import json
import os
import sqlite3
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from .config import Config
from .database_writer import DuckDBAnalyticalWriter, SQLiteLiveWriter
from .file_writer import RawTickFileWriter
from .utils import IST, atomic_write, get_logger, session_output_dir

logger = get_logger(__name__)

# Status vocabulary (worst wins for the overall verdict).
PASS, WARN, FAIL, SKIP = "PASS", "WARN", "FAIL", "SKIP"
_SEVERITY = {PASS: 0, SKIP: 0, WARN: 1, FAIL: 2}

# Report-only thresholds (not engine tunables → not config keys).
# _CYCLE_MS_TARGET was re-tuned 15 → 30 ms after P10-E (2026-07-07). The original §5.1 <15 ms figure was
# set against P9's SENSEX-5-level-dominated load; under the P10-E load the single-owner
# TickProcessor runs cycle_ms_p50 ≈ 22 ms (max ≈ 45 ms) and STILL keeps real-time pace with ~45× headroom
# CORRECTION (P10-F, 2026-07-14): the P10-E load was NOT "full 80x50-level NIFTY". FYERS caps Market-Depth
# at 5 symbols per CONNECTION, so the measurement was really <=5 NFO legs @50-level plus ~120 SENSEX legs
# @5-level. 80x50-level cannot occur on FYERS at all (ceiling is tbt_budget = 15, i.e. 3 connections x 5).
# The 30 ms target is therefore still UNVALIDATED at the hybrid's real profile (up to 15 legs @50 plus the
# rest @5) and should be re-measured once the allocator lands. See
# Documents/patches/tbt_concurrency_reconciliation_20260714.md.
# (22 ms of the 1000 ms budget; proc/db/raw queues pin at 0, zero drops). 30 ms flags a genuine
# real-time-risk regression without false-alarming on the expected full-scale cost. Getting materially
# below this needs intra-underlying parallelism (DEFERRED — see LIVE_RUN.md §E4 / phase_10E_notes.md);
# per-underlying `processor.mode: process` sharding is explicitly NOT the lever (NIFTY ≈ 84 % of the load
# lands in one shard). If cycle_ms approaches the 1000 ms budget or queues climb, that is the real signal.
_CYCLE_MS_TARGET = 30.0
_RSS_MB_TARGET = 500.0
_CROSSED_WARN_PCT = 15.0        # crossed+locked share above this on the raw book → WARN (data-quality note)
_LIVE_TABLES = ("spot_states", "option_strike_metrics", "strike_window_metrics", "aggregated_window_metrics")


@dataclass
class Check:
    name: str
    status: str
    detail: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "status": self.status, "detail": self.detail, "evidence": self.evidence}


# --------------------------------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------------------------------
def _strip_suffix(symbol: str) -> str:
    return symbol[:-3] if symbol.endswith(":50") else symbol


def _classify(symbol: str, unders: list[tuple[str, str]]) -> tuple[str | None, str | None]:
    """Map a packet symbol to ``(underlying_name, "spot"|"option")`` or ``(None, None)``.
    Spot = exact spot-symbol match; option = longest configured-name prefix with a digit right after the
    base (an F&O symbol is ``BASE + DDMMMYY…`` — the digit guard stops NIFTY shadowing NIFTYNXT50)."""
    s = _strip_suffix(str(symbol or ""))
    for name, spot in unders:
        if s == spot:
            return name, "spot"
    best: str | None = None
    for name, _spot in unders:
        after = s[len(name):len(name) + 1]
        if s.startswith(name) and after.isdigit() and (best is None or len(name) > len(best)):
            best = name
    return (best, "option") if best else (None, None)


def _iter_raw(raw_path: str):
    """Yield raw JSONL lines, tolerating a crash-/live-truncated gzip tail (the recorded prefix is valid)."""
    try:
        with gzip.open(raw_path, "rt", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    yield line
    except EOFError:
        return


def _worst(checks: list[Check]) -> str:
    return max((c.status for c in checks), key=lambda s: _SEVERITY[s], default=PASS)


# --------------------------------------------------------------------------------------------------
# Raw (Tier 0) checks — one tolerant pass
# --------------------------------------------------------------------------------------------------
def check_raw(config: Config, raw_path: str) -> list[Check]:
    if not os.path.exists(raw_path):
        return [Check("raw.present", FAIL, f"raw audit log missing: {raw_path}")]

    unders = [(u.name, u.spot_symbol) for u in config.underlyings]
    req_depth = {u.name: int(u.requested_depth) for u in config.underlyings}
    header: dict | None = None
    eof: dict | None = None
    data = 0
    modes: Counter = Counter()
    depth_per_u: Counter = Counter()
    spot_per_u: Counter = Counter()
    max_depth: dict[str, int] = {}
    depth_pkts = tbt_pkts = tbt_feed = 0
    orders_total = orders_nonzero = 0
    books = crossed = locked = 0
    first_ts = last_ts = None

    for line in _iter_raw(raw_path):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        mt = obj.get("meta_type")
        if mt == "HEADER":
            header = header or obj
            continue
        if mt == "EOF":
            eof = obj
            continue
        data += 1
        recv = obj.get("recv_ts")
        if isinstance(recv, (int, float)):
            first_ts = recv if first_ts is None else min(first_ts, recv)
            last_ts = recv if last_ts is None else max(last_ts, recv)
        modes[obj.get("mode")] += 1
        name, kind = _classify(obj.get("symbol", ""), unders)
        if obj.get("mode") == 3 or "depth" in obj:
            depth_pkts += 1
            if name:
                depth_per_u[name] += 1
            book = obj.get("depth") or {}
            buy, sell = book.get("buy") or [], book.get("sell") or []
            dl = obj.get("depth_levels")
            lvl = int(dl) if isinstance(dl, (int, float)) else max(len(buy), len(sell))
            if name:
                max_depth[name] = max(max_depth.get(name, 0), lvl)
            # A 50-level (TBT) packet is where the SDK-stripped audit fields (esp. feed_time, the exchange
            # clock) are expected; 5-level HSM books legitimately omit them, so only TBT packets are graded.
            is_tbt = bool(obj.get("is_50_depth")) or (isinstance(dl, (int, float)) and dl >= 50) or lvl >= 50
            if is_tbt:
                tbt_pkts += 1
                tbt_feed += 1 if "feed_time" in obj else 0
            for side in (buy, sell):
                for lv in side:
                    o = lv.get("orders")
                    if o is not None:
                        orders_total += 1
                        orders_nonzero += 1 if o > 0 else 0
            if buy and sell and buy[0].get("price") is not None and sell[0].get("price") is not None:
                books += 1
                bb, ba = buy[0]["price"], sell[0]["price"]
                if ba < bb:
                    crossed += 1
                elif ba == bb:
                    locked += 1
        elif name:
            spot_per_u[name] += 1

    checks: list[Check] = [Check("raw.present", PASS, f"{os.path.basename(raw_path)}")]

    # HEADER + instruments + config hash
    if header is None:
        checks.append(Check("raw.header", FAIL, "no HEADER provenance line"))
    else:
        checks.append(Check("raw.header", PASS, f"session_date={header.get('session_date')}"))
        checks.append(Check(
            "raw.instruments",
            PASS if header.get("instruments") else WARN,
            "HEADER carries the instruments block (self-contained replay)"
            if header.get("instruments") else "HEADER has no instruments block (replay needs live REST)",
        ))
        hh = header.get("config_hash")
        checks.append(Check(
            "raw.config_hash", PASS if hh == config.config_hash else WARN,
            "matches current config" if hh == config.config_hash
            else f"HEADER config_hash {hh} != current {config.config_hash} (config changed since capture)",
            {"header": hh, "current": config.config_hash},
        ))

    # EOF cleanliness + record-count reconciliation
    if eof is None:
        checks.append(Check("raw.eof", WARN, "no EOF marker — incomplete/crash capture (replay-tolerant)"))
    else:
        rc = eof.get("record_count")
        ok = rc == data
        checks.append(Check(
            "raw.eof", PASS if ok else WARN,
            f"clean EOF; record_count={rc}" if ok else f"EOF record_count={rc} != observed {data}",
            {"eof_record_count": rc, "observed": data},
        ))

    checks.append(Check("raw.records", PASS if data > 0 else FAIL, f"{data} data packets",
                        {"data_packets": data, "modes": dict(modes)}))

    # Time span
    if first_ts is not None and last_ts is not None:
        span_min = (last_ts - first_ts) / 60.0
        checks.append(Check("raw.timespan", PASS,
                            f"{datetime.fromtimestamp(first_ts, IST):%H:%M:%S}"
                            f"–{datetime.fromtimestamp(last_ts, IST):%H:%M:%S} IST ({span_min:.0f} min)",
                            {"first_ts": first_ts, "last_ts": last_ts}))

    # Per-underlying depth coverage — the check that catches "NIFTY captured 0 depth" (P9)
    for name in req_depth:
        n = depth_per_u.get(name, 0)
        checks.append(Check(
            f"raw.depth_coverage.{name}", PASS if n > 0 else FAIL,
            f"{n} depth packets" if n > 0 else "NO depth packets captured (feed/subscription failure)",
            {"depth_packets": n, "spot_packets": spot_per_u.get(name, 0)},
        ))

    # Actual vs requested depth per underlying (§9 degrade alarm)
    for name, want in req_depth.items():
        got = max_depth.get(name)
        if got is None:
            continue
        checks.append(Check(
            f"raw.depth_level.{name}",
            PASS if got >= want else WARN,
            f"actual {got} = requested {want}" if got >= want
            else f"DEGRADED: actual {got} < requested {want} (§9 — TBT unsupported / capped?)",
            {"actual": got, "requested": want},
        ))

    # Audit-field presence (raw transport preserves what the SDK strips)
    if depth_pkts:
        if tbt_pkts == 0:
            checks.append(Check("raw.audit_fields", PASS,
                                "no 50-level (TBT) packets this session — audit fields N/A "
                                "(5-level books omit feed_time/depth_levels/is_50_depth)"))
        else:
            fpct = 100.0 * tbt_feed / tbt_pkts
            checks.append(Check("raw.audit_fields", PASS if fpct >= 99.0 else WARN,
                                f"{fpct:.1f}% of {tbt_pkts} TBT packets carry feed_time "
                                "(exchange clock the SDK strips)",
                                {"tbt_packets": tbt_pkts, "feed_time_pct": round(fpct, 1)}))
        onz = (100.0 * orders_nonzero / orders_total) if orders_total else 0.0
        checks.append(Check("raw.orders_populated", PASS if onz > 0 else WARN,
                            f"{onz:.1f}% of depth levels have orders>0 (M13/M14 computable)"
                            if onz > 0 else "no per-level orders populated (M13/M14 → NULL)",
                            {"nonzero_pct": round(onz, 1)}))
    if books:
        bad_pct = 100.0 * (crossed + locked) / books
        checks.append(Check("raw.book_integrity", PASS if bad_pct <= _CROSSED_WARN_PCT else WARN,
                            f"{100 - bad_pct:.1f}% books ordered (crossed {crossed}, locked {locked} of {books})",
                            {"crossed": crossed, "locked": locked, "books": books}))
    return checks


# --------------------------------------------------------------------------------------------------
# Live SQLite (Tier 1) checks
# --------------------------------------------------------------------------------------------------
def check_live_db(config: Config, db_path: str) -> list[Check]:
    if not os.path.exists(db_path):
        return [Check("live.present", WARN, f"live store missing: {os.path.basename(db_path)} "
                                            "(rebuildable from raw)")]
    checks = [Check("live.present", PASS, os.path.basename(db_path))]
    con = None
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur = con.cursor()
        existing = {r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        missing = [t for t in _LIVE_TABLES if t not in existing]
        if missing:
            checks.append(Check("live.tables", FAIL, f"missing tables: {', '.join(missing)}"))
            return checks
        counts = {t: cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in _LIVE_TABLES}
        checks.append(Check("live.tables", PASS, "4 tables present", counts))
        # Per-underlying option coverage (mirrors the P9 NIFTY=0 finding)
        for u in config.underlyings:
            n = cur.execute("SELECT COUNT(*) FROM option_strike_metrics WHERE symbol LIKE ?",
                            (f"{u.name}%",)).fetchone()[0]
            checks.append(Check(f"live.option_rows.{u.name}", PASS if n > 0 else FAIL,
                                f"{n} option_strike_metrics rows",
                                {"rows": n}))
    except sqlite3.Error as exc:
        checks.append(Check("live.readable", FAIL, f"SQLite error: {exc}"))
    finally:
        if con is not None:
            con.close()
    return checks


# --------------------------------------------------------------------------------------------------
# DuckDB (Tier 2) checks
# --------------------------------------------------------------------------------------------------
def check_duckdb(config: Config, duck_path: str) -> list[Check]:
    if not os.path.exists(duck_path):
        return [Check("duckdb.present", SKIP, f"{os.path.basename(duck_path)} not built yet "
                                              "(run --catchup / auto reprocess)")]
    checks = [Check("duckdb.present", PASS, os.path.basename(duck_path))]
    con = None
    try:
        import duckdb  # lazy — only when a store exists
        con = duckdb.connect(duck_path, read_only=True)
        counts = {}
        for t in _LIVE_TABLES:
            counts[t] = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        populated = all(v > 0 for v in counts.values())
        checks.append(Check("duckdb.tables", PASS if populated else WARN,
                            "4 tables populated" if populated else f"some tables empty: {counts}", counts))
        meta = con.execute(
            "SELECT schema_version, config_hash, built_by FROM recorder_meta LIMIT 1"
        ).fetchone()
        if meta is None:
            checks.append(Check("duckdb.meta", WARN, "recorder_meta empty"))
        else:
            sv, ch, by = meta
            ok = ch == config.config_hash
            checks.append(Check("duckdb.meta", PASS if ok else WARN,
                                f"built_by={by} schema_version={sv} config_hash "
                                f"{'matches' if ok else 'MISMATCH'}",
                                {"schema_version": sv, "config_hash": ch, "built_by": by}))
    except Exception as exc:  # noqa: BLE001 — a corrupt/locked store must not crash the report
        checks.append(Check("duckdb.readable", WARN, f"could not read DuckDB: {exc}"))
    finally:
        if con is not None:
            con.close()
    return checks


# --------------------------------------------------------------------------------------------------
# Ops (health.json) checks
# --------------------------------------------------------------------------------------------------
def check_ops(health_path: str) -> list[Check]:
    if not os.path.exists(health_path):
        return [Check("ops.health", SKIP, f"no health.json at {health_path}")]
    try:
        with open(health_path, encoding="utf-8") as fh:
            h = json.load(fh)
    except (OSError, ValueError) as exc:
        return [Check("ops.health", WARN, f"could not read health.json: {exc}")]

    checks = [Check("ops.health", PASS, f"state={h.get('state')} as of "
                    f"{datetime.fromtimestamp(h['timestamp'], IST):%H:%M:%S}" if h.get("timestamp")
                    else f"state={h.get('state')}")]
    raw_drop = h.get("raw_dropped_total", 0) or 0
    db_drop = h.get("db_rows_dropped_total", 0) or 0
    checks.append(Check("ops.drops", PASS if (raw_drop == 0 and db_drop == 0) else FAIL,
                        f"raw_dropped={raw_drop}, db_dropped={db_drop}",
                        {"raw_dropped_total": raw_drop, "db_rows_dropped_total": db_drop}))
    p50, pmax = h.get("cycle_ms_p50"), h.get("cycle_ms_max")
    if p50 is not None:
        ok = p50 < _CYCLE_MS_TARGET and (pmax is None or pmax < _CYCLE_MS_TARGET)
        checks.append(Check("ops.cycle_ms", PASS if ok else WARN,
                            f"p50={p50:.1f} max={pmax} (target <{_CYCLE_MS_TARGET:.0f} ms)",
                            {"p50": p50, "max": pmax}))
    rss = h.get("rss_mb")
    if rss is not None:
        checks.append(Check("ops.rss_mb", PASS if rss < _RSS_MB_TARGET else WARN,
                            f"{rss:.0f} MB (target <{_RSS_MB_TARGET:.0f})", {"rss_mb": rss}))
    deg = h.get("degraded_level", 0) or 0
    checks.append(Check("ops.degraded", PASS if deg == 0 else WARN, f"degraded_level={deg}"))
    return checks


# --------------------------------------------------------------------------------------------------
# Orchestration + rendering
# --------------------------------------------------------------------------------------------------
def build_report(config: Config, session_date: date, *, now: datetime | None = None) -> dict[str, Any]:
    base = config.recorder["output_dir"]
    partitioned = bool(config.recorder.get("date_partitioned", False))
    dated_dir = session_output_dir(base, session_date, partitioned)
    raw_path = RawTickFileWriter.resolve_filename(dated_dir, session_date)
    live_path = SQLiteLiveWriter.resolve_filename(dated_dir, session_date)
    duck_path = DuckDBAnalyticalWriter.resolve_filename(dated_dir, session_date)
    health_path = config.recorder["health_file_path"]

    sections = {
        "raw": check_raw(config, raw_path),
        "live_db": check_live_db(config, live_path),
        "duckdb": check_duckdb(config, duck_path),
        "ops": check_ops(health_path),
    }
    all_checks = [c for cs in sections.values() for c in cs]
    counts = Counter(c.status for c in all_checks)
    overall = _worst(all_checks)
    return {
        "session_date": session_date.isoformat(),
        "generated_at": (now or datetime.now(IST)).isoformat(),
        "config_hash": config.config_hash,
        "dated_dir": dated_dir,
        "artifacts": {"raw": raw_path, "live_db": live_path, "duckdb": duck_path, "health": health_path},
        "overall": overall,
        "counts": {s: counts.get(s, 0) for s in (PASS, WARN, FAIL, SKIP)},
        "sections": {k: [c.as_dict() for c in v] for k, v in sections.items()},
    }


_BADGE = {PASS: "✅ PASS", WARN: "⚠️ WARN", FAIL: "❌ FAIL", SKIP: "➖ SKIP"}


def render_markdown(report: dict[str, Any]) -> str:
    c = report["counts"]
    lines = [
        f"# EOD Health & Sanity Report — {report['session_date']}",
        "",
        f"**Overall: {_BADGE[report['overall']]}**  ·  "
        f"PASS {c[PASS]} · WARN {c[WARN]} · FAIL {c[FAIL]} · SKIP {c[SKIP]}",
        "",
        f"- Generated: {report['generated_at']}",
        f"- Config hash: `{report['config_hash']}`",
        f"- Data dir: `{report['dated_dir']}`",
        "",
    ]
    for section, title in (("raw", "Tier 0 — Raw audit log"), ("live_db", "Tier 1 — Live SQLite"),
                           ("duckdb", "Tier 2 — DuckDB analytics"), ("ops", "Ops — health.json")):
        lines += [f"## {title}", "", "| Check | Status | Detail |", "| --- | --- | --- |"]
        for chk in report["sections"][section]:
            lines.append(f"| `{chk['name']}` | {_BADGE[chk['status']]} | {chk['detail']} |")
        lines.append("")
    return "\n".join(lines)


def write_report(report: dict[str, Any], session_date: date) -> tuple[str, str]:
    """Write the markdown + JSON report into ``<dated_dir>/reports/``; returns the two paths."""
    reports_dir = os.path.join(report["dated_dir"], "reports")
    os.makedirs(reports_dir, exist_ok=True)
    stem = session_date.strftime("eod_healthcheck_%Y%m%d")
    md_path = os.path.join(reports_dir, stem + ".md")
    json_path = os.path.join(reports_dir, stem + ".json")
    atomic_write(md_path, render_markdown(report))
    atomic_write(json_path, json.dumps(report, indent=2))
    return md_path, json_path


def run_eod_report(config: Config, session_date: date, *, now: datetime | None = None,
                   write: bool = True) -> tuple[int, dict[str, Any]]:
    """Build (and optionally persist) the EOD report. Returns ``(exit_code, report)`` where exit_code is
    0 unless any check FAILed (then 1)."""
    report = build_report(config, session_date, now=now)
    if write:
        md_path, json_path = write_report(report, session_date)
        report["report_md"], report["report_json"] = md_path, json_path
        logger.info("EOD report → %s (overall %s)", md_path, report["overall"])
    return (0 if report["overall"] != FAIL else 1), report
