"""
Open Chrome (debug profile). User logs into Chartink once.
Then scrape scan_dashboard pages 1-10 and write scans_url_index.md.
"""
from __future__ import annotations

import html as html_lib
import json
import re
import subprocess
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "_raw_dashboard"
OUT_MD = ROOT / "scans_url_index.md"
RAW.mkdir(parents=True, exist_ok=True)

CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
DEBUG_PORT = 9333
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/150.0.0.0 Safari/537.36"
)
TOTAL_EXPECTED = 478
PAGES = 10
PER_PAGE = 50
LOGIN_WAIT_SEC = 300  # 5 minutes for user login


def kill_chrome() -> None:
    subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], capture_output=True)
    time.sleep(1.5)


def wait_port(port: int, timeout: float = 40.0) -> dict:
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/json/version", timeout=1.5
            ) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            last = e
            time.sleep(0.4)
    raise RuntimeError(f"port {port} not ready: {last}")


def launch(user_data: Path) -> subprocess.Popen:
    args = [
        str(CHROME),
        f"--remote-debugging-port={DEBUG_PORT}",
        f"--user-data-dir={user_data}",
        "--no-first-run",
        "--no-default-browser-check",
        "https://chartink.com/login",
    ]
    return subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def attach_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{DEBUG_PORT}")
    return webdriver.Chrome(options=options)


def _is_chartink_app_url(url: str) -> bool:
    """True only for chartink.com app pages (not Google OAuth URLs that mention chartink)."""
    from urllib.parse import urlparse

    try:
        p = urlparse(url)
    except Exception:
        return False
    host = (p.netloc or "").lower()
    if host not in ("chartink.com", "www.chartink.com"):
        return False
    path = (p.path or "").lower()
    if path.startswith("/login") or path.startswith("/auth/"):
        return False
    return True


def wait_until_logged_in(driver, timeout: float = LOGIN_WAIT_SEC) -> None:
    print(
        "\n*** ACTION REQUIRED ***\n"
        "A Chrome window opened at Chartink login (Google OAuth).\n"
        "Please complete login until you land on Chartink (any page except /login).\n"
        f"Waiting up to {int(timeout)} seconds...\n"
    )
    deadline = time.time() + timeout
    last_print = ""
    while time.time() < deadline:
        url = driver.current_url or ""
        title = driver.title or ""
        msg = f"  waiting... host/path ok={_is_chartink_app_url(url)} title={title[:50]} url={url[:120]}"
        if msg != last_print:
            print(msg)
            last_print = msg
        if _is_chartink_app_url(url):
            driver.get("https://chartink.com/scan_dashboard?page=1&per_page=50")
            time.sleep(3)
            cur = driver.current_url or ""
            if _is_chartink_app_url(cur) and "scan_dashboard" in cur:
                # also require inertia data-page not login
                src = driver.page_source or ""
                if "Auth/Login" in src or 'component":"Auth' in src:
                    print("  still login component in page; continue waiting")
                else:
                    print("Logged in. Dashboard URL:", cur)
                    return
        time.sleep(2)
    raise TimeoutError("Timed out waiting for Chartink login")


def cookies_from_driver(driver) -> dict[str, str]:
    out = {}
    for c in driver.get_cookies():
        if "chartink" in (c.get("domain") or ""):
            out[c["name"]] = c["value"]
            print(f"cookie {c['name']} len={len(c['value'])}")
    return out


def parse_payload(text: str, content_type: str) -> dict:
    if "json" in (content_type or "") or text.lstrip().startswith("{"):
        return json.loads(text)
    m = re.search(r'data-page="([^"]+)"', text)
    if not m:
        raise ValueError("no inertia payload")
    return json.loads(html_lib.unescape(m.group(1)))


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


