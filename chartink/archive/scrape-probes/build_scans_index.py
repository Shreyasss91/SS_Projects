"""
Build chartink/scans_url_index.md from the authenticated scan dashboard.

Steps:
1. Read Chrome cookies for chartink.com (Chrome must NOT be locking Cookies DB).
2. Fetch pages 1..10 with per_page=50 via Inertia JSON.
3. Write scans_url_index.md with sl no, name, url, and folded extra details.
"""
from __future__ import annotations

import base64
import html as html_lib
import json
import re
import sqlite3
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
import win32crypt
from Cryptodome.Cipher import AES

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "_raw_dashboard"
OUT_MD = ROOT / "scans_url_index.md"
RAW.mkdir(parents=True, exist_ok=True)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)
TOTAL_EXPECTED = 478
PAGES = 10
PER_PAGE = 50


def chrome_key() -> bytes:
    local_state = (
        Path.home() / "AppData/Local/Google/Chrome/User Data/Local State"
    )
    data = json.loads(local_state.read_text(encoding="utf-8"))
    enc = base64.b64decode(data["os_crypt"]["encrypted_key"])
    assert enc[:5] == b"DPAPI"
    return win32crypt.CryptUnprotectData(enc[5:], None, None, None, 0)[1]


def decrypt_cookie(encrypted: bytes, key: bytes) -> str:
    if not encrypted:
        return ""
    if encrypted[:3] in (b"v10", b"v20"):
        nonce = encrypted[3:15]
        ct = encrypted[15:-16]
        tag = encrypted[-16:]
        return AES.new(key, AES.MODE_GCM, nonce=nonce).decrypt_and_verify(ct, tag).decode(
            "utf-8"
        )
    return win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)[1].decode(
        "utf-8"
    )


def load_cookies() -> dict[str, str]:
    src = (
        Path.home()
        / "AppData/Local/Google/Chrome/User Data/Default/Network/Cookies"
    )
    dst = Path(tempfile.mkdtemp(prefix="ck_")) / "Cookies"
    # try plain copy first
    import shutil

    last_err: Exception | None = None
    for attempt in range(5):
        try:
            shutil.copy2(src, dst)
            break
        except Exception as e:
            last_err = e
            time.sleep(0.5)
    else:
        raise RuntimeError(
            f"Cannot copy Chrome Cookies DB (is Chrome fully closed?): {last_err}"
        )

    key = chrome_key()
    con = sqlite3.connect(str(dst))
    cur = con.cursor()
    cur.execute(
        """
        SELECT name, value, encrypted_value, host_key
        FROM cookies
        WHERE host_key LIKE '%chartink%'
        """
    )
    cookies: dict[str, str] = {}
    for name, value, enc, host in cur.fetchall():
        plain = value or ""
        if not plain and enc:
            try:
                plain = decrypt_cookie(enc, key)
            except Exception as e:
                print(f"decrypt fail {name}: {e}")
                continue
        if plain:
            cookies[name] = plain
            print(f"cookie {host} {name} len={len(plain)}")
    con.close()
    if not cookies:
        raise RuntimeError("No chartink.com cookies found in Chrome Default profile")
    return cookies


def session_from_cookies(cookies: dict[str, str]) -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": UA,
            "Accept": "text/html, application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    for k, v in cookies.items():
        s.cookies.set(k, v, domain=".chartink.com")
        s.cookies.set(k, v, domain="chartink.com")
    return s


def parse_inertia_or_html(text: str, content_type: str) -> dict[str, Any]:
    if "json" in (content_type or "") or text.lstrip().startswith("{"):
        return json.loads(text)
    m = re.search(r'data-page="([^"]+)"', text)
    if not m:
        raise ValueError("No Inertia data-page found (still logged out?)")
    return json.loads(html_lib.unescape(m.group(1)))


