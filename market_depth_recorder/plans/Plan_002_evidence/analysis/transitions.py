"""delivering_legs flips 5 -> 15 at 13:56:29 and 15 -> 5 at 14:36:47. What happened at those instants?

Evidence note: Plan_002_evidence/2026-08-30_followup_investigation.md §3.3.

Also shows the 14:14 reconnect region, which is the one the plan cites as resolving UNKNOWN #1.

Run:  python plans/Plan_002_evidence/analysis/transitions.py
"""
from __future__ import annotations

import bisect
import os
import re
from pathlib import Path


def resolve_data_dir() -> Path:
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

with open(DATA / "f10b_recorder.log", encoding="utf-8", errors="replace") as fh:
    lines = fh.read().splitlines()

TS = re.compile(r"^\d{4}-\d{2}-\d{2} (\d{2}):(\d{2}):(\d{2}),(\d{3})")


def to_sec(h, m, s):
    return h * 3600 + m * 60 + s


stamps = []
for l in lines:
    m = TS.match(l)
    stamps.append(to_sec(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None)

# forward-fill for continuation lines (tracebacks)
last = 0
filled = []
for s in stamps:
    if s is None:
        filled.append(last)
    else:
        last = s
        filled.append(s)
stamps = filled


def hms(hhmmss: str) -> int:
    h, m, s = (int(x) for x in hhmmss.split(":"))
    return to_sec(h, m, s)


def show(label: str, hhmmss: str, before: int = 18, after: int = 10) -> None:
    target = hms(hhmmss)
    i = bisect.bisect_left(stamps, target)
    print("=" * 104)
    print(f"{label}   target {hhmmss}")
    print("=" * 104)
    lo, hi = max(0, i - before), min(len(lines), i + after)
    for j in range(lo, hi):
        mark = ">>" if stamps[j] == target else "  "
        print(f"{mark} {lines[j][:198]}")
    print()


print(f"data dir: {DATA}\n")
show("TRANSITION 1: delivering_legs 5 -> 15", "13:56:29")
show("TRANSITION 2: delivering_legs 15 -> 5", "14:36:47")
show("reconnect region (14:14)", "14:14:15", before=8, after=14)
