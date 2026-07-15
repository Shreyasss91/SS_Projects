"""Attempt Chrome v20 cookie decrypt via elevation_service COM IElevator."""
from __future__ import annotations

import base64
import json
import shutil
import sqlite3
import tempfile
from pathlib import Path

try:
    import comtypes
    import comtypes.client
    from comtypes import GUID, COMMETHOD, HRESULT, BSTR, IUnknown
    from ctypes import POINTER, c_ulong, c_int
except Exception as e:
    print("comtypes import failed", e)
    comtypes = None

# Chromium elevation service IIDs (may vary by version)
# From chromium: chrome/elevation_service/elevation_service_idl.idl

IID_IElevator = GUID("{A949CB4E-C4F9-44C4-B213-6BF8AA9AC69C}")  # might be library
# Actual interface IDs from public POCs:
CANDIDATE_CLSIDS = [
    "{708860E0-F641-4611-8895-7D867DD3675B}",  # AppID - wrong maybe
    "{BB2A15FE-8D70-4DAE-BE4A-4B1B9A7C3D2B}",
    "{1BF5208B-295F-4992-B5F4-3A9BB6494838}",
    "{A2721D66-376E-4D2F-9F0F-9070E9A42B5F}",
    "{B88C45B9-8825-4629-B564-7A5B8A0A3B0B}",
    "{C9C2B807-7731-4F34-81B7-44FF7779522B}",
]

# Google Chrome elevator CLSID from multiple public sources (Chrome):
# {708860E0-F641-4611-8895-7D867DD3675B} is AppID
# Chrome: CLSID_Elevator = {A2721D66-376E-4D2F-9F0F-9070E9A42B5F} ? 

# From xaitax chrome decrypt:
CHROME_CLSID = "{708860E0-F641-4611-8895-7D867DD3675B}"


def try_oleview_strings() -> None:
    exe = Path(r"C:\Program Files\Google\Chrome\Application\150.0.7871.125\elevation_service.exe")
    data = exe.read_bytes()
    # extract GUID-like strings
    import re
    text = data.decode("latin-1", errors="ignore")
    guids = re.findall(
        r"\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}",
        text,
    )
    uniq = []
    for g in guids:
        if g.upper() not in uniq:
            uniq.append(g.upper())
    print("GUIDs in elevation_service.exe:", len(uniq))
    for g in uniq[:40]:
        print(" ", g)


def main() -> None:
    try_oleview_strings()
    # also search for DecryptData string
    exe = Path(r"C:\Program Files\Google\Chrome\Application\150.0.7871.125\elevation_service.exe")
    data = exe.read_bytes()
    for s in [b"DecryptData", b"EncryptData", b"IElevator", b"APPB", b"Chrome"]:
        print(s, data.find(s))


if __name__ == "__main__":
    main()
