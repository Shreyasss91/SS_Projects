"""Extract Chartink screener URLs from Chrome History."""
from __future__ import annotations

import re
import shutil
import sqlite3
import tempfile
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "_raw_dashboard"
RAW.mkdir(parents=True, exist_ok=True)


def main() -> None:
    src = (
        Path.home()
        / "AppData/Local/Google/Chrome/User Data/Default/History"
    )
    dst = Path(tempfile.mkdtemp()) / "History"
    shutil.copy2(src, dst)
    print("copied history", dst.stat().st_size)

    con = sqlite3.connect(str(dst))
    cur = con.cursor()

    cur.execute(
        """
        SELECT url, title, visit_count, last_visit_time
        FROM urls
        WHERE url LIKE '%chartink.com%'
        ORDER BY last_visit_time DESC
        LIMIT 30
        """
    )
    print("\n=== recent chartink ===")
    for url, title, vc, _ in cur.fetchall():
        print(vc, (title or "")[:60], url[:140])

    cur.execute(
        """
        SELECT url, title, visit_count, last_visit_time
        FROM urls
        WHERE url LIKE '%chartink.com/screener/%'
           OR url LIKE '%chartink.com/stocks/%'
           OR url LIKE '%chartink.com/scan/%'
        ORDER BY last_visit_time DESC
        """
    )
    rows = cur.fetchall()
    print("\nTOTAL candidate scan urls", len(rows))

    # dedupe by canonical path
    by_path: dict[str, dict] = {}
    for url, title, vc, lvt in rows:
        # strip query/fragment
        p = urlparse(url)
        path = p.path.rstrip("/")
        if not path:
            continue
        # normalize
        key = path.lower()
        prev = by_path.get(key)
        if not prev or (lvt or 0) > (prev.get("last_visit_time") or 0):
            by_path[key] = {
                "url": f"https://chartink.com{path}",
                "title": title or "",
                "visit_count": vc or 0,
                "last_visit_time": lvt or 0,
                "path": path,
            }
        else:
            by_path[key]["visit_count"] = max(
                by_path[key]["visit_count"], vc or 0
            )

    items = sorted(
        by_path.values(),
        key=lambda x: (-x["visit_count"], x["url"]),
    )
    print("UNIQUE paths", len(items))
    for it in items[:40]:
        print(it["visit_count"], it["title"][:70], it["url"])

    out = RAW / "history_screeners.json"
    import json

    out.write_text(json.dumps(items, indent=2), encoding="utf-8")
    print("wrote", out)

    # also search typed_url / keyword_search_terms if useful
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    print("tables", [r[0] for r in cur.fetchall()])
    con.close()


if __name__ == "__main__":
    main()
