"""Scrape Chartink scan dashboard pages for inventory."""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)
OUT = Path(__file__).resolve().parent / "_raw_dashboard"


def fetch(url: str) -> tuple[int, str, dict]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/json,*/*",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            body = r.read().decode("utf-8", errors="replace")
            headers = {k.lower(): v for k, v in r.headers.items()}
            return r.status, body, headers
    except Exception as e:
        return 0, str(e), {}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    url = "https://chartink.com/scan_dashboard?page=1&per_page=50"
    status, body, headers = fetch(url)
    print("status", status, "len", len(body))
    print("content-type", headers.get("content-type"))
    (OUT / "page1.html").write_text(body, encoding="utf-8")

    # Patterns of interest
    patterns = [
        r'href=["\']([^"\']+)["\']',
        r'https?://chartink\.com/[^\s"\'<>]+',
        r'/screener/[^\s"\'<>]+',
        r'/scan[^\s"\'<>]*',
        r'api/[^\s"\'<>]+',
        r'"slug"\s*:\s*"([^"]+)"',
        r'"name"\s*:\s*"([^"]+)"',
        r'"title"\s*:\s*"([^"]+)"',
        r'data-[a-zA-Z-]+=["\'][^"\']+["\']',
        r'window\.[A-Za-z_]+\s*=\s*\{',
        r'__NEXT_DATA__',
        r'Laravel',
        r'login',
        r'csrf',
    ]
    for pat in patterns:
        matches = re.findall(pat, body, flags=re.I)
        print(f"\n=== {pat} count={len(matches)} ===")
        for m in matches[:25]:
            s = m if isinstance(m, str) else str(m)
            if len(s) > 200:
                s = s[:200] + "..."
            print(s)

    # Try common JSON endpoints
    candidates = [
        "https://chartink.com/api/scan_dashboard?page=1&per_page=50",
        "https://chartink.com/screener/process",
        "https://chartink.com/api/scans?page=1&per_page=50",
        "https://chartink.com/dashboard/scans?page=1&per_page=50",
        "https://chartink.com/scan_dashboard.json?page=1&per_page=50",
        "https://chartink.com/screener/list?page=1&per_page=50",
        "https://chartink.com/user/scans?page=1&per_page=50",
        "https://chartink.com/api/v1/scans?page=1&per_page=50",
    ]
    for c in candidates:
        st, b, h = fetch(c)
        print(f"\nCANDIDATE {c} -> {st} len={len(b)} ct={h.get('content-type')}")
        preview = b[:300].replace("\n", " ")
        print(preview)

    # Look at script srcs for app bundles that may contain routes
    srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', body, flags=re.I)
    print("\n=== script srcs ===")
    for s in srcs:
        print(s)


if __name__ == "__main__":
    main()
