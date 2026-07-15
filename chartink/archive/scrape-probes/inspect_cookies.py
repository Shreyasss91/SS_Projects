import base64
import json
import shutil
import sqlite3
import tempfile
from pathlib import Path

import win32crypt
from Cryptodome.Cipher import AES

ls_path = Path.home() / "AppData/Local/Google/Chrome/User Data/Local State"
ls = json.loads(ls_path.read_text(encoding="utf-8"))
osc = ls.get("os_crypt", {})
print("os_crypt keys:", list(osc.keys()))
for k, v in osc.items():
    if isinstance(v, str):
        print(f"  {k}: len={len(v)} prefix={v[:30]!r}")
    else:
        print(f"  {k}: {v!r}")

# Chrome version folders
ver = Path(r"C:\Program Files\Google\Chrome\Application")
if ver.exists():
    print("chrome dirs:", [p.name for p in ver.iterdir() if p.is_dir()][:8])

src = Path.home() / "AppData/Local/Google/Chrome/User Data/Default/Network/Cookies"
dst = Path(tempfile.mkdtemp()) / "Cookies"
shutil.copy2(src, dst)
con = sqlite3.connect(str(dst))
cur = con.cursor()
cur.execute(
    "SELECT name, length(encrypted_value), hex(substr(encrypted_value,1,10)) "
    "FROM cookies WHERE host_key LIKE '%chartink%'"
)
for r in cur.fetchall():
    print("cookie", r)

# try both keys if present
enc_key_b64 = osc.get("encrypted_key")
if enc_key_b64:
    enc = base64.b64decode(enc_key_b64)
    print("encrypted_key prefix bytes", enc[:5])
    key = win32crypt.CryptUnprotectData(enc[5:], None, None, None, 0)[1]
    print("dpapi key len", len(key), key[:4].hex())

    cur.execute(
        "SELECT name, encrypted_value FROM cookies WHERE host_key LIKE '%chartink%'"
    )
    for name, encv in cur.fetchall():
        if not encv:
            continue
        prefix = encv[:3]
        print(f" try {name} prefix={prefix!r} len={len(encv)}")
        if prefix in (b"v10", b"v11", b"v20"):
            nonce = encv[3:15]
            ciphertext = encv[15:-16]
            tag = encv[-16:]
            try:
                plain = AES.new(key, AES.MODE_GCM, nonce=nonce).decrypt_and_verify(
                    ciphertext, tag
                )
                print("  OK", plain[:40])
            except Exception as e:
                print("  AES fail", e)
                # try decrypt without verify, strip tag differently
                try:
                    plain = AES.new(key, AES.MODE_GCM, nonce=nonce).decrypt(encv[15:])
                    print("  raw decrypt last16", plain[-16:].hex(), "body", plain[:-16][:40])
                except Exception as e2:
                    print("  raw fail", e2)

# app_bound_encrypted_key attempt
ab = osc.get("app_bound_encrypted_key")
if ab:
    raw = base64.b64decode(ab)
    print("app_bound prefix", raw[:8], "len", len(raw))
    # often starts with APPB
    if raw[:4] == b"APPB":
        blob = raw[4:]
        try:
            # first DPAPI as user
            mid = win32crypt.CryptUnprotectData(blob, None, None, None, 0)[1]
            print("APPB user-dpapi ok len", len(mid), mid[:20])
        except Exception as e:
            print("APPB user-dpapi fail", e)

con.close()
