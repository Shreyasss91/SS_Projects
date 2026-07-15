"""
Launch Chrome with remote debugging (user profile), fetch Chartink cookies via CDP,
scrape scan_dashboard pages, write scans_url_index.md.
"""
from __future__ import annotations

import html as html_lib
import json
import re
import subprocess
import time
import urllib.error
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
USER_DATA = Path.home() / "AppData/Local/Google/Chrome/User Data"
DEBUG_PORT = 9222
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/150.0.0.0 Safari/537.36"
)
TOTAL_EXPECTED = 478
PAGES = 10
PER_PAGE = 50


def chrome_running() -> bool:
    r = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq chrome.exe"],
        capture_output=True,
        text=True,
    )
    return "chrome.exe" in r.stdout.lower()


def wait_debug_port(timeout: float = 30.0) -> dict:
    deadline = time.time() + timeout
    last_err = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{DEBUG_PORT}/json/version", timeout=2
            ) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            last_err = e
            time.sleep(0.4)
    raise RuntimeError(f"DevTools port not ready: {last_err}")


def cdp_http(path: str) -> Any:
    with urllib.request.urlopen(f"http://127.0.0.1:{DEBUG_PORT}{path}", timeout=10) as r:
        return json.loads(r.read().decode())


def get_cookies_via_cdp() -> list[dict]:
    """Use websocket-less approach: open a target and use /json endpoints...

    Prefer selenium/devtools websocket for Network.getAllCookies.
    """
    try:
        import websocket  # type: ignore
    except ImportError:
        websocket = None

    # ensure a tab exists
    targets = cdp_http("/json/list")
    page = None
    for t in targets:
        if t.get("type") == "page" and t.get("webSocketDebuggerUrl"):
            page = t
            break
    if not page:
        # open a new tab
        cdp_http("/json/new?https://chartink.com/")
        time.sleep(1)
        targets = cdp_http("/json/list")
        for t in targets:
            if t.get("type") == "page" and t.get("webSocketDebuggerUrl"):
                page = t
                break
    if not page:
        raise RuntimeError("No CDP page target")

    ws_url = page["webSocketDebuggerUrl"]
    if websocket is None:
        # fallback: use simple websocket via urllib is not possible; install? use selenium
        raise RuntimeError("websocket-client not installed")

    cookies: list[dict] = []
    ws = websocket.create_connection(ws_url, timeout=15)
    try:
        # Enable network and get all cookies
        msg_id = 1

        def send(method: str, params: dict | None = None) -> dict:
            nonlocal msg_id
            payload = {"id": msg_id, "method": method}
            if params:
                payload["params"] = params
            msg_id += 1
            ws.send(json.dumps(payload))
            # read until matching id
            while True:
                raw = ws.recv()
                data = json.loads(raw)
                if data.get("id") == payload["id"]:
                    return data

        send("Network.enable")
        result = send("Network.getAllCookies")
        all_cookies = (result.get("result") or {}).get("cookies") or []
        cookies = [c for c in all_cookies if "chartink.com" in (c.get("domain") or "")]
        print(f"CDP chartink cookies: {len(cookies)}")
        for c in cookies:
            print(f"  {c.get('name')} domain={c.get('domain')} len={len(c.get('value') or '')}")
    finally:
        ws.close()
    return cookies


def get_cookies_via_selenium() -> dict[str, str]:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{DEBUG_PORT}")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get("https://chartink.com/scan_dashboard?page=1&per_page=50")
        time.sleep(3)
        print("selenium title", driver.title, "url", driver.current_url)
        cookies = driver.get_cookies()
        out = {}
        for c in cookies:
            if "chartink" in (c.get("domain") or ""):
                out[c["name"]] = c["value"]
                print(f"  cookie {c['name']} len={len(c['value'])}")
        # also grab page source for page 1 if already loaded
        (RAW / "selenium_dash_p1.html").write_text(driver.page_source, encoding="utf-8")
        return out
    finally:
        # do not quit — would close the browser attached to user profile
        pass


def parse_page_payload(text: str, content_type: str) -> dict:
    if "json" in (content_type or "") or text.lstrip().startswith("{"):
        return json.loads(text)
    m = re.search(r'data-page="([^"]+)"', text)
    if not m:
        # try type=application/json in script
        m2 = re.search(
            r'<script type="application/json"[^>]*id="app"[^>]*>(.*?)</script>',
            text,
            re.S,
        )
        if m2:
            return json.loads(html_lib.unescape(m2.group(1)))
        raise ValueError("No inertia payload found")
    return json.loads(html_lib.unescape(m.group(1)))


