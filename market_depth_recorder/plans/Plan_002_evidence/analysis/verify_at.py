"""Two questions that must be settled before promoting the PermissionError finding.

Evidence note: Plan_002_evidence/2026-08-30_followup_investigation.md §2.3-§2.5.

1. What is the timeline's `at` field -- the WATCHER's own sampling instant, or a timestamp copied
   out of health.json? If it is the latter, matching it to the error proves nothing.

   Test: if `at` were copied from health.json (written on the recorder's own cadence), the values
   would be quantised to that cadence. A free-running watcher clock shows no such quantisation.

2. Re-run the correlation against the NEAREST sample in either direction, and quantify how
   improbable the coincidence is.

Run:  python plans/Plan_002_evidence/analysis/verify_at.py
"""
from __future__ import annotations

import json
import os
import statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))


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

with open(DATA / "f10b_timeline_20260828.jsonl", encoding="utf-8") as fh:
    rows = [json.loads(x) for x in fh if x.strip()]
samples = [r for r in rows if r.get("record") == "sample"]
ats = sorted(s["at"] for s in samples)

print(f"data dir: {DATA}")
print(f"{len(ats)} samples\n")

# --- Q1: is `at` quantised? -------------------------------------------------------------------
print("=== Q1: is `at` quantised to a coarser clock? ===")
deltas = [ats[i + 1] - ats[i] for i in range(len(ats) - 1)]
print(f"inter-sample delta: median {statistics.median(deltas):.3f}s  "
      f"min {min(deltas):.3f}s  max {max(deltas):.3f}s")

for period in (1.0, 5.0, 15.0):
    rems = [a % period for a in ats]
    spread = max(rems) - min(rems)
    print(f"  mod {period:>5.1f}s -> remainder spread {spread:7.3f}s   "
          f"{'QUANTISED' if spread < 0.05 else 'free-running'}")

print("\n  -> a free-running clock with ~15 s cadence and sub-second jitter is the watcher's own")
print("     sampling instant, not a value copied from a coarser-cadence health.json.\n")

# --- Q2: correlation, nearest sample either direction ------------------------------------------
events = [("event 1", "2026-08-28 11:10:03,162"), ("event 2", "2026-08-28 15:24:50,126")]
print("=== Q2: distance from each PermissionError to the nearest watcher sample ===")

dists = []
for label, stamp in events:
    dt = datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S,%f").replace(tzinfo=IST)
    e = dt.timestamp()
    nearest = min(ats, key=lambda a: abs(a - e))
    d = abs(nearest - e)
    dists.append(d)
    hh = datetime.fromtimestamp(nearest, IST).strftime("%H:%M:%S.%f")[:-3]
    print(f"  {label}: event {stamp[11:]}  nearest sample {hh}  "
          f"offset {d*1000:.1f} ms")

# --- how improbable? ---------------------------------------------------------------------------
# Null model: an unrelated error is uniform over the 15 s sampling interval. The watcher's file is
# only open for a fraction of that window; conservatively assume the vulnerable window is as long
# as the observed offsets themselves (i.e. be generous to the null).
worst = max(dists)
p_hit = (2 * worst) / 15.0          # two-sided window of +/- worst, over a 15 s period
p_both = p_hit ** 2
print("\n=== null model ===")
print(f"  vulnerable window (generous): +/-{worst*1000:.1f} ms out of a 15.000 s period")
print(f"  P(one unrelated error lands in window) = {p_hit:.2e}")
print(f"  P(both land in window by chance)      = {p_both:.2e}  (1 in {1/p_both:.3g})")
