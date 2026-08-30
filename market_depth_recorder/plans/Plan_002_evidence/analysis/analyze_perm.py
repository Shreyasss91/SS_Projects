"""Correlate the two health.json PermissionError events against watcher read windows.

Evidence note: Plan_002_evidence/2026-08-30_followup_investigation.md §2.

The plan's inference (Plan_002 §23.1): atomic_write ends in os.replace (utils.py:134), which on
Windows raises WinError 5 while any process holds the destination open -- and the watcher opens
health.json every 15 s (f10_live_monitor.py:110-113).

Test: do both PermissionError events fall inside a watcher read window?

Run:  python plans/Plan_002_evidence/analysis/analyze_perm.py
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))


def resolve_data_dir() -> Path:
    """Locate the F10B artifacts.

    Prefers $MARKET_DEPTH_DATA; else <repo>/data derived from this file's own location
    (analysis/ -> Plan_002_evidence/ -> plans/ -> <repo>); else the original scratch dir.
    """
    env = os.environ.get("MARKET_DEPTH_DATA")
    if env:
        return Path(env)
    repo_root = Path(__file__).resolve().parents[3]
    candidate = repo_root / "data"
    if (candidate / "f10b_timeline_20260828.jsonl").exists():
        return candidate
    fallback = Path.home() / "AppData" / "Local" / "Temp" / "mdr_analysis"
    if (fallback / "f10b_timeline_20260828.jsonl").exists():
        return fallback
    raise SystemExit(
        "Cannot locate the F10B artifacts. Set MARKET_DEPTH_DATA to the directory holding "
        "f10b_timeline_20260828.jsonl and f10b_recorder.log."
    )


DATA = resolve_data_dir()
TIMELINE = DATA / "f10b_timeline_20260828.jsonl"
RECORDER_LOG = DATA / "f10b_recorder.log"


def load_timeline():
    metas, samples = [], []
    with open(TIMELINE, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            (metas if o.get("record") == "meta" else samples).append(o)
    return metas, samples


def fmt(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, IST).strftime("%H:%M:%S.%f")[:-3]


def main() -> None:
    print(f"data dir: {DATA}\n")
    metas, samples = load_timeline()
    print(f"timeline: {len(metas)} meta rows, {len(samples)} non-meta rows\n")

    print("=== watcher sessions (meta rows) ===")
    for m in metas:
        st = datetime.fromisoformat(m["started"])
        print(f"  started {st.astimezone(IST).strftime('%H:%M:%S')} IST   "
              f"interval={m['interval']}s  sustain={m['sustain']}")

    ats = [s["at"] for s in samples]
    print(f"\nsample span: {fmt(min(ats))} .. {fmt(max(ats))} IST")
    gaps = [(ats[i + 1] - ats[i], ats[i], ats[i + 1]) for i in range(len(ats) - 1)]
    gaps.sort(reverse=True)
    print("largest sample gaps (s, from -> to):")
    for g, a, b in gaps[:5]:
        print(f"  {g:8.1f}s  {fmt(a)} -> {fmt(b)}")

    # --- the two PermissionError events, from f10b_recorder.log lines 1570 and 9004 -------------
    events = [
        ("event 1", "2026-08-28 11:10:03,162", 1570),
        ("event 2", "2026-08-28 15:24:50,126", 9004),
    ]

    print("\n" + "=" * 78)
    for label, stamp, lineno in events:
        dt_ist = datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S,%f").replace(tzinfo=IST)
        epoch = dt_ist.timestamp()
        print(f"\n{label}: {stamp} IST  (recorder log line {lineno})")

        before = [a for a in ats if a <= epoch]
        after = [a for a in ats if a > epoch]
        if before:
            print(f"  nearest watcher sample BEFORE : {fmt(before[-1])}  ({-1*(epoch-before[-1]):+.3f}s)")
        else:
            print("  nearest watcher sample BEFORE : none -- event precedes all samples")
        if after:
            print(f"  nearest watcher sample AFTER  : {fmt(after[0])}  ({after[0]-epoch:+.3f}s)")
        else:
            print("  nearest watcher sample AFTER  : none -- event is after the last sample")

        print("  samples within +/-20 s:")
        for a in ats:
            if abs(a - epoch) <= 20:
                print(f"      {fmt(a)}  ({a-epoch:+.2f}s)")

    # --- log context ---------------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("recorder-log context around each event\n")
    with open(RECORDER_LOG, encoding="utf-8", errors="replace") as fh:
        loglines = fh.read().splitlines()
    for label, stamp, lineno in events:
        print(f"--- {label} (line {lineno}) ---")
        for i in range(max(0, lineno - 1 - 6), min(len(loglines), lineno - 1 + 4)):
            print(f"  {i+1}: {loglines[i][:190]}")
        print()


if __name__ == "__main__":
    main()
