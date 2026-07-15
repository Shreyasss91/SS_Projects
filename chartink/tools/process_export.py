"""Build scans_url_index.md from exported chartink_dashboard_pages.json."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# chartink/ is parent of tools/
ROOT = Path(__file__).resolve().parent.parent
EXPORTS = ROOT / "data" / "exports"
OUT_MD = ROOT / "scans_url_index.md"
TOTAL_EXPECTED = 478
PAGES = 10
PER_PAGE = 50


def find_export() -> Path:
    candidates = [
        EXPORTS / "chartink_dashboard_pages.json",
        EXPORTS / "chartink_dashboard_pages.from_raw_dashboard.json",
        ROOT / "chartink_dashboard_pages.json",
        Path.home() / "Downloads" / "chartink_dashboard_pages.json",
        Path.home() / "Desktop" / "chartink_dashboard_pages.json",
    ]
    # also newest matching downloads
    dl = Path.home() / "Downloads"
    if dl.exists():
        for p in sorted(
            dl.glob("chartink_dashboard_pages*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        ):
            candidates.insert(0, p)
    if len(sys.argv) > 1:
        candidates.insert(0, Path(sys.argv[1]))
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(
        "Could not find chartink_dashboard_pages.json. "
        "Pass path as argv, or place under chartink/data/exports/ or Downloads."
    )


def extract_scans(props: dict) -> tuple[list[dict], dict]:
    meta: dict = {}
    found: list[dict] = []

    def looks(item: dict) -> bool:
        keys = set(item.keys())
        return bool(
            keys & {"slug", "name", "scan_name", "title", "atlas_query", "screener_url"}
        ) or ("id" in keys and ("name" in keys or "title" in keys))

    def consider(items: list, path: str) -> None:
        nonlocal found
        if found or not items or not isinstance(items[0], dict):
            return
        if looks(items[0]):
            print(f"list@{path} n={len(items)} keys={list(items[0].keys())[:30]}")
            found = items

    def walk(obj: Any, path: str = "props") -> None:
        if found:
            return
        if isinstance(obj, dict):
            for k in ("total", "last_page", "per_page", "current_page", "from", "to"):
                if k in obj and isinstance(obj[k], (int, float)):
                    meta.setdefault(k, obj[k])
            for key in ("data", "scans", "items", "screeners", "results"):
                if isinstance(obj.get(key), list):
                    consider(obj[key], f"{path}.{key}")
            for k, v in obj.items():
                walk(v, f"{path}.{k}")
        elif isinstance(obj, list) and obj and isinstance(obj[0], dict):
            consider(obj, path)

    walk(props)
    return found, meta


def normalize(raw: dict, n: int) -> dict:
    name = raw.get("name") or raw.get("scan_name") or raw.get("title") or f"Unnamed {n}"
    slug = raw.get("slug") or raw.get("scan_slug")
    scan_id = raw.get("id") or raw.get("scan_id")
    url = raw.get("url") or raw.get("scan_url") or raw.get("screener_url") or raw.get("link")
    if not url:
        if slug:
            url = f"https://chartink.com/screener/{slug}"
        elif scan_id:
            url = f"https://chartink.com/screener/{scan_id}"
        else:
            url = ""
    if isinstance(url, str) and url.startswith("/"):
        url = "https://chartink.com" + url
    skip = {
        "name", "scan_name", "title", "slug", "scan_slug", "url", "scan_url",
        "screener_url", "link", "atlas_json", "atlas_query", "query", "pivot_json",
        "id", "scan_id",  # already emitted as primary id/slug fields
    }
    extras = {}
    for k, v in raw.items():
        if k in skip or v in (None, "", [], {}):
            continue
        if isinstance(v, (str, int, float, bool)):
            extras[k] = v
        elif isinstance(v, list) and len(v) <= 30 and all(
            isinstance(x, (str, int, float, bool)) for x in v
        ):
            extras[k] = v
        elif isinstance(v, dict) and len(json.dumps(v, default=str)) < 400:
            extras[k] = v
        else:
            extras[k] = f"<{type(v).__name__} len={len(v) if hasattr(v,'__len__') else '?'}>"
    return {
        "sl_no": n,
        "scan_name": str(name).strip(),
        "scan_url": url,
        "scan_id": scan_id,
        "slug": slug,
        "extras": extras,
    }


def md_escape(s: str) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ").strip()


def write_md(scans: list[dict], raw_n: int, source: Path) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Chartink Scans URL Index",
        "",
        f"- **Source:** `https://chartink.com/scan_dashboard?page=1..{PAGES}&per_page={PER_PAGE}`",
        f"- **Export file:** `{source}`",
        f"- **Captured at:** {now}",
        f"- **Dashboard reported total (user):** {TOTAL_EXPECTED}",
        f"- **Entries in this index:** {len(scans)}",
        f"- **Raw objects fetched:** {raw_n}",
    ]
    if len(scans) != TOTAL_EXPECTED:
        lines.append(f"- **Note:** Indexed count differs from expected {TOTAL_EXPECTED}.")
    lines += [
        "",
        "## Index",
        "",
        "| Sl No | Scan name | Scan URL | Other details |",
        "|---:|---|---|---|",
    ]
    for s in scans:
        bits = []
        if s.get("scan_id") is not None:
            bits.append(f"id: {s['scan_id']}")
        if s.get("slug"):
            bits.append(f"slug: {s['slug']}")
        for k, v in s["extras"].items():
            if k in ("id", "scan_id", "slug"):
                continue
            if isinstance(v, (list, dict)):
                v = json.dumps(v, ensure_ascii=False, default=str)
            bits.append(f"{k}: {v}")
        other = "; ".join(bits)
        if len(other) > 220:
            other = other[:217] + "…"
        lines.append(
            f"| {s['sl_no']} | {md_escape(s['scan_name'])} | {s['scan_url']} | {md_escape(other)} |"
        )
    lines += [
        "",
        "## Folded details (per scan)",
        "",
        "Fields returned by the dashboard payload (ids, flags, timestamps, etc.). "
        "Large query bodies are omitted.",
        "",
    ]
    for s in scans:
        lines.append(f"### {s['sl_no']}. {s['scan_name']}")
        lines.append("")
        lines.append(f"- **Scan URL:** {s['scan_url'] or '_(missing)_'}")
        if s.get("scan_id") is not None:
            lines.append(f"- **ID:** `{s['scan_id']}`")
        if s.get("slug"):
            lines.append(f"- **Slug:** `{s['slug']}`")
        if s["extras"]:
            lines.append("- **Other fields:**")
            for k, v in s["extras"].items():
                if isinstance(v, (list, dict)):
                    v = json.dumps(v, ensure_ascii=False, default=str)
                lines.append(f"  - `{k}`: {v}")
        lines.append("")
    lines += [
        "## Reconciliation",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Expected (user) | {TOTAL_EXPECTED} |",
        f"| Indexed | {len(scans)} |",
        f"| Pages requested | {PAGES} × {PER_PAGE} |",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print("Wrote", OUT_MD, OUT_MD.stat().st_size)


def main() -> None:
    path = find_export()
    print("Using export", path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        data = [data]
    raw_scans: list[dict] = []
    for i, page_data in enumerate(data, 1):
        props = page_data.get("props") or page_data
        print(f"page blob {i}: component={page_data.get('component')} keys={list(props.keys())[:20]}")
        scans, meta = extract_scans(props)
        print(f"  scans={len(scans)} meta={meta}")
        raw_scans.extend(scans)

    EXPORTS.mkdir(parents=True, exist_ok=True)
    (EXPORTS / "all_scans_raw.json").write_text(
        json.dumps(raw_scans, indent=2, default=str), encoding="utf-8"
    )
    # keep a copy of the page export under data/exports if processed from elsewhere
    target = EXPORTS / "chartink_dashboard_pages.json"
    if path.resolve() != target.resolve() and not target.exists():
        target.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

    seen: set[str] = set()
    scans: list[dict] = []
    for raw in raw_scans:
        key = str(raw.get("id") or raw.get("slug") or raw.get("name") or id(raw))
        if key in seen:
            continue
        seen.add(key)
        scans.append(normalize(raw, len(scans) + 1))
    write_md(scans, len(raw_scans), path)
    print("DONE", len(scans))


if __name__ == "__main__":
    main()
