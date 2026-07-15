"""Decrypt Chrome cookies for chartink.com and scrape scan dashboard."""
from __future__ import annotations

import base64
import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import requests
import win32crypt
from Cryptodome.Cipher import AES

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "_raw_dashboard"
RAW.mkdir(parents=True, exist_ok=True)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


def get_chrome_key() -> bytes:
    local_state = (
        Path.home()
        / "AppData/Local/Google/Chrome/User Data/Local State"
    )
    data = json.loads(local_state.read_text(encoding="utf-8"))
    encrypted_key = base64.b64decode(data["os_crypt"]["encrypted_key"])
    # strip DPAPI prefix
    assert encrypted_key[:5] == b"DPAPI"
    key = win32crypt.CryptUnprotectData(encrypted_key[5:], None, None, None, 0)[1]
    return key


def decrypt_value(encrypted: bytes, key: bytes) -> str:
    if not encrypted:
        return ""
    # Chrome cookies: v10 / v20 + 12-byte nonce + ciphertext + 16-byte tag
    if encrypted[:3] in (b"v10", b"v20"):
        nonce = encrypted[3:15]
        ciphertext = encrypted[15:-16]
        tag = encrypted[-16:]
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        try:
            return cipher.decrypt_and_verify(ciphertext, tag).decode("utf-8")
        except Exception:
            # sometimes no separate verify path
            plain = AES.new(key, AES.MODE_GCM, nonce=nonce).decrypt(encrypted[15:])
            return plain[:-16].decode("utf-8", errors="replace")
    # older DPAPI
    try:
        return win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)[1].decode(
            "utf-8"
        )
    except Exception as e:
        return f"<decrypt_fail:{e}>"


def copy_cookies_db() -> Path:
    import ctypes
    from ctypes import wintypes

    src = (
        Path.home()
        / "AppData/Local/Google/Chrome/User Data/Default/Network/Cookies"
    )
    dst_dir = Path(tempfile.mkdtemp(prefix="chrome_cookies_"))
    dst = dst_dir / "Cookies"

    # Windows CreateFile with share flags can read Chrome's locked Cookies DB.
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    GENERIC_READ = 0x80000000
    FILE_SHARE_ALL = 0x00000007
    OPEN_EXISTING = 3
    FILE_ATTRIBUTE_NORMAL = 0x80
    INVALID = wintypes.HANDLE(-1).value

    handle = kernel32.CreateFileW(
        str(src),
        GENERIC_READ,
        FILE_SHARE_ALL,
        None,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        None,
    )
    if handle in (INVALID, -1):
        err = ctypes.get_last_error()
        raise RuntimeError(f"CreateFileW failed err={err}")

    chunks: list[bytes] = []
    try:
        buf = ctypes.create_string_buffer(1024 * 1024)
        nread = wintypes.DWORD(0)
        while True:
            ok = kernel32.ReadFile(handle, buf, len(buf), ctypes.byref(nread), None)
            if not ok:
                raise RuntimeError(f"ReadFile failed err={ctypes.get_last_error()}")
            if nread.value == 0:
                break
            chunks.append(buf.raw[: nread.value])
    finally:
        kernel32.CloseHandle(handle)

    data = b"".join(chunks)
    dst.write_bytes(data)
    print(f"shared-read copy ok bytes={len(data)}")
    return dst


def load_chartink_cookies(key: bytes) -> dict[str, str]:
    db = copy_cookies_db()
    con = sqlite3.connect(str(db))
    cur = con.cursor()
    # Chrome may use encrypted_value
    cur.execute(
        """
        SELECT name, value, encrypted_value, host_key, path, is_secure, expires_utc
        FROM cookies
        WHERE host_key LIKE '%chartink%'
        """
    )
    cookies: dict[str, str] = {}
    for name, value, enc, host, path, secure, exp in cur.fetchall():
        plain = value or ""
        if not plain and enc:
            plain = decrypt_value(enc, key)
        print(f"cookie {host} {name} len={len(plain)} path={path}")
        if plain and not plain.startswith("<decrypt_fail"):
            cookies[name] = plain
    con.close()
    return cookies