def extract_scan_list(props: dict) -> tuple[list[dict], dict]:
    meta: dict = {}
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
                "screener_url",
            }
        ) or ("id" in keys and ("name" in keys or "title" in keys))

    def consider(items: list, path: str) -> None:
        nonlocal found
        if found:
            return
        if items and isinstance(items[0], dict) and looks_like_scan(items[0]):
            print(f"  list @ {path} n={len(items)} keys={list(items[0].keys())[:25]}")
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


def fetch_all(session: requests.Session) -> list[dict]:
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
        print(
            f"page {page}: {r.status_code} {r.url} ct={r.headers.get('content-type')} len={len(r.text)}"
        )
        (RAW / f"dash_page_{page}.raw").write_text(r.text[:500000], encoding="utf-8")
        if "login" in r.url.lower():
            raise RuntimeError("Still on login — session invalid")
        data = parse_page_payload(r.text, r.headers.get("content-type", ""))
        version = data.get("version") or version
        print(f"  component={data.get('component')} keys={list((data.get('props') or {}).keys())}")
        (RAW / f"dash_page_{page}.json").write_text(
            json.dumps(data, indent=2, default=str)[:900000], encoding="utf-8"
        )
        scans, meta = extract_scan_list(data.get("props") or {})
        print(f"  scans={len(scans)} meta={meta}")
        if not scans:
            raise RuntimeError(f"No scans on page {page}")
        all_scans.extend(scans)
        time.sleep(0.3)
    return all_scans


def normalize(raw: dict, n: int) -> dict:
    name = (
        raw.get("name")
        or raw.get("scan_name")
        or raw.get("title")
        or f"Unnamed {n}"
    )
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
    if url.startswith("/"):
        url = "https://chartink.com" + url

    skip = {
        "name",
        "scan_name",
        "title",
        "slug",
        "scan_slug",
        "url",
        "scan_url",
        "screener_url",
        "link",
        "atlas_json",
        "atlas_query",
        "query",
        "pivot_json",
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
        elif isinstance(v, str):
            extras[k] = v[:200] + ("…" if len(v) > 200 else "")
        else:
            extras[k] = f"<{type(v).__name__} len={len(v)}>"
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
        lines.append(
            f"- **Note:** Indexed count differs from expected {TOTAL_EXPECTED}."
        )
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
    print("Wrote", OUT_MD, OUT_MD.stat().st_size, "bytes")


def main() -> None:
    if chrome_running():
        print("Chrome is still running — attempting attach to existing debug port first")
        try:
            ver = wait_debug_port(timeout=2)
            print("Already debugging:", ver.get("Browser"))
        except Exception:
            raise RuntimeError(
                "Chrome is running without remote debugging. "
                "Please fully quit Chrome, then re-run this script."
            )
        proc = None
    else:
        print("Launching Chrome with remote debugging on", DEBUG_PORT)
        proc = subprocess.Popen(
            [
                str(CHROME),
                f"--remote-debugging-port={DEBUG_PORT}",
                f"--user-data-dir={USER_DATA}",
                "--profile-directory=Default",
                "--restore-last-session",
                "https://chartink.com/scan_dashboard?page=1&per_page=50",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        ver = wait_debug_port(timeout=40)
        print("Chrome ready:", ver.get("Browser"))

    # Prefer selenium attach for cookies + possible page parse
    cookies = get_cookies_via_selenium()
    if not cookies:
        # try websocket CDP
        try:
            cdp_cookies = get_cookies_via_cdp()
            cookies = {c["name"]: c["value"] for c in cdp_cookies}
        except Exception as e:
            print("CDP cookie fallback failed:", e)

    if not cookies:
        raise RuntimeError("No chartink cookies obtained")

    (RAW / "cookies_names.json").write_text(
        json.dumps(sorted(cookies.keys())), encoding="utf-8"
    )

    session = requests.Session()
    session.headers["User-Agent"] = UA
    for k, v in cookies.items():
        session.cookies.set(k, v, domain=".chartink.com")
        session.cookies.set(k, v, domain="chartink.com")

    raw_scans = fetch_all(session)
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


if __name__ == "__main__":
    main()
