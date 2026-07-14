#!/usr/bin/env python3
"""FYERS TBT multi-channel probe — is the 5-symbol 50-level ceiling an upstream FYERS
limit or a client-side channel-protocol defect?

Drives ``broker.fyers.streaming.fyers_tbt_websocket.FyersTbtWebSocket`` DIRECTLY,
bypassing OpenAlgo's adapter (which auto-assigns channels lowest-first and exposes no
way to pin a channel). Each test opens a FRESH connection, sends hand-crafted
subscribe/resume frames with FULL control over the channel value and its TYPE
(string vs int), observes for a fixed window, and records every request we send,
every inbound FYERS TEXT frame (JSON subscribe ACKs), every FYERS error (protobuf
``socket_msg.error``, e.g. "symbol count exceeds limit: 5 …"), and per-symbol
50-level depth packet counts.

SCOPE NOTE: this tool lives under ``market_depth_recorder/`` but imports OpenAlgo
platform code (the FYERS streaming client). It is a deliberate, documented diagnostics
scope exception — read-only w.r.t. platform code (it drives the client, never edits it),
in the same spirit as ``Documents/patches/OPENALGO_PATCH.md``.

Canonical tests
  T1   5 syms on channel "1"  (string)   baseline — must stream, else config/market bad
  T2   5 syms on channel "2"  (string)   can a NON-1 channel stream at all?
  T2p  5 syms on channel  2   (int)      is it a string-vs-int channel-type bug?
  T3   5 on ch1 + 5 on ch2 (strings)     the real target: two independent channels?

----------------------------------------------------------------------------------------
Purpose
  Distinguish an undocumented FYERS TBT platform limit from an OpenAlgo channel-protocol
  bug, so the "full 50-level chain vs hybrid" design decision rests on live evidence.

Typical workflow
  1. STOP OpenAlgo's own feed first (avoid a concurrent FYERS session / 429 confound —
     the token is read from the persisted DB, so auto-load still works while it is down).
  2. During market hours, run the matrix with CURRENT-EXPIRY tickers (--group-a/--group-b).
  3. Read T2 vs T3: a non-1 channel that streams alone (T2) but is rejected when a second
     channel is added (T3, "exceeds limit: 5") means the 5-symbol cap is GLOBAL per
     connection, not per channel — channel spreading cannot raise it.

Example command line
  uv run python market_depth_recorder/tools/fyers/tbt_channel_probe.py \
      --out /tmp/tbt_probe.json
  # single arm, custom timing / tickers:
  uv run python market_depth_recorder/tools/fyers/tbt_channel_probe.py \
      --tests T3 --group-a "NSE:NIFTY...CE,..." --group-b "NSE:NIFTY...PE,..." \
      --observe-secs 45 --sub-resume-delay 0.3

Related documentation
  Documents/patches/OPENALGO_PATCH.md   (the channel-spread patch this probes)
  Documents/patches/Phase9_notes.md §3  (the original 5-per-channel finding)

Exit codes: 0 ran (see report), 2 setup/usage error (no token, import failure, bad args).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

# Shared internals live in the sibling module (the script dir is on sys.path[0]
# at launch; _tbt_common's platform imports are deferred). Aliased so this tool's
# body is unchanged after the extraction.
from _tbt_common import (  # noqa: E402
    DEFAULT_OPENALGO_ROOT as _DEFAULT_OPENALGO_ROOT,
    Recorder,
    load_token,
    make_instrumented_cls as _make_instrumented_cls,
    resume as _resume,
    subscribe as _subscribe,
)

# Defaults tied to the 2026-07-14 NIFTY weekly (spot ~24101). Override via
# --group-a / --group-b with CURRENT-EXPIRY FYERS tickers on any other day.
_DEFAULT_GROUP_A = (
    "NSE:NIFTY2671424050CE,NSE:NIFTY2671424100CE,NSE:NIFTY2671424100PE,"
    "NSE:NIFTY2671424150CE,NSE:NIFTY2671424150PE"
)
_DEFAULT_GROUP_B = (
    "NSE:NIFTY2671424000CE,NSE:NIFTY2671424000PE,NSE:NIFTY2671424200CE,"
    "NSE:NIFTY2671424200PE,NSE:NIFTY2671424250CE"
)


def run_test(cls, token: str, name: str, description: str, groups: list[tuple],
             observe: float, sub_resume_delay: float, resume_first: bool) -> dict:
    """groups: list of (symbols, channel_value). channel_value type is honored verbatim."""
    rec = Recorder(name, description)
    for symbols, _ch in groups:
        rec.subscribed.extend(symbols)

    client = cls(access_token=token, log_path="")
    client.recorder = rec
    client.set_callbacks(
        on_depth_update=lambda ticker, data: rec.record_packet(ticker),
        on_error=lambda e: rec.record_error(e),
        on_open=lambda: None,
        on_close=lambda msg: None,
    )

    print(f"\n--- {name}: {description}")
    if not client.connect():
        rec.record_error("connect() failed / timed out")
        print("    CONNECT FAILED")
        try:
            client.disconnect()
        except Exception:
            pass
        return rec.snapshot()

    client.reconnect_enabled = False  # deterministic single connection, no mid-test reconnect
    try:
        for symbols, channel in groups:
            if resume_first:
                rec.record_request("resume", None, channel); _resume(client, [channel])
                time.sleep(sub_resume_delay)
                rec.record_request("subscribe", symbols, channel); _subscribe(client, symbols, channel)
            else:
                rec.record_request("subscribe", symbols, channel); _subscribe(client, symbols, channel)
                time.sleep(sub_resume_delay)
                rec.record_request("resume", None, channel); _resume(client, [channel])
            print(f"    sent subscribe+resume: {len(symbols)} syms on channel "
                  f"{channel!r} ({type(channel).__name__})")
            time.sleep(0.2)

        print(f"    observing {observe:.0f}s ...")
        deadline = time.time() + observe
        while time.time() < deadline:
            time.sleep(0.5)
    finally:
        try:
            client.disconnect()
        except Exception as exc:  # noqa: BLE001
            rec.record_error(f"disconnect error: {exc}")

    snap = rec.snapshot()
    print(f"    result: {snap['streamed_count']}/{snap['subscribed_count']} symbols streamed; "
          f"{len(snap['errors'])} FYERS error(s); {len(snap['inbound_frames'])} text ACK frame(s)")
    return snap


def _print_report(results: list[dict]) -> None:
    print("\n" + "=" * 78)
    print("TBT CHANNEL PROBE — REPORT")
    print("=" * 78)
    for r in results:
        print(f"\n### {r['test']} — {r['description']}")
        print(f"  subscribed: {r['subscribed_count']}   streamed: {r['streamed_count']}")
        if r["streamed"]:
            for t, info in sorted(r["streamed"].items()):
                print(f"      STREAMED {t:<26} packets={info['packets']}")
        else:
            print("      STREAMED: none")
        not_streamed = [s for s in r["subscribed"] if s not in r["streamed"]]
        if not_streamed:
            print(f"      SILENT  : {', '.join(not_streamed)}")
        print("  requests sent:")
        for q in r["requests"]:
            print(f"      {q['op']:<9} channel={q['channel']!r} ({q['channel_type']})"
                  f"{'  syms=' + str(len(q['symbols'])) if q['symbols'] else ''}")
        print(f"  FYERS text ACKs ({len(r['inbound_frames'])}):")
        for f in r["inbound_frames"][:12]:
            print(f"      {f['raw']}")
        if len(r["inbound_frames"]) > 12:
            print(f"      ... (+{len(r['inbound_frames']) - 12} more)")
        print(f"  FYERS errors ({len(r['errors'])}):")
        for e in r["errors"][:12]:
            print(f"      {e['msg']}")
    print("\n" + "=" * 78)
    _print_hint(results)
    print("=" * 78)


def _print_hint(results: list[dict]) -> None:
    by = {r["test"]: r for r in results}

    def sc(name):
        return by[name]["streamed_count"] if name in by else None

    def sub(name):
        return by[name]["subscribed_count"] if name in by else None

    t1, t2, t2p = sc("T1"), sc("T2"), sc("T2p")
    t3, t3_sub = sc("T3"), sub("T3")
    print("HINT:")
    if t1 == 0:
        print("  T1 baseline streamed 0 — tickers likely stale/expired or market closed."
              " Fix --group-a and re-run before trusting the rest.")
        return
    notes: list[str] = []
    if t2p == 0 and (t2 or 0) > 0:
        notes.append("resume requires STRING channel ids; an integer channel silently leaves"
                     " the channel paused (no data, no error) — a latent client footgun.")
    if t3 is not None and t3_sub is not None:
        if t3 < t3_sub:
            notes.append(f"T3 streamed only {t3}/{t3_sub} with an 'exceeds limit' error: concurrent"
                         " channels do NOT add quota — the 5-symbol cap is GLOBAL per connection,"
                         " not per channel. Channel spreading cannot raise the ceiling;"
                         " use a hybrid (5 near-ATM @50 + rest @5) or multiple TBT connections.")
        else:
            notes.append("T3 streamed fully — channels ARE concurrently independent; the client"
                         " can scale 50-level via channel spreading.")
    elif (t2 or 0) > 0:
        notes.append("a non-1 channel streams alone (T2); run T3 to see if channels are"
                     " concurrently independent or share one global 5-symbol budget.")
    elif t2 == 0 and (t2p or 0) == 0:
        notes.append("neither T2 nor T2p streamed — inspect the ch2 ACKs: if FYERS accepted ch2"
                     " yet no data flowed, evidence favors an upstream FYERS limit / resume issue.")
    for n in notes:
        print(f"  {n}")


def _parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="tbt_channel_probe.py",
        description="Probe whether FYERS TBT can stream on channels other than 1.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog="Stop OpenAlgo's feed first (avoid a concurrent FYERS session). Exit: 0 ok, 2 error.",
    )
    p.add_argument("--openalgo-root", default=_DEFAULT_OPENALGO_ROOT,
                   help="OpenAlgo repo root (put on sys.path to import FYERS streaming)")
    p.add_argument("--token", default=None,
                   help="FYERS access token (else FYERS_TBT_TOKEN env, else auto-load from DB)")
    p.add_argument("--user-id", default="Shreyas S S", help="OpenAlgo user for token auto-load")
    p.add_argument("--group-a", default=_DEFAULT_GROUP_A,
                   help="comma-sep FYERS tickers (5) for the ch-A tests")
    p.add_argument("--group-b", default=_DEFAULT_GROUP_B,
                   help="comma-sep FYERS tickers (5) for ch-B in T3")
    p.add_argument("--channel-a", default="1", help="channel value for baseline/A (string)")
    p.add_argument("--channel-b", default="2", help="channel value for the non-1 tests (string)")
    p.add_argument("--observe-secs", type=float, default=30.0, help="observation window per test")
    p.add_argument("--sub-resume-delay", type=float, default=0.15,
                   help="delay between subscribe and resume")
    p.add_argument("--inter-test-delay", type=float, default=3.0,
                   help="pause between tests (avoid 429)")
    p.add_argument("--resume-first", action="store_true", help="send resume BEFORE subscribe")
    p.add_argument("--tests", default="T1,T2,T2p,T3", help="comma-sep subset of T1,T2,T2p,T3")
    p.add_argument("--out", default=None, help="write full JSON report here")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv)
    if not os.path.isdir(args.openalgo_root):
        print(f"error: --openalgo-root not found: {args.openalgo_root}", file=sys.stderr)
        return 2
    sys.path.insert(0, args.openalgo_root)
    os.chdir(args.openalgo_root)  # auth_db resolves db/ relative to cwd

    token = load_token(args.token, args.openalgo_root, args.user_id)
    if not token:
        return 2

    try:
        cls = _make_instrumented_cls()
    except Exception as exc:  # noqa: BLE001
        print(f"error: could not import FyersTbtWebSocket from {args.openalgo_root}: {exc}",
              file=sys.stderr)
        return 2

    group_a = [s.strip() for s in args.group_a.split(",") if s.strip()]
    group_b = [s.strip() for s in args.group_b.split(",") if s.strip()]
    ca, cb = args.channel_a, args.channel_b
    try:
        cb_int = int(cb)
    except ValueError:
        cb_int = cb  # non-numeric: pass through unchanged

    all_specs = {
        "T1":  ("baseline: 5 syms on channel %r (string)" % ca, [(group_a, ca)]),
        "T2":  ("5 syms on channel %r (string)" % cb, [(group_a, cb)]),
        "T2p": ("5 syms on channel %r (int)" % cb_int, [(group_a, cb_int)]),
        "T3":  ("5 on ch %r + 5 on ch %r (strings)" % (ca, cb), [(group_a, ca), (group_b, cb)]),
    }
    wanted = [t.strip() for t in args.tests.split(",") if t.strip()]

    results = []
    for i, name in enumerate(wanted):
        if name not in all_specs:
            print(f"warning: unknown test {name!r}, skipping", file=sys.stderr)
            continue
        desc, groups = all_specs[name]
        snap = run_test(cls, token, name, desc, groups,
                        observe=args.observe_secs, sub_resume_delay=args.sub_resume_delay,
                        resume_first=args.resume_first)
        results.append(snap)
        if i < len(wanted) - 1:
            time.sleep(args.inter_test_delay)

    _print_report(results)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({"generated": time.time(), "args": vars(args), "results": results},
                      fh, indent=2)
        print(f"\nfull JSON report -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
