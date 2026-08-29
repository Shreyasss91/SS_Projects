#!/usr/bin/env python3
"""FYERS TBT multi-connection probe — what is the EFFECTIVE concurrent 50-level
depth budget across the allowed connections?

The single-connection probe (``tbt_channel_probe.py``) already settled that
channels do NOT add capacity: the cap is 5 Market-Depth symbols per *connection*.
This tool answers the remaining protocol question — whether FYERS' documented
"3 active connections per app per user" combine to an effective **3 x 5 = 15**
concurrent 50-level symbols, or whether an undocumented per-token / per-user
limit clamps the total to 5 regardless of connection count.

It drives ``broker.fyers.streaming.fyers_tbt_websocket.FyersTbtWebSocket``
DIRECTLY (bypassing OpenAlgo's adapter), opening N genuinely independent
connections, each subscribing a DISTINCT 5-symbol group on channel "1", then
observing all of them CONCURRENTLY. Per connection and per symbol it records the
connect timestamp, the first snapshot arrival, the first incremental-update
arrival, sustained packet counts, every FYERS ACK/error, and any mid-run drop.

SCOPE NOTE: lives under ``market_depth_recorder/`` but imports OpenAlgo platform
code (the FYERS streaming client). Deliberate, documented diagnostics scope
exception — read-only w.r.t. platform code. See ``tools/fyers/README.md``.

----------------------------------------------------------------------------------------
Phases (each phase's connections are fresh; C4 runs while C3's 3 are still up)
  C1  baseline   1 connection,  5 syms                   must stream 5/5 (control)
  C3  core       3 connections, 5 distinct syms each     15 distinct total — the question
  C4  ceiling    attempt a 4th connection while 3 are up confirms the documented 3-conn cap

Interpretation
  * C3 streams 15/15  -> connections are independent; effective budget = 15.
  * C3 streams ~5 total (conn2/conn3 silent or "exceeds limit: 5") -> the cap is
    per token/user; a full chain needs the hybrid (5 near-ATM @50 + rest @5).
  * C4 connect refused -> the "3 connections per app per user" ceiling holds exactly.

Typical workflow
  1. STOP OpenAlgo's own feed first — its adapter already holds >=1 TBT connection,
     and with the 3-connection ceiling that would confound the C3/C4 accounting.
  2. During market hours, run with CURRENT-EXPIRY tickers (--groups).
  3. Read the verdict line; freeze the JSON (--out) as evidence.

Example command line
  uv run python market_depth_recorder/tools/fyers/tbt_multiconn_probe.py \
      --observe-secs 60 --out /tmp/tbt_multiconn.json

Related documentation
  Documents/evidence/openalgo_platform/OPENALGO_PATCH.md  §8.4  (the open multi-connection question)
  plans/Plan_001_evidence/Phase9_notes.md          (the FYERS TBT investigation trail)
  tools/fyers/tbt_channel_probe.py            (the single-connection channel matrix)

Exit codes: 0 ran (see report), 2 setup/usage error (no token, import failure, bad args).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

# The script's own directory (tools/fyers) is on sys.path[0] at launch, so the
# sibling shared module imports with only the stdlib (its platform imports are
# deferred). The OpenAlgo root is added to sys.path in main() before we touch it.
from _tbt_common import (  # noqa: E402
    DEFAULT_OPENALGO_ROOT,
    Recorder,
    load_token,
    make_instrumented_cls,
    resume,
    subscribe,
)

# Defaults: 15 distinct NIFTY legs on the 2026-07-14 weekly (all confirmed valid,
# streaming subscriptions in that day's own raw capture). Group 1 is exactly the
# channel-probe baseline group. Override via --groups on any other day with
# CURRENT-EXPIRY FYERS tickers. Groups are ';'-separated; symbols ','-separated.
_DEFAULT_GROUPS = ";".join([
    "NSE:NIFTY2671424050CE,NSE:NIFTY2671424100CE,NSE:NIFTY2671424100PE,"
    "NSE:NIFTY2671424150CE,NSE:NIFTY2671424150PE",
    "NSE:NIFTY2671424000CE,NSE:NIFTY2671424000PE,NSE:NIFTY2671424200CE,"
    "NSE:NIFTY2671424200PE,NSE:NIFTY2671424250CE",
    "NSE:NIFTY2671423900CE,NSE:NIFTY2671423900PE,NSE:NIFTY2671423950CE,"
    "NSE:NIFTY2671423950PE,NSE:NIFTY2671423850CE",
])


class Conn:
    """One physical probe connection: its recorder, client, group, connect result."""

    __slots__ = ("rec", "client", "group", "connected")

    def __init__(self, rec: Recorder, client, group: list[str], connected: bool):
        self.rec = rec
        self.client = client
        self.group = group
        self.connected = connected


def _make_client(cls, token: str, rec: Recorder):
    client = cls(access_token=token, log_path="")
    client.recorder = rec

    def _on_error(e):
        rec.record_error(e)
        # Stop a handshake-failure retry storm. FyersTbtWebSocket._run_websocket
        # re-enters run_forever() every time it *returns* (a handshake 429 returns
        # rather than raises, so the reconnect_enabled guard in its except-branch
        # is never reached) — that hammers FYERS ~10x/s and self-inflicts a
        # Cloudflare 1015 IP rate-limit that confounds the C4 ceiling test. If we
        # never reached a live connection, end the loop after this single attempt.
        if not client.connected:
            client.running = False

    client.set_callbacks(
        on_depth_update=lambda ticker, data: rec.record_packet(ticker, data.get("snapshot")),
        on_error=_on_error,
        on_open=lambda: None,
        on_close=lambda info: rec.record_close(info),
    )
    return client


def open_connections(cls, token: str, groups: list[list[str]], label: str,
                     connect_stagger: float) -> list[Conn]:
    """Open one fresh connection per group, staggered. Reconnect disabled on each
    so the concurrent-connection count stays deterministic (drops are recorded via
    the observe-loop poll instead)."""
    conns: list[Conn] = []
    for i, group in enumerate(groups):
        rec = Recorder(f"{label}-conn{i + 1}", f"connection {i + 1} of {label}: {len(group)} syms")
        rec.subscribed = list(group)
        client = _make_client(cls, token, rec)
        # Disable reconnect BEFORE connecting so a failed handshake is a single
        # clean attempt — not a tight retry storm that self-inflicts a Cloudflare
        # 429 (which would confound the C4 ceiling test) and never spawns a stray
        # extra connection. We never want reconnect in this deterministic probe.
        client.reconnect_enabled = False
        rec.connect_requested_ts = time.time()
        print(f"    [{label}] connecting conn{i + 1} ({len(group)} syms) ...", flush=True)
        ok = False
        try:
            ok = client.connect()
        except Exception as exc:  # noqa: BLE001
            rec.record_error(f"connect() raised: {exc}")
        if ok:
            rec.connect_ts = time.time()
            print(f"    [{label}] conn{i + 1} CONNECTED "
                  f"(+{rec.connect_ts - rec.connect_requested_ts:.2f}s)", flush=True)
        else:
            rec.record_error("connect() failed / timed out / refused")
            print(f"    [{label}] conn{i + 1} CONNECT FAILED", flush=True)
        conns.append(Conn(rec, client, group, ok))
        time.sleep(connect_stagger)
    return conns


def subscribe_all(conns: list[Conn], sub_resume_delay: float) -> None:
    """Subscribe each connected client to its distinct group on channel '1'."""
    for c in conns:
        if not c.connected:
            continue
        c.rec.record_request("subscribe", c.group, "1")
        subscribe(c.client, c.group, "1")
        time.sleep(sub_resume_delay)
        c.rec.record_request("resume", None, "1")
        resume(c.client, ["1"])
        print(f"    subscribed+resumed {len(c.group)} syms on {c.rec.test} (channel '1')",
              flush=True)


def observe(conns: list[Conn], secs: float, poll: float = 0.5) -> None:
    """Observe concurrently; record any connected -> disconnected transition."""
    prev = {id(c): True for c in conns if c.connected}
    print(f"    observing {secs:.0f}s (sustained-stream + drop watch) ...", flush=True)
    deadline = time.time() + secs
    while time.time() < deadline:
        for c in conns:
            if not c.connected:
                continue
            now = c.client.is_connected()
            if not now and prev.get(id(c), True):
                c.rec.record_close("is_connected -> False (unexpected drop during observe)")
                print(f"    !! {c.rec.test} DROPPED mid-observe", flush=True)
            prev[id(c)] = now
        time.sleep(poll)


def close_all(conns: list[Conn]) -> None:
    for c in conns:
        try:
            c.client.disconnect()
        except Exception as exc:  # noqa: BLE001
            c.rec.record_error(f"disconnect error: {exc}")


# --------------------------------------------------------------------------- report


def _fmt_delta(ts, base):
    if ts is None or base is None:
        return "  --  "
    return f"+{ts - base:.2f}s"


def _print_conn(snap: dict) -> None:
    base = snap["connect_ts"]
    print(f"\n  ### {snap['test']} — {snap['description']}")
    if snap["connect_ts"] and snap["connect_requested_ts"]:
        print(f"      connect: +{snap['connect_ts'] - snap['connect_requested_ts']:.2f}s "
              f"after request")
    else:
        print("      connect: FAILED")
    print(f"      subscribed {snap['subscribed_count']}   streamed {snap['streamed_count']}   "
          f"total_packets {snap['total_packets']}")
    for t in sorted(snap["subscribed"]):
        info = snap["streamed"].get(t)
        if info:
            print(f"        {t:<26} pkts={info['packets']:<5} "
                  f"snap={info['snapshots']} incr={info['increments']}  "
                  f"1st-snap {_fmt_delta(info['first_snapshot_ts'], base)}  "
                  f"1st-incr {_fmt_delta(info['first_incr_ts'], base)}")
        else:
            print(f"        {t:<26} SILENT (no packets)")
    if snap["errors"]:
        print(f"      FYERS errors ({len(snap['errors'])}):")
        for e in snap["errors"][:8]:
            print(f"        {e['msg']}")
    if snap["closes"]:
        print(f"      drops/closes ({len(snap['closes'])}):")
        for c in snap["closes"][:8]:
            print(f"        {c['info']}")
    if snap["inbound_frames"]:
        print(f"      FYERS text ACKs ({len(snap['inbound_frames'])}):")
        for f in snap["inbound_frames"][:6]:
            print(f"        {f['raw']}")


def _phase_streamed_total(snaps: list[dict]) -> int:
    seen = set()
    for s in snaps:
        seen.update(s["streamed"].keys())
    return len(seen)


def _print_report(phases: dict[str, list[dict]]) -> None:
    print("\n" + "=" * 80)
    print("TBT MULTI-CONNECTION PROBE — REPORT")
    print("=" * 80)
    for label, snaps in phases.items():
        print(f"\n--- PHASE {label} " + "-" * (72 - len(label)))
        for s in snaps:
            _print_conn(s)
    print("\n" + "=" * 80)
    _print_verdict(phases)
    print("=" * 80)


def _print_verdict(phases: dict[str, list[dict]]) -> None:
    print("VERDICT:")
    c1 = phases.get("C1", [])
    c3 = phases.get("C3", [])
    c4 = phases.get("C4", [])

    if c1:
        s = c1[0]
        print(f"  C1 baseline: {s['streamed_count']}/{s['subscribed_count']} streamed"
              + ("" if s["streamed_count"] else
                 "  <-- baseline failed: tickers stale/expired or market closed; "
                 "fix --groups and re-run before trusting C3/C4."))
        if s["streamed_count"] == 0:
            return

    if c3:
        subs = sum(s["subscribed_count"] for s in c3)
        total = _phase_streamed_total(c3)
        exceed = any("exceeds limit" in e["msg"].lower()
                     for s in c3 for e in s["errors"])
        per = ", ".join(f"{s['test'].split('-')[-1]}={s['streamed_count']}/{s['subscribed_count']}"
                        for s in c3)
        print(f"  C3 core: {total}/{subs} distinct symbols streamed across "
              f"{len(c3)} connections ({per})"
              + ("  [saw 'exceeds limit: 5']" if exceed else ""))
        if total >= subs and not exceed:
            print(f"  => Connections are INDEPENDENT. Effective 50-level budget = {subs} "
                  f"({len(c3)} conns x 5). The TBT Allocator gets tbt_budget={subs}; "
                  f"architecture unchanged.")
        elif total <= 5 or exceed:
            print("  => The 5-symbol cap is per TOKEN/USER, not per connection. Extra "
                  "connections do NOT add depth capacity — the HYBRID (5 near-ATM @50 + "
                  "rest @5) is required for a full chain.")
        else:
            print(f"  => PARTIAL: {total} streamed (between 5 and {subs}). Inspect per-conn "
                  "counts + ACKs/errors below; budget is neither a clean 5 nor a clean "
                  f"{subs}.")

    if c4:
        s = c4[0]
        if s["connect_ts"] is None:
            print("  C4 ceiling: 4th connection REFUSED while 3 were up -> the documented "
                  "'3 active connections per app/user' limit holds exactly.")
        else:
            print(f"  C4 ceiling: 4th connection CONNECTED and streamed "
                  f"{s['streamed_count']}/{s['subscribed_count']} -> the 3-connection limit "
                  "did NOT bind as documented; re-examine the connection accounting.")


# --------------------------------------------------------------------------- main


def _parse_groups(raw: str) -> list[list[str]]:
    groups = []
    for chunk in raw.split(";"):
        syms = [s.strip() for s in chunk.split(",") if s.strip()]
        if syms:
            groups.append(syms)
    return groups


def _parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="tbt_multiconn_probe.py",
        description="Probe the effective concurrent 50-level TBT budget across connections.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog="Stop OpenAlgo's feed first (avoid competing TBT connections). Exit: 0 ok, 2 error.",
    )
    p.add_argument("--openalgo-root", default=DEFAULT_OPENALGO_ROOT,
                   help="OpenAlgo repo root (put on sys.path to import FYERS streaming)")
    p.add_argument("--token", default=None,
                   help="FYERS access token (else FYERS_TBT_TOKEN env, else auto-load from DB)")
    p.add_argument("--user-id", default="Shreyas S S", help="OpenAlgo user for token auto-load")
    p.add_argument("--groups", default=_DEFAULT_GROUPS,
                   help="';'-separated groups of ','-separated FYERS tickers (5 per group)")
    p.add_argument("--connections", "-n", type=int, default=3,
                   help="number of concurrent connections for the core phase")
    p.add_argument("--observe-secs", type=float, default=60.0,
                   help="core (C3) observation window — long enough for sustained streaming")
    p.add_argument("--baseline-secs", type=float, default=20.0,
                   help="baseline (C1) observation window")
    p.add_argument("--c4-secs", type=float, default=15.0,
                   help="4th-connection (C4) observation window if it connects")
    p.add_argument("--connect-stagger", type=float, default=1.0,
                   help="delay between successive connect() calls (avoid a burst / 429)")
    p.add_argument("--sub-resume-delay", type=float, default=0.15,
                   help="delay between subscribe and resume on each connection")
    p.add_argument("--inter-phase-delay", type=float, default=3.0,
                   help="pause between phases (let sessions settle / avoid 429)")
    p.add_argument("--phases", default="C1,C3,C4",
                   help="comma-sep subset of C1,C3,C4 to run")
    p.add_argument("--out", default=None, help="write full JSON report here")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv)
    if not os.path.isdir(args.openalgo_root):
        print(f"error: --openalgo-root not found: {args.openalgo_root}", file=sys.stderr)
        return 2
    sys.path.insert(0, args.openalgo_root)
    os.chdir(args.openalgo_root)  # auth_db resolves db/ relative to cwd

    groups = _parse_groups(args.groups)
    if not groups:
        print("error: --groups parsed to nothing", file=sys.stderr)
        return 2

    wanted = [p.strip() for p in args.phases.split(",") if p.strip()]
    n = args.connections
    if "C3" in wanted and len(groups) < n:
        print(f"error: C3 needs {n} groups but only {len(groups)} provided "
              f"(pass --groups with {n} ';'-separated groups)", file=sys.stderr)
        return 2

    token = load_token(args.token, args.openalgo_root, args.user_id)
    if not token:
        return 2
    try:
        cls = make_instrumented_cls()
    except Exception as exc:  # noqa: BLE001
        print(f"error: could not import FyersTbtWebSocket from {args.openalgo_root}: {exc}",
              file=sys.stderr)
        return 2

    phases: dict[str, list[dict]] = {}

    # ---- C1: baseline, one connection, group 1 ----
    if "C1" in wanted:
        print("\n=== PHASE C1: baseline (1 connection, 5 syms) ===", flush=True)
        conns = open_connections(cls, token, groups[:1], "C1", args.connect_stagger)
        try:
            subscribe_all(conns, args.sub_resume_delay)
            observe(conns, args.baseline_secs)
            phases["C1"] = [c.rec.snapshot() for c in conns]
        finally:
            close_all(conns)
        time.sleep(args.inter_phase_delay)

    # ---- C3: core, N concurrent connections, distinct groups; keep up for C4 ----
    if "C3" in wanted:
        print(f"\n=== PHASE C3: core ({n} concurrent connections, 5 distinct syms each) ===",
              flush=True)
        core = open_connections(cls, token, groups[:n], "C3", args.connect_stagger)
        try:
            subscribe_all(core, args.sub_resume_delay)
            observe(core, args.observe_secs)
            phases["C3"] = [c.rec.snapshot() for c in core]

            # ---- C4: attempt a 4th connection WHILE the N are still up ----
            if "C4" in wanted:
                print("\n=== PHASE C4: ceiling (attempt a 4th connection while 3 are up) ===",
                      flush=True)
                # Reuse group 1's tickers — the connection-cap test does not need
                # fresh symbols; we only care whether the 4th connection is allowed.
                extra = open_connections(cls, token, [groups[0]], "C4", args.connect_stagger)
                try:
                    if extra[0].connected:
                        subscribe_all(extra, args.sub_resume_delay)
                        observe(extra, args.c4_secs)
                    phases["C4"] = [c.rec.snapshot() for c in extra]
                finally:
                    close_all(extra)
        finally:
            close_all(core)
    elif "C4" in wanted:
        print("warning: C4 requires C3 (needs 3 live connections first); skipping C4",
              file=sys.stderr)

    _print_report(phases)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({"generated": time.time(), "args": vars(args), "phases": phases},
                      fh, indent=2)
        print(f"\nfull JSON report -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
