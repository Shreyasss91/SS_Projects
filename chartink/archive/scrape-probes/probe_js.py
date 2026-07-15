"""Search Chartink JS for scan_dashboard data loading."""
from __future__ import annotations

import re
from pathlib import Path

RAW = Path(__file__).resolve().parent / "_raw_dashboard"
js = (RAW / "index-6c93b0f2.js").read_text(encoding="utf-8", errors="replace")

needles = [
    "scan_dashboard",
    "ScanDashboard",
    "scanDashboard",
    "/scans",
    "per_page",
    "screener/",
    "scan_name",
    "scanName",
    "my scans",
    "My Scans",
    "totalScans",
    "total_scans",
    "scan_url",
    "scanUrl",
]

for n in needles:
    idxs = [m.start() for m in re.finditer(re.escape(n), js, flags=re.I)]
    print(f"\n=== {n!r} count={len(idxs)} ===")
    for i in idxs[:8]:
        start = max(0, i - 200)
        end = min(len(js), i + 300)
        snippet = js[start:end].replace("\n", " ")
        print(snippet)
        print("---")
