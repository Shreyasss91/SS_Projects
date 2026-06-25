#!/usr/bin/env python3
"""
testscript_office.py
OpenAlgo + Tailscale diagnostic (Office-PC)

Edit DEVICE_NAMES if needed.
"""
import subprocess, socket, urllib.request, re, sys

DEVICE_NAMES = {
    "office": "desktop-mbo33ir",
    "home": "home-pc",
    "mobile": "shreyas-galaxy-a52",
}
PORT = 5000

def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, shell=True).stdout
    except Exception as e:
        return str(e)

def banner(t):
    print("\n"+"="*70)
    print(t)
    print("="*70)

def check(msg, ok):
    print(f"[{'PASS' if ok else 'FAIL'}] {msg}")

banner("OPENALGO OFFICE-PC DIAGNOSTIC")

print("Python :", sys.version.split()[0])

ts = run("tailscale status")
if not ts.strip():
    check("Tailscale installed / running", False)
    sys.exit(1)
check("Tailscale running", True)

ips={}
for line in ts.splitlines():
    p=line.split()
    if len(p)>=2:
        ips[p[1]]=p[0]

for role,name in DEVICE_NAMES.items():
    if name in ips:
        check(f"{role.title()} found ({name})",True)
        print("   IP:",ips[name])
    else:
        check(f"{role.title()} found ({name})",False)

banner("PORT CHECK")
net=run("netstat -ano | findstr :5000")
print(net)
check("Listening on 0.0.0.0", "0.0.0.0:5000" in net)

banner("HTTP")
tests=[
("localhost","http://127.0.0.1:5000"),
]
if "office" in DEVICE_NAMES and DEVICE_NAMES["office"] in ips:
    tests.append(("tailscale",f"http://{ips[DEVICE_NAMES['office']]}:{PORT}"))

for name,url in tests:
    try:
        with urllib.request.urlopen(url,timeout=5) as r:
            check(f"{name} ({url})", r.status==200)
    except Exception as e:
        check(f"{name} ({url})",False)
        print("   ",e)

banner("PING")
for role in ("home","mobile"):
    n=DEVICE_NAMES[role]
    if n in ips:
        out=run(f'ping -n 2 {ips[n]}')
        check(f"Ping {role}", "TTL=" in out)

banner("FIREWALL")
fw=run('powershell -Command "Get-NetFirewallRule -DisplayName \'OpenAlgo 5000\'"')
check("Firewall rule OpenAlgo 5000", "OpenAlgo 5000" in fw)

print("\nDone.")
