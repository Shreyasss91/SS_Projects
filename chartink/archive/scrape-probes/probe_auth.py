"""Probe Chartink HTML for API routes and try Chrome cookie / Selenium access."""
from __future__ import annotations

import html as html_lib
import json
import re
import shutil
import sqlite3
import tempfile
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "_raw_dashboard"
RAW.mkdir(parents=True, exist_ok=True)
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


def parse_page1() -> None:
    html = (RAW / "page1.html").read_text(encoding="utf-8")
    m = re.search(r'data-page="([^"]+)"', html)
    if m:
        raw = html_lib.unescape(m.group(1))
        (RAW / "data_page.json").write_text(raw, encoding="utf-8")
        print("DATA-PAGE keys ok, len", len(raw))
        print(raw[:2500])
    m2 = re.search(r"window\.CHARTINK\s*=\s*(\{.*?\});", html, re.S)
    if m2:
        print("CHARTINK", m2.group(1)[:2000])
    assets = sorted(set(re.findall(r"https://chartink\.com/build/assets/[^\s\"']+", html)))
    print("assets", assets)


def download_js_and_find_routes() -> None:
    # Fetch adminDashboard and index JS for API paths
    urls = [
        "https://chartink.com/build/assets/adminDashboard-e81abced.js",
        "https://chartink.com/build/assets/index-6c93b0f2.js",
        "https://chartink.com/build/assets/app-bd0a75b3.css",
    ]
    session = requests.Session()
    session.headers.update({"User-Agent": UA})
    patterns = [
        r"[\"'](/[^\"']*scan[^\"']*)[\"']",
        r"[\"'](/[^\"']*screener[^\"']*)[\"']",
        r"[\"'](/[^\"']*dashboard[^\"']*)[\"']",
        r"scan_dashboard",
        r"route\([\"']([^\"']+)[\"']",
        r"axios\.[a-z]+\([\"']([^\"']+)[\"']",
        r"\.get\([\"']([^\"']+)[\"']",
        r"\.post\([\"']([^\"']+)[\"']",
        r"inertia",
    ]
    for url in urls:
        if url.endswith(".css"):
            continue
        print("\n=== fetching", url)
        try:
            r = session.get(url, timeout=60)
            text = r.text
            (RAW / Path(url).name).write_text(text, encoding="utf-8")
            print("len", len(text))
            for pat in patterns:
                found = re.findall(pat, text, flags=re.I)
                uniq = []
                for f in found:
                    s = f if isinstance(f, str) else str(f)
                    if s not in uniq:
                        uniq.append(s)
                if uniq:
                    print(f"  {pat}: {len(uniq)}")
                    for u in uniq[:40]:
                        print("   ", u[:180])
        except Exception as e:
            print("ERR", e)


def try_chrome_cookies_copy() -> dict[str, str]:
    """Copy Chrome Cookies DB and read chartink.com cookies (may fail if locked/encrypted)."""
    src = Path.home() / "AppData/Local/Google/Chrome/User Data/Default/Network/Cookies"
    if not src.exists():
        print("No Chrome cookies DB")
        return {}
    tmp = Path(tempfile.mkdtemp()) / "Cookies"
    try:
        shutil.copy2(src, tmp)
    except Exception as e:
        print("cookie copy failed", e)
        return {}
    cookies: dict[str, str] = {}
    try:
        con = sqlite3.connect(str(tmp))
        cur = con.cursor()
        cur.execute(
            "SELECT name, value, host_key FROM cookies WHERE host_key LIKE '%chartink%'"
        )
        rows = cur.fetchall()
        print("chartink cookie rows", len(rows))
        for name, value, host in rows:
            print(f"  {host} {name} value_len={len(value or '')} preview={(value or '')[:20]!r}")
            if value:
                cookies[name] = value
        con.close()
    except Exception as e:
        print("sqlite read failed", e)
    return cookies


def try_selenium_chrome() -> None:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    import time

    # Use a temporary profile copy approach is heavy; try default first with remote debugging
    # or existing user data - may fail if Chrome is open.
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1400,1000")
    options.add_argument("--no-sandbox")
    # Don't load user profile in headless first - just open and see
    driver = webdriver.Chrome(options=options)
    try:
        driver.get("https://chartink.com/scan_dashboard?page=1&per_page=50")
        time.sleep(3)
        print("title", driver.title)
        print("url", driver.current_url)
        print("page snippet", driver.page_source[:500])
        (RAW / "selenium_page1.html").write_text(driver.page_source, encoding="utf-8")
    finally:
        driver.quit()


def try_selenium_with_profile() -> None:
    """Attach to logged-in Chrome profile if possible."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    import time

    user_data = Path.home() / "AppData/Local/Google/Chrome/User Data"
    # Copy profile is too large; try remote debugging port if user has Chrome open
    # Or use a dedicated profile dir copy of Local State + Default cookies only.

    # Prefer connecting via debuggerAddress if available
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    try:
        driver = webdriver.Chrome(options=options)
        print("attached to existing chrome 9222")
        driver.get("https://chartink.com/scan_dashboard?page=1&per_page=50")
        time.sleep(4)
        print("title", driver.title)
        print("url", driver.current_url)
        (RAW / "selenium_attached_page1.html").write_text(driver.page_source, encoding="utf-8")
        # extract links
        links = driver.find_elements("css selector", "a[href*='screener']")
        print("screener links", len(links))
        for a in links[:10]:
            print(a.get_attribute("href"), a.text[:80] if a.text else "")
        return
    except Exception as e:
        print("debugger attach failed:", e)

    # Try separate user-data-dir pointing at a temp copy of Default Network cookies - won't work without full profile encryption key.
    print("Trying dedicated chrome profile path (may fail if locked)")
    options = Options()
    options.add_argument(f"--user-data-dir={user_data}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--headless=new")
    try:
        driver = webdriver.Chrome(options=options)
        driver.get("https://chartink.com/scan_dashboard?page=1&per_page=50")
        time.sleep(4)
        print("title", driver.title)
        print("url", driver.current_url)
        (RAW / "selenium_profile_page1.html").write_text(driver.page_source, encoding="utf-8")
        driver.quit()
    except Exception as e:
        print("profile selenium failed:", e)


if __name__ == "__main__":
    parse_page1()
    download_js_and_find_routes()
    cookies = try_chrome_cookies_copy()
    print("usable plain cookies", list(cookies.keys()))
    try:
        try_selenium_chrome()
    except Exception as e:
        print("selenium headless failed", e)
    try:
        try_selenium_with_profile()
    except Exception as e:
        print("selenium profile failed", e)