def fetch_dashboard_pages(cookies: dict[str, str]) -> list[dict]:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": UA,
            "Accept": "text/html, application/xhtml+xml",
            "X-Requested-With": "XMLHttpRequest",
            "X-Inertia": "true",
            "X-Inertia-Version": "8e8ef90b3b7528cb3e7ecef83f452414",
        }
    )
    for k, v in cookies.items():
        session.cookies.set(k, v, domain=".chartink.com")

    all_scans: list[dict] = []
    for page in range(1, 11):
        url = f"https://chartink.com/scan_dashboard?page={page}&per_page=50"
        # First try Inertia JSON
        r = session.get(url, timeout=60)
        print(f"page {page} status={r.status_code} ct={r.headers.get('content-type')} len={len(r.text)}")
        (RAW / f"auth_page_{page}.txt").write_text(r.text[:200000], encoding="utf-8")
        ctype = r.headers.get("content-type", "")
        if "json" in ctype or r.text.lstrip().startswith("{"):
            try:
                data = r.json()
                (RAW / f"auth_page_{page}.json").write_text(
                    json.dumps(data, indent=2)[:500000], encoding="utf-8"
                )
                print("  component", data.get("component"))
                print("  url", data.get("url"))
                props = data.get("props") or {}
                # dump top-level prop keys
                print("  prop keys", list(props.keys())[:40])
                # try common shapes
                candidates = []
                for key in (
                    "scans",
                    "data",
                    "items",
                    "screeners",
                    "scan_list",
                    "results",
                    "paginator",
                    "scanDashboard",
                ):
                    if key in props:
                        candidates.append((key, props[key]))
                # nested
                for k, v in props.items():
                    if isinstance(v, dict) and any(
                        x in v for x in ("data", "scans", "items", "total")
                    ):
                        candidates.append((k, v))
                        print(f"  nested candidate {k} keys={list(v.keys())[:20]}")
                for name, val in candidates:
                    print(f"  candidate {name} type={type(val).__name__}")
                    if isinstance(val, list):
                        print(f"    list len={len(val)}")
                        if val:
                            print("    first keys", list(val[0].keys()) if isinstance(val[0], dict) else val[0])
                    elif isinstance(val, dict):
                        print("    dict keys", list(val.keys())[:30])
                # generic extract
                extracted = extract_scans_from_props(props)
                print(f"  extracted {len(extracted)} scans")
                all_scans.extend(extracted)
            except Exception as e:
                print("  json parse fail", e)
        else:
            # HTML - check if still login
            if "login" in r.url or "Login" in r.text[:2000]:
                print("  still login page")
            # try parse data-page
            import html as html_lib
            import re

            m = re.search(r'data-page="([^"]+)"', r.text)
            if m:
                raw = html_lib.unescape(m.group(1))
                try:
                    data = json.loads(raw)
                    (RAW / f"auth_page_{page}_datapage.json").write_text(
                        json.dumps(data, indent=2)[:500000], encoding="utf-8"
                    )
                    print("  data-page component", data.get("component"), "url", data.get("url"))
                    props = data.get("props") or {}
                    print("  prop keys", list(props.keys())[:40])
                    extracted = extract_scans_from_props(props)
                    print(f"  extracted {len(extracted)} scans")
                    all_scans.extend(extracted)
                except Exception as e:
                    print("  data-page parse fail", e)
        # without inertia header too on page 1
        if page == 1 and not all_scans:
            r2 = session.get(
                url,
                timeout=60,
                headers={
                    "User-Agent": UA,
                    "Accept": "text/html",
                },
            )
            print(f"  non-inertia status={r2.status_code} url={r2.url} len={len(r2.text)}")
            (RAW / "auth_page_1_html.html").write_text(r2.text, encoding="utf-8")
    return all_scans


def extract_scans_from_props(props: dict) -> list[dict]:
    """Heuristically find scan list structures in Inertia props."""
    found: list[dict] = []

    def walk(obj, path=""):
        if isinstance(obj, dict):
            # list of scan-like objects
            for key in ("data", "scans", "items", "screeners"):
                if key in obj and isinstance(obj[key], list) and obj[key]:
                    sample = obj[key][0]
                    if isinstance(sample, dict) and (
                        "slug" in sample
                        or "name" in sample
                        or "scan_name" in sample
                        or "title" in sample
                        or "id" in sample
                    ):
                        for item in obj[key]:
                            if isinstance(item, dict):
                                found.append(item)
                        return
            for k, v in obj.items():
                walk(v, f"{path}.{k}")
        elif isinstance(obj, list) and obj and isinstance(obj[0], dict):
            sample = obj[0]
            if any(k in sample for k in ("slug", "scan_name", "atlas_query")):
                for item in obj:
                    if isinstance(item, dict):
                        found.append(item)

    walk(props)
    # dedupe by id/slug
    seen = set()
    out = []
    for s in found:
        key = s.get("id") or s.get("slug") or s.get("name")
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out


def main() -> None:
    print("getting chrome key...")
    key = get_chrome_key()
    print("key len", len(key))
    cookies = load_chartink_cookies(key)
    print("cookies", list(cookies.keys()))
    (RAW / "cookie_names.json").write_text(json.dumps(list(cookies.keys())), encoding="utf-8")
    if not cookies:
        print("NO COOKIES - cannot proceed authenticated")
        return
    scans = fetch_dashboard_pages(cookies)
    print("TOTAL scans extracted", len(scans))
    (RAW / "all_scans_raw.json").write_text(
        json.dumps(scans, indent=2, default=str), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
