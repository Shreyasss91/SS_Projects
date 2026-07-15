"""
Start Chrome with the real Default profile via Selenium (Chrome must be closed).
If session is still valid, scrape scan dashboard pages and write scans_url_index.md.
"""
from __future__ import annotations

import html as html_lib
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "_raw_dashboard"
OUT_MD = ROOT / "scans_url_index.md"
RAW.mkdir(parents=True, exist_ok=True)

USER_DATA = Path.home() / "AppData/Local/Google/Chrome/User Data"
TOTAL_EXPECTED = 478
PAGES = 10
PER_PAGE = 50


def kill_chrome() -> None:
    subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], capture_output=True)
    time.sleep(2)


def is_app_url(url: str) -> bool:
    p = urlparse(url or "")
    host = (p.netloc or "").lower()
    if host not in ("chartink.com", "www.chartink.com"):
        return False
    path = (p.path or "").lower()
    return not (path.startswith("/login") or path.startswith("/auth/"))


def parse_payload(text: str) -> dict:
    if text.lstrip().startswith("{"):
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
    print("Ensuring Chrome is closed...")
    kill_chrome()

    options = Options()
    # Use a dedicated debug port so chromedriver can attach even when
    # Chrome takes longer to write DevToolsActivePort under a large profile.
    options.add_argument("--remote-debugging-port=9334")
    options.add_argument(f"--user-data-dir={USER_DATA}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--remote-allow-origins=*")
    # Avoid automation banner issues
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    print("Starting Chrome with real Default profile via Selenium...")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get("https://chartink.com/scan_dashboard?page=1&per_page=50")
        time.sleep(5)
        print("url:", driver.current_url)
        print("title:", driver.title)
        (RAW / "selenium_profile_p1.html").write_text(driver.page_source, encoding="utf-8")

        if not is_app_url(driver.current_url or ""):
            print(
                "\n*** Not logged in. Please complete Chartink login in this Chrome window. ***\n"
            )
            deadline = time.time() + 300
            while time.time() < deadline:
                time.sleep(3)
                if is_app_url(driver.current_url or ""):
                    driver.get("https://chartink.com/scan_dashboard?page=1&per_page=50")
                    time.sleep(3)
                    if is_app_url(driver.current_url or "") and "scan_dashboard" in (
                        driver.current_url or ""
                    ):
                        break
                print("  still waiting...", (driver.current_url or "")[:100])
            else:
                raise TimeoutError("login timeout")

        all_scans: list[dict] = []
        for page in range(1, PAGES + 1):
            url = f"https://chartink.com/scan_dashboard?page={page}&per_page={PER_PAGE}"
            driver.get(url)
            time.sleep(2.5)
            html = driver.page_source
            print(f"page {page}: {driver.current_url} len={len(html)}")
            (RAW / f"browser_page_{page}.html").write_text(html, encoding="utf-8")
            if not is_app_url(driver.current_url or ""):
                raise RuntimeError(f"lost session on page {page}: {driver.current_url}")
            data = parse_payload(html)
            print(
                f"  component={data.get('component')} "
                f"props={list((data.get('props') or {}).keys())}"
            )
            (RAW / f"browser_page_{page}.json").write_text(
                json.dumps(data, indent=2, default=str)[:1500000], encoding="utf-8"
            )
            scans, meta = extract_scans(data.get("props") or {})
            print(f"  scans={len(scans)} meta={meta}")
            if not scans:
                # try executing fetch in page context
                js = f"""
                const r = await fetch({url!r}, {{
                  credentials: 'include',
                  headers: {{
                    'X-Inertia': 'true',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'text/html, application/xhtml+xml'
                  }}
                }});
                return await r.text();
                """
                text = driver.execute_script(
                    "var cb = arguments[arguments.length-1];"
                    "(async()=>{try{const t=await (async()=>{" + js + "})(); cb(t);}catch(e){cb('ERR:'+e);}})();",
                    # async script
                )
                # use async script properly
                text = driver.execute_async_script(
                    """
                    const url = arguments[0];
                    const done = arguments[arguments.length - 1];
                    (async () => {
                      try {
                        const r = await fetch(url, {
                          credentials: 'include',
                          headers: {
                            'X-Inertia': 'true',
                            'X-Requested-With': 'XMLHttpRequest',
                            'Accept': 'text/html, application/xhtml+xml'
                          }
                        });
                        const t = await r.text();
                        done(t);
                      } catch (e) {
                        done('ERR:' + e);
                      }
                    })();
                    """,
                    url,
                )
                (RAW / f"browser_page_{page}_fetch.raw").write_text(text[:800000], encoding="utf-8")
                if text.startswith("ERR:"):
                    raise RuntimeError(text)
                data = parse_payload(text)
                scans, meta = extract_scans(data.get("props") or {})
                print(f"  fetch scans={len(scans)} meta={meta}")
                if not scans:
                    raise RuntimeError(f"no scans on page {page}")
            all_scans.extend(scans)

        (RAW / "all_scans_raw.json").write_text(
            json.dumps(all_scans, indent=2, default=str), encoding="utf-8"
        )
        seen: set[str] = set()
        scans_out: list[dict] = []
        for raw in all_scans:
            key = str(raw.get("id") or raw.get("slug") or raw.get("name") or id(raw))
            if key in seen:
                continue
            seen.add(key)
            scans_out.append(normalize(raw, len(scans_out) + 1))
        write_md(scans_out, len(all_scans))
        print("DONE", len(scans_out))
    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