def extract_scan_list(props: dict[str, Any]) -> tuple[list[dict], dict]:
    """Return (scans, meta) from Inertia props."""
    meta: dict[str, Any] = {}
    found: list[dict] = []

    def looks_like_scan(item: dict) -> bool:
        keys = set(item.keys())
        return bool(
            keys
            & {
                "slug",
                "name",
                "scan_name",
                "title",
                "atlas_query",
                "query",
                "screener_url",
            }
        ) or ("id" in keys and ("name" in keys or "title" in keys))

    def consider_list(items: list, path: str) -> None:
        nonlocal found
        if not items or not isinstance(items[0], dict):
            return
        if looks_like_scan(items[0]):
            print(f"  list hit at {path} len={len(items)} keys={list(items[0].keys())[:20]}")
            found = items

    def walk(obj: Any, path: str = "props") -> None:
        if found:
            return
        if isinstance(obj, dict):
            # pagination meta
            for k in ("total", "last_page", "per_page", "current_page", "from", "to"):
                if k in obj and isinstance(obj[k], (int, float)):
                    meta.setdefault(k, obj[k])
            for key in ("data", "scans", "items", "screeners", "results"):
                if key in obj and isinstance(obj[key], list):
                    consider_list(obj[key], f"{path}.{key}")
            for k, v in obj.items():
                walk(v, f"{path}.{k}")
        elif isinstance(obj, list) and obj and isinstance(obj[0], dict):
            consider_list(obj, path)

    walk(props)
    return found, meta


def fetch_all_scans(session: requests.Session) -> list[dict]:
    all_scans: list[dict] = []
    inertia_version = None

    for page in range(1, PAGES + 1):
        url = f"https://chartink.com/scan_dashboard?page={page}&per_page={PER_PAGE}"
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "X-Inertia": "true",
            "Referer": "https://chartink.com/scan_dashboard",
        }
        if inertia_version:
            headers["X-Inertia-Version"] = inertia_version

        r = session.get(url, headers=headers, timeout=60, allow_redirects=True)
        print(
            f"page {page}: status={r.status_code} url={r.url} "
            f"ct={r.headers.get('content-type')} len={len(r.text)}"
        )
        (RAW / f"dash_page_{page}.raw").write_text(r.text[:400000], encoding="utf-8")

        if "login" in r.url.lower():
            raise RuntimeError("Redirected to login — session cookie expired or missing")

        try:
            data = parse_inertia_or_html(r.text, r.headers.get("content-type", ""))
        except Exception:
            # retry without inertia headers
            r = session.get(url, timeout=60)
            data = parse_inertia_or_html(r.text, r.headers.get("content-type", ""))

        if data.get("version"):
            inertia_version = data["version"]

        print(f"  component={data.get('component')} page_url={data.get('url')}")
        props = data.get("props") or {}
        print(f"  prop keys: {list(props.keys())}")

        (RAW / f"dash_page_{page}.json").write_text(
            json.dumps(data, indent=2, default=str)[:800000], encoding="utf-8"
        )

        scans, meta = extract_scan_list(props)
        print(f"  extracted={len(scans)} meta={meta}")
        if not scans:
            # dump a small props sample for debugging
            sample = json.dumps(props, default=str)[:2000]
            print("  props sample:", sample)
            raise RuntimeError(f"No scans found on page {page}")
        all_scans.extend(scans)
        time.sleep(0.35)

    return all_scans


def normalize_scan(raw: dict, ordinal: int) -> dict[str, Any]:
    name = (
        raw.get("name")
        or raw.get("scan_name")
        or raw.get("title")
        or raw.get("scanName")
        or f"Unnamed scan {ordinal}"
    )
    slug = raw.get("slug") or raw.get("scan_slug") or raw.get("url_slug")
    scan_id = raw.get("id") or raw.get("scan_id") or raw.get("screener_id")
    url = (
        raw.get("url")
        or raw.get("scan_url")
        or raw.get("screener_url")
        or raw.get("link")
    )
    if not url:
        if slug:
            url = f"https://chartink.com/screener/{slug}"
        elif scan_id:
            url = f"https://chartink.com/screener/{scan_id}"
        else:
            url = ""

    if url and url.startswith("/"):
        url = "https://chartink.com" + url

    # fold remaining useful fields
    skip = {
        "name",
        "scan_name",
        "title",
        "scanName",
        "slug",
        "scan_slug",
        "url_slug",
        "url",
        "scan_url",
        "screener_url",
        "link",
        "atlas_json",
        "atlas_query",
        "query",
        "pivot_json",
    }
    extras: dict[str, Any] = {}
    for k, v in raw.items():
        if k in skip:
            continue
        if v is None or v == "" or v == [] or v == {}:
            continue
        # keep short/scalar-ish values
        if isinstance(v, (str, int, float, bool)):
            extras[k] = v
        elif isinstance(v, list) and len(v) <= 20 and all(
            isinstance(x, (str, int, float, bool)) for x in v
        ):
            extras[k] = v
        elif isinstance(v, dict) and len(json.dumps(v, default=str)) < 300:
            extras[k] = v
        else:
            # summarize large fields
            if isinstance(v, str) and len(v) > 200:
                extras[k] = v[:200] + "…"
            elif isinstance(v, (list, dict)):
                extras[k] = f"<{type(v).__name__} len={len(v)}>"

    # important long fields separately if present
    for long_key in ("description", "notes", "remark", "scan_description"):
        if raw.get(long_key):
            extras[long_key] = str(raw[long_key])

    return {
        "sl_no": ordinal,
        "scan_name": str(name).strip(),
        "scan_url": url,
        "scan_id": scan_id,
        "slug": slug,
        "extras": extras,
        "raw_keys": sorted(raw.keys()),
    }


