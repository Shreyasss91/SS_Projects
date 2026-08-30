"""Why did the 15-leg condition hold for only ~40 of 361 minutes?

Evidence note: Plan_002_evidence/2026-08-30_followup_investigation.md §3.

Key field discovered in the timeline: `delivering_legs` sits alongside `premium_legs`. The first
sample shows premium_legs=15 but delivering_legs=5. So the plan's "15-leg condition" is NOT
"the framework asked for 15" (that was nearly always true) but "15 legs were actually DELIVERING".

This runs entirely on the timeline -- no 329 MB raw-log replay needed.

Run:  python plans/Plan_002_evidence/analysis/analyze_15leg.py
"""
from __future__ import annotations

import json
import os
from collections import Counter
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
samples.sort(key=lambda s: s["at"])
print(f"data dir: {DATA}")
print(f"{len(samples)} samples\n")


def fmt(e):
    return datetime.fromtimestamp(e, IST).strftime("%H:%M:%S")


# --- distributions -----------------------------------------------------------------------------
for key in ("premium_legs", "delivering_legs", "desired_legs", "active_contracts"):
    vals = [s.get(key) for s in samples if s.get(key) is not None]
    c = Counter(vals)
    print(f"{key}: {len(vals)} samples, distinct values {len(c)}")
    print("   top:", ", ".join(f"{k}x{n}" for k, n in c.most_common(6)))
print()

# --- the 40-of-361 claim, recomputed ------------------------------------------------------------
minutes: dict[str, list[int]] = {}
for s in samples:
    m = datetime.fromtimestamp(s["at"], IST).strftime("%H:%M")
    minutes.setdefault(m, []).append(s.get("delivering_legs") or 0)

all_hold = [m for m, v in minutes.items() if v and all(x == 15 for x in v)]
any_hold = [m for m, v in minutes.items() if any(x == 15 for x in v)]
print(f"distinct minutes observed      : {len(minutes)}")
print(f"minutes where ALL samples == 15 : {len(all_hold)}")
print(f"minutes where ANY sample  == 15 : {len(any_hold)}")
print(f"minutes where NO  sample  == 15 : {len(minutes) - len(any_hold)}")
print()

# --- what does delivering_legs look like over the session? ---------------------------------------
print("=== delivering_legs: run-length encoding over the session ===")
runs = []
cur_val, cur_start, cur_n = None, None, 0
for s in samples:
    v = s.get("delivering_legs")
    if v != cur_val:
        if cur_val is not None:
            runs.append((cur_val, cur_start, s["at"], cur_n))
        cur_val, cur_start, cur_n = v, s["at"], 0
    cur_n += 1
if cur_val is not None:
    runs.append((cur_val, cur_start, samples[-1]["at"], cur_n))

for v, a, b, n in runs:
    dur = (b - a) / 60.0
    if dur >= 0.7 or v == 15:
        print(f"  {v:>3} legs  {fmt(a)} -> {fmt(b)}  {dur:6.1f} min  ({n} samples)")
print()

# --- is it the underlying's depth? ---------------------------------------------------------------
print("=== actual_depth per underlying: run-length encoding ===")
depth_runs = []
cur_key, cur_start, cur_n = None, None, 0
for s in samples:
    k = json.dumps(s.get("actual_depth") or {}, sort_keys=True)
    if k != cur_key:
        if cur_key is not None:
            depth_runs.append((cur_key, cur_start, s["at"], cur_n))
        cur_key, cur_start, cur_n = k, s["at"], 0
    cur_n += 1
if cur_key is not None:
    depth_runs.append((cur_key, cur_start, samples[-1]["at"], cur_n))

for k, a, b, n in depth_runs:
    dur = (b - a) / 60.0
    if dur >= 0.7:
        print(f"  {k}  {fmt(a)} -> {fmt(b)}  {dur:6.1f} min")
print()

# --- cross-tab: delivering_legs vs premium_legs ---------------------------------------------------
print("=== cross-tab: delivering_legs (rows) x premium_legs (cols) ===")
ct = Counter((s.get("delivering_legs"), s.get("premium_legs")) for s in samples)
prem_vals = sorted({p for _, p in ct})
print("  dl\\pl " + "".join(f"{p:>7}" for p in prem_vals))
for d in sorted({d for d, _ in ct}):
    print(f"  {d:>5} " + "".join(f"{ct.get((d, p), 0):>7}" for p in prem_vals))