def fetch_via_requests(session: requests.Session) -> list[dict]:
    all_scans: list[dict] = []
    version = None
    for page in range(1, PAGES + 1):
        url = f"https://chartink.com/scan_dashboard?page={page}&per_page={PER_PAGE}"
        headers = {
            "User-Agent": UA,
            "Accept": "text/html, application/xhtml+xml",
            "X-Requested-With": "XMLHttpRequest",
            "X-Inertia": "true",
            "Referer": "https://chartink.com/scan_dashboard",
        }
        if version:
            headers["X-Inertia-Version"] = version
        r = session.get(url, headers=headers, timeout=60)
        print(f"page {page}: {r.status_code} {r.url} ct={r.headers.get('content-type')} len={len(r.text)}")
        (RAW / f"dash_page_{page}.raw").write_text(r.text[:800000], encoding="utf-8")
        if "login" in r.url.lower():
            raise RuntimeError("lost session")
        data = parse_payload(r.text, r.headers.get("content-type", ""))
        version = data.get("version") or version
        print(f"  component={data.get('component')} props={list((data.get('props') or {}).keys())}")
        (RAW / f"dash_page_{page}.json").write_text(
            json.dumps(data, indent=2, default=str)[:1200000], encoding="utf-8"
        )
        scans, meta = extract_scans(data.get("props") or {})
        print(f"  scans={len(scans)} meta={meta}")
        if not scans:
            raise RuntimeError(f"no scans on page {page}")
        all_scans.extend(scans)
        time.sleep(0.25)
    return all_scans


def fetch_via_browser(driver) -> list[dict]:
    """Fallback: load each dashboard page in browser and parse data-page."""
    all_scans: list[dict] = []
    for page in range(1, PAGES + 1):
        url = f"https://chartink.com/scan_dashboard?page={page}&per_page={PER_PAGE}"
        driver.get(url)
        time.sleep(2.5)
        html = driver.page_source
        (RAW / f"browser_page_{page}.html").write_text(html, encoding="utf-8")
        print(f"browser page {page}: url={driver.current_url} len={len(html)}")
        if "login" in (driver.current_url or "").lower():
            raise RuntimeError("browser redirected to login")
        data = parse_payload(html, "text/html")
        print(f"  component={data.get('component')} props={list((data.get('props') or {}).keys())}")
        (RAW / f"browser_page_{page}.json").write_text(
            json.dumps(data, indent=2, default=str)[:1200000], encoding="utf-8"
        )
        scans, meta = extract_scans(data.get("props") or {})
        print(f"  scans={len(scans)} meta={meta}")
        if not scans:
            raise RuntimeError(f"no scans browser page {page}")
        all_scans.extend(scans)
    return all_scans


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


def write_md(scans: list[dict], raw_n: int) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Chartink Scans URL Index",
        "",
        f"- **Source:** `https://chartink.com/scan_dashboard?page=1..{PAGES}&per_page={PER_PAGE}`",
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
            if isinstance(v, (list, dict)):
                v = json.dumps(v, ensure_ascii=False, default=str)
            bits.append(f"{k}: {v}")
        other = "; ".join(bits)
        if len(other) > 200:
            other = other[:197] + "…"
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
    kill_chrome()
    user_data = Path(tempfile.mkdtemp(prefix="chartink_login_"))
    print("temp profile", user_data)
    launch(user_data)
    ver = wait_port(DEBUG_PORT)
    print("Chrome ready", ver.get("Browser"))
    driver = attach_driver()
    wait_until_logged_in(driver)

    # save page1 html for analysis
    (RAW / "logged_in_p1.html").write_text(driver.page_source, encoding="utf-8")

    cookies = cookies_from_driver(driver)
    session = requests.Session()
    session.headers["User-Agent"] = UA
    for k, v in cookies.items():
        session.cookies.set(k, v, domain=".chartink.com")
        session.cookies.set(k, v, domain="chartink.com")

    try:
        raw_scans = fetch_via_requests(session)
    except Exception as e:
        print("requests path failed:", e)
        print("falling back to browser page walk")
        raw_scans = fetch_via_browser(driver)

    (RAW / "all_scans_raw.json").write_text(
        json.dumps(raw_scans, indent=2, default=str), encoding="utf-8"
    )
    print("raw", len(raw_scans))

    seen: set[str] = set()
    scans: list[dict] = []
    for raw in raw_scans:
        key = str(raw.get("id") or raw.get("slug") or raw.get("name") or id(raw))
        if key in seen:
            continue
        seen.add(key)
        scans.append(normalize(raw, len(scans) + 1))
    write_md(scans, len(raw_scans))
    print("DONE", len(scans))
    print("You can close the temporary Chrome window.")


if __name__ == "__main__":
    main()
