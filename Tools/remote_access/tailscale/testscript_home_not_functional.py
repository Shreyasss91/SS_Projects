#!/usr/bin/env python3
"""
testscript_home.py
Remote connectivity test (Home-PC)
Edit OFFICE_NAME if required.
"""
import subprocess, urllib.request, sys

OFFICE_NAME="desktop-mbo33ir"
PORT=5000

def run(cmd):
    return subprocess.run(cmd,capture_output=True,text=True,shell=True).stdout

def check(msg,ok):
    print(f"[{'PASS' if ok else 'FAIL'}] {msg}")

print("="*70)
print("OPENALGO HOME-PC DIAGNOSTIC")
print("="*70)
print("Python:",sys.version.split()[0])

ts=run("tailscale status")
if not ts.strip():
    check("Tailscale running",False)
    raise SystemExit

check("Tailscale running",True)

office_ip=None
for l in ts.splitlines():
    p=l.split()
    if len(p)>=2 and p[1]==OFFICE_NAME:
        office_ip=p[0]
        break

check("Office-PC found",office_ip is not None)
if not office_ip:
    raise SystemExit

print("Office IP:",office_ip)

out=run(f"ping -n 2 {office_ip}")
check("Ping Office-PC","TTL=" in out)

url=f"http://{office_ip}:{PORT}"
try:
    with urllib.request.urlopen(url,timeout=5) as r:
        check("HTTP reachable",r.status==200)
        print("Status:",r.status)
except Exception as e:
    check("HTTP reachable",False)
    print(e)

print("\nOpen in browser:")
print(url)
