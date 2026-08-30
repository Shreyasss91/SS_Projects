"""Confirm the mechanism: delivering_legs is sticky (cumulative packets observed per claimed leg)
and resets when a reconnect discards the adapter's local knowledge.

Evidence note: Plan_002_evidence/2026-08-30_followup_investigation.md §3.3-§3.5.

If that holds, `delivering_legs` measures MARKET LIQUIDITY across the 15 premium strikes -- how many
of them have ticked at least once -- and NOT whether the framework allocated 15 slots.

Run:  python plans/Plan_002_evidence/analysis/verify_mechanism.py
"""
from __future__ import annotations

import json
import os
import re
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
samples = sorted((r for r in rows if r.get("record") == "sample"), key=lambda s: s["at"])

print(f"data dir: {DATA}")


def fmt(e):
    return datetime.fromtimestamp(e, IST).strftime("%H:%M:%S")


# --- every run, unfiltered -------------------------------------------------------------------------
print("\n=== every delivering_legs run (unfiltered) ===")
runs = []
cur, start, n = None, None, 0
for s in samples:
    v = s.get("delivering_legs")
    if v != cur:
        if cur is not None:
            runs.append((cur, start, s["at"], n))
        cur, start, n = v, s["at"], 0
    n += 1
runs.append((cur, start, samples[-1]["at"], n))
for v, a, b, n in runs:
    print(f"  {v:>3} legs  {fmt(a)} -> {fmt(b)}  {(b-a)/60:6.2f} min  ({n} samples)")
print()

# --- reconnects from the recorder log ---------------------------------------------------------------
with open(DATA / "f10b_recorder.log", encoding="utf-8", errors="replace") as fh:
    log = fh.read().splitlines()

RECONN = re.compile(r"^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}),(\d{3}).*(?:feed disconnected|reissued \d+ leg)")
reconns = []
for l in log:
    m = RECONN.match(l)
    if m:
        reconns.append((m.group(2), m.group(1), l))
print(f"=== {len(reconns)} reconnect/reissue log lines ===")


def secs(hms):
    h, m, s = (int(x) for x in hms.split(":"))
    return h * 3600 + m * 60 + s


seen = set()
for t, d, l in reconns:
    if t in seen:
        continue
    seen.add(t)
    kind = "DISCONNECT" if "feed disconnected" in l else "REISSUE  "
    print(f"  {kind} {t}")

# --- do the drops in delivering_legs line up with reconnects? ----------------------------------------
print("\n=== decreases in delivering_legs vs nearest reconnect ===")
recon_secs = sorted(secs(t) for t in seen)
for i in range(1, len(runs)):
    prev_v, _, b, _ = runs[i - 1]
    new_v, a, _, _ = runs[i]
    if new_v >= prev_v:
        continue
    target = secs(datetime.fromtimestamp(a, IST).strftime("%H:%M:%S"))
    if recon_secs:
        near = min(recon_secs, key=lambda r: abs(r - target))
        near_hms = f"{near // 3600:02d}:{near // 60 % 60:02d}:{near % 60:02d}"
        print(f"  DROP {prev_v:>2} -> {new_v:<2} at {fmt(a)}   "
              f"nearest reconnect {near_hms}  ({target - near:+d}s)")
    else:
        print(f"  DROP {prev_v:>2} -> {new_v:<2} at {fmt(a)}   (no reconnect logged)")

print("\n=== session context ===")
print("  market session window from log: 09:15..15:30 (teardown +5 min)")
print(f"  first sample {fmt(samples[0]['at'])}   last sample {fmt(samples[-1]['at'])}")
full = [s for s in samples if s.get("delivering_legs") == 15]
if full:
    print(f"  15-leg window: {fmt(full[0]['at'])} .. {fmt(full[-1]['at'])}  "
          f"({(full[-1]['at']-full[0]['at'])/60:.1f} min, {len(full)} samples)")
print("  D18 measurement window per the plan: 13:56:29 .. 14:36:32")