def md_escape(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ").strip()


def fold_extras(extras: dict[str, Any]) -> str:
    if not extras:
        return ""
    parts = []
    for k, v in extras.items():
        if isinstance(v, (list, dict)):
            v = json.dumps(v, ensure_ascii=False, default=str)
        parts.append(f"{k}: {v}")
    return "; ".join(parts)


def write_markdown(scans: list[dict[str, Any]], raw_count: int) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = []
    lines.append("# Chartink Scans URL Index")
    lines.append("")
    lines.append(f"- **Source:** `https://chartink.com/scan_dashboard?page=1..{PAGES}&per_page={PER_PAGE}`")
    lines.append(f"- **Captured at:** {now}")
    lines.append(f"- **Dashboard reported total (user):** {TOTAL_EXPECTED}")
    lines.append(f"- **Entries in this index:** {len(scans)}")
    lines.append(f"- **Raw objects fetched:** {raw_count}")
    if len(scans) != TOTAL_EXPECTED:
        lines.append(
            f"- **Note:** Count differs from expected {TOTAL_EXPECTED}; "
            "reconcile against the live dashboard."
        )
    lines.append("")
    lines.append("## Index")
    lines.append("")
    lines.append("| Sl No | Scan name | Scan URL | Other details |")
    lines.append("|---:|---|---|---|")

    for s in scans:
        extras = fold_extras(s["extras"])
        # always fold id/slug into other details if not empty
        base_bits = []
        if s.get("scan_id") is not None:
            base_bits.append(f"id: {s['scan_id']}")
        if s.get("slug"):
            base_bits.append(f"slug: {s['slug']}")
        if extras:
            base_bits.append(extras)
        other = "; ".join(base_bits)
        # collapse for table readability; full extras also in details section
        if len(other) > 180:
            other = other[:177] + "…"
        lines.append(
            f"| {s['sl_no']} | {md_escape(s['scan_name'])} | {s['scan_url']} | {md_escape(other)} |"
        )

    lines.append("")
    lines.append("## Folded details (per scan)")
    lines.append("")
    lines.append(
        "Each entry below keeps fields returned by the dashboard payload "
        "(ids, timestamps, flags, counts, etc.). Large query bodies are omitted here."
    )
    lines.append("")

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

    lines.append("## Reconciliation")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|---|---:|")
    lines.append(f"| Expected (user) | {TOTAL_EXPECTED} |")
    lines.append(f"| Indexed | {len(scans)} |")
    lines.append(f"| Pages requested | {PAGES} × {PER_PAGE} |")
    lines.append("")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Wrote", OUT_MD, "bytes", OUT_MD.stat().st_size)


def main() -> None:
    print("Loading Chrome cookies for chartink.com ...")
    cookies = load_cookies()
    print("Cookie names:", sorted(cookies.keys()))
    session = session_from_cookies(cookies)
    raw_scans = fetch_all_scans(session)
    print("Raw scan objects:", len(raw_scans))
    (RAW / "all_scans_raw.json").write_text(
        json.dumps(raw_scans, indent=2, default=str), encoding="utf-8"
    )

    # dedupe by id/slug/url while preserving order
    seen: set[str] = set()
    normalized: list[dict] = []
    for raw in raw_scans:
        key = str(
            raw.get("id")
            or raw.get("slug")
            or raw.get("url")
            or raw.get("name")
            or id(raw)
        )
        if key in seen:
            continue
        seen.add(key)
        normalized.append(normalize_scan(raw, len(normalized) + 1))

    write_markdown(normalized, len(raw_scans))
    print("DONE", len(normalized), "scans")


if __name__ == "__main__":
    main()
