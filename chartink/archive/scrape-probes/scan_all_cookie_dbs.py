"""Scan all Chrome/Edge cookie DBs for chartink sessions."""
from __future__ import annotations

import base64
import json
import shutil
import sqlite3
import tempfile
from pathlib import Path

import win32crypt
from Cryptodome.Cipher import AES

UA = "Mozilla/5.0"


def get_key(local_state: Path) -> bytes:
    data = json.loads(local_state.read_text(encoding="utf-8"))
    encrypted_key = base64.b64decode(data["os_crypt"]["encrypted_key"])
    assert encrypted_key[:5] == b"DPAPI"
    return win32crypt.CryptUnprotectData(encrypted_key[5:], None, None, None, 0)[1]


def decrypt_value(encrypted: bytes, key: bytes) -> str:
    if not encrypted:
        return ""
    if encrypted[:3] in (b"v10", b"v20"):
        nonce = encrypted[3:15]
        ciphertext = encrypted[15:-16]
        tag = encrypted[-16:]
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        try:
            return cipher.decrypt_and_verify(ciphertext, tag).decode("utf-8")
        except Exception:
            plain = AES.new(key, AES.MODE_GCM, nonce=nonce).decrypt(encrypted[15:])
            return plain[:-16].decode("utf-8", errors="replace")
    try:
        return win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)[1].decode(
            "utf-8"
        )
    except Exception as e:
        return f"<fail:{e}>"


def try_db(path: Path, key: bytes) -> dict[str, str]:
    tmp = Path(tempfile.mkdtemp()) / "Cookies"
    try:
        shutil.copy2(path, tmp)
    except Exception as e:
        print(f"  copy fail {path}: {e}")
        return {}
    cookies = {}
    try:
        con = sqlite3.connect(str(tmp))
        cur = con.cursor()
        cur.execute(
            "SELECT name, value, encrypted_value, host_key FROM cookies WHERE host_key LIKE '%chartink%'"
        )
        rows = cur.fetchall()
        print(f"  chartink rows: {len(rows)}")
        for name, value, enc, host in rows:
            plain = value or ""
            if not plain and enc:
                plain = decrypt_value(enc, key)
            print(f"    {host} {name} len={len(plain)}")
            if plain and not plain.startswith("<fail"):
                cookies[name] = plain
        con.close()
    except Exception as e:
        print(f"  sqlite fail: {e}")
    return cookies


def main() -> None:
    browsers = [
        (
            "chrome",
            Path.home() / "AppData/Local/Google/Chrome/User Data",
        ),
        (
            "edge",
            Path.home() / "AppData/Local/Microsoft/Edge/User Data",
        ),
    ]
    import requests

    for bname, base in browsers:
        ls = base / "Local State"
        if not ls.exists():
            continue
        print(f"\n==== {bname} key ====")
        key = get_key(ls)
        for profile in sorted(base.iterdir()):
            if not profile.is_dir():
                continue
            cdb = profile / "Network" / "Cookies"
            if not cdb.exists():
                cdb = profile / "Cookies"
            if not cdb.exists():
                continue
            print(f"\nprofile {profile.name} size={cdb.stat().st_size}")
            cookies = try_db(cdb, key)
            if not cookies:
                continue
            # test session
            s = requests.Session()
            s.headers["User-Agent"] = UA
            for k, v in cookies.items():
                s.cookies.set(k, v, domain=".chartink.com")
            r = s.get(
                "https://chartink.com/scan_dashboard?page=1&per_page=50",
                timeout=30,
                headers={
                    "X-Inertia": "true",
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json, text/html",
                },
            )
            print(f"  status={r.status_code} url={r.url} ct={r.headers.get('content-type')}")
            preview = r.text[:300].replace("\n", " ")
            print("  preview", preview)
            if "login" not in r.url.lower() and "Login" not in r.text[:500]:
                out = Path(__file__).resolve().parent / "_raw_dashboard" / f"session_{bname}_{profile.name}.json"
                out.write_text(json.dumps(cookies), encoding="utf-8")
                print("  SAVED session cookies to", out)


if __name__ == "__main__":
    main()
